# Test Analysis

Trigger a test analysis and monitor its progress.

## Steps

1. **Trigger a test analysis** (replace TestChannel with actual channel name)
```bash
curl -X POST https://resourceful-passion-production.up.railway.app/analyze \
  -H "Content-Type: application/json" \
  -d '{"channel_name": "TestChannel", "access_key": "TEST-KEY-001", "email": "yves.matro@gmail.com"}'
```

2. **Check the status after a few seconds**
```bash
curl -s https://resourceful-passion-production.up.railway.app/status/TEST-KEY-001 | python3 -m json.tool
```

3. Monitor Railway logs in the dashboard for `[ANALYSIS]` output lines.

## Notes
- Analysis runs in background, may take several minutes
- Check Supabase `analyses` table for status updates
- You should receive either a success or failure email
