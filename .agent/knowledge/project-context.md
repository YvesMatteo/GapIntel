# GAP Intel: Project Context & Knowledge

## Project Overview
GAP Intel is a modern SaaS platform designed to identify content gaps for YouTube creators. It uses an AI-powered pipeline to analyze channel performance and community feedback (comments) to provide actionable video ideas.

## System Architecture

### 1. Frontend (Next.js)
- **Framework:** Next.js 14 (App Router)
- **Styling:** Tailwind CSS + Vanilla CSS (Glassmorphism)
- **Charts:** Recharts / Chart.js
- **Location:** `gap-intel-website/`

### 2. API / Backend (Railway)
- **Framework:** FastAPI
- **Main Script:** `GAP_ULTIMATE.py` (located in `railway-api/`)
- **Processing:** Background tasks for long-running analyses.

### 3. Database (Supabase)
- **Type:** PostgreSQL
- **Key Table:** `analyses` (stores channel name, email, access key, status, and JSON results).

---


## Critical Knowledge & Fixes

### 🌟 Project Rules & Guidelines
**Read this first:** [Project Rules](file:///Users/yvesromano/AiRAG/.agent/knowledge/project-rules.md) - Contains coding standards, Do's/Don'ts, and troubleshooting tips.

### 🛠️ Common Workflows
- **Backend Issues?** See [Troubleshoot Backend](file:///Users/yvesromano/AiRAG/.agent/workflows/troubleshoot-backend.md)
- **Database Maintenance?** See [Manage Database](file:///Users/yvesromano/AiRAG/.agent/workflows/manage-database.md)

### Railway Execution


- Railway has aggressive caching for `.py` files. To force updates, the main script was renamed to `GAP_ULTIMATE.py`. If argument errors persist, consider renaming again.

### Supabase Integration
- Use direct `requests` calls to Supabase REST endpoints in the Python backend instead of the `supabase` library to avoid dependency conflicts.

### ffmpeg Configuration
- ffmpeg is installed via Railway's Dockerfile at `/usr/bin/ffmpeg`. `yt-dlp` is configured to use this path.

### AI Models
- Primary model: `gemini-2.5-flash-preview-05-20` for speed and cost-effectiveness.

---

## Database Schema (`analyses` table)
| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary Key |
| `channel_name` | TEXT | YouTube handle |
| `email` | TEXT | User email |
| `access_key` | TEXT | Unique access token |
| `analysis_status`| TEXT | pending, processing, completed, failed |
| `analysis_result`| JSONB | Full GAP report data |
