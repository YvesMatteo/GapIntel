# GAP Intel: Project Rules & Guidelines

## 1. Project Overview
GAP Intel is a SaaS platform combining a Next.js frontend with a Python (FastAPI) backend on Railway, using Supabase as the database.

## 2. Technology Stack & Standards

### Frontend (User-Facing)
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS + Vanilla CSS (for glassmorphism effects).
  - *Rule:* Prefer Tailwind utility classes. Use `globals.css` only for base styles and complex animations.
- **State Management:** React Hooks directly.
- **Location:** `gap-intel-website/`

### Backend (Analysis Engine)
- **Framework:** FastAPI
- **Language:** Python 3.9+
- **Location:** `railway-api/`
- **EntryPoint:** `GAP_ULTIMATE.py` (Must keep this name to avoid Railway cache issues).
- **Processing:** Asynchronous background tasks for video analysis.

### Database
- **Platform:** Supabase (PostgreSQL)
- **Integration Rule:** In Python, use **`requests`** to call Supabase REST API directly.
  - *Do NOT* use the `supabase-py` client library in the backend to avoid dependency conflicts and strict typing issues.
- **Schema Management:** Apply SQL changes via the Supabase Dashboard or the provided SQL scripts in `railway-api/premium/db/`.

## 3. Critical "Do's and Don'ts"

### ✅ DO
- **Run local checks:** Before pushing backend code, ensure it runs locally or use the `/deploy-railway` workflow to test on dev.
- **Use meaningful commit messages:** Deployments are triggered by git push.
- **Check Railway logs:** If an analysis is "stuck", checks the Railway logs first.

### ❌ DON'T
- **Rename `GAP_ULTIMATE.py`:** Unless absolutely necessary to break a cache, keep this filename.
- **Commit secrets:** Ensure `.env` files are in `.gitignore`.
- **Mix Async/Sync improperly:** FastAPI is async; ensure database calls don't block the main event loop if possible (though `requests` is sync, it's currently accepted for simplicity in this project).

## 4. Troubleshooting cheat sheet
- **Stuck Analysis?** Run `python3 railway-api/debug_stuck_reports.py`.
- **Database Error?** Check the RLS policies in Supabase.
- **Deployment Failed?** Check the Build Logs in Railway.
