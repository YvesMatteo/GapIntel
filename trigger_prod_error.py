
import requests
import json
import uuid

# Production URL
BASE_URL = "https://thriving-presence-production-ca4a.up.railway.app"
API_KEY = "74616235-9503-4f51-a9f8-76906a457493" # The correct key

def trigger_error():
    url = f"{BASE_URL}/api/youtube-analytics/authorize"
    params = {
        "user_id": str(uuid.uuid4()),
        "redirect_uri": "https://gapintel.online/api/youtube-analytics/callback"
    }
    headers = {"X-API-Key": API_KEY}
    
    print(f"Triggering {url}...")
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    trigger_error()
