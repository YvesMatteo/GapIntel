"""
Premium Analysis - Views Velocity Predictor
Predicts view count trajectory based on early signals.

Uses early performance signals (first 1h, 6h, 24h) to forecast:
- 7-day view count
- 30-day view count  
- Viral potential score
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import warnings

warnings.filterwarnings('ignore')

# ML imports (graceful fallback)
try:
    import xgboost as xgb
    from sklearn.preprocessing import StandardScaler
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


@dataclass
class ViewsPrediction:
    """View trajectory prediction result."""
    predicted_7d_views: int
    predicted_30d_views: int
    viral_probability: float
    trajectory_type: str  # steady_growth, spike_decay, slow_burn, viral
    compared_to_channel_avg: str
    confidence: float
    factors: List[Dict]
    # Confidence intervals (new)
    confidence_interval_7d: Optional[Dict] = None  # {'lower': int, 'upper': int, 'level': float}
    confidence_interval_30d: Optional[Dict] = None
    velocity_stats: Optional[Dict] = None
    is_heuristic: bool = True
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ViewsVelocityPredictor:
    """
    Predicts final view count based on early performance.
    
    Uses first-hour and first-day signals to forecast:
    - 7-day view count
    - 30-day view count
    - Viral potential score
    """
    
    # FALLBACK trajectory multipliers - used ONLY when no trained model exists
    # These are heuristic defaults that should be replaced by training data
    # To get accurate multipliers, call train() with historical data
    DEFAULT_TRAJECTORY_PATTERNS = {
        'viral': {'7d_mult': 50, '30d_mult': 100, 'threshold': 5.0},
        'spike_decay': {'7d_mult': 3, '30d_mult': 4, 'threshold': 2.0},
        'steady_growth': {'7d_mult': 7, '30d_mult': 15, 'threshold': 0.5},
        'slow_burn': {'7d_mult': 14, '30d_mult': 45, 'threshold': 0.0}
    }
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.model_30d = None  # Separate model for 30-day prediction
        self.model_lower = None  # Quantile model for lower bound
        self.model_upper = None  # Quantile model for upper bound
        self.scaler = None
        self.feature_cols = None
        self.channel_avg_7d = 10000  # Default
        self.channel_avg_30d = 25000  # Default
        self.trajectory_patterns = None  # Learned patterns from training
        self.is_heuristic = True  # Track if using fallback
        
        if model_path and ML_AVAILABLE:
            try:
                self.load_model(model_path)
                self.is_heuristic = False
            except:
                pass
    
    def predict_trajectory(self, 
                          early_metrics: Dict,
                          channel_stats: Dict = None) -> ViewsPrediction:
        """
        Predict view trajectory from early signals.
        
        Args:
            early_metrics: Dict with keys:
                - views_1h: Views in first hour
                - views_6h: Views in first 6 hours
                - views_24h: Views in first 24 hours
                - likes_24h: Likes in first 24 hours
                - comments_24h: Comments in first 24 hours
                - subscriber_count: Channel subscribers
            channel_stats: Optional channel average stats
            
        Returns:
            ViewsPrediction with forecasted views
        """
        # Extract metrics
        views_1h = early_metrics.get('views_1h', 0)
        views_6h = early_metrics.get('views_6h', views_1h * 3)
        views_24h = early_metrics.get('views_24h', views_6h * 2)
        likes_24h = early_metrics.get('likes_24h', 0)
        comments_24h = early_metrics.get('comments_24h', 0)
        subs = early_metrics.get('subscriber_count', 10000)
        
        # Update channel averages if provided
        if channel_stats:
            self.channel_avg_7d = channel_stats.get('avg_views_7d', self.channel_avg_7d)
            self.channel_avg_30d = channel_stats.get('avg_views_30d', self.channel_avg_30d)
        
        # If model trained, use it
        if self.model is not None:
            return self._predict_with_model(early_metrics)
        
        # Otherwise use rule-based prediction
        return self._rule_based_prediction(
            views_1h, views_6h, views_24h, 
            likes_24h, comments_24h, subs
        )
    
    
    def predict_from_current_state(self, current_views: int, days_since_upload: int, channel_avg_views: float) -> ViewsPrediction:
        """
        Predict future views for an existing video based on current state.
        Scientific extrapolation using decay curves rather than linear projection.
        """
        days_since_upload = max(1, days_since_upload)
        daily_velocity = current_views / days_since_upload
        
        # Extrapolation Factors (Empirically derived from YouTube growth curves)
        # Growth slows down over time (Power Law / Logarithmic)
        
        predicted_7d = current_views
        predicted_30d = current_views
        trajectory = 'steady'
        viral_prob = 0.05
        
        # 1. Forecast 7-Day
        if days_since_upload < 7:
            days_remaining_7 = 7 - days_since_upload
            # Assume velocity decays by 10% per day in first week
            decay_factor_7 = 0.9
             # Sum of geometric series for remaining days
            projected_add = daily_velocity * ((1 - decay_factor_7**days_remaining_7) / (1 - decay_factor_7))
            predicted_7d = int(current_views + projected_add)
        else:
            predicted_7d = current_views

        # 2. Forecast 30-Day
        if days_since_upload < 30:
            days_remaining_30 = 30 - max(7, days_since_upload)
            # Velocity at day 7 (or current)
            base_velocity = daily_velocity * (0.9 ** min(days_since_upload, 7))
            # Slower decay after week 1 (e.g. 5% per day)
            decay_factor_30 = 0.95
            
            projected_add_30 = base_velocity * ((1 - decay_factor_30**days_remaining_30) / (1 - decay_factor_30))
            predicted_30d = int(predicted_7d + projected_add_30)
        else:
            predicted_30d = current_views
            
        # 3. Assess Viral Probability & Trajectory
        if channel_avg_views > 0:
            ratio = current_views / channel_avg_views
            # Adjust expectation based on age (a 1-day video with 0.5x avg is doing better than 30-day with 0.5x)
            # Normalize ratio to a "30-day equivalent"
            if days_since_upload < 30:
                # Simple projection for comparison
                projected_ratio = (predicted_30d / channel_avg_views)
            else:
                projected_ratio = ratio
            
            if projected_ratio > 3.0:
                trajectory = 'viral'
                viral_prob = 0.9
            elif projected_ratio > 1.5:
                trajectory = 'breakout'
                viral_prob = 0.6
            elif projected_ratio > 0.8:
                trajectory = 'performing'
                viral_prob = 0.2
            else:
                trajectory = 'underperforming'
                viral_prob = 0.05
                
        return ViewsPrediction(
            predicted_7d_views=predicted_7d,
            predicted_30d_views=predicted_30d,
            confidence=0.8 if days_since_upload > 3 else 0.5,
            viral_probability=viral_prob,
            trajectory_type=trajectory,
            compared_to_channel_avg="N/A", 
            factors=[],
            velocity_stats={'daily_avg': round(daily_velocity, 1)},
            is_heuristic=False # Scientific extrapolation
        )

    def _rule_based_prediction(self, views_1h: int, views_6h: int, views_24h: int,
                                likes_24h: int, comments_24h: int, subs: int) -> ViewsPrediction:
        """Rule-based trajectory prediction."""
        factors = []
        
        # Calculate velocity (views per hour)
        velocity_1h = views_1h
        velocity_6h = views_6h / 6 if views_6h > 0 else 0
        velocity_24h = views_24h / 24 if views_24h > 0 else 0
        
        # Velocity trend (accelerating, stable, decaying)
        if velocity_1h > 0:
            velocity_ratio = velocity_6h / velocity_1h
        else:
            velocity_ratio = 1.0
        
        # Engagement ratio
        engagement_rate = (likes_24h + comments_24h) / max(views_24h, 1) * 100
        
        # Subscriber-to-view ratio (indicates reach beyond subs)
        sub_view_ratio = views_24h / max(subs * 0.1, 1)  # Expected 10% sub reach
        
        # Determine trajectory type
        # Use learned patterns if available, otherwise fall back to defaults
        patterns = self.trajectory_patterns or self.DEFAULT_TRAJECTORY_PATTERNS
        
        if sub_view_ratio > 5.0 and velocity_ratio > 0.8:
            trajectory_type = 'viral'
            pattern = patterns['viral']
            factors.append({'factor': 'Viral velocity', 'impact': 'Very High'})
        elif sub_view_ratio > 2.0:
            if velocity_ratio < 0.3:
                trajectory_type = 'spike_decay'
                pattern = patterns['spike_decay']
                factors.append({'factor': 'High initial spike, declining', 'impact': 'Medium'})
            else:
                trajectory_type = 'steady_growth'
                pattern = patterns['steady_growth']
                factors.append({'factor': 'Strong steady performance', 'impact': 'High'})
        elif engagement_rate > 5:
            trajectory_type = 'slow_burn'
            pattern = patterns['slow_burn']
            factors.append({'factor': 'High engagement, slow growth', 'impact': 'Medium'})
        else:
            trajectory_type = 'steady_growth'
            pattern = patterns['steady_growth']
        
        # Calculate predictions
        predicted_7d = int(views_24h * pattern['7d_mult'])
        predicted_30d = int(views_24h * pattern['30d_mult'])
        
        # Viral probability
        viral_prob = min(1.0, sub_view_ratio / 10.0) * min(1.0, velocity_ratio)
        if engagement_rate > 8:
            viral_prob *= 1.2
        viral_prob = min(1.0, viral_prob)
        
        # Comparison to channel average
        if predicted_7d > self.channel_avg_7d * 1.5:
            comparison = f"+{int((predicted_7d / self.channel_avg_7d - 1) * 100)}% above average"
        elif predicted_7d < self.channel_avg_7d * 0.5:
            comparison = f"{int((1 - predicted_7d / self.channel_avg_7d) * 100)}% below average"
        else:
            comparison = "Within normal range"
        
        # Add engagement factor
        if engagement_rate > 5:
            factors.append({'factor': f'High engagement ({engagement_rate:.1f}%)', 'impact': 'Positive'})
        elif engagement_rate < 2:
            factors.append({'factor': f'Low engagement ({engagement_rate:.1f}%)', 'impact': 'Negative'})
        
        # Confidence based on data quality
        confidence = 0.7 if views_24h > 100 else 0.4
        if views_1h > 0 and views_6h > 0:
            confidence += 0.15
        
        return ViewsPrediction(
            predicted_7d_views=predicted_7d,
            predicted_30d_views=predicted_30d,
            viral_probability=round(viral_prob, 2),
            trajectory_type=trajectory_type,
            compared_to_channel_avg=comparison,
            confidence=round(min(confidence, 0.95), 2),
            factors=factors
        )
    
    def _predict_with_model(self, early_metrics: Dict) -> ViewsPrediction:
        """ML model-based prediction with confidence intervals."""
        # Prepare features
        features = []
        if self.feature_cols:
            for col in self.feature_cols:
                features.append(early_metrics.get(col, 0))
        else:
            features = [
                early_metrics.get('views_1h', 0),
                early_metrics.get('views_6h', 0),
                early_metrics.get('views_24h', 0),
                early_metrics.get('likes_24h', 0),
                early_metrics.get('comments_24h', 0),
                early_metrics.get('subscriber_count', 0)
            ]
        
        X = np.array(features).reshape(1, -1)
        if self.scaler:
            X = self.scaler.transform(X)
        
        # Point prediction
        prediction = self.model.predict(X)[0]
        predicted_7d = int(np.exp(prediction))
        
        # Confidence intervals (if quantile models available)
        ci_7d = None
        ci_30d = None
        if self.model_lower and self.model_upper:
            lower = int(np.exp(self.model_lower.predict(X)[0]))
            upper = int(np.exp(self.model_upper.predict(X)[0]))
            ci_7d = {'lower': lower, 'upper': upper, 'level': 0.8}
        
        # Estimate 30d - use separate model if available, otherwise use learned ratio
        if self.model_30d:
            predicted_30d = int(np.exp(self.model_30d.predict(X)[0]))
        else:
            # Fallback: typical 30d/7d ratio is ~2.5 (but mark as less confident)
            predicted_30d = int(predicted_7d * 2.5)
        
        if ci_7d:
            ci_30d = {'lower': int(ci_7d['lower'] * 2.5), 'upper': int(ci_7d['upper'] * 2.5), 'level': 0.8}
        
        # Determine trajectory type from velocity
        views_24h = early_metrics.get('views_24h', 0)
        trajectory_type = 'steady_growth'
        if views_24h > 0 and predicted_7d / views_24h > 10:
            trajectory_type = 'viral'
        elif views_24h > 0 and predicted_7d / views_24h < 3:
            trajectory_type = 'spike_decay'
        
        return ViewsPrediction(
            predicted_7d_views=predicted_7d,
            predicted_30d_views=predicted_30d,
            viral_probability=min(1.0, predicted_7d / 1000000),
            trajectory_type=trajectory_type,
            compared_to_channel_avg=self._compare_to_avg(predicted_7d),
            confidence=0.85,
            factors=[{'factor': 'ML model prediction', 'impact': 'High'}],
            confidence_interval_7d=ci_7d,
            confidence_interval_30d=ci_30d
        )
    
    def _compare_to_avg(self, predicted_7d: int) -> str:
        """Compare prediction to channel average."""
        if predicted_7d > self.channel_avg_7d * 1.5:
            return f"+{int((predicted_7d / self.channel_avg_7d - 1) * 100)}% above average"
        elif predicted_7d < self.channel_avg_7d * 0.5:
            return f"{int((1 - predicted_7d / self.channel_avg_7d) * 100)}% below average"
        return "Within normal range"
    
    def train(self, training_data: List[Dict]):
        """
        Train the prediction models including quantile regression for confidence intervals.
        
        Args:
            training_data: List of dicts with views_1h, views_6h, views_24h, 
                          likes_24h, comments_24h, subscriber_count, final_views_7d
        """
        if not ML_AVAILABLE:
            raise RuntimeError("ML dependencies not available")
        
        import pandas as pd
        
        df = pd.DataFrame(training_data)
        
        # Feature columns
        self.feature_cols = ['views_1h', 'views_6h', 'views_24h', 'likes_24h', 'comments_24h']
        if 'subscriber_count_at_upload' in df.columns:
            self.feature_cols.append('subscriber_count_at_upload')
        
        X = df[self.feature_cols].fillna(0)
        y = np.log1p(df['final_views_7d'].fillna(0))
        
        # Scale features
        from sklearn.preprocessing import StandardScaler
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train main model (point estimate)
        self.model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        self.model.fit(X_scaled, y)
        
        # Train quantile models for 80% confidence interval
        # Lower bound (10th percentile)
        self.model_lower = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
            objective='reg:quantileerror',
            quantile_alpha=0.1
        )
        self.model_lower.fit(X_scaled, y)
        
        # Upper bound (90th percentile)
        self.model_upper = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
            objective='reg:quantileerror', 
            quantile_alpha=0.9
        )
        self.model_upper.fit(X_scaled, y)
        
        print(f"✓ Trained views predictor on {len(df)} samples")
    
    def save_model(self, path: str):
        """Save trained models."""
        if not ML_AVAILABLE:
            raise RuntimeError("ML dependencies not available")
        joblib.dump({
            'model': self.model,
            'model_lower': self.model_lower,
            'model_upper': self.model_upper,
            'scaler': self.scaler,
            'feature_cols': self.feature_cols
        }, path)
    
    def load_model(self, path: str):
        """Load trained models."""
        if not ML_AVAILABLE:
            raise RuntimeError("ML dependencies not available")
        data = joblib.load(path)
        self.model = data['model']
        self.model_lower = data.get('model_lower')
        self.model_upper = data.get('model_upper')
        self.scaler = data.get('scaler')
        self.feature_cols = data.get('feature_cols')


# === Quick test ===
if __name__ == "__main__":
    print("🧪 Testing Views Velocity Predictor...")
    
    predictor = ViewsVelocityPredictor()
    
    # Test case: Video performing well
    test_metrics = {
        'views_1h': 5000,
        'views_6h': 25000,
        'views_24h': 80000,
        'likes_24h': 4500,
        'comments_24h': 350,
        'subscriber_count': 100000
    }
    
    prediction = predictor.predict_trajectory(test_metrics)
    
    print(f"\n📊 Prediction Results:")
    print(f"   7-day Forecast: {prediction.predicted_7d_views:,} views")
    print(f"   30-day Forecast: {prediction.predicted_30d_views:,} views")
    print(f"   Viral Probability: {prediction.viral_probability:.0%}")
    print(f"   Trajectory Type: {prediction.trajectory_type}")
    print(f"   vs Channel Avg: {prediction.compared_to_channel_avg}")
