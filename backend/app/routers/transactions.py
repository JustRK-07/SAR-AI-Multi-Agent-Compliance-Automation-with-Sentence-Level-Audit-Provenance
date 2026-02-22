from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict

from app.db.database import get_db
from app.db import crud
from app.models.transaction import (
    Transaction,
    TransactionListResponse,
    TransactionGraphResponse,
    GraphNode,
    GraphEdge,
    TransactionType,
)

router = APIRouter()


@router.get("/", response_model=TransactionListResponse)
def list_transactions(
    alert_id: str = Query(..., description="Alert ID to get transactions for"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Get all transactions associated with an alert.
    """
    # Verify alert exists
    alert = crud.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    transactions = crud.get_transactions_by_alert(db, alert_id, limit)
    stats = crud.get_transaction_stats(db, alert_id)

    transaction_responses = [
        Transaction(
            id=txn.id,
            alert_id=txn.alert_id,
            date=txn.date,
            amount=txn.amount,
            type=TransactionType(txn.type),
            direction=txn.direction,
            source_account=txn.source_account,
            destination_account=txn.destination_account,
            source_location=txn.source_location,
            destination_location=txn.destination_location,
            description=txn.description,
            is_suspicious=txn.is_suspicious,
        )
        for txn in transactions
    ]

    return TransactionListResponse(
        transactions=transaction_responses,
        total=stats["transaction_count"],
        total_amount=stats["total_amount"],
        date_range=stats["date_range"],
    )


@router.get("/graph/{alert_id}", response_model=TransactionGraphResponse)
def get_transaction_graph(
    alert_id: str,
    db: Session = Depends(get_db),
):
    """
    Get transaction flow graph data for React Flow visualization.
    Returns nodes (accounts) and edges (transactions).
    """
    # Verify alert exists
    alert = crud.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    graph_data = crud.get_transaction_graph_data(db, alert_id)

    # Convert to response models
    accounts = [
        GraphNode(
            id=acc["id"],
            label=acc["label"],
            location=acc.get("location"),
            is_subject=acc.get("is_subject", False),
            is_high_risk=acc.get("is_high_risk", False),
        )
        for acc in graph_data["accounts"]
    ]

    transactions = [
        GraphEdge(
            id=txn["id"],
            source=txn["source"],
            target=txn["target"],
            amount=txn["amount"],
            date=txn["date"],
            type=TransactionType(txn["type"]),
        )
        for txn in graph_data["transactions"]
    ]

    # Detect patterns
    patterns_detected = detect_patterns(accounts, transactions)

    return TransactionGraphResponse(
        accounts=accounts,
        transactions=transactions,
        patterns_detected=patterns_detected,
    )


def detect_patterns(accounts: list[GraphNode], transactions: list[GraphEdge]) -> list[str]:
    """
    Analyze transaction graph for suspicious patterns.
    Performs comprehensive timestamp and flow analysis.
    """
    patterns = []

    # Count unique sources to subject
    subject_accounts = [a.id for a in accounts if a.is_subject]
    if not subject_accounts:
        return patterns

    subject_id = subject_accounts[0]

    # Pattern 1: Multiple sources to single destination (Collection Pattern)
    inbound_sources = set()
    for txn in transactions:
        if txn.target == subject_id:
            inbound_sources.add(txn.source)

    if len(inbound_sources) > 10:
        patterns.append(f"Collection Pattern: {len(inbound_sources)} unique sources")

    # Pattern 2: High-risk destinations
    high_risk_destinations = [a for a in accounts if a.is_high_risk]
    if high_risk_destinations:
        patterns.append(
            f"High-Risk Jurisdictions: {', '.join(a.location or 'Unknown' for a in high_risk_destinations)}"
        )

    # Pattern 3: Rapid outbound after inbound (Layering) - with timestamp analysis
    layering_detected = _detect_layering_pattern(transactions, subject_id)
    if layering_detected:
        patterns.append(layering_detected)

    # Pattern 4: Structuring (multiple similar amounts below reporting threshold)
    structuring_pattern = _detect_structuring_pattern(transactions)
    if structuring_pattern:
        patterns.append(structuring_pattern)

    # Pattern 5: Round-trip transactions (funds returning to origin)
    round_trip = _detect_round_trip_pattern(transactions)
    if round_trip:
        patterns.append(round_trip)

    # Pattern 6: Rapid succession transactions (multiple in short timeframe)
    rapid_txns = _detect_rapid_transactions(transactions)
    if rapid_txns:
        patterns.append(rapid_txns)

    return patterns


def _detect_layering_pattern(transactions: list[GraphEdge], subject_id: str) -> Optional[str]:
    """
    Detect layering pattern by analyzing timestamps.
    Layering: Rapid movement of funds through multiple accounts in short time.
    """
    # Group transactions by date
    inbound_by_date = defaultdict(list)
    outbound_by_date = defaultdict(list)

    for txn in transactions:
        txn_date = txn.date if isinstance(txn.date, datetime) else datetime.fromisoformat(str(txn.date).replace('Z', '+00:00'))

        if txn.target == subject_id:
            inbound_by_date[txn_date.date()].append(txn)
        elif txn.source == subject_id:
            outbound_by_date[txn_date.date()].append(txn)

    # Check for same-day or next-day outbound after inbound
    layering_days = 0
    total_layered_amount = 0

    for date, inbound_txns in inbound_by_date.items():
        # Check same day
        if date in outbound_by_date:
            inbound_total = sum(t.amount for t in inbound_txns)
            outbound_total = sum(t.amount for t in outbound_by_date[date])
            if outbound_total >= inbound_total * 0.5:  # At least 50% moved out same day
                layering_days += 1
                total_layered_amount += outbound_total

        # Check next day
        next_day = date + timedelta(days=1)
        if next_day in outbound_by_date:
            inbound_total = sum(t.amount for t in inbound_txns)
            outbound_total = sum(t.amount for t in outbound_by_date[next_day])
            if outbound_total >= inbound_total * 0.5:
                layering_days += 1
                total_layered_amount += outbound_total

    if layering_days >= 3:
        return f"Layering: Rapid fund movement detected ({layering_days} instances, ₹{total_layered_amount:,.0f} moved within 24hrs of receipt)"

    return None


def _detect_structuring_pattern(transactions: list[GraphEdge]) -> Optional[str]:
    """
    Detect structuring pattern (smurfing).
    Multiple transactions just below CTR threshold (₹10 lakh / $10,000).
    """
    # CTR threshold in INR (10 lakh)
    CTR_THRESHOLD = 1000000
    STRUCTURING_RANGE = (CTR_THRESHOLD * 0.85, CTR_THRESHOLD * 0.99)

    structured_txns = [
        txn for txn in transactions
        if STRUCTURING_RANGE[0] <= txn.amount <= STRUCTURING_RANGE[1]
    ]

    if len(structured_txns) >= 3:
        total_structured = sum(t.amount for t in structured_txns)
        return f"Structuring: {len(structured_txns)} transactions just below CTR threshold (₹{total_structured:,.0f} total)"

    # Also check for multiple smaller amounts that together exceed threshold
    amounts = [txn.amount for txn in transactions]
    if amounts:
        avg_amount = sum(amounts) / len(amounts)
        # Check if many transactions cluster around same amount
        similar_amounts = [a for a in amounts if abs(a - avg_amount) < avg_amount * 0.1]
        if len(similar_amounts) >= 5 and avg_amount < CTR_THRESHOLD:
            return f"Structuring: {len(similar_amounts)} similar-amount transactions averaging ₹{avg_amount:,.0f}"

    return None


def _detect_round_trip_pattern(transactions: list[GraphEdge]) -> Optional[str]:
    """
    Detect round-trip transactions where funds return to original source.
    """
    # Build a map of source->targets and target->sources
    flows = defaultdict(lambda: {"sent_to": set(), "received_from": set()})

    for txn in transactions:
        flows[txn.source]["sent_to"].add(txn.target)
        flows[txn.target]["received_from"].add(txn.source)

    # Find accounts that both sent to and received from the same counterparty
    round_trips = []
    for account, flow in flows.items():
        common = flow["sent_to"] & flow["received_from"]
        if common:
            round_trips.extend(list(common))

    if len(round_trips) >= 2:
        return f"Round-Trip: Funds circulating between {len(set(round_trips))} accounts"

    return None


def _detect_rapid_transactions(transactions: list[GraphEdge]) -> Optional[str]:
    """
    Detect rapid succession transactions (many transactions in short timeframe).
    """
    if len(transactions) < 5:
        return None

    # Sort transactions by date
    sorted_txns = sorted(
        transactions,
        key=lambda t: t.date if isinstance(t.date, datetime) else datetime.fromisoformat(str(t.date).replace('Z', '+00:00'))
    )

    # Check for bursts of activity
    burst_threshold = timedelta(hours=24)
    burst_count_threshold = 5

    for i in range(len(sorted_txns) - burst_count_threshold + 1):
        start_date = sorted_txns[i].date
        end_date = sorted_txns[i + burst_count_threshold - 1].date

        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        if (end_date - start_date) <= burst_threshold:
            burst_amount = sum(sorted_txns[j].amount for j in range(i, i + burst_count_threshold))
            return f"Rapid Activity: {burst_count_threshold}+ transactions within 24 hours (₹{burst_amount:,.0f})"

    return None
