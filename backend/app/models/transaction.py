from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional


class TransactionType(str, Enum):
    CASH_DEPOSIT = "CASH_DEPOSIT"
    CASH_WITHDRAWAL = "CASH_WITHDRAWAL"
    WIRE_TRANSFER = "WIRE_TRANSFER"
    ACH_TRANSFER = "ACH_TRANSFER"
    CHECK_DEPOSIT = "CHECK_DEPOSIT"
    INTERNAL_TRANSFER = "INTERNAL_TRANSFER"


class TransactionDirection(str, Enum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"


class Transaction(BaseModel):
    id: str
    alert_id: str
    date: datetime
    amount: float
    type: TransactionType
    direction: TransactionDirection
    source_account: str
    destination_account: str
    source_location: Optional[str] = None
    destination_location: Optional[str] = None
    description: Optional[str] = None
    is_suspicious: bool = False

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    transactions: list[Transaction]
    total: int
    total_amount: float
    date_range: tuple[datetime, datetime]


class GraphNode(BaseModel):
    id: str
    label: str
    location: Optional[str] = None
    is_subject: bool = False
    is_high_risk: bool = False
    balance: Optional[float] = None


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    amount: float
    date: datetime
    type: TransactionType


class TransactionGraphResponse(BaseModel):
    accounts: list[GraphNode]
    transactions: list[GraphEdge]
    patterns_detected: list[str]
