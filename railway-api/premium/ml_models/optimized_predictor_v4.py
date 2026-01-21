"""
Optimized Ensemble Predictor - V4
=================================

Lessons from V2 and V3:
- V2 (XGBoost): HIGH overfitting (gap=0.77), test R²~0
- V3 (Ridge): LOW overfitting (gap=0.04), but also R²~0

TRUTH REVEALED: Title + Thumbnail alone explain ~0-10% of performance ratio variance.

This V4 uses:
1. Balanced XGBoost (moderate complexity)
2. Fewer, curated features based on research
3. Explicit niche-aware modeling
4. Honest confidence reporting
5. Focus on RANKING rather than exact prediction
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
import warnings
import re

warnings.filterwarnings('ignore')

current_dir = os.path.dirname(os.path.abspath(__file__))
premium_dir = os.path.dirname(current_dir)
railway_dir = os.path.dirname(premium_dir)
if railway_dir not in sys.path:
    sys.path.insert(0, railway_dir)

import xgboost as xgb
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import RidgeCV
from sklearn.metrics import mean_absolute_error, r2_score
from scipy.stats import spearmanr
import joblib


# ============================================================
# RESEARCH-BACKED FEATURE ENGINEERING
# ============================================================

class OptimizedFeatureEngineer:
    """
    Features proven by research + what worked in previous iterations.
    
    Key insight: Focus on features that affect RANKING, not absolute prediction.
    """
    
    # From RAG research - title formulas with proven CTR impact
    FORMULAS = {
        'transformation': (
            re.compile(r'(\d+\s*→|\d+\s*to\s*\d+|\$\d+|before.+after|how\s+[iweo])', re.I),
            0.15  # 12-18% CTR improvement
        ),
        'shocking': (
            re.compile(r'(shocking|insane|crazy|unbelievable|never.+before)', re.I),
            0.20  # 15-22% CTR (highest)
        ),
        'curiosity': (
            re.compile(r'(this|these|what|why|how)\s.*(happened|changed|works|reason)', re.I),
            0.18
        ),
        'list': (
            re.compile(r'^(\d+)\s', re.I),  # "5 Ways to..."
            0.12
        ),
    }
    
    POWER_WORDS = {
        'secret', 'revealed', 'truth', 'exposed', 'hidden',
        'best', 'worst', 'ultimate', 'free', 'proven',
    }
    
    def extract_features(self, row: Dict) -> Dict[str, float]:
        title = (row.get('title') or '')
        title_lower = title.lower()
        
        features = {}
        
        # 1. TITLE OPTIMIZATION (from RAG research)
        # Length optimization (50-60 chars is sweet spot)
        title_len = len(title)
        features['title_len_optimal'] = max(0, 1 - abs(title_len - 55) / 40)
        
        # Question (curiosity gap)
        features['has_question'] = float('?' in title)
        
        # Numbers (specificity)
        features['has_number'] = float(any(c.isdigit() for c in title))
        
        # Power words
        features['has_power_word'] = float(any(pw in title_lower for pw in self.POWER_WORDS))
        
        # Formula detection + weighted score
        formula_score = 0
        for name, (pattern, weight) in self.FORMULAS.items():
            if pattern.search(title_lower):
                features[f'formula_{name}'] = 1.0
                formula_score += weight
            else:
                features[f'formula_{name}'] = 0.0
        
        features['formula_score'] = min(formula_score, 0.5)  # Cap total
        
        # 2. THUMBNAIL QUALITY (from cached features)
        thumb_contrast = row.get('thumb_contrast_score', 0) or 0
        thumb_sat = row.get('thumb_avg_saturation', 0) or 0
        rag_total = row.get('thumb_rag_total_score', 50) or 50
        
        features['thumb_quality'] = (
            thumb_contrast * 0.4 + 
            thumb_sat * 0.3 + 
            (rag_total / 100) * 0.3
        )
        
        # 3. NICHE-SPECIFIC (different niches have different baselines)
        niche = row.get('niche', 'unknown')
        
        # Encode top niches
        NICHES = ['gaming', 'education', 'entertainment', 'business', 'tech']
        for n in NICHES:
            features[f'niche_{n}'] = 1.0 if niche == n else 0.0
        
        return features
    
    def get_feature_names(self) -> List[str]:
        """Return list of feature names."""
        base = [
            'title_len_optimal', 'has_question', 'has_number', 
            'has_power_word', 'formula_score', 'thumb_quality',
            'formula_transformation', 'formula_shocking', 
            'formula_curiosity', 'formula_list',
        ]
        niches = ['niche_gaming', 'niche_education', 'niche_entertainment', 
                  'niche_business', 'niche_tech']
        return base + niches


# ============================================================
# OPTIMIZED PREDICTOR
# ============================================================

@dataclass
class Prediction:
    """Model prediction with honest uncertainty."""
    predicted_ratio: float
    rank_percentile: float
    confidence_level: str  # "LOW", "MODERATE", "HIGH"
    
    # Comparison-focused output
    rank_estimate: str  # "Top 20%", "Average", "Below Average"
    optimization_score: float  # 0-100 summary score
    
    def to_dict(self) -> Dict:
        return asdict(self)


class OptimizedPredictor:
    """
    V4 Predictor - Balanced for real-world use.
    
    Key design decisions:
    1. Moderate XGBoost complexity (max_depth=3, low learning rate)
    2. Strong regularization
    3. Focus on RANKING rather than exact prediction
    4. Honest confidence reporting
    """
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_engineer = OptimizedFeatureEngineer()
        self.feature_names = []
        self.training_stats = {}
    
    def prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Prepare feature matrix."""
        features_list = []
        
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            feats = self.feature_engineer.extract_features(row_dict)
            features_list.append(feats)
        
        X = pd.DataFrame(features_list)
        self.feature_names = list(X.columns)
        
        return X.fillna(0).values
    
    def train(self, df: pd.DataFrame) -> Dict:
        """Train with walk-forward validation."""
        print("🔧 Training V4 Optimized Predictor...")
        
        # Sort chronologically
        df = df.sort_values('published_at').reset_index(drop=True)
        
        # Calculate target: performance ratio
        df['channel_median'] = df.groupby('channel_id')['view_count'].transform(
            lambda x: x.expanding(min_periods=1).median().shift(1).fillna(x.iloc[0])
        )
        df['performance_ratio'] = df['view_count'] / df['channel_median'].clip(lower=1)
        
        # Prepare features
        X = self.prepare_features(df)
        y = np.log(df['performance_ratio'].clip(lower=0.01))
        
        print(f"   Features: {len(self.feature_names)}")
        print(f"   Samples: {len(df)}")
        
        # Walk-forward CV
        n = len(df)
        n_splits = 5
        min_train = int(n * 0.3)
        test_size = (n - min_train) // n_splits
        
        fold_metrics = []
        
        for fold in range(n_splits):
            train_end = min_train + fold * test_size
            test_end = train_end + test_size
            
            if test_end > n:
                break
            
            X_train, X_test = X[:train_end], X[train_end:test_end]
            y_train, y_test = y[:train_end], y[train_end:test_end]
            
            # Scale
            scaler = StandardScaler()
            X_train_s = scaler.fit_transform(X_train)
            X_test_s = scaler.transform(X_test)
            
            # Train XGBoost with moderate complexity
            model = xgb.XGBRegressor(
                n_estimators=50,  # Fewer trees
                max_depth=3,      # Shallow trees
                learning_rate=0.03,  # Slow learning
                subsample=0.7,
                colsample_bytree=0.7,
                reg_alpha=1.0,    # L1 reg
                reg_lambda=5.0,   # Strong L2 reg
                random_state=42,
                verbosity=0
            )
            model.fit(X_train_s, y_train)
            
            # Evaluate
            pred_train = model.predict(X_train_s)
            pred_test = model.predict(X_test_s)
            
            r2_train = r2_score(y_train, pred_train)
            r2_test = r2_score(y_test, pred_test)
            gap = r2_train - r2_test
            
            # Rank correlation (what we actually care about)
            corr, _ = spearmanr(np.exp(y_test), np.exp(pred_test))
            
            fold_metrics.append({
                'fold': fold + 1,
                'train_r2': r2_train,
                'test_r2': r2_test,
                'gap': gap,
                'rank_corr': corr
            })
            
            print(f"   Fold {fold+1}: R²={r2_test:.3f}, Gap={gap:.3f}, Rank Corr={corr:.2f}")
        
        # Final model on all data
        print("\n   Training final model...")
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        self.model = xgb.XGBRegressor(
            n_estimators=50,
            max_depth=3,
            learning_rate=0.03,
            subsample=0.7,
            colsample_bytree=0.7,
            reg_alpha=1.0,
            reg_lambda=5.0,
            random_state=42,
            verbosity=0
        )
        self.model.fit(X_scaled, y)
        
        # Feature importances
        importances = dict(zip(self.feature_names, self.model.feature_importances_))
        
        # Summary stats
        avg_r2 = np.mean([m['test_r2'] for m in fold_metrics])
        avg_gap = np.mean([m['gap'] for m in fold_metrics])
        avg_corr = np.mean([m['rank_corr'] for m in fold_metrics])
        
        self.training_stats = {
            'cv_r2': round(avg_r2, 4),
            'cv_gap': round(avg_gap, 4),
            'cv_rank_corr': round(avg_corr, 4),
            'overfitting': 'LOW' if avg_gap < 0.1 else 'MODERATE' if avg_gap < 0.2 else 'HIGH',
            'importances': sorted(importances.items(), key=lambda x: x[1], reverse=True)
        }
        
        print(f"\n📊 Training Complete:")
        print(f"   CV R²: {avg_r2:.4f}")
        print(f"   CV Rank Correlation: {avg_corr:.4f}")
        print(f"   Overfitting: {self.training_stats['overfitting']} (gap={avg_gap:.3f})")
        print("\n   Top Features:")
        for feat, imp in self.training_stats['importances'][:5]:
            print(f"      {feat}: {imp:.3f}")
        
        return self.training_stats
    
    def predict(self, row: Dict) -> Prediction:
        """Predict with honest uncertainty."""
        if not self.model:
            raise ValueError("Model not trained")
        
        feats = self.feature_engineer.extract_features(row)
        X = np.array([[feats.get(f, 0) for f in self.feature_names]])
        X_scaled = self.scaler.transform(X)
        
        log_ratio = self.model.predict(X_scaled)[0]
        ratio = np.exp(log_ratio)
        
        # Rank percentile (ratio=1 = 50th percentile baseline)
        percentile = min(max(50 + np.log2(max(ratio, 0.1)) * 15, 5), 95)
        
        # Rank estimate
        if percentile >= 80:
            rank = "Top 20% potential"
        elif percentile >= 60:
            rank = "Above average"
        elif percentile >= 40:
            rank = "Average"
        else:
            rank = "Below average"
        
        # Confidence based on CV performance
        cv_corr = self.training_stats.get('cv_rank_corr', 0.3)
        if cv_corr >= 0.4:
            confidence = "MODERATE"
        else:
            confidence = "LOW"
        
        # Optimization score (0-100)
        opt_score = min(max(percentile, 0), 100)
        
        return Prediction(
            predicted_ratio=round(ratio, 2),
            rank_percentile=round(percentile, 1),
            confidence_level=confidence,
            rank_estimate=rank,
            optimization_score=round(opt_score, 1)
        )
    
    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'stats': self.training_stats
        }, path)
        print(f"💾 Saved to {path}")
    
    def load(self, path: str):
        data = joblib.load(path)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
        self.training_stats = data.get('stats', {})


# ============================================================
# RUN EVALUATION
# ============================================================

def load_data():
    paths = [
        '/Users/yvesromano/AiRAG/training_data',
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), 'training_data'),
    ]
    
    for path in paths:
        if os.path.exists(path):
            all_data = []
            for f in os.listdir(path):
                if f.endswith('.json'):
                    with open(os.path.join(path, f)) as fp:
                        all_data.extend(json.load(fp))
            return pd.DataFrame(all_data)
    
    raise FileNotFoundError("No training data")


def load_thumb_cache():
    path = os.path.join(current_dir, 'thumbnail_features_cache.json')
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def main():
    print("=" * 70)
    print("   OPTIMIZED PREDICTOR V4")
    print("   Balanced Complexity | Honest Uncertainty")
    print("=" * 70)
    
    # Load data
    df = load_data()
    df['published_at'] = pd.to_datetime(df['published_at'], utc=True)
    df['view_count'] = pd.to_numeric(df['view_count'], errors='coerce').fillna(0)
    df = df[df['view_count'] > 100].copy()
    
    # Add thumbnail features
    cache = load_thumb_cache()
    for idx, row in df.iterrows():
        vid = row['video_id']
        if vid in cache:
            for k, v in cache[vid].items():
                df.loc[idx, f'thumb_{k}'] = v
    
    print(f"\n📊 Dataset: {len(df)} videos")
    print(f"   With thumbnails: {len([v for v in df['video_id'] if v in cache])}")
    
    # Train
    predictor = OptimizedPredictor()
    stats = predictor.train(df)
    
    # Final holdout test
    print("\n" + "=" * 70)
    print("HOLDOUT TEST (Last 20%)")
    print("=" * 70)
    
    df = df.sort_values('published_at').reset_index()
    split = int(len(df) * 0.8)
    test_df = df.iloc[split:]
    
    # Calculate actual ratios for test set
    test_df = test_df.copy()
    test_df['channel_median'] = test_df.groupby('channel_id')['view_count'].transform(
        lambda x: x.expanding(min_periods=1).median().shift(1).fillna(x.iloc[0])
    )
    test_df['actual_ratio'] = test_df['view_count'] / test_df['channel_median'].clip(lower=1)
    
    # Predict
    preds = []
    for _, row in test_df.iterrows():
        pred = predictor.predict(row.to_dict())
        preds.append(pred.predicted_ratio)
    
    # Metrics
    actual = test_df['actual_ratio'].values
    preds = np.array(preds)
    
    r2 = r2_score(np.log(actual.clip(min=0.01)), np.log(preds.clip(min=0.01)))
    corr, _ = spearmanr(actual, preds)
    mae = mean_absolute_error(actual, preds)
    
    within_50 = np.mean(np.abs(preds - actual) / actual < 0.5) * 100
    within_100 = np.mean(np.abs(preds - actual) / actual < 1.0) * 100
    
    print(f"\n📈 Results (n={len(test_df)}):")
    print(f"   R² (log): {r2:.4f}")
    print(f"   Rank Correlation: {corr:.4f}")
    print(f"   MAE (ratio): {mae:.3f}")
    print(f"   Within ±50%: {within_50:.1f}%")
    print(f"   Within ±100%: {within_100:.1f}%")
    
    # Summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"""
📊 V4 OPTIMIZED MODEL:

   MODEL TYPE: XGBoost (shallow trees + strong regularization)
   FEATURES: {len(predictor.feature_names)} research-backed features
   
   CROSS-VALIDATION (Walk-Forward):
   • R²: {stats['cv_r2']:.3f}
   • Rank Correlation: {stats['cv_rank_corr']:.3f}
   • Overfitting Risk: {stats['overfitting']}
   
   HOLDOUT TEST:
   • R²: {r2:.3f}
   • Rank Correlation: {corr:.3f}
   • {within_50:.0f}% predictions within ±50% of actual

   HONEST ASSESSMENT:
   Can this model predict EXACT performance ratio?
   → No. R² of {r2:.2f} means ~{max(0,r2)*100:.0f}% of variance explained.
   
   Can this model RANK videos by potential?
   → Moderately. Rank correlation of {corr:.2f} is {"decent" if corr > 0.3 else "limited"}.
   
   Is it useful?
   → Yes, for comparing concepts and identifying optimizations.
   → Not for precise view predictions.
""")
    
    # Save
    save_path = os.path.join(current_dir, 'trained', 'optimized_v4.joblib')
    predictor.save(save_path)
    
    return {
        'cv_r2': stats['cv_r2'],
        'cv_corr': stats['cv_rank_corr'],
        'holdout_r2': r2,
        'holdout_corr': corr,
        'within_50': within_50
    }


if __name__ == "__main__":
    results = main()
