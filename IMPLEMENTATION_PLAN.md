# Scientific Model v2 Upgrade Plan

## Goal
Upgrade the view prediction model from a simple metadata baseline (v1) to a "Quality-Aware" model (v2) that can predict performance on **unseen video ideas** by analyzing the semantic quality of the Title and the visual patterns of the Thumbnail.

## User Review Required
> [!IMPORTANT]
> **dependency addition**: We will add `sentence-transformers` to `requirements.txt`.
> **Note**: `torch` is likely already present due to `openai-whisper`, so the slug size impact should be manageable (~80MB for the model).

## Proposed Changes

### 1. Data Engineering Layer

#### [MODIFY] `data_collector_v2.py`
- Integrate `ThumbnailFeatureExtractor`.
- For every video fetched, download the thumbnail (in memory) and extract the 50+ visual features.
- Save these features into the JSON dataset.

### 2. Feature Engineering Layer

#### [NEW] `text_embedder.py`
- Create a lightweight service class `TextEmbedder`.
- Use `sentence-transformers/all-MiniLM-L6-v2` (fast, 384 dimensions).
- Implement caching to avoid re-computing common words/phrases if needed.

### 3. Training Pipeline

#### [MODIFY] `scientific_trainer.py`
- **Update Features**: Add `thumbnail_*` columns and `title_embedding_*` vector columns to the training set.
- **Dimensionality Reduction (Optional)**: If 384 dimensions is too much for 1000 samples, use PCA to reduce text embeddings to ~20 components.
- **Model**: Keep XGBoost but retrain with the expanded feature set.

### 4. Inference Engine

#### [MODIFY] `inference_engine.py`
- Initialize `TextEmbedder` and `ThumbnailFeatureExtractor`.
- Update `predict_expected_views` to accept a `thumbnail_url` or `thumbnail_path`.
- Generate features on-the-fly for new predictions.

## Verification Plan

### Automated Tests
1. **`tests/test_scientific_v2.py`**:
   - **Semantic Test**: Feed two titles to the model: "Gaming Video 1" vs "MINECRAFT MANHUNT VS SPEEDRUNNER (INSANE)". Verify the model predicts higher views for the clearer, more exciting title (assuming the niche prefers it).
   - **Visual Test**: Feed a black square vs a bright, high-contrast thumbnail. Verify the model reacts to the visual difference.

### Manual Verification
- Run `inference_engine.py` manually with a real YouTube URL and see if the "Predicted Views" aligns with reality better than the v1 baseline.
