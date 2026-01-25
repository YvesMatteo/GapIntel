# View Railway Logs

Quick access to Railway deployment logs for debugging.

## Steps

1. **Check if Railway CLI is installed**
```bash
which railway || echo "Railway CLI not installed. Use 'brew install railway' or check dashboard."
```

2. **View recent logs** (if CLI available)
```bash
railway logs --tail 100
```

3. **Alternative: Check via health endpoint**
If Railway CLI is not available, check recent activity:
```bash
curl -s https://thriving-presence-production-ca4a.up.railway.app/health
```

## Dashboard Access
If CLI is not working, view logs directly:
- Railway Dashboard: https://railway.app/dashboard
- Select your project > Deployments > View Logs

## Log Patterns to Watch
- `[ANALYSIS]` - Analysis progress
- `[ERROR]` - Errors during processing
- `[QUEUE]` - Queue operations
- `[EMAIL]` - Email sending status

## Notes
- Railway logs rotate, older logs may not be available
- For persistent logging, check Supabase `analyses` table
- Use `/troubleshoot` for systematic debugging
