# GAP Intel: Backend Deep Dive

This document details the architecture and implementation of the GAP Intel backend, primarily located in `railway-api/`.

## Core Orchestrator: `GAP_ULTIMATE.py`

`GAP_ULTIMATE.py` is the primary engine for deep channel analysis. It implements a 4-phase pipeline (Plus a Trends enrichment phase).

### 1. Phase 1: Signal-to-Noise Filter
- **Purpose**: Reduce AI costs and noise by filtering public comments.
- **Logic**: Uses Python-based keyword matching and length filters to identify comments that express confusion, specific questions, or requests (e.g., "how to", "struggling", "?").
- **Sentiment Integration**: Includes a DistilBERT-based `SentimentEngine` to categorize comments (Confusion, Inquiry, Success, etc.).

### 2. Phase 2: Pain Point Extraction (AI)
- **Purpose**: Identify what the audience *needs* without hallucinating solutions.
- **Method**: Batches high-signal comments and passes them to an LLM (Gemini 2.5 Flash) to extract specific "Pain Points" or "Knowledge Gaps".
- **Clustering (Phase 2B)**: Merges similar pain points to find common themes and calculates total engagement (likes) per topic.

### 3. Phase 3: Gap Verification
- **Purpose**: Verify that the identified pain points are *actual* gaps in the creator's library.
- **Method**: Cross-references verified pain points against the transcripts of the channel's 15-20 most recent videos.
- **Statuses**:
    - `TRUE_GAP`: Not mentioned in recent content.
    - `UNDER_EXPLAINED`: Mentioned but not deeply explored.
    - `SATURATED`: Fully covered in recent videos.

### 4. Phase 3.5: Market Trends Enrichment
- **Purpose**: Validate data-driven opportunities with real-world momentum.
- **Logic**: Uses `pytrends` (Google Trends) to check interest scores and trajectories (Rising, Stable, Falling) for the top identified gaps.

### 5. Phase 4: Viral Title Generation
- **Purpose**: Provide actionable video ideas for verified gaps.
- **Method**: Generates 3 viral-optimized titles per gap, calculating an "Influence Score" based on comment demand, competitor coverage, and trend momentum.

---

## The "Premium" Skills (`railway-api/premium/`)

The system is built around 7 core analytical skills implemented as modular Python classes:

1.  **`enhanced_gap_analyzer.py`**: The main logic for multi-signal gap discovery.
2.  **`satisfaction_analyzer.py`**: Infers audience satisfaction from engagement patterns and sentiment depth.
3.  **`growth_pattern_analyzer.py`**: Analyzes what topics and series drive the most subscribers.
4.  **`hook_analyzer.py`**: Analyzes video intro transcripts to evaluate "hook strength".
5.  **`thumbnail_optimizer.py` / `visual_analyzer.py`**: Analyzes thumbnail colors, faces, and text density using AI vision.
6.  **`market_intelligence.py`**: Benchmarks against competitors and monitors niche-wide trends.
7.  **`publish_optimizer.py`**: Uses historical performance data to suggest optimal upload days and times.

---

## Machine Learning Models (`railway-api/premium/ml_models/`)

The backend utilizes several specialized ML models for predictive analytics:

- **`viral_predictor.py`**: Predicts the likelihood of a video going viral based on title, topic, and historical performance.
- **`ctr_predictor.py`**: Estimates the Click-Through Rate proxy based on visual and metadata signals.
- **`sentiment_engine.py`**: Fine-tuned transformer for YouTube-specific sentiment and category classification.
- **`content_clusterer.py`**: Semantic clustering of video topics using embeddings.

---

## Supabase Integration

- **Authentication**: Uses Supabase Auth for user management.
- **Database**:
    - `analyses` table: Stores report metadata, status, and the final JSON result.
    - `embeddings` logic: Used for semantic search and content clustering.
- **Implementation**: Uses direct `requests` to Supabase REST endpoints to avoid heavy library dependencies in the Railway environment.
