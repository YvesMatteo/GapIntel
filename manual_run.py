import os
import subprocess
import json
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")
load_dotenv("railway-api/.env.example") 

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Missing Supabase credentials")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ACCESS_KEY = "GAP-MQ0HKiRM37kP"
CHANNEL = "a" # Derived from your database entry

print(f"🚀 Manually starting analysis for {CHANNEL} ({ACCESS_KEY})")

try:
    # 1. Update status to processing
    supabase.table("analyses").update({
        "analysis_status": "processing"
    }).eq("access_key", ACCESS_KEY).execute()

    # 2. Run the analyzer script
    # Note: channel 'a' might be invalid for YouTube, but we run it anyway
    print("Running gap_analyzer.py...")
    result = subprocess.run(
        [
            "python3", "gap_analyzer.py",
            "--channel", f"@{CHANNEL}",
            "--videos", "5",
            "--json"
        ],
        capture_output=True,
        text=True,
        timeout=600,
        cwd=os.getcwd()
    )

    # 3. Process results
    if result.returncode == 0:
        try:
            analysis_result = json.loads(result.stdout)
        except json.JSONDecodeError:
            # Fallback for plain text
            analysis_result = {
                "raw_report": result.stdout,
                "generated_at": datetime.utcnow().isoformat()
            }
        
        print("✅ Analysis successful!")
        
        # 4. Update Supabase with success
        supabase.table("analyses").update({
            "analysis_status": "completed",
            "analysis_result": analysis_result,
            "report_generated_at": datetime.utcnow().isoformat()
        }).eq("access_key", ACCESS_KEY).execute()
        
    else:
        print(f"❌ Analysis failed: {result.stderr}")
        supabase.table("analyses").update({
            "analysis_status": "failed",
            "analysis_result": {"error": result.stderr or "Unknown Script Error"}
        }).eq("access_key", ACCESS_KEY).execute()

except Exception as e:
    print(f"💥 Critical Error: {e}")
    supabase.table("analyses").update({
        "analysis_status": "failed",
        "analysis_result": {"error": str(e)}
    }).eq("access_key", ACCESS_KEY).execute()
