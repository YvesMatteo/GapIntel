#!/usr/bin/env python3
"""
Channel Gap Analyzer - Phase 2 & 3

Analyzes the last N videos from a YouTube channel to find 'Content Gaps' -
topics the audience is asking for that the creator hasn't covered recently.

Usage:
    python3 gap_analyzer.py @ChannelHandle -n 5
    python3 gap_analyzer.py @Technoblade --videos 10
"""

import argparse
import json
import os
import re
import sys
import requests
import time
from datetime import datetime
from pathlib import Path
from pytrends.request import TrendReq

from dotenv import load_dotenv
load_dotenv()

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from openai import OpenAI
# google.generativeai will be imported dynamically to prevent warnings

# Import the modular process_video function
from ingest_manager import process_video


def get_channel_id(youtube, handle: str) -> tuple[str, str]:
    """
    Get channel ID and title from a channel handle (e.g., @Technoblade).
    
    Returns:
        Tuple of (channel_id, channel_title)
    """
    # Remove @ if present
    handle_clean = handle.lstrip('@')
    
    # Search for channel by handle
    request = youtube.search().list(
        part='snippet',
        q=f"@{handle_clean}",
        type='channel',
        maxResults=1
    )
    response = request.execute()
    
    if not response.get('items'):
        raise ValueError(f"Channel not found: @{handle_clean}")
    
    channel_id = response['items'][0]['snippet']['channelId']
    channel_title = response['items'][0]['snippet']['channelTitle']
    
    return channel_id, channel_title


def get_uploads_playlist_id(youtube, channel_id: str) -> str:
    """Get the 'Uploads' playlist ID for a channel."""
    request = youtube.channels().list(
        part='contentDetails',
        id=channel_id
    )
    response = request.execute()
    
    if not response.get('items'):
        raise ValueError(f"Could not get channel details for: {channel_id}")
    
    return response['items'][0]['contentDetails']['relatedPlaylists']['uploads']


def get_latest_videos(youtube, playlist_id: str, count: int, skip_shorts: bool = False) -> list[dict]:
    """
    Get the latest N videos from an uploads playlist.
    Optionally filters out Shorts (videos <= 60 seconds).
    
    Returns:
        List of dicts with video_id, title, published_at, duration_seconds
    """
    videos = []
    next_page_token = None
    
    # Fetch more than needed if filtering shorts
    fetch_multiplier = 3 if skip_shorts else 1
    
    while len(videos) < count:
        request = youtube.playlistItems().list(
            part='snippet',
            playlistId=playlist_id,
            maxResults=min(50, (count - len(videos)) * fetch_multiplier),
            pageToken=next_page_token
        )
        response = request.execute()
        
        # Get video IDs to fetch durations
        video_ids = [item['snippet']['resourceId']['videoId'] for item in response.get('items', [])]
        
        # Fetch video details (duration)
        if video_ids:
            details_request = youtube.videos().list(
                part='contentDetails',
                id=','.join(video_ids)
            )
            details_response = details_request.execute()
            
            # Map video_id to duration in seconds
            duration_map = {}
            for detail in details_response.get('items', []):
                duration_str = detail['contentDetails']['duration']  # ISO 8601 format: PT1M30S
                duration_map[detail['id']] = parse_duration(duration_str)
        
        for item in response.get('items', []):
            snippet = item['snippet']
            video_id = snippet['resourceId']['videoId']
            duration_seconds = duration_map.get(video_id, 0)
            
            # Skip Shorts if requested (Shorts are <= 60 seconds)
            if skip_shorts and duration_seconds <= 60:
                continue
            
            videos.append({
                'video_id': video_id,
                'title': snippet['title'],
                'published_at': snippet['publishedAt'],
                'url': f"https://youtube.com/watch?v={video_id}",
                'duration_seconds': duration_seconds
            })
            
            if len(videos) >= count:
                break
        
        next_page_token = response.get('nextPageToken')
        if not next_page_token or len(videos) >= count:
            break
    
    return videos[:count]


def parse_duration(duration_str: str) -> int:
    """
    Parse ISO 8601 duration format (PT1H2M30S) to seconds.
    """
    import re
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def filter_high_signal_comments(comments: list) -> list:
    """
    PHASE 1: Signal-to-Noise Pre-Filter (Python only, no AI cost).
    Filters out low-value comments and scores remaining by intent.
    """
    HIGH_INTENT_KEYWORDS = [
        'how to', 'how do', 'why did', 'can you explain', 'tutorial', 
        'struggling', 'please make', 'help me', 'confused', 'don\'t understand',
        'what is', 'what\'s the', 'could you', 'when will', 'video on'
    ]
    LOW_INTENT_KEYWORDS = [
        'love this', 'fire', 'king', 'goat', 'goated', 'underrated', 
        'amazing', 'great video', 'first', 'legend', 'best channel',
        '🔥', '❤️', '👑', '💯', 'w video', 'massive w'
    ]
    
    scored_comments = []
    
    for comment in comments:
        text = comment.get('text', '').lower()
        
        # Length filter: Skip very short comments
        if len(text) < 15:
            continue
        
        # Calculate signal score
        signal_score = 0
        
        # High intent markers
        for keyword in HIGH_INTENT_KEYWORDS:
            if keyword in text:
                signal_score += 2
        
        # Question mark is a strong signal
        if '?' in text:
            signal_score += 3
        
        # Low intent markers (reduce score)
        for keyword in LOW_INTENT_KEYWORDS:
            if keyword in text:
                signal_score -= 1
        
        # Only keep comments with positive signal score
        if signal_score > 0:
            comment['signal_score'] = signal_score
            scored_comments.append(comment)
    
    # Sort by signal score (highest first), then by likes
    scored_comments.sort(key=lambda x: (x['signal_score'], x['likes']), reverse=True)
    
    # Return top 50% of high-signal comments
    cutoff = max(len(scored_comments) // 2, 20)  # At least 20 comments
    filtered = scored_comments[:cutoff]
    
    print(f"   📊 Signal Filter: {len(comments)} → {len(filtered)} high-signal comments")
    
    return filtered


def get_trend_data(keywords: list) -> dict:
    """
    Check Google Trends interest (0-100) for given key phrases.
    Robust validation to prevent 429 errors.
    """
    trend_results = {}
    pytrends = TrendReq(hl='en-US', tz=360)
    
    print("\n📈 Checking Google Trends data...")
    for kw in keywords:
        try:
            # Clean keyword for trends (remove emojis, keep simple)
            clean_kw = re.sub(r'[^\w\s]', '', kw).strip()
            if not clean_kw: continue
            
            # Rate limit protection
            time.sleep(2)
            pytrends.build_payload([clean_kw], timeframe='today 3-m')
            data = pytrends.interest_over_time()
            
            if not data.empty:
                # Get average interest of last 30 days
                recent_data = data.tail(4) 
                score = int(recent_data[clean_kw].mean())
                # Determine trajectory
                slope = "STABLE"
                if len(recent_data) >= 2:
                    start, end = recent_data[clean_kw].iloc[0], recent_data[clean_kw].iloc[-1]
                    if end > start * 1.2: slope = "RISING"
                    elif end < start * 0.8: slope = "FALLING"
                
                trend_results[kw] = {"score": score, "trajectory": slope}
                print(f"   • {clean_kw}: {score} ({slope})")
            else:
                trend_results[kw] = {"score": 0, "trajectory": "UNKNOWN"}
        except Exception as e:
            print(f"   ⚠️ Trend lookup failed for '{kw}': {e}")
            trend_results[kw] = {"score": 0, "trajectory": "ERROR"}
            
    return trend_results


def fetch_competitor_videos(youtube, competitors: list) -> dict:
    """
    Fetch comprehensive metrics from competitor channels to analyze supply and performance.
    
    Returns:
        Dict keyed by competitor name with:
        - videos: List of recent video details
        - subscriber_count: Total subs
        - metrics: Aggregated stats (CVR, Format Mix, Avg Views)
    """
    comp_data = {}
    print("\n⚔️ Analyzing Competitors (Deep Dive)...")
    
    for comp in competitors:
        try:
            # 1. Get Channel Details (ID + Subs)
            handle_clean = comp.lstrip('@')
            search_resp = youtube.search().list(part='snippet', q=f"@{handle_clean}", type='channel', maxResults=1).execute()
            
            if not search_resp.get('items'):
                print(f"   ⚠️ Competitor not found: {comp}")
                continue
                
            channel_id = search_resp['items'][0]['snippet']['channelId']
            channel_title = search_resp['items'][0]['snippet']['channelTitle']
            
            # Fetch subs count
            chan_stats_resp = youtube.channels().list(part='statistics,contentDetails', id=channel_id).execute()
            stats = chan_stats_resp['items'][0]['statistics']
            subs_count = int(stats.get('subscriberCount', 0))
            uploads_id = chan_stats_resp['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            print(f"   • Fetching: {channel_title} ({subs_count:,} subs)")
            
            # 2. Get Last 20 Videos
            playlist_items = youtube.playlistItems().list(
                playlistId=uploads_id, part='snippet', maxResults=20
            ).execute()
            
            video_ids = [item['snippet']['resourceId']['videoId'] for item in playlist_items['items']]
            
            # 3. Get Video Statistics & Duration
            vid_metrics = []
            if video_ids:
                vid_resp = youtube.videos().list(
                    part='statistics,contentDetails,snippet',
                    id=','.join(video_ids)
                ).execute()
                
                for v in vid_resp['items']:
                    views = int(v['statistics'].get('viewCount', 0))
                    duration_sec = parse_duration(v['contentDetails']['duration'])
                    
                    # Estimate Question Density (Simple heuristic without fetching comments to save quota)
                    # Channels with high comment/view ratios often have high interaction/questions
                    comment_count = int(v['statistics'].get('commentCount', 0))
                    q_density_score = (comment_count / views * 1000) if views > 0 else 0
                    
                    vid_metrics.append({
                        'title': v['snippet']['title'],
                        'video_id': v['id'],
                        'views': views,
                        'duration_seconds': duration_sec,
                        'published_at': v['snippet']['publishedAt'],
                        'cvr_proxy': (views / subs_count * 100) if subs_count > 0 else 0,
                        'comment_count': comment_count,
                        'question_density_score': round(q_density_score, 2)
                    })
            
            # 4. Aggregate Metrics
            if vid_metrics:
                avg_views = sum(v['views'] for v in vid_metrics) / len(vid_metrics)
                avg_cvr = sum(v['cvr_proxy'] for v in vid_metrics) / len(vid_metrics)
                
                # Format Mix
                shorts = len([v for v in vid_metrics if v['duration_seconds'] <= 60])
                long_form = len([v for v in vid_metrics if v['duration_seconds'] > 60])
                avg_duration = sum(v['duration_seconds'] for v in vid_metrics) / len(vid_metrics)
                
                comp_data[channel_title] = {
                    "meta": {
                        "subscriber_count": subs_count,
                        "handle": comp,
                        "channel_id": channel_id
                    },
                    "metrics": {
                        "avg_views": int(avg_views),
                        "avg_cvr_proxy": round(avg_cvr, 2),
                        "avg_duration_sec": int(avg_duration),
                        "shorts_count": shorts,
                        "long_form_count": long_form,
                        "format_mix": "Hybrid" if (shorts > 0 and long_form > 0) else ("Shorts" if shorts > long_form else "Long-form")
                    },
                    "recent_videos": vid_metrics
                }
            
        except Exception as e:
            print(f"   ⚠️ Failed to analyze competitor {comp}: {e}")
            
    return comp_data


def call_ai_model(client, prompt: str, model_type: str = "openai", gemini_model_name: str = "gemini-2.5-pro") -> dict:
    """
    Abstracts API calls for OpenAI vs Gemini.
    """
    try:
        if model_type == "openai":
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            return json.loads(response.choices[0].message.content)
            
        elif model_type == "gemini":
            # client is the configured genai module or model object
            model = client.GenerativeModel(gemini_model_name,
                                         generation_config={"response_mime_type": "application/json"})
            response = model.generate_content(prompt)
            return json.loads(response.text)
            
        elif model_type == "local":
            # Ollama local inference
            try:
                response = requests.post('http://localhost:11434/api/chat', json={
                    "model": "llama3",
                    "messages": [{"role": "user", "content": prompt + "\n\nRESPOND IN JSON ONLY."}],
                    "format": "json",
                    "stream": False,
                    "options": {"temperature": 0.3}
                })
                if response.status_code == 200:
                    content = response.json().get('message', {}).get('content', '{}')
                    # Clean potential markdown code blocks if Ollama includes them
                    if "```json" in content:
                        content = content.replace("```json", "").replace("```", "")
                    return json.loads(content)
                else:
                    print(f"   ⚠️ Ollama Error: {response.text}")
                    return {}
            except Exception as e:
                print(f"   ⚠️ Local AI Failed: {e}. Is Ollama running?")
                return {}
            
    except Exception as e:
        print(f"   ⚠️ AI Call Failed ({model_type}): {e}")
        return {}


def extract_batch_signals(client, batch_comments: list, channel_name: str, batch_id: int, model_type: str = "openai", gemini_model: str = "gemini-2.5-pro") -> dict:
    """
    PHASE 2 (MAP): Extract USER PAIN POINTS, not video ideas.
    This prevents hallucination by asking for problems, not solutions.
    """
    total_batch_likes = sum(c['likes'] for c in batch_comments)
    
    prompt = f"""You are analyzing viewer comments for the YouTube channel "{channel_name}".

INPUT:
- Batch #{batch_id} of {len(batch_comments)} pre-filtered high-signal comments
- Total engagement in batch: {total_batch_likes:,} likes

TASK: Identify UNMET NEEDS and KNOWLEDGE GAPS from these comments.

CRITICAL RULES:
1. Extract what users are CONFUSED about or STRUGGLING with
2. Do NOT invent video titles or topics
3. Do NOT assume what they want - only report what they EXPLICITLY state
4. Focus on comments containing questions, requests for help, or expressions of confusion
5. The "topic_keyword" should be a NOUN or CONCEPT, not a title

For each pain point found:
- topic_keyword: The core subject they're asking about (e.g., "stop loss placement", "entry timing", "risk management")
- user_struggle: What specifically confuses them? (e.g., "Doesn't know when to exit trades")
- sentiment: One of [Frustrated, Curious, Begging]
- evidence: The EXACT comment text (verbatim quote)
- engagement: Sum of likes from comments about this topic

COMMENTS:
"""
    # Adjust context limit based on model capability
    limit = 1000 if model_type == "gemini" else 250
    
    for c in batch_comments[:limit]:
        prompt += f"[{c['likes']} likes] \"{c['text'][:150]}\"\n"
        
    prompt += """

OUTPUT JSON (only include pain points you found evidence for):
{
    "pain_points": [
        {
            "topic_keyword": "the core concept/noun",
            "user_struggle": "what they're confused about",
            "sentiment": "Frustrated/Curious/Begging",
            "evidence": "exact quote from comment",
            "engagement": 500
        }
    ]
}
"""
    result = call_ai_model(client, prompt, model_type, gemini_model)
    if not result:
        return {"pain_points": []}
    return result


def cluster_pain_points(client, all_pain_points: list, channel_name: str, model_type: str = "openai", gemini_model: str = "gemini-2.5-pro") -> dict:
    """
    PHASE 2B (REDUCE): Cluster similar pain points without inventing new concepts.
    """
    # Flatten all pain points from batches
    flat_points = []
    for batch in all_pain_points:
        for pp in batch.get('pain_points', []):
            flat_points.append(f"- Topic: {pp.get('topic_keyword', 'N/A')} | Struggle: {pp.get('user_struggle', 'N/A')} | Engagement: {pp.get('engagement', 0)}")
    
    if not flat_points:
        return {"clustered_pain_points": []}
    
    points_text = "\n".join(flat_points)
    
    prompt = f"""You are analyzing user pain points for "{channel_name}".

INPUT:
Pain points extracted from viewer comments (pre-filtered for quality).

TASK: Cluster similar pain points together.

RULES:
1. Group pain points that are about the SAME topic
2. Preserve the EXACT wording users used - do NOT invent new terms
3. Sum up the engagement scores when merging
4. Keep the most specific user_struggle description
5. Do NOT create generic categories - keep it specific to what users said

INPUT PAIN POINTS:
{points_text}

OUTPUT JSON:
{{
    "clustered_pain_points": [
        {{
            "topic_keyword": "exact term from comments",
            "user_struggle": "specific confusion described",
            "total_engagement": 1500,
            "mention_count": 5,
            "sample_evidence": ["quote 1", "quote 2"]
        }}
    ]
}}
"""
    return call_ai_model(client, prompt, model_type, gemini_model)


def verify_gaps_against_content(client, pain_points: list, transcripts: list, model_type: str = "openai", gemini_model: str = "gemini-2.5-pro") -> dict:
    """
    PHASE 3: The Gap Verification Engine.
    Cross-references pain points against creator's actual content.
    This is the 'sellable' feature that proves gaps are real.
    """
    # Prepare pain points summary
    pain_text = "\n".join([f"- {pp.get('topic_keyword', 'N/A')}: {pp.get('user_struggle', 'N/A')} (engagement: {pp.get('total_engagement', 0)})" for pp in pain_points])
    
    # Prepare transcript summaries
    transcript_text = ""
    for t in transcripts:
        transcript_text += f"\n--- VIDEO: {t['title']} ---\n{t['transcript_excerpt'][:2000]}\n"
    
    prompt = f"""You are verifying content gaps for a YouTube creator.

TASK: For each USER PAIN POINT, check if the creator has ALREADY addressed it.

## USER PAIN POINTS (what viewers are confused about):
{pain_text}

## CREATOR'S RECENT CONTENT (last 15 videos):
{transcript_text}

## VERIFICATION TASK:
For each pain point, determine:
- TRUE_GAP: The creator has NEVER addressed this topic in detail
- UNDER_EXPLAINED: The creator mentioned it but didn't explain it fully
- SATURATED: The creator already made detailed content about this

Be STRICT. If the transcript shows a full explanation, mark as SATURATED.
If it's only briefly mentioned, mark as UNDER_EXPLAINED.
If there's no mention at all, mark as TRUE_GAP.

OUTPUT JSON:
{{
    "verified_gaps": [
        {{
            "topic_keyword": "from input",
            "user_struggle": "from input",
            "total_engagement": 1500,
            "gap_status": "TRUE_GAP/UNDER_EXPLAINED/SATURATED",
            "verification_evidence": "Why you classified it this way (quote from transcript or 'No mention found')"
        }}
    ]
}}
"""
    return call_ai_model(client, prompt, model_type, gemini_model)


# Old merge_signals_reduce is replaced by cluster_pain_points and verify_gaps_against_content above


def analyze_with_ai(ai_client, videos_data: list[dict], channel_name: str, competitors_data: dict, model_type: str = "openai", gemini_model: str = "gemini-2.5-pro") -> dict:
    """
    ANALYTICAL EXTRACTION PIPELINE (4 Phases):
    1. Signal-to-Noise Filter (Python)
    2. Pain Point Extraction (AI)
    3. Gap Verification (AI)
    4. Title Generation for Verified Gaps Only (AI)
    """
    # =========================================================
    # PHASE 1: SIGNAL-TO-NOISE FILTER (Python only, no AI cost)
    # =========================================================
    all_comments = []
    transcripts_summary = []
    
    for v in videos_data:
        for comment in v['comments']:
            all_comments.append({
                'video': v['video_info']['title'],
                'text': comment['text'],
                'likes': comment['likes']
            })
        transcripts_summary.append({
            'title': v['video_info']['title'],
            'transcript_excerpt': v['transcript'][:3000]
        })
    
    total_raw_comments = len(all_comments)
    
    # Apply signal filter
    print(f"\n📊 PHASE 1: Signal-to-Noise Filter...")
    high_signal_comments = filter_high_signal_comments(all_comments)
    
    if not high_signal_comments:
        print("   ⚠️ No high-signal comments found. Falling back to top liked comments.")
        all_comments.sort(key=lambda x: x['likes'], reverse=True)
        high_signal_comments = all_comments[:100]
    
    # =========================================================
    # PHASE 2: PAIN POINT EXTRACTION (AI)
    # =========================================================
    print(f"\n🔍 PHASE 2: Extracting Pain Points...")
    
    # Dynamic batch size
    batch_size = 500 if model_type == "gemini" else 100
    all_pain_results = []
    
    for i in range(0, len(high_signal_comments), batch_size):
        batch = high_signal_comments[i:i+batch_size]
        batch_id = (i // batch_size) + 1
        print(f"   🔹 Batch {batch_id}: Analyzing {len(batch)} comments...")
        
        result = extract_batch_signals(ai_client, batch, channel_name, batch_id, model_type, gemini_model)
        all_pain_results.append(result)
    
    # Cluster pain points
    print(f"\n📉 PHASE 2B: Clustering Pain Points...")
    clustered = cluster_pain_points(ai_client, all_pain_results, channel_name, model_type, gemini_model)
    pain_points = clustered.get('clustered_pain_points', [])
    print(f"   ✓ Found {len(pain_points)} distinct user struggles")
    
    # =========================================================
    # PHASE 3: GAP VERIFICATION (The Sellable Feature)
    # =========================================================
    print(f"\n🔎 PHASE 3: Verifying Gaps Against Creator's Content...")
    verified = verify_gaps_against_content(ai_client, pain_points, transcripts_summary, model_type, gemini_model)
    verified_gaps = verified.get('verified_gaps', [])
    
    # Separate by status
    true_gaps = [g for g in verified_gaps if g.get('gap_status') == 'TRUE_GAP']
    under_explained = [g for g in verified_gaps if g.get('gap_status') == 'UNDER_EXPLAINED']
    saturated = [g for g in verified_gaps if g.get('gap_status') == 'SATURATED']
    
    print(f"   ✓ TRUE GAPS: {len(true_gaps)}")
    print(f"   ✓ Under-explained: {len(under_explained)}")
    print(f"   ✓ Saturated (already covered): {len(saturated)}")
    
    # =========================================================
    # PHASE 3.5: GOOGLE TRENDS CHECK
    # =========================================================
    actionable_gaps = true_gaps + under_explained
    
    if actionable_gaps:
        print(f"\n📈 PHASE 3.5: Checking Google Trends for {len(actionable_gaps)} opportunities...")
        
        # Get keywords from gaps
        trend_keywords = [g.get('topic_keyword', '')[:50] for g in actionable_gaps[:10]]  # Top 10 only
        trends_data = get_trend_data(trend_keywords)
        
        # Enrich gaps with trend data
        for gap in actionable_gaps:
            kw = gap.get('topic_keyword', '')[:50]
            trend_info = trends_data.get(kw, {})
            gap['trend_score'] = trend_info.get('score', 0)
            gap['trend_trajectory'] = trend_info.get('trajectory', 'UNKNOWN')
        
        print(f"   ✓ Trends data added for {len(trends_data)} topics")
    
    # =========================================================
    # PHASE 4: TITLE GENERATION (Only for verified gaps)
    # =========================================================
    if actionable_gaps:
        print(f"\n✍️ PHASE 4: Generating Titles for {len(actionable_gaps)} Verified Gaps...")
        
        gap_text = json.dumps(actionable_gaps, indent=2)
        
        title_prompt = f"""You are a YouTube title expert for "{channel_name}".

We have VERIFIED CONTENT GAPS (these are NOT hallucinated - they were cross-referenced against transcripts):

{gap_text}

COMPETITOR DATA (Use this to score 'competitor_influence'):
{json.dumps(competitors_data, indent=2)}

NOTE on Competitor Metrics:
- 'cvr_proxy': (Views / Subs) %. High CVR (>10%) means their audience LOVES this topic.
- 'question_density_score': Higher means more audience questions/engagement.
- 'format_mix': Shows if they use Shorts vs Long-form.


TASK: For each verified gap, generate 3 viral title ideas and score the INFLUENCE of each data source.

NOTE: Each gap now includes trend_score (0-100 from Google Trends) and trend_trajectory (RISING/STABLE/FALLING).

INFLUENCE SCORING (0-100 for each):
- comment_influence: How much did YouTube comments drive this opportunity? (based on engagement, mentions)
- competitor_influence: Are competitors covering this? (high = they cover it, opportunity to steal traffic)
- trend_influence: How much is this topic trending on Google? (use the trend_score from input directly)
- gap_severity_influence: How severe is the content gap? (TRUE_GAP = 100, UNDER_EXPLAINED = 60)

For each title:
1. Make it clickable and curiosity-driven
2. Reference the specific user struggle
3. If competitors cover this topic, suggest a "stealing traffic" angle

OUTPUT JSON:
{{
    "opportunities": [
        {{
            "topic_keyword": "from input",
            "gap_status": "TRUE_GAP or UNDER_EXPLAINED",
            "user_struggle": "from input",
            "total_engagement": 1500,
            "verification_evidence": "from input",
            "viral_titles": ["Title 1", "Title 2", "Title 3"],
            "why_this_gap": "Explanation of why this is a real opportunity",
            "influence_scores": {{
                "comment_influence": 85,
                "competitor_influence": 40,
                "trend_influence": 60,
                "gap_severity_influence": 100,
                "overall_score": 75
            }}
        }}
    ],
    "top_opportunity": {{
        "topic_keyword": "best opportunity",
        "best_title": "Your Next Viral Video",
        "engagement_potential": 5000,
        "reason": "Why this is the #1 pick"
    }}
}}
"""
        final_result = call_ai_model(ai_client, title_prompt, model_type, gemini_model)
    else:
        final_result = {"opportunities": [], "top_opportunity": {}}
    
    # =========================================================
    # RETURN STRUCTURED DATA
    # =========================================================
    return {
        'pipeline_stats': {
            'raw_comments': total_raw_comments,
            'high_signal_comments': len(high_signal_comments),
            'pain_points_found': len(pain_points),
            'true_gaps': len(true_gaps),
            'under_explained': len(under_explained),
            'saturated': len(saturated)
        },
        'verified_gaps': verified_gaps,
        'opportunities': final_result.get('opportunities', []),
        'top_opportunity': final_result.get('top_opportunity', {}),
        'competitors_analyzed': list(competitors_data.keys()) if competitors_data else [],
        'competitor_metrics': competitors_data  # Save full rich data for dashboard
    }


def generate_report(output_path: Path, channel_name: str, videos_data: list, analysis: dict, is_sample: bool = False):
    """Generate the analytical GAP_REPORT.md file with verified gaps."""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        if is_sample:
            f.write("# 🎁 FREE SAMPLE ANALYSIS: " + channel_name + "\n")
            f.write("> *This is a limited preview analysis. Contact us for the full Deep Dive Report.*\n\n")
        else:
            f.write(f"# 🎯 Verified Content Gap Report: {channel_name}\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  \n")
        f.write(f"**Videos Analyzed:** {len(videos_data)}  \n")
        
        # Pipeline Stats
        stats = analysis.get('pipeline_stats', {})
        f.write(f"\n### 📊 Analysis Pipeline\n")
        f.write(f"| Stage | Count |\n")
        f.write(f"|-------|-------|\n")
        f.write(f"| Raw Comments | {stats.get('raw_comments', 0):,} |\n")
        f.write(f"| High-Signal (after filter) | {stats.get('high_signal_comments', 0):,} |\n")
        f.write(f"| Pain Points Identified | {stats.get('pain_points_found', 0)} |\n")
        f.write(f"| **TRUE GAPS** | {stats.get('true_gaps', 0)} |\n")
        f.write(f"| Under-explained | {stats.get('under_explained', 0)} |\n")
        f.write(f"| Already Covered | {stats.get('saturated', 0)} |\n")
        
        f.write("\n---\n\n")
        
        # =========================================================
        # TOP OPPORTUNITY
        # =========================================================
        top_opp = analysis.get('top_opportunity', {})
        if top_opp and top_opp.get('topic_keyword'):
            f.write("## 🏆 #1 VERIFIED OPPORTUNITY\n\n")
            f.write(f"### {top_opp.get('topic_keyword', 'Unknown')}\n\n")
            f.write(f"> **{top_opp.get('best_title', 'No title generated')}**\n\n")
            f.write(f"**Engagement Potential:** {top_opp.get('engagement_potential', 0):,}  \n")
            f.write(f"**Why This is #1:** {top_opp.get('reason', 'N/A')}  \n\n")
            f.write("---\n\n")
        
        # =========================================================
        # VERIFIED OPPORTUNITIES (Actionable Gaps)
        # =========================================================
        opportunities = analysis.get('opportunities', [])
        
        if opportunities:
            f.write("## ✅ Verified Content Gaps (Ready to Act On)\n\n")
            f.write("*These gaps were verified against your recent video transcripts.*\n\n")
            
            for i, opp in enumerate(opportunities, 1):
                status = opp.get('gap_status', 'UNKNOWN')
                emoji = '🔴' if status == 'TRUE_GAP' else '🟡'
                
                f.write(f"### {emoji} {i}. {opp.get('topic_keyword', 'Unknown')}\n\n")
                
                # Status & Evidence
                f.write(f"| Attribute | Value |\n")
                f.write(f"|-----------|-------|\n")
                f.write(f"| **Status** | {status} |\n")
                f.write(f"| **User Struggle** | {opp.get('user_struggle', 'N/A')} |\n")
                f.write(f"| **Engagement** | {opp.get('total_engagement', 0):,} |\n")
                f.write(f"| **Verification** | {opp.get('verification_evidence', 'N/A')} |\n\n")
                
                # Why this is a gap
                if opp.get('why_this_gap'):
                    f.write(f"**Why This is a Gap:** {opp.get('why_this_gap')}  \n\n")
                
                # Viral Titles
                titles = opp.get('viral_titles', [])
                if titles:
                    f.write("**💡 Suggested Titles:**\n")
                    for j, title in enumerate(titles[:3], 1):
                        f.write(f"{j}. {title}\n")
                    f.write("\n")
        else:
            f.write("## ✅ No Verified Gaps Found\n\n")
            f.write("Your recent content appears to cover what your audience is asking for!\n\n")
        
        # =========================================================
        # SATURATED TOPICS (Already Covered)
        # =========================================================
        verified_gaps = analysis.get('verified_gaps', [])
        saturated = [g for g in verified_gaps if g.get('gap_status') == 'SATURATED']
        
        if saturated:
            f.write("---\n\n")
            f.write("## 🟢 Already Covered Topics\n\n")
            f.write("*These topics are already well-covered in your recent videos.*\n\n")
            
            for item in saturated:
                f.write(f"- **{item.get('topic_keyword', 'Unknown')}**: {item.get('verification_evidence', 'Covered')}\n")
            f.write("\n")
        
        # =========================================================
        # VIDEOS ANALYZED
        # =========================================================
        f.write("---\n\n")
        f.write("## 📹 Videos Analyzed\n\n")
        
        for v in videos_data:
            info = v['video_info']
            f.write(f"- **{info['title']}**  \n")
            f.write(f"  Comments: {len(v['comments'])} | ")
            f.write(f"[Watch]({info['url']})\n\n")
        
        # =========================================================
        # COMPETITORS
        # =========================================================
        # =========================================================
        # COMPETITORS
        # =========================================================
        competitors = analysis.get('competitors_analyzed', [])
        if competitors:
            f.write("---\n\n")
            f.write("## ⚔️ Competitors Analyzed\n\n")
            f.write("---\n\n")
            f.write("## ⚔️ Competitors Analyzed\n\n")
            
            # Check if we have rich metrics
            comp_metrics = analysis.get('competitor_metrics', {})
            
            if comp_metrics:
                f.write("| Competitor | Subs | Avg Views | CVR Proxy | Format Mix |\n")
                f.write("|------------|------|-----------|-----------|------------|\n")
                for name, data in comp_metrics.items():
                    metrics = data.get('metrics', {})
                    meta = data.get('meta', {})
                    subs = meta.get('subscriber_count', 0)
                    f.write(f"| {name} | {subs:,} | {metrics.get('avg_views', 0):,} | {metrics.get('avg_cvr_proxy', 0)}% | {metrics.get('format_mix', 'N/A')} |\n")
            else:
                for comp in competitors:
                    f.write(f"- {comp}\n")
        
        if is_sample:
            f.write("\n---\n")
            f.write("### 🚀 Want the Full Analysis?\n")
            f.write("This sample only analyzed 3 recent videos. The full report covers:\n")
            f.write("- **30+ Videos** Analyzed\n")
            f.write("- **Deep Competitor Strategy** Breakdown\n")
            f.write("- **Viral Thumbnail Concepts**\n")
            f.write("- **Content Calendar** Plan\n\n")
            f.write("**[Reply 'FULL' to upgrade to the Deep Dive Analysis]**\n")
    
    print(f"\n📄 Report saved to: {output_path}")





def main():
    parser = argparse.ArgumentParser(
        description="Analyze a YouTube channel for content gaps.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 gap_analyzer.py @Technoblade -n 5
    python3 gap_analyzer.py @mkbhd --videos 10 --model small
        """
    )
    parser.add_argument('channel', help='YouTube channel handle (e.g., @Technoblade)')
    parser.add_argument('-n', '--videos', type=int, default=5,
                        help='Number of recent videos to analyze (default: 5)')
    parser.add_argument('--model', '-m', default='base',
                        choices=['tiny', 'base', 'small', 'medium', 'large'],
                        help='Whisper model size (default: base)')
    parser.add_argument('--skip-shorts', action='store_true',
                        help='Skip YouTube Shorts (videos <= 60 seconds)')
    parser.add_argument('--ai', choices=['openai', 'gemini', 'local'], default='openai',
                        help='AI backend: openai (default), gemini (huge context), or local (free/ollama).')
    parser.add_argument('--gemini-model', default='gemini-2.5-pro',
                        help='Specific Gemini model to use (default: gemini-2.5-pro). Try gemini-3-pro-preview!')
    parser.add_argument('--competitors', nargs='+', help='List of competitor channel handles (e.g. @Rival1 @Rival2)')
    parser.add_argument('--sample', action='store_true', help='Run in "Free Sample" mode (3 videos, preview report)')
    
    args = parser.parse_args()
    
    # Load API keys
    youtube_api_key = os.getenv('YOUTUBE_API_KEY')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    
    if not youtube_api_key:
        print("❌ YOUTUBE_API_KEY not found in .env")
        sys.exit(1)
    
    # Validate AI keys based on selection
    ai_client = None
    if args.ai == 'openai':
        if not openai_api_key:
            print("❌ OPENAI_API_KEY not found in .env")
            sys.exit(1)
        ai_client = OpenAI(api_key=openai_api_key)
    elif args.ai == 'gemini':
        import google.generativeai as genai
        if not gemini_api_key:
            print("❌ GEMINI_API_KEY not found in .env")
            sys.exit(1)
        genai.configure(api_key=gemini_api_key)
        ai_client = genai
    elif args.ai == 'local':
        # No client needed for requests, but we verify connection
        try:
            resp = requests.get('http://localhost:11434/')
            if resp.status_code != 200:
                 print("❌ Ollama not responding at localhost:11434. Run 'ollama serve'")
                 sys.exit(1)
            ai_client = "local_requests" # Placeholder
        except Exception:
             print("❌ Ollama not responding. Is it installed and running?")
             sys.exit(1)
    
    print(f"\n🔍 Channel Gap Analyzer (AI: {args.ai.upper()})")
    print(f"="*50)
    
    try:
        # Initialize APIs
        youtube = build('youtube', 'v3', developerKey=youtube_api_key)
        
        if args.sample:
            print("\n🎁 RUNNING IN FREE SAMPLE MODE")
            print("   (Limiting analysis to 3 videos for preview)")
            args.videos = 3
            args.skip_shorts = True  # Better quality for samples
        
        # Step 1: Find channel
        print(f"\n📺 Looking up channel: {args.channel}")
        channel_id, channel_name = get_channel_id(youtube, args.channel)
        print(f"   ✓ Found: {channel_name}")
        
        # Step 2: Get uploads playlist
        uploads_playlist = get_uploads_playlist_id(youtube, channel_id)
        
        # Step 3: Get latest N videos
        shorts_text = " (excluding Shorts)" if args.skip_shorts else ""
        print(f"\n📋 Fetching last {args.videos} videos{shorts_text}...")
        videos = get_latest_videos(youtube, uploads_playlist, args.videos, skip_shorts=args.skip_shorts)
        for v in videos:
            duration_mins = v.get('duration_seconds', 0) // 60
            print(f"   • {v['title'][:45]}... ({duration_mins}m)")
        
        # Step 4: Process each video
        print(f"\n⚙️ Processing videos (this may take a while)...")
        videos_data = []
        
        for i, video in enumerate(videos, 1):
            print(f"\n[{i}/{len(videos)}] {video['title'][:40]}...")
            try:
                result = process_video(
                    video['url'], 
                    youtube_api_key, 
                    model_name=args.model,
                    verbose=True
                )
                videos_data.append(result)
            except Exception as e:
                print(f"   ⚠️ Failed: {e}")
                continue
        
        if not videos_data:
            print("❌ No videos could be processed")
            sys.exit(1)
        
        # Step 4.5: Competitor Analysis (Step 8)
        competitors_data = {}
        if args.competitors:
             competitors_data = fetch_competitor_videos(youtube, args.competitors)

        # Step 5: AI Analysis
        print(f"\n🧠 Running AI gap analysis...")
        analysis = analyze_with_ai(ai_client, videos_data, channel_name, competitors_data, model_type=args.ai, gemini_model=args.gemini_model)
        
        # Setup output paths
        script_dir = Path(__file__).parent.resolve()
        data_dir = script_dir / "data"
        data_dir.mkdir(exist_ok=True)
        
        # Save JSON for Dashboard (Step 9)
        json_output_path = script_dir / "analysis_result.json"
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2)
        print(f"📊 Dashboard data saved to: {json_output_path}")

        # IMPORTANT: Print JSON to stdout for server.py to capture
        print("\n___JSON_START___")
        print(json.dumps(analysis))
        print("___JSON_END___\n")

        # Step 6: Generate report
        
        
        report_path = data_dir / f"GAP_REPORT_{channel_name.replace(' ', '_')}.md"
        generate_report(report_path, channel_name, videos_data, analysis, is_sample=args.sample)
        
        print(f"\n🎉 Analysis complete!")
        print(f"   Report: {report_path}")
        
        # Print quick summary
        top_gap = analysis.get('top_gap', {})
        if top_gap.get('topic'):
            print(f"\n   🎯 Top Gap: {top_gap['topic']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("⏳ Initializing Gap Analyzer...", flush=True)
    main()

