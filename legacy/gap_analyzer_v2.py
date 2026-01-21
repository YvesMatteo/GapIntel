#!/usr/bin/env python3
"""
GapIntel v2 - YouTube Intelligence Engine

Advanced content gap analysis with ML thumbnail analysis, real-time market 
intelligence, and weighted viral scoring.

New $79 Premium Tier Features:
- ML Vision Analysis (thumbnail performance correlation)
- Google Trends Integration (momentum classification)
- Dynamic Niche Explorer (live competitor discovery)
- Weighted Viral Priority Score (1-100)
- 5 Video Packages with thumbnail concepts

Usage:
    python gap_analyzer_v2.py @TJRTrades --videos 15 --tier premium
    python gap_analyzer_v2.py @ChannelHandle --videos 10 --tier basic
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from googleapiclient.discovery import build

# Import Gemini for AI processing
import google.generativeai as genai

# Import GapIntel modules
from gap_analyzer import (
    get_channel_id, get_uploads_playlist_id, get_latest_videos,
    filter_high_signal_comments, extract_batch_signals, cluster_pain_points,
    verify_gaps_against_content, call_ai_model
)
from ingest_manager import process_video
from vision_analyzer import analyze_channel_thumbnails, generate_thumbnail_recommendation
from market_intel import analyze_market_trends, explore_niche
from scoring_engine import score_gap_opportunities, ScoreCalculator


# Tier configurations
TIER_CONFIG = {
    "basic": {
        "price": 49,
        "videos": 15,
        "comments": 200,
        "vision_analysis": False,
        "niche_explorer": False,
        "video_packages": 3
    },
    "premium": {
        "price": 79,
        "videos": 50,
        "comments": 500,
        "vision_analysis": True,
        "niche_explorer": True,
        "video_packages": 5
    }
}


def run_v2_analysis(
    channel_handle: str,
    num_videos: int = 15,
    tier: str = "premium",
    niche_category: str = "finance"
) -> dict:
    """
    Run the complete GapIntel v2 analysis pipeline.
    
    Args:
        channel_handle: YouTube channel handle (e.g., @TJRTrades)
        num_videos: Number of videos to analyze
        tier: Pricing tier (basic or premium)
        niche_category: Category for niche explorer (finance, trading, etc.)
    
    Returns:
        Complete analysis result dict
    
    Note: Always uses Gemini 2.5 Flash for AI and tiny Whisper for transcription.
    """
    config = TIER_CONFIG.get(tier, TIER_CONFIG["premium"])
    num_videos = min(num_videos, config["videos"])
    
    # Initialize APIs
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY not found in environment")
    
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    # Initialize Gemini 2.5 Flash
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY not found in environment")
    genai.configure(api_key=gemini_api_key)
    ai_client = genai  # Pass the genai module as client
    model_type = "gemini"
    gemini_model = "gemini-2.5-flash-preview-05-20"
    
    print(f"\n{'='*60}")
    print(f"🎯 GapIntel v2 - {tier.upper()} Tier Analysis")
    print(f"{'='*60}")
    print(f"Channel: {channel_handle}")
    print(f"Videos: {num_videos}")
    print(f"Tier: {tier.upper()} (${config['price']})")
    print(f"{'='*60}\n")
    
    # Step 1: Get channel info
    print("📡 Step 1: Fetching channel data...")
    channel_id, channel_name = get_channel_id(youtube, channel_handle)
    uploads_id = get_uploads_playlist_id(youtube, channel_id)
    videos = get_latest_videos(youtube, uploads_id, num_videos, skip_shorts=True)
    print(f"   ✓ Found {len(videos)} videos from '{channel_name}'")
    
    # Step 2: Vision Analysis (Premium only)
    vision_results = None
    if config["vision_analysis"]:
        print("\n🎨 Step 2: ML Thumbnail Analysis...")
        vision_results = analyze_channel_thumbnails(youtube, channel_id, min(50, num_videos))
        print(f"   ✓ Analyzed {vision_results['total_analyzed']} thumbnails")
        print(f"   ✓ Found {len(vision_results['winning_patterns'])} winning patterns")
    else:
        print("\n⏭️ Step 2: Vision Analysis (Premium only - skipped)")
    
    # Step 3: Niche Explorer (Premium only)
    niche_results = None
    if config["niche_explorer"]:
        print(f"\n🔍 Step 3: Niche Explorer ({niche_category})...")
        niche_results = explore_niche(youtube, category=niche_category)
        print(f"   ✓ Found {len(niche_results['trending_videos'])} trending videos")
        print(f"   ✓ Niche saturation: {niche_results['saturation']['classification']}")
    else:
        print("\n⏭️ Step 3: Niche Explorer (Premium only - skipped)")
    
    # Step 4: Process videos (comments + transcripts)
    print(f"\n📥 Step 4: Processing {len(videos)} videos...")
    videos_data = []
    for i, video in enumerate(videos):
        print(f"   [{i+1}/{len(videos)}] {video['title'][:50]}...")
        try:
            result = process_video(
                video['url'],
                api_key=api_key,
                model_name="tiny",  # Fast transcription
                verbose=False
            )
            videos_data.append(result)
        except Exception as e:
            print(f"      ⚠️ Skipped: {str(e)[:40]}")
    
    # Step 5: Signal-to-Noise Filter
    print("\n📊 Step 5: Filtering high-signal comments...")
    all_comments = []
    transcripts = []
    
    for v in videos_data:
        for comment in v['comments']:
            all_comments.append({
                'video': v['video_info']['title'],
                'text': comment['text'],
                'likes': comment['likes']
            })
        transcripts.append({
            'title': v['video_info']['title'],
            'transcript_excerpt': v['transcript'][:3000]
        })
    
    high_signal = filter_high_signal_comments(all_comments)
    print(f"   ✓ Filtered to {len(high_signal)} high-signal comments")
    
    # Step 6: Pain Point Extraction
    print("\n🔍 Step 6: Extracting pain points...")
    batch_size = 100
    all_pain_results = []
    
    for i in range(0, len(high_signal), batch_size):
        batch = high_signal[i:i+batch_size]
        batch_id = (i // batch_size) + 1
        result = extract_batch_signals(ai_client, batch, channel_name, batch_id, model_type, gemini_model)
        all_pain_results.append(result)
    
    clustered = cluster_pain_points(ai_client, all_pain_results, channel_name, model_type, gemini_model)
    pain_points = clustered.get('clustered_pain_points', [])
    print(f"   ✓ Found {len(pain_points)} distinct pain points")
    
    # Step 7: Gap Verification
    print("\n🔎 Step 7: Verifying gaps against content...")
    verified = verify_gaps_against_content(ai_client, pain_points, transcripts, model_type, gemini_model)
    verified_gaps = verified.get('verified_gaps', [])
    
    true_gaps = [g for g in verified_gaps if g.get('gap_status') == 'TRUE_GAP']
    under_explained = [g for g in verified_gaps if g.get('gap_status') == 'UNDER_EXPLAINED']
    
    print(f"   ✓ TRUE GAPS: {len(true_gaps)}")
    print(f"   ✓ Under-explained: {len(under_explained)}")
    
    # Step 8: Google Trends Analysis
    print("\n📈 Step 8: Checking Google Trends...")
    actionable_gaps = true_gaps + under_explained
    trend_keywords = [g.get('topic_keyword', '')[:50] for g in actionable_gaps[:10]]
    trend_results = analyze_market_trends(trend_keywords)
    
    # Step 9: Viral Scoring
    print("\n🎯 Step 9: Calculating Viral Priority Scores...")
    scored_opportunities = score_gap_opportunities(
        verified_gaps=actionable_gaps,
        vision_results=vision_results,
        trend_results=trend_results,
        niche_results=niche_results
    )
    
    for opp in scored_opportunities[:5]:
        print(f"   📊 {opp['topic']}: {opp['viral_score']} ({opp['priority']})")
    
    # Step 10: Generate Video Packages
    print(f"\n📦 Step 10: Generating {config['video_packages']} Video Packages...")
    video_packages = generate_video_packages(
        ai_client=ai_client,
        scored_opportunities=scored_opportunities[:config['video_packages']],
        vision_results=vision_results,
        channel_name=channel_name,
        model_type=model_type,
        gemini_model=gemini_model
    )
    
    # Compile results
    result = {
        "channel": channel_name,
        "channel_handle": channel_handle,
        "tier": tier,
        "generated_at": datetime.now().isoformat(),
        "pipeline_stats": {
            "videos_analyzed": len(videos_data),
            "raw_comments": len(all_comments),
            "high_signal_comments": len(high_signal),
            "pain_points": len(pain_points),
            "true_gaps": len(true_gaps),
            "under_explained": len(under_explained)
        },
        "vision_analysis": vision_results,
        "niche_analysis": niche_results,
        "trend_analysis": trend_results,
        "scored_opportunities": scored_opportunities,
        "video_packages": video_packages
    }
    
    print(f"\n{'='*60}")
    print("✅ GapIntel v2 Analysis Complete!")
    print(f"{'='*60}\n")
    
    return result


def generate_video_packages(
    ai_client,
    scored_opportunities: list,
    vision_results: dict,
    channel_name: str,
    model_type: str = "gemini",
    gemini_model: str = "gemini-2.5-flash-preview-05-20"
) -> list:
    """
    Generate complete Video Packages with title, thumbnail concept, and reasoning.
    """
    packages = []
    
    # Get winning patterns for thumbnail recommendations
    winning_patterns = []
    if vision_results and vision_results.get("winning_patterns"):
        winning_patterns = vision_results["winning_patterns"]
    
    for opp in scored_opportunities:
        # Generate thumbnail recommendation
        if winning_patterns:
            thumbnail_concept = generate_thumbnail_recommendation(
                winning_patterns=winning_patterns,
                topic=opp["topic"]
            )
        else:
            thumbnail_concept = f"Use high-contrast colors with your face visible. Include bold text overlay with key benefit for '{opp['topic']}'."
        
        # Generate optimized titles with AI
        title_prompt = f"""Generate 3 viral YouTube title options for this topic.

Channel: {channel_name}
Topic: {opp['topic']}
User Struggle: {opp.get('user_struggle', 'N/A')}
Viral Score: {opp['viral_score']}/100
Priority: {opp['priority']}

Requirements:
1. Each title must be curiosity-driven and clickable
2. Include a number or specific promise when possible
3. Keep under 60 characters
4. Reference the user's pain point

Return JSON:
{{"titles": ["Title 1", "Title 2", "Title 3"]}}
"""
        
        title_result = call_ai_model(ai_client, title_prompt, model_type, gemini_model)
        titles = title_result.get("titles", [f"The Complete Guide to {opp['topic']}"])
        
        # Build the "Why" explanation
        why_parts = []
        
        if opp["viral_score"] >= 70:
            why_parts.append(f"🔥 HIGH viral potential ({opp['viral_score']}/100)")
        
        components = opp.get("components", {})
        if components.get("trend_momentum", 0) > 10:
            why_parts.append("📈 Trending on Google right now")
        if components.get("comment_frequency", 0) > 10:
            why_parts.append(f"💬 Strong audience demand ({opp.get('total_engagement', 0):,} engagement)")
        if components.get("saturation_inverse", 0) > 15:
            why_parts.append("🎯 Low competition in this space")
        
        why_text = " | ".join(why_parts) if why_parts else "Verified content gap with audience demand"
        
        package = {
            "rank": opp.get("rank", 0),
            "topic": opp["topic"],
            "viral_score": opp["viral_score"],
            "priority": opp["priority"],
            "proposed_titles": titles,
            "thumbnail_concept": thumbnail_concept,
            "the_why": why_text,
            "gap_status": opp.get("gap_status", "UNKNOWN"),
            "user_struggle": opp.get("user_struggle", ""),
            "components": components
        }
        
        packages.append(package)
    
    return packages


def save_results(result: dict, channel_name: str):
    """Save analysis results to JSON and generate markdown report."""
    # Save JSON
    json_path = Path(f"data/gapintel_v2_{channel_name.replace(' ', '_')}.json")
    json_path.parent.mkdir(exist_ok=True)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"📄 JSON saved: {json_path}")
    
    # Generate Markdown Report
    md_path = Path(f"data/GAPINTEL_V2_{channel_name.replace(' ', '_')}.md")
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# 🎯 GapIntel v2 Report: {result['channel']}\n\n")
        f.write(f"**Generated:** {result['generated_at']}  \n")
        f.write(f"**Tier:** {result['tier'].upper()}  \n\n")
        
        # Pipeline Stats
        stats = result['pipeline_stats']
        f.write("## 📊 Analysis Summary\n\n")
        f.write(f"| Metric | Value |\n|--------|-------|\n")
        f.write(f"| Videos Analyzed | {stats['videos_analyzed']} |\n")
        f.write(f"| Comments Scanned | {stats['raw_comments']:,} |\n")
        f.write(f"| High-Signal | {stats['high_signal_comments']:,} |\n")
        f.write(f"| TRUE GAPS | {stats['true_gaps']} |\n")
        f.write(f"| Under-Explained | {stats['under_explained']} |\n\n")
        
        # Video Packages
        f.write("## 📦 Video Packages\n\n")
        
        for pkg in result['video_packages']:
            priority_emoji = "🔥" if pkg['priority'] == "HIGH" else ("📈" if pkg['priority'] == "MEDIUM" else "📊")
            
            f.write(f"### {priority_emoji} #{pkg['rank']}: {pkg['topic']}\n\n")
            f.write(f"**Viral Score:** {pkg['viral_score']}/100 ({pkg['priority']} Priority)  \n\n")
            
            f.write("**📝 Proposed Titles:**\n")
            for i, title in enumerate(pkg['proposed_titles'], 1):
                f.write(f"{i}. {title}\n")
            
            f.write(f"\n**🎨 Thumbnail Concept:**  \n> {pkg['thumbnail_concept']}\n\n")
            f.write(f"**💡 Why This Topic:**  \n{pkg['the_why']}\n\n")
            f.write("---\n\n")
        
        # Vision Analysis (if available)
        if result.get('vision_analysis') and result['vision_analysis'].get('winning_patterns'):
            f.write("## 🎨 Thumbnail Intelligence\n\n")
            f.write("**Winning Visual Patterns Found:**\n\n")
            
            for pattern in result['vision_analysis']['winning_patterns']:
                f.write(f"- **{pattern['finding']}**: {pattern['impact']}  \n")
                f.write(f"  *{pattern['recommendation']}*\n\n")
        
        # Niche Analysis (if available)
        if result.get('niche_analysis'):
            niche = result['niche_analysis']
            f.write("## 🔍 Niche Intelligence\n\n")
            f.write(f"**Category:** {niche['category']}  \n")
            f.write(f"**Saturation:** {niche['saturation']['classification']} ({niche['saturation']['score']}/100)  \n\n")
            
            if niche.get('top_channels'):
                f.write("**Top Channels in Niche:**\n")
                for ch in niche['top_channels'][:5]:
                    f.write(f"- {ch}\n")
    
    print(f"📄 Report saved: {md_path}")
    
    return json_path, md_path


def main():
    parser = argparse.ArgumentParser(description="GapIntel v2 - YouTube Intelligence Engine")
    parser.add_argument("channel", help="YouTube channel handle (e.g., @TJRTrades)")
    parser.add_argument("-n", "--videos", type=int, default=15, help="Number of videos to analyze")
    parser.add_argument("--tier", choices=["basic", "premium"], default="premium", help="Analysis tier")
    parser.add_argument("--niche", default="finance", help="Niche category for explorer")
    
    args = parser.parse_args()
    
    print("🤖 Using Gemini 2.5 Flash for AI analysis")
    print("🎙️ Using Whisper tiny for transcription")
    
    try:
        result = run_v2_analysis(
            channel_handle=args.channel,
            num_videos=args.videos,
            tier=args.tier,
            niche_category=args.niche
        )
        
        # Save results
        save_results(result, result['channel'])
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
