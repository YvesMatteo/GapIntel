"""
Views Training Data Collector
Collects early video metrics (1h, 6h, 24h) and final counts (7d, 30d)
for ML model training. Requires creator opt-in.

Usage:
    collector = ViewsDataCollector()
    if collector.check_opt_in(user_id):
        collector.start_collection(video_id, channel_id, user_id)
"""

import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

# Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# YouTube API
try:
    from googleapiclient.discovery import build
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False


@dataclass
class CollectionStatus:
    """Status of a video's data collection."""
    video_id: str
    status: str  # pending, collecting_1h, collecting_6h, collecting_24h, collecting_7d, collecting_30d, complete
    next_collection_at: Optional[datetime]
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        if result['next_collection_at']:
            result['next_collection_at'] = result['next_collection_at'].isoformat()
        return result


class ViewsDataCollector:
    """
    Collects early video metrics for ML training.
    
    Collection Schedule:
    1. Start collection when video published (record metadata)
    2. Collect views_1h at 1 hour mark
    3. Collect views_6h at 6 hour mark
    4. Collect views_24h at 24 hour mark
    5. Collect final_views_7d at 7 day mark
    6. Collect final_views_30d at 30 day mark (complete)
    """
    
    def __init__(self, 
                 supabase_url: Optional[str] = None,
                 supabase_key: Optional[str] = None,
                 youtube_api_key: Optional[str] = None):
        self.supabase: Optional[Client] = None
        self.youtube = None
        
        # Initialize Supabase
        if SUPABASE_AVAILABLE:
            url = supabase_url or os.getenv("SUPABASE_URL")
            key = supabase_key or os.getenv("SUPABASE_SERVICE_KEY")
            if url and key:
                self.supabase = create_client(url, key)
        
        # Initialize YouTube API
        if YOUTUBE_API_AVAILABLE:
            api_key = youtube_api_key or os.getenv("YOUTUBE_API_KEY")
            if api_key:
                self.youtube = build('youtube', 'v3', developerKey=api_key)
    
    def check_opt_in(self, user_id: str) -> bool:
        """Check if user has opted in to data collection."""
        if not self.supabase:
            return False
            
        try:
            result = self.supabase.table("creator_data_settings")\
                .select("data_collection_opt_in")\
                .eq("user_id", user_id)\
                .single()\
                .execute()
            
            if result.data:
                return result.data.get("data_collection_opt_in", False)
            return False
        except Exception as e:
            print(f"⚠️ Opt-in check failed: {e}")
            return False
    
    def set_opt_in(self, user_id: str, channel_id: str, opt_in: bool) -> bool:
        """Set user's data collection preference."""
        if not self.supabase:
            return False
            
        try:
            data = {
                "user_id": user_id,
                "channel_id": channel_id,
                "data_collection_opt_in": opt_in,
                "consent_timestamp": datetime.utcnow().isoformat() if opt_in else None,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            self.supabase.table("creator_data_settings").upsert(data).execute()
            return True
        except Exception as e:
            print(f"⚠️ Opt-in update failed: {e}")
            return False
    
    def start_collection(self, video_id: str, channel_id: str, user_id: str,
                         video_published_at: datetime = None) -> bool:
        """
        Start data collection for a newly published video.
        Creates a record and schedules metric collection.
        """
        if not self.supabase:
            return False
            
        # Verify opt-in
        if not self.check_opt_in(user_id):
            print(f"⚠️ User {user_id} has not opted in to data collection")
            return False
        
        try:
            # Get video metadata
            video_info = self._get_video_info(video_id)
            if not video_info:
                return False
            
            published_at = video_published_at or datetime.utcnow()
            
            data = {
                "video_id": video_id,
                "channel_id": channel_id,
                "user_id": user_id,
                "video_published_at": published_at.isoformat(),
                "title_length": len(video_info.get('title', '')),
                "has_number_in_title": any(c.isdigit() for c in video_info.get('title', '')),
                "upload_hour": published_at.hour,
                "upload_day_of_week": published_at.weekday(),
                "subscriber_count_at_upload": video_info.get('subscriber_count', 0),
                "collection_status": "collecting_1h"
            }
            
            self.supabase.table("views_training_data").upsert(data).execute()
            return True
            
        except Exception as e:
            print(f"⚠️ Failed to start collection: {e}")
            return False
    
    def collect_metrics_at_interval(self, video_id: str, interval: str) -> bool:
        """
        Collect metrics at a specific interval (1h, 6h, 24h, 7d, 30d).
        Called by a scheduled job.
        """
        if not self.supabase or not self.youtube:
            return False
        
        try:
            # Fetch current video stats
            stats = self._get_video_stats(video_id)
            if not stats:
                return False
            
            views = stats.get('views', 0)
            likes = stats.get('likes', 0)
            comments = stats.get('comments', 0)
            
            # Map interval to column names and next status
            interval_map = {
                '1h': ('views_1h', 'metrics_1h_collected_at', 'collecting_6h'),
                '6h': ('views_6h', 'metrics_6h_collected_at', 'collecting_24h'),
                '24h': ('views_24h', 'metrics_24h_collected_at', 'collecting_7d'),
                '7d': ('final_views_7d', 'metrics_7d_collected_at', 'collecting_30d'),
                '30d': ('final_views_30d', 'metrics_30d_collected_at', 'complete'),
            }
            
            if interval not in interval_map:
                return False
                
            views_col, timestamp_col, next_status = interval_map[interval]
            
            update_data = {
                views_col: views,
                timestamp_col: datetime.utcnow().isoformat(),
                "collection_status": next_status
            }
            
            # Include likes/comments for 24h interval
            if interval == '24h':
                update_data['likes_24h'] = likes
                update_data['comments_24h'] = comments
            
            self.supabase.table("views_training_data")\
                .update(update_data)\
                .eq("video_id", video_id)\
                .execute()
            
            return True
            
        except Exception as e:
            print(f"⚠️ Metrics collection failed for {video_id} at {interval}: {e}")
            return False
    
    def get_videos_pending_collection(self, interval: str, limit: int = 100) -> List[Dict]:
        """
        Get videos that are due for collection at a specific interval.
        Used by scheduled job to process batches.
        """
        if not self.supabase:
            return []
        
        status_map = {
            '1h': 'collecting_1h',
            '6h': 'collecting_6h',
            '24h': 'collecting_24h',
            '7d': 'collecting_7d',
            '30d': 'collecting_30d',
        }
        
        status = status_map.get(interval)
        if not status:
            return []
        
        try:
            result = self.supabase.table("views_training_data")\
                .select("video_id, channel_id, video_published_at")\
                .eq("collection_status", status)\
                .limit(limit)\
                .execute()
            
            return result.data or []
        except Exception as e:
            print(f"⚠️ Failed to get pending videos: {e}")
            return []
    
    def prepare_training_dataset(self, min_final_views: int = 1000) -> List[Dict]:
        """
        Prepare complete training data for model training.
        Returns only records with complete data (all metrics collected).
        """
        if not self.supabase:
            return []
        
        try:
            result = self.supabase.table("views_training_data")\
                .select("*")\
                .eq("collection_status", "complete")\
                .gte("final_views_7d", min_final_views)\
                .execute()
            
            return result.data or []
        except Exception as e:
            print(f"⚠️ Failed to prepare dataset: {e}")
            return []
    
    def _get_video_info(self, video_id: str) -> Optional[Dict]:
        """Get video metadata from YouTube API."""
        if not self.youtube:
            return None
            
        try:
            response = self.youtube.videos().list(
                part='snippet,statistics',
                id=video_id
            ).execute()
            
            if not response.get('items'):
                return None
                
            item = response['items'][0]
            snippet = item.get('snippet', {})
            stats = item.get('statistics', {})
            
            # Get channel subscriber count
            channel_id = snippet.get('channelId')
            sub_count = 0
            if channel_id:
                ch_response = self.youtube.channels().list(
                    part='statistics',
                    id=channel_id
                ).execute()
                if ch_response.get('items'):
                    sub_count = int(ch_response['items'][0].get('statistics', {}).get('subscriberCount', 0))
            
            return {
                'title': snippet.get('title', ''),
                'channel_id': channel_id,
                'subscriber_count': sub_count
            }
        except Exception as e:
            print(f"⚠️ YouTube API error: {e}")
            return None
    
    def _get_video_stats(self, video_id: str) -> Optional[Dict]:
        """Get current video statistics."""
        if not self.youtube:
            return None
            
        try:
            response = self.youtube.videos().list(
                part='statistics',
                id=video_id
            ).execute()
            
            if not response.get('items'):
                return None
                
            stats = response['items'][0].get('statistics', {})
            return {
                'views': int(stats.get('viewCount', 0)),
                'likes': int(stats.get('likeCount', 0)),
                'comments': int(stats.get('commentCount', 0))
            }
        except Exception as e:
            print(f"⚠️ YouTube API error: {e}")
            return None


# === Quick test ===
if __name__ == "__main__":
    print("🧪 Testing Views Data Collector...")
    
    collector = ViewsDataCollector()
    
    # Test opt-in check (will fail without DB connection)
    print(f"\n📊 Opt-in check: {collector.check_opt_in('test-user')}")
    
    print("\n✓ ViewsDataCollector initialized successfully")
