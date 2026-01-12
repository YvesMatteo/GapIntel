import json
from datetime import datetime
import requests

# Hardcoded credentials for immediate manual fix
SUPABASE_URL = "https://ttmbwiylctslgwjxrcht.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR0bWJ3aXlsY3RzbGd3anhyY2h0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzM4OTQwNywiZXhwIjoyMDgyOTY1NDA3fQ.TPT2Lw5QytHxxTPDmLYgYSX6nrenLrGC8diDq3-hujY"

# Target user key
ACCESS_KEY = "GAP-gvWWMj2eX-Wt"

try:
    with open('/Users/yvesromano/AiRAG/analysis_result.json') as f:
        result = json.load(f)
except FileNotFoundError:
    print("❌ analysis_result.json not found yet. Run gap_analyzer.py first.")
    exit(1)

payload = {
    "analysis_status": "completed",
    "analysis_result": result,
    "report_generated_at": datetime.utcnow().isoformat()
}

url = f"{SUPABASE_URL}/rest/v1/analyses?access_key=eq.{ACCESS_KEY}"
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

print(f"Updating Supabase for {ACCESS_KEY} at {url}...")
resp = requests.patch(url, headers=headers, json=payload)
print(f"Status: {resp.status_code}")
if resp.status_code >= 400:
    print(f"Error: {resp.text}")
else:
    print("✅ Success! Database updated.")
