# GAP Intel: Development & Operations Guide

This document contains essential instructions for developing, testing, and deploying the GAP Intel platform.

## Local Development Setup

### Backend (Python/FastAPI)
1. **Navigate**: `cd railway-api`
2. **Environment**: Ensure `.env` contains:
    - `YOUTUBE_API_KEY`
    - `OPENAI_API_KEY` or `GEMINI_API_KEY`
    - `SUPABASE_URL` & `SUPABASE_SERVICE_ROLE_KEY`
3. **Run**: `python3 server.py` (Main FastAPI server)
4. **Test Logic**: You can run `python3 GAP_ULTIMATE.py @Handle` to test the full analysis pipeline locally without the API.

### Frontend (Next.js)
1. **Navigate**: `cd gap-intel-website`
2. **Environment**: Verify `.env.local` has:
    - `NEXT_PUBLIC_SUPABASE_URL`
    - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
    - `API_BASE_URL` (Pointing to your local or staging backend)
3. **Run**: `npm run dev`

---

## Deployment Workflows

### 1. Deploying the Backend (Railway)
- The backend is deployed to Railway via GitHub integration.
- **Aggressive Caching**: Railway sometimes caches `.py` files aggressively. If changes don't reflect, you may need to rename the main script (from `gap_analyzer.py` to `GAP_ULTIMATE.py`) or force a rebuild without cache.
- **Config**: Ensure `railway.json` and `Procfile` correctly point to `server.py`.

### 2. Deploying the Frontend (Vercel/Railway)
- The frontend is typically deployed via Vercel or Railway.
- Ensure all `NEXT_PUBLIC_` environment variables are correctly set in the production environment.

---

## Common Maintenance Tasks

- **Database Migrations**: Update `railway-api/supabase/migrations/` and apply them to Supabase.
- **API Quotas**: Monitor YouTube API usage. The deep analysis is quota-intensive (fetching transcripts and thousands of comments).
- **ML Model Reloads**: If models in `premium/ml_models/` are updated, the FastAPI server must be restarted to load the new weights/logic.

## Troubleshooting

- **"Failed to generate authorization URL"**: Check Google Cloud OAuth credentials and redirect URIs.
- **"Stuck in Processing"**: Usually indicates a crash in the background analysis script. Check Railway logs for `GAP_ULTIMATE.py` execution errors.
- **"Broken UI/Layout"**: Verify `globals.css` hasn't been corrupted; the "Glassmorphism" effect relies on specific backdrop-filter and transparency settings.
