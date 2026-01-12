"""
Premium Analysis - Data Collector
Collects comprehensive performance data from YouTube channels for ML training.

Collects:
- Historical video performance (views, likes, comments)
- Thumbnails for feature extraction
- Channel metrics and growth data
- Competitor channel data
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import requests

# YouTube API
from googleapiclient.discovery import build


@dataclass
class VideoPerformance:
    """Performance metrics for a single video."""
    video_id: str
    channel_id: str
    title: str
    description: str
    published_at: str
    thumbnail_url: str
    
    # Core metrics
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    
    # Computed metrics
    engagement_rate: float = 0.0
    ctr_proxy: float = 0.0  # views / (subscriber_count * 0.1)
    
    # Metadata
    duration_seconds: int = 0
    tags: List[str] = None
    category_id: str = ""
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ChannelStats:
    """Channel-level statistics."""
    channel_id: str
    channel_name: str
    subscriber_count: int = 0
    total_views: int = 0
    video_count: int = 0
    avg_views_per_video: float = 0.0
    upload_frequency_days: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)


class YouTubeDataCollector:
    """
    Collects comprehensive YouTube data for ML training.
    
    Usage:
        collector = YouTubeDataCollector(api_key="YOUR_KEY")
        channel_data = collector.collect_channel_data("@ChannelName", video_limit=50)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY not provided")
        
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
    
    def get_channel_id(self, handle_or_id: str) -> Tuple[str, str]:
        """
        Resolve channel handle to ID.
        Returns (channel_id, channel_name).
        """
        handle = handle_or_id.replace('@', '')
        
        # Try as handle first
        try:
            response = self.youtube.channels().list(
                part='snippet',
                forHandle=handle
            ).execute()
            
            if response.get('items'):
                item = response['items'][0]
                return item['id'], item['snippet']['title']
        except:
            pass
        
        # Try as username
        try:
            response = self.youtube.channels().list(
                part='snippet',
                forUsername=handle
            ).execute()
            
            if response.get('items'):
                item = response['items'][0]
                return item['id'], item['snippet']['title']
        except:
            pass
        
        # Try as channel ID directly
        try:
            response = self.youtube.channels().list(
                part='snippet',
                id=handle_or_id
            ).execute()
            
            if response.get('items'):
                item = response['items'][0]
                return item['id'], item['snippet']['title']
        except:
            pass
        
        raise ValueError(f"Could not find channel: {handle_or_id}")
    
    def get_channel_stats(self, channel_id: str) -> ChannelStats:
        """Get channel-level statistics."""
        response = self.youtube.channels().list(
            part='snippet,statistics,contentDetails',
            id=channel_id
        ).execute()
        
        if not response.get('items'):
            raise ValueError(f"Channel not found: {channel_id}")
        
        item = response['items'][0]
        stats = item['statistics']
        snippet = item['snippet']
        
        return ChannelStats(
            channel_id=channel_id,
            channel_name=snippet['title'],
            subscriber_count=int(stats.get('subscriberCount', 0)),
            total_views=int(stats.get('viewCount', 0)),
            video_count=int(stats.get('videoCount', 0))
        )
    
    def get_uploads_playlist_id(self, channel_id: str) -> str:
        """Get the uploads playlist ID for a channel."""
        response = self.youtube.channels().list(
            part='contentDetails',
            id=channel_id
        ).execute()
        
        if not response.get('items'):
            raise ValueError(f"Channel not found: {channel_id}")
        
        return response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    
    def collect_videos(self, channel_id: str, limit: int = 50) -> List[VideoPerformance]:
        """
        Collect video data from a channel's uploads.
        
        Args:
            channel_id: YouTube channel ID
            limit: Maximum number of videos to collect
            
        Returns:
            List of VideoPerformance objects
        """
        videos = []
        
        # Get uploads playlist
        uploads_playlist = self.get_uploads_playlist_id(channel_id)
        
        # Get channel stats for CTR proxy calculation
        channel_stats = self.get_channel_stats(channel_id)
        subscriber_count = max(channel_stats.subscriber_count, 1)
        
        # Paginate through videos
        next_page_token = None
        collected = 0
        
        while collected < limit:
            batch_size = min(50, limit - collected)
            
            response = self.youtube.playlistItems().list(
                part='snippet,contentDetails',
                playlistId=uploads_playlist,
                maxResults=batch_size,
                pageToken=next_page_token
            ).execute()
            
            video_ids = [item['contentDetails']['videoId'] for item in response.get('items', [])]
            
            if not video_ids:
                break
            
            # Get detailed stats for these videos
            stats_response = self.youtube.videos().list(
                part='statistics,contentDetails,snippet',
                id=','.join(video_ids)
            ).execute()
            
            for item in stats_response.get('items', []):
                video_id = item['id']
                snippet = item['snippet']
                stats = item.get('statistics', {})
                content = item.get('contentDetails', {})
                
                # Parse duration
                duration = content.get('duration', 'PT0S')
                duration_seconds = self._parse_duration(duration)
                
                # Get best thumbnail
                thumbnails = snippet.get('thumbnails', {})
                thumbnail_url = (
                    thumbnails.get('maxres', {}).get('url') or
                    thumbnails.get('high', {}).get('url') or
                    thumbnails.get('medium', {}).get('url') or
                    thumbnails.get('default', {}).get('url', '')
                )
                
                # Calculate metrics
                view_count = int(stats.get('viewCount', 0))
                like_count = int(stats.get('likeCount', 0))
                comment_count = int(stats.get('commentCount', 0))
                
                # CTR proxy: views / (expected impressions based on subs)
                ctr_proxy = view_count / (subscriber_count * 0.1) if subscriber_count > 0 else 0
                
                # Engagement rate
                engagement_rate = ((like_count + comment_count) / view_count * 100) if view_count > 0 else 0
                
                video = VideoPerformance(
                    video_id=video_id,
                    channel_id=channel_id,
                    title=snippet.get('title', ''),
                    description=snippet.get('description', '')[:500],
                    published_at=snippet.get('publishedAt', ''),
                    thumbnail_url=thumbnail_url,
                    view_count=view_count,
                    like_count=like_count,
                    comment_count=comment_count,
                    engagement_rate=engagement_rate,
                    ctr_proxy=ctr_proxy,
                    duration_seconds=duration_seconds,
                    tags=snippet.get('tags', []),
                    category_id=snippet.get('categoryId', '')
                )
                
                videos.append(video)
                collected += 1
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        
        print(f"📹 Collected {len(videos)} videos from channel")
        return videos
    
    def collect_channel_data(self, channel_handle: str, video_limit: int = 50) -> Dict:
        """
        Collect complete channel data including videos and stats.
        
        Returns a dictionary with all collected data.
        """
        print(f"🔍 Collecting data for {channel_handle}...")
        
        # Resolve channel
        channel_id, channel_name = self.get_channel_id(channel_handle)
        print(f"  Found: {channel_name} ({channel_id})")
        
        # Get channel stats
        channel_stats = self.get_channel_stats(channel_id)
        print(f"  Subscribers: {channel_stats.subscriber_count:,}")
        print(f"  Total Videos: {channel_stats.video_count:,}")
        
        # Collect videos
        videos = self.collect_videos(channel_id, limit=video_limit)
        
        # Calculate additional stats
        if videos:
            channel_stats.avg_views_per_video = sum(v.view_count for v in videos) / len(videos)
            
            # Upload frequency (average days between uploads)
            if len(videos) > 1:
                dates = sorted([
                    datetime.fromisoformat(v.published_at.replace('Z', '+00:00'))
                    for v in videos
                ])
                total_days = (dates[-1] - dates[0]).days
                channel_stats.upload_frequency_days = total_days / (len(videos) - 1) if total_days > 0 else 0
        
        return {
            'channel': channel_stats.to_dict(),
            'videos': [v.to_dict() for v in videos],
            'collected_at': datetime.now().isoformat()
        }
    
    def discover_competitors(self, channel_id: str, search_terms: List[str] = None, 
                              max_competitors: int = 10) -> List[Dict]:
        """
        Discover competitor channels in the same niche.
        
        Methods:
        1. Search YouTube for similar content
        2. Analyze related channels (if available)
        """
        competitors = []
        seen_ids = {channel_id}
        
        # Get channel info for context
        channel_stats = self.get_channel_stats(channel_id)
        
        # Search-based discovery
        if not search_terms:
            # Use channel name as default search
            search_terms = [channel_stats.channel_name.split()[0]]
        
        for term in search_terms[:3]:
            try:
                response = self.youtube.search().list(
                    part='snippet',
                    q=term,
                    type='channel',
                    maxResults=20
                ).execute()
                
                for item in response.get('items', []):
                    comp_id = item['id']['channelId']
                    
                    if comp_id in seen_ids:
                        continue
                    seen_ids.add(comp_id)
                    
                    try:
                        comp_stats = self.get_channel_stats(comp_id)
                        
                        # Filter by similar size (0.1x to 10x subscribers)
                        if channel_stats.subscriber_count > 0:
                            ratio = comp_stats.subscriber_count / channel_stats.subscriber_count
                            if 0.1 <= ratio <= 10:
                                competitors.append({
                                    'channel_id': comp_id,
                                    'channel_name': comp_stats.channel_name,
                                    'subscriber_count': comp_stats.subscriber_count,
                                    'size_ratio': ratio,
                                    'discovery_method': 'search'
                                })
                    except:
                        continue
                    
                    if len(competitors) >= max_competitors:
                        break
            except Exception as e:
                print(f"⚠️ Search failed for '{term}': {e}")
        
        print(f"🔍 Discovered {len(competitors)} competitor channels")
        return competitors[:max_competitors]
    
    def _parse_duration(self, duration: str) -> int:
        """Parse ISO 8601 duration to seconds."""
        import re
        
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration)
        
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds


# === Quick test ===
if __name__ == "__main__":
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        print("❌ YOUTUBE_API_KEY not set")
        exit(1)
    
    collector = YouTubeDataCollector(api_key=api_key)
    
    # Test with a sample channel
    test_channel = "@MrBeast"
    print(f"\n📊 Testing data collection for {test_channel}...")
    
    try:
        data = collector.collect_channel_data(test_channel, video_limit=5)
        
        print(f"\n✅ Collection successful!")
        print(f"  Channel: {data['channel']['channel_name']}")
        print(f"  Videos collected: {len(data['videos'])}")
        
        if data['videos']:
            sample = data['videos'][0]
            print(f"\n  Sample video: {sample['title'][:50]}...")
            print(f"    Views: {sample['view_count']:,}")
            print(f"    Likes: {sample['like_count']:,}")
            print(f"    CTR Proxy: {sample['ctr_proxy']:.2f}")
    except Exception as e:
        print(f"❌ Test failed: {e}")
