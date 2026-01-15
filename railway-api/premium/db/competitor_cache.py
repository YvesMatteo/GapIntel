"""
Competitor Data Cache - Supabase-backed with 24h TTL

Caches basic competitor stats to avoid redundant API calls.
Only caches non-volatile data (channel basics, averages).
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict
import requests


class CompetitorCache:
    """
    Supabase-backed cache for competitor channel data.
    
    Cache Strategy:
    - 24h TTL for basic stats (subscriber count, avg views, formats)
    - Does NOT cache detailed analysis (fresh each time for accuracy)
    """
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        self.table_name = 'competitor_cache'
        self.ttl_hours = 24
        
        if not self.supabase_url or not self.supabase_key:
            print("⚠️ Supabase credentials not configured - cache disabled")
            self.enabled = False
        else:
            self.enabled = True
    
    def _get_headers(self) -> Dict:
        return {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
    
    def get(self, channel_id: str) -> Optional[Dict]:
        """
        Get cached competitor data if fresh (within TTL).
        Returns None if not cached or expired.
        """
        if not self.enabled:
            return None
        
        try:
            url = f"{self.supabase_url}/rest/v1/{self.table_name}"
            params = {
                'channel_id': f'eq.{channel_id}',
                'select': '*'
            }
            
            response = requests.get(url, headers=self._get_headers(), params=params)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            if not data:
                return None
            
            cache_entry = data[0]
            cached_at = datetime.fromisoformat(cache_entry['cached_at'].replace('Z', '+00:00'))
            
            # Check TTL
            if datetime.now(cached_at.tzinfo) - cached_at > timedelta(hours=self.ttl_hours):
                # Expired - delete and return None
                self._delete(channel_id)
                return None
            
            return json.loads(cache_entry['data'])
            
        except Exception as e:
            print(f"⚠️ Cache read error: {e}")
            return None
    
    def set(self, channel_id: str, data: Dict) -> bool:
        """
        Cache competitor basic stats.
        
        Only caches "safe" data that doesn't change rapidly:
        - channel_name
        - subscriber_count (rounded to nearest 1000)
        - avg_views (rounded)
        - avg_engagement
        - upload_frequency_days
        - top_formats
        - posting_days
        """
        if not self.enabled:
            return False
        
        # Filter to cacheable data only
        cacheable_data = {
            'channel_name': data.get('channel_name', ''),
            'subscriber_count': round(data.get('subscriber_count', 0), -3),  # Round to 1000s
            'avg_views': round(data.get('avg_views', 0), -2),  # Round to 100s
            'avg_engagement': round(data.get('avg_engagement', 0), 2),
            'upload_frequency_days': round(data.get('upload_frequency_days', 0), 1),
            'top_formats': data.get('top_formats', [])[:3],
            'posting_days': data.get('posting_days', [])[:3],
        }
        
        try:
            # Upsert (insert or update)
            url = f"{self.supabase_url}/rest/v1/{self.table_name}"
            
            payload = {
                'channel_id': channel_id,
                'data': json.dumps(cacheable_data),
                'cached_at': datetime.utcnow().isoformat() + 'Z'
            }
            
            # Try to update first
            update_url = f"{url}?channel_id=eq.{channel_id}"
            response = requests.patch(update_url, headers=self._get_headers(), json=payload)
            
            if response.status_code == 200 and response.json():
                return True
            
            # If not updated (didn't exist), insert
            response = requests.post(url, headers=self._get_headers(), json=payload)
            return response.status_code in [200, 201]
            
        except Exception as e:
            print(f"⚠️ Cache write error: {e}")
            return False
    
    def _delete(self, channel_id: str) -> bool:
        """Delete expired cache entry."""
        if not self.enabled:
            return False
        
        try:
            url = f"{self.supabase_url}/rest/v1/{self.table_name}?channel_id=eq.{channel_id}"
            response = requests.delete(url, headers=self._get_headers())
            return response.status_code in [200, 204]
        except:
            return False


# Singleton instance for global use
_cache_instance = None

def get_competitor_cache() -> CompetitorCache:
    """Get the singleton cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CompetitorCache()
    return _cache_instance


# === Quick test ===
if __name__ == "__main__":
    print("🧪 Competitor Cache module loaded")
    cache = get_competitor_cache()
    print(f"   Cache enabled: {cache.enabled}")
