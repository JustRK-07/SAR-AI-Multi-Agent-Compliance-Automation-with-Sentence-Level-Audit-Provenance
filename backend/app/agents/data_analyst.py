from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Any

from app.db import crud


class DataAnalystAgent:
    """
    Agent 1: Data Analyst

    Responsible for:
    - Executing SQL queries to extract transaction facts
    - Aggregating statistics (counts, sums, averages)
    - Identifying anomalies compared to historical baseline
    """

    def __init__(self, db: Session):
        self.db = db

    async def extract_facts(self, alert_id: str) -> dict[str, Any]:
        """
        Extract all relevant facts for a given alert.

        Returns:
            Dictionary containing all facts needed for SAR generation
        """
        facts = {
            "alert_id": alert_id,
            "queries": [],
        }

        # Get alert info
        alert = crud.get_alert_by_id(self.db, alert_id)
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        facts["scenario"] = alert.scenario
        facts["risk_score"] = alert.risk_score
        facts["trigger_date"] = alert.trigger_date.isoformat()

        # Get customer info
        if alert.customer:
            facts["customer"] = {
                "id": alert.customer.id,
                "name": alert.customer.name,
                "pan": alert.customer.pan,
                "account_number": alert.customer.account_number,
                "occupation": alert.customer.occupation,
                "address": alert.customer.address,
                "account_open_date": alert.customer.account_open_date.isoformat() if alert.customer.account_open_date else None,
            }

        # Execute transaction queries
        stats = await self._get_transaction_stats(alert_id)
        facts.update(stats)

        # Get transaction patterns
        patterns = await self._analyze_patterns(alert_id)
        facts["patterns"] = patterns

        # Get transaction details
        transactions = await self._get_transaction_details(alert_id)
        facts["transactions"] = transactions

        return facts

    async def _get_transaction_stats(self, alert_id: str) -> dict:
        """Get aggregate transaction statistics."""
        stats = crud.get_transaction_stats(self.db, alert_id)

        # Log query for audit trail
        query = f"""
        SELECT
            COUNT(*) as transaction_count,
            SUM(amount) as total_amount,
            MIN(date) as min_date,
            MAX(date) as max_date,
            COUNT(DISTINCT source_account) as unique_sources
        FROM transactions
        WHERE alert_id = '{alert_id}'
        """

        return {
            "transaction_count": stats["transaction_count"],
            "total_amount": stats["total_amount"],
            "date_range": (
                stats["date_range"][0].isoformat() if stats["date_range"][0] else None,
                stats["date_range"][1].isoformat() if stats["date_range"][1] else None,
            ),
            "unique_sources": stats["unique_sources"],
            "queries": [{"query": query, "results": [stats]}],
        }

    async def _analyze_patterns(self, alert_id: str) -> list[str]:
        """Identify suspicious patterns in transactions."""
        patterns = []
        transactions = crud.get_transactions_by_alert(self.db, alert_id)

        if not transactions:
            return patterns

        # Pattern 1: Structuring (multiple transactions below threshold)
        amounts = [txn.amount for txn in transactions]
        below_threshold = sum(1 for a in amounts if 9000 <= a <= 10000)
        if below_threshold > len(amounts) * 0.5:
            patterns.append("Structuring: Multiple transactions just below reporting threshold")

        # Pattern 2: Rapid movement (multiple transactions in short period)
        if len(transactions) > 10:
            dates = sorted([txn.date for txn in transactions])
            if dates:
                days_span = (dates[-1] - dates[0]).days
                if days_span <= 7 and len(transactions) > 20:
                    patterns.append(f"Rapid Movement: {len(transactions)} transactions in {days_span} days")

        # Pattern 3: Multiple unique sources
        unique_sources = set(txn.source_account for txn in transactions if txn.source_account)
        if len(unique_sources) > 10:
            patterns.append(f"Collection Account: Funds from {len(unique_sources)} unique sources")

        # Pattern 4: High-risk destinations
        high_risk_locations = ["Cayman Islands", "Panama", "British Virgin Islands", "Switzerland"]
        high_risk_txns = [
            txn for txn in transactions
            if txn.destination_location in high_risk_locations
        ]
        if high_risk_txns:
            total_high_risk = sum(txn.amount for txn in high_risk_txns)
            patterns.append(f"High-Risk Jurisdictions: ₹{total_high_risk:,.0f} to offshore locations")

        # Pattern 5: Round amounts
        round_amounts = sum(1 for a in amounts if a % 1000 == 0)
        if round_amounts > len(amounts) * 0.7:
            patterns.append("Round Amounts: Majority of transactions are round numbers")

        return patterns

    async def _get_transaction_details(self, alert_id: str, limit: int = 10) -> list[dict]:
        """Get detailed transaction information for narrative."""
        transactions = crud.get_transactions_by_alert(self.db, alert_id, limit)

        return [
            {
                "id": txn.id,
                "date": txn.date.isoformat(),
                "amount": txn.amount,
                "type": txn.type,
                "direction": txn.direction,
                "source": txn.source_account,
                "destination": txn.destination_account,
                "source_location": txn.source_location,
                "destination_location": txn.destination_location,
            }
            for txn in transactions
        ]
