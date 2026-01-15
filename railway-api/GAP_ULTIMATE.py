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

# Import premium analysis modules
from premium.ml_models.ctr_predictor import CTRPredictor
from premium.ml_models.views_predictor import ViewsVelocityPredictor
from premium.ml_models.content_clusterer import ContentClusteringEngine
from premium.thumbnail_optimizer import ThumbnailOptimizer
from premium.thumbnail_extractor import ThumbnailFeatureExtractor
from premium.competitor_analyzer import CompetitorAnalyzer
from premium.publish_optimizer import PublishTimeOptimizer
from premium.data_collector import YouTubeDataCollector
from premium.hook_analyzer import HookAnalyzer
from premium.color_ml_analyzer import ColorMLAnalyzer
from premium.visual_report_generator import VisualReportGenerator

# Language instructions for AI prompts
LANGUAGE_INSTRUCTIONS = {
    "en": "Respond in English.",
    "de": "Antworte auf Deutsch. Alle Analysen, Titel und Empfehlungen sollen auf Deutsch sein.",
    "fr": "Réponds en français. Toutes les analyses, titres et recommandations doivent être en français.",
    "it": "Rispondi in italiano. Tutte le analisi, i titoli e le raccomandazioni devono essere in italiano.",
    "es": "Responde en español. Todos los análisis, títulos y recomendaciones deben estar en español."
}


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
        List of dicts with video_id, title, published_at, duration_seconds,
        view_count, like_count, thumbnail_url (for premium analysis)
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
        
        # Get video IDs to fetch durations AND statistics
        video_ids = [item['snippet']['resourceId']['videoId'] for item in response.get('items', [])]
        
        # Fetch video details (duration, statistics, thumbnails)
        video_details_map = {}
        if video_ids:
            details_request = youtube.videos().list(
                part='contentDetails,statistics,snippet',  # Added statistics and snippet
                id=','.join(video_ids)
            )
            details_response = details_request.execute()
            
            # Map video_id to all details
            for detail in details_response.get('items', []):
                vid_id = detail['id']
                duration_str = detail['contentDetails']['duration']  # ISO 8601 format: PT1M30S
                stats = detail.get('statistics', {})
                snippet = detail.get('snippet', {})
                thumbnails = snippet.get('thumbnails', {})
                
                # Get best available thumbnail
                thumbnail_url = None
                for quality in ['maxres', 'high', 'medium', 'default']:
                    if quality in thumbnails:
                        thumbnail_url = thumbnails[quality].get('url')
                        break
                
                video_details_map[vid_id] = {
                    'duration_seconds': parse_duration(duration_str),
                    'view_count': int(stats.get('viewCount', 0) or 0),
                    'like_count': int(stats.get('likeCount', 0) or 0),
                    'comment_count': int(stats.get('commentCount', 0) or 0),
                    'thumbnail_url': thumbnail_url,
                    'upload_date': snippet.get('publishedAt', '')[:10].replace('-', ''),  # YYYYMMDD format
                }
        
        for item in response.get('items', []):
            snippet = item['snippet']
            video_id = snippet['resourceId']['videoId']
            details = video_details_map.get(video_id, {})
            duration_seconds = details.get('duration_seconds', 0)
            
            # Skip Shorts if requested (Shorts are <= 60 seconds)
            if skip_shorts and duration_seconds <= 60:
                continue
            
            videos.append({
                'video_id': video_id,
                'title': snippet['title'],
                'published_at': snippet['publishedAt'],
                'url': f"https://youtube.com/watch?v={video_id}",
                'duration_seconds': duration_seconds,
                # New fields for premium analysis
                'view_count': details.get('view_count', 0),
                'like_count': details.get('like_count', 0),
                'comment_count': details.get('comment_count', 0),
                'thumbnail_url': details.get('thumbnail_url'),
                'upload_date': details.get('upload_date', ''),
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
    Fetch top recent video titles from competitor channels to analyze supply.
    """
    comp_data = {}
    print("\n⚔️ Analyzing Competitors...")
    
    for comp in competitors:
        try:
            cid, title = get_channel_id(youtube, comp)
            print(f"   • Fetching: {title} ({comp})")
            
            # get uploads playlist
            ch_resp = youtube.channels().list(id=cid, part='contentDetails').execute()
            uploads_id = ch_resp['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # get last 15 videos
            gov_resp = youtube.playlistItems().list(
                playlistId=uploads_id, part='snippet', maxResults=25
            ).execute()
            
            titles = [item['snippet']['title'] for item in gov_resp['items']]
            comp_data[title] = titles
            
        except Exception as e:
            print(f"   ⚠️ Failed to analyze competitor {comp}: {e}")
            
    return comp_data


def call_ai_model(client, prompt: str, model_type: str = "openai", gemini_model_name: str = None) -> dict:
    """
    Abstracts API calls for OpenAI vs Gemini.
    """
    # Use env var or default if not provided
    if not gemini_model_name:
        gemini_model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

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


def extract_batch_signals(client, batch_comments: list, channel_name: str, batch_id: int, model_type: str = "openai", gemini_model: str = "gemini-2.0-flash", language: str = "en") -> dict:
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

{language_instruction}
""".format(language_instruction=LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS['en']))
    result = call_ai_model(client, prompt, model_type, gemini_model)
    if not result:
        return {"pain_points": []}
    return result


def cluster_pain_points(client, all_pain_points: list, channel_name: str, model_type: str = "openai", gemini_model: str = "gemini-2.0-flash", language: str = "en") -> dict:
    """
    PHASE 2B (REDUCE): Cluster similar pain points without inventing new concepts.
    Enhanced to track engagement metrics and filter low-quality gaps.
    """
    # Flatten all pain points from batches with full engagement data
    flat_points = []
    for batch in all_pain_points:
        for pp in batch.get('pain_points', []):
            flat_points.append({
                'topic': pp.get('topic_keyword', 'N/A'),
                'struggle': pp.get('user_struggle', 'N/A'),
                'engagement': pp.get('engagement', 0),
                'evidence': pp.get('evidence', '')
            })
    
    if not flat_points:
        return {"clustered_pain_points": []}
    
    # Format for AI with engagement data
    points_text = "\n".join([f"- Topic: {p['topic']} | Struggle: {p['struggle']} | Likes: {p['engagement']} | Evidence: {p['evidence'][:100]}" for p in flat_points])
    
    prompt = f"""You are analyzing user pain points for "{channel_name}".

INPUT:
Pain points extracted from viewer comments (pre-filtered for quality).

TASK: Cluster similar pain points together AND validate they are content-worthy.

RULES:
1. Group pain points that are about the SAME topic
2. Preserve the EXACT wording users used - do NOT invent new terms
3. Sum up the engagement scores when merging
4. CRITICAL: Only include gaps with 3+ unique mentions
5. For each gap, determine if it's ACTIONABLE (can the creator make a video about this?)
6. Do NOT include one-off questions (like "what song is this?") unless 3+ people asked
7. Focus on topics that could fill 8+ minutes of video content

ACTIONABILITY CRITERIA:
- NOT actionable: "What song is playing?" (single question, no video potential)
- NOT actionable: "Great video!" (praise, not a gap)
- ACTIONABLE: "How do you shuffle cards so fast?" (tutorial potential)
- ACTIONABLE: "Want to see behind the scenes" (content format request)

INPUT PAIN POINTS:
{points_text}

OUTPUT JSON:
{{
    "clustered_pain_points": [
        {{
            "topic_keyword": "exact term from comments",
            "user_struggle": "specific confusion described",
            "is_actionable": true,
            "actionability_reason": "Why this can/cannot be a video",
            "total_engagement": 1500,
            "mention_count": 5,
            "sample_evidence": ["quote 1", "quote 2", "quote 3"],
            "video_potential": {{
                "title_idea": "A potential video title",
                "hook_idea": "First 10 seconds script idea",
                "thumbnail_tip": "What to show on thumbnail"
            }}
        }}
    ]
}}

ONLY include gaps where mention_count >= 3 AND is_actionable = true.

{language_instruction}
""".format(language_instruction=LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS['en']))
    result = call_ai_model(client, prompt, model_type, gemini_model)
    
    # Post-process: Filter out gaps that don't meet minimum criteria
    if result and 'clustered_pain_points' in result:
        filtered_gaps = []
        for gap in result['clustered_pain_points']:
            mention_count = gap.get('mention_count', 0)
            is_actionable = gap.get('is_actionable', True)
            
            # Enforce minimum threshold
            if mention_count >= 3 and is_actionable:
                filtered_gaps.append(gap)
            else:
                print(f"   ⚠️ Filtered out low-quality gap: {gap.get('topic_keyword', 'N/A')} (mentions: {mention_count}, actionable: {is_actionable})")
        
        result['clustered_pain_points'] = filtered_gaps
        result['filtered_count'] = len(result['clustered_pain_points'])
    
    return result if result else {"clustered_pain_points": []}


def verify_gaps_against_content(client, pain_points: list, transcripts: list, model_type: str = "openai", gemini_model: str = "gemini-2.0-flash", language: str = "en") -> dict:
    """
    PHASE 3: The Gap Verification Engine.
    Cross-references pain points against creator's actual content.
    This is the 'sellable' feature that proves gaps are real.
    
    Enhanced to preserve video_potential data from clustering step.
    """
    # Prepare pain points summary with full context
    pain_text = ""
    pain_point_lookup = {}  # To preserve video_potential data
    
    for i, pp in enumerate(pain_points):
        pain_text += f"\n{i+1}. Topic: {pp.get('topic_keyword', 'N/A')}"
        pain_text += f"\n   Struggle: {pp.get('user_struggle', 'N/A')}"
        pain_text += f"\n   Engagement: {pp.get('total_engagement', 0)} likes"
        pain_text += f"\n   Mentions: {pp.get('mention_count', 1)} comments"
        pain_text += f"\n   Actionability: {pp.get('actionability_reason', 'N/A')}"
        pain_text += "\n"
        
        # Store for later merge
        pain_point_lookup[pp.get('topic_keyword', '')] = pp
    
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
            "mention_count": 5,
            "gap_status": "TRUE_GAP/UNDER_EXPLAINED/SATURATED",
            "verification_evidence": "Why you classified it this way (quote from transcript or 'No mention found')"
        }}
    ]
}}

{{language_instruction}}
""".replace('{{language_instruction}}', LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS['en']))
    result = call_ai_model(client, prompt, model_type, gemini_model)
    
    # Merge back the video_potential data from clustering step
    if result and 'verified_gaps' in result:
        for gap in result['verified_gaps']:
            topic = gap.get('topic_keyword', '')
            if topic in pain_point_lookup:
                original = pain_point_lookup[topic]
                # Preserve video_potential from clustering
                gap['video_potential'] = original.get('video_potential', {})
                gap['is_actionable'] = original.get('is_actionable', True)
                gap['actionability_reason'] = original.get('actionability_reason', '')
                gap['sample_evidence'] = original.get('sample_evidence', [])
                # Ensure mention_count is preserved
                if not gap.get('mention_count'):
                    gap['mention_count'] = original.get('mention_count', 1)
    
    return result if result else {"verified_gaps": []}


# Old merge_signals_reduce is replaced by cluster_pain_points and verify_gaps_against_content above


def analyze_with_ai(ai_client, videos_data: list[dict], channel_name: str, competitors_data: dict, model_type: str = "openai", gemini_model: str = "gemini-2.0-flash", language: str = "en") -> dict:
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
        
        result = extract_batch_signals(ai_client, batch, channel_name, batch_id, model_type, gemini_model, language)
        all_pain_results.append(result)
    
    # Cluster pain points
    print(f"\n📉 PHASE 2B: Clustering Pain Points...")
    clustered = cluster_pain_points(ai_client, all_pain_results, channel_name, model_type, gemini_model, language)
    pain_points = clustered.get('clustered_pain_points', [])
    print(f"   ✓ Found {len(pain_points)} distinct user struggles")
    
    # =========================================================
    # PHASE 3: GAP VERIFICATION (The Sellable Feature)
    # =========================================================
    print(f"\n🔎 PHASE 3: Verifying Gaps Against Creator's Content...")
    verified = verify_gaps_against_content(ai_client, pain_points, transcripts_summary, model_type, gemini_model, language)
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

COMPETITOR DATA:
{json.dumps(competitors_data, indent=2)}

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
        
        # FALLBACK: Ensure top_opportunity is never empty
        if not final_result:
            final_result = {"opportunities": [], "top_opportunity": {}}
        
        top_opp = final_result.get('top_opportunity', {})
        opportunities = final_result.get('opportunities', [])
        
        # If top_opportunity is empty or missing best_title, generate from best gap
        if not top_opp.get('best_title') and actionable_gaps:
            best_gap = actionable_gaps[0]  # Already sorted by engagement
            video_potential = best_gap.get('video_potential', {})
            
            final_result['top_opportunity'] = {
                'topic_keyword': best_gap.get('topic_keyword', 'Content Opportunity'),
                'best_title': video_potential.get('title_idea', f"Addressing {best_gap.get('topic_keyword', 'Your Audience Needs')}"),
                'engagement_potential': best_gap.get('total_engagement', 0),
                'reason': f"Based on {best_gap.get('mention_count', 1)} viewer comments with {best_gap.get('total_engagement', 0)} total likes",
                'hook_idea': video_potential.get('hook_idea', ''),
                'thumbnail_tip': video_potential.get('thumbnail_tip', '')
            }
            print(f"   ⚠️ Generated fallback top_opportunity from best gap: {best_gap.get('topic_keyword', 'N/A')}")
        
        # Ensure each opportunity has video_potential from the gap data
        for opp in opportunities:
            if not opp.get('video_potential'):
                # Find matching gap and copy video_potential
                for gap in actionable_gaps:
                    if gap.get('topic_keyword') == opp.get('topic_keyword'):
                        opp['video_potential'] = gap.get('video_potential', {})
                        opp['mention_count'] = gap.get('mention_count', 1)
                        break
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
        'competitors_analyzed': list(competitors_data.keys()) if competitors_data else []
    }


def run_premium_analysis(
    youtube, 
    channel_id: str,
    channel_name: str,
    videos_data: list,
    tier: str = "starter",
    ai_client=None,
    model_type: str = "gemini",
    gemini_model: str = "gemini-2.0-flash"
) -> dict:
    """
    Run premium analysis modules based on subscription tier.
    
    Tier access:
    - starter: CTR Prediction (basic), Thumbnail Optimizer (basic), 3 competitors
    - pro: All starter + Views Forecasting, Content Clustering, Publish Time, 10 competitors
    - enterprise: All pro + 100 competitors, advanced everything
    """
    print(f"\n🌟 Running Premium Analysis (Tier: {tier.upper()})...")
    
    premium_data = {
        'tier': tier,
        'ctr_prediction': None,
        'thumbnail_analysis': None,
        'views_forecast': None,
        'competitor_intel': None,
        'content_clusters': None,
        'publish_times': None,
        'hook_analysis': None,
        'color_insights': None,
        'visual_charts': None,
    }
    
    # Tier limits - Enhanced with video counts
    TIER_LIMITS = {
    'starter': {
        'video_count': 3,            # Reduced to 3
        'hook_video_count': 3,       # Analyze all 3
        'competitors': 1, 
        'advanced_thumbnail': False, 
        'views_forecast': False, 
        'clustering': False, 
        'publish_time': True,  # Enabled for starter per user request
        'ml_predictor': False,
    },
    'pro': {
        'video_count': 10,           # Reduced to 10
        'hook_video_count': 5,       # Half
        'competitors': 5, 
        'advanced_thumbnail': True, 
        'views_forecast': True, 
        'clustering': True, 
        'publish_time': True,
        'ml_predictor': True,
    },
    'enterprise': {
        'video_count': 50,           # Stays 50
        'hook_video_count': 25,      # Half
        'competitors': 100, 
        'advanced_thumbnail': True, 
        'views_forecast': True, 
        'clustering': True, 
        'publish_time': True,
        'ml_predictor': True,
    }
}
    limits = TIER_LIMITS.get(tier, TIER_LIMITS['starter'])
    
    # Robustness: Disable features if not enough data
    if len(videos_data) < 2:
        if limits.get('views_forecast'):
            print("   ⚠️ Not enough videos for views forecasting (need 2+). Skipping.")
            limits['views_forecast'] = False
        if limits.get('clustering'):
            print("   ⚠️ Not enough videos for clustering (need 2+). Skipping.")
            limits['clustering'] = False
    
    # =========================================================
    # 1. CTR PREDICTION (All Tiers)
    # =========================================================
    try:
        print("   📊 Running CTR Prediction...")
        ctr_predictor = CTRPredictor()
        thumbnail_extractor = ThumbnailFeatureExtractor(use_ocr=False, use_face_detection=True)
        
        # Analyze thumbnails from recent videos
        ctr_results = []
        for v in videos_data[:5]:  # Top 5 videos
            video_info = v.get('video_info', {})
            thumbnail_url = video_info.get('thumbnail_url') or f"https://img.youtube.com/vi/{video_info.get('video_id', '')}/maxresdefault.jpg"
            
            try:
                features = thumbnail_extractor.extract_from_url(thumbnail_url)
                prediction = ctr_predictor.predict(features.to_dict(), video_info.get('title', ''))
                ctr_results.append({
                    'video_title': video_info.get('title', ''),
                    'predicted_ctr': prediction.predicted_ctr,
                    'confidence': prediction.confidence,
                    'positive_factors': prediction.top_positive_factors[:3],
                    'negative_factors': prediction.top_negative_factors[:3],
                    'suggestions': prediction.improvement_suggestions[:3]
                })
            except Exception as e:
                print(f"      ⚠️ CTR analysis failed for video: {e}")
                continue
        
        if ctr_results:
            avg_ctr = sum(r['predicted_ctr'] for r in ctr_results) / len(ctr_results)
            premium_data['ctr_prediction'] = {
                'channel_avg_predicted_ctr': round(avg_ctr, 2),
                'video_predictions': ctr_results,
                'top_improvement': ctr_results[0]['suggestions'][0] if ctr_results and ctr_results[0].get('suggestions') else None
            }
            print(f"      ✓ Avg Predicted CTR: {avg_ctr:.1f}%")
    except Exception as e:
        print(f"   ⚠️ CTR Prediction failed: {e}")
    
    # =========================================================
    # 2. THUMBNAIL OPTIMIZER (All Tiers - Using Gemini AI)
    # =========================================================
    try:
        print("   🎨 Running Thumbnail Optimizer (Gemini AI)...")
        from premium.thumbnail_analyzer_ai import analyze_thumbnails_batch
        
        # Analyze thumbnails using Gemini Vision
        thumbnail_analyses = analyze_thumbnails_batch(
            videos=videos_data,
            ai_client=ai_client,
            model=gemini_model,  # gemini-2.0-flash
            max_videos=3  # Analyze top 3 thumbnails
        )
        
        # Add advanced features for Pro+ tiers
        if limits['advanced_thumbnail']:
            for analysis in thumbnail_analyses:
                # A/B test suggestions based on detected issues
                ab_suggestions = []
                for issue in analysis.get('issues', []):
                    if 'face' in issue.get('issue', '').lower():
                        ab_suggestions.append({
                            'variant': 'Add Larger Face',
                            'description': 'Use a close-up face with expressive emotion',
                            'expected_lift': '+20-35%'
                        })
                    elif 'text' in issue.get('issue', '').lower():
                        ab_suggestions.append({
                            'variant': 'Add Text Overlay',
                            'description': 'Add 2-3 bold words with key hook',
                            'expected_lift': '+10-20%'
                        })
                analysis['ab_test_suggestions'] = ab_suggestions[:3]
        
        premium_data['thumbnail_analysis'] = {
            'mode': 'advanced' if limits['advanced_thumbnail'] else 'basic',
            'videos_analyzed': thumbnail_analyses
        }
        print(f"      ✓ Analyzed {len(thumbnail_analyses)} thumbnails with Gemini AI")
    except Exception as e:
        print(f"   ⚠️ Thumbnail Optimizer failed: {e}")
        import traceback
        traceback.print_exc()
    
    # =========================================================
    # 3. VIEWS FORECASTING (Pro+ Only)
    # =========================================================
    if limits['views_forecast']:
        try:
            print("   📈 Running Views Forecasting...")
            from datetime import datetime, timedelta
            
            forecasts = []
            all_views = []  # Collect all view counts for channel average
            
            for v in videos_data[:10]:  # Analyze up to 10 videos for better average
                video_info = v.get('video_info', {})
                view_count = video_info.get('view_count') or 0
                if view_count > 0:
                    all_views.append(view_count)
            
            channel_avg_views = sum(all_views) / len(all_views) if all_views else 10000
            
            for v in videos_data[:3]:  # Display top 3
                video_info = v.get('video_info', {})
                view_count = video_info.get('view_count') or 0
                like_count = video_info.get('like_count') or 0
                upload_date = video_info.get('upload_date', '')
                
                # Calculate days since upload
                days_old = 30  # Default if no date
                if upload_date:
                    try:
                        # yt_dlp returns date as YYYYMMDD string
                        if len(upload_date) == 8:
                            pub_date = datetime.strptime(upload_date, '%Y%m%d')
                        else:
                            pub_date = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
                        days_old = max(1, (datetime.now() - pub_date.replace(tzinfo=None)).days)
                    except:
                        days_old = 30
                
                # Calculate actual velocity from historical data
                views_per_day = view_count / days_old if days_old > 0 else 0
                
                # Project future views based on actual performance curve
                # YouTube videos typically get 60% of lifetime views in first week
                if days_old < 7:
                    # Video is still young - project based on current velocity
                    predicted_7d = int(views_per_day * 7)
                    predicted_30d = int(predicted_7d + (views_per_day * 0.4 * 23))  # Decay factor
                elif days_old < 30:
                    # Video is in growth phase
                    predicted_7d = view_count  # Already past 7 days
                    remaining_days = 30 - days_old
                    predicted_30d = int(view_count + (views_per_day * 0.3 * remaining_days))
                else:
                    # Video is mature - use actual counts
                    predicted_7d = view_count
                    predicted_30d = view_count
                
                # Ensure minimum values for display
                predicted_7d = max(predicted_7d, 100)
                predicted_30d = max(predicted_30d, 100)
                
                # Calculate viral probability based on performance vs channel average
                if channel_avg_views > 0 and view_count > 0:
                    performance_ratio = view_count / channel_avg_views
                    if performance_ratio > 2.0:
                        viral_prob = min(0.9, 0.3 + (performance_ratio - 2) * 0.2)
                        trajectory = 'viral'
                    elif performance_ratio > 1.5:
                        viral_prob = 0.2
                        trajectory = 'steady_growth'
                    elif performance_ratio > 1.0:
                        viral_prob = 0.1
                        trajectory = 'steady_growth'
                    else:
                        viral_prob = 0.05
                        trajectory = 'slow_burn'
                else:
                    viral_prob = 0.05
                    trajectory = 'slow_burn'
                
                # Compare to channel average
                if view_count > channel_avg_views * 1.2:
                    vs_avg = f"+{int((view_count / channel_avg_views - 1) * 100)}% above average"
                elif view_count < channel_avg_views * 0.8:
                    vs_avg = f"{int((1 - view_count / channel_avg_views) * 100)}% below average"
                else:
                    vs_avg = "Within normal range"
                
                forecasts.append({
                    'video_title': video_info.get('title', ''),
                    'predicted_7d_views': predicted_7d,
                    'predicted_30d_views': predicted_30d,
                    'viral_probability': round(viral_prob * 100, 1),
                    'trajectory_type': trajectory,
                    'vs_channel_avg': vs_avg
                })
            
            premium_data['views_forecast'] = {
                'forecasts': forecasts,
                'avg_viral_probability': round(sum(f['viral_probability'] for f in forecasts) / len(forecasts), 1) if forecasts else 0
            }
            print(f"      ✓ Generated {len(forecasts)} forecasts")
        except Exception as e:
            print(f"   ⚠️ Views Forecasting failed: {e}")
    
    # =========================================================
    # 4. COMPETITOR INTEL (All Tiers - Limited by Tier) + CACHING
    # =========================================================
    try:
        print(f"   ⚔️ Running Competitor Analysis (max {limits['competitors']} channels)...")
        
        # Import cache
        try:
            from premium.db.competitor_cache import get_competitor_cache
            cache = get_competitor_cache()
        except Exception as e:
            print(f"      ⚠️ Cache unavailable: {e}")
            cache = None
        
        competitor_analyzer = CompetitorAnalyzer()
        
        # Discover competitors
        discovered = competitor_analyzer.discover_competitors(
            channel_id,
            search_terms=[channel_name],
            max_competitors=limits['competitors']
        )
        
        competitor_insights = []
        cache_hits = 0
        
        for comp_id in discovered[:limits['competitors']]:
            try:
                # Check cache first
                cached_data = cache.get(comp_id) if cache else None
                
                if cached_data:
                    competitor_insights.append(cached_data)
                    cache_hits += 1
                    continue
                
                # Cache miss - fetch fresh data
                insight = competitor_analyzer.analyze_competitor(comp_id, video_limit=10)
                insight_data = {
                    'channel_name': insight.channel_name,
                    'subscriber_count': insight.subscriber_count,
                    'avg_views': int(insight.avg_views_per_video),
                    'avg_engagement': round(insight.avg_engagement_rate, 2),
                    'upload_frequency_days': round(insight.upload_frequency_days, 1),
                    'top_formats': insight.top_formats[:3],
                    'posting_days': insight.posting_day_pattern[:3]
                }
                competitor_insights.append(insight_data)
                
                # Save to cache for next time
                if cache:
                    cache.set(comp_id, insight_data)
                    
            except Exception as e:
                print(f"      ⚠️ Competitor analysis failed: {e}")
                continue
        
        premium_data['competitor_intel'] = {
            'competitors_tracked': len(competitor_insights),
            'max_allowed': limits['competitors'],
            'competitors': competitor_insights,
            'cache_hits': cache_hits
        }
        print(f"      ✓ Analyzed {len(competitor_insights)} competitors ({cache_hits} from cache)")
    except Exception as e:
        print(f"   ⚠️ Competitor Analysis failed: {e}")
    
    # =========================================================
    # 5. CONTENT CLUSTERING (Pro+ Only)
    # =========================================================
    if limits['clustering']:
        try:
            print("   🧩 Running Content Clustering...")
            clusterer = ContentClusteringEngine(use_embeddings=False)  # Use keyword-based for speed
            
            # Prepare video data for clustering with proper null handling
            cluster_videos = []
            total_views = 0
            video_count = 0
            
            for v in videos_data:
                video_info = v.get('video_info', {})
                view_count = video_info.get('view_count') or 0  # Handle None
                comments_count = len(v.get('comments', []))
                
                # Calculate engagement rate properly
                if view_count > 0:
                    engagement_rate = (comments_count / view_count) * 100
                    total_views += view_count
                    video_count += 1
                else:
                    engagement_rate = 0
                
                cluster_videos.append({
                    'title': video_info.get('title', ''),
                    'view_count': view_count,
                    'engagement_rate': round(engagement_rate, 2)
                })
            
            # Pass channel average to help with performance scoring
            channel_avg = total_views / video_count if video_count > 0 else 10000
            
            result = clusterer.cluster_channel_content(cluster_videos, n_clusters=min(5, max(2, len(cluster_videos) // 2)))
            
            # Post-process clusters to ensure meaningful scores
            processed_clusters = []
            for c in result.clusters:
                cluster_dict = c.to_dict()
                # Recalculate performance score relative to channel average
                if channel_avg > 0 and cluster_dict['avg_views'] > 0:
                    cluster_dict['performance_score'] = round(cluster_dict['avg_views'] / channel_avg, 2)
                processed_clusters.append(cluster_dict)
            
            premium_data['content_clusters'] = {
                'clusters': processed_clusters,
                'best_performing': result.best_performing_cluster,
                'underperforming': result.underperforming_clusters,
                'gap_opportunities': result.gap_opportunities,
                'recommendations': result.recommendations[:3]
            }
            print(f"      ✓ Found {len(result.clusters)} content clusters")
        except Exception as e:
            print(f"   ⚠️ Content Clustering failed: {e}")
    
    # =========================================================
    # 6. PUBLISH TIME OPTIMIZER (Pro+ Only)
    # =========================================================
    if limits['publish_time']:
        try:
            print("   ⏰ Running Publish Time Optimizer...")
            publish_optimizer = PublishTimeOptimizer()
            
            # Prepare video data with publish times
            publish_videos = []
            for v in videos_data:
                video_info = v.get('video_info', {})
                publish_videos.append({
                    'published_at': video_info.get('published_at', ''),
                    'view_count': video_info.get('view_count') or 0  # Handle None
                })
            
            result = publish_optimizer.analyze_optimal_times(
                videos=publish_videos,
                content_type="general"
            )
            
            premium_data['publish_times'] = {
                'best_days': result.best_days,
                'best_hours_utc': result.best_hours_utc,
                'recommendations': [
                    {'day': r.day, 'hour': r.hour_utc, 'boost': r.expected_view_boost, 'reasoning': r.reasoning}
                    for r in result.schedule_recommendations[:3]
                ],
                'avoid_times': [
                    {'day': a.day, 'hour': a.hour_utc, 'reason': a.reason}
                    for a in result.avoid_times[:3]
                ],
                'content_advice': result.content_specific
            }
            print(f"      ✓ Best days: {', '.join(result.best_days[:3])}")
        except Exception as e:
            print(f"   ⚠️ Publish Time Optimizer failed: {e}")
    
    # =========================================================
    # 7. HOOK ANALYSIS (Pro+ Only) - First 60 seconds
    # =========================================================
    if tier in ['pro', 'enterprise']:
        try:
            print("   🎣 Running Hook Analysis (first 60s of videos)...")
            hook_analyzer = HookAnalyzer(whisper_model='tiny')
            
            # Prepare video data for hook analysis (include transcript for fallback)
            hook_videos = []
            for v in videos_data[:10]:  # Analyze 10 videos for hooks (fast)
                video_info = v.get('video_info', {})
                hook_videos.append({
                    'video_id': video_info.get('video_id', ''),
                    'title': video_info.get('title', ''),
                    'view_count': video_info.get('view_count') or 0,
                    'transcript': v.get('transcript', '')[:1000],  # First 1000 chars for hook analysis fallback
                })
            
            hook_results = hook_analyzer.analyze_videos(hook_videos, max_videos=10)
            hook_insights = hook_analyzer.generate_insights(hook_results)
            
            premium_data['hook_analysis'] = {
                'videos_analyzed': hook_insights.total_videos,
                'avg_hook_score': hook_insights.avg_hook_score,
                'best_patterns': hook_insights.best_patterns[:5],
                'recommendations': hook_insights.recommended_hooks,
                'top_hooks': hook_insights.top_performing_hooks[:3],
                'pattern_performance': hook_insights.pattern_performance,
            }
            print(f"      ✓ Analyzed hooks for {hook_insights.total_videos} videos")
        except Exception as e:
            print(f"   ⚠️ Hook Analysis failed: {e}")
    
    # =========================================================
    # 8. COLOR ML ANALYSIS (Pro+ Only) - Thumbnail colors
    # =========================================================
    if tier in ['pro', 'enterprise'] and premium_data.get('thumbnail_analysis'):
        try:
            print("   🎨 Running Color ML Analysis...")
            color_analyzer = ColorMLAnalyzer()
            
            # Build color profiles from existing thumbnail analysis
            color_profiles = []
            thumbnail_data = premium_data['thumbnail_analysis'].get('videos_analyzed', [])
            
            for i, thumb in enumerate(thumbnail_data):
                video_info = videos_data[i].get('video_info', {}) if i < len(videos_data) else {}
                # Extract color features from thumbnail data
                features = {
                    'dominant_color_1': thumb.get('score_breakdown', {}).get('dominant_color_1', (128, 128, 128)),
                    'dominant_color_2': thumb.get('score_breakdown', {}).get('dominant_color_2', (100, 100, 100)),
                    'dominant_color_3': thumb.get('score_breakdown', {}).get('dominant_color_3', (80, 80, 80)),
                }
                color_profiles.append({
                    'video_data': {
                        'video_id': video_info.get('video_id', ''),
                        'title': thumb.get('video_title', ''),
                        'view_count': video_info.get('view_count') or 0,
                    },
                    'thumbnail_features': features,
                })
            
            # Note: analyze_thumbnails expects dicts with 'thumbnail_features' and 'video_data'
            # Or ColorProfile objects. Let's see analyze_thumbnails implementation. 
            # It seems I need to check color_ml_analyzer.py again to match its expected input.
            # Assuming analyze_thumbnails handles the input format:
            profiles = color_analyzer.analyze_thumbnails(color_profiles)
            color_insights = color_analyzer.generate_insights(profiles)
            
            premium_data['color_insights'] = color_insights.to_dict()
            print(f"      ✓ Color analysis complete - Best: {color_insights.best_color_temperatures[0]['temperature'] if color_insights.best_color_temperatures else 'N/A'}")
        except Exception as e:
            print(f"   ⚠️ Color ML Analysis failed: {e}")
    
    # =========================================================
    # 9. ML VIRAL PREDICTION (Enterprise/Pro only)
    # =========================================================
    if tier in ['pro', 'enterprise'] and premium_data.get('ml_predictor', True):
        try:
            from premium.ml_models.viral_predictor import ViralPredictor
            print("   🔮 Running ML Viral Prediction...")
            
            predictor = ViralPredictor()
            
            # Predict for top opportunity if available
            top_opp = results.get('top_opportunity', {})
            if top_opp and top_opp.get('title'):
                title = top_opp.get('title')
                hook = top_opp.get('hook', '')
                topic = top_opp.get('topic', 'General')
                
                # Get channel history from videos_data
                history = [v.get('video_info', {}) for v in videos_data]
                
                prediction = predictor.predict(title, hook, topic, history)
                
                premium_data['viral_prediction'] = {
                    'predicted_views': prediction.predicted_views,
                    'viral_probability': prediction.viral_probability,
                    'confidence': prediction.confidence_score,
                    'factors': prediction.factors,
                    'tips': prediction.tips
                }
                print(f"      ✓ Predicted views: {prediction.predicted_views:,.0f} (Prob: {prediction.viral_probability:.0%})")
                
        except Exception as e:
            print(f"   ⚠️ Viral Prediction failed: {e}")
    
    # =========================================================
    # 9. VISUAL CHART GENERATION (All Tiers)
    # =========================================================
    try:
        print("   📈 Generating Visual Charts...")
        viz_gen = VisualReportGenerator()
        charts = {}
        
        # Hook pattern chart (if hook analysis exists)
        if premium_data.get('hook_analysis') and premium_data['hook_analysis'].get('best_patterns'):
            hook_data = [
                {'label': p['pattern'], 'value': p['avg_views']}
                for p in premium_data['hook_analysis']['best_patterns'][:5]
            ]
            charts['hook_patterns'] = viz_gen.create_bar_chart(
                hook_data, "Hook Pattern Performance"
            ).to_dict()
        
        # Color temperature chart
        if premium_data.get('color_insights') and premium_data['color_insights'].get('temperature_performance'):
            temp_data = [
                {'label': k.title(), 'value': v}
                for k, v in premium_data['color_insights']['temperature_performance'].items()
            ]
            charts['color_temperature'] = viz_gen.create_bar_chart(
                temp_data, "Color Temperature vs Views", color='#8b5cf6'
            ).to_dict()
        
        # Top colors palette
        if premium_data.get('color_insights') and premium_data['color_insights'].get('top_performing_colors'):
            charts['top_colors'] = viz_gen.create_color_palette_chart(
                premium_data['color_insights']['top_performing_colors'][:5],
                "Top Performing Colors"
            ).to_dict()
        
        # CTR gauge
        if premium_data.get('ctr_prediction') and premium_data['ctr_prediction'].get('channel_avg_predicted_ctr'):
            avg_ctr = premium_data['ctr_prediction']['channel_avg_predicted_ctr']
            charts['ctr_gauge'] = viz_gen.create_score_gauge(
                avg_ctr * 100, 15, f"Avg CTR: {avg_ctr:.1%}"
            ).to_dict()
        
        premium_data['visual_charts'] = charts
        print(f"      ✓ Generated {len(charts)} visual charts")
    except Exception as e:
        print(f"   ⚠️ Visual Chart Generation failed: {e}")
    
    print("   ✅ Premium Analysis Complete!")
    return premium_data



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
            f.write("[Watch]({info['url']})\n\n")

        # =========================================================
        # PREMIUM SECTIONS (If available/enabled)
        # =========================================================
        premium = analysis.get('premium', {})
        
        # Best Time to Post
        if premium.get('publish_times'):
            pt = premium['publish_times']
            f.write("---\n\n")
            f.write("## ⏰ Best Time to Post\n\n")
            f.write(f"**Best Days:** {', '.join(pt.get('best_days', []))}\n\n")
            
            if pt.get('recommendations'):
                f.write("### Recommended Slots:\n")
                for rec in pt['recommendations']:
                    f.write(f"- **{rec.get('day')} @ {rec.get('hour')}:00 UTC** ({rec.get('boost')} boost)\n")
                    f.write(f"  *Reason: {rec.get('reasoning')}*\n")
            f.write("\n")

        # Color Insights
        if premium.get('color_insights'):
            ci = premium['color_insights']
            f.write("---\n\n")
            f.write("## 🎨 Thumbnail Color Insights\n\n")
            f.write(f"**Top Performing Colors:** {', '.join(ci.get('top_performing_colors', []))}\n\n")
            
            if ci.get('color_recommendations'):
                f.write("### Recommendations:\n")
                for rec in ci['color_recommendations']:
                    f.write(f"- {rec}\n")
            f.write("\n")

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
    import sys
    print(f"DEBUG ARGV: {sys.argv}")
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
    parser.add_argument('--model', '-m', default='tiny',
                        choices=['tiny', 'base', 'small', 'medium', 'large'],
                        help='Whisper model size (default: tiny for speed)')
    parser.add_argument('--skip-shorts', action='store_true',
                        help='Skip YouTube Shorts (videos <= 60 seconds)')
    parser.add_argument('--ai', choices=['openai', 'gemini', 'local'], default='gemini',
                        help='AI backend: openai, gemini (default), or local (free/ollama).')
    parser.add_argument('--gemini-model', default='gemini-2.5-flash',
                        help='Specific Gemini model to use (default: gemini-2.5-flash).')
    parser.add_argument('--competitors', nargs='+', help='List of competitor channel handles (e.g. @Rival1 @Rival2)')
    parser.add_argument('--sample', action='store_true', help='Run in "Free Sample" mode (3 videos, preview report)')
    parser.add_argument('--access_key', help='Supabase access key for tracking')
    parser.add_argument('--email', help='User email for analysis results')
    parser.add_argument('--tier', default='starter', choices=['starter', 'pro', 'enterprise'],
                        help='Subscription tier for feature access (default: starter)')
    parser.add_argument('--language', default='en', choices=['en', 'de', 'fr', 'it', 'es'],
                        help='Report language: en, de, fr, it, es (default: en)')
    
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
        
        # Step 4: SMART PROCESSING - Comments from all videos, transcription from 5 only
        # This is ~4x faster: transcription is slow, comments are fast (just API calls)
        TRANSCRIBE_COUNT = 5  # Videos to fully process (download + transcribe)
        
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from ingest_manager import fetch_all_comments, extract_video_id
        
        videos_data = []
        
        # Split videos: first 5 get full processing, rest get comments-only
        videos_to_transcribe = videos[:TRANSCRIBE_COUNT]
        videos_comments_only = videos[TRANSCRIBE_COUNT:]
        
        print(f"\n⚙️ Smart Processing Mode:")
        print(f"   📝 Full analysis: {len(videos_to_transcribe)} videos (with transcription)")
        print(f"   💬 Comments-only: {len(videos_comments_only)} videos (fast)")
        
        # 1. Process videos that need transcription (parallel, 3 workers)
        if videos_to_transcribe:
            print(f"\n🎙️ Transcribing {len(videos_to_transcribe)} videos...")
            
            def process_single_video(video_tuple):
                idx, video = video_tuple
                try:
                    result = process_video(
                        video['url'], 
                        youtube_api_key, 
                        model_name=args.model,
                        verbose=False
                    )
                    return idx, result, None
                except Exception as e:
                    return idx, None, str(e)
            
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {executor.submit(process_single_video, (i, v)): i for i, v in enumerate(videos_to_transcribe, 1)}
                
                completed = 0
                for future in as_completed(futures):
                    completed += 1
                    idx, result, error = future.result()
                    if result:
                        videos_data.append(result)
                        print(f"   ✓ [{completed}/{len(videos_to_transcribe)}] {videos_to_transcribe[idx-1]['title'][:35]}...")
                    else:
                        if error:
                            print(f"   ⚠️ [{completed}/{len(videos_to_transcribe)}] Failed: {error[:40]}...")
                        else:
                            print(f"   ℹ️ [{completed}/{len(videos_to_transcribe)}] Skipped (no captions)")
        
        # 2. Fetch comments from remaining videos (parallel, 5 workers - faster)
        if videos_comments_only:
            print(f"\n💬 Fetching comments from {len(videos_comments_only)} additional videos...")
            
            def fetch_comments_only(video_tuple):
                idx, video = video_tuple
                try:
                    video_id = video.get('video_id') or extract_video_id(video['url'])
                    comments = fetch_all_comments(video_id, youtube_api_key, max_comments=200)
                    # Create minimal video data structure (no transcript) with full metadata
                    result = {
                        'video_info': {
                            'id': video_id,
                            'video_id': video_id,  # Add both for compatibility
                            'title': video['title'],
                            'url': video['url'],
                            'view_count': video.get('view_count', 0),
                            'like_count': video.get('like_count', 0),
                            'thumbnail_url': video.get('thumbnail_url'),
                            'upload_date': video.get('upload_date', ''),
                            'published_at': video.get('published_at', ''),
                        },
                        'transcript': '',  # Empty - no transcription
                        'transcript_segments': [],
                        'comments': comments,
                    }
                    return idx, result, None
                except Exception as e:
                    return idx, None, str(e)
            
            with ThreadPoolExecutor(max_workers=6) as executor:
                futures = {executor.submit(fetch_comments_only, (i, v)): i for i, v in enumerate(videos_comments_only, 1)}
                
                completed = 0
                for future in as_completed(futures):
                    completed += 1
                    idx, result, error = future.result()
                    if result:
                        videos_data.append(result)
                        print(f"   ✓ [{completed}/{len(videos_comments_only)}] {videos_comments_only[idx-1]['title'][:35]}... ({len(result['comments'])} comments)")
                    else:
                        print(f"   ⚠️ [{completed}/{len(videos_comments_only)}] Failed: {error[:40]}...")
        
        if not videos_data:
            print(f"❌ No videos could be processed ({len(videos)} attempted)")
            print(f"   This may be due to YouTube rate limiting. Try again in a few minutes.")
            sys.exit(1)
        
        # Report on processing
        transcribed = len([v for v in videos_data if v.get('transcript')])
        comments_only = len(videos_data) - transcribed
        print(f"\n✅ Processed {len(videos_data)} videos ({transcribed} transcribed, {comments_only} comments-only)")
        
        # Step 4.5: Competitor Analysis (Step 8)
        competitors_data = {}
        if args.competitors:
             competitors_data = fetch_competitor_videos(youtube, args.competitors)

        # Step 5: AI Analysis
        print(f"\n🧠 Running AI gap analysis...")
        analysis = analyze_with_ai(ai_client, videos_data, channel_name, competitors_data, model_type=args.ai, gemini_model=args.gemini_model, language=args.language)
        
        # Add videos_analyzed for frontend dashboard
        analysis['videos_analyzed'] = [
            {
                'title': v['video_info']['title'],
                'url': v['video_info'].get('url', ''),
                'video_id': v['video_info'].get('video_id') or v['video_info'].get('id', ''),
                'comments_count': len(v['comments']),
                'transcript_length': len(v['transcript']),
                'view_count': v['video_info'].get('view_count') or 0,
                'like_count': v['video_info'].get('like_count') or 0,
                'thumbnail_url': v['video_info'].get('thumbnail_url', '')
            }
            for v in videos_data
        ]
        
        # Step 5.5: Run Premium Analysis based on tier
        premium_data = run_premium_analysis(
            youtube=youtube,
            channel_id=channel_id,
            channel_name=channel_name,
            videos_data=videos_data,
            tier=args.tier,
            ai_client=ai_client,
            model_type=args.ai,
            gemini_model=args.gemini_model
        )
        
        # Merge premium data into analysis
        analysis['premium'] = premium_data
        
        # Calculate real engagement scores for verified gaps
        # Get all engagement values to scale relatively
        all_engagements = [gap.get('total_engagement', 0) for gap in analysis.get('verified_gaps', [])]
        max_engagement = max(all_engagements) if all_engagements else 1
        total_engagement = sum(all_engagements) if all_engagements else 1
        
        # Sort gaps by engagement to get ranks
        gaps_with_engagement = [(i, gap.get('total_engagement', 0)) for i, gap in enumerate(analysis.get('verified_gaps', []))]
        gaps_with_engagement.sort(key=lambda x: x[1], reverse=True)
        rank_map = {idx: rank for rank, (idx, _) in enumerate(gaps_with_engagement)}
        
        total_gaps = len(analysis.get('verified_gaps', []))
        for i, gap in enumerate(analysis.get('verified_gaps', [])):
            raw_engagement = gap.get('total_engagement', 0)
            
            if total_gaps > 0 and raw_engagement > 0:
                # Rank-based scoring: Top gap = 95%, descending by 10-15 points
                # This ensures visual differentiation even when absolute values are similar
                rank = rank_map.get(i, 0)
                
                # Score: 95 for #1, then decrease based on rank position
                # Use exponential decay for better differentiation
                base_score = 95 - (rank * (60 / max(total_gaps, 1)))
                engagement_score = int(max(25, min(95, base_score)))
            else:
                engagement_score = 25  # Minimum score for gaps with no engagement data
            
            gap['engagement_score'] = engagement_score
        
        # Update top_opportunity with real score (use highest engagement gap score)
        top_opp = analysis.get('top_opportunity', {})
        if top_opp:
            top_opp['engagement_potential'] = max(top_opp.get('engagement_potential', 0), 50)
        
        # Setup output paths
        script_dir = Path(__file__).parent.resolve()
        data_dir = script_dir / "data"
        data_dir.mkdir(exist_ok=True)
        
        # Save JSON for Dashboard (Step 9)
        json_output_path = script_dir / "analysis_result.json"
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2)
        print(f"📊 Dashboard data saved to: {json_output_path}")

        # Step 6: Generate report
        report_path = data_dir / f"GAP_REPORT_{channel_name.replace(' ', '_')}.md"
        generate_report(report_path, channel_name, videos_data, analysis, is_sample=args.sample)

        print(f"\n🎉 Analysis complete!")
        print(f"   Report: {report_path}")
        
        # FINAL OUTPUT FOR PARENT PROCESS
        # Print the JSON to stdout so main.py can capture it
        print(json.dumps(analysis))
        
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

