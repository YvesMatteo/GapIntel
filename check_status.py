import os
from supabase import create_client
from dotenv import load_dotenv

# Load env vars
load_dotenv(".env")
load_dotenv("railway-api/.env.example") # Fallback

url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("Error: Missing Supabase credentials")
    exit(1)

supabase = create_client(url, key)

# Get the latest analysis
response = supabase.table("analyses").select("*").order("created_at", desc=True).limit(1).execute()

if response.data:
    latest = response.data[0]
    print(f"Latest Analysis:")
    print(f"Key: {latest.get('access_key')}")
    print(f"Channel: {latest.get('channel_name')}")
    print(f"Status: {latest.get('analysis_status')}")
    print(f"Created At: {latest.get('created_at')}")
else:
    print("No analyses found")
