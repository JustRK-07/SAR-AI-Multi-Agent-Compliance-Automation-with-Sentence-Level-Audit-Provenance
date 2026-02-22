from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, ForeignKey, Text, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class AlertStatusEnum(enum.Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    SAR_GENERATED = "sar_generated"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    DISMISSED = "dismissed"


class SARStatusEnum(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DRAFT = "draft"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    REJECTED = "rejected"


class CustomerDB(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    dob = Column(DateTime)
    pan = Column(String)
    address = Column(Text)
    occupation = Column(String)
    income_source = Column(String)
    account_number = Column(String, unique=True)
    account_type = Column(String)
    account_open_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    alerts = relationship("AlertDB", back_populates="customer")
    transactions = relationship("TransactionDB", back_populates="customer")


class AlertDB(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True)
    trigger_date = Column(DateTime, nullable=False)
    scenario = Column(String, nullable=False)  # Structuring, Layering, etc.
    risk_score = Column(Integer, nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"))
    status = Column(String, default="pending")
    assigned_to = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("CustomerDB", back_populates="alerts")
    transactions = relationship("TransactionDB", back_populates="alert")
    sars = relationship("SARDB", back_populates="alert")


class TransactionDB(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True)
    alert_id = Column(String, ForeignKey("alerts.id"))
    customer_id = Column(String, ForeignKey("customers.id"))
    date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)  # CASH_DEPOSIT, WIRE_TRANSFER, etc.
    direction = Column(String, nullable=False)  # INBOUND, OUTBOUND
    source_account = Column(String)
    destination_account = Column(String)
    source_location = Column(String)
    destination_location = Column(String)
    description = Column(Text)
    is_suspicious = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    alert = relationship("AlertDB", back_populates="transactions")
    customer = relationship("CustomerDB", back_populates="transactions")


class SARDB(Base):
    __tablename__ = "sars"

    id = Column(String, primary_key=True)
    alert_id = Column(String, ForeignKey("alerts.id"))
    narrative = Column(Text)
    typology = Column(String)
    fincen_code = Column(String)
    status = Column(String, default="pending")
    confidence_score = Column(Float, default=0.0)
    sentence_count = Column(Integer, default=0)
    created_by = Column(String)
    approved_by = Column(String)
    approved_at = Column(DateTime)
    filing_id = Column(String)
    submitted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    alert = relationship("AlertDB", back_populates="sars")
    audit_logs = relationship("AuditLogDB", back_populates="sar")


class AuditLogDB(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True)
    sar_id = Column(String, ForeignKey("sars.id"))
    sentence_index = Column(Integer)
    entry_type = Column(String)  # sql_query, llm_generation, fact_verification
    data = Column(JSON)  # Stores query, results, prompts, etc.
    confidence = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    sar = relationship("SARDB", back_populates="audit_logs")


class KnowledgeDocDB(Base):
    __tablename__ = "knowledge_docs"

    id = Column(String, primary_key=True)
    doc_type = Column(String)  # fincen_typology, fatf_recommendation, historical_sar
    title = Column(String)
    content = Column(Text)
    doc_metadata = Column(JSON)  # renamed from 'metadata' (reserved in SQLAlchemy)
    created_at = Column(DateTime, default=datetime.utcnow)
