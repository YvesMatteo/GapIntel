---
description: Diagnose and fix common backend issues in the GAP Intel Railway environment.
---

# Troubleshoot Backend

This workflow helps you diagnose and resolve common issues with the Python backend on Railway.

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
   If an analysis is stuck in "processing" for too long, run this script to reset or investigate it.
   ```bash
   cd /Users/yvesromano/AiRAG && python3 railway-api/debug_stuck_reports.py
   ```

4. **View Railway Logs**
   Use the Railway CLI (if installed) or checking the dashboard is often the fastest way to see stack traces.
   ```bash
   # If you have railway CLI installed:
   railway logs
   ```
   > **Note:** If you don't have the CLI, check the project dashboard at [railway.app](https://railway.app).

5. **Restart Service**
   If the service is unresponsive, trigger a rebuild.
   ```bash
   railway restart
   ```
   *Alternative:* Push an empty commit to trigger a redeploy.
   ```bash
   git commit --allow-empty -m "Trigger redeploy to fix freeze" && git push origin main
   ```
