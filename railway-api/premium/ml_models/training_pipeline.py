"""
Premium Analysis - ML Model Training Pipeline
Orchestrates training of all ML models from collected data.

Models:
1. CTR Predictor (XGBoost)
2. Views Velocity Predictor (XGBoost)
3. Content Clustering (K-means/DBSCAN)

Data Sources:
- Supabase video_performance table
- Supabase thumbnail_features table
- YouTube API (for fresh data)
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd
import warnings

warnings.filterwarnings('ignore')

# ML imports
try:
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    import xgboost as xgb
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


@dataclass
class TrainingResult:
    """Result of model training."""
    model_name: str
    success: bool
    metrics: Dict
    training_samples: int
    training_time_seconds: float
    model_path: str
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ModelTrainingPipeline:
    """
    Orchestrates training of all premium ML models.
    
    Usage:
        pipeline = ModelTrainingPipeline()
        results = pipeline.train_all_models(training_data)
    """
    
    MODELS_DIR = os.path.join(os.path.dirname(__file__), 'ml_models', 'trained')
    
    def __init__(self):
        # Create models directory if needed
        os.makedirs(self.MODELS_DIR, exist_ok=True)
    
    def train_all_models(self, 
                         video_data: pd.DataFrame,
                         thumbnail_features: pd.DataFrame = None) -> Dict[str, TrainingResult]:
        """
        Train all models from provided data.
        
        Args:
            video_data: DataFrame with video performance data
            thumbnail_features: DataFrame with thumbnail features
            
        Returns:
            Dict of model names to TrainingResult
        """
        if not ML_AVAILABLE:
            return {'error': TrainingResult(
                model_name='all',
                success=False,
                metrics={},
                training_samples=0,
                training_time_seconds=0,
                model_path='',
                error='ML dependencies not available'
            )}
        
        results = {}
        
        # 1. Train CTR Predictor
        results['ctr_predictor'] = self._train_ctr_model(video_data, thumbnail_features)
        
        # 2. Train Views Velocity Predictor
        results['views_predictor'] = self._train_views_model(video_data)

        # 3. Train Viral Supervised Predictor
        results['viral_predictor'] = self._train_viral_model(video_data, thumbnail_features)
        
        return results
    
    def _train_viral_model(self, 
                           video_data: pd.DataFrame,
                           thumbnail_features: pd.DataFrame) -> TrainingResult:
        """Train Supervised Viral Predictor."""
        import time
        start_time = time.time()
        
        try:
            # Import here to avoid circular dependencies
            try:
                from premium.ml_models.supervised_viral_predictor import SupervisedViralPredictor
            except ImportError:
                from .supervised_viral_predictor import SupervisedViralPredictor

            # Prepare data
            # Merge with thumbnail features
            if thumbnail_features is not None and len(thumbnail_features) > 0:
                df = video_data.merge(
                    thumbnail_features, 
                    on='video_id', 
                    how='left' # Left join to keep all videos even without thumb features
                )
            else:
                df = video_data.copy()

            # Ensure we have required columns
            if 'title' not in df.columns:
                 return TrainingResult(
                    model_name='viral_predictor',
                    success=False,
                    metrics={},
                    training_samples=len(df),
                    training_time_seconds=0,
                    model_path='',
                    error='Missing title column'
                )

            # Train
            predictor = SupervisedViralPredictor()
            metrics = predictor.train(df)
            
            if 'error' in metrics:
                 return TrainingResult(
                    model_name='viral_predictor',
                    success=False,
                    metrics={},
                    training_samples=len(df),
                    training_time_seconds=time.time() - start_time,
                    model_path='',
                    error=metrics['error']
                )

            return TrainingResult(
                model_name='viral_predictor',
                success=True,
                metrics=metrics,
                training_samples=len(df),
                training_time_seconds=round(time.time() - start_time, 2),
                model_path=os.path.join(self.MODELS_DIR, 'viral_supervised_xgb.joblib')
            )
            
        except Exception as e:
            return TrainingResult(
                model_name='viral_predictor',
                success=False,
                metrics={},
                training_samples=0,
                training_time_seconds=time.time() - start_time,
                model_path='',
                error=str(e)
            )
    
    def _train_ctr_model(self, 
                         video_data: pd.DataFrame,
                         thumbnail_features: pd.DataFrame) -> TrainingResult:
        """Train CTR prediction model."""
        import time
        start_time = time.time()
        
        try:
            # Check if we have enough data
            if len(video_data) < 50:
                return TrainingResult(
                    model_name='ctr_predictor',
                    success=False,
                    metrics={},
                    training_samples=len(video_data),
                    training_time_seconds=0,
                    model_path='',
                    error=f'Not enough data ({len(video_data)} samples, need 50+)'
                )
            
            # Prepare features
            # If thumbnail features available, merge
            if thumbnail_features is not None and len(thumbnail_features) > 0:
                df = video_data.merge(
                    thumbnail_features, 
                    on='video_id', 
                    how='inner'
                )
            else:
                df = video_data.copy()
            
            # Create CTR proxy if not available
            if 'ctr_proxy' not in df.columns:
                # CTR proxy = views in first 48h / impressions estimate
                # Simplified: use view velocity
                df['ctr_proxy'] = df.apply(
                    lambda x: min(12, max(1, x['view_count'] / max(x.get('subscriber_count', 10000) * 0.1, 1) * 5)),
                    axis=1
                )
            
            # Feature columns
            feature_cols = [
                col for col in df.columns 
                if col not in ['video_id', 'channel_id', 'title', 'published_at', 
                              'ctr_proxy', 'view_count', 'created_at', 'updated_at']
                and df[col].dtype in [np.float64, np.int64, np.float32, np.int32, bool]
            ]
            
            if len(feature_cols) < 5:
                return TrainingResult(
                    model_name='ctr_predictor',
                    success=False,
                    metrics={},
                    training_samples=len(df),
                    training_time_seconds=time.time() - start_time,
                    model_path='',
                    error=f'Not enough features ({len(feature_cols)} found)'
                )
            
            # Prepare X and y
            X = df[feature_cols].fillna(0)
            y = df['ctr_proxy']
            
            # Split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train XGBoost
            model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test_scaled)
            mae = np.mean(np.abs(y_test - y_pred))
            rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))
            r2 = 1 - (np.sum((y_test - y_pred) ** 2) / np.sum((y_test - np.mean(y_test)) ** 2))
            
            # Save model
            model_path = os.path.join(self.MODELS_DIR, 'ctr_global.joblib')
            joblib.dump({
                'model': model,
                'scaler': scaler,
                'feature_cols': feature_cols,
                'trained_at': datetime.now().isoformat()
            }, model_path)
            
            return TrainingResult(
                model_name='ctr_predictor',
                success=True,
                metrics={
                    'mae': round(mae, 4),
                    'rmse': round(rmse, 4),
                    'r2': round(r2, 4),
                    'features_used': len(feature_cols)
                },
                training_samples=len(X_train),
                training_time_seconds=round(time.time() - start_time, 2),
                model_path=model_path
            )
            
        except Exception as e:
            return TrainingResult(
                model_name='ctr_predictor',
                success=False,
                metrics={},
                training_samples=0,
                training_time_seconds=time.time() - start_time,
                model_path='',
                error=str(e)
            )
    
    def _train_views_model(self, video_data: pd.DataFrame) -> TrainingResult:
        """Train views velocity prediction model."""
        import time
        start_time = time.time()
        
        try:
            # Check data requirements
            required_cols = ['views_24h', 'view_count']
            missing = [c for c in required_cols if c not in video_data.columns]
            
            if missing:
                # Create synthetic early metrics if not available
                video_data = video_data.copy()
                if 'views_24h' not in video_data.columns:
                    # Estimate: 24h views are typically 10-30% of total
                    video_data['views_24h'] = video_data['view_count'] * np.random.uniform(0.1, 0.3, len(video_data))
                if 'views_7d' not in video_data.columns:
                    video_data['views_7d'] = video_data['view_count'] * np.random.uniform(0.4, 0.7, len(video_data))
            
            if len(video_data) < 30:
                return TrainingResult(
                    model_name='views_predictor',
                    success=False,
                    metrics={},
                    training_samples=len(video_data),
                    training_time_seconds=0,
                    model_path='',
                    error=f'Not enough data ({len(video_data)} samples)'
                )
            
            # Features
            feature_cols = ['views_24h']
            if 'like_count' in video_data.columns:
                feature_cols.append('like_count')
            if 'comment_count' in video_data.columns:
                feature_cols.append('comment_count')
            if 'subscriber_count' in video_data.columns:
                feature_cols.append('subscriber_count')
            
            # Target: log(views_7d)
            X = video_data[feature_cols].fillna(0)
            y = np.log1p(video_data.get('views_7d', video_data['view_count'] * 0.6))
            
            # Split and scale
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train
            model = xgb.XGBRegressor(
                n_estimators=80,
                max_depth=4,
                learning_rate=0.1,
                random_state=42
            )
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test_scaled)
            mae = np.mean(np.abs(y_test - y_pred))
            rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))
            
            # Save
            model_path = os.path.join(self.MODELS_DIR, 'views_predictor.joblib')
            joblib.dump({
                'model': model,
                'scaler': scaler,
                'feature_cols': feature_cols,
                'trained_at': datetime.now().isoformat()
            }, model_path)
            
            return TrainingResult(
                model_name='views_predictor',
                success=True,
                metrics={
                    'mae': round(mae, 4),
                    'rmse': round(rmse, 4),
                    'features_used': len(feature_cols)
                },
                training_samples=len(X_train),
                training_time_seconds=round(time.time() - start_time, 2),
                model_path=model_path
            )
            
        except Exception as e:
            return TrainingResult(
                model_name='views_predictor',
                success=False,
                metrics={},
                training_samples=0,
                training_time_seconds=time.time() - start_time,
                model_path='',
                error=str(e)
            )
    
    def load_training_data_from_supabase(self, supabase_url: str, supabase_key: str) -> pd.DataFrame:
        """Load training data from Supabase."""
        import requests
        
        # Fetch video_performance
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}'
        }
        
        response = requests.get(
            f"{supabase_url}/rest/v1/video_performance?select=*",
            headers=headers
        )
        
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        else:
            return pd.DataFrame()
    
    def get_trained_models(self) -> Dict[str, Dict]:
        """Get info about currently trained models."""
        models = {}
        
        for model_file in ['ctr_global.joblib', 'views_predictor.joblib', 'viral_supervised_xgb.joblib']:
            path = os.path.join(self.MODELS_DIR, model_file)
            if os.path.exists(path):
                try:
                    data = joblib.load(path)
                    models[model_file.replace('.joblib', '')] = {
                        'trained_at': data.get('trained_at', 'unknown'),
                        'features': len(data.get('feature_cols', [])),
                        'path': path
                    }
                except:
                    pass
        
        return models


# === Quick test ===
if __name__ == "__main__":
    print("🧪 Testing Model Training Pipeline...")
    
    pipeline = ModelTrainingPipeline()
    
    # Create sample training data
    np.random.seed(42)
    sample_data = pd.DataFrame({
        'video_id': [f'vid_{i}' for i in range(100)],
        'channel_id': ['channel_1'] * 100,
        'view_count': np.random.randint(1000, 100000, 100),
        'like_count': np.random.randint(50, 5000, 100),
        'comment_count': np.random.randint(10, 500, 100),
        'subscriber_count': [10000] * 100,
        'views_24h': np.random.randint(100, 10000, 100),
        'views_7d': np.random.randint(500, 50000, 100),
        'face_count': np.random.randint(0, 3, 100),
        'word_count': np.random.randint(0, 8, 100),
        'avg_saturation': np.random.uniform(0.2, 0.8, 100),
        'contrast_score': np.random.uniform(0.1, 0.5, 100)
    })
    
    results = pipeline.train_all_models(sample_data)
    
    print(f"\n📊 Training Results:")
    for model_name, result in results.items():
        print(f"\n   {model_name}:")
        print(f"      Success: {result.success}")
        if result.success:
            print(f"      Samples: {result.training_samples}")
            print(f"      Time: {result.training_time_seconds}s")
            print(f"      Metrics: {result.metrics}")
        else:
            print(f"      Error: {result.error}")
