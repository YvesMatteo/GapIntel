
import os
import requests
import json
from datetime import datetime
import uuid

# Configuration
SUPABASE_URL = "https://ttmbwiylctslgwjxrcht.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR0bWJ3aXlsY3RzbGd3anhyY2h0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzM4OTQwNywiZXhwIjoyMDgyOTY1NDA3fQ.TPT2Lw5QytHxxTPDmLYgYSX6nrenLrGC8diDq3-hujY"
API_URL = "https://thriving-presence-production-ca4a.up.railway.app/api/youtube-analytics"
DEBUG_URL = "https://thriving-presence-production-ca4a.up.railway.app/api/debug/config"

# Test Data
USER_ID = str(uuid.uuid4())
CHANNEL_ID = "test_channel"

def check_supabase_connection():
    print(f"Checking Supabase: {SUPABASE_URL}")
    print(f"Using Key: {SUPABASE_KEY[:10]}...")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    # 1. Read Test
    try:
        url = f"{SUPABASE_URL}/rest/v1/youtube_analytics_tokens?select=count"
        res = requests.get(url, headers=headers)
        print(f"Count Response: {res.text}")
        
        # Read latest
        url = f"{SUPABASE_URL}/rest/v1/youtube_analytics_tokens?limit=1&order=created_at.desc"
        res = requests.get(url, headers=headers)
        print("Latest Token:")
        print(json.dumps(res.json(), indent=2))
        
    except Exception as e:
        print(f"Read Error: {e}")

    # 2. Write Test
    print(f"\nAttempting Insert Test for user {USER_ID}...")
    data = {
        "user_id": USER_ID,
        "channel_id": CHANNEL_ID,
        "access_token_encrypted": "test",
        "refresh_token_encrypted": "test",
        "expires_at": "2025-01-01T00:00:00Z",
        "scopes": []
    }
    
    try:
        url = f"{SUPABASE_URL}/rest/v1/youtube_analytics_tokens"
        res = requests.post(url, headers=headers, json=data)
        print(f"Insert Response: {res.status_code} - {res.text}")
        
        if res.status_code in [200, 201]:
            print("\nTest token inserted. Verifying via Backend API...")
            verify_api_access(USER_ID)
            
    except Exception as e:
        print(f"Write Error: {e}")

def verify_api_access(user_id):
    # This checks if the backend can read the token we just inserted
    # And specifically if it accepts our API KEY
    
    # We need the API Secret Key for the header
    # It's '74616235-9503-4f51-a9f8-76906a457493' based on previous context 
    # but we can try without if we just want to test liveness first
    
    headers = {
        "X-API-Key": "74616235-9503-4f51-a9f8-76906a457493"
    }
    
    try:
        # Check Status Endpoint
        url = f"{API_URL}/status?user_id={user_id}"
        res = requests.get(url, headers=headers)
        print(f"Backend API Status Check: {res.status_code}")
        print(f"Response: {res.text}")
    except Exception as e:
        print(f"API Check Error: {e}")

if __name__ == "__main__":
    check_supabase_connection()
