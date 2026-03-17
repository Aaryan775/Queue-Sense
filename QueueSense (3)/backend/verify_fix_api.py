import requests
import json

BASE_URL = "http://127.0.0.1:5000/api/queues"
AUTH_URL = "http://127.0.0.1:5000/api/auth/login"

def test_queue_flow():
    # 1. Login to get token
    print("Logging in...")
    resp = requests.post(AUTH_URL, json={"username": "staff@test.com", "password": "password"})
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    
    token = resp.json()['token']
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Call Next
    print("Calling next...")
    payload = {"service_id": 0, "location_id": 0, "counter_number": 1}
    resp = requests.post(f"{BASE_URL}/call-next", json=payload, headers=headers)
    
    if resp.status_code != 200:
        print(f"Call Next failed (maybe empty?): {resp.text}")
        return
    
    data = resp.json()
    queue_id = data['queue_id']
    queue_type = data['queue_type']
    token_val = data['token']
    print(f"Called token {token_val} (ID: {queue_id}, Type: {queue_type})")
    
    # 3. Mark Served
    print(f"Marking {token_val} as served...")
    resp = requests.post(f"{BASE_URL}/serve/{queue_type}/{queue_id}", headers=headers)
    
    if resp.status_code == 200:
        print("Success: Customer marked as served.")
    else:
        print(f"Failed to mark served: {resp.text}")

if __name__ == "__main__":
    test_queue_flow()
