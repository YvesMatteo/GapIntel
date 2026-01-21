
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

def check_report_by_channel(channel_query):
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Missing Supabase credentials")
        return

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    # Query reports by channel name or handle
    # Using ilike for case-insensitive partial match
    url = f"{SUPABASE_URL}/rest/v1/user_reports?select=id,access_key,channel_name,channel_handle,status,progress_percentage,created_at,updated_at&or=(channel_name.ilike.*{channel_query}*,channel_handle.ilike.*{channel_query}*)"
    
    resp = requests.get(url, headers=headers)
    
    if resp.status_code != 200:
        print(f"❌ Failed to fetch reports: {resp.text}")
        return

    reports = resp.json()
    if not reports:
        print(f"ℹ️ No reports found matching '{channel_query}'")
        return

    print(f"Found {len(reports)} reports matching '{channel_query}':")
    for r in reports:
        prog = r.get('progress_percentage', 0)
        print(f"ID: {r['id']}, Name: {r['channel_name']}, Handle: {r['channel_handle']}, Status: {r['status']}, Progress: {prog}%, Updated: {r['updated_at']}")

if __name__ == "__main__":
    query = "tjr"
    check_report_by_channel(query)
