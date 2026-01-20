# Implementation Plan

## Status
- [x] Planning
- [ ] In Progress
- [ ] Verification
- [ ] Complete

## Task List

### Phase 1: Comprehensive Code Review (Scientific Purity)
- [x] Review `premium/ml_models/viral_predictor.py` for residual heuristics. (Clean)
- [x] Review `premium/ml_models/views_predictor.py` for residual heuristics. (Clean, uses Decay Curves)
- [x] Review `premium/ml_models/ctr_predictor.py` for residual heuristics. (Clean, Falls back gracefully)
- [x] Review `premium/ml_models/sentiment_engine.py` for residual heuristics. (Uses Prototype Embeddings, falls back to Rules if Env missing)
- [x] Review `GAP_ULTIMATE.py` pipeline flow. (Uses ML predictors)

### Phase 2: Requirements Compilation
- [ ] Explicitly add `transformers`, `torch` to `requirements.txt` to ensure ML path activates.
- [ ] Scan text for 'TODO' or 'Require' in codebase to identify User Dependencies.
- [ ] Check SQL migrations (`supabase/migrations/`) for required table setups.
- [ ] Check `.env` usage for required keys.
- [ ] Create `REQUIREMENTS_LIST.md` with executable SQL and instructions.

### Phase 3: Final Verification
- [x] Run `python3 tests/verify_scientific_validity.py`. (PASSED)

## Notes & Findings
- 2026-01-20: Initialized Ralph Loop. Building on top of recent "Scientific Validity Overhaul".
- 2026-01-20: `SentimentEngine` requires `transformers` and `torch` to avoid fallback. Added to `REQUIREMENTS_LIST.md`.
- 2026-01-20: Compiled `REQUIREMENTS_LIST.md` with SQL for `ctr_training_data`.
- 2026-01-20: All tests passed. System is scientifically robust and handled fallbacks gracefully.

### Phase 3: Final Verification
- [ ] Run `python3 tests/verify_scientific_validity.py`.

## Notes & Findings
- 2026-01-20: Initialized Ralph Loop. Building on top of recent "Scientific Validity Overhaul".
