
import os
import sys

# Add the current directory to path
sys.path.append('/Users/yvesromano/AiRAG/railway-api')

try:
    from server import recover_stuck_jobs, job_queue
    import time
    
    # We want to force recovery even if it hasn't been 30 mins (though it has)
    # But since the script uses 30 mins threshold, it should pick it up automatically
    
    print("🚀 Triggering recovery for stuck jobs...")
    recover_stuck_jobs()
    
    if job_queue.active_jobs > 0:
        print(f"📊 Active jobs in queue: {job_queue.active_jobs}")
        print("⏳ Waiting for job to start (10s)...")
        time.sleep(10)
    else:
        print("ℹ️ No active jobs found by the automated checker yet.")
        
except Exception as e:
    print(f"❌ Error during manual recovery: {e}")
    import traceback
    traceback.print_exc()
