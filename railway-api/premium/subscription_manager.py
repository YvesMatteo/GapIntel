"""
Subscription Management - Verification and Tier Gating
Handles subscription status checking and usage tracking.
"""

import os
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from functools import wraps

# Supabase client
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


class SubscriptionTier(Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class TierLimits:
    """Usage limits per tier."""
    analyses_per_month: int
    api_calls_per_day: int  # Rate limit for API access
    competitor_channels: int
    api_access: bool
    premium_features: bool
    report_generation: bool
    white_label: bool


# Tier configurations - strict limits to protect resources
# API calls that create reports also count towards analyses_per_month
TIER_LIMITS = {
    SubscriptionTier.FREE: TierLimits(
        analyses_per_month=0,
        api_calls_per_day=0,
        competitor_channels=0,
        api_access=False,
        premium_features=False,
        report_generation=False,
        white_label=False
    ),
    SubscriptionTier.STARTER: TierLimits(
        analyses_per_month=1,           # 1 report per month
        api_calls_per_day=0,            # No API access
        competitor_channels=3,
        api_access=False,
        premium_features=True,
        report_generation=True,
        white_label=False
    ),
    SubscriptionTier.PRO: TierLimits(
        analyses_per_month=5,           # 5 reports per month
        api_calls_per_day=0,            # No API access for Pro
        competitor_channels=10,
        api_access=False,
        premium_features=True,
        report_generation=True,
        white_label=False
    ),
    SubscriptionTier.ENTERPRISE: TierLimits(
        analyses_per_month=25,          # 25 reports per month (API calls count towards this)
        api_calls_per_day=500,          # 500 API calls per day max
        competitor_channels=100,
        api_access=True,
        premium_features=True,
        report_generation=True,
        white_label=True
    )
}


@dataclass
class UserSubscription:
    """User subscription info."""
    email: str
    tier: SubscriptionTier
    status: str
    analyses_this_month: int
    analyses_reset_at: datetime
    current_period_end: Optional[datetime]
    stripe_customer_id: Optional[str] = None
    user_id: Optional[str] = None
    
    @property
    def limits(self) -> TierLimits:
        return TIER_LIMITS[self.tier]
    
    @property
    def is_active(self) -> bool:
        return self.status in ('active', 'trialing')
    
    @property
    def can_analyze(self) -> bool:
        if not self.is_active:
            return False
        return self.analyses_this_month < self.limits.analyses_per_month
    
    @property
    def analyses_remaining(self) -> int:
        return max(0, self.limits.analyses_per_month - self.analyses_this_month)


class SubscriptionManager:
    """
    Manages subscription verification and usage tracking.
    
    Usage:
        manager = SubscriptionManager()
        sub = await manager.get_subscription("user@email.com")
        if sub.can_analyze:
            await manager.increment_usage("user@email.com")
    """
    
    def __init__(self):
        self.supabase: Optional[Client] = None
        if SUPABASE_AVAILABLE:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_SERVICE_KEY")
            if url and key:
                self.supabase = create_client(url, key)
    
    async def get_subscription(self, email: str) -> UserSubscription:
        """Get subscription info for a user."""
        if not self.supabase:
            # Fallback for development - return free tier
            return UserSubscription(
                email=email,
                tier=SubscriptionTier.FREE,
                status="active",
                analyses_this_month=0,
                analyses_reset_at=datetime.now(),
                current_period_end=None
            )
        
        try:
            result = self.supabase.table("user_subscriptions").select("*").eq("user_email", email).single().execute()
            
            if result.data:
                data = result.data
                return UserSubscription(
                    email=data["user_email"],
                    tier=SubscriptionTier(data["tier"]),
                    status=data["status"],
                    analyses_this_month=data["analyses_this_month"],
                    analyses_reset_at=datetime.fromisoformat(data["analyses_reset_at"].replace("Z", "+00:00")),
                    current_period_end=datetime.fromisoformat(data["current_period_end"].replace("Z", "+00:00")) if data.get("current_period_end") else None,
                    stripe_customer_id=data.get("stripe_customer_id"),
                    user_id=data.get("user_id")
                )
            else:
                # No subscription found - create free tier entry
                return await self._create_free_subscription(email)
                
        except Exception as e:
            print(f"⚠️ Subscription lookup error: {e}")
            return UserSubscription(
                email=email,
                tier=SubscriptionTier.FREE,
                status="active",
                analyses_this_month=0,
                analyses_reset_at=datetime.now(),
                current_period_end=None,
                user_id=None
            )
    
    async def _create_free_subscription(self, email: str) -> UserSubscription:
        """Create a free tier subscription for new user."""
        try:
            self.supabase.table("user_subscriptions").insert({
                "user_email": email,
                "tier": "free",
                "status": "active",
                "analyses_this_month": 0
            }).execute()
        except:
            pass  # Ignore if already exists
        
        return UserSubscription(
            email=email,
            tier=SubscriptionTier.FREE,
            status="active",
            analyses_this_month=0,
            analyses_reset_at=datetime.now(),
            current_period_end=None
        )
    
    async def increment_usage(self, email: str) -> bool:
        """Increment analysis usage count."""
        if not self.supabase:
            return True
        
        try:
            # Get current count
            result = self.supabase.table("user_subscriptions").select("analyses_this_month, analyses_reset_at").eq("user_email", email).single().execute()
            
            if result.data:
                current = result.data["analyses_this_month"]
                reset_at = datetime.fromisoformat(result.data["analyses_reset_at"].replace("Z", "+00:00"))
                
                # Check if needs reset (new month)
                if datetime.now(reset_at.tzinfo) > reset_at + timedelta(days=30):
                    current = 0
                    self.supabase.table("user_subscriptions").update({
                        "analyses_this_month": 1,
                        "analyses_reset_at": datetime.now().isoformat()
                    }).eq("user_email", email).execute()
                else:
                    self.supabase.table("user_subscriptions").update({
                        "analyses_this_month": current + 1
                    }).eq("user_email", email).execute()
                
                return True
        except Exception as e:
            print(f"⚠️ Usage increment error: {e}")
        
        return False
    
    async def update_subscription(self, 
                                   email: str, 
                                   tier: str, 
                                   status: str,
                                   stripe_customer_id: str = None,
                                   stripe_subscription_id: str = None,
                                   current_period_end: datetime = None) -> bool:
        """Update subscription after Stripe webhook."""
        if not self.supabase:
            return False
        
        try:
            # Check if user exists
            existing = self.supabase.table("user_subscriptions").select("id").eq("user_email", email).execute()
            
            data = {
                "user_email": email,
                "tier": tier,
                "status": status,
                "stripe_customer_id": stripe_customer_id,
                "stripe_subscription_id": stripe_subscription_id,
                "current_period_end": current_period_end.isoformat() if current_period_end else None
            }
            
            if existing.data:
                self.supabase.table("user_subscriptions").update(data).eq("user_email", email).execute()
            else:
                data["analyses_this_month"] = 0
                self.supabase.table("user_subscriptions").insert(data).execute()
            
            return True
        except Exception as e:
            print(f"⚠️ Subscription update error: {e}")
            return False
    
    def check_feature_access(self, subscription: UserSubscription, feature: str) -> Tuple[bool, str]:
        """
        Check if user has access to a specific feature.
        
        Returns:
            (has_access, error_message)
        """
        if not subscription.is_active:
            return False, "Subscription is not active. Please resubscribe."
        
        limits = subscription.limits
        
        # Feature checks
        if feature == "premium_features" and not limits.premium_features:
            return False, f"Premium features require Starter ($29/mo) or higher. You're on {subscription.tier.value}."
        
        if feature == "api_access" and not limits.api_access:
            return False, f"API access requires Enterprise ($129/mo). You're on {subscription.tier.value}."
        
        if feature == "analyze" and not subscription.can_analyze:
            remaining = subscription.analyses_remaining
            if remaining == 0:
                return False, f"Monthly analysis limit reached ({limits.analyses_per_month}/month). Upgrade for more analyses."
            return True, ""
        
        if feature == "report" and not limits.report_generation:
            return False, f"Report generation requires Starter ($29/mo) or higher."
        
        if feature == "white_label" and not limits.white_label:
            return False, f"White-label reports require Enterprise ($129/mo)."
        
        return True, ""

    async def decrement_usage(self, email: str) -> bool:
        """Decrement analysis usage count (for failed reports)."""
        if not self.supabase:
            return True
        
        try:
            # Get current count
            result = self.supabase.table("user_subscriptions").select("analyses_this_month").eq("user_email", email).single().execute()
            
            if result.data:
                current = result.data["analyses_this_month"]
                if current > 0:
                    self.supabase.table("user_subscriptions").update({
                        "analyses_this_month": current - 1
                    }).eq("user_email", email).execute()
                    return True
        except Exception as e:
            print(f"⚠️ Usage decrement error: {e}")
        
        return False

    async def check_timeout_status(self, email: str) -> Tuple[bool, str]:
        """
        Check if user is temporarily timed out due to failures.
        Returns (is_timed_out, timeout_expiry_iso_string)
        """
        if not self.supabase:
            return False, ""
            
        try:
            # First get user_id
            sub = await self.get_subscription(email)
            if not sub.user_id:
                return False, ""
                
            # Check last 5 reports
            result = self.supabase.table("user_reports").select("status, created_at").eq("user_id", sub.user_id).order("created_at", desc=True).limit(5).execute()
            
            reports = result.data
            if not reports or len(reports) < 5:
                return False, ""
                
            # Check if all 5 failed
            if all(r["status"] == "failed" for r in reports):
                # Check time of latest failure
                latest_fail = datetime.fromisoformat(reports[0]["created_at"].replace("Z", "+00:00"))
                timeout_end = latest_fail + timedelta(hours=1)
                
                if datetime.now(latest_fail.tzinfo) < timeout_end:
                    return True, timeout_end.isoformat()
                    
        except Exception as e:
            print(f"⚠️ Timeout check error: {e}")
            
        return False, ""


# Singleton instance
_manager: Optional[SubscriptionManager] = None

def get_subscription_manager() -> SubscriptionManager:
    """Get the subscription manager singleton."""
    global _manager
    if _manager is None:
        _manager = SubscriptionManager()
    return _manager
