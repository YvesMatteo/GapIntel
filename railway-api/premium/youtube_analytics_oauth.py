"""
YouTube Analytics OAuth2 Integration
Handles creator authentication to access their channel analytics.

Requires:
- Google Cloud OAuth2 credentials configured
- Scopes: https://www.googleapis.com/auth/yt-analytics.readonly

Environment variables:
- GOOGLE_CLIENT_ID: OAuth2 client ID
- GOOGLE_CLIENT_SECRET: OAuth2 client secret
- ENCRYPTION_KEY: Fernet key for token encryption
"""

import os
import json
import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import requests

# Encryption for token storage
try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️ cryptography not installed. Token encryption disabled.")

# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"

# Required scopes for YouTube Analytics
YOUTUBE_ANALYTICS_SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",  # For channel info
]


@dataclass
class OAuthTokens:
    """OAuth token storage."""
    access_token: str
    refresh_token: str
    expires_at: datetime
    scopes: list
    channel_id: str = ""
    
    def is_expired(self) -> bool:
        """Check if access token is expired (with 5 min buffer)."""
        # Use UTC-aware datetime for comparison
        now = datetime.now(timezone.utc)
        # Make expires_at timezone-aware if it isn't
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return now >= (expires - timedelta(minutes=5))
    
    def to_dict(self) -> Dict:
        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_at': self.expires_at.isoformat(),
            'scopes': self.scopes,
            'channel_id': self.channel_id
        }


class TokenEncryption:
    """Handles encryption/decryption of OAuth tokens."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        self.key = encryption_key or os.getenv('ENCRYPTION_KEY')
        self.fernet = None
        
        if CRYPTO_AVAILABLE and self.key:
            # Ensure key is valid Fernet key (32 bytes, base64 encoded)
            try:
                self.fernet = Fernet(self.key.encode() if isinstance(self.key, str) else self.key)
            except Exception as e:
                print(f"⚠️ Invalid encryption key: {e}")
        else:
            print("⚠️ Encryption disabled (missing module or key). Using Base64 fallback.")
    
    def encrypt(self, data: str) -> str:
        """Encrypt a string."""
        if self.fernet:
            return self.fernet.encrypt(data.encode()).decode()
        # Fallback: base64 encode (NOT secure, for dev only)
        # Add simpler fallback prefix to distinguish
        return "b64:" + base64.b64encode(data.encode()).decode()
    
    def decrypt(self, encrypted: str) -> str:
        """Decrypt a string."""
        if self.fernet:
            try:
                return self.fernet.decrypt(encrypted.encode()).decode()
            except Exception:
                # Try fallback if decryption fails
                pass
                
        # Fallback: base64 decode
        clean_data = encrypted
        if encrypted.startswith("b64:"):
            clean_data = encrypted[4:]
            
        try:
             return base64.b64decode(clean_data.encode()).decode()
        except Exception as e:
            print(f"❌ Decryption failed: {e}")
            return ""


class YouTubeAnalyticsOAuth:
    """
    Manages OAuth2 flow for YouTube Analytics API.
    
    Usage:
        oauth = YouTubeAnalyticsOAuth()
        
        # Step 1: Get authorization URL
        auth_url, state = oauth.get_authorization_url(
            user_id="user123",
            redirect_uri="https://gapintel.online/api/youtube-analytics/callback"
        )
        
        # Step 2: Handle callback after user authorizes
        tokens = oauth.handle_callback(code="...", state="...")
        
        # Step 3: Use access token for API calls
        # Step 4: Refresh when expired
        new_access_token = oauth.refresh_access_token(refresh_token="...")
    """
    
    def __init__(self, 
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None,
                 supabase_url: Optional[str] = None,
                 supabase_key: Optional[str] = None):
        self.client_id = (client_id or os.getenv('GOOGLE_CLIENT_ID', '')).strip().strip('"').strip("'")
        self.client_secret = (client_secret or os.getenv('GOOGLE_CLIENT_SECRET', '')).strip().strip('"').strip("'")
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_SERVICE_KEY')
        
        self.encryptor = TokenEncryption()
        self._state_cache = {}  # In production, use Redis or similar
        
        if not self.client_id or not self.client_secret:
            print("⚠️ Google OAuth credentials not configured")
        else:
            # Debug log (masked)
            cid_masked = f"{self.client_id[:5]}...{self.client_id[-5:]}" if len(self.client_id) > 10 else "SHORT"
            print(f"✅ OAuth Configured with Client ID: {cid_masked}")
    
    def get_authorization_url(self, user_id: str, redirect_uri: str) -> Tuple[str, str]:
        """
        Generate OAuth authorization URL for user.
        
        Args:
            user_id: Unique identifier for the user (for state validation)
            redirect_uri: Where to redirect after authorization
            
        Returns:
            Tuple of (authorization_url, state_token)
        """
        # Create stateless state token containing user_id and redirect_uri
        state_data = json.dumps({
            'user_id': user_id,
            'redirect_uri': redirect_uri,
            'expires': (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
            'nonce': secrets.token_hex(8)  # Randomness
        })
        
        # Encrypt state so it can't be tampered with
        state = self.encryptor.encrypt(state_data)
        
        # Build authorization URL
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(YOUTUBE_ANALYTICS_SCOPES),
            'access_type': 'offline',  # Get refresh token
            'prompt': 'consent',  # Always show consent screen for refresh token
            'state': state,
        }
        
        query_string = '&'.join(f"{k}={requests.utils.quote(str(v))}" for k, v in params.items())
        auth_url = f"{GOOGLE_AUTH_URL}?{query_string}"
        
        return auth_url, state
    
    def validate_state(self, state: str) -> Optional[Dict]:
        """Validate state token and return associated data."""
        try:
            # Decrypt state
            decrypted = self.encryptor.decrypt(state)
            data = json.loads(decrypted)
            
            # Check expiration - ensure timezone-aware comparison
            expires_str = data['expires']
            expires = datetime.fromisoformat(expires_str)
            # Make timezone-aware if not already
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires:
                print("❌ State token expired")
                return None
            
            return data
        except Exception as e:
            print(f"❌ Invalid state token: {e}")
            return None
    
    def handle_callback(self, code: str, state: str) -> Optional[OAuthTokens]:
        """
        Exchange authorization code for tokens.
        
        Args:
            code: Authorization code from Google
            state: State token for validation
            
        Returns:
            OAuthTokens if successful, None if failed
        """
        # Validate state (stateless)
        state_data = self.validate_state(state)
        if not state_data:
            print("❌ Invalid or expired state token")
            return None
        
        # Exchange code for tokens
        token_data = {
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': state_data['redirect_uri'],
            'grant_type': 'authorization_code',
        }
        
        try:
            response = requests.post(GOOGLE_TOKEN_URL, data=token_data)
            response.raise_for_status()
            tokens = response.json()
        except requests.RequestException as e:
            print(f"❌ Token exchange failed: {e}")
            return None
        
        # Calculate expiration (use UTC-aware datetime)
        expires_in = tokens.get('expires_in', 3600)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        
        # Get channel ID
        channel_id = self._get_channel_id(tokens['access_token'])
        
        oauth_tokens = OAuthTokens(
            access_token=tokens['access_token'],
            refresh_token=tokens.get('refresh_token', ''),
            expires_at=expires_at,
            scopes=tokens.get('scope', '').split(' '),
            channel_id=channel_id
        )
        
        # Store tokens in database
        self._store_tokens(state_data['user_id'], oauth_tokens)
        
        return oauth_tokens
    
    def _get_channel_id(self, access_token: str) -> str:
        """Get the authenticated user's channel ID."""
        try:
            response = requests.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params={'part': 'id', 'mine': 'true'},
                headers={'Authorization': f'Bearer {access_token}'}
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('items'):
                return data['items'][0]['id']
        except Exception as e:
            print(f"⚠️ Could not get channel ID: {e}")
        
        return ""
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Refresh an expired access token.
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            New access token if successful, None if failed
        """
        token_data = {
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
        }
        
        try:
            response = requests.post(GOOGLE_TOKEN_URL, data=token_data)
            response.raise_for_status()
            tokens = response.json()
            return tokens.get('access_token')
        except requests.RequestException as e:
            print(f"❌ Token refresh failed: {e}")
            return None
    
    def revoke_access(self, access_token: str) -> bool:
        """
        Revoke OAuth access (disconnect).
        
        Args:
            access_token: The access token to revoke
            
        Returns:
            True if successful
        """
        try:
            response = requests.post(
                GOOGLE_REVOKE_URL,
                params={'token': access_token}
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def _store_tokens(self, user_id: str, tokens: OAuthTokens) -> bool:
        """Store encrypted tokens in Supabase (upsert by user_id)."""
        if not self.supabase_url or not self.supabase_key:
            print("⚠️ Supabase not configured, tokens not persisted")
            return False
        
        headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
        }
        
        data = {
            'user_id': user_id,
            'channel_id': tokens.channel_id,
            'access_token_encrypted': self.encryptor.encrypt(tokens.access_token),
            'refresh_token_encrypted': self.encryptor.encrypt(tokens.refresh_token),
            'expires_at': tokens.expires_at.isoformat(),
            'scopes': tokens.scopes,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # First, delete all existing tokens for this user (to avoid duplicates)
            delete_response = requests.delete(
                f"{self.supabase_url}/rest/v1/youtube_analytics_tokens?user_id=eq.{user_id}",
                headers=headers
            )
            print(f"🗑️ Cleaned up old tokens for user {user_id[:8]}...: {delete_response.status_code}")
            
            # Then insert the new token
            response = requests.post(
                f"{self.supabase_url}/rest/v1/youtube_analytics_tokens",
                headers=headers,
                json=data
            )
            print(f"✅ Stored token for user {user_id[:8]}...: {response.status_code}")
            return response.status_code in [200, 201]
        except requests.RequestException as e:
            print(f"❌ Failed to store tokens: {e}")
            return False
    
    def get_tokens(self, user_id: str) -> Optional[OAuthTokens]:
        """
        Retrieve tokens for a user from Supabase.
        
        Automatically refreshes if expired.
        """
        if not self.supabase_url or not self.supabase_key:
            print("❌ Supabase not configured")
            return None
        
        headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
        }
        
        try:
            # Get the most recent token for this user
            response = requests.get(
                f"{self.supabase_url}/rest/v1/youtube_analytics_tokens",
                headers=headers,
                params={
                    'user_id': f'eq.{user_id}', 
                    'select': '*',
                    'order': 'updated_at.desc',
                    'limit': '1'
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if not data:
                print(f"ℹ️ No tokens found for user {user_id[:8]}...")
                return None
            
            row = data[0]
            print(f"✅ Found token for user {user_id[:8]}..., channel: {row.get('channel_id', 'unknown')}")
            
            # Decrypt tokens
            access_token = self.encryptor.decrypt(row['access_token_encrypted'])
            refresh_token = self.encryptor.decrypt(row['refresh_token_encrypted'])
            
            if not access_token or not refresh_token:
                print(f"❌ Failed to decrypt tokens for user {user_id[:8]}...")
                return None
            
            tokens = OAuthTokens(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=datetime.fromisoformat(row['expires_at'].replace('Z', '+00:00')),
                scopes=row['scopes'],
                channel_id=row['channel_id']
            )
            
            # Refresh if expired
            if tokens.is_expired():
                print(f"🔄 Token expired for user {user_id[:8]}..., refreshing...")
                new_access_token = self.refresh_access_token(tokens.refresh_token)
                if new_access_token:
                    tokens.access_token = new_access_token
                    tokens.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
                    self._store_tokens(user_id, tokens)
                    print(f"✅ Token refreshed successfully for user {user_id[:8]}...")
                else:
                    print(f"❌ Token refresh failed for user {user_id[:8]}..., connection lost")
                    return None  # Refresh failed
            
            return tokens
            
        except Exception as e:
            print(f"❌ Failed to retrieve tokens: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def disconnect(self, user_id: str) -> bool:
        """
        Disconnect YouTube Analytics access.
        
        Revokes token and deletes from database.
        """
        tokens = self.get_tokens(user_id)
        if tokens:
            self.revoke_access(tokens.access_token)
        
        # Delete from database
        if self.supabase_url and self.supabase_key:
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
            }
            try:
                requests.delete(
                    f"{self.supabase_url}/rest/v1/youtube_analytics_tokens",
                    headers=headers,
                    params={'user_id': f'eq.{user_id}'}
                )
            except:
                pass
        
        return True


# === Quick test ===
if __name__ == "__main__":
    print("🧪 Testing YouTube Analytics OAuth...")
    
    oauth = YouTubeAnalyticsOAuth()
    
    # Test authorization URL generation
    auth_url, state = oauth.get_authorization_url(
        user_id="test_user_123",
        redirect_uri="http://localhost:3000/api/youtube-analytics/callback"
    )
    
    print(f"\n📎 Authorization URL:")
    print(f"   {auth_url[:80]}...")
    print(f"\n🔑 State token: {state}")
    
    # Test state validation
    state_data = oauth.validate_state(state)
    print(f"\n✅ State validated: {state_data is not None}")
    
    print("\n🔐 Token encryption test:")
    test_token = "ya29.test_access_token_12345"
    encrypted = oauth.encryptor.encrypt(test_token)
    decrypted = oauth.encryptor.decrypt(encrypted)
    print(f"   Original: {test_token}")
    print(f"   Encrypted: {encrypted[:40]}...")
    print(f"   Decrypted matches: {test_token == decrypted}")
