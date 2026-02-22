from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional


class SARStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DRAFT = "draft"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    REJECTED = "rejected"


class SARGenerateRequest(BaseModel):
    alert_id: str


class SARGenerateResponse(BaseModel):
    task_id: str
    sar_id: str
    status: SARStatus
    message: str


class SAR(BaseModel):
    id: str
    alert_id: str
    narrative: str
    typology: str
    fincen_code: str
    status: SARStatus
    confidence_score: float
    sentence_count: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SARResponse(BaseModel):
    id: str
    alert_id: str
    narrative: str
    typology: str
    fincen_code: str
    status: SARStatus
    confidence_score: float
    sentence_count: int
    sentences: list[str]  # Split narrative for interactive UI
    created_at: datetime
    updated_at: datetime
    customer_name: str
    account_number: str
    total_amount: float
    transaction_count: int


class SARUpdateRequest(BaseModel):
    narrative: Optional[str] = None
    status: Optional[SARStatus] = None


class SARSubmitResponse(BaseModel):
    sar_id: str
    filing_id: str
    submitted_at: datetime
    status: str
