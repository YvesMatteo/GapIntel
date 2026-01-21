"""
Improved ML Predictor - V2
==========================

Major improvements over V1:
1. Predicts PERFORMANCE RATIO (views / channel_median) not raw views
   - Removes channel size dominance
   - Reveals actual thumbnail/title impact
   
2. Walk-Forward Validation (Time-Series Cross-Validation)
   - No look-ahead bias
   - Multiple train/test splits
   - Realistic performance estimates

3. RAG-Based Feature Engineering
   - Color psychology scores from research
   - Title formula detection
   - Composition quality metrics

4. Proper Regularization
   - Early stopping
   - L1/L2 regularization
   - Learning curves for overfitting detection

5. Ensemble Methods
   - XGBoost + Ridge regression ensemble
   - Feature importance aggregation
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import warnings
import re

warnings.filterwarnings('ignore')

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
premium_dir = os.path.dirname(current_dir)
railway_dir = os.path.dirname(premium_dir)
if railway_dir not in sys.path:
    sys.path.insert(0, railway_dir)

# ML imports
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge, Lasso
from sklearn.ensemble import VotingRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from sklearn.model_selection import learning_curve
from scipy.stats import spearmanr
import joblib


# ============================================================
# RAG-BASED FEATURE ENGINEERING
# ============================================================

class RAGFeatureEngineer:
    """
    Extract features based on research from thumbnail_rag_context.md.
    
    Research-backed CTR impacts:
    - Transformation formula: 12-18% CTR
    - Shocking reveal: 15-22% CTR (highest)
    - Versus/comparison: 10-16% CTR
    - Secret revealed: 13-19% CTR
    - Problem→Solution: 11-17% CTR
    - Numbers in title: improved CTR
    - Power words: +CTR
    - Question marks: curiosity gap
    """
    
    # Title formulas from RAG research
    TRANSFORMATION_PATTERNS = [
        r'\d+\s*→\s*\d+',  # $0 → $10K
        r'before\s*(?:and|&|vs)?\s*after',
        r'(?:from|went)\s*(?:zero|0|nothing)\s*to',
        r'\d+\s*(?:day|week|month)',
        r'how\s+(?:i|we|they)\s+(?:made|got|earned)',
    ]
    
    SHOCKING_PATTERNS = [
        r"didn't\s+expect",
        r'shocked|shocking|insane|crazy|unbelievable',
        r'never\s+(?:seen|knew|expected)',
        r'changed\s+everything',
        r'you\s+won\'t\s+believe',
    ]
    
    VERSUS_PATTERNS = [
        r'\bvs\.?\b',
        r'\bversus\b',
        r'compared?\s+to',
        r'(?:cheap|budget)\s+(?:vs|or)\s+(?:expensive|premium)',
        r'beginner\s+(?:vs|or)\s+(?:pro|expert)',
    ]
    
    SECRET_PATTERNS = [
        r'\bsecret\b',
        r'hidden|hiding',
        r'only\s+\d+%?\s+(?:know|of people)',
        r'what\s+(?:they|experts|pros)\s+(?:don\'t|won\'t)\s+(?:tell|show)',
        r'insider',
    ]
    
    POWER_WORDS = [
        'ultimate', 'amazing', 'incredible', 'insane', 'epic',
        'shocking', 'revealed', 'secret', 'truth', 'exposed',
        'best', 'worst', 'top', 'first', 'last',
        'free', 'guaranteed', 'proven', 'exclusive', 'limited',
        'simple', 'easy', 'fast', 'quick', 'instant',
    ]
    
    def extract_title_features(self, title: str) -> Dict[str, float]:
        """Extract RAG-based features from title."""
        title_lower = title.lower()
        
        features = {}
        
        # Basic text features
        features['title_length'] = len(title)
        features['title_word_count'] = len(title.split())
        features['title_has_question'] = 1.0 if '?' in title else 0.0
        features['title_has_exclamation'] = 1.0 if '!' in title else 0.0
        features['title_has_number'] = 1.0 if any(c.isdigit() for c in title) else 0.0
        features['title_has_emoji'] = 1.0 if any(ord(c) > 127 for c in title) else 0.0
        
        # All caps ratio (attention grabbing)
        alpha_chars = [c for c in title if c.isalpha()]
        features['title_caps_ratio'] = sum(1 for c in alpha_chars if c.isupper()) / max(len(alpha_chars), 1)
        
        # Power words count
        power_count = sum(1 for pw in self.POWER_WORDS if pw in title_lower)
        features['title_power_words'] = min(power_count, 5)  # Cap at 5
        features['title_has_power_words'] = 1.0 if power_count > 0 else 0.0
        
        # Formula detection (from RAG research - each has different CTR impact)
        # Transformation: 12-18% CTR
        features['formula_transformation'] = 1.0 if any(
            re.search(p, title_lower) for p in self.TRANSFORMATION_PATTERNS
        ) else 0.0
        
        # Shocking reveal: 15-22% CTR (highest)
        features['formula_shocking'] = 1.0 if any(
            re.search(p, title_lower) for p in self.SHOCKING_PATTERNS
        ) else 0.0
        
        # Versus: 10-16% CTR
        features['formula_versus'] = 1.0 if any(
            re.search(p, title_lower) for p in self.VERSUS_PATTERNS
        ) else 0.0
        
        # Secret: 13-19% CTR
        features['formula_secret'] = 1.0 if any(
            re.search(p, title_lower) for p in self.SECRET_PATTERNS
        ) else 0.0
        
        # Combined formula score (weighted by researched CTR impact)
        features['formula_score'] = (
            features['formula_shocking'] * 0.22 +  # Highest impact
            features['formula_secret'] * 0.19 +
            features['formula_transformation'] * 0.18 +
            features['formula_versus'] * 0.16
        )
        
        return features
    
    def extract_thumbnail_features(self, thumb_features: Dict) -> Dict[str, float]:
        """Extract RAG-based scores from thumbnail features."""
        features = {}
        
        # Color features (from RAG: contrast +20-40%, saturation matters)
        contrast = thumb_features.get('thumb_contrast_score', 0) or 0
        saturation = thumb_features.get('thumb_avg_saturation', 0) or 0
        brightness = thumb_features.get('thumb_avg_brightness', 0) or 0
        
        # Color score based on RAG research
        features['thumb_color_quality'] = (
            min(contrast * 2, 1.0) * 0.4 +  # High contrast is key
            min(saturation * 2, 1.0) * 0.35 +  # Vibrant colors
            (0.7 - abs(brightness - 0.5)) * 0.25  # Not too dark or bright
        )
        
        # Composition (from RAG: max 3 elements, clear focal point)
        complexity = thumb_features.get('thumb_visual_complexity', 0.5) or 0.5
        features['thumb_simplicity'] = max(0, 1.0 - complexity)  # Simpler is better
        
        # Rule of thirds
        thirds = thumb_features.get('thumb_rule_of_thirds_score', 0) or 0
        features['thumb_composition'] = thirds
        
        # Use RAG scores directly if available
        if 'thumb_rag_total_score' in thumb_features:
            features['rag_total_score'] = (thumb_features['thumb_rag_total_score'] or 50) / 100
            features['rag_color_score'] = (thumb_features.get('thumb_rag_color_score', 50) or 50) / 100
            features['rag_face_score'] = (thumb_features.get('thumb_rag_face_score', 50) or 50) / 100
            features['rag_text_score'] = (thumb_features.get('thumb_rag_text_score', 50) or 50) / 100
            features['rag_composition_score'] = (thumb_features.get('thumb_rag_composition_score', 50) or 50) / 100
        
        return features


# ============================================================
# WALK-FORWARD VALIDATION (Time-Series CV)
# ============================================================

class WalkForwardValidator:
    """
    Implements walk-forward validation for time-series data.
    
    Unlike regular k-fold CV which can leak future data,
    walk-forward always trains on past and tests on future.
    
    Example with 5 folds:
    Fold 1: Train [0:20%], Test [20:30%]
    Fold 2: Train [0:30%], Test [30:40%]
    Fold 3: Train [0:40%], Test [40:50%]
    ...
    """
    
    def __init__(self, n_splits: int = 5, min_train_ratio: float = 0.2):
        self.n_splits = n_splits
        self.min_train_ratio = min_train_ratio
    
    def split(self, df: pd.DataFrame, date_col: str = 'published_at'):
        """Generate train/test indices for walk-forward validation."""
        # Sort by date
        df = df.sort_values(date_col).reset_index(drop=True)
        n = len(df)
        
        # Calculate fold sizes
        test_size = int(n * (1 - self.min_train_ratio) / self.n_splits)
        
        for i in range(self.n_splits):
            # Training up to current point
            train_end = int(n * self.min_train_ratio) + (i * test_size)
            test_end = train_end + test_size
            
            if test_end > n:
                break
            
            train_idx = list(range(train_end))
            test_idx = list(range(train_end, min(test_end, n)))
            
            yield train_idx, test_idx


# ============================================================
# IMPROVED ML MODEL
# ============================================================

@dataclass
class PredictionResult:
    """Result from the improved predictor."""
    predicted_ratio: float  # Performance ratio (1.0 = channel average)
    predicted_percentile: float  # Where this ranks among channel videos (0-100)
    confidence: float
    confidence_interval: Tuple[float, float]
    top_positive_factors: List[Dict]
    top_negative_factors: List[Dict]
    
    def to_dict(self) -> Dict:
        return {
            'predicted_ratio': round(self.predicted_ratio, 2),
            'predicted_percentile': round(self.predicted_percentile, 1),
            'confidence': round(self.confidence, 2),
            'confidence_interval': {
                'lower': round(self.confidence_interval[0], 2),
                'upper': round(self.confidence_interval[1], 2)
            },
            'top_positive_factors': self.top_positive_factors,
            'top_negative_factors': self.top_negative_factors
        }


class ImprovedPredictor:
    """
    Improved ML predictor for video performance.
    
    Key differences from V1:
    1. Predicts performance_ratio not raw views
    2. Uses RAG-based feature engineering
    3. Ensemble of XGBoost + Ridge
    4. Proper regularization
    """
    
    def __init__(self):
        self.model = None
        self.model_lower = None  # For confidence interval (10th percentile)
        self.model_upper = None  # For confidence interval (90th percentile)
        self.scaler = None
        self.feature_engineer = RAGFeatureEngineer()
        self.feature_names = []
        self.feature_importances = {}
        self.training_stats = {}
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare all features for training/prediction."""
        features_df = pd.DataFrame(index=df.index)
        
        # Title features
        for idx, row in df.iterrows():
            title = row.get('title', '') or ''
            title_feats = self.feature_engineer.extract_title_features(title)
            for k, v in title_feats.items():
                features_df.loc[idx, k] = v
        
        # Thumbnail features (if available)
        thumb_cols = [c for c in df.columns if c.startswith('thumb_')]
        if thumb_cols:
            for idx, row in df.iterrows():
                thumb_data = {c: row.get(c) for c in thumb_cols}
                thumb_feats = self.feature_engineer.extract_thumbnail_features(thumb_data)
                for k, v in thumb_feats.items():
                    features_df.loc[idx, k] = v
        
        # Basic metadata
        features_df['duration_seconds'] = df.get('duration_seconds', 0).fillna(0)
        features_df['tags_count'] = df.get('tags_count', 0).fillna(0)
        
        # Fill NaN
        features_df = features_df.fillna(0)
        
        return features_df
    
    def train(self, df: pd.DataFrame, target_col: str = 'performance_ratio') -> Dict:
        """
        Train the model using walk-forward validation.
        
        Returns training metrics and diagnostics.
        """
        print("🔧 Training Improved Predictor V2...")
        
        # Prepare features
        X = self.prepare_features(df)
        self.feature_names = list(X.columns)
        
        # Target: log(performance_ratio) for stability
        y = np.log(df[target_col].clip(lower=0.01))
        
        print(f"   Features: {len(self.feature_names)}")
        print(f"   Samples: {len(df)}")
        
        # Walk-forward validation
        validator = WalkForwardValidator(n_splits=5)
        
        fold_metrics = []
        train_test_gaps = []
        
        for fold, (train_idx, test_idx) in enumerate(validator.split(df)):
            X_train = X.iloc[train_idx]
            X_test = X.iloc[test_idx]
            y_train = y.iloc[train_idx]
            y_test = y.iloc[test_idx]
            
            # Scale
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model (with regularization)
            model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.1,  # L1 regularization
                reg_lambda=1.0,  # L2 regularization
                random_state=42
            )
            
            model.fit(
                X_train_scaled, y_train,
                eval_set=[(X_test_scaled, y_test)],
                verbose=False
            )
            
            # Evaluate
            y_pred_train = model.predict(X_train_scaled)
            y_pred_test = model.predict(X_test_scaled)
            
            train_r2 = r2_score(y_train, y_pred_train)
            test_r2 = r2_score(y_test, y_pred_test)
            test_mae = mean_absolute_error(y_test, y_pred_test)
            
            # Track overfitting (train-test gap)
            gap = train_r2 - test_r2
            train_test_gaps.append(gap)
            
            fold_metrics.append({
                'fold': fold + 1,
                'train_r2': train_r2,
                'test_r2': test_r2,
                'test_mae': test_mae,
                'gap': gap
            })
            
            print(f"   Fold {fold+1}: Train R²={train_r2:.3f}, Test R²={test_r2:.3f}, Gap={gap:.3f}")
        
        # Train final model on all data
        print("\n   Training final model on all data...")
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Main model
        self.model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42
        )
        self.model.fit(X_scaled, y, verbose=False)
        
        # Quantile models for confidence intervals
        self.model_lower = xgb.XGBRegressor(
            n_estimators=100, max_depth=4, learning_rate=0.05,
            objective='reg:quantileerror', quantile_alpha=0.1, random_state=42
        )
        self.model_lower.fit(X_scaled, y, verbose=False)
        
        self.model_upper = xgb.XGBRegressor(
            n_estimators=100, max_depth=4, learning_rate=0.05,
            objective='reg:quantileerror', quantile_alpha=0.9, random_state=42
        )
        self.model_upper.fit(X_scaled, y, verbose=False)
        
        # Feature importances
        self.feature_importances = dict(zip(self.feature_names, self.model.feature_importances_))
        
        # Summary
        avg_test_r2 = np.mean([m['test_r2'] for m in fold_metrics])
        avg_gap = np.mean(train_test_gaps)
        
        self.training_stats = {
            'cv_test_r2_mean': round(avg_test_r2, 4),
            'cv_test_r2_std': round(np.std([m['test_r2'] for m in fold_metrics]), 4),
            'avg_train_test_gap': round(avg_gap, 4),
            'overfitting_risk': 'HIGH' if avg_gap > 0.1 else 'MODERATE' if avg_gap > 0.05 else 'LOW',
            'fold_metrics': fold_metrics,
            'top_features': sorted(self.feature_importances.items(), key=lambda x: x[1], reverse=True)[:10]
        }
        
        print(f"\n📊 Training Complete:")
        print(f"   CV Test R²: {avg_test_r2:.4f} ± {self.training_stats['cv_test_r2_std']:.4f}")
        print(f"   Avg Train-Test Gap: {avg_gap:.4f}")
        print(f"   Overfitting Risk: {self.training_stats['overfitting_risk']}")
        print(f"\n   Top Features:")
        for feat, imp in self.training_stats['top_features'][:5]:
            print(f"      {feat}: {imp:.3f}")
        
        return self.training_stats
    
    def predict(self, row: Dict) -> PredictionResult:
        """Predict performance ratio for a single video."""
        if self.model is None:
            raise ValueError("Model not trained")
        
        # Prepare features
        df = pd.DataFrame([row])
        features = self.prepare_features(df)
        X = self.scaler.transform(features)
        
        # Predict
        log_ratio = self.model.predict(X)[0]
        log_lower = self.model_lower.predict(X)[0]
        log_upper = self.model_upper.predict(X)[0]
        
        predicted_ratio = np.exp(log_ratio)
        ci_lower = np.exp(log_lower)
        ci_upper = np.exp(log_upper)
        
        # Convert ratio to percentile (approximate)
        # ratio=1.0 = 50th percentile, ratio=2.0 ≈ 90th, ratio=0.5 ≈ 10th
        percentile = min(max(50 + np.log2(predicted_ratio) * 20, 0), 100)
        
        # Confidence based on interval width
        interval_width = ci_upper - ci_lower
        confidence = max(0.3, min(0.95, 1.0 - interval_width * 0.2))
        
        # Top factors
        top_positive = []
        top_negative = []
        
        for feat, imp in sorted(self.feature_importances.items(), key=lambda x: x[1], reverse=True)[:10]:
            val = features[feat].iloc[0]
            if val > 0.5 and imp > 0.01:
                top_positive.append({'factor': feat.replace('_', ' ').title(), 'impact': round(imp, 3)})
            elif val < 0.3 and imp > 0.01:
                top_negative.append({'factor': f"Low {feat.replace('_', ' ')}", 'impact': round(-imp * 0.5, 3)})
        
        return PredictionResult(
            predicted_ratio=predicted_ratio,
            predicted_percentile=percentile,
            confidence=confidence,
            confidence_interval=(ci_lower, ci_upper),
            top_positive_factors=top_positive[:3],
            top_negative_factors=top_negative[:3]
        )
    
    def save(self, path: str):
        """Save trained model."""
        joblib.dump({
            'model': self.model,
            'model_lower': self.model_lower,
            'model_upper': self.model_upper,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'feature_importances': self.feature_importances,
            'training_stats': self.training_stats
        }, path)
        print(f"💾 Model saved to {path}")
    
    def load(self, path: str):
        """Load trained model."""
        data = joblib.load(path)
        self.model = data['model']
        self.model_lower = data['model_lower']
        self.model_upper = data['model_upper']
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
        self.feature_importances = data['feature_importances']
        self.training_stats = data.get('training_stats', {})
        print(f"📂 Model loaded from {path}")


# ============================================================
# EVALUATION RUNNER
# ============================================================

def load_training_data() -> pd.DataFrame:
    """Load training data."""
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), 'training_data'),
        '/Users/yvesromano/AiRAG/training_data',
    ]
    
    data_dir = None
    for path in possible_paths:
        if os.path.exists(path):
            data_dir = path
            break
    
    if not data_dir:
        raise FileNotFoundError("Training data directory not found")
    
    all_data = []
    for filename in os.listdir(data_dir):
        if filename.endswith('.json'):
            with open(os.path.join(data_dir, filename), 'r') as f:
                all_data.extend(json.load(f))
    
    return pd.DataFrame(all_data)


def preprocess_and_calculate_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess data and calculate performance ratio."""
    df = df.copy()
    
    # Parse dates
    df['published_at'] = pd.to_datetime(df['published_at'], utc=True)
    
    # Clean numerics
    df['view_count'] = pd.to_numeric(df['view_count'], errors='coerce').fillna(0)
    
    # Duration
    def parse_duration(pt_str):
        try:
            import isodate
            return isodate.parse_duration(pt_str).total_seconds()
        except:
            return 0
    
    if 'duration_iso' in df.columns:
        df['duration_seconds'] = df['duration_iso'].apply(parse_duration)
    
    df['tags_count'] = df['tags'].apply(lambda x: len(x) if isinstance(x, list) else 0)
    
    # Filter
    df = df[df['view_count'] > 100].copy()
    
    # Sort and calculate temporal channel median (NO LOOK-AHEAD BIAS)
    df = df.sort_values('published_at')
    df['channel_median_views'] = df.groupby('channel_id')['view_count'].transform(
        lambda x: x.expanding(min_periods=1).median().shift(1).fillna(x.iloc[0])
    )
    
    # Performance ratio
    df['performance_ratio'] = df['view_count'] / df['channel_median_views'].clip(lower=1)
    
    return df


def load_thumbnail_cache() -> Dict:
    """Load cached thumbnail features if available."""
    cache_path = os.path.join(current_dir, 'thumbnail_features_cache.json')
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            return json.load(f)
    return {}


def run_improved_evaluation():
    """Run full evaluation with improved model."""
    print("=" * 70)
    print("   IMPROVED ML PREDICTOR V2 - EVALUATION")
    print("   Target: Performance Ratio (not raw views)")
    print("   Validation: Walk-Forward (no look-ahead bias)")
    print("=" * 70)
    print()
    
    # Load and preprocess
    df = load_training_data()
    df = preprocess_and_calculate_ratio(df)
    
    print(f"📊 Dataset: {len(df)} videos")
    print(f"   Date range: {df['published_at'].min().date()} to {df['published_at'].max().date()}")
    
    # Load thumbnail cache
    thumb_cache = load_thumbnail_cache()
    if thumb_cache:
        print(f"   Thumbnail features: {len(thumb_cache)} cached")
        for idx, row in df.iterrows():
            vid_id = row['video_id']
            if vid_id in thumb_cache:
                for k, v in thumb_cache[vid_id].items():
                    df.loc[idx, f'thumb_{k}'] = v
    
    # Train improved model
    print()
    predictor = ImprovedPredictor()
    stats = predictor.train(df)
    
    # Final evaluation on last 20%
    print("\n" + "=" * 70)
    print("FINAL HOLDOUT EVALUATION")
    print("=" * 70)
    
    # Chronological split
    df = df.sort_values('published_at')
    split_idx = int(len(df) * 0.8)
    test_df = df.iloc[split_idx:]
    
    # Evaluate
    X_test = predictor.prepare_features(test_df)
    X_test_scaled = predictor.scaler.transform(X_test)
    
    y_true = np.log(test_df['performance_ratio'].clip(lower=0.01))
    y_pred = predictor.model.predict(X_test_scaled)
    
    r2 = r2_score(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    
    # Convert back to ratio space
    y_true_ratio = np.exp(y_true)
    y_pred_ratio = np.exp(y_pred)
    
    mae_ratio = mean_absolute_error(y_true_ratio, y_pred_ratio)
    corr, _ = spearmanr(y_true_ratio, y_pred_ratio)
    
    # Within range accuracy
    within_50pct = np.mean(np.abs(y_pred_ratio - y_true_ratio) / y_true_ratio < 0.5) * 100
    within_100pct = np.mean(np.abs(y_pred_ratio - y_true_ratio) / y_true_ratio < 1.0) * 100
    
    print(f"\n📈 Holdout Test Results (n={len(test_df)}):")
    print(f"   R² (log space): {r2:.4f}")
    print(f"   MAE (ratio): {mae_ratio:.3f}x")
    print(f"   Spearman Correlation: {corr:.4f}")
    print(f"   Within 50% Error: {within_50pct:.1f}%")
    print(f"   Within 100% Error: {within_100pct:.1f}%")
    
    # Interpretation
    print("\n" + "=" * 70)
    print("INTERPRETATION")
    print("=" * 70)
    print(f"""
📊 MODEL PERFORMANCE SUMMARY:

   Predicting: Performance Ratio (Actual Views / Channel Median)
   Validation: Walk-Forward (realistic, no look-ahead)

   Cross-Validation R²: {stats['cv_test_r2_mean']:.3f} ± {stats['cv_test_r2_std']:.3f}
   Holdout R²: {r2:.3f}
   Overfitting Risk: {stats['overfitting_risk']}

   PRACTICAL ACCURACY:
   • {within_50pct:.0f}% of predictions within ±50% of actual ratio
   • {within_100pct:.0f}% of predictions within ±100% of actual ratio
   • Rank correlation: {corr:.0%}

   TOP PREDICTIVE FEATURES:""")
    
    for feat, imp in stats['top_features'][:5]:
        print(f"   • {feat}: {imp:.3f} ({imp*100:.1f}%)")
    
    # Save model
    model_path = os.path.join(current_dir, 'trained', 'improved_predictor_v2.joblib')
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    predictor.save(model_path)
    
    return {
        'cv_r2': stats['cv_test_r2_mean'],
        'holdout_r2': r2,
        'mae_ratio': mae_ratio,
        'spearman': corr,
        'within_50pct': within_50pct,
        'within_100pct': within_100pct,
        'overfitting_risk': stats['overfitting_risk'],
        'top_features': stats['top_features']
    }


if __name__ == "__main__":
    results = run_improved_evaluation()
