"""
Premium Analysis - ML Viral Predictor
Predicts viral potential of video ideas based on channel history and content patterns.
Updated to use Scientific XGBoost Models.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np
import math

@dataclass
class ViralPrediction:
    predicted_views: int
    viral_probability: float  # 0-1
    confidence_score: float   # 0-1
    factors: Dict[str, float] # Contribution of each factor
    tips: List[str]
    is_heuristic: bool = False # Whether prediction used fallback logic

# Import Scientific Inference Engine
try:
    # Try relative import (standard for package execution)
    from .inference_engine import ScientificInference, detect_niche
    scientific_inference = ScientificInference()
    HAS_SCIENTIFIC = True
except ImportError:
    try:
        # Fallback for direct script execution or different path contexts
        from premium.ml_models.inference_engine import ScientificInference, detect_niche
        scientific_inference = ScientificInference()
        HAS_SCIENTIFIC = True
    except ImportError:
        print("⚠️ Scientific Inference Engine not found. Falling back to heuristics.")
        HAS_SCIENTIFIC = False
        scientific_inference = None

class ViralPredictor:
    def __init__(self):
        self.inference_engine = scientific_inference

    def predict(self, 
                title: str, 
                hook_text: str,
                topic: str,
                channel_history: List[Dict],
                thumbnail_features: Optional[Dict] = None) -> 'ViralPrediction':
        """
        Predict viral potential using Scientific ML Models.
        """
        # Calculate channel stats for baseline
        if not channel_history:
            avg_views = 10000
            median_views = 5000
        else:
            views = [v.get('view_count', 0) for v in channel_history]
            avg_views = np.mean(views) if views else 10000
            median_views = np.median(views) if views else 5000
            
        # === SCIENTIFIC MODEL PATH ===
        if self.inference_engine:
            try:
                # 1. Detect Niche
                # Combine title and topic for better context
                niche = detect_niche(f"{title} {topic}")
                
                # 2. Extract Channel Context
                # The inference engine expects 'view_average' etc
                channel_stats = {
                    'view_average': avg_views,
                    'median_views': median_views,
                    'subscriber_count': median_views * 10, # Rough proxy if unknown
                    'video_count': len(channel_history)
                }
                
                # 3. Predict Expected Views
                video_metadata = {
                    'title': title,
                    'duration_seconds': 600, # Default to 10m
                    'tags': [] 
                }
                
                prediction = self.inference_engine.predict_expected_views(
                    niche=niche,
                    video_metadata=video_metadata,
                    channel_stats=channel_stats
                )
                
                expected_views = prediction.get('expected_views', 0)
                
                # 4. Calculate Viral Probability (Uplift)
                # If Expected > Median, probability increases
                uplift = 0
                if median_views > 0:
                    uplift = expected_views / median_views
                
                # Log-sigmoid mapping
                # uplift=1.0 -> 0.0 log -> 0.5 prob
                # uplift=2.0 -> 1.0 log -> ~0.8 prob
                def sigmoid(x):
                  return 1 / (1 + math.exp(-x))
                
                viral_prob = sigmoid(math.log2(max(uplift, 0.1)) * 1.5)
                
                # Adjust for Hook (Heuristic override on top of Scientific Model)
                hook_score = self._analyze_hook(hook_text)
                
                # Weighted blend: 70% Scientific, 30% Hook
                final_prob = (viral_prob * 0.7) + (hook_score * 0.3)
                
                tips = []
                if uplift < 0.8:
                    tips.append(f"Topic '{niche}' typically underperforms for this channel size.")
                if hook_score < 0.5:
                    tips.append("Hook is weak - add curiosity or urgency.")
                if final_prob > 0.8:
                    tips.append("Strong viral potential detected!")
                    
                return ViralPrediction(
                    predicted_views=int(expected_views),
                    viral_probability=round(final_prob, 2),
                    confidence_score=0.85, # ML confidence
                    factors={
                        'ml_uplift': round(uplift, 2),
                        'hook_strength': round(hook_score, 2),
                        'niche_baseline': int(median_views)
                    },
                    tips=tips,
                    is_heuristic=False
                )
                
            except Exception as e:
                print(f"⚠️ Scientific prediction failed: {e}")
                # Fallthrough to heuristic

        # === HEURISTIC FALLBACK (Legacy) ===
        return self._heuristic_fallback(title, hook_text, avg_views)

    def _heuristic_fallback(self, title, hook, avg_views) -> ViralPrediction:
        """Legacy heuristic logic."""
        hook_score = self._analyze_hook(hook)
        title_score = 0.5 + (0.1 if len(title) > 20 else 0)
        prob = (hook_score + title_score) / 2
        return ViralPrediction(
            predicted_views=int(avg_views * prob * 1.5),
            viral_probability=round(prob, 2),
            confidence_score=0.4,
            factors={'heuristic': True},
            tips=["Using heuristic fallback - install ML models for better accuracy."],
            is_heuristic=True
        )

    def _analyze_hook(self, hook: str) -> float:
        score = 0.5
        hook_lower = hook.lower()
        if '?' in hook: score += 0.1
        if any(w in hook_lower for w in ['you', 'your', 'i', 'my']): score += 0.1
        if any(w in hook_lower for w in ['secret', 'know', 'never', 'stop']): score += 0.1
        return min(score, 1.0)
