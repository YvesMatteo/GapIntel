#!/usr/bin/env python3
"""
YouTube Ingest Manager - Phase 2 (Modular)

Fetches YouTube video audio, transcribes with Whisper, and extracts viewer questions.
Can be used standalone or imported by other scripts (e.g., gap_analyzer.py).

Usage (standalone):
    python3 ingest_manager.py "https://youtube.com/watch?v=VIDEO_ID"
    
Usage (as module):
    from ingest_manager import process_video
    result = process_video(url, api_key)
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("❌ python-dotenv not installed. Run: pip install python-dotenv")
    sys.exit(1)

try:
    import yt_dlp
except ImportError:
    print("❌ yt-dlp not installed. Run: pip install yt-dlp")
    sys.exit(1)

# import whisper (Removed: strict caption-only mode)

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("❌ google-api-python-client not installed. Run: pip install google-api-python-client")
    sys.exit(1)

# Try to import youtube-transcript-api
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    CAPTIONS_AVAILABLE = True
except ImportError:
    CAPTIONS_AVAILABLE = False
    print("⚠️ youtube-transcript-api not available, smart transcription disabled")


# Whisper model cache removed
_whisper_model_name = None


def get_whisper_model(model_name: str = "tiny"):
    """Get cached Whisper model or load it."""
    global _whisper_model, _whisper_model_name
    if _whisper_model is None or _whisper_model_name != model_name:
        print(f"   Loading Whisper {model_name} model...")
        _whisper_model = whisper.load_model(model_name)
        _whisper_model_name = model_name
    return _whisper_model


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


def sanitize_filename(title: str) -> str:
    """Sanitize video title for use as filename."""
    sanitized = re.sub(r'[<>:"/\\|?*]', '', title)
    sanitized = re.sub(r'\s+', '_', sanitized)
    return sanitized[:100]


def fetch_all_comments(video_id: str, api_key: str, max_comments: int = 500) -> list[dict]:
    """
    Fetch ALL comments from a YouTube video (no filtering).
    Returns raw comments for AI processing, sorted by relevance (top comments first).
    """
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    comments = []
    next_page_token = None
    
    try:
        while len(comments) < max_comments:
            request = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=100,
                pageToken=next_page_token,
                textFormat='plainText',
                order='relevance'
            )
            response = request.execute()
            
            for item in response.get('items', []):
                snippet = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'author': snippet['authorDisplayName'],
                    'text': snippet['textDisplay'],
                    'likes': snippet['likeCount'],
                    'published_at': snippet['publishedAt'],
                })
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
                
    except HttpError as e:
        if e.resp.status == 403:
            print(f"   ⚠️ Comments disabled or quota exceeded")
        else:
            print(f"   ⚠️ API error: {e}")
    
    return comments


def download_audio(youtube_url: str, output_dir: Path, video_id: str, verbose: bool = False, max_retries: int = 3) -> tuple[Path, dict]:
    """
    Download audio from YouTube video using yt-dlp with robust fallbacks.
    
    Implements multiple strategies to handle YouTube blocks:
    1. Exponential backoff retries
    2. Different format fallbacks
    3. Anti-blocking measures (user-agent rotation, etc.)
    
    Returns:
        Tuple of (audio_path, video_info)
    """
    import random
    import time
    
    audio_path = output_dir / f"{video_id}.mp3"
    
    # Force ffmpeg directory into PATH (Railway environment fix)
    os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + "/usr/bin"
    
    # User agents to rotate through
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    # Different format strategies to try
    format_strategies = [
        'bestaudio/best',
        'worstaudio/worst',  # Sometimes simpler formats work better
        'bestaudio[ext=m4a]/bestaudio/best',
        '140',  # m4a audio format code
    ]
    
    last_error = None
    
    for attempt in range(max_retries):
        # Rotate through strategies
        format_choice = format_strategies[attempt % len(format_strategies)]
        user_agent = random.choice(user_agents)
        
        if verbose or attempt > 0:
            print(f"   📥 Download attempt {attempt + 1}/{max_retries} (format: {format_choice[:15]}...)")
        
        ydl_opts = {
            'format': format_choice,
            'outtmpl': str(output_dir / f"{video_id}.%(ext)s"),
            'quiet': True,
            'no_warnings': True,
            'ffmpeg_location': '/usr/bin/',
            # Timeout and retry settings
            'socket_timeout': 60,
            'retries': 5,
            'fragment_retries': 5,
            'http_chunk_size': 10485760,  # 10MB chunks
            # Anti-blocking measures
            'user_agent': user_agent,
            'referer': 'https://www.youtube.com/',
            'sleep_interval': 1,  # Small delay between requests
            'max_sleep_interval': 3,
            # Bypass age gate and other restrictions
            'nocheckcertificate': True,
            'ignoreerrors': False,
            # Try to extract video without downloading first (faster failure detection)
            'skip_download': False,
            # Use cookies from browser if available
            'cookiesfrombrowser': None,  # Can be set to ('chrome',) etc.
            # Extractor retries
            'extractor_retries': 3,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                
                # Find the downloaded file
                downloaded_files = list(output_dir.glob(f"{video_id}.*"))
                if not downloaded_files:
                    raise FileNotFoundError(f"Download completed but file not found for {video_id}")
                
                audio_path = downloaded_files[0]
                
                video_info = {
                    'id': info.get('id'),
                    'video_id': info.get('id'),  # Add for compatibility
                    'title': info.get('title', 'Unknown Title'),
                    'channel': info.get('channel', 'Unknown Channel'),
                    'duration': info.get('duration'),
                    'upload_date': info.get('upload_date'),
                    'view_count': info.get('view_count'),
                    'like_count': info.get('like_count'),
                    'thumbnail_url': info.get('thumbnail'),
                    'description': info.get('description', '')[:500],
                    'url': youtube_url,
                }
                
                if verbose:
                    print(f"   ✓ Downloaded successfully: {video_info['title'][:40]}...")
                
                return audio_path, video_info
                
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            
            # Check if it's a permanent error (video unavailable, private, etc.)
            permanent_errors = ['private video', 'video unavailable', 'removed', 'terminated', 'copyright']
            if any(err in error_str for err in permanent_errors):
                if verbose:
                    print(f"   ⚠️ Video unavailable (permanent): {str(e)[:80]}")
                break
            
            # For temporary errors (403, rate limit), wait and retry
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(1, 3)  # Exponential backoff with jitter
                if verbose:
                    print(f"   ⚠️ Failed: {str(e)[:50]}... Retrying in {wait_time:.1f}s")
                time.sleep(wait_time)
            else:
                if verbose:
                    print(f"   ⚠️ Failed: {str(e)[:80]}")
    
    # All retries failed - raise the last error
    raise Exception(f"Failed to download {video_id} after {max_retries} attempts: {last_error}")


def transcribe_audio(audio_path: Path, model_name: str = "tiny") -> dict:
    """
    Transcribe audio using OpenAI Whisper (local).
    """
    model = get_whisper_model(model_name)
    result = model.transcribe(str(audio_path))
    
    segments = []
    for seg in result.get('segments', []):
        segments.append({
            'start': round(seg['start'], 2),
            'end': round(seg['end'], 2),
            'text': seg['text'].strip(),
        })
    
    return {
        'text': result['text'],
        'language': result.get('language', 'unknown'),
        'segments': segments,
    }


def fetch_captions(video_id: str) -> dict:
    """
    Fetch YouTube captions for a video using youtube-transcript-api.
    Returns format compatible with Whisper output: {text, segments}
    """
    if not CAPTIONS_AVAILABLE:
        return None
        
    try:
        # Use new API (v1.2.3+)
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        
        full_text = ""
        segments = []
        
        for snippet in transcript:
            text = snippet.text.replace('\n', ' ').strip()
            start = snippet.start
            end = start + snippet.duration
            
            full_text += text + " "
            
            segments.append({
                'start': start,
                'end': end,
                'text': text
            })
            
        return {
            'text': full_text.strip(),
            'language': 'en',  # Assumed or API could provide
            'segments': segments
        }
    except Exception as e:
        # Don't print huge stack traces for common "no caption" errors
        error = str(e).lower()
        if 'disabled' in error or 'not found' in error or 'no transcript' in error:
            return None
        print(f"⚠️ Caption fetch failed: {e}")
        return None


def process_video(url: str, api_key: str, model_name: str = "tiny", 
                  temp_dir: Path = None, verbose: bool = True) -> dict:
    """
    Process a single YouTube video: download, transcribe, fetch comments.
    
    This is the main reusable function for other scripts.
    
    Args:
        url: YouTube video URL
        api_key: YouTube Data API key
        model_name: Whisper model size
        temp_dir: Directory for temp audio files (default: ./data/.temp)
        verbose: Print progress messages
        
    Returns:
        dict with keys:
            - video_info: Video metadata
            - transcript: Full transcript text
            - transcript_segments: List of {start, end, text}
            - comments: List of raw comments
    """
    # Setup temp directory
    if temp_dir is None:
        script_dir = Path(__file__).parent.resolve()
        temp_dir = script_dir / "data" / ".temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract video ID
    video_id = extract_video_id(url)
    
    if verbose:
        print(f"\n📹 Processing: {video_id}")
    
    # Step 1: Smart Transcription (Strict: Captions ONLY)
    transcription = None # Audio/Transcribe functions removed (Strict mode)
    video_info = None
    
    # Try fetching captions
    if verbose:
        print(f"   🔍 Checking for captions...")
    
    caption_result = fetch_captions(video_id)
    
    if not caption_result:
        if verbose:
            print(f"   ❌ No captions found. Skipping video (Strict mode).")
        return None
        
    if verbose:
        print(f"   ✅ Captions found!")
    transcription = caption_result
    
    # Fetch metadata (lightweight, no download)
    if verbose:
        print(f"   ℹ️ Fetching metadata only...")
    
    try:
        ydl_opts_meta = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True, # Key: don't download anything
        }
        with yt_dlp.YoutubeDL(ydl_opts_meta) as ydl:
            info = ydl.extract_info(url, download=False)
            video_info = {
                'id': info.get('id'),
                'title': info.get('title'),
                'url': info.get('webpage_url'),
                'uploader': info.get('uploader'),
                'uploader_id': info.get('uploader_id'),
                'description': info.get('description'),
                'view_count': info.get('view_count'),
                'like_count': info.get('like_count'),
                'duration': info.get('duration'),
                'upload_date': info.get('upload_date'),
                'thumbnail_url': info.get('thumbnail'),
                'tags': info.get('tags', []),
            }
    except Exception as e:
        print(f"⚠️ Metadata fetch failed: {e}")
        # Minimal fallback
        video_info = {'id': video_id, 'title': f"Video {video_id}", 'url': url}

    # Step 2: Fetch comments
    if verbose:
        print(f"   💬 Fetching comments...")
    comments = fetch_all_comments(video_id, api_key, max_comments=200)
    if verbose:
        print(f"   ✓ {len(comments)} comments")
    
    word_count = len(transcription['text'].split())
    if verbose:
        print(f"   ✓ {word_count} words in transcript")
    
    # Return structured data
    return {
        'video_info': video_info,
        'transcript': transcription['text'],
        'transcript_segments': transcription['segments'],
        'comments': comments,
    }


# ============================================================
# Standalone CLI mode (for backwards compatibility)
# ============================================================

def format_timestamp(seconds: float) -> str:
    """Format seconds to HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def is_question(text: str) -> bool:
    """Check if a comment text appears to be a question."""
    text_lower = text.lower().strip()
    if '?' in text:
        return True
    question_words = ['what', 'why', 'how', 'when', 'where', 'who', 'which', 
                      'can', 'could', 'would', 'should', 'is', 'are', 'do', 
                      'does', 'did', 'will', 'have', 'has']
    for word in question_words:
        if text_lower.startswith(word + ' '):
            return True
    return False


def export_markdown(output_path: Path, video_info: dict, transcription: dict, questions: list):
    """Export results as Markdown file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# {video_info['title']}\n\n")
        f.write(f"**Channel:** {video_info['channel']}  \n")
        f.write(f"**Video ID:** {video_info['id']}  \n")
        if video_info.get('upload_date'):
            upload_date = video_info['upload_date']
            formatted_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
            f.write(f"**Upload Date:** {formatted_date}  \n")
        if video_info.get('view_count'):
            f.write(f"**Views:** {video_info['view_count']:,}  \n")
        f.write(f"**Language:** {transcription.get('language', 'unknown')}  \n")
        f.write(f"**Processed:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  \n")
        f.write("\n---\n\n")
        
        f.write("## 📝 Transcript\n\n")
        for segment in transcription.get('segments', []):
            timestamp = format_timestamp(segment['start'])
            f.write(f"**[{timestamp}]** {segment['text']}\n\n")
        if not transcription.get('segments'):
            f.write(transcription.get('text', 'No transcript available.'))
            f.write("\n\n")
        
        f.write("---\n\n")
        f.write("## 💭 Viewer Sentiment & Questions\n\n")
        
        if questions:
            f.write(f"*{len(questions)} viewer questions identified (sorted by engagement):*\n\n")
            for i, q in enumerate(questions, 1):
                f.write(f"### Q{i}. {q['author']}\n")
                f.write(f"> {q['text']}\n\n")
                f.write(f"👍 {q['likes']} likes\n\n")
        else:
            f.write("*No viewer questions found in the comments.*\n\n")


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Ingest Manager - Download, transcribe, and analyze videos.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument('--model', '-m', default='tiny',
                        choices=['tiny', 'base', 'small', 'medium', 'large'],
                        help='Whisper model size (default: tiny)')
    
    args = parser.parse_args()
    
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        print("❌ YOUTUBE_API_KEY not found in environment.")
        sys.exit(1)
    
    try:
        # Use the new process_video function
        result = process_video(args.url, api_key, args.model)
        
        # Filter for questions (for standalone mode)
        questions = [c for c in result['comments'] if is_question(c['text'])]
        questions.sort(key=lambda x: x['likes'], reverse=True)
        questions = questions[:50]
        
        # Export
        script_dir = Path(__file__).parent.resolve()
        data_dir = script_dir / "data"
        data_dir.mkdir(exist_ok=True)
        
        filename = sanitize_filename(result['video_info']['title']) + ".md"
        output_path = data_dir / filename
        
        transcription = {
            'text': result['transcript'],
            'segments': result['transcript_segments'],
            'language': 'auto',
        }
        export_markdown(output_path, result['video_info'], transcription, questions)
        
        print(f"\n🎉 Done! Output saved to:")
        print(f"   {output_path}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
    