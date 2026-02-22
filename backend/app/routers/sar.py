from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import uuid
from datetime import datetime
import io

from app.db.database import get_db
from app.db import crud
from app.models.sar import (
    SARGenerateRequest,
    SARGenerateResponse,
    SARResponse,
    SARUpdateRequest,
    SARStatus,
    SARSubmitResponse,
)
from app.services.sar_generator import SARGeneratorService

router = APIRouter()

# Store for tracking generation tasks
generation_tasks: dict[str, dict] = {}


@router.post("/generate", response_model=SARGenerateResponse)
async def generate_sar(
    request: SARGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Start SAR narrative generation for an alert.
    Returns immediately with task_id. Generation happens in background.
    Use WebSocket /ws/sar/{task_id} to track progress.
    """
    # Verify alert exists
    alert = crud.get_alert_by_id(db, request.alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Check if SAR already exists for this alert
    existing_sar = crud.get_sar_by_alert(db, request.alert_id)
    if existing_sar and existing_sar.status not in ["rejected"]:
        return SARGenerateResponse(
            task_id="existing",
            sar_id=existing_sar.id,
            status=SARStatus(existing_sar.status),
            message="SAR already exists for this alert",
        )

    # Create task ID
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    sar_id = f"SAR_{datetime.now().strftime('%Y')}_{uuid.uuid4().hex[:8].upper()}"

    # Store task info
    generation_tasks[task_id] = {
        "sar_id": sar_id,
        "alert_id": request.alert_id,
        "status": "processing",
        "progress": 0,
        "current_agent": None,
    }

    # Start background generation
    background_tasks.add_task(
        run_sar_generation,
        task_id=task_id,
        sar_id=sar_id,
        alert_id=request.alert_id,
    )

    return SARGenerateResponse(
        task_id=task_id,
        sar_id=sar_id,
        status=SARStatus.PROCESSING,
        message="SAR generation started",
    )


async def run_sar_generation(task_id: str, sar_id: str, alert_id: str):
    """Background task to run SAR generation pipeline."""
    from app.db.database import SessionLocal

    db = SessionLocal()
    try:
        generator = SARGeneratorService(db)

        # Update progress callback
        def on_progress(agent: str, progress: int):
            generation_tasks[task_id]["current_agent"] = agent
            generation_tasks[task_id]["progress"] = progress

        result = await generator.generate(
            alert_id=alert_id,
            sar_id=sar_id,
            on_progress=on_progress,
        )

        generation_tasks[task_id]["status"] = "completed"
        generation_tasks[task_id]["progress"] = 100

    except Exception as e:
        generation_tasks[task_id]["status"] = "failed"
        generation_tasks[task_id]["error"] = str(e)
    finally:
        db.close()


@router.get("/task/{task_id}")
def get_task_status(task_id: str):
    """Get the status of a SAR generation task."""
    if task_id not in generation_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    return generation_tasks[task_id]


@router.get("/{sar_id}", response_model=SARResponse)
def get_sar(sar_id: str, db: Session = Depends(get_db)):
    """Get SAR by ID with full narrative and metadata."""
    sar = crud.get_sar_by_id(db, sar_id)
    if not sar:
        raise HTTPException(status_code=404, detail="SAR not found")

    alert = crud.get_alert_by_id(db, sar.alert_id)
    stats = crud.get_transaction_stats(db, sar.alert_id)

    # Split narrative into sentences for interactive UI
    sentences = [s.strip() + "." for s in sar.narrative.split(".") if s.strip()]

    return SARResponse(
        id=sar.id,
        alert_id=sar.alert_id,
        narrative=sar.narrative,
        typology=sar.typology,
        fincen_code=sar.fincen_code,
        status=SARStatus(sar.status),
        confidence_score=sar.confidence_score,
        sentence_count=sar.sentence_count,
        sentences=sentences,
        created_at=sar.created_at,
        updated_at=sar.updated_at,
        customer_name=alert.customer.name if alert and alert.customer else "Unknown",
        account_number=alert.customer.account_number if alert and alert.customer else "Unknown",
        total_amount=stats["total_amount"],
        transaction_count=stats["transaction_count"],
    )


@router.get("/by-alert/{alert_id}", response_model=SARResponse)
def get_sar_by_alert(alert_id: str, db: Session = Depends(get_db)):
    """Get SAR by alert ID."""
    sar = crud.get_sar_by_alert(db, alert_id)
    if not sar:
        raise HTTPException(status_code=404, detail="SAR not found for this alert")

    return get_sar(sar.id, db)


@router.patch("/{sar_id}")
def update_sar(
    sar_id: str,
    request: SARUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update SAR narrative or status (analyst edits)."""
    sar = crud.update_sar(
        db,
        sar_id=sar_id,
        narrative=request.narrative,
        status=request.status.value if request.status else None,
    )

    if not sar:
        raise HTTPException(status_code=404, detail="SAR not found")

    return {"message": "SAR updated", "sar_id": sar_id}


@router.post("/{sar_id}/submit", response_model=SARSubmitResponse)
def submit_sar(
    sar_id: str,
    approved_by: str = "analyst",
    db: Session = Depends(get_db),
):
    """Approve and submit SAR for regulatory filing."""
    sar = crud.submit_sar(db, sar_id, approved_by)

    if not sar:
        raise HTTPException(status_code=404, detail="SAR not found")

    return SARSubmitResponse(
        sar_id=sar.id,
        filing_id=sar.filing_id,
        submitted_at=sar.submitted_at,
        status="submitted",
    )


@router.get("/{sar_id}/export")
def export_sar_pdf(sar_id: str, db: Session = Depends(get_db)):
    """Export SAR as PDF with audit trail."""
    sar = crud.get_sar_by_id(db, sar_id)
    if not sar:
        raise HTTPException(status_code=404, detail="SAR not found")

    # Generate PDF with full audit trail
    from app.services.pdf_generator import generate_sar_pdf

    pdf_buffer = generate_sar_pdf(db, sar)

    return StreamingResponse(
        io.BytesIO(pdf_buffer),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={sar_id}.pdf"},
    )
