"""
Enterprise API Key Manager
Handles API key generation, validation, and rate limiting for Enterprise tier.
"""

import os
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
import requests

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL') or os.getenv('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

class APIKeyManager:
    """Manages API keys for Enterprise tier users."""
    
    # Rate limits by tier
    RATE_LIMITS = {
        'starter': 0,
        'pro': 0, 
        'enterprise': 500
    }
    
    def __init__(self):
        self.base_url = SUPABASE_URL
        self.headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            'Content-Type': 'application/json'
        }
    
    def generate_api_key(self, organization_id: str, name: str = "Default API Key") -> Tuple[str, str]:
        """
        Generate a new API key for an organization.
        
        Returns:
            Tuple of (full_key, key_prefix) - full key is only shown once!
        """
        # Generate a secure random key
        random_part = secrets.token_urlsafe(32)
        full_key = f"gapi_{random_part}"
        key_prefix = full_key[:12]  # "gapi_XXXXXXX"
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        
        # Store in database
        payload = {
            'organization_id': organization_id,
            'name': name,
            'key_prefix': key_prefix,
            'key_hash': key_hash,
            'scopes': ['analyze', 'read'],
            'calls_today': 0,
            'is_active': True
        }
        
        response = requests.post(
            f"{self.base_url}/rest/v1/api_keys",
            headers=self.headers,
            json=payload
        )
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to create API key: {response.text}")
        
        return full_key, key_prefix
    
    def validate_api_key(self, api_key: str) -> Dict[str, Any]:
        """
        Validate an API key and check rate limits.
        
        Returns:
            Dict with validation result:
            {
                'valid': bool,
                'organization_id': str,
                'rate_limited': bool,
                'calls_remaining': int,
                'error': str (if invalid)
            }
        """
        if not api_key or not api_key.startswith('gapi_'):
            return {'valid': False, 'error': 'Invalid API key format'}
        
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_prefix = api_key[:12]
        
        # Lookup key in database
        response = requests.get(
            f"{self.base_url}/rest/v1/api_keys",
            headers=self.headers,
            params={
                'key_hash': f'eq.{key_hash}',
                'is_active': 'eq.true',
                'select': 'id,organization_id,calls_today,last_reset_at,scopes'
            }
        )
        
        if response.status_code != 200:
            return {'valid': False, 'error': 'Database error'}
        
        keys = response.json()
        if not keys:
            return {'valid': False, 'error': 'API key not found or inactive'}
        
        key_data = keys[0]
        
        # Check if we need to reset daily counter
        last_reset = key_data.get('last_reset_at')
        calls_today = key_data.get('calls_today', 0)
        
        if last_reset:
            last_reset_date = datetime.fromisoformat(last_reset.replace('Z', '+00:00')).date()
            today = datetime.now(timezone.utc).date()
            if last_reset_date < today:
                # Reset counter
                calls_today = 0
                self._reset_daily_counter(key_data['id'])
        
        # Check rate limit (500 for enterprise)
        daily_limit = 500
        if calls_today >= daily_limit:
            return {
                'valid': True,
                'organization_id': key_data['organization_id'],
                'rate_limited': True,
                'calls_remaining': 0,
                'error': 'Daily rate limit exceeded'
            }
        
        return {
            'valid': True,
            'organization_id': key_data['organization_id'],
            'key_id': key_data['id'],
            'rate_limited': False,
            'calls_remaining': daily_limit - calls_today,
            'scopes': key_data.get('scopes', [])
        }
    
    def increment_usage(self, key_id: str) -> bool:
        """Increment the API call counter for a key."""
        response = requests.post(
            f"{self.base_url}/rest/v1/rpc/increment_api_call",
            headers=self.headers,
            json={'key_id': key_id}
        )
        return response.status_code == 200
    
    def _reset_daily_counter(self, key_id: str):
        """Reset the daily call counter."""
        requests.patch(
            f"{self.base_url}/rest/v1/api_keys",
            headers=self.headers,
            params={'id': f'eq.{key_id}'},
            json={
                'calls_today': 0,
                'last_reset_at': datetime.now(timezone.utc).isoformat()
            }
        )
    
    def get_organization_keys(self, organization_id: str) -> list:
        """Get all API keys for an organization."""
        response = requests.get(
            f"{self.base_url}/rest/v1/api_keys",
            headers=self.headers,
            params={
                'organization_id': f'eq.{organization_id}',
                'select': 'id,name,key_prefix,calls_today,calls_total,is_active,created_at'
            }
        )
        
        if response.status_code == 200:
            return response.json()
        return []
    
    def revoke_key(self, key_id: str, organization_id: str) -> bool:
        """Revoke an API key."""
        response = requests.patch(
            f"{self.base_url}/rest/v1/api_keys",
            headers=self.headers,
            params={
                'id': f'eq.{key_id}',
                'organization_id': f'eq.{organization_id}'
            },
            json={'is_active': False}
        )
        return response.status_code == 200


class TeamManager:
    """Manages team members for Enterprise organizations."""
    
    def __init__(self):
        self.base_url = SUPABASE_URL
        self.headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            'Content-Type': 'application/json'
        }
    
    def get_organization(self, user_id: str) -> Optional[Dict]:
        """Get the organization for a user (as owner or member)."""
        # Check if user owns an org
        response = requests.get(
            f"{self.base_url}/rest/v1/organizations",
            headers=self.headers,
            params={
                'owner_id': f'eq.{user_id}',
                'select': '*'
            }
        )
        
        if response.status_code == 200 and response.json():
            return response.json()[0]
        
        # Check if user is a member
        response = requests.get(
            f"{self.base_url}/rest/v1/team_members",
            headers=self.headers,
            params={
                'user_id': f'eq.{user_id}',
                'status': 'eq.active',
                'select': 'organization_id,role,organizations(*)'
            }
        )
        
        if response.status_code == 200 and response.json():
            member = response.json()[0]
            org = member.get('organizations')
            if org:
                org['user_role'] = member['role']
                return org
        
        return None
    
    def create_organization(self, user_id: str, name: str, tier: str = 'enterprise') -> Dict:
        """Create a new organization."""
        max_seats = {'starter': 1, 'pro': 3, 'enterprise': 10}.get(tier, 1)
        max_api = {'starter': 0, 'pro': 0, 'enterprise': 500}.get(tier, 0)
        
        payload = {
            'name': name,
            'owner_id': user_id,
            'subscription_tier': tier,
            'max_seats': max_seats,
            'max_api_calls_per_day': max_api
        }
        
        response = requests.post(
            f"{self.base_url}/rest/v1/organizations",
            headers={**self.headers, 'Prefer': 'return=representation'},
            json=payload
        )
        
        if response.status_code in [200, 201]:
            return response.json()[0]
        raise Exception(f"Failed to create organization: {response.text}")
    
    def get_team_members(self, organization_id: str) -> list:
        """Get all team members for an organization."""
        response = requests.get(
            f"{self.base_url}/rest/v1/team_members",
            headers=self.headers,
            params={
                'organization_id': f'eq.{organization_id}',
                'select': 'id,email,role,status,invited_at,accepted_at'
            }
        )
        
        if response.status_code == 200:
            return response.json()
        return []
    
    def invite_member(self, organization_id: str, email: str, role: str, invited_by: str) -> Dict:
        """Invite a new team member."""
        payload = {
            'organization_id': organization_id,
            'email': email.lower(),
            'role': role,
            'status': 'pending',
            'invited_by': invited_by
        }
        
        response = requests.post(
            f"{self.base_url}/rest/v1/team_members",
            headers={**self.headers, 'Prefer': 'return=representation'},
            json=payload
        )
        
        if response.status_code in [200, 201]:
            return response.json()[0]
        raise Exception(f"Failed to invite member: {response.text}")
    
    def remove_member(self, member_id: str, organization_id: str) -> bool:
        """Remove a team member."""
        response = requests.patch(
            f"{self.base_url}/rest/v1/team_members",
            headers=self.headers,
            params={
                'id': f'eq.{member_id}',
                'organization_id': f'eq.{organization_id}'
            },
            json={'status': 'revoked'}
        )
        return response.status_code == 200
    
    def update_member_role(self, member_id: str, organization_id: str, new_role: str) -> bool:
        """Update a team member's role."""
        response = requests.patch(
            f"{self.base_url}/rest/v1/team_members",
            headers=self.headers,
            params={
                'id': f'eq.{member_id}',
                'organization_id': f'eq.{organization_id}'
            },
            json={'role': new_role}
        )
        return response.status_code == 200
    
    def accept_invite(self, user_id: str, email: str) -> bool:
        """Accept a pending invite (called when user logs in)."""
        response = requests.patch(
            f"{self.base_url}/rest/v1/team_members",
            headers=self.headers,
            params={
                'email': f'eq.{email.lower()}',
                'status': 'eq.pending'
            },
            json={
                'user_id': user_id,
                'status': 'active',
                'accepted_at': datetime.now(timezone.utc).isoformat()
            }
        )
        return response.status_code == 200


class BrandingManager:
    """Manages white-label branding for Enterprise organizations."""
    
    def __init__(self):
        self.base_url = SUPABASE_URL
        self.headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            'Content-Type': 'application/json'
        }
    
    def get_branding(self, organization_id: str) -> Optional[Dict]:
        """Get branding settings for an organization."""
        response = requests.get(
            f"{self.base_url}/rest/v1/organization_branding",
            headers=self.headers,
            params={
                'organization_id': f'eq.{organization_id}',
                'select': '*'
            }
        )
        
        if response.status_code == 200 and response.json():
            return response.json()[0]
        return None
    
    def update_branding(self, organization_id: str, branding: Dict) -> Dict:
        """Update or create branding settings."""
        # Check if exists
        existing = self.get_branding(organization_id)
        
        payload = {
            'organization_id': organization_id,
            'logo_url': branding.get('logo_url'),
            'primary_color': branding.get('primary_color', '#7cffb2'),
            'secondary_color': branding.get('secondary_color', '#1a1a2e'),
            'accent_color': branding.get('accent_color', '#b8b8ff'),
            'company_name': branding.get('company_name'),
            'custom_footer_text': branding.get('custom_footer_text'),
            'hide_gap_intel_branding': branding.get('hide_gap_intel_branding', False),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        if existing:
            response = requests.patch(
                f"{self.base_url}/rest/v1/organization_branding",
                headers=self.headers,
                params={'organization_id': f'eq.{organization_id}'},
                json=payload
            )
        else:
            response = requests.post(
                f"{self.base_url}/rest/v1/organization_branding",
                headers={**self.headers, 'Prefer': 'return=representation'},
                json=payload
            )
        
        if response.status_code in [200, 201, 204]:
            return self.get_branding(organization_id) or payload
        raise Exception(f"Failed to update branding: {response.text}")


# Singleton instances
api_key_manager = APIKeyManager()
team_manager = TeamManager()
branding_manager = BrandingManager()
