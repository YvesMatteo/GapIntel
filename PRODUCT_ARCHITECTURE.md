# GAP Intel - Product Architecture & Implementation Guide

## 1. Product Vision (The "What")
**GAP Intel** is an AI-powered SaaS tool that helps YouTube creators identify "Content Gaps"—topics their audience is actively asking for but haven't been adequately covered.

**Core Value Proposition:**
- **Stop Guessing:** Use data, not intuition, to plan videos.
- **Guaranteed Demand:** Create content you *know* people typically want.
- **Optimization:** Get AI-driven advice on titles, thumbnails, and SEO.

**User Journey:**
1.  **Landing Page:** User enters `@ChannelHandle` + Email.
2.  **Payment:** Redirects to Stripe for a one-time payment.
3.  **Processing:** 
    - Webhook triggers backend.
    - AI analyzes 20+ recent videos and thousands of comments.
    - Identifying "High Signal" comments (questions, struggles).
4.  **Delivery:** User receives an email with a unique `Access Key`.
5.  **Dashboard:** User views a premium, interactive report displaying opportunities, health scores, and actionable advice.

---

## 2. Technical Architecture (The "How")

### High-Level Stack
- **Frontend:** Next.js 14 (App Router), Tailwind CSS, Framer Motion.
- **Backend:** Python (FastAPI) running on Railway.
- **Database:** Supabase (PostgreSQL) + Storage.
- **AI Engine:** Google Gemini 2.0 Flash / OpenAI GPT-4o-mini.
- **Payments:** Stripe (Payment Links + Webhooks).

### Data Flow Pipeline
1.  **Trigger:** Stripe Webhook (`/api/webhook/stripe`) -> Calls Backend (`/analyze`).
2.  **Queue:** Backend ([server.py](file:///Users/yvesromano/AiRAG/debug_server.py)) validates request and adds job to in-memory [JobQueue](file:///Users/yvesromano/AiRAG/railway-api/server.py#103-155).
3.  **Ingestion ([GAP_ULTIMATE.py](file:///Users/yvesromano/AiRAG/railway-api/GAP_ULTIMATE.py)):**
    - Fetches video metadata and comments via YouTube Data API.
    - Filters "High Signal" comments (questions, pain points) using Python logic (no API cost).
4.  **Analysis (The 4-Phase Engine):**
    - **Phase 1: Signal Filter:** Python-based rule engine to find questions.
    - **Phase 2: Pain Point Extraction (AI):** LLM extracts "user struggles" from comments.
    - **Phase 3: Verification (AI):** LLM checks channel transcripts to see if the topic was already covered ("TRUE GAP" vs "SATURATED").
    - **Phase 4: Optimization (AI):** Generates titles, hooks, and thumbnail ideas for verified gaps.
5.  **Storage:** Results saved to Supabase `user_reports` table.
6.  **Presentation:** Frontend (`/report/[key]`) fetches JSON, computes visualization metrics (Health Score), and renders the dashboard.

---

## 3. Codebase Structure (The "Where")

### 📂 Backend (`/railway-api`)
This is the "Brain" of the operation.
- **`server.py`**: The API Gateway.
    - **Endpoints**: `/analyze` (protected), `/status/[key]`, `/health`.
    - **Responsibilities**: Auth (API Key), Rate Limiting, Job Queuing, Supabase Updates.
- **`GAP_ULTIMATE.py`**: The Main Orchestrator.
    - Runs the entire analysis pipeline script.
    - Manages parallel processing of comments.
- **`premium/`**: Specialized Intelligence Modules.
    - `ml_models/`: Custom predictors for viral probability, CTR, etc.
    - `thumbnail_optimizer.py`: Analyzes visual patterns.
    - `competitor_analyzer.py`: Benchmarks against rival channels.
    - `growth_pattern_analyzer.py`: Detects upload consistency and series potential.

### 📂 Frontend (`/gap-intel-website`)
This is the "Face" of the product.
- **`src/app/page.tsx`**: Landing page with conversion funnel.
- **`src/app/report/[key]/page.tsx`**: The Dynamic Report Dashboard.
    - **Logic**: Server-side fetching of report data.
    - **Visualization**: Calculates `HealthScore` on the fly based on raw report data.
- **`src/components/report/`**: Modular UI sections.
    - `EngagementSection.tsx`: Comment sentiment & depth.
    - `ContentLandscapeSection.tsx`: Topic bubbles & coverage map.
    - `SatisfactionSection.tsx`: User happiness signals.

### 📂 Database (Supabase)
- **Table `analyses` / `user_reports`**:
    - `access_key` (Primary Lookup)
    - `report_data` (Huge JSON blob containing full analysis)
    - `status` (queued, processing, completed, failed)

---

## 4. Key Implementation Details

### The "Gap Verification" Logic
This is the killer feature. It doesn't just find keywords; it verifies them.
```python
# Pseudo-code logic in GAP_ULTIMATE.py
for pain_point in user_struggles:
    evidence = search_transcripts(pain_point.topic)
    if evidence == "detailed_explanation":
        mark_as("SATURATED")
    elif evidence == "brief_mention":
        mark_as("UNDER_EXPLAINED") # Good opportunity
    else:
        mark_as("TRUE_GAP") # Golden opportunity
```

### The "Health Score" Algorithm
Calculated on the frontend (`report/[key]/page.tsx`) to keep it dynamic.
It weighs 5 factors:
- **Engagement Impact (25%)**: Are people commenting/asking questions?
- **Satisfaction (25%)**: Sentiment analysis ratio.
- **SEO Strength (20%)**: Title length, keyword placement, hooks.
- **Growth Patterns (15%)**: Consistency, series usage.
- **Title Potential (15%)**: Use of psychology/hooks.
