# GAP Intel - Project Memory (MCP Context)

This file serves as the persistent memory for the GapIntel analysis pipeline. It contains critical architectural decisions, environment details, and "hidden" knowledge to preserve context across AI sessions.

## 🏗️ Architecture Overview

The system consists of three main components:
1.  **Frontend (Next.js)**: Hosted on Vercel. Handles Stripe checkout and report display.
    - Webhook: `/api/webhook/stripe` triggers Railway.
2.  **API/Backend (Railway)**: FastAPI server with long-running background tasks.
    - Production URL: `https://resourceful-passion-production.up.railway.app`
    - Main Script: `GAP_ULTIMATE.py` (Renamed from `gap_analyzer.py` - see "Nuclear Option").
3.  **Database (Supabase)**: Stores analysis status and JSON results.

## 🛡️ Critical Fixes & "Hidden" Knowledge

### 1. The "Nuclear Option" (Script Renaming)
**Problem**: Railway exhibits aggressive caching of `.py` files. Despite local updates and successful builds, it would occasionally execute stale versions of `gap_analyzer.py`, leading to "unrecognized arguments" errors.
**Solution**: Renamed the primary entry point to `GAP_ULTIMATE.py`. If argument errors persist in the future, rename the script again (e.g., `GAP_ULTIMATE_V2.py`) to force a fresh execution context.

### 2. Environment (ffmpeg & Gemini)
- **ffmpeg**: Installed via Railway's `apt-get` in `Dockerfile`. Verified at `/usr/bin/ffmpeg`.
- **yt-dlp**: Configured to find system ffmpeg automatically.
- **AI Models**: Hardcoded to use `gemini-2.5-flash-preview-05-20` for production speed.

### 3. Supabase Integration
- **REST API**: Replaced the `supabase` Python library with direct `requests` calls to Supabase REST endpoints to resolve dependency conflicts and "proxy" initialization errors in the server environment.

### 4. Email Pipeline
- **Service**: `email_service.py` handles two types of emails:
    1.  **Start Email**: Immediate confirmation upon checkout.
    2.  **Finish Email**: Once the background analysis completes.
- **Provider**: Gmail SMTP. Credentials in environment variables `GMAIL_SENDER_EMAIL` and `GMAIL_APP_PASSWORD`.

## 🛠️ Maintenance Commands

### Deployment
```bash
cd railway-api && railway up
```

### Manual Analysis Trigger (for testing)
```bash
curl -X POST https://resourceful-passion-production.up.railway.app/analyze \
  -H "Content-Type: application/json" \
  -d '{"channel_name": "@Channel", "access_key": "YOUR-KEY", "email": "user@example.com"}'
```

### Health Check
```bash
curl https://resourceful-passion-production.up.railway.app/debug
```

## 📈 Roadmap & Next Steps
- [ ] Implement Vercel deployment for the `gap-intel-website`.
- [ ] Connect Stripe Live keys.
- [ ] Scale `GAP_ULTIMATE.py` to handle more videos as stability increases.
