# Implementation Plan - Fix Thumbnail Persistence

## Proposed Changes

### Data Pipeline
#### [MODIFY] `railway-api/GAP_ULTIMATE.py`
We need to update the `process_single_video` function (inside the `Smart Processing Mode` section) to explicitly merge the original video metadata *back* into the result returned by `process_video`.

**Rationale**: `process_video` returns a fresh `video_info` dict which might differ or lack fields compared to the `video` dict we already possess. We should treat our known `video` dict as the source of truth for metadata.

**Changes**:
Inside `process_single_video(video_tuple)`:
1.  After getting `result` from `process_video`:
2.  Update `result['video_info']['thumbnail_url']` with `video['thumbnail_url']` if missing.
3.  Actually, simpler: bulk update `result['video_info']` with the fields we want to ensure exist.

**Code Snippet Logic**:
```python
if result:
    # PRESERVE METADATA: Merge original info back into result
    # This fixes the missing thumbnail bug
    result['video_info']['thumbnail_url'] = video.get('thumbnail_url')
    result['video_info']['view_count'] = video.get('view_count') or result['video_info'].get('view_count')
    result['video_info']['like_count'] = video.get('like_count') or result['video_info'].get('like_count')
    result['video_info']['upload_date'] = video.get('upload_date') or result['video_info'].get('upload_date')
    
    return idx, result, None
```

## Verification
### Manual Verification
1.  Run the gap analyzer: `python3 railway-api/GAP_ULTIMATE.py @ChannelName --sample`
2.  Check the output JSON (printed to stdout or saved to `analysis_result.json`)
3.  Verify that `videos_analyzed` entries for the transcribed videos (the first ones) have a valid `thumbnail_url` populated.
