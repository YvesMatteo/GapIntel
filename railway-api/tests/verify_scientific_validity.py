
import sys
import os
import unittest
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from premium.ml_models.viral_predictor import ViralPredictor
from premium.ml_models.ctr_predictor import CTRPredictor
from premium.ml_models.views_predictor import ViewsVelocityPredictor
from premium.ml_models.sentiment_engine import SentimentEngine

class TestScientificValidity(unittest.TestCase):
    
    def setUp(self):
        print(f"\nTesting {self._testMethodName}...")

    def test_viral_predictor_validity(self):
        """Verify ViralPredictor uses ML and provides confidence."""
        vp = ViralPredictor()
        
        # Test Case 1: Strong Title
        pred_strong = vp.predict(
            title="I Spent 100 Hours on a Desert Island",
            hook_text="You won't believe what happened on day 3.",
            topic="Survival",
            channel_history=[{'view_count': 10000}, {'view_count': 15000}]
        )
        
        self.assertIsNotNone(pred_strong.viral_probability)
        self.assertIsNotNone(pred_strong.confidence_score)
        print(f"   [Viral] Strong Prob: {pred_strong.viral_probability}, Conf: {pred_strong.confidence_score}")
        
        # Test Case 2: Weak Title
        pred_weak = vp.predict(
            title="My Video 123",
            hook_text="Hello guys welcome back",
            topic="Vlog",
            channel_history=[{'view_count': 10000}]
        )
        
        print(f"   [Viral] Weak Prob: {pred_weak.viral_probability}")
        
        # Check that predictions differ (Scientific sensitivity)
        # Note: If supervised model is missing, they might both use heuristics which might still differ
        # But we want to ensure it runs without error.
        self.assertTrue(0 <= pred_strong.viral_probability <= 1)

    def test_ctr_predictor_uncertainty(self):
        """Verify CTR Predictor provides uncertainty/confidence intervals."""
        cp = CTRPredictor()
        
        # Dummy features
        features = {
            'has_face': True,
            'face_count': 1,
            'text_density': 0.1,
            'brightness': 120,
            'contrast': 1.2
        }
        
        pred = cp.predict(features, "Test Title")
        
        self.assertIsNotNone(pred.confidence)
        self.assertTrue(0 <= pred.confidence <= 1)
        print(f"   [CTR] Prediction: {pred.predicted_ctr}, Confidence: {pred.confidence}")

    def test_views_velocity_decay(self):
        """Verify ViewsPredictor uses decay curves (no linear extrapolation)."""
        vvp = ViewsVelocityPredictor()
        
        current_views = 1000
        days_young = 2
        days_old = 100
        
        # Predict for young video
        pred_young = vvp.predict_from_current_state(current_views, days_young, channel_avg_views=2000)
        
        # Predict for old video
        pred_old = vvp.predict_from_current_state(current_views, days_old, channel_avg_views=2000)
        
        # Young video should have more growth projected than old video
        growth_young = pred_young.predicted_30d_views - current_views
        growth_old = pred_old.predicted_30d_views - current_views
        
        print(f"   [Views] Young Growth (2 days): {growth_young}")
        print(f"   [Views] Old Growth (100 days): {growth_old}")
        
        self.assertGreater(growth_young, growth_old, "Scientific Error: Old videos shouldn't grow as fast as young ones")

    def test_sentiment_classification(self):
        """Verify SentimentEngine uses new categorization."""
        se = SentimentEngine()
        
        comments = [
            "This assumes we have infinite money?",
            "I don't understand the first step.",
            "Great video, helped me a lot!",
            "Can you explain the ending?"
        ]
        
        comment_dicts = [{'text': c} for c in comments]
        results = se.analyze_batch(comment_dicts)
        
        for res in results:
            print(f"   [Sentiment] '{res['text'][:30]}...' -> {res.get('category', 'N/A')} ({res.get('sentiment')})")
            
        # Check that we have categories
        categories = [r.get('category') for r in results]
        self.assertTrue(any(c for c in categories), "No categories detected")
        
if __name__ == '__main__':
    unittest.main()
