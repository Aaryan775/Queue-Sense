import requests
import sys

BASE_URL = "http://127.0.0.1:5000/api"

# We need a token. I'll try to login as admin.
# Default admin credentials from seed_db or similar are usually admin/admin123
def get_token():
    try:
        res = requests.post(f"{BASE_URL}/auth/login", json={
            "username": "admin@queuesense.com",
            "password": "Admin@123!"
        })
        if res.status_code == 200:
            return res.json().get('token')
    except:
        pass
    return None

def verify():
    token = get_token()
    if not token:
        print("Could not get admin token. Verification might be limited.")
        # Try to hit health regardless
        res = requests.get(f"http://127.0.0.1:5000/health")
        print(f"Health check: {res.status_code}")
        return

    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n--- Verifying /api/analytics/history ---")
    res = requests.get(f"{BASE_URL}/analytics/history", headers=headers)
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print(f"Type: {type(data)}")
        if isinstance(data, list) and len(data) > 0:
            print(f"First item keys: {list(data[0].keys())}")
            expected = {'label', 'tokens', 'appointments'}
            missing = expected - set(data[0].keys())
            if not missing:
                print("SUCCESS: History structure matches frontend expectations.")
            else:
                print(f"FAILURE: Missing keys {missing}")
        else:
            print("INFO: No data returned in history (maybe empty DB).")
            # Even if empty, it should be a list
            if isinstance(data, list):
                print("SUCCESS: Result is a list as expected.")

    print("\n--- Verifying /api/analytics/hourly ---")
    res = requests.get(f"{BASE_URL}/analytics/hourly", headers=headers)
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        if 'hourly_data' in data and len(data['hourly_data']) > 0:
            keys = list(data['hourly_data'][0].keys())
            print(f"Hourly keys: {keys}")
            if 'avg_queue' in keys:
                print("SUCCESS: avg_queue present in hourly data.")
            else:
                print("FAILURE: avg_queue missing from hourly data.")

if __name__ == "__main__":
    verify()
