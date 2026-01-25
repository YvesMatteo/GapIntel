# Reset Analysis

Reset a stuck or failed analysis to allow it to be reprocessed.

## Instructions

When asked to reset an analysis, you need the `access_key` of the analysis.

## Steps

1. **Find the stuck analysis**
First, identify which analyses are stuck:
```bash
python3 /Users/yvesromano/AiRAG/railway-api/debug_stuck_reports.py
```

2. **Reset via API** (if endpoint exists)
```bash
curl -X POST https://thriving-presence-production-ca4a.up.railway.app/reset-analysis \
  -H "Content-Type: application/json" \
  -d '{"access_key": "ACCESS_KEY_HERE"}'
```

3. **Reset via direct SQL** (alternative)
Use the `/sql` command with this query:
```sql
UPDATE analyses
SET analysis_status = 'pending',
    updated_at = NOW()
WHERE access_key = 'ACCESS_KEY_HERE';
```

4. **Verify the reset**
```bash
curl -s https://thriving-presence-production-ca4a.up.railway.app/status/ACCESS_KEY_HERE | python3 -m json.tool
```

## Notes
- Resetting moves status back to "pending" so it can be reprocessed
- The analysis will be picked up on the next queue cycle
- Check Railway logs to confirm reprocessing starts
