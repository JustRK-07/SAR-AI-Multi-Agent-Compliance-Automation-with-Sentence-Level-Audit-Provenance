"""
IBM AML Dataset Import Script
=============================

Converts IBM Synthetic Transactions dataset to SAR Narrative Generator format.

Usage:
    python import_ibm_aml.py data/HI-Small_Trans.csv

The script will:
1. Read IBM format CSV
2. Create customers from unique accounts
3. Create alerts for suspicious patterns
4. Import transactions linked to alerts
"""

import csv
import sys
import uuid
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.database import SessionLocal, create_tables
from app.db.models import CustomerDB, AlertDB, TransactionDB


# AML Scenario classification based on patterns
SCENARIOS = {
    'structuring': 'Structuring',
    'layering': 'Layering',
    'rapid_movement': 'Rapid Movement',
    'collection': 'Collection Account',
    'round_trip': 'Round Trip',
}

# High-risk locations (for demo purposes)
HIGH_RISK_LOCATIONS = [
    'Cayman Islands', 'Panama', 'British Virgin Islands',
    'Switzerland', 'Luxembourg', 'Dubai', 'Singapore'
]


def generate_id(prefix: str, seed: str) -> str:
    """Generate consistent ID from seed."""
    hash_val = hashlib.md5(seed.encode()).hexdigest()[:8].upper()
    return f"{prefix}_{hash_val}"


def parse_timestamp(ts: str) -> datetime:
    """Parse IBM timestamp format."""
    try:
        # IBM format: integer representing step/time
        step = int(ts)
        # Convert to datetime (assuming each step is 1 hour from base date)
        base_date = datetime(2024, 1, 1)
        return base_date + timedelta(hours=step)
    except:
        return datetime.now()


def classify_scenario(transactions: list) -> tuple[str, int]:
    """Classify AML scenario based on transaction patterns."""
    amounts = [t['amount'] for t in transactions]

    # Check for structuring (many transactions just below threshold)
    threshold = 10000  # Common CTR threshold
    below_threshold = sum(1 for a in amounts if threshold * 0.8 < a < threshold)
    if below_threshold >= 3:
        return 'Structuring', min(95, 70 + below_threshold * 3)

    # Check for layering (rapid in/out)
    inbound = sum(1 for t in transactions if t['direction'] == 'INBOUND')
    outbound = sum(1 for t in transactions if t['direction'] == 'OUTBOUND')
    if inbound > 0 and outbound > 0 and len(transactions) > 5:
        return 'Layering', min(95, 75 + len(transactions))

    # Check for collection (many inbound from different sources)
    sources = set(t['source'] for t in transactions if t['direction'] == 'INBOUND')
    if len(sources) > 5:
        return 'Collection Account', min(95, 70 + len(sources) * 2)

    # Check for rapid movement (large amounts quickly moved)
    total = sum(amounts)
    if total > 100000 and len(transactions) > 3:
        return 'Rapid Movement', min(95, 70 + int(total / 50000))

    # Default
    return 'Suspicious Activity', 70


def import_ibm_dataset(csv_path: str, max_alerts: int = 50, max_txn_per_alert: int = 50):
    """
    Import IBM AML dataset.

    Args:
        csv_path: Path to HI-Small_Trans.csv or similar
        max_alerts: Maximum number of alerts to create (for demo)
        max_txn_per_alert: Maximum transactions per alert
    """
    print(f"Reading {csv_path}...")

    # Group transactions by account (to find suspicious accounts)
    account_transactions = defaultdict(list)
    suspicious_accounts = set()

    # First pass: read and group transactions
    row_count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        # IBM CSV columns:
        # Timestamp, From Bank, From Account, To Bank, To Account,
        # Amount Received, Receiving Currency, Amount Paid, Payment Currency,
        # Payment Format, Is Laundering

        for row in reader:
            row_count += 1
            if row_count % 100000 == 0:
                print(f"  Processed {row_count:,} rows...")

            is_suspicious = row.get('Is Laundering', '0') == '1'
            from_account = row.get('From Account', row.get('Account', ''))
            to_account = row.get('To Account', '')

            # Track suspicious accounts
            if is_suspicious:
                suspicious_accounts.add(from_account)

            # Store transaction
            txn_data = {
                'timestamp': row.get('Timestamp', '0'),
                'from_bank': row.get('From Bank', ''),
                'from_account': from_account,
                'to_bank': row.get('To Bank', ''),
                'to_account': to_account,
                'amount': float(row.get('Amount Paid', row.get('Amount Received', 0)) or 0),
                'currency': row.get('Payment Currency', row.get('Receiving Currency', 'USD')),
                'payment_format': row.get('Payment Format', 'Wire'),
                'is_suspicious': is_suspicious,
                'source': from_account,
                'direction': 'OUTBOUND',
            }

            account_transactions[from_account].append(txn_data)

            # Also track as inbound for destination
            inbound_txn = txn_data.copy()
            inbound_txn['direction'] = 'INBOUND'
            inbound_txn['source'] = from_account
            account_transactions[to_account].append(inbound_txn)

    print(f"Total rows: {row_count:,}")
    print(f"Unique accounts: {len(account_transactions):,}")
    print(f"Suspicious accounts: {len(suspicious_accounts):,}")

    # Find accounts with suspicious activity (for alerts)
    alert_candidates = []
    for account, txns in account_transactions.items():
        suspicious_txns = [t for t in txns if t['is_suspicious']]
        if len(suspicious_txns) >= 3:  # At least 3 suspicious transactions
            total_suspicious = sum(t['amount'] for t in suspicious_txns)
            alert_candidates.append({
                'account': account,
                'transactions': suspicious_txns[:max_txn_per_alert],
                'total': total_suspicious,
                'count': len(suspicious_txns),
            })

    # Sort by total suspicious amount and take top N
    alert_candidates.sort(key=lambda x: x['total'], reverse=True)
    alert_candidates = alert_candidates[:max_alerts]

    print(f"Creating {len(alert_candidates)} alerts...")

    # Create database records
    print("Ensuring database tables exist...")
    create_tables()

    db = SessionLocal()

    try:
        # Clear existing data
        print("Clearing existing data...")
        db.query(TransactionDB).delete()
        db.query(AlertDB).delete()
        db.query(CustomerDB).delete()
        db.commit()

        customers_created = 0
        alerts_created = 0
        transactions_created = 0

        for i, candidate in enumerate(alert_candidates):
            account = candidate['account']
            txns = candidate['transactions']

            # Create customer
            customer_id = generate_id('CUST', account)
            customer = CustomerDB(
                id=customer_id,
                name=f"Account Holder {account[-6:]}",  # Anonymous name
                account_number=account,
                account_type='SAVINGS',
                occupation='Not Disclosed',
            )
            db.merge(customer)
            customers_created += 1

            # Classify scenario
            scenario, risk_score = classify_scenario(txns)

            # Create alert
            alert_id = generate_id('ALT', f"{account}_{i}")
            first_txn_date = parse_timestamp(txns[0]['timestamp'])

            alert = AlertDB(
                id=alert_id,
                customer_id=customer_id,
                trigger_date=first_txn_date,
                scenario=scenario,
                risk_score=risk_score,
                status='pending',
            )
            db.merge(alert)
            alerts_created += 1

            # Create transactions
            for j, txn in enumerate(txns):
                txn_id = generate_id('TXN', f"{account}_{i}_{j}")

                # Determine transaction type from payment format
                payment_format = txn.get('payment_format', 'Wire').upper()
                if 'CASH' in payment_format or 'CHEQUE' in payment_format:
                    txn_type = 'CASH_DEPOSIT'
                elif 'WIRE' in payment_format or 'ACH' in payment_format:
                    txn_type = 'WIRE_TRANSFER'
                elif 'CREDIT' in payment_format:
                    txn_type = 'CREDIT_CARD'
                else:
                    txn_type = 'WIRE_TRANSFER'

                # Random high-risk location for suspicious transactions
                import random
                dest_location = None
                if txn['is_suspicious'] and random.random() > 0.5:
                    dest_location = random.choice(HIGH_RISK_LOCATIONS)

                transaction = TransactionDB(
                    id=txn_id,
                    alert_id=alert_id,
                    customer_id=customer_id,
                    date=parse_timestamp(txn['timestamp']),
                    amount=txn['amount'],
                    type=txn_type,
                    direction=txn['direction'],
                    source_account=txn['from_account'],
                    destination_account=txn['to_account'],
                    source_location=txn.get('from_bank', 'Unknown'),
                    destination_location=dest_location or txn.get('to_bank', 'Unknown'),
                    description=f"{payment_format} transaction",
                    is_suspicious=txn['is_suspicious'],
                )
                db.merge(transaction)
                transactions_created += 1

            if (i + 1) % 10 == 0:
                print(f"  Created {i + 1}/{len(alert_candidates)} alerts...")
                db.commit()

        db.commit()

        print("\n" + "="*50)
        print("IMPORT COMPLETE!")
        print("="*50)
        print(f"Customers created: {customers_created}")
        print(f"Alerts created:    {alerts_created}")
        print(f"Transactions:      {transactions_created}")
        print("="*50)

    finally:
        db.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Import IBM AML Dataset')
    parser.add_argument('csv_file', help='Path to IBM CSV file (e.g., HI-Small_Trans.csv)')
    parser.add_argument('--max-alerts', type=int, default=50, help='Maximum alerts to create (default: 50)')
    parser.add_argument('--max-txn', type=int, default=50, help='Max transactions per alert (default: 50)')

    args = parser.parse_args()

    if not Path(args.csv_file).exists():
        print(f"Error: File not found: {args.csv_file}")
        print("\nPlease download from:")
        print("https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml")
        sys.exit(1)

    import_ibm_dataset(args.csv_file, args.max_alerts, args.max_txn)


if __name__ == '__main__':
    main()
