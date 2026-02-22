from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud
from app.models.audit import AuditEvidence, AuditTrailResponse, ClaimVerification

router = APIRouter()


@router.get("/sar/{sar_id}/evidence/{sentence_index}", response_model=AuditEvidence)
def get_sentence_evidence(
    sar_id: str,
    sentence_index: int,
    db: Session = Depends(get_db),
):
    """
    Get audit evidence for a specific sentence in the SAR.
    Returns data source, SQL query, results, confidence, and reasoning.
    """
    sar = crud.get_sar_by_id(db, sar_id)
    if not sar:
        raise HTTPException(status_code=404, detail="SAR not found")

    # Get audit logs for this sentence
    audit_logs = crud.get_audit_logs_by_sentence(db, sar_id, sentence_index)

    if not audit_logs:
        raise HTTPException(
            status_code=404,
            detail=f"No audit evidence found for sentence {sentence_index}",
        )

    # Extract sentence from narrative
    sentences = [s.strip() + "." for s in sar.narrative.split(".") if s.strip()]
    if sentence_index >= len(sentences):
        raise HTTPException(status_code=400, detail="Invalid sentence index")

    sentence = sentences[sentence_index]

    # Aggregate audit data
    sql_queries = []
    query_results = []
    claims = []
    llm_prompt = None
    llm_response = None
    reasoning = ""
    confidence = 1.0

    for log in audit_logs:
        data = log.data or {}

        if log.entry_type == "sql_query":
            sql_queries.append(data.get("query", ""))
            query_results.extend(data.get("results", []))

        elif log.entry_type == "fact_verification":
            claims.append(
                ClaimVerification(
                    claim=data.get("claim", ""),
                    expected_value=data.get("expected"),
                    actual_value=data.get("actual"),
                    is_verified=data.get("verified", False),
                    confidence=data.get("confidence", 0),
                )
            )
            confidence = min(confidence, data.get("confidence", 1.0))

        elif log.entry_type == "llm_generation":
            llm_prompt = data.get("prompt")
            llm_response = data.get("response")
            reasoning = data.get("reasoning", "")

    return AuditEvidence(
        sentence=sentence,
        sentence_index=sentence_index,
        data_source="transactions, customers",
        sql_query="\n\n".join(sql_queries) if sql_queries else "N/A",
        query_results=query_results,
        confidence=confidence,
        reasoning=reasoning or "Generated based on verified transaction data.",
        claims=claims,
        llm_prompt=llm_prompt,
        llm_response=llm_response,
    )


@router.get("/sar/{sar_id}", response_model=AuditTrailResponse)
def get_full_audit_trail(
    sar_id: str,
    db: Session = Depends(get_db),
):
    """
    Get the complete audit trail for a SAR.
    Includes all evidence for every sentence.
    """
    sar = crud.get_sar_by_id(db, sar_id)
    if not sar:
        raise HTTPException(status_code=404, detail="SAR not found")

    sentences = [s.strip() + "." for s in sar.narrative.split(".") if s.strip()]
    all_logs = crud.get_audit_logs_by_sar(db, sar_id)

    # Group logs by sentence
    entries = []
    total_queries = 0
    total_tokens = 0

    for idx, sentence in enumerate(sentences):
        sentence_logs = [log for log in all_logs if log.sentence_index == idx]

        if sentence_logs:
            # Build evidence for this sentence
            sql_queries = []
            query_results = []
            claims = []
            confidence = 1.0

            for log in sentence_logs:
                data = log.data or {}

                if log.entry_type == "sql_query":
                    sql_queries.append(data.get("query", ""))
                    query_results.extend(data.get("results", []))
                    total_queries += 1

                elif log.entry_type == "fact_verification":
                    claims.append(
                        ClaimVerification(
                            claim=data.get("claim", ""),
                            expected_value=data.get("expected"),
                            actual_value=data.get("actual"),
                            is_verified=data.get("verified", False),
                            confidence=data.get("confidence", 0),
                        )
                    )
                    confidence = min(confidence, data.get("confidence", 1.0))

                elif log.entry_type == "llm_generation":
                    tokens = data.get("tokens_used", {})
                    total_tokens += tokens.get("total", 0)

            entries.append(
                AuditEvidence(
                    sentence=sentence,
                    sentence_index=idx,
                    data_source="transactions, customers",
                    sql_query="\n".join(sql_queries),
                    query_results=query_results,
                    confidence=confidence,
                    reasoning="Verified against database records.",
                    claims=claims,
                )
            )

    verified_count = len([e for e in entries if e.confidence >= 0.95])
    overall_confidence = (
        sum(e.confidence for e in entries) / len(entries) if entries else 0
    )

    return AuditTrailResponse(
        sar_id=sar_id,
        total_sentences=len(sentences),
        verified_sentences=verified_count,
        overall_confidence=overall_confidence,
        entries=entries,
        generation_timestamp=sar.created_at,
        total_queries_executed=total_queries,
        total_tokens_used=total_tokens,
    )
