
import os
import sys
import requests
from dotenv import load_dotenv

# Load env from parent directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")

if not url or not key:
    print("❌ Missing Supabase credentials")
    sys.exit(1)

def check_channel(name):
    print(f"\n🔍 Checking for channel: {name}")
    try:
        # Supabase REST API
        endpoint = f"{url}/rest/v1/user_reports?channel_name=ilike.%{name}%&select=id,channel_name,status,created_at,user_id,access_key"
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(endpoint, headers=headers)
        
        if response.status_code != 200:
            print(f"   ❌ API Error: {response.status_code} {response.text}")
            return

        data = response.json()
        if data:
            print(f"   Found {len(data)} records:")
            for report in data:
                print(f"   - [{report.get('status')}] {report.get('channel_name')} (ID: {report.get('id')}) Created: {report.get('created_at')}")
                # Print command to delete
                print(f"     👉 To Delete: curl -X DELETE '{url}/rest/v1/user_reports?id=eq.{report.get('id')}' -H 'apikey: {key}' -H 'Authorization: Bearer {key}'")
        else:
            print("   No records found.")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    import time
    print("\n🔍 Polling API Health...")
    health_url = "https://resourceful-passion-production.up.railway.app/health"
    
    for i in range(12): # Try for 60 seconds
        try:
            resp = requests.get(health_url, timeout=5)
            if resp.status_code == 200:
                print("   ✅ API is UP!")
                print(resp.json())
                break
            else:
                print(f"   ⏳ Waiting for deployment... ({resp.status_code})")
        except Exception:
            print("   ⏳ Waiting for deployment... (Connection Error)")
        
        time.sleep(5)
        
    print("\n🔍 Checking TJR Report Status:")
    try:
        endpoint = f"{url}/rest/v1/user_reports?channel_name=ilike.%TJR%&order=created_at.desc&limit=1"
        headers = {
             "apikey": key,
             "Authorization": f"Bearer {key}",
             "Content-Type": "application/json"
        }
        resp = requests.get(endpoint, headers=headers)
        if resp.status_code == 200:
             reports = resp.json()
             for r in reports:
                  print(f" - [{r['status']}] {r['channel_name']} (ID: {r['id']}) Created: {r['created_at']}")
    except Exception as e:
        print(e)
