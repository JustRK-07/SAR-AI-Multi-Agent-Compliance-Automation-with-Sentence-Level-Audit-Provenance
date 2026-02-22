from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any


class AuditEntry(BaseModel):
    id: str
    sar_id: str
    sentence_index: int
    entry_type: str  # "sql_query", "llm_generation", "fact_verification", "rag_retrieval"
    timestamp: datetime
    data: dict[str, Any]

    class Config:
        from_attributes = True


class QueryResult(BaseModel):
    query: str
    results: list[dict[str, Any]]
    execution_time_ms: float


class ClaimVerification(BaseModel):
    claim: str
    expected_value: Any
    actual_value: Any
    is_verified: bool
    confidence: float


class AuditEvidence(BaseModel):
    sentence: str
    sentence_index: int
    data_source: str
    sql_query: str
    query_results: list[dict[str, Any]]
    confidence: float
    reasoning: str
    claims: list[ClaimVerification]
    llm_prompt: Optional[str] = None
    llm_response: Optional[str] = None
    template_used: Optional[str] = None
    retrieved_documents: Optional[list[str]] = None


class AuditTrailResponse(BaseModel):
    sar_id: str
    total_sentences: int
    verified_sentences: int
    overall_confidence: float
    entries: list[AuditEvidence]
    generation_timestamp: datetime
    total_queries_executed: int
    total_tokens_used: int
