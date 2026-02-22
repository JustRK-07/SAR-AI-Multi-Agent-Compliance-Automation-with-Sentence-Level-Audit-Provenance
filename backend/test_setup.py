"""
Test script to verify the setup is working correctly.

Run: python test_setup.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_database():
    """Test database connection and data."""
    print("\n1. Testing Database...")

    from app.db.database import SessionLocal
    from app.db.models import CustomerDB, AlertDB, TransactionDB

    db = SessionLocal()

    customers = db.query(CustomerDB).count()
    alerts = db.query(AlertDB).count()
    transactions = db.query(TransactionDB).count()

    print(f"   Customers:    {customers}")
    print(f"   Alerts:       {alerts}")
    print(f"   Transactions: {transactions}")

    if alerts == 0:
        print("   ⚠️  No data found! Run seed_data.py or import_ibm_aml.py first")
        return False

    print("   ✅ Database OK")
    db.close()
    return True


def test_api():
    """Test API endpoints."""
    print("\n2. Testing API...")

    import httpx

    base_url = "http://127.0.0.1:8000"

    try:
        # Test health
        r = httpx.get(f"{base_url}/health", timeout=5)
        if r.status_code == 200:
            print("   ✅ Health endpoint OK")
        else:
            print(f"   ❌ Health endpoint failed: {r.status_code}")
            return False

        # Test alerts
        r = httpx.get(f"{base_url}/api/alerts/", timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"   ✅ Alerts endpoint OK ({data['total']} alerts)")
        else:
            print(f"   ❌ Alerts endpoint failed: {r.status_code}")
            return False

        # Test single alert
        if data['total'] > 0:
            alert_id = data['alerts'][0]['id']
            r = httpx.get(f"{base_url}/api/alerts/{alert_id}", timeout=5)
            if r.status_code == 200:
                print(f"   ✅ Single alert endpoint OK")
            else:
                print(f"   ❌ Single alert endpoint failed: {r.status_code}")

        # Test transaction graph
        if data['total'] > 0:
            alert_id = data['alerts'][0]['id']
            r = httpx.get(f"{base_url}/api/transactions/graph/{alert_id}", timeout=5)
            if r.status_code == 200:
                graph = r.json()
                print(f"   ✅ Transaction graph OK ({len(graph['accounts'])} accounts, {len(graph['transactions'])} edges)")
            else:
                print(f"   ❌ Transaction graph failed: {r.status_code}")

        return True

    except httpx.ConnectError:
        print("   ❌ Cannot connect to API. Is the backend running?")
        print("      Run: cd backend && source venv/bin/activate && uvicorn app.main:app --reload")
        return False


def test_sar_generation():
    """Test SAR generation (without actually calling LLM)."""
    print("\n3. Testing SAR Components...")

    from app.services.sar_generator import SARGeneratorService, TokenUsageTracker
    from app.services.fact_checker import FactCheckerService

    # Test TokenUsageTracker
    tracker = TokenUsageTracker()
    tracker.add_usage('writer', 100, 50)
    assert tracker.total_tokens == 150
    print("   ✅ TokenUsageTracker OK")

    # Test FactCheckerService
    service = FactCheckerService(None)
    claims = service.extract_claims("John made 47 transactions totaling ₹125,000 in March 2024.")
    assert len(claims) > 0
    print(f"   ✅ Claim extraction OK ({len(claims)} claims found)")

    # Test date verification
    from datetime import datetime
    date_range = (datetime(2024, 1, 1), datetime(2024, 6, 30))
    result = service._verify_date_claim('March 15, 2024', date_range)
    assert result['verified'] == True
    print("   ✅ Date verification OK")

    return True


def main():
    print("="*50)
    print("SAR NARRATIVE GENERATOR - SETUP TEST")
    print("="*50)

    results = []

    results.append(("Database", test_database()))
    results.append(("API", test_api()))
    results.append(("SAR Components", test_sar_generation()))

    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {name}: {status}")
        if not passed:
            all_passed = False

    print("="*50)

    if all_passed:
        print("\n🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Open http://localhost:5174 in browser")
        print("2. Go to 'Alerts' page")
        print("3. Click 'Review' on any alert")
        print("4. Click 'Generate SAR' to create narrative")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
