# Viral Title Predictor v2.0 - Complete Rework

## Objective
Completely rework the Viral Title Predictor to use **Gemini 2.5 Flash** as the core AI engine, following the scientific methodology defined in the RAG document (`@.agent/knowledge/YouTube_View_Prediction_RAG`).

## Problem Statement
The current implementation is fundamentally flawed:
1. **Alternative titles** are generated from hardcoded templates - always the same patterns
2. **Hook scores** are arbitrary regex-based pattern matching with made-up CTR boosts
3. **No thumbnail analysis** capability despite thumbnails being 25-30% of view prediction
4. **Viral scores** don't follow any validated methodology
5. **ML predictions** show "0" because models aren't properly trained/connected

## Success Criteria
- [ ] Gemini 2.5 Flash analyzes ALL inputs (thumbnail, title, hook)
- [ ] Thumbnail upload functionality works seamlessly
- [ ] Predictions follow the RAG document's formulas and weightings
- [ ] Alternative titles are AI-generated (unique, contextual, no templates)
- [ ] Confidence intervals are properly calculated (±30-70%)
- [ ] Output matches the RAG document's output template format

## Core Requirements

### 1. Input System (Frontend)
- **Thumbnail Upload**: Image upload with preview
- **Video Title**: Text input (50-70 chars optimal)
- **Opening Hook**: First sentence/hook text
- **Channel Size**: Dropdown (Nano/Micro/Small/Large/Mega per RAG)
- **Niche Selection**: Gaming/Education/Entertainment/Tech/Review/Finance/Vlog

### 2. Gemini 2.5 Flash Integration
Single API call to Gemini with multi-modal input:
- Thumbnail image (if provided)
- Title text
- Hook text
- Channel context

Gemini should output structured JSON following RAG scoring rubrics:
- Thumbnail Quality Score (0-10) with CTR Impact
- Hook Quality Score (0-10) with AVD Impact
- Title Quality Score (0-10) with CTR Impact
- Psychological triggers detected
- Optimization recommendations

### 3. View Prediction Formula (From RAG)
```
PREDICTED_VIEWS = (IMPRESSIONS × CTR%) × AVD_FACTOR × NICHE_FACTOR × CHANNEL_FACTOR × ALGORITHMIC_BOOST
```

### 4. Output Display
Match RAG document's output template:
- Component Analysis (Thumbnail, Hook, Title scores)
- Predicted Performance (views, CTR, AVD, confidence interval)
- Optimization Recommendations
- Benchmark Comparison (vs niche average)
- Risk Factors

## Technical Constraints
- **API**: Gemini 2.5 Flash (cost-effective, fast, multi-modal)
- **Frontend**: Next.js 14 (existing stack)
- **Backend**: FastAPI (existing stack)
- **Image Handling**: Base64 encoding for Gemini API

## Out of Scope
- Training custom ML models
- Historical video analysis (use channel size as proxy)
- Video content analysis (only thumbnail, title, hook)
