from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional


class AlertStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    SAR_GENERATED = "sar_generated"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    DISMISSED = "dismissed"


class Alert(BaseModel):
    id: str
    trigger_date: datetime
    scenario: str  # e.g., "Structuring", "Layering", "Rapid Movement"
    risk_score: int  # 0-100
    customer_id: str
    customer_name: str
    account_number: str
    flagged_transaction_ids: list[str]
    status: AlertStatus = AlertStatus.PENDING
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    id: str
    trigger_date: datetime
    scenario: str
    risk_score: int
    customer_id: str
    customer_name: str
    account_number: str
    status: AlertStatus
    transaction_count: int
    total_amount: float
    assigned_to: Optional[str] = None
    created_at: datetime


class AlertListResponse(BaseModel):
    alerts: list[AlertResponse]
    total: int
    page: int
    page_size: int
