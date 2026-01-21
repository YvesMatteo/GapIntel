# User Objective
**Upgrade Scientific Models to v2 (Quality Features)**

The goal is to enable the ML models to predict video performance on *unseen* data (like new video ideas) by analyzing the *quality* of the creative assets, not just metadata.

## Core Requirements
1.  **Title Embeddings:** Replace simple heuristic features (length, "?") with semantic embeddings (e.g., using a small BERT model or TF-IDF/Word2Vec if lightweight). The model should understand "Minecraft Speedrun" vs "Minecraft Tutorial".
2.  **Thumbnail Integration:** Feed extracted thumbnail features (colors, face count, text density, etc.) into the training pipeline.
3.  **Strictly Scientific:** No heuristic "hooks" (e.g., `if '?' in title: score += 10`). The model must *learn* if questions work for that specific niche.
4.  **Integration:** Update `scientific_trainer.py` to process these new features and `inference_engine.py` to generate them at runtime.

## Success Criteria
- [ ] `ScientificTrainer` processes text embeddings and thumbnail vectors.
- [ ] XGBoost models are retrained with these "Quality Features".
- [ ] `ViralPredictor` can predict a view count for a *new* idea (Title + Thumbnail) that is statistically grounded.
- [ ] Verification script proves the model differentiates between two titles for the same topic based on semantic quality.
