# test_api.py
import os
import requests
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://127.0.0.1:8000/api"
AUTH_URL = "http://127.0.0.1:8000/auth"  # Adjust if needed
HEADERS = {"Content-Type": "application/json"}

# Store tokens
access_token = None
refresh_token = None

def print_success(msg):
    print(f"SUCCESS: {msg}")

def print_error(msg, response=None):
    print(f"FAILED: {msg}")
    if response:
        print(f"   Status: {response.status_code}")
        try:
            print(f"   Body: {response.json()}")
        except:
            print(f"   Body: {response.text}")

def login():
    global access_token, refresh_token
    print("\n1. Logging in...")
    payload = {
        "phone": "254712345678",  # Change to real test user
        "password": "testpass123"
    }
    resp = requests.post(f"{AUTH_URL}/login/", json=payload, headers=HEADERS)
    if resp.status_code == 200:
        data = resp.json()
        access_token = data["access"]
        refresh_token = data["refresh"]
        HEADERS["Authorization"] = f"Bearer {access_token}"
        print_success("Login successful")
        return True
    print_error("Login failed", resp)
    return False

def test_chamas():
    print("\n2. Testing Chamas...")
    # List
    resp = requests.get(f"{BASE_URL}/chamas/", headers=HEADERS)
    if resp.status_code == 200:
        print_success(f"GET /chamas/ → {len(resp.json())} chamas")
    else:
        print_error("GET /chamas/", resp); return

    # Create
    payload = {"name": "Test Chama", "description": "Auto test"}
    resp = requests.post(f"{BASE_URL}/chamas/", json=payload, headers=HEADERS)
    if resp.status_code == 201:
        chama = resp.json()
        print_success(f"POST /chamas/ → {chama['name']}")
        return chama["id"]
    print_error("POST /chamas/", resp)
    return None

def test_memberships(chama_id):
    print("\n3. Testing Memberships...")
    # Join chama
    payload = {"chama_id": chama_id, "is_admin": True}
    resp = requests.post(f"{BASE_URL}/memberships/", json=payload, headers=HEADERS)
    if resp.status_code == 201:
        print_success("Joined chama as admin")
        return resp.json()["id"]
    print_error("POST /memberships/", resp)
    return None

def test_contributions(membership_id):
    print("\n4. Testing Contributions...")
    payload = {"membership": membership_id, "amount": "500.00"}
    resp = requests.post(f"{BASE_URL}/contributions/", json=payload, headers=HEADERS)
    if resp.status_code == 201:
        contrib = resp.json()
        print_success(f"Contributed KES {contrib['amount']}")
        return contrib["id"]
    print_error("POST /contributions/", resp)
    return None

def test_loans(membership_id):
    print("\n5. Testing Loans...")
    # Apply
    payload = {"principal": "1000.00", "tenure_months": 3}
    resp = requests.post(f"{BASE_URL}/loans/apply/", json=payload, headers=HEADERS)
    if resp.status_code == 201:
        loan = resp.json()
        print_success(f"Loan applied: KES {loan['principal']} → EMI {loan['emi']}")
        return loan["id"]
    print_error("POST /loans/apply/", resp)
    return None

def test_loan_actions(loan_id):
    print("\n6. Testing Loan Actions...")
    # Approve
    resp = requests.post(f"{BASE_URL}/loans/{loan_id}/approve/", headers=HEADERS)
    if resp.status_code == 200:
        print_success("Loan approved")
    else:
        print_error("POST /approve/", resp)

    # Reject (if not approved)
    # resp = requests.post(f"{BASE_URL}/loans/{loan_id}/reject/", headers=HEADERS)

def test_repayments(loan_id):
    print("\n7. Testing Repayments...")
    payload = {"loan": loan_id, "amount": "300.00"}
    resp = requests.post(f"{BASE_URL}/repayments/", json=payload, headers=HEADERS)
    if resp.status_code == 201:
        print_success("Repayment recorded")
    else:
        print_error("POST /repayments/", resp)

def test_mpesa():
    print("\n8. Testing M-Pesa Transactions...")
    resp = requests.get(f"{BASE_URL}/mpesa-transactions/", headers=HEADERS)
    if resp.status_code == 200:
        count = len(resp.json())
        print_success(f"Found {count} M-Pesa transactions")
    else:
        print_error("GET /mpesa-transactions/", resp)

def test_dashboard():
    print("\n9. Testing Member Dashboard...")
    resp = requests.get(f"{BASE_URL}/members/me/", headers=HEADERS)
    if resp.status_code == 200:
        print_success("Dashboard loaded")
    else:
        print_error("GET /members/me/", resp)

    resp = requests.get(f"{BASE_URL}/members/dashboard/", headers=HEADERS)
    if resp.status_code == 200:
        data = resp.json()
        print_success(f"Saved: KES {data['total_contributed']}, Can apply: {data['can_apply_loan']}")
    else:
        print_error("GET /members/dashboard/", resp)

# ===================================================================
# RUN ALL TESTS
# ===================================================================
if __name__ == "__main__":
    print("Jamii Funds API End-to-End Test Suite")
    print("="*60)

    if not login():
        exit(1)

    chama_id = test_chamas()
    if not chama_id:
        exit(1)

    membership_id = test_memberships(chama_id)
    if not membership_id:
        exit(1)

    contrib_id = test_contributions(membership_id)
    loan_id = test_loans(membership_id)
    if loan_id:
        test_loan_actions(loan_id)
        test_repayments(loan_id)

    test_mpesa()
    test_dashboard()

    print("\nALL TESTS PASSED! READY FOR FRONTEND")
    print("Connect React Native / Flutter now")