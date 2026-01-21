"""
Verify Optimization Scorer
==========================

Runs the OptimizationScorer on a sample of real videos from training data
to verify the recommendations and detailed breakdowns.
"""

import os
import sys
import json
import pandas as pd
from typing import Dict, List

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
premium_dir = os.path.dirname(current_dir)
railway_dir = os.path.dirname(premium_dir)
if railway_dir not in sys.path:
    sys.path.insert(0, railway_dir)

from premium.ml_models.optimization_scorer import OptimizationScorer

def load_sample_data(limit=20):
    possible_paths = [
       os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), 'training_data'),
        '/Users/yvesromano/AiRAG/training_data',
    ]
    
    data = []
    for path in possible_paths:
        if os.path.exists(path):
            for f in os.listdir(path):
                if f.endswith('.json'):
                    with open(os.path.join(path, f)) as fp:
                        batch = json.load(fp)
                        data.extend(batch)
                        if len(data) >= limit:
                            return data[:limit]
    return data

def load_thumb_cache():
    path = os.path.join(current_dir, 'thumbnail_features_cache.json')
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

def run_verification():
    print("="*60)
    print("Optimization Scorer Verification")
    print("="*60)

    videos = load_sample_data(20)
    thumb_cache = load_thumb_cache()
    scorer = OptimizationScorer()

    print(f"Loaded {len(videos)} videos for testing.")

    for i, vid in enumerate(videos):
        vid_id = vid.get('video_id')
        title = vid.get('title', "No Title")
        
        # Get thumbnail features if cached
        thumb_feats = {}
        if vid_id in thumb_cache:
            # Prefix correction: cache keys don't have 'thumb_' prefix usually, 
            # but scorer expects features dict. Let's map them.
            # Cache format in improved_predictor was just dict of features.
            # Scorer's `score_thumbnail` looks for keys like 'thumb_contrast_score'.
            # I need to ensure keys match what scorer expects.
            
            # Let's see what keys are in cache by printing one if needed.
            # Based on evaluate_with_thumbnails.py, cache keys are like 'contrast_score', 
            # 'rag_total_score' etc.
            # The scorer looks for `thumb_contrast_score`. 
            # So I should prefix them.
            
            raw_feats = thumb_cache[vid_id]
            thumb_feats = {f"thumb_{k}": v for k, v in raw_feats.items()}
        
        result = scorer.evaluate(title, thumb_feats)
        
        print(f"\nVideo {i+1}: {title[:50]}...")
        print(f"  Score: {result.total_score:.1f} ({result.rating})")
        print(f"  Title Score: {result.title_score:.1f} | Thumb Score: {result.thumbnail_score:.1f}")
        
        if result.positive_factors:
            print(f"  ✅ Pros: {', '.join(result.positive_factors[:3])}")
        
        if result.recommendations:
            print(f"  ⚠️ Recs: {', '.join(result.recommendations[:3])}")

if __name__ == "__main__":
    run_verification()
