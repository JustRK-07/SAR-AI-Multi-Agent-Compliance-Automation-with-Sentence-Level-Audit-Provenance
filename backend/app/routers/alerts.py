from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.db import crud
from app.models.alert import AlertResponse, AlertListResponse, AlertStatus

router = APIRouter()


@router.get("/", response_model=AlertListResponse)
def list_alerts(
    status: Optional[str] = Query(None, description="Filter by status"),
    scenario: Optional[str] = Query(None, description="Filter by scenario type"),
    min_risk: int = Query(0, ge=0, le=100, description="Minimum risk score"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    List all alerts with optional filtering.
    Sorted by risk score (highest first).
    """
    skip = (page - 1) * page_size
    alerts, total = crud.get_alerts(
        db,
        status=status,
        scenario=scenario,
        min_risk=min_risk,
        skip=skip,
        limit=page_size,
    )

    alert_responses = []
    for alert in alerts:
        stats = crud.get_transaction_stats(db, alert.id)
        alert_responses.append(
            AlertResponse(
                id=alert.id,
                trigger_date=alert.trigger_date,
                scenario=alert.scenario,
                risk_score=alert.risk_score,
                customer_id=alert.customer_id,
                customer_name=alert.customer.name if alert.customer else "Unknown",
                account_number=alert.customer.account_number if alert.customer else "Unknown",
                status=AlertStatus(alert.status),
                transaction_count=stats["transaction_count"],
                total_amount=stats["total_amount"],
                assigned_to=alert.assigned_to,
                created_at=alert.created_at,
            )
        )

    return AlertListResponse(
        alerts=alert_responses,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific alert."""
    alert = crud.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    stats = crud.get_transaction_stats(db, alert_id)

    return AlertResponse(
        id=alert.id,
        trigger_date=alert.trigger_date,
        scenario=alert.scenario,
        risk_score=alert.risk_score,
        customer_id=alert.customer_id,
        customer_name=alert.customer.name if alert.customer else "Unknown",
        account_number=alert.customer.account_number if alert.customer else "Unknown",
        status=AlertStatus(alert.status),
        transaction_count=stats["transaction_count"],
        total_amount=stats["total_amount"],
        assigned_to=alert.assigned_to,
        created_at=alert.created_at,
    )


@router.patch("/{alert_id}/status")
def update_alert_status(
    alert_id: str,
    status: AlertStatus,
    db: Session = Depends(get_db),
):
    """Update the status of an alert."""
    alert = crud.update_alert_status(db, alert_id, status.value)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {"message": "Status updated", "alert_id": alert_id, "status": status}
