"""
Scientific Inference Engine
---------------------------
Loads trained XGBoost models to provide scientific predictions.
Used by GAP_ULTIMATE and scoring_engine to replace heuristics.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Scientific V2 Imports
import sys
import os

# Script path: railway-api/premium/ml_models/inference_engine.py
# We want to add 'railway-api' to sys.path to allow 'from premium...' imports
current_dir = os.path.dirname(os.path.abspath(__file__)) 
premium_dir = os.path.dirname(current_dir)
railway_api_dir = os.path.dirname(premium_dir)

if railway_api_dir not in sys.path:
    sys.path.append(railway_api_dir)

try:
    from premium.ml_models.text_embedder import TextEmbedder
    HAS_V2_MODULES = True
except ImportError:
    try:
         from .text_embedder import TextEmbedder
         HAS_V2_MODULES = True
    except:
         logger.warning("V2 Modules not found in inference engine.")
         HAS_V2_MODULES = False

class ScientificInference:
    def __init__(self, models_dir: str = "railway-api/premium/ml_models/trained"):
        self.models_dir = models_dir
        self.models = {} # Cache
        self.niche_map = {} # Map niche names to filenames
        self.embedder = None
        if HAS_V2_MODULES:
            try:
                self.embedder = TextEmbedder() # Uses OpenAI by default now
            except:
                pass
        self._load_available_models()
        
    def _load_available_models(self):
        """Scan directory and index available models."""
        if not os.path.exists(self.models_dir):
            logger.warning(f"Models directory not found: {self.models_dir}")
            return
            
        for filename in os.listdir(self.models_dir):
            if filename.endswith(".joblib") and filename.startswith("benchmark_"):
                # Extract niche slug from benchmark_{slug}.joblib
                slug = filename.replace("benchmark_", "").replace(".joblib", "")
                self.niche_map[slug] = filename
                
        logger.info(f"Indexed {len(self.niche_map)} scientific models.")

    def get_model(self, niche: str):
        """Lazy load model for a niche."""
        # Normalize niche name to slug
        slug = niche.lower().replace(" & ", "_").replace(" ", "_").replace("/", "_")
        
        # Fallback for exact matches not found (e.g. unknown niche -> generic?)
        # For now, just try to find best match or return None
        if slug not in self.niche_map:
            # Try to find partial match
            for s in self.niche_map:
                if s in slug or slug in s:
                    slug = s
                    break
        
        if slug not in self.niche_map:
            return None
            
        # load if not cached
        if slug not in self.models:
            path = os.path.join(self.models_dir, self.niche_map[slug])
            try:
                self.models[slug] = joblib.load(path)
            except Exception as e:
                logger.error(f"Failed to load model {slug}: {e}")
                return None
                
        return self.models[slug]

    def predict_expected_views(self, niche: str, video_metadata: Dict, channel_stats: Dict, thumbnail_features: Dict = None) -> Dict:
        """
        Predict 'Expected Views' given metadata, channel stats, and optional visual features.
        """
        """
        Predict 'Expected Views' for a video given its metadata and channel stats.
        Returns prediction and confidence/error margins.
        """
        model_bundle = self.get_model(niche)
        if not model_bundle:
            return {"error": "No model for niche", "is_scientific": False}
        
        model = model_bundle['model']
        scaler = model_bundle['scaler']
        model = model_bundle['model']
        scaler = model_bundle['scaler']
        feature_cols = model_bundle['features']
        pca = model_bundle.get('pca') # Optional PCA model for embeddings
        
        # Prepare Features
        # Must match training time preprocessing exactly
        
        # Duration
        duration = video_metadata.get('duration_seconds', 0)
        
        # Title features
        title = video_metadata.get('title', "")
        title_length = len(title)
        title_has_question = 1 if '?' in title else 0
        title_has_number = 1 if any(c.isdigit() for c in title) else 0
        
        # Tags
        tags = video_metadata.get('tags', [])
        tags_count = len(tags)
        
        # Channel Stats (Subscriber Count Log)
        # Use median views if subs not available, or log(subs)
        # Training used log1p(channel_median_views) as 'subscriber_count_log' proxy
        # Here we should use the same proxy if possible, or mapping real subs -> views proxy
        # Since we don't have the "channel median" at inference time easily without history,
        # we will use log1p(avg_views_last_30_videos) which is passed in channel_stats.
        avg_views = channel_stats.get('view_average', 0)
        if avg_views == 0:
             # Fallback to subs if avg views not available, but scale might be off
             # Training data: log(views). Real subs >> views usually.
             # We should probably use log(subs / 10) as rough heuristic for 'expected views'
             # Or better: just use log(subs) but acknowledge model might be slightly skewed.
             # Ideally training should used real subs.
             
             # For this V1, let's use avg_views if available.
             avg_views = channel_stats.get('subscriber_count', 1000) * 0.1 # 10% assumption
             
        subscriber_count_log = np.log1p(avg_views)
        
        # Create input vector
        # MATCHING TRAINING ORDER EXACTLY:
        # ['duration_seconds', 'title_length', 'title_has_question', 
        #  'title_has_number', 'tags_count', 'subscriber_count_log']
        
        input_vector = [
            duration,
            title_length,
            title_has_question,
            title_has_number,
            tags_count,
            subscriber_count_log
        ]
        
        # === V2 Feature Extension ===
        
        # 1. Add Thumbnail Features (if model expects them)
        # We check 'feature_cols' to see what the model was trained on.
        # This makes it backward compatible with V1 models (which won't have thumb_ cols)
        
        # We construct a dict of avail features first
        avail_features = {
            'duration_seconds': duration,
            'title_length': title_length,
            'title_has_question': title_has_question,
            'title_has_number': title_has_number,
            'tags_count': tags_count,
            'subscriber_count_log': subscriber_count_log
        }
        
        # Add visual features to avail_features
        if thumbnail_features:
            for k, v in thumbnail_features.items():
                if isinstance(v, (int, float, bool)):
                     avail_features[f'thumb_{k}'] = float(v)
        
        # Re-build input vector based on model's feature_cols
        # This handles dynamic V2 features order
        final_input_vector = []
        embedding_cols_indices = [] # Track where embeddings go
        
        for i, col in enumerate(feature_cols):
            if col.startswith('emb_'):
                # Handle embeddings separately (need PCA)
                embedding_cols_indices.append((i, col))
                final_input_vector.append(0.0) # Placeholder
            else:
                final_input_vector.append(avail_features.get(col, 0.0))
        
        # 2. Add Embeddings (if model needs them)
        if embedding_cols_indices and self.embedder:
            try:
                # Generate embedding
                emb_vector = self.embedder.embed(title) # (1536,)
                
                # Apply PCA if available
                if pca:
                    emb_reduced = pca.transform(emb_vector.reshape(1, -1))[0] # (20,)
                    
                    # Fill placeholders
                    # Assuming emb_0, emb_1... correspond to pca components 0, 1...
                    for idx, col_name in embedding_cols_indices:
                        comp_idx = int(col_name.split('_')[1])
                        if comp_idx < len(emb_reduced):
                            final_input_vector[idx] = emb_reduced[comp_idx]
            except Exception as e:
                logger.error(f"Embedding/PCA failed at inference: {e}")

        # Scale
        X = np.array(final_input_vector).reshape(1, -1)
        X_scaled = scaler.transform(X)
        
        # Predict
        log_pred = model.predict(X_scaled)[0]
        expected_views = np.expm1(log_pred)
        
        return {
            "expected_views": int(expected_views),
            "log_prediction": float(log_pred),
            "is_scientific": True,
            "niche_used": niche
        }

    def calculate_viral_uplift(self, actual_views: int, expected_views: int) -> float:
        """
        Calculate viral uplift score (multiplier).
        1.0 = performed exactly as expected.
        2.0 = 2x better than expected.
        """
        if expected_views < 10: return 1.0
        return actual_views / expected_views

# Semantic helper for niche detection (simple keyword match for now)
NICHE_KEYWORDS = {
    "Gaming": ["game", "play", "minecraft", "roblox", "fortnite", "ps5", "xbox"],
    "Technology & Software": ["tech", "review", "iphone", "samsung", "code", "programming", "tutorial", "software", "ai"],
    "Finance & Business": ["money", "crypto", "stock", "invest", "wealth", "business", "entrepreneur"],
    "Education & Science": ["science", "history", "math", "physics", "learn", "study", "analysis"],
    # ... extensible
}

def detect_niche(text: str) -> str:
    """Best-effort niche detection from text (title/description)."""
    text = text.lower()
    scores = {n: 0 for n in NICHE_KEYWORDS}
    
    for niche, keywords in NICHE_KEYWORDS.items():
        for k in keywords:
            if k in text:
                scores[niche] += 1
    
    # Return best match or default
    best = max(scores.items(), key=lambda x: x[1])
    if best[1] > 0:
        return best[0]
    return "Lifestyle & Vlogs" # Default fallback
