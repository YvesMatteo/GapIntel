# GAP Intel: Project Context for Claude Code

## Project Overview
GAP Intel is a modern SaaS platform that identifies content gaps for YouTube creators. It uses an AI-powered pipeline to analyze channel performance and community feedback (comments) to provide actionable video ideas.

## System Architecture

### Frontend (Next.js)
- **Framework:** Next.js 14 (App Router)
- **Styling:** Tailwind CSS + Vanilla CSS (Glassmorphism)
- **Charts:** Recharts / Chart.js
- **Location:** `gap-intel-website/`

### Backend (Railway)
- **Framework:** FastAPI
- **Main Script:** `GAP_ULTIMATE.py` (in `railway-api/`)
- **Processing:** Background tasks for long-running analyses

### Database (Supabase)
- **Type:** PostgreSQL
- **Key Table:** `analyses` (stores channel name, email, access key, status, and JSON results)

---

## Technology Stack & Standards

### Frontend Standards
- **Language:** TypeScript
- **Styling Rule:** Prefer Tailwind utility classes. Use `globals.css` only for base styles and complex animations.
- **State Management:** React Hooks directly

### Backend Standards
- **Language:** Python 3.9+
- **EntryPoint:** `GAP_ULTIMATE.py` (keep this name to avoid Railway cache issues)
- **Processing:** Async background tasks for video analysis
- **Database Integration:** Use `requests` to call Supabase REST API directly
  - Do NOT use the `supabase-py` client library to avoid dependency conflicts

---

## Critical Do's and Don'ts

### DO
- Run local checks before pushing backend code
- Use meaningful commit messages (deployments triggered by git push)
- Check Railway logs if analysis is "stuck"

### DON'T
- Rename `GAP_ULTIMATE.py` unless necessary to break cache
- Commit secrets (ensure `.env` files are in `.gitignore`)
- Mix async/sync improperly

---

## The 7-Skill Architecture

GAP Intel uses 7 parallel analytical skills that feed into a synthesis engine:

| Skill | Purpose | Key Metrics |
|-------|---------|-------------|
| **1. Engagement Quality** | Analyze comment depth and quality | CVR, Question Density, Sentiment |
| **2. Content Landscape** | Map existing channel content | Topic Coverage, Saturation |
| **3. Demand Signals** | Extract what viewers want | Question Frequency, Opportunity Score |
| **4. Satisfaction Signals** | Infer viewer satisfaction | Satisfaction Index, Clarity Score |
| **5. Metadata & SEO** | Evaluate optimization | Title Effectiveness, SEO Strength |
| **6. Growth Patterns** | Identify growth drivers | Series Effectiveness, Consistency |
| **7. CTR Proxy** | Analyze title effectiveness | Hook Strength, Title Correlation |

### Gap Identification Formula
```
Gap Score = (Demand Signals x Competitor Gap) / (Existing Content Coverage)

Where:
- High demand + Low supply = TRUE GAP (create new content)
- High demand + Poor coverage = UNDER_EXPLAINED (expand existing)
- Low demand + High coverage = Low priority (avoid)
```

---

## Key Files

- `railway-api/GAP_ULTIMATE.py` - Primary production-grade analysis engine
- `railway-api/server.py` - FastAPI server entry point
- `railway-api/premium/` - Core 7-skill logic and ML models
- `gap-intel-website/` - Next.js frontend

---

## Database Schema (`analyses` table)

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary Key |
| `channel_name` | TEXT | YouTube handle |
| `email` | TEXT | User email |
| `access_key` | TEXT | Unique access token |
| `analysis_status` | TEXT | pending, processing, completed, failed |
| `analysis_result` | JSONB | Full GAP report data |

---

## Railway URLs

- **Health Check:** https://resourceful-passion-production.up.railway.app/health
- **Debug:** https://resourceful-passion-production.up.railway.app/debug

---

## Troubleshooting Cheatsheet

- **Stuck Analysis?** Run `python3 railway-api/debug_stuck_reports.py`
- **Database Error?** Check the RLS policies in Supabase
- **Deployment Failed?** Check Build Logs in Railway
- **Force Railway Rebuild?** Push an empty commit: `git commit --allow-empty -m "Trigger redeploy"`

---

## Ralph Loop Methodology

For complex, multi-step features, use the persistent file approach:

1. **PROMPT.md** - The "User's Voice": high-level objective, constraints, success criteria
2. **IMPLEMENTATION_PLAN.md** - The "Agent's Brain": detailed task breakdown, status, notes

### The Loop Protocol
1. **ANCHOR**: Read `PROMPT.md` to confirm the goal
2. **CONTEXT**: Read `IMPLEMENTATION_PLAN.md` to identify next task
3. **PLAN**: If plan is empty/outdated, populate it from PROMPT.md
4. **EXECUTE**: Pick the single most important next step
5. **UPDATE**: Edit IMPLEMENTATION_PLAN.md with progress
6. **REPEAT**: Go back to step 1

---

## Available Slash Commands

Run these with `/command-name`:
- `/deploy` - Smart deploy to Railway
- `/health` - Check Railway API health
- `/troubleshoot` - Diagnose backend issues
- `/database` - Manage Supabase database
- `/sql` - Execute SQL queries directly
- `/test-analysis` - Trigger a test analysis
- `/test-email` - Test email sending
- `/architect` - Generate PROMPT.md and IMPLEMENTATION_PLAN.md for a feature
- `/init-ralph` - Initialize Ralph Loop files

---

## Quality Gates

- Minimum 50 comments per channel for reliable analysis
- Minimum 20 videos for pattern recognition
- Confidence threshold: >65% for each skill output
- Analysis completion target: <5 minutes per channel
