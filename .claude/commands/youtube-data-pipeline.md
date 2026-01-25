# YouTube Data Pipeline

Handle extraction and normalization of data from YouTube.

## Instructions

When working on data pipeline features:

1. **Architecture**:
   - Download: Extract audio via `yt-dlp` (bestaudio/mp3)
   - Transcribe: Local inference using `whisper` (base/medium models)
   - Enrich: Fetch comments via API (max 500-1000)
   - Filter: Remove low-signal comments

2. **Signal Filtering (Phase 1)**:

   **Keep if**:
   - Contains `?` (Question)
   - Contains "how to", "why", "help", "struggling"
   - Length > 15 chars

   **Discard if**:
   - Only "fire", "love this", "great video" (Low Intent)
   - Short length

3. **Data Storage Structure**:
   ```
   /data/{video_id}/
   ├── video_info.json    # Metadata (views, date, description)
   ├── transcript.txt     # Plain text for LLM context
   ├── transcript.json    # Full segments with timestamps
   ├── comments.json      # Raw comment dump
   └── audio.mp3          # (Optional, deleted after transcription)
   ```

4. **Core Functions**:
   - `download_audio(url, path)` - Uses yt-dlp
   - `transcribe_audio(path, model="base")` - Uses Whisper
   - `fetch_comments(video_id, api_key, max=500)` - Pages through API

5. **Requirements**:
   - yt-dlp and ffmpeg installed
   - Whisper model loaded
   - Valid YouTube API Key
   - Filter PII from comments
