#!/usr/bin/env python3
"""
Market Intelligence - GapIntel v2 Module 2

Real-time market analysis combining Google Trends and YouTube niche exploration.

Features:
- Enhanced Google Trends integration with momentum classification
- Dynamic Niche Explorer (discovers trending videos, no hardcoded competitors)
- Topic trajectory analysis (RISING / STABLE / FALLING)

Usage:
    from market_intel import analyze_market_trends, explore_niche
    trends = analyze_market_trends(keywords)
    niche = explore_niche(youtube, category="finance")
"""

import time
import re
from typing import Optional
from pytrends.request import TrendReq
from datetime import datetime


def analyze_market_trends(keywords: list, region: str = "GB") -> dict:
    """
    Enhanced Google Trends analysis with momentum scoring.
    
    Args:
        keywords: List of keywords to analyze
        region: Geo region (GB for UK, US for USA, etc.)
    
    Returns:
        Dict with trend data for each keyword
    """
    results = {}
    pytrends = TrendReq(hl='en-GB', tz=0, geo=region)
    
    print(f"\n📈 MARKET INTEL: Analyzing {len(keywords)} keywords...")
    
    for kw in keywords[:15]:  # Limit to prevent rate limiting
        try:
            # Clean keyword
            clean_kw = re.sub(r'[^\w\s]', '', kw).strip()[:50]
            if not clean_kw or len(clean_kw) < 3:
                continue
            
            print(f"   • Checking: {clean_kw}...")
            time.sleep(2)  # Rate limiting
            
            # 3-month trend analysis
            pytrends.build_payload([clean_kw], timeframe='today 3-m', geo=region)
            data = pytrends.interest_over_time()
            
            if data.empty:
                results[kw] = {
                    "score": 0,
                    "trajectory": "UNKNOWN",
                    "momentum": 0,
                    "category": "unknown"
                }
                continue
            
            # Calculate metrics
            values = data[clean_kw].values
            
            # Current score (last data point)
            current_score = int(values[-1])
            
            # Average score
            avg_score = int(values.mean())
            
            # Momentum: Compare last week to first week
            first_week_avg = values[:4].mean() if len(values) >= 4 else values[0]
            last_week_avg = values[-4:].mean() if len(values) >= 4 else values[-1]
            
            if first_week_avg > 0:
                momentum = ((last_week_avg - first_week_avg) / first_week_avg) * 100
            else:
                momentum = 0
            
            # Classify trajectory
            if momentum > 25:
                trajectory = "RISING"
                category = "high_growth"
            elif momentum > 5:
                trajectory = "RISING"
                category = "growing"
            elif momentum < -25:
                trajectory = "FALLING"
                category = "declining"
            elif momentum < -5:
                trajectory = "FALLING"
                category = "saturating"
            else:
                trajectory = "STABLE"
                category = "evergreen"
            
            # Calculate trend strength (0-100)
            trend_strength = min(100, max(0, 
                (current_score * 0.4) + (avg_score * 0.3) + (abs(momentum) * 0.3 if momentum > 0 else 0)
            ))
            
            results[kw] = {
                "score": current_score,
                "avg_score": avg_score,
                "trajectory": trajectory,
                "momentum": round(momentum, 1),
                "category": category,
                "trend_strength": round(trend_strength, 1)
            }
            
            print(f"      ✓ Score: {current_score}, Trajectory: {trajectory} ({momentum:+.1f}%)")
            
        except Exception as e:
            print(f"      ⚠️ Failed: {str(e)[:50]}")
            results[kw] = {
                "score": 0,
                "trajectory": "ERROR",
                "momentum": 0,
                "category": "error"
            }
    
    return results


def explore_niche(youtube, category: str = "finance", region: str = "GB", max_videos: int = 20) -> dict:
    """
    Dynamic Niche Explorer - discovers what's currently trending in a niche.
    No hardcoded competitor list.
    
    Args:
        youtube: YouTube API client
        category: Niche to explore (finance, trading, investing, tech, etc.)
        region: Region code
        max_videos: Maximum videos to analyze
    
    Returns:
        Dict with trending videos, common patterns, and niche insights
    """
    # Category-specific search terms
    NICHE_QUERIES = {
        "finance": ["UK finance tips 2026", "money saving UK", "ISA investing", "personal finance UK"],
        "trading": ["day trading strategy", "forex trading UK", "stock trading tutorial", "trading for beginners"],
        "investing": ["investing for beginners UK", "stock market UK", "index fund investing", "dividend investing"],
        "tech": ["tech review 2026", "best gadgets", "tech news today", "smartphone review"],
        "business": ["start a business UK", "side hustle ideas", "passive income", "entrepreneurship"],
        "crypto": ["crypto trading", "bitcoin news", "cryptocurrency UK", "defi explained"]
    }
    
    queries = NICHE_QUERIES.get(category.lower(), [f"{category} tutorial", f"{category} guide", f"best {category}"])
    
    print(f"\n🔍 NICHE EXPLORER: Scanning '{category}' niche...")
    
    all_videos = []
    channels_seen = set()
    
    for query in queries:
        try:
            print(f"   • Searching: '{query}'...")
            
            response = youtube.search().list(
                part="snippet",
                q=query,
                type="video",
                regionCode=region,
                maxResults=10,
                order="viewCount",  # Top performing videos
                publishedAfter=(datetime.now().replace(day=1)).isoformat() + "Z"  # This month
            ).execute()
            
            video_ids = [item["id"]["videoId"] for item in response.get("items", [])]
            
            if video_ids:
                # Get video statistics
                stats_response = youtube.videos().list(
                    part="statistics,snippet,contentDetails",
                    id=",".join(video_ids)
                ).execute()
                
                for video in stats_response.get("items", []):
                    channel_id = video["snippet"]["channelId"]
                    
                    # Skip if we've already seen this channel (avoid duplicates)
                    if channel_id in channels_seen:
                        continue
                    channels_seen.add(channel_id)
                    
                    views = int(video["statistics"].get("viewCount", 0))
                    
                    all_videos.append({
                        "video_id": video["id"],
                        "title": video["snippet"]["title"],
                        "channel_title": video["snippet"]["channelTitle"],
                        "channel_id": channel_id,
                        "views": views,
                        "published_at": video["snippet"]["publishedAt"],
                        "thumbnail": video["snippet"]["thumbnails"]["high"]["url"],
                        "description": video["snippet"]["description"][:200]
                    })
                    
        except Exception as e:
            print(f"      ⚠️ Search failed: {str(e)[:50]}")
    
    # Sort by views and take top performers
    all_videos.sort(key=lambda x: x["views"], reverse=True)
    top_videos = all_videos[:max_videos]
    
    # Analyze patterns
    patterns = analyze_niche_patterns(top_videos)
    
    # Calculate niche saturation
    saturation = calculate_niche_saturation(top_videos, category)
    
    print(f"   ✓ Found {len(top_videos)} trending videos from {len(channels_seen)} unique channels")
    
    return {
        "category": category,
        "region": region,
        "trending_videos": top_videos,
        "unique_channels": len(channels_seen),
        "patterns": patterns,
        "saturation": saturation,
        "top_channels": list(set(v["channel_title"] for v in top_videos[:10]))
    }


def analyze_niche_patterns(videos: list) -> dict:
    """
    Analyze common patterns in trending niche videos.
    """
    if not videos:
        return {}
    
    # Title patterns
    title_words = []
    for v in videos:
        words = re.findall(r'\b[A-Za-z]{4,}\b', v["title"].lower())
        title_words.extend(words)
    
    # Count word frequency
    word_counts = {}
    for word in title_words:
        word_counts[word] = word_counts.get(word, 0) + 1
    
    # Filter common words
    STOP_WORDS = {"this", "that", "with", "from", "have", "will", "what", "when", "where", "your", "about"}
    common_words = [(w, c) for w, c in word_counts.items() if c >= 2 and w not in STOP_WORDS]
    common_words.sort(key=lambda x: x[1], reverse=True)
    
    # Number patterns (years, money amounts)
    has_year = sum(1 for v in videos if re.search(r'202[4-6]', v["title"]))
    has_money = sum(1 for v in videos if re.search(r'£|\$|k|K', v["title"]))
    has_numbers = sum(1 for v in videos if re.search(r'\d', v["title"]))
    
    # Title length
    avg_title_length = sum(len(v["title"]) for v in videos) / len(videos)
    
    # Average views
    avg_views = sum(v["views"] for v in videos) / len(videos)
    
    return {
        "common_title_words": common_words[:10],
        "titles_with_year": has_year,
        "titles_with_money": has_money,
        "titles_with_numbers": has_numbers,
        "avg_title_length": round(avg_title_length, 1),
        "avg_views": int(avg_views),
        "total_videos_analyzed": len(videos)
    }


def calculate_niche_saturation(videos: list, topic: str) -> dict:
    """
    Calculate how saturated a niche is based on video patterns.
    Higher saturation = more competition = harder to rank.
    
    Returns:
        Dict with saturation score (0-100) and classification
    """
    if not videos:
        return {"score": 50, "classification": "unknown", "inverse_score": 50}
    
    # Factors that indicate high saturation:
    # 1. Many recent videos
    # 2. High average views (established players)
    # 3. Many unique channels
    
    avg_views = sum(v["views"] for v in videos) / len(videos)
    unique_channels = len(set(v["channel_id"] for v in videos))
    
    # Calculate saturation score
    saturation_score = 0
    
    # View competition (normalized to 0-40)
    if avg_views > 1000000:
        saturation_score += 40
    elif avg_views > 100000:
        saturation_score += 30
    elif avg_views > 10000:
        saturation_score += 20
    else:
        saturation_score += 10
    
    # Channel competition (normalized to 0-30)
    channel_factor = min(30, unique_channels * 2)
    saturation_score += channel_factor
    
    # Volume factor (normalized to 0-30)
    volume_factor = min(30, len(videos) * 1.5)
    saturation_score += volume_factor
    
    # Normalize to 0-100
    saturation_score = min(100, saturation_score)
    
    # Classify
    if saturation_score >= 70:
        classification = "high"
    elif saturation_score >= 40:
        classification = "medium"
    else:
        classification = "low"
    
    # Inverse score (for opportunity calculation)
    inverse_score = 100 - saturation_score
    
    return {
        "score": round(saturation_score, 1),
        "classification": classification,
        "inverse_score": round(inverse_score, 1),
        "interpretation": f"{'High' if classification == 'high' else 'Medium' if classification == 'medium' else 'Low'} competition in this niche"
    }


def get_related_queries(keyword: str, region: str = "GB") -> list:
    """
    Get related/rising queries for a keyword from Google Trends.
    """
    try:
        pytrends = TrendReq(hl='en-GB', tz=0, geo=region)
        pytrends.build_payload([keyword], timeframe='today 3-m', geo=region)
        
        related = pytrends.related_queries()
        
        if keyword in related and related[keyword]["rising"] is not None:
            rising = related[keyword]["rising"].head(5).to_dict("records")
            return [{"query": r["query"], "value": r["value"]} for r in rising]
        
        return []
        
    except Exception as e:
        print(f"⚠️ Related queries failed: {e}")
        return []


def calculate_trend_momentum_score(trend_data: dict) -> float:
    """
    Calculate a normalized trend momentum score (0-100) for use in the scoring engine.
    
    Args:
        trend_data: Dict from analyze_market_trends
    
    Returns:
        Score between 0-100
    """
    if not trend_data:
        return 50  # Neutral score
    
    score = trend_data.get("score", 0)
    momentum = trend_data.get("momentum", 0)
    trajectory = trend_data.get("trajectory", "STABLE")
    
    # Base score from current interest (0-40)
    base_score = min(40, score * 0.4)
    
    # Momentum bonus (0-40)
    if momentum > 0:
        momentum_score = min(40, momentum * 0.8)
    else:
        momentum_score = max(0, 20 + momentum * 0.4)  # Penalty for declining
    
    # Trajectory bonus (0-20)
    trajectory_bonus = {
        "RISING": 20,
        "STABLE": 10,
        "FALLING": 0,
        "UNKNOWN": 5,
        "ERROR": 5
    }.get(trajectory, 5)
    
    final_score = base_score + momentum_score + trajectory_bonus
    
    return min(100, max(0, final_score))


if __name__ == "__main__":
    # Test the market intelligence module
    print("Testing Market Intelligence Module...")
    
    # Test trend analysis
    test_keywords = ["stock trading", "ISA investing", "side hustle"]
    results = analyze_market_trends(test_keywords)
    
    for kw, data in results.items():
        print(f"\n{kw}:")
        print(f"  Score: {data['score']}, Trajectory: {data['trajectory']}")
        print(f"  Momentum: {data['momentum']:+.1f}%")
        print(f"  Trend Strength: {data.get('trend_strength', 'N/A')}")
