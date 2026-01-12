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

try:
    import whisper
except ImportError:
    print("❌ openai-whisper not installed. Run: pip install openai-whisper")
    sys.exit(1)

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("❌ google-api-python-client not installed. Run: pip install google-api-python-client")
    sys.exit(1)


# Global Whisper model cache (avoid reloading for each video)
_whisper_model = None
_whisper_model_name = None


def get_whisper_model(model_name: str = "base"):
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


def download_audio(youtube_url: str, output_dir: Path, video_id: str, verbose: bool = False) -> tuple[Path, dict]:
    """
    Download audio from YouTube video using local ffmpeg.
    
    Returns:
        Tuple of (audio_path, video_info)
    """
    audio_path = output_dir / f"{video_id}.mp3"
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.resolve()
    ffmpeg_local = script_dir / "ffmpeg"
    
    # Force ffmpeg directory into PATH (Railway environment fix)
    os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + "/usr/bin"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(output_dir / f"{video_id}.%(ext)s"),
        'quiet': True,
        'no_warnings': True,
        # Point to the directory containing ffmpeg/ffprobe
        'ffmpeg_location': '/usr/bin/',
    }
    
    # Logic to find ffmpeg:
    # We've forced /usr/bin into PATH and ydl_opts.
    pass
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        # Find the file (extension is unknown now)
        downloaded_files = list(output_dir.glob(f"{video_id}.*"))
        if not downloaded_files:
            raise FileNotFoundError(f"Download failed for {video_id}")
        audio_path = downloaded_files[0]
        
    video_info = {
        'id': info.get('id'),
        'title': info.get('title', 'Unknown Title'),
        'channel': info.get('channel', 'Unknown Channel'),
        'duration': info.get('duration'),
        'upload_date': info.get('upload_date'),
        'view_count': info.get('view_count'),
        'description': info.get('description', '')[:500],
        'url': youtube_url,
    }
    
    return audio_path, video_info


def transcribe_audio(audio_path: Path, model_name: str = "base") -> dict:
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


def process_video(url: str, api_key: str, model_name: str = "base", 
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
    
    # Step 1: Download audio
    if verbose:
        print(f"   📥 Downloading audio...")
    audio_path, video_info = download_audio(url, temp_dir, video_id, verbose)
    if verbose:
        print(f"   ✓ {video_info['title'][:50]}...")
    
    # Step 2: Fetch comments (raw, no filtering)
    if verbose:
        print(f"   💬 Fetching comments...")
    comments = fetch_all_comments(video_id, api_key, max_comments=200)
    if verbose:
        print(f"   ✓ {len(comments)} comments")
    
    # Step 3: Transcribe
    if verbose:
        print(f"   🎙️ Transcribing...")
    transcription = transcribe_audio(audio_path, model_name)
    word_count = len(transcription['text'].split())
    if verbose:
        print(f"   ✓ {word_count} words")
    
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
    parser.add_argument('--model', '-m', default='base',
                        choices=['tiny', 'base', 'small', 'medium', 'large'],
                        help='Whisper model size (default: base)')
    
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
    