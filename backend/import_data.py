"""
CSV Data Import Script for SAR Narrative Generator

This script imports real/test data from CSV files into the database.

Usage:
    python import_data.py --customers customers.csv --alerts alerts.csv --transactions transactions.csv

CSV Formats Required:
--------------------

1. customers.csv:
   id,name,dob,pan,address,occupation,income_source,account_number,account_type,account_open_date
   CUST001,John Smith,1985-03-15,ABCDE1234F,123 Main St,Business Owner,Self-Employed,1234567890,SAVINGS,2020-01-15

2. alerts.csv:
   id,customer_id,trigger_date,scenario,risk_score,status
   ALT001,CUST001,2024-01-15,Structuring,85,pending

3. transactions.csv:
   id,alert_id,customer_id,date,amount,type,direction,source_account,destination_account,source_location,destination_location,description,is_suspicious
   TXN001,ALT001,CUST001,2024-01-10,9500,CASH_DEPOSIT,INBOUND,EXT123,1234567890,Mumbai,Mumbai,Cash deposit,true
"""

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.database import SessionLocal, create_tables
from app.db.models import CustomerDB, AlertDB, TransactionDB


def parse_date(date_str: str) -> datetime:
    """Parse date string in various formats."""
    if not date_str or date_str.lower() == 'null':
        return None

    formats = [
        '%Y-%m-%d',
        '%Y-%m-%d %H:%M:%S',
        '%d-%m-%Y',
        '%d/%m/%Y',
        '%m/%d/%Y',
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue

    print(f"Warning: Could not parse date '{date_str}'")
    return None


def parse_bool(val: str) -> bool:
    """Parse boolean string."""
    if isinstance(val, bool):
        return val
    return str(val).lower() in ('true', '1', 'yes', 'y')


def import_customers(db, csv_path: str) -> int:
    """Import customers from CSV."""
    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            customer = CustomerDB(
                id=row['id'].strip(),
                name=row['name'].strip(),
                dob=parse_date(row.get('dob', '')),
                pan=row.get('pan', '').strip() or None,
                address=row.get('address', '').strip() or None,
                occupation=row.get('occupation', '').strip() or None,
                income_source=row.get('income_source', '').strip() or None,
                account_number=row['account_number'].strip(),
                account_type=row.get('account_type', 'SAVINGS').strip(),
                account_open_date=parse_date(row.get('account_open_date', '')),
            )
            db.merge(customer)  # merge to handle duplicates
            count += 1

    db.commit()
    return count


def import_alerts(db, csv_path: str) -> int:
    """Import alerts from CSV."""
    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            alert = AlertDB(
                id=row['id'].strip(),
                customer_id=row['customer_id'].strip(),
                trigger_date=parse_date(row['trigger_date']) or datetime.now(),
                scenario=row['scenario'].strip(),
                risk_score=int(row['risk_score']),
                status=row.get('status', 'pending').strip(),
                assigned_to=row.get('assigned_to', '').strip() or None,
            )
            db.merge(alert)
            count += 1

    db.commit()
    return count


def import_transactions(db, csv_path: str) -> int:
    """Import transactions from CSV."""
    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            txn = TransactionDB(
                id=row['id'].strip(),
                alert_id=row['alert_id'].strip(),
                customer_id=row['customer_id'].strip(),
                date=parse_date(row['date']) or datetime.now(),
                amount=float(row['amount']),
                type=row['type'].strip(),
                direction=row['direction'].strip(),
                source_account=row.get('source_account', '').strip() or None,
                destination_account=row.get('destination_account', '').strip() or None,
                source_location=row.get('source_location', '').strip() or None,
                destination_location=row.get('destination_location', '').strip() or None,
                description=row.get('description', '').strip() or None,
                is_suspicious=parse_bool(row.get('is_suspicious', 'false')),
            )
            db.merge(txn)
            count += 1

    db.commit()
    return count


def main():
    parser = argparse.ArgumentParser(description='Import data from CSV files')
    parser.add_argument('--customers', help='Path to customers CSV file')
    parser.add_argument('--alerts', help='Path to alerts CSV file')
    parser.add_argument('--transactions', help='Path to transactions CSV file')
    parser.add_argument('--clear', action='store_true', help='Clear existing data before import')

    args = parser.parse_args()

    if not any([args.customers, args.alerts, args.transactions]):
        parser.print_help()
        print("\n\nExample usage:")
        print("  python import_data.py --customers data/customers.csv --alerts data/alerts.csv --transactions data/transactions.csv")
        print("\nOr import one at a time:")
        print("  python import_data.py --customers data/customers.csv")
        return

    # Create tables if they don't exist
    print("Ensuring database tables exist...")
    create_tables()

    db = SessionLocal()

    try:
        if args.clear:
            print("Clearing existing data...")
            db.query(TransactionDB).delete()
            db.query(AlertDB).delete()
            db.query(CustomerDB).delete()
            db.commit()

        if args.customers:
            print(f"Importing customers from {args.customers}...")
            count = import_customers(db, args.customers)
            print(f"  Imported {count} customers")

        if args.alerts:
            print(f"Importing alerts from {args.alerts}...")
            count = import_alerts(db, args.alerts)
            print(f"  Imported {count} alerts")

        if args.transactions:
            print(f"Importing transactions from {args.transactions}...")
            count = import_transactions(db, args.transactions)
            print(f"  Imported {count} transactions")

        print("\nImport complete!")

    finally:
        db.close()


if __name__ == '__main__':
    main()
