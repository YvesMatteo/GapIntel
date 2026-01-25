# Troubleshoot Backend

Diagnose and fix common backend issues in the GAP Intel Railway environment.

## Steps

1. **Check System Health**
Verify the API is responsive.
```bash
curl -s https://resourceful-passion-production.up.railway.app/health
```

2. **Check Debug Info**
Inspect environment variables and internal state.
```bash
curl -s https://gapintel-api-production.up.railway.app/debug | python3 -m json.tool
```

3. **Debug Stuck Reports**
If an analysis is stuck in "processing" for too long:
```bash
cd /Users/yvesromano/AiRAG && python3 railway-api/debug_stuck_reports.py
```

4. **View Railway Logs**
Use the Railway CLI or check the dashboard.
```bash
# If you have railway CLI installed:
railway logs
```
> **Note:** Check the project dashboard at railway.app if CLI is not available.

5. **Restart Service**
If the service is unresponsive, trigger a rebuild.
```bash
railway restart
```
Alternative - push empty commit:
```bash
git commit --allow-empty -m "Trigger redeploy to fix freeze" && git push origin main
```
