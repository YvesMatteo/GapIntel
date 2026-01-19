
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def check_local():
    print(f"Checking {BASE_URL} ...")
    
    # 1. Debug Config
    try:
        res = requests.get(f"{BASE_URL}/api/debug/config", timeout=5)
        print(f"Debug Config: {res.status_code}")
        if res.status_code == 200:
            print(json.dumps(res.json(), indent=2))
    except Exception as e:
        print(f"Debug Check Failed: {e}")

    # 2. Authorize Endpoint (Trigger URL Generation)
    try:
        print("\nTriggering /authorize...")
        res = requests.get(f"{BASE_URL}/api/youtube-analytics/authorize?user_id=test_user", timeout=5)
        print(f"Authorize Status: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            print(f"Auth URL generated: {data.get('url', 'MISSING')[:50]}...")
        else:
            print(f"Error: {res.text}")
    except Exception as e:
        print(f"Authorize Failed: {e}")

if __name__ == "__main__":
    time.sleep(2) # Give server time to start
    check_local()
