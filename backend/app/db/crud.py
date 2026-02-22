from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime
import uuid

from app.db.models import AlertDB, CustomerDB, TransactionDB, SARDB, AuditLogDB


# ============== ALERTS ==============

def get_alerts(
    db: Session,
    status: Optional[str] = None,
    scenario: Optional[str] = None,
    min_risk: int = 0,
    skip: int = 0,
    limit: int = 20,
):
    query = db.query(AlertDB)

    if status:
        query = query.filter(AlertDB.status == status)
    if scenario:
        query = query.filter(AlertDB.scenario == scenario)
    if min_risk > 0:
        query = query.filter(AlertDB.risk_score >= min_risk)

    total = query.count()
    alerts = query.order_by(AlertDB.risk_score.desc()).offset(skip).limit(limit).all()

    return alerts, total


def get_alert_by_id(db: Session, alert_id: str) -> Optional[AlertDB]:
    return db.query(AlertDB).filter(AlertDB.id == alert_id).first()


def update_alert_status(db: Session, alert_id: str, status: str) -> Optional[AlertDB]:
    alert = get_alert_by_id(db, alert_id)
    if alert:
        alert.status = status
        alert.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(alert)
    return alert


# ============== CUSTOMERS ==============

def get_customer_by_id(db: Session, customer_id: str) -> Optional[CustomerDB]:
    return db.query(CustomerDB).filter(CustomerDB.id == customer_id).first()


def get_customer_by_account(db: Session, account_number: str) -> Optional[CustomerDB]:
    return db.query(CustomerDB).filter(CustomerDB.account_number == account_number).first()


# ============== TRANSACTIONS ==============

def get_transactions_by_alert(
    db: Session,
    alert_id: str,
    limit: int = 100,
):
    transactions = (
        db.query(TransactionDB)
        .filter(TransactionDB.alert_id == alert_id)
        .order_by(TransactionDB.date)
        .limit(limit)
        .all()
    )
    return transactions


def get_transaction_stats(db: Session, alert_id: str) -> dict:
    result = (
        db.query(
            func.count(TransactionDB.id).label("count"),
            func.sum(TransactionDB.amount).label("total"),
            func.min(TransactionDB.date).label("min_date"),
            func.max(TransactionDB.date).label("max_date"),
            func.count(func.distinct(TransactionDB.source_account)).label("unique_sources"),
        )
        .filter(TransactionDB.alert_id == alert_id)
        .first()
    )

    return {
        "transaction_count": result.count or 0,
        "total_amount": float(result.total or 0),
        "date_range": (result.min_date, result.max_date),
        "unique_sources": result.unique_sources or 0,
    }


def get_transaction_graph_data(db: Session, alert_id: str) -> dict:
    """Get transaction data formatted for graph visualization."""
    transactions = get_transactions_by_alert(db, alert_id)
    alert = get_alert_by_id(db, alert_id)

    # Build unique accounts
    accounts = {}
    subject_account = alert.customer.account_number if alert and alert.customer else None

    HIGH_RISK_LOCATIONS = ["Cayman Islands", "Panama", "British Virgin Islands", "Switzerland"]

    for txn in transactions:
        # Add source account
        if txn.source_account and txn.source_account not in accounts:
            accounts[txn.source_account] = {
                "id": txn.source_account,
                "label": txn.source_account[-4:],  # Last 4 digits
                "location": txn.source_location,
                "is_subject": txn.source_account == subject_account,
                "is_high_risk": txn.source_location in HIGH_RISK_LOCATIONS,
            }

        # Add destination account
        if txn.destination_account and txn.destination_account not in accounts:
            accounts[txn.destination_account] = {
                "id": txn.destination_account,
                "label": txn.destination_account[-4:],
                "location": txn.destination_location,
                "is_subject": txn.destination_account == subject_account,
                "is_high_risk": txn.destination_location in HIGH_RISK_LOCATIONS,
            }

    # Format edges
    edges = [
        {
            "id": txn.id,
            "source": txn.source_account,
            "target": txn.destination_account,
            "amount": txn.amount,
            "date": txn.date.isoformat(),
            "type": txn.type,
        }
        for txn in transactions
        if txn.source_account and txn.destination_account
    ]

    return {
        "accounts": list(accounts.values()),
        "transactions": edges,
    }


# ============== SARs ==============

def create_sar(
    db: Session,
    alert_id: str,
    narrative: str,
    typology: str,
    fincen_code: str,
    confidence_score: float,
) -> SARDB:
    sar_id = f"SAR_{datetime.now().strftime('%Y')}_{uuid.uuid4().hex[:8].upper()}"

    sentences = [s.strip() for s in narrative.split('.') if s.strip()]

    sar = SARDB(
        id=sar_id,
        alert_id=alert_id,
        narrative=narrative,
        typology=typology,
        fincen_code=fincen_code,
        status="draft",
        confidence_score=confidence_score,
        sentence_count=len(sentences),
    )

    db.add(sar)
    db.commit()
    db.refresh(sar)

    # Update alert status
    update_alert_status(db, alert_id, "sar_generated")

    return sar


def get_sar_by_id(db: Session, sar_id: str) -> Optional[SARDB]:
    return db.query(SARDB).filter(SARDB.id == sar_id).first()


def get_sar_by_alert(db: Session, alert_id: str) -> Optional[SARDB]:
    return db.query(SARDB).filter(SARDB.alert_id == alert_id).first()


def update_sar(
    db: Session,
    sar_id: str,
    narrative: Optional[str] = None,
    status: Optional[str] = None,
) -> Optional[SARDB]:
    sar = get_sar_by_id(db, sar_id)
    if not sar:
        return None

    if narrative is not None:
        sar.narrative = narrative
        sentences = [s.strip() for s in narrative.split('.') if s.strip()]
        sar.sentence_count = len(sentences)

    if status is not None:
        sar.status = status

    sar.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(sar)
    return sar


def submit_sar(db: Session, sar_id: str, approved_by: str) -> Optional[SARDB]:
    sar = get_sar_by_id(db, sar_id)
    if not sar:
        return None

    sar.status = "submitted"
    sar.approved_by = approved_by
    sar.approved_at = datetime.utcnow()
    sar.submitted_at = datetime.utcnow()
    sar.filing_id = f"FINCEN_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:6].upper()}"

    db.commit()
    db.refresh(sar)

    # Update alert status
    update_alert_status(db, sar.alert_id, "submitted")

    return sar


# ============== AUDIT LOGS ==============

def create_audit_log(
    db: Session,
    sar_id: str,
    sentence_index: int,
    entry_type: str,
    data: dict,
    confidence: float = 1.0,
) -> AuditLogDB:
    log_id = f"AUD_{uuid.uuid4().hex[:12]}"

    audit_log = AuditLogDB(
        id=log_id,
        sar_id=sar_id,
        sentence_index=sentence_index,
        entry_type=entry_type,
        data=data,
        confidence=confidence,
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log


def get_audit_logs_by_sar(db: Session, sar_id: str) -> list[AuditLogDB]:
    return (
        db.query(AuditLogDB)
        .filter(AuditLogDB.sar_id == sar_id)
        .order_by(AuditLogDB.sentence_index, AuditLogDB.timestamp)
        .all()
    )


def get_audit_logs_by_sentence(
    db: Session, sar_id: str, sentence_index: int
) -> list[AuditLogDB]:
    return (
        db.query(AuditLogDB)
        .filter(AuditLogDB.sar_id == sar_id, AuditLogDB.sentence_index == sentence_index)
        .order_by(AuditLogDB.timestamp)
        .all()
    )
