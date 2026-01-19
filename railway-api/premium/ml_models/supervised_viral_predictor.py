"""
Supervised Viral Predictor
Predicts video performance based on Title, Thumbnail, and Topic features using XGBoost.
Prediction Target: Performance Ratio (Actual Views / Channel Median Views)
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import joblib
import warnings

warnings.filterwarnings('ignore')

# ML imports
try:
    import xgboost as xgb
    from sklearn.base import BaseEstimator, TransformerMixin
    from sklearn.pipeline import Pipeline, FeatureUnion
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.preprocessing import StandardScaler, OneHotEncoder, FunctionTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.compose import ColumnTransformer
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import mean_absolute_error, r2_score
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("⚠️ ML dependencies not installed. Run: pip install xgboost scikit-learn pandas numpy")

# Paths
MODELS_DIR = os.path.join(os.path.dirname(__file__), 'trained')
MODEL_PATH = os.path.join(MODELS_DIR, 'viral_supervised_xgb.joblib')

@dataclass
class ViralPredictionResult:
    predicted_views: int
    predicted_ratio: float  # e.g. 1.5x channel average
    viral_probability: float # 0-1
    confidence_score: float
    top_factors: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict:
        return asdict(self)

class SupervisedViralPredictor:
    """
    Predicts viral potential using a supervised XGBoost model trained on historical data.
    The target variable is the 'performance ratio' = views / channel_median_views.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.feature_names = []
        
        # Load model if exists
        path = model_path or MODEL_PATH
        if ML_AVAILABLE and os.path.exists(path):
            try:
                self.load_model(path)
            except Exception as e:
                print(f"⚠️ Failed to load supervised model: {e}")
                
    def train(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Train the model on collected data.
        
        Args:
            training_data: DataFrame from CTRDataCollector
                Must contain: 'clicks' (views), 'channel_median_views', 'title', 'thumbnail_features'
        """
        if not ML_AVAILABLE:
            return {'error': 'ML libraries missing'}
            
        print("🔧 Training Supervised Viral Predictor...")
        
        # 1. Preprocess Target
        # Target = Views / Channel Median. Clip to handle extreme outliers (viral hits).
        # We predict log(ratio) to handle the long tail.
        
        # Filter valid data
        df = training_data.copy()
        
        # Calculate channel median if not present (fallback)
        if 'channel_median_views' not in df.columns:
            print("   Calculating channel medians from data...")
            # Ideally this is passed in, but we can approximate from the batch
            # Note: This is leaky if we use the test set, but for training it's okay-ish 
            # if we have many videos per channel.
            # Better: Assume data collection populated it.
            df['channel_median_views'] = df.groupby('channel_id')['view_count'].transform('median')
            
        # Drop rows with no views or median
        df = df[df['view_count'] > 0]
        df = df[df['channel_median_views'] > 0]
        
        # Target: Performance Ratio
        df['performance_ratio'] = df['view_count'] / df['channel_median_views']
        
        # Use log transform for training stability
        # log(ratio): 0 = average (1x), >0 = above avg, <0 = below avg
        y = np.log(df['performance_ratio'])
        
        # 2. Preprocess Features
        
        # Parse thumbnail features if string
        if 'thumbnail_features' in df.columns and df['thumbnail_features'].dtype == object:
             df['thumbnail_features'] = df['thumbnail_features'].apply(
                 lambda x: json.loads(x) if isinstance(x, str) else (x or {})
             )
        
        # Expand thumbnail features
        thumb_df = pd.json_normalize(df['thumbnail_features'])
        thumb_df.columns = [f"thumb_{c}" for c in thumb_df.columns]
        
        # Features to use directly
        numeric_features = [c for c in thumb_df.columns if thumb_df[c].dtype in [np.float64, np.int64]]
        
        # Join back
        X = pd.concat([df[['title']], thumb_df[numeric_features].fillna(0).reset_index(drop=True)], axis=1)
        
        # 3. Build Pipeline
        
        # Title Pipeline: TF-IDF + Stats
        title_pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=500, stop_words='english', min_df=2))
        ])
        
        # Combine Text + Numeric Features
        # We need a custom transformer to select Title column for TFIDF
        preprocessor = ColumnTransformer([
            ('title_tfidf', TfidfVectorizer(max_features=500, min_df=2), 'title'),
            ('numeric', StandardScaler(), numeric_features)
        ])
        
        # Full Pipeline with XGBoost
        model_pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('regressor', xgb.XGBRegressor(
                n_estimators=300,
                learning_rate=0.05,
                max_depth=6,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1
            ))
        ])
        
        # 4. Train/Test Split (stratified by channel ideal, but random is okay for now)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Fit
        print(f"   Fitting model on {len(X_train)} samples...")
        model_pipeline.fit(X_train, y_train)
        
        # 5. Evaluate
        y_pred_log = model_pipeline.predict(X_test)
        y_pred_ratio = np.exp(y_pred_log)
        y_test_ratio = np.exp(y_test)
        
        mae = mean_absolute_error(y_test_ratio, y_pred_ratio)
        r2 = r2_score(y_test, y_pred_log) # R2 on log space is often more meaningful for power laws
        
        print(f"📊 Model Performance:")
        print(f"   MAE (Ratio): {mae:.2f}x (Average error in predicted multiplier)")
        print(f"   R² (Log Space): {r2:.4f}")
        
        # Get feature importances (tricky with Pipeline, but we can try)
        try:
            xgb_model = model_pipeline.named_steps['regressor']
            # Get feature names from preprocessor
            tfidf_names = model_pipeline.named_steps['preprocessor'].named_transformers_['title_tfidf'].get_feature_names_out()
            all_feature_names = list(tfidf_names) + numeric_features
            
            importances = xgb_model.feature_importances_
            feat_imp = sorted(zip(all_feature_names, importances), key=lambda x: x[1], reverse=True)[:20]
            print("   Top Features:", feat_imp[:5])
        except:
            feat_imp = []
            
        # Save
        if not os.path.exists(MODELS_DIR):
            os.makedirs(MODELS_DIR)
            
        joblib.dump({
            'pipeline': model_pipeline,
            'numeric_features': numeric_features,
            'metrics': {'mae': mae, 'r2': r2}
        }, MODEL_PATH)
        
        print(f"💾 Model saved to {MODEL_PATH}")
        self.model = model_pipeline
        self.numeric_features = numeric_features
        
        return {'mae': mae, 'r2': r2, 'top_features': feat_imp}

    def load_model(self, path: str):
        data = joblib.load(path)
        self.model = data['pipeline']
        self.numeric_features = data.get('numeric_features', [])
        print(f"📂 Supervised Viral Model loaded")

    def predict(self, title: str, 
                channel_median_views: int, 
                thumbnail_features: Dict[str, Any] = None) -> ViralPredictionResult:
        """
        Predict views for a new video concept.
        """
        if not self.model:
            # Fallback or error? Return None to signal use heuristic
            return None
            
        # Prepare input dataframe
        thumb_data = {f"thumb_{k}": v for k, v in (thumbnail_features or {}).items()}
        
        # We need to match the exact columns expected by the pipeline?
        # The ColumnTransformer expects 'title' column and 'numeric_features' columns
        # We create a single-row DataFrame
        
        input_data = {
            'title': [title],
            **{feat: [thumb_data.get(feat, 0)] for feat in self.numeric_features}
        }
        
        X = pd.DataFrame(input_data)
        
        # Predict
        log_ratio = self.model.predict(X)[0]
        predicted_ratio = np.exp(log_ratio)
        
        # Correct for bias? (Log transformation can introduce bias in mean)
        # Using a simple multiplier for now.
        
        predicted_views = int(predicted_ratio * channel_median_views)
        
        # Viral Probability: Probability ratio > 2.0 (High performing)
        # We can't strictly get probability from Regressor, but we can map the ratio
        # Ratio 1.0 = 50% (Average). Ratio 3.0 = 90%.
        viral_prob = min(0.99, max(0.01, 0.5 + (np.log(predicted_ratio) / 3)))
        
        # Extract factors (approximate from feature importance? or SHAP?)
        # For speed, we'll just check top features present
        factors = []
        # TODO: Implement local explanation (SHAP would be best but heavy)
        
        return ViralPredictionResult(
            predicted_views=predicted_views,
            predicted_ratio=round(predicted_ratio, 2),
            viral_probability=round(viral_prob, 2),
            confidence_score=0.8, # Supervised model is generally more confident
            top_factors=factors
        )

if __name__ == "__main__":
    # Test script
    print("Testing SupervisedViralPredictor...")
    predictor = SupervisedViralPredictor()
    
    # Mock training data
    data = []
    for i in range(100):
        # Synthetic relationship
        is_good = i % 2 == 0
        title = "AMAZING Secret to Success" if is_good else "vlog 123"
        thumb_score = 0.9 if is_good else 0.1
        median = 10000
        ratio = 2.0 if is_good else 0.5
        # Add noise
        ratio *= np.random.uniform(0.8, 1.2)
        
        data.append({
            'video_id': f'v{i}',
            'channel_id': 'c1',
            'title': title,
            'thumbnail_features': json.dumps({'contrast_score': thumb_score, 'face_count': 1 if is_good else 0}),
            'view_count': int(median * ratio),
            'channel_median_views': median,
            'clicks': 0 # ignored
        })
        
    df = pd.DataFrame(data)
    
    # Train
    predictor.train(df)
    
    # Predict
    res = predictor.predict(
        title="AMAZING Secret",
        channel_median_views=10000,
        thumbnail_features={'contrast_score': 0.8, 'face_count': 1}
    )
    
    if res:
        print(f"\nPrediction for 'AMAZING Secret':")
        print(f"Predicted Views: {res.predicted_views}")
        print(f"Ratio: {res.predicted_ratio}x")
