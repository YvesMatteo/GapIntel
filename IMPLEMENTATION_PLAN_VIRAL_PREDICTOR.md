# Implementation Plan: Viral Title Predictor v2.0

## Overview
Complete rework of the Viral Title Predictor using Gemini 2.5 Flash and the scientific RAG methodology.

---

## Phase 1: Backend - Gemini Integration

### Task 1.1: Create Gemini Viral Analyzer Module
**File**: `/railway-api/premium/ml_models/gemini_viral_analyzer.py`
**Status**: [x] COMPLETED

Create a new Python module that:
- Accepts thumbnail (base64), title, hook, channel_size, niche
- Constructs a comprehensive prompt using RAG document methodology
- Calls Gemini 2.5 Flash API with multi-modal input
- Parses structured JSON response
- Calculates final view prediction using RAG formulas

**Key Functions**:
```python
class GeminiViralAnalyzer:
    async def analyze(
        self,
        title: str,
        hook: str,
        niche: str,
        channel_size: str,
        thumbnail_base64: Optional[str] = None
    ) -> ViralAnalysisResult

    def _build_analysis_prompt(self) -> str  # RAG-based prompt
    def _calculate_predicted_views(self, scores: dict) -> ViewPrediction
    def _generate_recommendations(self, analysis: dict) -> List[str]
```

**Notes**:
- Use RAG scoring rubrics verbatim in prompt
- Include niche-specific benchmarks from RAG
- Return structured ViralAnalysisResult dataclass

---

### Task 1.2: Create New API Endpoint
**File**: `/railway-api/server.py`
**Status**: [x] COMPLETED

Create `POST /api/v2/predict-viral`:
```python
@app.post("/api/v2/predict-viral")
async def predict_viral_v2(
    title: str = Form(...),
    hook: str = Form(None),
    niche: str = Form(...),
    channel_size: str = Form(...),
    thumbnail: UploadFile = File(None)
):
    # 1. Convert thumbnail to base64 if provided
    # 2. Call GeminiViralAnalyzer.analyze()
    # 3. Return comprehensive prediction
```

**Response Schema**:
```json
{
  "video_details": {
    "title": "string",
    "niche": "string",
    "niche_confidence": "float",
    "channel_size": "string",
    "channel_multiplier": "float"
  },
  "component_analysis": {
    "thumbnail": {
      "score": "float (0-10)",
      "ctr_impact": "string (+X%)",
      "visual_contrast": "float",
      "face_presence": "float",
      "emotion_intensity": "float",
      "text_readability": "float",
      "color_vibrancy": "float",
      "alignment_with_content": "float"
    },
    "hook": {
      "score": "float (0-10)",
      "avd_impact": "string (+X%)",
      "information_gap": "float",
      "emotional_authenticity": "float",
      "open_loop_clarity": "float",
      "personal_relevance": "float",
      "value_proposition": "float",
      "processing_ease": "float",
      "psychological_triggers": ["string"]
    },
    "title": {
      "score": "float (0-10)",
      "ctr_impact": "string (+X%)",
      "specificity": "float",
      "number_inclusion": "float",
      "curiosity_words": "float",
      "personal_pronoun": "float",
      "keyword_relevance": "float",
      "title_hook_coherence": "float"
    }
  },
  "predicted_performance": {
    "predicted_views": "int",
    "confidence_interval": "string (±X%)",
    "view_range": {"low": "int", "high": "int"},
    "predicted_ctr": "string (X%)",
    "predicted_avd": "string (X%)",
    "phase_1_success_index": "float (0-10)"
  },
  "optimization_recommendations": {
    "thumbnail": ["string"],
    "hook": ["string"],
    "title": ["string"],
    "strategy": ["string"]
  },
  "alternative_titles": [
    {"title": "string", "hook_type": "string", "expected_ctr_boost": "string"}
  ],
  "benchmark_comparison": {
    "vs_niche_average": "string (+X% or -X%)",
    "vs_channel_typical": "string",
    "competitive_positioning": "string (Strong/Average/Below Average)"
  },
  "risk_factors": {
    "click_to_content_mismatch": "string (Low/Medium/High)",
    "saturation_risk": "string",
    "algorithmic_risk": "string"
  }
}
```

---

### Task 1.3: Environment Setup
**Status**: [x] COMPLETED (google-generativeai already in requirements.txt)

- Add `GEMINI_API_KEY` to Railway environment variables
- Add `google-generativeai` to requirements.txt
- Test Gemini 2.5 Flash model availability

---

## Phase 2: Frontend - Complete UI Rework

### Task 2.1: Create Image Upload Component
**File**: `/gap-intel-website/src/components/ThumbnailUpload.tsx`
**Status**: [x] COMPLETED

Features:
- Drag-and-drop support
- Click to upload
- Image preview with remove button
- File size validation (max 5MB)
- File type validation (JPEG, PNG, WebP)
- Responsive design matching existing UI

---

### Task 2.2: Update Viral Predictor Page
**File**: `/gap-intel-website/src/app/viral-predictor/page.tsx`
**Status**: [x] COMPLETED - Complete rewrite with dark theme, Gemini integration

Complete rewrite:
1. **Input Section**:
   - Thumbnail upload (NEW)
   - Video Title input (keep, add char counter)
   - Opening Hook textarea (keep)
   - Channel Size dropdown (update options to RAG categories)
   - Niche dropdown (update to RAG's 7 niches)

2. **Results Section** (match RAG output template):
   - Hero card: Overall viral score (0-100) with confidence interval
   - Component Analysis cards (Thumbnail, Hook, Title - each with 6 sub-scores)
   - Predicted Performance box (views, CTR, AVD)
   - Optimization Recommendations (expandable)
   - Alternative Titles (AI-generated, unique)
   - Benchmark Comparison
   - Risk Factors

3. **Loading State**:
   - Shimmer/skeleton while Gemini processes (~2-3 seconds)

4. **Error Handling**:
   - Graceful degradation if no thumbnail provided
   - Clear error messages

---

### Task 2.3: Remove Legacy Code
**Status**: [x] COMPLETED - Old titleAnalyzer.ts no longer used by new page

Delete or archive:
- `/gap-intel-website/src/lib/titleAnalyzer.ts` (replace with Gemini)
- Old heuristic functions in page.tsx
- Hardcoded hook patterns and CTR boosts

---

### Task 2.4: Update API Client
**File**: `/gap-intel-website/src/lib/api.ts` (or create new)
**Status**: [ ] Not Started

Create typed API client:
```typescript
interface ViralPredictionRequest {
  title: string;
  hook?: string;
  niche: string;
  channel_size: string;
  thumbnail?: File;
}

async function predictViral(request: ViralPredictionRequest): Promise<ViralAnalysisResult>
```

---

## Phase 3: Gemini Prompt Engineering

### Task 3.1: Create RAG-Based Analysis Prompt
**Status**: [x] COMPLETED - Embedded in GeminiViralAnalyzer._build_analysis_prompt()

The Gemini prompt must include:
1. Full scoring rubrics from RAG document
2. Niche-specific benchmarks
3. Channel size multipliers
4. Psychological trigger framework
5. Output schema (JSON)

**Prompt Structure**:
```
You are a YouTube video performance analyst. Analyze the provided content using the following scientific framework:

[THUMBNAIL ANALYSIS FRAMEWORK - from RAG Section 4]
[HOOK ANALYSIS FRAMEWORK - from RAG Section 5]
[TITLE ANALYSIS FRAMEWORK - from RAG Section 2.3]
[NICHE BENCHMARKS - from RAG Section 6]
[CHANNEL SIZE MULTIPLIERS - from RAG Section 7]

Input:
- Thumbnail: [image if provided]
- Title: {title}
- Hook: {hook}
- Niche: {niche}
- Channel Size: {channel_size}

Provide your analysis as valid JSON following this exact schema:
{schema}
```

---

### Task 3.2: Alternative Title Generation Prompt
**Status**: [ ] Not Started

Separate prompt for generating 3-5 unique alternative titles:
- Must use different hook types (Number, How-To, Question, Curiosity Gap)
- Contextually relevant to original title topic
- Estimate CTR boost for each
- NO templates, fully AI-generated

---

## Phase 4: Testing & Polish

### Task 4.1: Backend Testing
**Status**: [ ] Not Started

- Test Gemini API integration
- Test image upload handling
- Test rate limiting / error handling
- Test with various niches and channel sizes

---

### Task 4.2: Frontend Testing
**Status**: [ ] Not Started

- Test thumbnail upload UX
- Test responsive design
- Test loading states
- Test error states

---

### Task 4.3: End-to-End Testing
**Status**: [ ] Not Started

- Full flow: upload thumbnail, enter title/hook, get prediction
- Compare predictions with RAG benchmarks
- Verify alternative titles are unique and contextual

---

## Phase 5: Deployment

### Task 5.1: Deploy Backend
**Status**: [ ] Not Started

- Push to Railway
- Verify Gemini API key is set
- Test production endpoint

---

### Task 5.2: Deploy Frontend
**Status**: [ ] Not Started

- Build and deploy
- Test production flow
- Monitor for errors

---

## Task Priority Order

1. **Task 1.3** - Environment setup (Gemini API key)
2. **Task 1.1** - Gemini Viral Analyzer module
3. **Task 3.1** - RAG-based prompt engineering
4. **Task 1.2** - New API endpoint
5. **Task 2.1** - Thumbnail upload component
6. **Task 2.2** - Viral predictor page rewrite
7. **Task 2.3** - Remove legacy code
8. **Task 2.4** - API client
9. **Task 3.2** - Alternative title generation
10. **Task 4.x** - Testing
11. **Task 5.x** - Deployment

---

## Notes

- The RAG document provides exact formulas and benchmarks - follow them precisely
- Gemini 2.5 Flash is cost-effective (~$0.0001 per request)
- Keep old `/api/predict-video` endpoint for backward compatibility initially
- The new endpoint is `/api/v2/predict-viral`

---

## Dependencies

- `google-generativeai` Python package
- Gemini 2.5 Flash API access
- Frontend: No new dependencies (use native File API)

---

## Estimated Effort

| Phase | Estimated Time |
|-------|---------------|
| Phase 1 (Backend) | 2-3 hours |
| Phase 2 (Frontend) | 3-4 hours |
| Phase 3 (Prompts) | 1-2 hours |
| Phase 4 (Testing) | 1-2 hours |
| Phase 5 (Deploy) | 30 minutes |

**Total**: ~8-12 hours
