"""
Massive Data Collector V2
-------------------------
Fetches large-scale YouTube data for scientific ML training.
 stratified by Niche.

Features:
- Niche-based searching (Gaming, Tech, etc.)
- Parallel execution
- Rate limit handling
- Data normalization
- Storage to local Parquet/JSON or Supabase
"""

import os
import json
import time
import argparse
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Scientific V2 Imports
import sys
import os

# Script path: railway-api/premium/ml_models/data_collector_v2.py
# We want to add 'railway-api' to sys.path to allow 'from premium...' imports
current_dir = os.path.dirname(os.path.abspath(__file__)) # ml_models
premium_dir = os.path.dirname(current_dir) # premium
railway_api_dir = os.path.dirname(premium_dir) # railway-api

if railway_api_dir not in sys.path:
    sys.path.append(railway_api_dir)

try:
    from premium.ml_models.text_embedder import TextEmbedder
    from premium.thumbnail_extractor import ThumbnailFeatureExtractor
    HAS_V2_MODULES = True
except ImportError as e:
    print(f"⚠️ V2 Modules not found (ImportError: {e}). Skipping advanced features.")
    HAS_V2_MODULES = False

# Load env
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# --- Configuration ---
NICHES = [
    "Gaming",
    "Technology & Software",
    "Education & Science",
    "Finance & Business", 
    "Lifestyle & Vlogs",
    "Health & Fitness",
    "Entertainment & Comedy", 
    "Food & Cooking",
    "DIY & Crafts", 
    "Beauty & Fashion",
    "News & Politics", 
    "Travel"
]

# Map specific search queries to help finding niche content if category ID isn't enough
NICHE_QUERIES = {
    "Gaming": ["gaming", "gameplay", "walkthrough", "minecraft", "roblox", "fortnite"],
    "Technology & Software": ["tech review", "coding tutorial", "smartphone review", "software engineering", "AI tools"],
    "Education & Science": ["science explained", "math tutorial", "history documentary", "physics", "biology"],
    "Finance & Business": ["investing", "stock market", "passive income", "business tips", "crypto"],
    "Lifestyle & Vlogs": ["daily vlog", "day in the life", "productivity", "morning routine"],
    "Health & Fitness": ["workout routine", "healthy diet", "weight loss", "yoga", "gym motivation"],
    "Entertainment & Comedy": ["comedy skit", "funny moments", "prank", "stand up comedy"],
    "Food & Cooking": ["recipe", "cooking tutorial", "street food", "food review"],
    "DIY & Crafts": ["diy project", "home decor", "woodworking", "art tutorial"],
    "Beauty & Fashion": ["makeup tutorial", "clothing haul", "skincare routine", "fashion trends"],
    "News & Politics": ["news update", "political commentary", "world events", "breaking news"],
    "Travel": ["travel vlog", "city tour", "best places to visit", "backpacking"]
}

OUTPUT_DIR = "training_data"

class MassiveDataCollector:
    def __init__(self, api_key: str):
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.known_video_ids = set()
        
        # Ensure output dir exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        # Load existing IDs to avoid dupes
        self._load_existing_ids()
        
        # Initialize V2 Extractors
        self.embedder = None
        self.thumb_extractor = None
        if HAS_V2_MODULES:
            try:
                self.embedder = TextEmbedder()
                # Disable OCR/Face for speed if massive batch, 
                # but user requested Quality Features so we enable them.
                self.thumb_extractor = ThumbnailFeatureExtractor(use_ocr=True, use_face_detection=True)
                print("✅ V2 Features Enabled: Text Embeddings + Thumbnail Analysis")
            except Exception as e:
                print(f"⚠️ Failed to init V2 modules: {e}")

    def _load_existing_ids(self):
        """Load already fetched video IDs to prevent duplicate work."""
        for filename in os.listdir(OUTPUT_DIR):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(OUTPUT_DIR, filename), 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for v in data:
                                self.known_video_ids.add(v.get('video_id'))
                except:
                    pass
        print(f"Loaded {len(self.known_video_ids)} existing video IDs.")

    def search_niche(self, niche: str, max_results: int = 500) -> List[Dict]:
        """Search for videos within a specific niche."""
        print(f" Searching niche: {niche}...")
        videos = []
        next_page_token = None
        
        # Cycle through queries for variety
        queries = NICHE_QUERIES.get(niche, [niche])
        random.shuffle(queries)
        
        query_idx = 0
        total_fetched = 0
        
        while total_fetched < max_results:
            current_query = queries[query_idx % len(queries)]
            
            try:
                request = self.youtube.search().list(
                    part="snippet",
                    q=current_query,
                    type="video",
                    maxResults=50,
                    order="date", # Get recent stuff first usually good practice, or 'relevance'
                    pageToken=next_page_token,
                    relevanceLanguage="en",
                    videoDuration="medium" # Filter short/long? 'medium' is 4-20 mins, good for analysis
                )
                response = request.execute()
                
                items = response.get('items', [])
                if not items:
                    print(f"  No more items for query '{current_query}'")
                    query_idx += 1
                    next_page_token = None
                    if query_idx >= len(queries): # Exhausted all queries
                        break
                    continue
                
                # Extract IDs
                vid_ids = [item['id']['videoId'] for item in items if item['id']['videoId'] not in self.known_video_ids]
                
                if vid_ids:
                    # Get full details (stats, contentDetails)
                    details = self._fetch_video_details(vid_ids, niche)
                    videos.extend(details)
                    self.known_video_ids.update(vid_ids)
                    total_fetched += len(details)
                    print(f"  Fetched {len(details)} videos for '{current_query}' (Total: {total_fetched}/{max_results})")
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    query_idx += 1
                    if query_idx >= len(queries):
                        break
                        
            except HttpError as e:
                print(f"  HTTP Error: {e}")
                if "quota" in str(e).lower():
                    print("  CRITICAL: Quota exceeded.")
                    break
                time.sleep(5) # backoff
            except Exception as e:
                print(f"  Error: {e}")
                time.sleep(1)

        return videos

    def _fetch_video_details(self, video_ids: List[str], niche: str) -> List[Dict]:
        """Fetch detailed stats for a list of video IDs."""
        if not video_ids:
            return []
            
        try:
            request = self.youtube.videos().list(
                part="snippet,statistics,contentDetails,topicDetails",
                id=",".join(video_ids)
            )
            response = request.execute()
            
            clean_videos = []
            for item in response.get('items', []):
                stats = item.get('statistics', {})
                snippet = item.get('snippet', {})
                content = item.get('contentDetails', {})
                
                # Basic cleaning
                video_data = {
                    'video_id': item['id'],
                    'niche': niche,
                    'title': snippet.get('title'),
                    'channel_id': snippet.get('channelId'),
                    'channel_title': snippet.get('channelTitle'),
                    'published_at': snippet.get('publishedAt'),
                    'description': snippet.get('description'),
                    'tags': snippet.get('tags', []),
                    'category_id': snippet.get('categoryId'),
                    'duration_iso': content.get('duration'),
                    'definition': content.get('definition'),
                    'view_count': int(stats.get('viewCount', 0)),
                    'like_count': int(stats.get('likeCount', 0)),
                    'comment_count': int(stats.get('commentCount', 0)),
                    'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url'),
                    'collected_at': datetime.now().isoformat()
                }
                
                # Check 7-day performance logic would require historical data tracking
                # For now, we collect the snapshot. 
                # Ideally, we'd fetch "upload_date" and calculate days_since_upload
                
                # Advanced Feature Extraction (V2)
                if self.embedder and video_data.get('title'):
                    # 1. Text Embeddings
                    emb = self.embedder.embed(video_data['title'])
                    video_data['title_embedding'] = emb.tolist() # JSON serializable
                
                if self.thumb_extractor and video_data.get('thumbnail_url'):
                    # 2. Thumbnail Features
                    try:
                        features = self.thumb_extractor.extract_from_url(video_data['thumbnail_url'])
                        video_data['thumbnail_features'] = features.to_dict()
                    except Exception as e:
                        # Don't fail the whole batch for one bad image
                        # print(f"  Thumb error: {e}") 
                        pass
                
                clean_videos.append(video_data)
                
            return clean_videos
            
        except Exception as e:
            print(f"  Error fetching details: {e}")
            return []

    def save_batch(self, videos: List[Dict], niche: str):
        """Save a batch of videos to disk."""
        if not videos:
            return
            
        filename = f"{niche.replace(' ', '_').lower()}_{int(time.time())}.json"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, 'w') as f:
            json.dump(videos, f, indent=2)
        print(f"Saved {len(videos)} videos to {filepath}")

    def run_collection(self, target_per_niche: int = 1000):
        """Run collection for all niches."""
        print(f"Starting Massive Data Collection (Target: {target_per_niche} per niche)")
        
        for niche in NICHES:
            print(f"\n--- Processing Niche: {niche} ---")
            videos = self.search_niche(niche, max_results=target_per_niche)
            self.save_batch(videos, niche)
            time.sleep(2) # be nice to API

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect YouTube Data per Niche")
    parser.add_argument("--limit", type=int, default=100, help="Videos per niche to fetch")
    args = parser.parse_args()
    
    if not YOUTUBE_API_KEY:
        print("ERROR: YOUTUBE_API_KEY not found in .env")
        exit(1)
        
    collector = MassiveDataCollector(YOUTUBE_API_KEY)
    collector.run_collection(target_per_niche=args.limit)
