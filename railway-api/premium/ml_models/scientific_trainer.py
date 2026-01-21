"""
Scientific Trainer
------------------
Trains niche-specific machine learning models to replace heuristics.

Primary Models:
1. Viral Benchmark Model (XGBoost):
   - Predicts 'Expected Views' for a video based on channel stats and metadata.
   - Used to calculate Viral Score (Actual / Expected) scientifically.
   - Replaces hardcoded weightings in scoring_engine.py.

Usage:
    trainer = NicheTrainer()
    metrics = trainer.train_all_niches("training_data/")
    trainer.save_models("railway-api/premium/ml_models/trained/")
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import xgboost as xgb
from sklearn.model_selection import train_test_split, KFold
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder

class NicheTrainer:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_cols = [
            'subscriber_count_log',
            'video_count_log',
            'title_length',
            'title_has_question',
            'title_has_number',
            'tags_count',
            'duration_seconds'
        ]
        
    def load_data(self, data_dir: str) -> pd.DataFrame:
        """Load and merge all JSON datasets from the data directory."""
        all_data = []
        for filename in os.listdir(data_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(data_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        # Extract niche from filename if not in data
                        niche_guess = filename.split('_')[0]
                        for entry in data:
                            if 'niche' not in entry:
                                entry['niche'] = niche_guess
                        all_data.extend(data)
                except Exception as e:
                    print(f"Skipping {filename}: {e}")
        
        df = pd.DataFrame(all_data)
        print(f"Loaded {len(df)} total samples.")
        return df

    def preprocess_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Feature engineering for the benchmark model."""
        # Clean numeric fields
        df['view_count'] = pd.to_numeric(df['view_count'], errors='coerce').fillna(0)
        df['like_count'] = pd.to_numeric(df['like_count'], errors='coerce').fillna(0)
        # We need subscriber count, but data_collector_v2 current implementation
        # might verify if it fetched channel stats. 
        # CAUTION: The collector fetched video details which includes channelId, 
        # but not channel subscriber count directly in the 'video' resource. 
        # We might need to estimate or drop this feature if missing.
        # For this v1 implementation, we will use 'view_count' as target and 
        # try to use 'like_count' or derived stats as features, 
        # BUT 'like_count' is highly correlated with target (leakage).
        
        # Valid Features (Metadata & Channel Identity)
        # We assume we want to predict performance based on METADATA mainly.
        
        # Duration parsing (ISO 8601 to seconds)
        def parse_duration(pt_str):
            try:
                import isodate
                return isodate.parse_duration(pt_str).total_seconds()
            except:
                return 0
        
        if 'duration_iso' in df.columns:
            df['duration_seconds'] = df['duration_iso'].apply(parse_duration)
        else:
            df['duration_seconds'] = 0
            
        # Title features
        df['title'] = df['title'].fillna("")
        df['title_length'] = df['title'].apply(len)
        df['title_has_question'] = df['title'].apply(lambda x: 1 if '?' in x else 0)
        df['title_has_number'] = df['title'].apply(lambda x: 1 if any(c.isdigit() for c in x) else 0)
        df['tags_count'] = df['tags'].apply(lambda x: len(x) if isinstance(x, list) else 0)
        
        # Proxy for channel size if subs missing: median views of channel in dataset
        # (This is a rough heuristic, but better than nothing for a snapshot)
        if 'channel_id' in df.columns:
            channel_medians = df.groupby('channel_id')['view_count'].transform('median')
            df['channel_baseline_views'] = channel_medians
            df['subscriber_count_log'] = np.log1p(channel_medians) # Proxy
        else:
            df['subscriber_count_log'] = 0

        # Log transform targets and skewed features
        df['video_count_log'] = 0 # Placeholder
        
        # Remove outliers (e.g. 0 views)
        df = df[df['view_count'] > 100].copy()
        
        return df

    def train_all_niches(self, data_dir: str) -> Dict[str, Dict]:
        """Train a separate model for each Niche."""
        df = self.load_data(data_dir)
        df = self.preprocess_features(df)
        
        results = {}
        unique_niches = df['niche'].unique()
        
        for niche in unique_niches:
            print(f"\nTraining Benchmark Model for Niche: {niche}")
            niche_df = df[df['niche'] == niche]
            
            if len(niche_df) < 50:
                print(f"  ⚠️ Warning: Only {len(niche_df)} samples. Skipping or training weak model.")
                if len(niche_df) < 10:
                    continue
            
            # Prepare X, y
            # We predict log(views) to handle exponential scale
            target_col = 'view_count'
            y = np.log1p(niche_df[target_col])
            
            # Features
            # Note: channel_baseline_views is a strong predictor (autoregressive), 
            # but valid for benchmarking "performance relative to channel norm".
            features = ['duration_seconds', 'title_length', 'title_has_question', 
                        'title_has_number', 'tags_count', 'subscriber_count_log']
            
            X = niche_df[features].fillna(0)
            
            # Split
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train XGBoost
            model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                random_state=42
            )
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            preds = model.predict(X_test_scaled)
            mae = mean_absolute_error(y_test, preds)
            r2 = r2_score(y_test, preds)
            
            # Convert MAE back to view multiplier
            # MAE of 0.5 in log scale means approx exp(0.5) = 1.6x error factor
            error_factor = np.exp(mae)
            
            print(f"  R²: {r2:.3f}")
            print(f"  Log MAE: {mae:.3f} (Avg error factor: {error_factor:.2f}x)")
            
            # Feature Importance
            importances = dict(zip(features, model.feature_importances_))
            top_feat = max(importances.items(), key=lambda x: x[1])
            print(f"  Top Feature: {top_feat[0]} ({top_feat[1]:.2f})")
            
            # Store
            self.models[niche] = model
            self.scalers[niche] = scaler
            results[niche] = {
                'r2': r2, 
                'mae': mae, 
                'error_factor': error_factor,
                'top_feature': top_feat
            }
            
        return results

    def save_models(self, save_dir: str):
        """Save all trained models."""
        os.makedirs(save_dir, exist_ok=True)
        for niche, model in self.models.items():
            # Clean filename
            slug = niche.lower().replace(" & ", "_").replace(" ", "_").replace("/", "_")
            path = os.path.join(save_dir, f"benchmark_{slug}.joblib")
            
            bundle = {
                'model': model,
                'scaler': self.scalers[niche],
                'features': self.feature_cols,
                'niche': niche
            }
            joblib.dump(bundle, path)
            print(f"Saved model for {niche} to {path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="training_data", help="Data directory")
    parser.add_argument("--out", default="railway-api/premium/ml_models/trained", help="Output directory")
    args = parser.parse_args()
    
    trainer = NicheTrainer()
    if os.path.exists(args.data):
        trainer.train_all_niches(args.data)
        trainer.save_models(args.out)
    else:
        print(f"Data directory {args.data} not found.")
