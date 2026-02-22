from sqlalchemy.orm import Session
from typing import Any
from datetime import datetime

from app.db import crud


class AuditTrailService:
    """
    Service for managing audit trail entries.
    Provides methods to log and retrieve evidence for SAR sentences.
    """

    def __init__(self, db: Session):
        self.db = db

    def log_sql_query(
        self,
        sar_id: str,
        sentence_index: int,
        query: str,
        results: list[dict[str, Any]],
        execution_time_ms: float = 0,
    ):
        """Log a SQL query execution."""
        return crud.create_audit_log(
            db=self.db,
            sar_id=sar_id,
            sentence_index=sentence_index,
            entry_type="sql_query",
            data={
                "query": query,
                "results": results,
                "execution_time_ms": execution_time_ms,
                "result_count": len(results),
            },
            confidence=1.0,
        )

    def log_fact_verification(
        self,
        sar_id: str,
        sentence_index: int,
        claim: str,
        expected_value: Any,
        actual_value: Any,
        is_verified: bool,
    ):
        """Log a fact verification result."""
        confidence = 1.0 if is_verified else 0.0

        return crud.create_audit_log(
            db=self.db,
            sar_id=sar_id,
            sentence_index=sentence_index,
            entry_type="fact_verification",
            data={
                "claim": claim,
                "expected": expected_value,
                "actual": actual_value,
                "verified": is_verified,
                "confidence": confidence,
            },
            confidence=confidence,
        )

    def log_llm_generation(
        self,
        sar_id: str,
        sentence_index: int,
        prompt: str,
        response: str,
        reasoning: str,
        model: str = "llama-3.1-8b",
        temperature: float = 0.3,
        tokens_used: dict = None,
    ):
        """Log an LLM generation call."""
        return crud.create_audit_log(
            db=self.db,
            sar_id=sar_id,
            sentence_index=sentence_index,
            entry_type="llm_generation",
            data={
                "prompt": prompt,
                "response": response,
                "reasoning": reasoning,
                "model": model,
                "temperature": temperature,
                "tokens_used": tokens_used or {},
            },
            confidence=0.95,  # LLM outputs have inherent uncertainty
        )

    def log_rag_retrieval(
        self,
        sar_id: str,
        sentence_index: int,
        query: str,
        retrieved_docs: list[str],
        similarity_scores: list[float],
    ):
        """Log a RAG retrieval operation."""
        return crud.create_audit_log(
            db=self.db,
            sar_id=sar_id,
            sentence_index=sentence_index,
            entry_type="rag_retrieval",
            data={
                "query": query,
                "retrieved_docs": retrieved_docs,
                "similarity_scores": similarity_scores,
                "doc_count": len(retrieved_docs),
            },
            confidence=max(similarity_scores) if similarity_scores else 0.5,
        )

    def log_typology_classification(
        self,
        sar_id: str,
        sentence_index: int,
        typology: str,
        fincen_code: str,
        confidence: float,
        indicators: list[str],
    ):
        """Log a typology classification decision."""
        return crud.create_audit_log(
            db=self.db,
            sar_id=sar_id,
            sentence_index=sentence_index,
            entry_type="typology_classification",
            data={
                "typology": typology,
                "fincen_code": fincen_code,
                "confidence": confidence,
                "indicators": indicators,
            },
            confidence=confidence,
        )

    def get_sentence_evidence(self, sar_id: str, sentence_index: int) -> dict:
        """Get all audit evidence for a specific sentence."""
        logs = crud.get_audit_logs_by_sentence(self.db, sar_id, sentence_index)

        evidence = {
            "sql_queries": [],
            "fact_verifications": [],
            "llm_generations": [],
            "rag_retrievals": [],
            "overall_confidence": 1.0,
        }

        confidences = []

        for log in logs:
            data = log.data or {}

            if log.entry_type == "sql_query":
                evidence["sql_queries"].append(data)
            elif log.entry_type == "fact_verification":
                evidence["fact_verifications"].append(data)
                confidences.append(data.get("confidence", 1.0))
            elif log.entry_type == "llm_generation":
                evidence["llm_generations"].append(data)
            elif log.entry_type == "rag_retrieval":
                evidence["rag_retrievals"].append(data)

        if confidences:
            evidence["overall_confidence"] = min(confidences)

        return evidence

    def get_full_audit_trail(self, sar_id: str) -> list[dict]:
        """Get the complete audit trail for a SAR."""
        logs = crud.get_audit_logs_by_sar(self.db, sar_id)

        return [
            {
                "id": log.id,
                "sentence_index": log.sentence_index,
                "entry_type": log.entry_type,
                "data": log.data,
                "confidence": log.confidence,
                "timestamp": log.timestamp.isoformat(),
            }
            for log in logs
        ]
