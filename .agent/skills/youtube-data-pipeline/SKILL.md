---
name: youtube-data-pipeline
description: Skill for the Data Collection Layer. Use to fetch audio/transcripts/comments, handle API quotas, and normalize YouTube data.
---

# YouTube Data Pipeline

Handles the extraction and normalization of data from YouTube. Combines `yt-dlp` (Audio), `OpenAI Whisper` (Transcription), and `YouTube Data API` (Comments/Metadata).

## When to Use This Skill

- Fetching video transcripts (Audio download + Whisper)
- Downloading high-volume comments (with pagination)
- Extracting raw video metadata
- Signal-to-Noise filtering of comments
- Saving standardized JSON datasets

## Architecture (`youtube_processor.py`)

1.  **Download**: Extract audio via `yt-dlp` (bestaudio/mp3).
2.  **Transcribe**: Local inference using `whisper` (base/medium models).
3.  **Enrich**: Fetch comments via API (max 500-1000).
4.  **Filter**: `filter_high_signal_comments` removes "Great video!" noise.

## Core Functions

### Audio & Transcript

```python
def download_audio(url, path):
    # Uses yt-dlp to get audio stream
    # Returns path_to_mp3

def transcribe_audio(path, model="base"):
    # Uses OpenAI Whisper locally
    # Returns { text, segments: [{start, end, text}] }
```

### Comment Fetching

```python
def fetch_comments(video_id, api_key, max_comments=500):
    # Pages through CommentThreads
    # Returns list of normalized comment objects
```

### Signal Filtering (Phase 1)

Clean raw comments before sending to AI (saves tokens/cost).

**Keep if:**
*   Contains `?` (Question)
*   Contains "how to", "why", "help", "struggling"
*   Length > 15 chars

**Discard if:**
*   Contains only "fire", "love this", "great video" (Low Intent)
*   Short length

## Data Storage Standard

All data is saved in a standardized folder structure:

```
/data/{video_id}/
├── video_info.json    # Metadata (views, date, description)
├── transcript.txt     # Plain text for LLM context
├── transcript.json    # Full segments with timestamps
├── comments.json      # Raw comment dump
└── audio.mp3          # (Optional, deleted after transcription)
```

## Validation Checklist

- [ ] Is `yt-dlp` and `ffmpeg` installed?
- [ ] Is the Whisper model loaded correctly?
- [ ] Is the YouTube API Key valid?
- [ ] Are comments filtered for PII or excessive noise?
- [ ] Does audio path handle variable extensions (mp3/m4a/webm)?
