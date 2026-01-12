"""
Railway API Service for GAP Intel
Runs gap_analyzer.py as a background job triggered by Stripe webhooks.
Security-hardened with API authentication, rate limiting, and queue system.
"""

import os
import json
import time
import threading
from datetime import datetime
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, validator
import requests
import subprocess
import asyncio
import re

from email_service import (
    send_report_complete_email, 
    send_analysis_started_email, 
    send_analysis_failed_email,
    send_admin_failure_notification,
    send_admin_timeout_notification,
    send_user_timeout_email
)


# ============================================
# Configuration
# ============================================

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
API_SECRET_KEY = os.environ.get("API_SECRET_KEY", "")  # Shared secret with frontend
MAX_CONCURRENT_JOBS = int(os.environ.get("MAX_CONCURRENT_JOBS", "5"))

# Allowed origins (restrict CORS)
ALLOWED_ORIGINS = [
    "https://gapintel.online",
    "https://www.gapintel.online",
    "https://renewed-comfort-production.up.railway.app",
    "http://localhost:3000",  # Local dev
]


# ============================================
# Rate Limiting
# ============================================

class RateLimiter:
    """Simple in-memory rate limiter."""
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
        self._lock = threading.Lock()
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed for this IP."""
        now = time.time()
        with self._lock:
            # Clean old requests
            self.requests[client_ip] = [
                t for t in self.requests[client_ip] 
                if now - t < self.window_seconds
            ]
            # Check limit
            if len(self.requests[client_ip]) >= self.max_requests:
                return False
            # Record request
            self.requests[client_ip].append(now)
            return True

rate_limiter = RateLimiter(max_requests=10, window_seconds=60)


# ============================================
# Job Queue (Thread-safe, in-memory with DB backup)
# ============================================

class JobQueue:
    """Thread-safe job queue with concurrent job limiting."""
    def __init__(self, max_concurrent: int = 1):
        self.max_concurrent = max_concurrent
        self.active_jobs = 0
        self.queue = []
        self._lock = threading.Lock()
        self._worker_running = False
    
    def enqueue(self, job_data: dict):
        """Add job to queue."""
        with self._lock:
            self.queue.append(job_data)
            print(f"📥 Job queued: {job_data['access_key']} (queue size: {len(self.queue)})")
            if not self._worker_running:
                self._start_worker()
    
    def _start_worker(self):
        """Start background worker if not running."""
        self._worker_running = True
        thread = threading.Thread(target=self._process_queue, daemon=True)
        thread.start()
    
    def _process_queue(self):
        """Process jobs from queue one at a time."""
        while True:
            job = None
            with self._lock:
                if self.queue and self.active_jobs < self.max_concurrent:
                    job = self.queue.pop(0)
                    self.active_jobs += 1
                elif not self.queue:
                    self._worker_running = False
                    return
            
            if job:
                try:
                    print(f"🔄 Processing job: {job['access_key']}")
                    run_analysis(
                        job['channel_name'],
                        job['access_key'],
                        job['email'],
                        job['video_count'],
                        job.get('tier', 'starter'),
                        job.get('include_shorts', True)
                    )
                finally:
                    with self._lock:
                        self.active_jobs -= 1
            else:
                time.sleep(1)  # Wait before checking again

job_queue = JobQueue(max_concurrent=MAX_CONCURRENT_JOBS)


# ============================================
# API Key Authentication
# ============================================

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    """Verify API key for protected endpoints."""
    if not API_SECRET_KEY:
        # No key configured = skip auth (development mode)
        print("⚠️ API_SECRET_KEY not set - skipping authentication")
        return True
    
    if api_key != API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return True


# ============================================
# Input Validation
# ============================================

class AnalyzeRequest(BaseModel):
    channel_name: str
    access_key: str
    email: str
    video_count: int = 1
    include_shorts: bool = True
    tier: str = "starter"
    
    @validator('channel_name')
    def validate_channel_name(cls, v):
        # Remove @ and sanitize
        v = v.lstrip('@').strip()
        # Only allow alphanumeric, underscores, hyphens
        if not re.match(r'^[\w\-]+$', v):
            raise ValueError('Invalid channel name format')
        if len(v) < 1 or len(v) > 100:
            raise ValueError('Channel name must be 1-100 characters')
        return v
    
    @validator('access_key')
    def validate_access_key(cls, v):
        if not v.startswith('GAP-'):
            raise ValueError('Invalid access key format')
        if len(v) > 50:
            raise ValueError('Access key too long')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
            raise ValueError('Invalid email format')
        return v
    
    @validator('video_count')
    def validate_video_count(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Video count must be 1-100')
        return v


class AnalyzeResponse(BaseModel):
    status: str
    message: str
    access_key: str
    queue_position: int = 0


# ============================================
# Helper Functions
# ============================================

def create_analysis_record(access_key: str, channel_name: str, email: str) -> bool:
    """Create initial analysis record in Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️ Supabase credentials missing")
        return False

    url = f"{SUPABASE_URL}/rest/v1/analyses"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "access_key": access_key,
        "channel_name": channel_name,
        "email": email,
        "analysis_status": "queued",
    }
            
    try:
        resp = requests.post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            print(f"⚠️ Supabase create failed: {resp.text}")
            return False
        print(f"✅ Supabase record created for {access_key}")
        return True
    except Exception as e:
        print(f"⚠️ Supabase request error: {e}")
        return False


def update_analysis_status(access_key: str, status: str, result: dict = None):
    """Update analysis status in user_reports table via REST API."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return

    url = f"{SUPABASE_URL}/rest/v1/user_reports?access_key=eq.{access_key}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    # Map status to 'user_reports' schema
    payload = {"status": status}
    
    if result:
        payload["report_data"] = result
        if status == "completed":
            payload["updated_at"] = datetime.utcnow().isoformat()
            
    try:
        resp = requests.patch(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            print(f"⚠️ Supabase update failed: {resp.text}")
        else:
            print(f"✅ Supabase status updated to {status}")
    except Exception as e:
        print(f"⚠️ Supabase request error: {e}")


def fetch_analysis_status(access_key: str) -> dict:
    """Fetch analysis record via REST API."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None

    url = f"{SUPABASE_URL}/rest/v1/analyses?access_key=eq.{access_key}&select=*"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                return data[0]
    except Exception as e:
        print(f"⚠️ Supabase fetch error: {e}")
    return None


def handle_failure_logic(email: str, access_key: str, channel_name: str, error_msg: str):
    """Handle side effects of analysis failure (usage decrement, timeout check)."""
    try:
        from premium.subscription_manager import get_subscription_manager
        manager = get_subscription_manager()
        
        # Decrement usage count since report failed
        asyncio.run(manager.decrement_usage(email))
        
        # Check if user should be timed out
        is_timed_out, expiry = asyncio.run(manager.check_timeout_status(email))
        
        # Notification logic
        send_admin_failure_notification(email, access_key, channel_name, error_msg, 5 if is_timed_out else 1)
        
        if is_timed_out:
            send_admin_timeout_notification(email, 5, expiry)
            send_user_timeout_email(email, expiry, 5)
            
    except Exception as e:
        print(f"⚠️ Error in failure logic: {e}")


# ============================================
# Analysis Runner
# ============================================

# Maximum time for an analysis job (10 minutes)
JOB_TIMEOUT_SECONDS = 10 * 60

def run_analysis(channel_name: str, access_key: str, email: str, video_count: int = 1, tier: str = "starter", include_shorts: bool = True):
    """Run the gap analyzer with timeout protection. Called by queue worker."""
    print(f"🚀 Starting analysis for @{channel_name} (key: {access_key}) videos: {video_count} tier: {tier} shorts: {include_shorts}")
    
    try:
        update_analysis_status(access_key, "processing")
        
        import sys
        cmd_list = [
            sys.executable, "GAP_ULTIMATE.py",
            channel_name,
            "--access_key", access_key,
            "--email", email,
            "--videos", str(video_count),
            "--model", "tiny",
            "--ai", "gemini",
            "--gemini-model", "gemini-2.0-flash",
            "--tier", tier
        ]
        
        # Handle shorts preference
        if not include_shorts:
            cmd_list.append("--skip-shorts")
        
        print(f"🔄 Running: {' '.join(cmd_list)} (timeout: {JOB_TIMEOUT_SECONDS}s)")
        
        process = subprocess.Popen(
            cmd_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        try:
            # Use communicate with timeout instead of iterating stdout
            stdout_text, _ = process.communicate(timeout=JOB_TIMEOUT_SECONDS)
            
            # Print output for logging
            for line in stdout_text.split('\n'):
                if line.strip():
                    print(f"   [ANALYSIS] {line.strip()}")
            
            output = stdout_text.split('\n')
            
        except subprocess.TimeoutExpired:
            # Kill the process if it times out
            process.kill()
            process.wait()
            error_msg = f"Analysis timed out after {JOB_TIMEOUT_SECONDS // 60} minutes"
            print(f"⏰ {error_msg}")
            update_analysis_status(access_key, "failed", {"error": error_msg})
            send_analysis_failed_email(email, access_key, channel_name, error_msg)
            handle_failure_logic(email, access_key, channel_name, error_msg)
            return
        
        if process.returncode == 0:
            try:
                json_candidate = ""
                for line in reversed(output):
                    if line.strip().startswith("{") and line.strip().endswith("}"):
                        json_candidate = line.strip()
                        break
                
                if json_candidate:
                    analysis_result = json.loads(json_candidate)
                else:
                    analysis_result = {
                        "raw_report": stdout_text,
                        "generated_at": datetime.utcnow().isoformat()
                    }
            except Exception:
                analysis_result = {
                    "raw_report": stdout_text,
                    "generated_at": datetime.utcnow().isoformat()
                }
            
            update_analysis_status(access_key, "completed", analysis_result)
            print(f"✅ Analysis complete for {channel_name}")
            send_report_complete_email(email, channel_name, access_key)
            
        else:
            error_msg = f"Analysis failed (code: {process.returncode})"
            last_lines = '\n'.join(output[-10:]) if output else "No output"
            print(f"❌ {error_msg}")
            update_analysis_status(access_key, "failed", {"error": error_msg, "last_output": last_lines})
            send_analysis_failed_email(email, channel_name, error_msg)
            handle_failure_logic(email, access_key, channel_name, error_msg)
                
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"💥 {error_msg}")
        update_analysis_status(access_key, "failed", {"error": error_msg})
        send_analysis_failed_email(email, channel_name, error_msg)
        handle_failure_logic(email, access_key, channel_name, error_msg)


# ============================================
# FastAPI App
# ============================================

def recover_stuck_jobs():
    """
    Check database for stuck jobs (processing for too long) and handle them.
    Called at startup to recover from crashes or sleep.
    
    Logic:
    - Jobs processing for >30 minutes are considered stuck
    - Stuck jobs get retry_count incremented and re-queued
    - Jobs with retry_count >= 3 are marked as failed (prevent infinite loops)
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️ Cannot recover stuck jobs: Supabase credentials missing")
        return
    
    # Max time a job can be "processing" before considered stuck (30 minutes)
    STUCK_THRESHOLD_MINUTES = 30
    MAX_RETRIES = 3
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    try:
        # Find reports stuck in "processing" status
        url = f"{SUPABASE_URL}/rest/v1/user_reports?select=id,access_key,channel_name,channel_handle,status,user_id,updated_at,retry_count&status=eq.processing"
        resp = requests.get(url, headers=headers)
        
        if resp.status_code != 200:
            print(f"⚠️ Failed to fetch stuck jobs: {resp.text}")
            return
        
        processing_jobs = resp.json()
        if not processing_jobs:
            print("✅ No stuck jobs found")
            return
        
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        stuck_threshold = timedelta(minutes=STUCK_THRESHOLD_MINUTES)
        
        stuck_count = 0
        requeued_count = 0
        failed_count = 0
        
        for job in processing_jobs:
            # Check how long it's been processing
            updated_at = job.get('updated_at')
            if updated_at:
                try:
                    job_time = datetime.fromisoformat(updated_at.replace('Z', '+00:00')).replace(tzinfo=None)
                    time_stuck = now - job_time
                    
                    if time_stuck < stuck_threshold:
                        # Not stuck long enough, skip
                        continue
                except Exception:
                    pass  # If time parsing fails, treat as stuck
            
            stuck_count += 1
            access_key = job['access_key']
            retry_count = job.get('retry_count', 0) or 0
            
            if retry_count >= MAX_RETRIES:
                # Too many retries - mark as permanently failed
                print(f"   ❌ Marking as failed (max retries): {access_key}")
                update_url = f"{SUPABASE_URL}/rest/v1/user_reports?access_key=eq.{access_key}"
                requests.patch(
                    update_url,
                    headers=headers,
                    json={
                        "status": "failed",
                        "report_data": {"error": f"Analysis failed after {MAX_RETRIES} retry attempts"}
                    }
                )
                failed_count += 1
            else:
                # Re-queue with incremented retry count
                print(f"   🔄 Re-queuing (retry #{retry_count + 1}): {access_key}")
                
                # Update retry count
                update_url = f"{SUPABASE_URL}/rest/v1/user_reports?access_key=eq.{access_key}"
                requests.patch(
                    update_url,
                    headers=headers,
                    json={"status": "pending", "retry_count": retry_count + 1}
                )
                
                # Add to job queue
                job_data = {
                    'channel_name': job.get('channel_handle') or job.get('channel_name'),
                    'access_key': access_key,
                    'email': "recovered@gapintel.online",
                    'video_count': 20,
                    'tier': 'pro'
                }
                job_queue.enqueue(job_data)
                requeued_count += 1
        
        if stuck_count > 0:
            print(f"✅ Processed {stuck_count} stuck job(s): {requeued_count} re-queued, {failed_count} failed")
        else:
            print("✅ No stuck jobs found (all processing jobs are within time limit)")
        
    except Exception as e:
        print(f"⚠️ Error recovering stuck jobs: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifecycle."""
    print(f"🔧 Starting GAP Intel API v2.0.0 (Security Hardened)")
    print(f"   CORS: {len(ALLOWED_ORIGINS)} origins")
    print(f"   Rate Limit: 10/min")
    print(f"   Max Concurrent Jobs: {MAX_CONCURRENT_JOBS}")
    print(f"   API Auth: {'Enabled' if API_SECRET_KEY else 'Disabled (dev mode)'}")
    
    # Recover any stuck jobs from database
    print("🔍 Checking for stuck jobs...")
    recover_stuck_jobs()
    
    yield
    print("👋 Shutting down...")


app = FastAPI(
    title="GAP Intel Analysis API",
    description="Secure YouTube channel gap analysis service",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None,  # Disable Swagger in production
    redoc_url=None  # Disable ReDoc in production
)

# Restricted CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
    allow_credentials=False,
)


# ============================================
# API Routes
# ============================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "GAP Intel Analysis API",
        "version": "2.0.0"
    }

# Worker Heartbeat (to detect frozen threads)
last_worker_heartbeat = time.time()

def worker():
    """Background worker to process reports from the queue."""
    global last_worker_heartbeat
    print("👷 Worker started, waiting for jobs...")
    
    while True:
        try:
            # Update heartbeat
            last_worker_heartbeat = time.time()
            
            # blocked waiting for job
            job = job_queue.dequeue()
            if job:
                process_job(job)
            else:
                time.sleep(1) 
                
        except Exception as e:
            print(f"⚠️ Worker error: {e}")
            time.sleep(5)

@app.get("/health")
def health_check():
    """Health check endpoint for Railway."""
    # Check if worker is alive (heartbeat within last 10 minutes)
    time_since_heartbeat = time.time() - last_worker_heartbeat
    
    if time_since_heartbeat > 600:
        print(f"❌ Worker stuck! Last heartbeat {int(time_since_heartbeat)}s ago.")
        raise HTTPException(status_code=500, detail="Worker thread stuck")
        
    return {"status": "ok", "worker_heartbeat_age": int(time_since_heartbeat)}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: AnalyzeRequest,
    req: Request,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Trigger a gap analysis for a YouTube channel.
    Protected by API key authentication and rate limiting.
    """
    # Rate limiting
    client_ip = req.client.host if req.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    
    channel_name = request.channel_name
    access_key = request.access_key
    email = request.email
    include_shorts = request.include_shorts
    
    # Check if user is timed out
    from premium.subscription_manager import get_subscription_manager
    manager = get_subscription_manager()
    is_timed_out, expiry = await manager.check_timeout_status(email)
    if is_timed_out:
        raise HTTPException(status_code=429, detail=f"Account temporarily paused until {expiry} due to repeated failed reports.")
    video_count = request.video_count
    
    print(f"📨 Received analysis request: {access_key} ({video_count} videos)")

    # Create DB record - Skipped as Frontend now handles this in user_reports
    # db_success = create_analysis_record(access_key, channel_name, email)
    # if not db_success:
    #     print(f"⚠️ DB record creation failed for {access_key}")
    
    # Send start email
    send_analysis_started_email(email, channel_name, access_key)
    
    # Add to queue
    job_data = {
        'channel_name': channel_name,
        'access_key': access_key,
        'include_shorts': include_shorts,
        'email': email,
        'video_count': video_count,
        'tier': request.tier
    }
    job_queue.enqueue(job_data)
    
    queue_position = len(job_queue.queue)
    
    return AnalyzeResponse(
        status="queued",
        message=f"Analysis queued for @{channel_name}. Position: {queue_position}",
        access_key=access_key,
        queue_position=queue_position
    )


@app.get("/status/{access_key}")
async def get_status(access_key: str):
    """Check the status of an analysis."""
    # Basic validation
    if not access_key.startswith("GAP-") or len(access_key) > 50:
        raise HTTPException(status_code=400, detail="Invalid access key format")
    
    analysis = fetch_analysis_status(access_key)
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return {
        "access_key": access_key,
        "channel_name": analysis.get("channel_name"),
        "status": analysis.get("analysis_status"),
        "created_at": analysis.get("created_at"),
        "completed_at": analysis.get("report_generated_at")
    }


@app.get("/queue-status")
async def queue_status():
    """Get current queue status (public endpoint)."""
    return {
        "queue_length": len(job_queue.queue),
        "active_jobs": job_queue.active_jobs,
        "max_concurrent": job_queue.max_concurrent
    }


# ============================================
# Subscription Management Endpoints
# ============================================

@app.get("/subscription/status")
async def get_subscription_status(
    req: Request,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Get subscription status for a user.
    
    Query params:
    - email: User email address
    """
    email = req.query_params.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="email parameter required")
    
    try:
        from premium.subscription_manager import get_subscription_manager
        manager = get_subscription_manager()
        subscription = await manager.get_subscription(email)
        
        return {
            "status": "success",
            "subscription": {
                "tier": subscription.tier.value,
                "is_active": subscription.is_active,
                "analyses_this_month": subscription.analyses_this_month,
                "analyses_remaining": subscription.analyses_remaining,
                "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None
            },
            "limits": {
                "analyses_per_month": subscription.limits.analyses_per_month,
                "competitor_channels": subscription.limits.competitor_channels,
                "api_access": subscription.limits.api_access,
                "premium_features": subscription.limits.premium_features
            }
        }
    except Exception as e:
        print(f"❌ Subscription status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook/stripe-subscription")
async def stripe_subscription_webhook(req: Request):
    """
    Handle Stripe subscription webhooks.
    Updates user subscription status in database.
    """
    import stripe
    from datetime import datetime
    
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    payload = await req.body()
    sig_header = req.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except Exception as e:
        print(f"❌ Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle subscription events
    try:
        from premium.subscription_manager import get_subscription_manager
        manager = get_subscription_manager()
        
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            customer_email = session.get("customer_email")
            
            # Determine tier from metadata or price
            metadata = session.get("metadata", {})
            tier = metadata.get("tier", "starter")
            
            if customer_email:
                await manager.update_subscription(
                    email=customer_email,
                    tier=tier,
                    status="active",
                    stripe_customer_id=session.get("customer"),
                    stripe_subscription_id=session.get("subscription")
                )
                print(f"✅ New subscription: {customer_email} -> {tier}")
        
        elif event["type"] == "customer.subscription.updated":
            subscription = event["data"]["object"]
            customer_id = subscription.get("customer")
            status = subscription.get("status")
            
            # Map Stripe status to our status
            status_map = {"active": "active", "trialing": "trialing", 
                          "past_due": "past_due", "canceled": "cancelled"}
            
            # Get customer email from Stripe
            customer = stripe.Customer.retrieve(customer_id)
            customer_email = customer.get("email")
            
            if customer_email:
                # Determine tier from price
                price_id = subscription["items"]["data"][0]["price"]["id"]
                tier = _get_tier_from_price(price_id)
                
                period_end = datetime.fromtimestamp(subscription["current_period_end"])
                
                await manager.update_subscription(
                    email=customer_email,
                    tier=tier,
                    status=status_map.get(status, status),
                    stripe_customer_id=customer_id,
                    stripe_subscription_id=subscription.get("id"),
                    current_period_end=period_end
                )
                print(f"✅ Subscription updated: {customer_email} -> {tier} ({status})")
        
        elif event["type"] == "customer.subscription.deleted":
            subscription = event["data"]["object"]
            customer_id = subscription.get("customer")
            
            customer = stripe.Customer.retrieve(customer_id)
            customer_email = customer.get("email")
            
            if customer_email:
                await manager.update_subscription(
                    email=customer_email,
                    tier="free",
                    status="cancelled",
                    stripe_customer_id=customer_id
                )
                print(f"✅ Subscription cancelled: {customer_email}")
        
        return {"status": "received"}
    
    except Exception as e:
        print(f"❌ Webhook processing error: {e}")
        return {"status": "error", "message": str(e)}


def _get_tier_from_price(price_id: str) -> str:
    """Map Stripe price ID to tier name."""
    # These should match your Stripe price IDs
    price_tiers = {
        os.getenv("STRIPE_PRICE_STARTER"): "starter",
        os.getenv("STRIPE_PRICE_PRO"): "pro", 
        os.getenv("STRIPE_PRICE_ENTERPRISE"): "enterprise"
    }
    return price_tiers.get(price_id, "starter")


# ============================================
# Premium Analysis Endpoints
# ============================================


@app.post("/premium/analyze-thumbnail")
async def analyze_thumbnail(
    req: Request,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Analyze a thumbnail and predict CTR.
    Requires API key authentication AND active subscription.
    
    Request body:
    {
        "thumbnail_url": "https://...",
        "title": "Video Title",
        "user_email": "subscriber@email.com"
    }
    """
    # Rate limiting
    client_ip = req.client.host if req.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    try:
        body = await req.json()
        thumbnail_url = body.get("thumbnail_url")
        title = body.get("title", "")
        user_email = body.get("user_email")
        
        if not thumbnail_url:
            raise HTTPException(status_code=400, detail="thumbnail_url is required")
        
        if not user_email:
            raise HTTPException(status_code=400, detail="user_email is required for subscription verification")
        
        # Verify subscription
        from premium.subscription_manager import get_subscription_manager
        manager = get_subscription_manager()
        subscription = await manager.get_subscription(user_email)
        
        # Check access
        can_access, error_msg = manager.check_feature_access(subscription, "premium_features")
        if not can_access:
            raise HTTPException(status_code=403, detail=error_msg)
        
        can_analyze, error_msg = manager.check_feature_access(subscription, "analyze")
        if not can_analyze:
            raise HTTPException(status_code=403, detail=error_msg)
        
        # Import premium modules (lazy load)
        from premium.thumbnail_extractor import ThumbnailFeatureExtractor
        from premium.ml_models.ctr_predictor import CTRPredictor
        
        # Extract features
        extractor = ThumbnailFeatureExtractor(use_ocr=False, use_face_detection=True)
        features = extractor.extract_from_url(thumbnail_url)
        
        # Predict CTR
        predictor = CTRPredictor()
        prediction = predictor.predict(features.to_dict(), title)
        
        # Increment usage
        await manager.increment_usage(user_email)
        
        return {
            "status": "success",
            "subscription": {
                "tier": subscription.tier.value,
                "analyses_remaining": subscription.analyses_remaining - 1
            },
            "thumbnail_analysis": {
                "features": features.to_dict(),
                "ctr_prediction": prediction.to_dict()
            }

        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Thumbnail analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/premium/predict-ctr")
async def predict_ctr(
    req: Request,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Predict CTR for a video concept.
    
    Request body:
    {
        "thumbnail_features": {...},  // From thumbnail analysis
        "title": "Proposed Video Title"
    }
    """
    client_ip = req.client.host if req.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    try:
        body = await req.json()
        thumbnail_features = body.get("thumbnail_features", {})
        title = body.get("title", "")
        
        from premium.ml_models.ctr_predictor import CTRPredictor
        
        predictor = CTRPredictor()
        prediction = predictor.predict(thumbnail_features, title)
        
        return {
            "status": "success",
            "prediction": prediction.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ CTR prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/premium/discover-competitors")
async def discover_competitors(
    req: Request,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Discover competitor channels for a given channel.
    
    Request body:
    {
        "channel_handle": "@ChannelName",
        "max_competitors": 10,
        "search_terms": ["optional", "keywords"]
    }
    """
    client_ip = req.client.host if req.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    try:
        body = await req.json()
        channel_handle = body.get("channel_handle")
        max_competitors = body.get("max_competitors", 10)
        search_terms = body.get("search_terms")
        
        if not channel_handle:
            raise HTTPException(status_code=400, detail="channel_handle is required")
        
        from premium.data_collector import YouTubeDataCollector
        
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="YouTube API key not configured")
        
        collector = YouTubeDataCollector(api_key)
        
        # Resolve channel
        channel_id, channel_name = collector.get_channel_id(channel_handle)
        
        # Discover competitors
        competitors = collector.discover_competitors(
            channel_id, 
            search_terms=search_terms,
            max_competitors=max_competitors
        )
        
        return {
            "status": "success",
            "channel": {
                "id": channel_id,
                "name": channel_name
            },
            "competitors": competitors
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Competitor discovery error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/premium/features")
async def list_premium_features():
    """List available premium analysis features."""
    return {
        "features": [
            {
                "endpoint": "/premium/analyze-thumbnail",
                "description": "Extract 50+ features from a thumbnail and predict CTR",
                "requires_auth": True
            },
            {
                "endpoint": "/premium/predict-ctr",
                "description": "Predict click-through rate for a video concept",
                "requires_auth": True
            },
            {
                "endpoint": "/premium/discover-competitors",
                "description": "Discover competitor channels in your niche",
                "requires_auth": True
            },
            {
                "endpoint": "/premium/optimize-thumbnail",
                "description": "Get optimization suggestions for a thumbnail",
                "requires_auth": True
            },
            {
                "endpoint": "/premium/optimal-publish-times",
                "description": "Find optimal publishing times",
                "requires_auth": True
            },
            {
                "endpoint": "/premium/gap-analysis",
                "description": "Comprehensive content gap discovery",
                "requires_auth": True
            },
            {
                "endpoint": "/premium/generate-report",
                "description": "Generate premium analysis report",
                "requires_auth": True
            },
            {
                "endpoint": "/premium/predict-views",
                "description": "Predict view trajectory from early signals",
                "requires_auth": True
            }
        ],
        "version": "2.0.0"
    }


@app.post("/premium/optimize-thumbnail")
async def optimize_thumbnail(
    req: Request,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Get optimization suggestions for a thumbnail.
    
    Request body:
    {
        "thumbnail_url": "https://...",
        "title": "Video Title",
        "topic": "optional topic"
    }
    """
    client_ip = req.client.host if req.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    try:
        body = await req.json()
        thumbnail_url = body.get("thumbnail_url")
        title = body.get("title", "")
        topic = body.get("topic", "")
        
        if not thumbnail_url:
            raise HTTPException(status_code=400, detail="thumbnail_url is required")
        
        from premium.thumbnail_extractor import ThumbnailFeatureExtractor
        from premium.thumbnail_optimizer import ThumbnailOptimizer
        
        # Extract features
        extractor = ThumbnailFeatureExtractor(use_ocr=False, use_face_detection=True)
        features = extractor.extract_from_url(thumbnail_url)
        
        # Optimize
        optimizer = ThumbnailOptimizer()
        result = optimizer.analyze_and_optimize(features.to_dict(), title, topic)
        
        return {
            "status": "success",
            "optimization": result.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Thumbnail optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/premium/optimal-publish-times")
async def get_optimal_publish_times(
    req: Request,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Find optimal publishing times.
    
    Request body:
    {
        "content_type": "tutorial|news|entertainment|etc",
        "videos": [...] (optional channel video data)
    }
    """
    client_ip = req.client.host if req.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    try:
        body = await req.json()
        content_type = body.get("content_type", "general")
        videos = body.get("videos", [])
        
        from premium.publish_optimizer import PublishTimeOptimizer
        
        optimizer = PublishTimeOptimizer()
        result = optimizer.analyze_optimal_times(
            videos=videos if videos else None,
            content_type=content_type
        )
        
        return {
            "status": "success",
            "publish_optimization": result.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Publish time optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/premium/gap-analysis")
async def comprehensive_gap_analysis(
    req: Request,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Comprehensive content gap discovery.
    
    Request body:
    {
        "channel_videos": [...],
        "competitor_videos": [...] (optional),
        "comment_gaps": [...] (optional, from regular analysis),
        "trends": ["topic1", "topic2"] (optional)
    }
    """
    client_ip = req.client.host if req.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    try:
        body = await req.json()
        channel_videos = body.get("channel_videos", [])
        competitor_videos = body.get("competitor_videos", [])
        comment_gaps = body.get("comment_gaps", [])
        trends = body.get("trends", [])
        
        if not channel_videos:
            raise HTTPException(status_code=400, detail="channel_videos is required")
        
        from premium.enhanced_gap_analyzer import EnhancedGapAnalyzer
        
        analyzer = EnhancedGapAnalyzer()
        result = analyzer.analyze_comprehensive_gaps(
            channel_videos=channel_videos,
            competitor_videos=competitor_videos if competitor_videos else None,
            comment_gaps=comment_gaps if comment_gaps else None,
            trends=trends if trends else None
        )
        
        return {
            "status": "success",
            "gap_analysis": result.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Gap analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/premium/predict-views")
async def predict_view_trajectory(
    req: Request,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Predict view trajectory from early signals.
    
    Request body:
    {
        "views_1h": 1000,
        "views_6h": 5000,
        "views_24h": 15000,
        "likes_24h": 800,
        "comments_24h": 50,
        "subscriber_count": 50000
    }
    """
    client_ip = req.client.host if req.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    try:
        body = await req.json()
        
        if not body.get("views_24h"):
            raise HTTPException(status_code=400, detail="views_24h is required")
        
        from premium.ml_models.views_predictor import ViewsVelocityPredictor
        
        predictor = ViewsVelocityPredictor()
        prediction = predictor.predict_trajectory(body)
        
        return {
            "status": "success",
            "prediction": prediction.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Views prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/premium/generate-report")
async def generate_premium_report(
    req: Request,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Generate comprehensive premium analysis report.
    
    Request body:
    {
        "channel": {...},
        "videos": [...],
        "thumbnail_analysis": {...},
        "competitor_analysis": {...},
        "gap_analysis": {...}
    }
    """
    client_ip = req.client.host if req.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    try:
        body = await req.json()
        
        from premium.report_generator import PremiumReportGenerator
        
        generator = PremiumReportGenerator()
        report = generator.generate_premium_report(body)
        
        return {
            "status": "success",
            "report": report
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Report generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/premium/cluster-content")
async def cluster_channel_content(
    req: Request,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Cluster videos by topic/format to find winning formulas.
    
    Request body:
    {
        "videos": [
            {"title": "...", "view_count": 10000, "engagement_rate": 5.0},
            ...
        ],
        "n_clusters": 5
    }
    """
    client_ip = req.client.host if req.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    try:
        body = await req.json()
        videos = body.get("videos", [])
        n_clusters = body.get("n_clusters", 5)
        
        if not videos or len(videos) < 3:
            raise HTTPException(status_code=400, detail="At least 3 videos required")
        
        from premium.ml_models.content_clusterer import ContentClusteringEngine
        
        engine = ContentClusteringEngine(use_embeddings=False)
        result = engine.cluster_channel_content(videos, n_clusters)
        
        return {
            "status": "success",
            "clustering": result.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Content clustering error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 🏢 ENTERPRISE API ENDPOINTS
# ============================================

from premium.enterprise_manager import api_key_manager, team_manager, branding_manager

# Public API key header
public_api_key_header = APIKeyHeader(name="X-GAP-API-Key", auto_error=False)


class PublicAnalyzeRequest(BaseModel):
    """Request model for public API analysis."""
    channel_name: str
    video_count: int = 5
    webhook_url: str = None  # Optional webhook for async results
    
    @validator('channel_name')
    def validate_channel(cls, v):
        v = v.lstrip('@').strip()
        if not re.match(r'^[\w\-]+$', v):
            raise ValueError('Invalid channel name')
        return v
    
    @validator('video_count')
    def validate_count(cls, v):
        if v < 1 or v > 50:
            raise ValueError('video_count must be 1-50')
        return v


@app.post("/api/v1/analyze")
async def public_api_analyze(
    request: PublicAnalyzeRequest,
    api_key: str = Depends(public_api_key_header)
):
    """
    🔓 PUBLIC API - Analyze a YouTube channel (Enterprise only)
    
    Requires X-GAP-API-Key header with valid Enterprise API key.
    Rate limited to 500 calls per day.
    
    Returns analysis_id to check status, or use webhook for async notification.
    """
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-GAP-API-Key header")
    
    # Validate API key
    validation = api_key_manager.validate_api_key(api_key)
    
    if not validation['valid']:
        raise HTTPException(status_code=401, detail=validation.get('error', 'Invalid API key'))
    
    if validation.get('rate_limited'):
        raise HTTPException(
            status_code=429, 
            detail=f"Rate limit exceeded. Resets at midnight UTC. Remaining: 0/500"
        )
    
    # Generate access key for this analysis
    import secrets
    access_key = f"GAP-API-{secrets.token_hex(8).upper()}"
    
    # Increment usage counter
    api_key_manager.increment_usage(validation['key_id'])
    
    # Create report record in database
    org_id = validation['organization_id']
    
    # Get branding for this org
    branding = branding_manager.get_branding(org_id)
    
    # Create report in Supabase
    report_data = {
        'channel_name': request.channel_name,
        'access_key': access_key,
        'status': 'pending',
        'tier': 'enterprise',
        'organization_id': org_id,
        'webhook_url': request.webhook_url,
        'branding': branding  # Include white-label branding
    }
    
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/user_reports",
        headers={
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        },
        json=report_data
    )
    
    if response.status_code not in [200, 201]:
        raise HTTPException(status_code=500, detail="Failed to create analysis record")
    
    # Queue the analysis
    job_data = {
        'channel_name': request.channel_name,
        'access_key': access_key,
        'email': '',  # No email for API calls
        'video_count': request.video_count,
        'tier': 'enterprise',
        'webhook_url': request.webhook_url,
        'branding': branding
    }
    job_queue.enqueue(job_data)
    
    return {
        "status": "queued",
        "analysis_id": access_key,
        "channel": request.channel_name,
        "video_count": request.video_count,
        "calls_remaining": validation['calls_remaining'] - 1,
        "status_url": f"https://thriving-presence-production-ca4a.up.railway.app/api/v1/status/{access_key}",
        "report_url": f"https://www.gapintel.online/report/{access_key}"
    }


@app.get("/api/v1/status/{analysis_id}")
async def public_api_status(
    analysis_id: str,
    api_key: str = Depends(public_api_key_header)
):
    """Get status of an API-initiated analysis."""
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-GAP-API-Key header")
    
    validation = api_key_manager.validate_api_key(api_key)
    if not validation['valid']:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Fetch analysis
    analysis = fetch_analysis_status(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Verify this analysis belongs to the org
    if analysis.get('organization_id') != validation['organization_id']:
        raise HTTPException(status_code=403, detail="Not authorized to view this analysis")
    
    result = {
        "analysis_id": analysis_id,
        "status": analysis.get("status"),
        "channel_name": analysis.get("channel_name"),
        "created_at": analysis.get("created_at")
    }
    
    # Include full report data if completed
    if analysis.get("status") == "completed" and analysis.get("report_data"):
        result["report"] = analysis["report_data"]
    
    return result


@app.get("/api/v1/usage")
async def public_api_usage(api_key: str = Depends(public_api_key_header)):
    """Get current API usage statistics."""
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-GAP-API-Key header")
    
    validation = api_key_manager.validate_api_key(api_key)
    if not validation['valid']:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return {
        "calls_today": 500 - validation['calls_remaining'],
        "calls_remaining": validation['calls_remaining'],
        "daily_limit": 500,
        "resets_at": "00:00 UTC"
    }


# ============================================
# 👥 TEAM MANAGEMENT ENDPOINTS
# ============================================

class InviteMemberRequest(BaseModel):
    email: str
    role: str = "viewer"
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ['admin', 'editor', 'viewer']:
            raise ValueError('Role must be admin, editor, or viewer')
        return v


@app.get("/enterprise/organization")
async def get_organization(authenticated: bool = Depends(verify_api_key)):
    """Get current user's organization."""
    # In production, get user_id from JWT token
    # For now, this requires the internal API key
    return {"message": "Use frontend API routes for organization management"}


@app.post("/enterprise/team/invite")
async def invite_team_member(
    request: InviteMemberRequest,
    org_id: str,
    user_id: str,
    authenticated: bool = Depends(verify_api_key)
):
    """Invite a new team member."""
    try:
        member = team_manager.invite_member(org_id, request.email, request.role, user_id)
        return {"status": "invited", "member": member}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/enterprise/team/{member_id}")
async def remove_team_member(
    member_id: str,
    org_id: str,
    authenticated: bool = Depends(verify_api_key)
):
    """Remove a team member."""
    success = team_manager.remove_member(member_id, org_id)
    if success:
        return {"status": "removed"}
    raise HTTPException(status_code=400, detail="Failed to remove member")


# ============================================
# 🔑 API KEY MANAGEMENT ENDPOINTS
# ============================================

class CreateAPIKeyRequest(BaseModel):
    name: str = "Default API Key"


@app.post("/enterprise/api-keys")
async def create_api_key(
    request: CreateAPIKeyRequest,
    org_id: str,
    authenticated: bool = Depends(verify_api_key)
):
    """Create a new API key for the organization."""
    try:
        full_key, key_prefix = api_key_manager.generate_api_key(org_id, request.name)
        return {
            "status": "created",
            "api_key": full_key,  # Only shown once!
            "key_prefix": key_prefix,
            "warning": "Save this key securely. It will not be shown again."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/enterprise/api-keys")
async def list_api_keys(
    org_id: str,
    authenticated: bool = Depends(verify_api_key)
):
    """List all API keys for the organization (prefixes only)."""
    keys = api_key_manager.get_organization_keys(org_id)
    return {"keys": keys}


@app.delete("/enterprise/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    org_id: str,
    authenticated: bool = Depends(verify_api_key)
):
    """Revoke an API key."""
    success = api_key_manager.revoke_key(key_id, org_id)
    if success:
        return {"status": "revoked"}
    raise HTTPException(status_code=400, detail="Failed to revoke key")


# ============================================
# 🎨 WHITE-LABEL BRANDING ENDPOINTS
# ============================================

class BrandingRequest(BaseModel):
    logo_url: str = None
    primary_color: str = "#7cffb2"
    secondary_color: str = "#1a1a2e"
    accent_color: str = "#b8b8ff"
    company_name: str = None
    custom_footer_text: str = None
    hide_gap_intel_branding: bool = False


@app.get("/enterprise/branding")
async def get_branding(
    org_id: str,
    authenticated: bool = Depends(verify_api_key)
):
    """Get organization's branding settings."""
    branding = branding_manager.get_branding(org_id)
    return {"branding": branding or {}}


@app.put("/enterprise/branding")
async def update_branding(
    request: BrandingRequest,
    org_id: str,
    authenticated: bool = Depends(verify_api_key)
):
    """Update organization's branding settings."""
    try:
        branding = branding_manager.update_branding(org_id, request.dict())
        return {"status": "updated", "branding": branding}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/predict-video")
async def predict_video(request: Request):
    """
    Predict viral potential for a video idea.
    """
    try:
        data = await request.json()
        title = data.get('title')
        hook = data.get('hook', '')
        topic = data.get('topic', 'General')
        access_key = data.get('access_key')
        
        if not title:
            raise HTTPException(status_code=400, detail="Title is required")

        history = data.get('history', [])
        channel_name_context = ""

        # Fetch history from report if access_key provided
        if access_key:
            analysis = fetch_analysis_status(access_key)
            if analysis and analysis.get("report_data"):
                report = analysis["report_data"]
                channel_name_context = report.get("channelName", "")
                
                # Try to extract history from various report sections
                # 1. Premium views forecast history
                if report.get("premium", {}).get("views_forecast", {}).get("forecasts"):
                     # This usually contains recent videos
                     pass
                
                # 2. Videos analyzed list (most reliable if populated with views)
                if report.get("videos_analyzed"):
                    # Transform to expected history format
                    # {title, view_count, like_count, comment_count}
                    for v in report["videos_analyzed"]:
                        history.append({
                            "title": v.get("title", ""),
                            "view_count": v.get("view_count", 0),  # Ensure backend saves this
                            "like_count": v.get("like_count", 0),
                            "comment_count": v.get("comments_count", 0)
                        })

        from premium.ml_models.viral_predictor import ViralPredictor
        predictor = ViralPredictor()
        
        prediction = predictor.predict(title, hook, topic, history)
        
        return {
            'predicted_views': prediction.predicted_views,
            'viral_probability': prediction.viral_probability,
            'confidence': prediction.confidence_score,
            'factors': prediction.factors,
            'tips': prediction.tips,
            'channel_context': channel_name_context
        }

    except Exception as e:
        print(f"Prediction failed: {str(e)}") # Use print as logger might be missing
        raise HTTPException(status_code=500, detail=str(e))


def periodic_stuck_job_checker():
    """
    Background thread that periodically checks for stuck jobs.
    Runs every 15 minutes to catch jobs that got stuck without server restart.
    """
    import time
    CHECK_INTERVAL_MINUTES = 15
    
    print(f"🔄 Starting periodic stuck job checker (every {CHECK_INTERVAL_MINUTES} min)")
    
    while True:
        time.sleep(CHECK_INTERVAL_MINUTES * 60)
        try:
            print(f"🔍 Periodic check: Looking for stuck jobs...")
            recover_stuck_jobs()
        except Exception as e:
            print(f"⚠️ Periodic stuck job check failed: {e}")


@app.on_event("startup")
async def on_startup():
    """Run recovery tasks on startup and start periodic checker."""
    # Start periodic stuck job checker in background
    threading.Thread(target=periodic_stuck_job_checker, daemon=True).start()


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

