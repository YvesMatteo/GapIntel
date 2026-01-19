"""
CTR Training Data Collector
Collects and prepares data for ML model training.

Data sources:
- YouTube Analytics API (actual CTR from connected creators)
- Existing thumbnail_extractor.py for visual features
- Video metadata from YouTube Data API

Usage:
    collector = CTRDataCollector()
    
    # Collect from a connected creator's channel
    result = collector.collect_from_channel(channel_id="UCxxx", user_id="user123")
    
    # Prepare training dataset
    df = collector.prepare_training_dataset(min_impressions=1000)
    
    # Get dataset statistics
    stats = collector.get_dataset_stats()
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np
import requests

# Local imports
# Local imports
try:
    # Try absolute import (works when run from root)
    from premium.youtube_analytics_oauth import YouTubeAnalyticsOAuth
    from premium.youtube_analytics_fetcher import YouTubeAnalyticsFetcher
    from premium.thumbnail_extractor import ThumbnailFeatureExtractor
except ImportError:
    # Try parent relative import (works when package)
    try:
        from ..youtube_analytics_oauth import YouTubeAnalyticsOAuth
        from ..youtube_analytics_fetcher import YouTubeAnalyticsFetcher
        from ..thumbnail_extractor import ThumbnailFeatureExtractor
    except ImportError:
        # Fallback (legacy/local run)
        from youtube_analytics_oauth import YouTubeAnalyticsOAuth
        from youtube_analytics_fetcher import YouTubeAnalyticsFetcher
        ThumbnailFeatureExtractor = None


@dataclass
class CollectionResult:
    """Result of a data collection run."""
    channel_id: str
    videos_processed: int
    videos_collected: int
    errors: List[str]
    duration_seconds: float
    status: str  # 'success', 'partial', 'failed'
    
    def to_dict(self) -> Dict:
        return asdict(self)


class CTRDataCollector:
    """
    Collects CTR data from connected creators for ML model training.
    
    The collection process:
    1. Get OAuth tokens for the user
    2. Fetch video list from their channel
    3. Get CTR data from YouTube Analytics API
    4. Extract thumbnail features
    5. Store combined data for training
    """
    
    # Power words for title feature extraction
    POWER_WORDS = [
        'secret', 'revealed', 'shocking', 'insane', 'ultimate',
        'best', 'worst', 'top', 'how to', 'why', 'tutorial',
        'tips', 'tricks', 'guide', 'review', 'vs', 'unboxing',
        'reaction', 'challenge', 'truth', 'exposed', 'finally',
        'new', 'update', 'breaking', 'exclusive', 'free'
    ]
    
    def __init__(self, 
                 supabase_url: Optional[str] = None,
                 supabase_key: Optional[str] = None,
                 youtube_api_key: Optional[str] = None):
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.youtube_api_key = youtube_api_key or os.getenv('YOUTUBE_API_KEY')
        
        self.oauth = YouTubeAnalyticsOAuth(
            supabase_url=self.supabase_url,
            supabase_key=self.supabase_key
        )
        
        # Initialize thumbnail extractor if available
        self.thumbnail_extractor = None
        if ThumbnailFeatureExtractor:
            try:
                self.thumbnail_extractor = ThumbnailFeatureExtractor()
            except Exception as e:
                print(f"⚠️ Thumbnail extractor not available: {e}")
    
    def collect_from_channel(self, 
                             channel_id: str, 
                             user_id: str,
                             max_videos: int = 100) -> CollectionResult:
        """
        Collect CTR data for all videos from a connected channel.
        
        Args:
            channel_id: YouTube channel ID
            user_id: User ID (for OAuth token lookup)
            max_videos: Maximum videos to process
            
        Returns:
            CollectionResult with collection statistics
        """
        import time
        start_time = time.time()
        errors = []
        videos_processed = 0
        videos_collected = 0
        
        # Get OAuth tokens
        tokens = self.oauth.get_tokens(user_id)
        if not tokens:
            return CollectionResult(
                channel_id=channel_id,
                videos_processed=0,
                videos_collected=0,
                errors=["No valid OAuth tokens found for user"],
                duration_seconds=time.time() - start_time,
                status='failed'
            )
        
        # Initialize fetcher with access token
        fetcher = YouTubeAnalyticsFetcher(tokens.access_token)
        
        # Fetch CTR data from YouTube Analytics
        print(f"📊 Fetching CTR data for channel {channel_id}...")
        ctr_df = fetcher.fetch_all_video_ctr(
            channel_id=channel_id,
            days=90,
            min_impressions=100
        )
        
        if ctr_df.empty:
            msg = "No video data found. Please ensure you have public videos and Analytics permissions."
            print(f"❌ {msg}")
            return CollectionResult(
                channel_id=channel_id,
                videos_processed=0,
                videos_collected=0,
                errors=[msg],
                duration_seconds=time.time() - start_time,
                status='failed'
            )
        
        print(f"   Found {len(ctr_df)} videos with CTR data")
        
        # Get video metadata and thumbnail features
        for _, row in ctr_df.head(max_videos).iterrows():
            videos_processed += 1
            video_id = row['video_id']
            
            try:
                # Get video details from YouTube Data API
                video_info = self._get_video_details(video_id)
                
                if not video_info:
                    errors.append(f"Could not get details for {video_id}")
                    continue
                
                # Extract thumbnail features
                thumbnail_features = {}
                if self.thumbnail_extractor and video_info.get('thumbnail_url'):
                    try:
                        features = self.thumbnail_extractor.extract_from_url(
                            video_info['thumbnail_url']
                        )
                        thumbnail_features = features.to_dict() if hasattr(features, 'to_dict') else {}
                    except Exception as e:
                        errors.append(f"Thumbnail extraction failed for {video_id}: {str(e)}")
                
                # Extract title features
                title = video_info.get('title', '')
                title_features = self._extract_title_features(title)
                
                # Store training data
                training_record = {
                    'video_id': video_id,
                    'channel_id': channel_id,
                    'impressions': int(row['impressions']),
                    'clicks': int(row['clicks']),
                    'ctr_actual': float(row['ctr_actual']),
                    'thumbnail_features': json.dumps(thumbnail_features),
                    'thumbnail_url': video_info.get('thumbnail_url'),
                    'title': title,
                    **title_features,
                    'published_at': video_info.get('published_at'),
                    'duration_seconds': video_info.get('duration_seconds', 0),
                    'category_id': video_info.get('category_id', ''),
                    'data_source': 'youtube_analytics'
                }
                
                if self._store_training_record(training_record):
                    videos_collected += 1
                else:
                    errors.append(f"Failed to store data for {video_id}")
                    
            except Exception as e:
                errors.append(f"Error processing {video_id}: {str(e)}")
        
        # Log collection run
        self._log_collection(channel_id, user_id, videos_processed, videos_collected, errors)
        
        duration = time.time() - start_time
        status = 'success' if videos_collected > 0 else 'failed'
        if errors and videos_collected > 0:
            status = 'partial'
        
        return CollectionResult(
            channel_id=channel_id,
            videos_processed=videos_processed,
            videos_collected=videos_collected,
            errors=errors[:10],  # Limit error list
            duration_seconds=round(duration, 2),
            status=status
        )
    
    def _get_video_details(self, video_id: str) -> Optional[Dict]:
        """Get video details from YouTube Data API."""
        if not self.youtube_api_key:
            return None
        
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            'part': 'snippet,contentDetails,statistics',
            'id': video_id,
            'key': self.youtube_api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('items'):
                return None
            
            item = data['items'][0]
            snippet = item.get('snippet', {})
            stats = item.get('statistics', {})
            
            # Get best thumbnail
            thumbnails = snippet.get('thumbnails', {})
            thumbnail_url = (
                thumbnails.get('maxres', {}).get('url') or
                thumbnails.get('high', {}).get('url') or
                thumbnails.get('default', {}).get('url') or
                f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            )
            
            # Parse duration
            duration = item.get('contentDetails', {}).get('duration', 'PT0S')
            duration_seconds = self._parse_duration(duration)
            
            return {
                'video_id': video_id,
                'title': snippet.get('title', ''),
                'description': snippet.get('description', '')[:500],
                'thumbnail_url': thumbnail_url,
                'published_at': snippet.get('publishedAt'),
                'category_id': snippet.get('categoryId', ''),
                'duration_seconds': duration_seconds,
                'view_count': int(stats.get('viewCount', 0)),
                'like_count': int(stats.get('likeCount', 0)),
                'comment_count': int(stats.get('commentCount', 0)),
            }
            
        except Exception as e:
            print(f"⚠️ Failed to get video details: {e}")
            return None
    
    def _parse_duration(self, duration: str) -> int:
        """Parse ISO 8601 duration to seconds."""
        import re
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if not match:
            return 0
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds
    
    def _extract_title_features(self, title: str) -> Dict:
        """Extract features from video title."""
        title_lower = title.lower()
        
        return {
            'title_length': len(title),
            'title_has_numbers': any(c.isdigit() for c in title),
            'title_has_question': '?' in title,
            'title_has_power_words': any(pw in title_lower for pw in self.POWER_WORDS),
            'title_capitalization_ratio': round(
                sum(1 for c in title if c.isupper()) / max(len(title), 1), 
                2
            )
        }
    
    def _store_training_record(self, record: Dict) -> bool:
        """Store training record in Supabase."""
        if not self.supabase_url or not self.supabase_key:
            print("⚠️ Supabase not configured")
            return False
        
        headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'resolution=merge-duplicates'
        }
        
        try:
            response = requests.post(
                f"{self.supabase_url}/rest/v1/ctr_training_data",
                headers=headers,
                json=record,
                timeout=10
            )
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"❌ Failed to store record: {e}")
            return False
    
    def _log_collection(self, channel_id: str, user_id: str, 
                        processed: int, collected: int, errors: List[str]):
        """Log collection run to database."""
        if not self.supabase_url or not self.supabase_key:
            return
        
        headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
        }
        
        log_data = {
            'channel_id': channel_id,
            'user_id': user_id,
            'videos_processed': processed,
            'videos_collected': collected,
            'errors': errors[:20],  # Limit stored errors
            'completed_at': datetime.now().isoformat(),
            'status': 'completed' if collected > 0 else 'failed'
        }
        
        try:
            requests.post(
                f"{self.supabase_url}/rest/v1/ctr_collection_log",
                headers=headers,
                json=log_data,
                timeout=5
            )
        except:
            pass
    
    def prepare_training_dataset(self, 
                                  min_impressions: int = 1000,
                                  max_samples: int = 10000) -> pd.DataFrame:
        """
        Prepare training dataset from collected data.
        
        Args:
            min_impressions: Minimum impressions for statistical significance
            max_samples: Maximum samples to include
            
        Returns:
            DataFrame with features and target (ctr_actual)
        """
        if not self.supabase_url or not self.supabase_key:
            print("⚠️ Supabase not configured")
            return pd.DataFrame()
        
        headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
        }
        
        try:
            # Fetch training data
            response = requests.get(
                f"{self.supabase_url}/rest/v1/ctr_training_data",
                headers=headers,
                params={
                    'impressions': f'gte.{min_impressions}',
                    'select': '*',
                    'order': 'fetch_date.desc',
                    'limit': max_samples
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if not data:
                print("⚠️ No training data found")
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            
            # Parse thumbnail features from JSONB
            if 'thumbnail_features' in df.columns:
                thumbnail_df = pd.json_normalize(
                    df['thumbnail_features'].apply(
                        lambda x: json.loads(x) if isinstance(x, str) else (x or {})
                    )
                )
                
                # Prefix thumbnail columns
                thumbnail_df.columns = [f'thumb_{c}' for c in thumbnail_df.columns]
                
                # Merge back
                df = pd.concat([df, thumbnail_df], axis=1)
                df = df.drop(columns=['thumbnail_features'])
            
            print(f"📊 Prepared {len(df)} samples for training")
            print(f"   Unique channels: {df['channel_id'].nunique()}")
            print(f"   CTR range: {df['ctr_actual'].min():.1f}% - {df['ctr_actual'].max():.1f}%")
            
            return df
            
        except Exception as e:
            print(f"❌ Failed to prepare dataset: {e}")
            return pd.DataFrame()
    
    def get_dataset_stats(self) -> Dict:
        """Get statistics about current training dataset."""
        if not self.supabase_url or not self.supabase_key:
            return {'error': 'Supabase not configured'}
        
        headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
        }
        
        try:
            # Call the stats function
            response = requests.post(
                f"{self.supabase_url}/rest/v1/rpc/get_training_data_stats",
                headers={**headers, 'Content-Type': 'application/json'},
                json={},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    return data[0] if isinstance(data, list) else data
            
            # Fallback: calculate stats manually
            response = requests.get(
                f"{self.supabase_url}/rest/v1/ctr_training_data",
                headers=headers,
                params={
                    'select': 'video_id,channel_id,ctr_actual,impressions,fetch_date',
                    'impressions': 'gte.1000'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    df = pd.DataFrame(data)
                    return {
                        'total_samples': len(df),
                        'unique_channels': df['channel_id'].nunique(),
                        'unique_videos': df['video_id'].nunique(),
                        'avg_ctr': round(df['ctr_actual'].mean(), 2),
                        'min_ctr': round(df['ctr_actual'].min(), 2),
                        'max_ctr': round(df['ctr_actual'].max(), 2),
                        'last_collection': df['fetch_date'].max() if 'fetch_date' in df else None,
                        'can_train': len(df) >= 1000
                    }
            
            return {'total_samples': 0, 'can_train': False}
            
        except Exception as e:
            return {'error': str(e), 'can_train': False}


# === Quick test ===
if __name__ == "__main__":
    print("🧪 Testing CTR Data Collector...")
    
    collector = CTRDataCollector()
    
    # Test title feature extraction
    test_title = "7 SECRETS to Grow Your YouTube Channel FAST in 2026"
    features = collector._extract_title_features(test_title)
    
    print(f"\n📝 Title Features Test:")
    print(f"   Title: {test_title}")
    print(f"   Length: {features['title_length']}")
    print(f"   Has numbers: {features['title_has_numbers']}")
    print(f"   Has question: {features['title_has_question']}")
    print(f"   Has power words: {features['title_has_power_words']}")
    print(f"   Cap ratio: {features['title_capitalization_ratio']}")
    
    # Test dataset stats
    print(f"\n📊 Dataset Stats:")
    stats = collector.get_dataset_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
