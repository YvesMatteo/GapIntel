#!/usr/bin/env python3
"""
Market Intelligence Module for GAP Intel
Combines Google Trends momentum with YouTube niche saturation data.
"""

import time
import re
from typing import Optional, List, Dict, Any
from pytrends.request import TrendReq
from datetime import datetime
import pandas as pd
import numpy as np

class MarketIntelligence:
    def __init__(self, region: str = "GB"):
        self.region = region
        # Use a generous timeout for pytrends
        self.pytrends = TrendReq(hl=f'en-{region}', tz=0, geo=region, timeout=(10,25))

    def analyze_market_trends(self, keywords: List[str]) -> Dict[str, Any]:
        """
        Enhanced Google Trends analysis with momentum scoring and seasonality.
        """
        results = {}
        print(f"\n📈 MARKET INTEL: Analyzing {len(keywords)} keywords...")
        
        # Batching to avoid rate limits
        BATCH_SIZE = 5
        clean_keywords_map = {}
        valid_keywords = []

        for kw in keywords:
            clean = re.sub(r'[^\w\s]', '', kw).strip()[:50]
            if clean and len(clean) >= 3:
                clean_keywords_map[clean] = kw
                valid_keywords.append(clean)

        # Remove duplicates while preserving order
        valid_keywords = list(dict.fromkeys(valid_keywords))

        for i in range(0, len(valid_keywords), BATCH_SIZE):
            batch = valid_keywords[i:i+BATCH_SIZE]
            print(f"   • Checking batch: {batch}...")
            
            try:
                time.sleep(2)  # Rate limiting
                
                # 12-month trend analysis for seasonality
                self.pytrends.build_payload(batch, timeframe='today 12-m', geo=self.region)
                data = self.pytrends.interest_over_time()
                
                if data.empty:
                    for kw in batch:
                        original_kw = clean_keywords_map[kw]
                        results[original_kw] = self._get_empty_result()
                    continue
                
                for clean_kw in batch:
                    if clean_kw not in data:
                        continue
                        
                    original_kw = clean_keywords_map[clean_kw]
                    series = data[clean_kw]
                    
                    # 1. Calculate Core Metrics
                    current_score = int(series.iloc[-1])
                    avg_score = int(series.mean())
                    
                    # Short-term momentum (last 4 weeks)
                    short_term = series.tail(4)
                    if len(short_term) >= 2:
                        st_start = short_term.iloc[0]
                        st_end = short_term.iloc[-1]
                        if st_start > 0:
                            momentum = ((st_end - st_start) / st_start) * 100
                        else:
                            momentum = 100 if st_end > 0 else 0
                    else:
                        momentum = 0
                        
                    # 2. Seasonality Detection
                    seasonality = self._detect_seasonality(series)
                    
                    # 3. Trajectory Classification
                    trajectory = self._classify_trajectory(momentum)
                    
                    # 4. Composite Score
                    trend_strength = self._calculate_trend_strength(current_score, avg_score, momentum, trajectory)
                    
                    results[original_kw] = {
                        "score": current_score,
                        "avg_score": avg_score,
                        "trajectory": trajectory,
                        "momentum": round(momentum, 1),
                        "seasonality": seasonality,
                        "trend_strength": round(trend_strength, 1),
                        "is_opportunity": trend_strength > 60 and trajectory == "RISING"
                    }
                    
                    print(f"      ✓ {original_kw}: {trajectory} ({momentum:+.1f}%) | Strength: {trend_strength}")
                    
            except Exception as e:
                print(f"      ⚠️ Batch failed: {str(e)[:100]}")
                for kw in batch:
                    original_kw = clean_keywords_map[kw]
                    results[original_kw] = self._get_empty_result()
        
        return results

    def _get_empty_result(self):
        return {
            "score": 0, 
            "trajectory": "UNKNOWN", 
            "momentum": 0, 
            "seasonality": "unknown",
            "trend_strength": 0,
            "is_opportunity": False
        }

    def _detect_seasonality(self, series: pd.Series) -> str:
        """Detects if the trend is seasonal (e.g., peaks every December)."""
        # Simple heuristic: Check if peaks occur in specific months
        # In a real 12-m series, we have ~52 weeks.
        
        try:
            # Find peaks (above 80th percentile)
            threshold = series.quantile(0.8)
            peaks = series[series > threshold]
            
            if peaks.empty:
                return "flat"
                
            # Check month distribution of peaks
            peak_months = peaks.index.month.value_counts()
            
            # If peaks are concentrated in 1-2 months
            if not peak_months.empty and (peak_months.iloc[0] / len(peaks) > 0.5):
                top_month = peak_months.index[0]
                month_name = datetime(2000, top_month, 1).strftime('%B')
                return f"Peaks in {month_name}"
            
            return "volatile"
        except:
            return "unknown"

    def _classify_trajectory(self, momentum: float) -> str:
        if momentum > 25: return "RISING"
        if momentum > 5: return "STABLE_UP"
        if momentum < -25: return "FALLING"
        if momentum < -5: return "STABLE_DOWN"
        return "STABLE"

    def _calculate_trend_strength(self, current: int, avg: int, momentum: float, trajectory: str) -> float:
        """0-100 score indicating how 'hot' this topic is right now."""
        base = (current * 0.5) + (avg * 0.3)
        
        mom_bonus = 0
        if momentum > 0:
            mom_bonus = min(20, momentum * 0.5)
        
        traj_bonus = 0
        if "RISING" in trajectory: traj_bonus = 10
        if "FALLING" in trajectory: traj_bonus = -10
        
        return min(100, max(0, base + mom_bonus + traj_bonus))

    def explore_niche(self, youtube, category: str = "finance", max_videos: int = 20) -> dict:
        """
        Dynamic Niche Explorer - discovers what's currently trending in a niche.
        """
        NICHE_QUERIES = {
            "finance": ["UK finance tips 2026", "money saving UK", "ISA investing", "personal finance UK"],
            "trading": ["day trading strategy", "forex trading", "crypto trading", "trading for beginners"],
            "tech": ["tech review 2026", "best gadgets", "tech news", "smartphone review"],
        }
        
        queries = NICHE_QUERIES.get(category.lower(), [f"{category} trends", f"best {category} videos"])
        
        print(f"\n🔍 NICHE EXPLORER: Scanning '{category}' niche...")
        all_videos = []
        channels_seen = set()
        
        for query in queries:
            try:
                response = youtube.search().list(
                    part="snippet",
                    q=query,
                    type="video",
                    regionCode=self.region,
                    maxResults=10,
                    order="viewCount",
                    publishedAfter=(datetime.now().replace(day=1)).isoformat() + "Z"
                ).execute()
                
                video_ids = [item["id"]["videoId"] for item in response.get("items", [])]
                if not video_ids: continue
                
                stats_resp = youtube.videos().list(
                    part="statistics,snippet",
                    id=",".join(video_ids)
                ).execute()
                
                for video in stats_resp.get("items", []):
                    ch_id = video["snippet"]["channelId"]
                    if ch_id in channels_seen: continue
                    channels_seen.add(ch_id)
                    
                    all_videos.append({
                        "title": video["snippet"]["title"],
                        "views": int(video["statistics"].get("viewCount", 0)),
                        "channel": video["snippet"]["channelTitle"],
                        "url": f"https://youtu.be/{video['id']}"
                    })
            except Exception as e:
                print(f"   ⚠️ Search error: {e}")
                
        # Sort and return
        all_videos.sort(key=lambda x: x['views'], reverse=True)
        return {
            "category": category,
            "trending_videos": all_videos[:max_videos],
            "saturation_score": self._calculate_saturation(all_videos)
        }

    def _calculate_saturation(self, videos: list) -> int:
        if not videos: return 50
        avg_views = sum(v['views'] for v in videos) / len(videos)
        if avg_views > 500000: return 90  # High saturation
        if avg_views > 100000: return 70
        if avg_views > 10000: return 40
        return 20  # Low saturation

    def check_opportunity_alert(self, gap_data: dict, trend_data: dict) -> Optional[dict]:
        """
        Cross-references an internal gap with external market data.
        Returns an Alert object if this is a 'Golden Opportunity'.
        """
        gap_score = gap_data.get('score', 0) # Assuming some internal score
        trend_score = trend_data.get('trend_strength', 0)
        trajectory = trend_data.get('trajectory', 'STABLE')
        
        # Golden Opportunity Criteria:
        # 1. Rising Trend (> 60 strength + RISING)
        # 2. Addressed as a Gap internally (Verified TRUE_GAP)
        
        if trend_score > 50 and "RISING" in trajectory:
            return {
                "type": "GOLDEN_OPPORTUNITY",
                "topic": gap_data.get('topic_keyword'),
                "reason": f"Rising external trend ({trajectory}) with internal audience demand.",
                "score": (gap_score + trend_score) / 2
            }
        return None

if __name__ == "__main__":
    # Test
    mi = MarketIntelligence()
    print(mi.analyze_market_trends(["AI Agents", "Python Programming"]))
