#!/usr/bin/env python3
"""
YouTube Audio Transcription & Comments Fetcher

Downloads audio from a YouTube video, transcribes it using Whisper,
and fetches comments via the YouTube Data API v3.

Usage:
    python youtube_processor.py <YOUTUBE_URL> --api-key <YOUR_API_KEY>
    
    # With custom Whisper model
    python youtube_processor.py <YOUTUBE_URL> --api-key <KEY> --model medium
    
    # Skip comments (no API key needed)
    python youtube_processor.py <YOUTUBE_URL> --skip-comments
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime

try:
    import yt_dlp
except ImportError:
    print("Error: yt-dlp not installed. Run: pip install yt-dlp")
    sys.exit(1)

try:
    import whisper
except ImportError:
    print("Error: openai-whisper not installed. Run: pip install openai-whisper")
    sys.exit(1)

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("Warning: google-api-python-client not installed. Comments fetching will be disabled.")
    build = None


def extract_video_id(url: str) -> str:
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:embed/)([a-zA-Z0-9_-]{11})',
        r'(?:shorts/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from URL: {url}")


def download_audio(youtube_url: str, output_dir: Path) -> tuple[Path, dict]:
    """
    Download audio from YouTube video.
    
    Returns:
        Tuple of (audio_path, video_info)
    """
    print(f"\n📥 Downloading audio from: {youtube_url}")
    
    output_template = str(output_dir / "audio.%(ext)s")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_template,
        'quiet': False,
        'no_warnings': False,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        
    audio_path = output_dir / "audio.mp3"
    
    if not audio_path.exists():
        # Sometimes the extension might differ
        for ext in ['mp3', 'm4a', 'webm', 'opus']:
            alt_path = output_dir / f"audio.{ext}"
            if alt_path.exists():
                audio_path = alt_path
                break
    
    video_info = {
        'id': info.get('id'),
        'title': info.get('title'),
        'channel': info.get('channel'),
        'duration': info.get('duration'),
        'upload_date': info.get('upload_date'),
        'view_count': info.get('view_count'),
        'description': info.get('description', '')[:500],  # Truncate description
    }
    
    print(f"✅ Audio downloaded: {audio_path}")
    print(f"   Video: {video_info['title']}")
    print(f"   Channel: {video_info['channel']}")
    
    return audio_path, video_info


def transcribe_audio(audio_path: Path, model_name: str = "base") -> dict:
    """
    Transcribe audio using OpenAI Whisper.
    
    Args:
        audio_path: Path to audio file
        model_name: Whisper model (tiny, base, small, medium, large)
        
    Returns:
        Transcription result with text and segments
    """
    print(f"\n🎙️ Transcribing audio with Whisper ({model_name} model)...")
    print("   This may take a while depending on audio length and model size...")
    
    model = whisper.load_model(model_name)
    result = model.transcribe(str(audio_path))
    
    # Format segments for better readability
    formatted_segments = []
    for seg in result.get('segments', []):
        formatted_segments.append({
            'start': round(seg['start'], 2),
            'end': round(seg['end'], 2),
            'text': seg['text'].strip(),
        })
    
    transcription = {
        'text': result['text'],
        'language': result.get('language', 'unknown'),
        'segments': formatted_segments,
    }
    
    word_count = len(result['text'].split())
    print(f"✅ Transcription complete: {word_count} words, {len(formatted_segments)} segments")
    
    return transcription


def fetch_comments(video_id: str, api_key: str, max_comments: int = 500) -> list[dict]:
    """
    Fetch comments from YouTube video using Data API v3.
    
    Args:
        video_id: YouTube video ID
        api_key: YouTube Data API key
        max_comments: Maximum number of top-level comments to fetch
        
    Returns:
        List of comment dictionaries
    """
    if build is None:
        print("⚠️ google-api-python-client not available, skipping comments")
        return []
    
    print(f"\n💬 Fetching comments (max {max_comments})...")
    
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    comments = []
    next_page_token = None
    
    try:
        while len(comments) < max_comments:
            request = youtube.commentThreads().list(
                part='snippet,replies',
                videoId=video_id,
                maxResults=min(100, max_comments - len(comments)),
                pageToken=next_page_token,
                textFormat='plainText',
                order='relevance'
            )
            response = request.execute()
            
            for item in response.get('items', []):
                snippet = item['snippet']['topLevelComment']['snippet']
                comment = {
                    'id': item['id'],
                    'author': snippet['authorDisplayName'],
                    'author_channel_id': snippet.get('authorChannelId', {}).get('value', ''),
                    'text': snippet['textDisplay'],
                    'likes': snippet['likeCount'],
                    'published_at': snippet['publishedAt'],
                    'updated_at': snippet['updatedAt'],
                    'reply_count': item['snippet']['totalReplyCount'],
                }
                
                # Include up to 5 replies (API limit without additional calls)
                replies = []
                if 'replies' in item:
                    for reply in item['replies']['comments']:
                        reply_snippet = reply['snippet']
                        replies.append({
                            'id': reply['id'],
                            'author': reply_snippet['authorDisplayName'],
                            'text': reply_snippet['textDisplay'],
                            'likes': reply_snippet['likeCount'],
                            'published_at': reply_snippet['publishedAt'],
                        })
                comment['replies'] = replies
                
                comments.append(comment)
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
                
            print(f"   Fetched {len(comments)} comments...")
                
    except HttpError as e:
        if e.resp.status == 403:
            print(f"⚠️ Comments disabled or API quota exceeded: {e.reason}")
        elif e.resp.status == 404:
            print(f"⚠️ Video not found: {video_id}")
        else:
            print(f"⚠️ API error: {e}")
        return comments
    
    print(f"✅ Fetched {len(comments)} comments")
    return comments


def save_outputs(output_dir: Path, video_info: dict, transcription: dict, comments: list):
    """Save all outputs to the output directory."""
    
    print(f"\n💾 Saving outputs to: {output_dir}")
    
    # Save video metadata
    metadata_path = output_dir / "video_info.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(video_info, f, indent=2, ensure_ascii=False)
    print(f"   ✓ {metadata_path.name}")
    
    # Save plain text transcript
    transcript_txt_path = output_dir / "transcript.txt"
    with open(transcript_txt_path, 'w', encoding='utf-8') as f:
        f.write(f"# Transcript: {video_info.get('title', 'Unknown')}\n")
        f.write(f"# Channel: {video_info.get('channel', 'Unknown')}\n")
        f.write(f"# Language: {transcription.get('language', 'unknown')}\n")
        f.write(f"# Generated: {datetime.now().isoformat()}\n")
        f.write("\n" + "="*60 + "\n\n")
        f.write(transcription['text'])
    print(f"   ✓ {transcript_txt_path.name}")
    
    # Save full transcript with timestamps (JSON)
    transcript_json_path = output_dir / "transcript.json"
    with open(transcript_json_path, 'w', encoding='utf-8') as f:
        json.dump(transcription, f, indent=2, ensure_ascii=False)
    print(f"   ✓ {transcript_json_path.name}")
    
    # Save comments
    if comments:
        comments_path = output_dir / "comments.json"
        comments_data = {
            'video_id': video_info.get('id'),
            'video_title': video_info.get('title'),
            'fetched_at': datetime.now().isoformat(),
            'total_comments': len(comments),
            'comments': comments,
        }
        with open(comments_path, 'w', encoding='utf-8') as f:
            json.dump(comments_data, f, indent=2, ensure_ascii=False)
        print(f"   ✓ {comments_path.name} ({len(comments)} comments)")
    
    print("\n✨ All outputs saved successfully!")


def main():
    parser = argparse.ArgumentParser(
        description="Download YouTube audio, transcribe with Whisper, and fetch comments.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python youtube_processor.py "https://youtube.com/watch?v=VIDEO_ID" --api-key YOUR_KEY
    python youtube_processor.py "https://youtu.be/VIDEO_ID" --skip-comments
    python youtube_processor.py "URL" --api-key KEY --model medium --max-comments 1000
        """
    )
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument('--api-key', '-k', help='YouTube Data API key (required for comments)')
    parser.add_argument('--model', '-m', default='base',
                        choices=['tiny', 'base', 'small', 'medium', 'large'],
                        help='Whisper model size (default: base)')
    parser.add_argument('--output', '-o', default='./output',
                        help='Output directory (default: ./output)')
    parser.add_argument('--max-comments', type=int, default=500,
                        help='Maximum comments to fetch (default: 500)')
    parser.add_argument('--skip-comments', action='store_true',
                        help='Skip fetching comments (no API key needed)')
    parser.add_argument('--skip-transcription', action='store_true',
                        help='Skip transcription (only download audio and comments)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.skip_comments and not args.api_key:
        print("⚠️  No API key provided. Use --api-key or --skip-comments")
        print("    To get an API key: https://console.cloud.google.com/apis/credentials")
        sys.exit(1)
    
    try:
        video_id = extract_video_id(args.url)
        print(f"🎬 Video ID: {video_id}")
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # Create output directory
    output_base = Path(args.output)
    output_dir = output_base / video_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Output directory: {output_dir}")
    
    try:
        # Step 1: Download audio
        audio_path, video_info = download_audio(args.url, output_dir)
        
        # Step 2: Transcribe
        if args.skip_transcription:
            print("\n⏭️  Skipping transcription")
            transcription = {'text': '', 'segments': [], 'language': 'skipped'}
        else:
            transcription = transcribe_audio(audio_path, args.model)
        
        # Step 3: Fetch comments
        if args.skip_comments:
            print("\n⏭️  Skipping comments")
            comments = []
        else:
            comments = fetch_comments(video_id, args.api_key, args.max_comments)
        
        # Step 4: Save all outputs
        save_outputs(output_dir, video_info, transcription, comments)
        
        print(f"\n🎉 Done! Check {output_dir} for results.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
