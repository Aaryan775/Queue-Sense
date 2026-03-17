import requests
import json

BASE_URL = "http://127.0.0.1:5000/api/queues"
AUTH_URL = "http://127.0.0.1:5000/api/auth/login"

def test_queue_api():
    # 1. Login
    print("Logging in...")
    resp = requests.post(AUTH_URL, json={"username": "staff@test.com", "password": "password"})
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    token = resp.json()['token']
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get Queue Status (Service 0, Location 0 for ALL)
    print("Fetching queue status...")
    resp = requests.get(f"{BASE_URL}/status/0/0", headers=headers)
    
    if resp.status_code != 200:
        print(f"Failed to get status: {resp.text}")
        return
        
    data = resp.json()
    print(f"Elder Queue Count: {len(data.get('elder_queue', []))}")
    print(f"Normal Queue Count: {len(data.get('normal_queue', []))}")
    
    if data.get('normal_queue'):
        print("First Normal Entry:", data['normal_queue'][0])
    else:
        print("No normal entries found in API response.")

if __name__ == "__main__":
    test_queue_api()
