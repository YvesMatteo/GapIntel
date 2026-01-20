"""
Premium Analysis - ML Viral Predictor
Predicts viral potential of video ideas based on channel history and content patterns.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np
import os

# Try to import supervised model
try:
    # Try absolute import (works when run from root)
    from premium.ml_models.supervised_viral_predictor import SupervisedViralPredictor
except ImportError:
    try:
        # Try relative import
        from .supervised_viral_predictor import SupervisedViralPredictor
    except ImportError:
        SupervisedViralPredictor = None

@dataclass
class ViralPrediction:
    predicted_views: int
    viral_probability: float  # 0-1
    confidence_score: float   # 0-1
    factors: Dict[str, float] # Contribution of each factor
    tips: List[str]
    is_heuristic: bool = False # Whether prediction used fallback logic

class ViralPredictor:
    def __init__(self):
        # Weights removed - we now strictly prefer the supervised model
        self.weights = None
        
        # Initialize supervised model if available
        self.supervised_model = None
        if SupervisedViralPredictor:
            try:
                self.supervised_model = SupervisedViralPredictor()
                if not self.supervised_model.model:
                    self.supervised_model = None # Model file not found/loaded
            except Exception as e:
                print(f"⚠️ Could not initialize supervised viral predictor: {e}")

    def predict(self, 
                title: str, 
                hook_text: str,
                topic: str,
                channel_history: List[Dict],
                thumbnail_features: Optional[Dict] = None) -> 'ViralPrediction':
        """
        Predict viral potential of a video idea.
        
        Args:
            title: Proposed video title
            hook_text: Proposed hook script
            topic: Video topic/category
            channel_history: List of past videos with view counts
            thumbnail_features: Optional dictionary of thumbnail features
            
        Returns:
            ViralPrediction object
        """
        # Calculate baselines from history
        if not channel_history:
            avg_views = 10000
            median_views = 5000
            max_views = 50000
        else:
            views = [v.get('view_count', 0) for v in channel_history]
            avg_views = np.mean(views) if views else 10000
            median_views = np.median(views) if views else 5000
            max_views = max(views) if views else 50000

        # === SUPERVISED MODEL PATH ===
        if self.supervised_model:
            try:
                result = self.supervised_model.predict(
                    title=title,
                    channel_median_views=median_views,
                    thumbnail_features=thumbnail_features
                )
                
                if result:
                    # Combine with heuristic hook analysis
                    hook_score = self._analyze_hook(hook_text)
                    
                    final_prob = result.viral_probability
                    if hook_score < 0.4:
                        final_prob *= 0.8
                    elif hook_score > 0.8:
                        final_prob = min(0.98, final_prob * 1.1)
                        
                    tips = []
                    if result.predicted_ratio < 1.0:
                        tips.append("Model predicts below-average performance based on title/thumbnail.")
                    if hook_score < 0.6:
                         tips.append("Hook needs more urgency or curiosity gap.")
                         
                    return ViralPrediction(
                        predicted_views=result.predicted_views,
                        viral_probability=final_prob,
                        confidence_score=result.confidence_score,
                        factors={
                            'ml_score': result.predicted_ratio, 
                            'hook_heuristic': hook_score
                        },
                        tips=tips,
                        is_heuristic=False
                    )
            except Exception as e:
                print(f"⚠️ Supervised prediction failed, falling back to heuristics: {e}")

        # === HEURISTIC FALLBACK ===
        
        # 1. Analyze Title Power
        title_score = self._analyze_title(title, channel_history)
        
        # 2. Analyze Topic Relevance
        topic_score = self._analyze_topic(topic, channel_history)
        
        # 3. Analyze Hook Strength
        hook_score = self._analyze_hook(hook_text)
        
        # Calculate viral probability
        raw_score = (
            title_score * 0.3 +
            topic_score * 0.3 +
            hook_score * 0.2 +
            0.5 * 0.2  # Timing/Format placeholder
        )
        
        viral_prob = min(max(raw_score, 0), 0.95)
        
        # Predict views
        if viral_prob > 0.8:
            base = max_views
            multiplier = 0.8 + (viral_prob - 0.8)
        elif viral_prob > 0.5:
            base = avg_views
            multiplier = 1.0 + (viral_prob - 0.5)
        else:
            base = median_views
            multiplier = 0.5 + viral_prob
            
        predicted_views = int(base * multiplier)
        
        # Generate tips
        tips = []
        if title_score < 0.6:
            tips.append("Title could be stronger - try adding 'power words' or click-triggers.")
        if hook_score < 0.6:
            tips.append("Hook needs more urgency or curiosity gap.")
        if viral_prob > 0.8:
            tips.append("High viral potential! Ensure thumbnail matches title intensity.")
            
        return ViralPrediction(
            predicted_views=predicted_views,
            viral_probability=round(viral_prob, 2),
            confidence_score=0.4, # Low confidence for heuristic
            factors={
                'title': round(title_score, 2),
                'topic': round(topic_score, 2),
                'hook': round(hook_score, 2)
            },
            tips=tips,
            is_heuristic=True
        )
        
    def _analyze_title(self, title: str, history: List[Dict]) -> float:
        # Simple heuristic: check length and power words
        score = 0.5
        
        # Length check (optimal: 30-60 chars)
        if 30 <= len(title) <= 60:
            score += 0.1
        
        # Power words check
        power_words = ['secret', 'amazing', 'best', 'ultimate', 'how to', 'why', 'what', 'top', 'shocking']
        title_lower = title.lower()
        for word in power_words:
            if word in title_lower:
                score += 0.05
                break
            
        # Check for successful past patterns (only if history exists)
        if history:
            top_videos = sorted(history, key=lambda x: x.get('view_count', 0), reverse=True)[:5]
            
            matches = 0
            for vid in top_videos:
                past_title = vid.get('title', '').lower()
                # Check for common bigrams
                words = past_title.split()
                for i in range(len(words)-1):
                    if f"{words[i]} {words[i+1]}" in title_lower:
                        matches += 1
                        
            score += min(matches * 0.1, 0.3)
        
        return min(score, 1.0)

    def _analyze_topic(self, topic: str, history: List[Dict]) -> float:
        """
        Analyze topic relevance based on channel history.
        
        Returns a score 0-1 based on how well similar topics performed historically.
        - 0.5 = neutral (no history or topic not found)
        - >0.5 = similar topics performed above channel average
        - <0.5 = similar topics performed below channel average
        """
        if not history or not topic:
            return 0.5  # Neutral when no data
        
        topic_lower = topic.lower()
        topic_words = set(topic_lower.split())
        
        # Find videos with overlapping topic words
        matching_videos = []
        for vid in history:
            title = vid.get('title', '').lower()
            title_words = set(title.split())
            # Check for word overlap
            overlap = len(topic_words & title_words)
            if overlap >= 1:  # At least one word matches
                matching_videos.append(vid)
        
        if not matching_videos:
            return 0.5  # Unknown topic
        
        # Calculate performance of matching videos vs channel average
        channel_views = [v.get('view_count', 0) for v in history if v.get('view_count', 0) > 0]
        matching_views = [v.get('view_count', 0) for v in matching_videos if v.get('view_count', 0) > 0]
        
        if not channel_views or not matching_views:
            return 0.5
        
        channel_avg = sum(channel_views) / len(channel_views)
        matching_avg = sum(matching_views) / len(matching_views)
        
        # Score: ratio of matching avg to channel avg, normalized to 0-1
        # ratio of 1.0 = 0.5, ratio of 2.0 = 0.75, ratio of 0.5 = 0.25
        if channel_avg > 0:
            ratio = matching_avg / channel_avg
            score = 0.25 + (min(ratio, 3.0) / 3.0) * 0.5  # Clamp to 0.25-0.75
        else:
            score = 0.5
        
        return round(min(1.0, max(0.0, score)), 2)

    def _analyze_hook(self, hook: str) -> float:
        score = 0.5
        hook_lower = hook.lower()
        
        # Check for hook elements
        if '?' in hook: # Question
            score += 0.1
        if any(w in hook_lower for w in ['you', 'your', 'i', 'my']): # Personal
            score += 0.1
        if any(w in hook_lower for w in ['secret', 'know', 'never', 'stop']): # Curiosity
            score += 0.1
            
        return min(score, 1.0)
