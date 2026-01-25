# Goal
Fix the missing thumbnails in the GAP Intel report.

## Context
The user reported that thumbnails are not showing up in the generated report.
Analysis reveals that while `GAP_ULTIMATE.py` correctly fetches thumbnail URLs for all videos initially (in `get_latest_videos`), this data is **lost** for the top 5 videos that go through the transcription process (`process_video`).

`process_video` in `ingest_manager.py` attempts to re-fetch metadata but fails silently if the API call errors or if specific fields are missing, leading to incomplete `video_info` being returned.

## Requirements
- **Preserve Metadata**: The transcription pipeline in `GAP_ULTIMATE.py` MUST preserve the original `thumbnail_url`, `view_count`, `like_count`, and `upload_date` fetched during the initial playlist scan.
- **Fail-safe**: Even if `process_video` fails to fetch fresh metadata, we must use the data we already have.
- **Consistency**: Ensure transcribed videos (top 5) and comment-only videos (the rest) share the exact same metadata structure.
