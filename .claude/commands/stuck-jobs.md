# Stuck Jobs Diagnostics

Find and fix stuck analysis jobs in the GAP Intel pipeline.

## Steps

1. **Run the stuck reports diagnostic script**
```bash
python3 /Users/yvesromano/AiRAG/railway-api/debug_stuck_reports.py
```

2. **Check queue status on Railway**
```bash
curl -s https://thriving-presence-production-ca4a.up.railway.app/queue-status | python3 -m json.tool
```

3. **Wake up Railway if sleeping**
Railway may be asleep - wake it up:
```bash
curl -s https://thriving-presence-production-ca4a.up.railway.app/health
```

4. **Check for analyses stuck > 30 minutes**
```bash
curl -s "https://thriving-presence-production-ca4a.up.railway.app/api/debug/stuck" | python3 -m json.tool
```

## Common Causes of Stuck Jobs
1. **Railway sleeping**: App goes to sleep after inactivity
2. **YouTube API quota**: Daily quota exceeded
3. **Processing error**: Unhandled exception in analysis
4. **Memory issues**: Large channels causing OOM

## Recovery Actions

**Option 1: Trigger recovery manually**
```bash
curl -X POST https://thriving-presence-production-ca4a.up.railway.app/api/recovery/run
```

**Option 2: Reset specific job** (use `/reset-analysis`)

**Option 3: Force redeploy**
```bash
git commit --allow-empty -m "Trigger redeploy to recover stuck jobs" && git push origin main
```

## Notes
- Stuck threshold is 30 minutes
- Alert threshold is 60 minutes (triggers email)
- Recovery runs every 15 minutes automatically
- Check Railway dashboard for memory/CPU issues
