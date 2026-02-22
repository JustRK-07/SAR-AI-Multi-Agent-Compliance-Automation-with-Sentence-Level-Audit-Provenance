"""
Seed script to populate the database with sample data for development/demo.
Run with: python seed_data.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import random
import uuid

from app.db.database import SessionLocal, create_tables
from app.db.models import CustomerDB, AlertDB, TransactionDB


# Sample data
FIRST_NAMES = ["Rajesh", "Priya", "Amit", "Sunita", "Vikram", "Anita", "Suresh", "Kavita", "Rahul", "Meera"]
LAST_NAMES = ["Kumar", "Shah", "Patel", "Sharma", "Singh", "Gupta", "Verma", "Joshi", "Reddy", "Nair"]
OCCUPATIONS = ["Software Engineer", "Business Owner", "Doctor", "Accountant", "Teacher", "Consultant", "Manager", "Freelancer"]
LOCATIONS = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune", "Ahmedabad"]
HIGH_RISK_LOCATIONS = ["Cayman Islands", "Panama", "British Virgin Islands", "Switzerland"]

SCENARIOS = [
    ("Structuring", 85, 95),
    ("Layering", 80, 92),
    ("Rapid Movement", 75, 90),
    ("Collection Account", 70, 88),
]


def generate_pan():
    """Generate a fake PAN number."""
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    digits = "0123456789"
    return (
        "".join(random.choices(letters, k=5)) +
        "".join(random.choices(digits, k=4)) +
        random.choice(letters)
    )


def generate_account_number():
    """Generate a fake account number."""
    return "".join(random.choices("0123456789", k=12))


def create_customer(db, idx: int) -> CustomerDB:
    """Create a sample customer."""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)

    customer = CustomerDB(
        id=f"CUST_{uuid.uuid4().hex[:8].upper()}",
        name=f"{first_name} {last_name}",
        dob=datetime(1970 + random.randint(0, 35), random.randint(1, 12), random.randint(1, 28)),
        pan=generate_pan(),
        address=f"{random.randint(1, 500)} {random.choice(['MG Road', 'Park Street', 'Brigade Road', 'FC Road'])}, {random.choice(LOCATIONS)}",
        occupation=random.choice(OCCUPATIONS),
        income_source="Salary" if random.random() > 0.3 else "Business",
        account_number=generate_account_number(),
        account_type="Savings",
        account_open_date=datetime.now() - timedelta(days=random.randint(365, 2000)),
    )

    db.add(customer)
    return customer


def create_alert(db, customer: CustomerDB, scenario: tuple) -> AlertDB:
    """Create a sample alert."""
    scenario_name, min_risk, max_risk = scenario

    alert = AlertDB(
        id=f"ALT_{uuid.uuid4().hex[:8].upper()}",
        trigger_date=datetime.now() - timedelta(days=random.randint(1, 30)),
        scenario=scenario_name,
        risk_score=random.randint(min_risk, max_risk),
        customer_id=customer.id,
        status="pending",
    )

    db.add(alert)
    return alert


def create_transactions(db, alert: AlertDB, customer: CustomerDB, count: int) -> list[TransactionDB]:
    """Create sample transactions for an alert."""
    transactions = []
    base_date = alert.trigger_date - timedelta(days=7)

    # Generate unique source accounts
    source_accounts = [generate_account_number() for _ in range(min(count, 50))]

    for i in range(count):
        txn_date = base_date + timedelta(
            days=random.randint(0, 7),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        # Determine transaction type based on scenario
        if alert.scenario == "Structuring":
            # Multiple deposits just below threshold
            amount = random.randint(8500, 9900)
            txn_type = "CASH_DEPOSIT"
            direction = "INBOUND"
            source = random.choice(source_accounts)
            dest = customer.account_number
            source_loc = random.choice(LOCATIONS)
            dest_loc = random.choice(LOCATIONS)

        elif alert.scenario == "Layering":
            if i < count * 0.7:
                # Inbound transfers
                amount = random.randint(50000, 200000)
                txn_type = "WIRE_TRANSFER"
                direction = "INBOUND"
                source = random.choice(source_accounts)
                dest = customer.account_number
                source_loc = random.choice(LOCATIONS)
                dest_loc = random.choice(LOCATIONS)
            else:
                # Outbound to offshore
                amount = random.randint(100000, 500000)
                txn_type = "WIRE_TRANSFER"
                direction = "OUTBOUND"
                source = customer.account_number
                dest = generate_account_number()
                source_loc = random.choice(LOCATIONS)
                dest_loc = random.choice(HIGH_RISK_LOCATIONS)

        elif alert.scenario == "Rapid Movement":
            if i < count * 0.5:
                amount = random.randint(100000, 500000)
                txn_type = "WIRE_TRANSFER"
                direction = "INBOUND"
                source = random.choice(source_accounts)
                dest = customer.account_number
                source_loc = random.choice(LOCATIONS)
                dest_loc = random.choice(LOCATIONS)
            else:
                amount = random.randint(90000, 490000)
                txn_type = "WIRE_TRANSFER"
                direction = "OUTBOUND"
                source = customer.account_number
                dest = generate_account_number()
                source_loc = random.choice(LOCATIONS)
                dest_loc = random.choice(HIGH_RISK_LOCATIONS)

        else:  # Collection Account
            amount = random.randint(50000, 150000)
            txn_type = random.choice(["WIRE_TRANSFER", "ACH_TRANSFER", "CHECK_DEPOSIT"])
            direction = "INBOUND"
            source = random.choice(source_accounts)
            dest = customer.account_number
            source_loc = random.choice(LOCATIONS)
            dest_loc = random.choice(LOCATIONS)

        txn = TransactionDB(
            id=f"TXN_{uuid.uuid4().hex[:12].upper()}",
            alert_id=alert.id,
            customer_id=customer.id,
            date=txn_date,
            amount=amount,
            type=txn_type,
            direction=direction,
            source_account=source,
            destination_account=dest,
            source_location=source_loc,
            destination_location=dest_loc,
            description=f"Transaction {i+1}",
            is_suspicious=True,
        )

        transactions.append(txn)
        db.add(txn)

    return transactions


def seed_database():
    """Main seeding function."""
    print("Creating database tables...")
    create_tables()

    db = SessionLocal()

    try:
        # Check if data already exists
        existing_alerts = db.query(AlertDB).count()
        if existing_alerts > 0:
            print(f"Database already has {existing_alerts} alerts. Skipping seed.")
            return

        print("Seeding database with sample data...")

        # Create 10 customers with alerts
        for i in range(10):
            print(f"Creating customer {i+1}/10...")

            # Create customer
            customer = create_customer(db, i)
            db.flush()

            # Create alert with random scenario
            scenario = random.choice(SCENARIOS)
            alert = create_alert(db, customer, scenario)
            db.flush()

            # Create transactions based on scenario
            if scenario[0] == "Structuring":
                txn_count = random.randint(30, 50)
            elif scenario[0] == "Layering":
                txn_count = random.randint(10, 25)
            elif scenario[0] == "Rapid Movement":
                txn_count = random.randint(5, 15)
            else:
                txn_count = random.randint(15, 30)

            create_transactions(db, alert, customer, txn_count)

        db.commit()
        print("Database seeded successfully!")
        print(f"Created: 10 customers, 10 alerts, {db.query(TransactionDB).count()} transactions")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
