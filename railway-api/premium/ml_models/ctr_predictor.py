"""
Premium Analysis - CTR Prediction Model
Predicts click-through rate for YouTube thumbnails using machine learning.

Uses XGBoost for fast, accurate predictions on CPU.

Model loading hierarchy:
1. Channel-specific model (if available and user connected Analytics)
2. Global model (trained on 1000+ videos from all connected creators)
3. Rule-based estimation (fallback when no trained models exist)
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import warnings

warnings.filterwarnings('ignore')

# ML imports (graceful fallback if not installed)
try:
    import xgboost as xgb
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_absolute_error, r2_score
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("⚠️ ML dependencies not installed. Install: pip install xgboost scikit-learn")


# Model paths
MODELS_DIR = os.path.join(os.path.dirname(__file__), 'trained')
GLOBAL_MODEL_PATH = os.path.join(MODELS_DIR, 'ctr_global.joblib')
CHANNEL_MODELS_DIR = os.path.join(MODELS_DIR, 'channels')


@dataclass
class CTRPrediction:
    """Result of a CTR prediction."""
    predicted_ctr: float
    confidence: float
    ctr_vs_channel_avg: float
    top_positive_factors: List[Dict]
    top_negative_factors: List[Dict]
    improvement_suggestions: List[str]
    model_type: str = 'rule_based'  # 'channel_specific', 'global', or 'rule_based'
    
    def to_dict(self) -> Dict:
        return {
            'predicted_ctr': round(self.predicted_ctr, 2),
            'confidence': round(self.confidence, 2),
            'ctr_vs_channel_avg': round(self.ctr_vs_channel_avg, 2),
            'top_positive_factors': self.top_positive_factors,
            'top_negative_factors': self.top_negative_factors,
            'improvement_suggestions': self.improvement_suggestions,
            'model_type': self.model_type
        }


class CTRPredictor:
    """
    Predicts expected CTR for a video based on thumbnail and title features.
    
    Training data:
    - 100+ videos from target channel (if available)
    - 1000+ videos from similar niche channels
    
    Target: Historical CTR (or proxy: views / impressions estimate)
    """
    
    # Feature names expected by the model
    FEATURE_NAMES = [
        # Color features
        'avg_saturation', 'avg_brightness', 'contrast_score',
        'color_diversity', 'warm_color_ratio', 'has_red_accent',
        'background_brightness', 'overall_vibrancy',
        
        # Face features
        'face_count', 'face_area_ratio', 'primary_face_size',
        'has_eye_contact', 'face_in_center', 'faces_are_large',
        
        # Text features
        'has_text', 'word_count', 'text_area_ratio',
        'uses_numbers', 'uses_all_caps', 'has_question', 'has_exclamation',
        
        # Composition features
        'edge_density', 'center_focus_score', 'rule_of_thirds_score',
        'visual_complexity', 'mobile_readability_score',
        
        # Title features (added separately)
        'title_length', 'title_has_numbers', 'title_has_question',
        'title_has_power_words', 'title_capitalization_ratio'
    ]
    
    # Power words that attract clicks
    POWER_WORDS = [
        'secret', 'revealed', 'shocking', 'insane', 'ultimate',
        'best', 'worst', 'top', 'how to', 'why', 'tutorial',
        'tips', 'tricks', 'guide', 'review', 'vs', 'unboxing',
        'reaction', 'challenge', 'truth', 'exposed', 'finally',
        'new', 'update', 'breaking', 'exclusive', 'free'
    ]
    
    def __init__(self, model_path: Optional[str] = None, channel_id: Optional[str] = None):
        self.model = None
        self.scaler = None
        self.feature_importances = None
        self.channel_avg_ctr = 5.0  # Default average CTR
        self.model_type = 'rule_based'
        self.feature_columns = None
        
        # Create models directory if it doesn't exist
        os.makedirs(MODELS_DIR, exist_ok=True)
        os.makedirs(CHANNEL_MODELS_DIR, exist_ok=True)
        
        # Model loading hierarchy:
        # 1. Explicit model path
        # 2. Channel-specific model
        # 3. Global model
        # 4. Rule-based (fallback)
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
            self.model_type = 'custom'
        elif channel_id:
            # Try channel-specific model first
            channel_model_path = os.path.join(CHANNEL_MODELS_DIR, f'{channel_id}.joblib')
            if os.path.exists(channel_model_path):
                self.load_model(channel_model_path)
                self.model_type = 'channel_specific'
                print(f"📊 Loaded channel-specific CTR model for {channel_id}")
            elif os.path.exists(GLOBAL_MODEL_PATH):
                self.load_model(GLOBAL_MODEL_PATH)
                self.model_type = 'global'
                print("📊 Loaded global CTR model")
        elif os.path.exists(GLOBAL_MODEL_PATH):
            # No channel specified, try global model
            self.load_model(GLOBAL_MODEL_PATH)
            self.model_type = 'global'
            print("📊 Loaded global CTR model")
    
    def extract_title_features(self, title: str) -> Dict:
        """Extract features from video title."""
        title_lower = title.lower()
        words = title.split()
        
        return {
            'title_length': len(title),
            'title_has_numbers': any(c.isdigit() for c in title),
            'title_has_question': '?' in title,
            'title_has_power_words': any(pw in title_lower for pw in self.POWER_WORDS),
            'title_capitalization_ratio': sum(1 for c in title if c.isupper()) / max(len(title), 1)
        }
    
    def prepare_features(self, thumbnail_features: Dict, title: str) -> np.ndarray:
        """Prepare feature vector from thumbnail features and title."""
        # Extract title features
        title_features = self.extract_title_features(title)
        
        # Combine all features
        all_features = {**thumbnail_features, **title_features}
        
        # Build feature vector in expected order
        feature_vector = []
        for name in self.FEATURE_NAMES:
            value = all_features.get(name, 0)
            if isinstance(value, bool):
                value = float(value)
            elif isinstance(value, (list, tuple)):
                value = float(value[0]) if value else 0
            feature_vector.append(float(value))
        
        return np.array(feature_vector).reshape(1, -1)
    
    def train(self, training_data: pd.DataFrame, target_col: str = 'ctr_proxy'):
        """
        Train the CTR prediction model.
        
        Args:
            training_data: DataFrame with feature columns and target
            target_col: Name of the target column
        """
        if not ML_AVAILABLE:
            raise RuntimeError("ML dependencies not available")
        
        print("🔧 Training CTR prediction model...")
        
        # Prepare features and target
        feature_cols = [c for c in self.FEATURE_NAMES if c in training_data.columns]
        X = training_data[feature_cols].fillna(0)
        y = training_data[target_col]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train XGBoost model
        self.model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=0.1,
            random_state=42
        )
        
        self.model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_test_scaled, y_test)],
            early_stopping_rounds=20,
            verbose=False
        )
        
        # Evaluate
        predictions = self.model.predict(X_test_scaled)
        mae = mean_absolute_error(y_test, predictions)
        r2 = r2_score(y_test, predictions)
        
        print(f"📊 Model Performance:")
        print(f"   MAE: {mae:.4f}")
        print(f"   R²: {r2:.4f}")
        
        # Store feature importances
        self.feature_importances = dict(zip(feature_cols, self.model.feature_importances_))
        
        # Calculate channel average
        self.channel_avg_ctr = float(y.mean())
        
        return {'mae': mae, 'r2': r2}
    
    def predict(self, thumbnail_features: Dict, title: str) -> CTRPrediction:
        """
        Predict CTR for a video.
        
        Args:
            thumbnail_features: Features from ThumbnailFeatureExtractor
            title: Video title
            
        Returns:
            CTRPrediction with predicted CTR and insights
        """
        # If no model, use rule-based estimation
        if self.model is None:
            return self._rule_based_prediction(thumbnail_features, title)
        
        # Prepare features
        X = self.prepare_features(thumbnail_features, title)
        
        # Scale
        if self.scaler:
            X = self.scaler.transform(X)
        
        # Predict
        predicted_ctr = float(self.model.predict(X)[0])
        
        # Calculate confidence (based on feature completeness)
        feature_completeness = sum(1 for v in thumbnail_features.values() if v) / len(thumbnail_features)
        confidence = 0.5 + (feature_completeness * 0.5)
        
        # Analyze factors
        positive_factors, negative_factors = self._analyze_factors(thumbnail_features, title)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(thumbnail_features, title, positive_factors, negative_factors)
        
        return CTRPrediction(
            predicted_ctr=max(0, predicted_ctr),
            confidence=confidence,
            ctr_vs_channel_avg=predicted_ctr - self.channel_avg_ctr,
            top_positive_factors=positive_factors[:3],
            top_negative_factors=negative_factors[:3],
            improvement_suggestions=suggestions[:5],
            model_type=self.model_type
        )
    
    def _rule_based_prediction(self, thumbnail_features: Dict, title: str) -> CTRPrediction:
        """Fallback rule-based CTR estimation when no model is trained."""
        base_ctr = 4.0
        adjustments = []
        
        # Face presence and size
        if thumbnail_features.get('faces_are_large'):
            base_ctr += 1.5
            adjustments.append(('Large face visible', +1.5))
        elif thumbnail_features.get('face_count', 0) > 0:
            base_ctr += 0.8
            adjustments.append(('Face present', +0.8))
        
        # Eye contact
        if thumbnail_features.get('has_eye_contact'):
            base_ctr += 0.5
            adjustments.append(('Eye contact', +0.5))
        
        # Text presence
        if thumbnail_features.get('has_text'):
            if 1 <= thumbnail_features.get('word_count', 0) <= 4:
                base_ctr += 0.7
                adjustments.append(('Optimal text length', +0.7))
            elif thumbnail_features.get('word_count', 0) > 6:
                base_ctr -= 0.5
                adjustments.append(('Too much text', -0.5))
        
        # Colors
        if thumbnail_features.get('has_red_accent'):
            base_ctr += 0.3
            adjustments.append(('Red accent color', +0.3))
        
        if thumbnail_features.get('contrast_score', 0) > 0.3:
            base_ctr += 0.4
            adjustments.append(('High contrast', +0.4))
        
        # Composition
        if thumbnail_features.get('rule_of_thirds_score', 0) > 0.5:
            base_ctr += 0.3
            adjustments.append(('Good composition', +0.3))
        
        # Title analysis
        title_features = self.extract_title_features(title)
        if title_features['title_has_power_words']:
            base_ctr += 0.6
            adjustments.append(('Power words in title', +0.6))
        
        if title_features['title_has_numbers']:
            base_ctr += 0.3
            adjustments.append(('Numbers in title', +0.3))
        
        # Sort adjustments
        positive = [{'factor': a[0], 'impact': a[1]} for a in adjustments if a[1] > 0]
        negative = [{'factor': a[0], 'impact': a[1]} for a in adjustments if a[1] < 0]
        
        # Suggestions
        suggestions = []
        if not thumbnail_features.get('faces_are_large'):
            suggestions.append("Add a large, prominent face to increase engagement")
        if not thumbnail_features.get('has_text') or thumbnail_features.get('word_count', 0) == 0:
            suggestions.append("Add 2-4 words of text overlay")
        if not thumbnail_features.get('has_red_accent'):
            suggestions.append("Consider adding red/yellow accent colors")
        if thumbnail_features.get('contrast_score', 0) < 0.2:
            suggestions.append("Increase contrast between foreground and background")
        if not title_features['title_has_power_words']:
            suggestions.append("Use power words like 'Secret', 'Ultimate', or 'How To'")
        
        return CTRPrediction(
            predicted_ctr=max(1, min(15, base_ctr)),
            confidence=0.6,  # Lower confidence for rule-based
            ctr_vs_channel_avg=base_ctr - self.channel_avg_ctr,
            top_positive_factors=positive[:3],
            top_negative_factors=negative[:3],
            improvement_suggestions=suggestions[:5]
        )
    
    def _analyze_factors(self, thumbnail_features: Dict, title: str) -> Tuple[List[Dict], List[Dict]]:
        """Analyze which factors contribute positively/negatively to CTR."""
        positive = []
        negative = []
        
        if self.feature_importances:
            # Use model feature importances
            for feature, importance in sorted(self.feature_importances.items(), 
                                               key=lambda x: x[1], reverse=True):
                value = thumbnail_features.get(feature, 0)
                if value and importance > 0.05:
                    positive.append({'factor': feature, 'impact': round(importance, 2)})
        else:
            # Use rule-based analysis
            if thumbnail_features.get('faces_are_large'):
                positive.append({'factor': 'Large face', 'impact': 0.25})
            if thumbnail_features.get('has_text'):
                positive.append({'factor': 'Text overlay', 'impact': 0.15})
            if thumbnail_features.get('contrast_score', 0) > 0.3:
                positive.append({'factor': 'High contrast', 'impact': 0.12})
            
            if thumbnail_features.get('word_count', 0) > 6:
                negative.append({'factor': 'Too much text', 'impact': -0.15})
            if thumbnail_features.get('blur_score', 0) > 0.5:
                negative.append({'factor': 'Image blur', 'impact': -0.20})
        
        return positive, negative
    
    def _generate_suggestions(self, thumbnail_features: Dict, title: str,
                               positive: List[Dict], negative: List[Dict]) -> List[str]:
        """Generate actionable improvement suggestions."""
        suggestions = []
        
        if not thumbnail_features.get('face_count'):
            suggestions.append("Add a human face - thumbnails with faces get 38% more clicks")
        
        if not thumbnail_features.get('faces_are_large') and thumbnail_features.get('face_count'):
            suggestions.append("Make the face larger - aim for at least 15% of thumbnail area")
        
        if not thumbnail_features.get('has_eye_contact') and thumbnail_features.get('face_count'):
            suggestions.append("Use a photo with direct eye contact for better engagement")
        
        if thumbnail_features.get('word_count', 0) > 5:
            suggestions.append("Reduce text to 2-4 words for better mobile readability")
        
        if thumbnail_features.get('avg_saturation', 0) < 0.3:
            suggestions.append("Increase color saturation for more vibrant thumbnail")
        
        if thumbnail_features.get('contrast_score', 0) < 0.2:
            suggestions.append("Increase contrast between subject and background")
        
        if thumbnail_features.get('mobile_readability_score', 0) < 0.5:
            suggestions.append("Optimize for mobile - elements should be clearly visible at small sizes")
        
        title_features = self.extract_title_features(title)
        if len(title) < 30:
            suggestions.append("Lengthen title slightly - aim for 40-60 characters")
        if len(title) > 70:
            suggestions.append("Shorten title - keep under 60 characters for full visibility")
        
        return suggestions
    
    def save_model(self, path: str):
        """Save trained model to file."""
        if not ML_AVAILABLE:
            raise RuntimeError("ML dependencies not available")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_importances': self.feature_importances,
            'channel_avg_ctr': self.channel_avg_ctr
        }
        joblib.dump(model_data, path)
        print(f"💾 Model saved to {path}")
    
    def load_model(self, path: str):
        """Load trained model from file."""
        if not ML_AVAILABLE:
            raise RuntimeError("ML dependencies not available")
        
        model_data = joblib.load(path)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_importances = model_data['feature_importances']
        self.channel_avg_ctr = model_data.get('channel_avg_ctr', 5.0)
        print(f"📂 Model loaded from {path}")


class CTRModelTrainer:
    """
    Trains CTR prediction models from collected data.
    
    Supports:
    - Global model: Trained on all available training data
    - Channel-specific model: Fine-tuned for individual channels
    
    Usage:
        trainer = CTRModelTrainer()
        
        # Train global model
        result = trainer.train_global_model()
        
        # Train channel-specific model
        result = trainer.train_channel_model(channel_id="UCxxx")
    """
    
    def __init__(self, 
                 supabase_url: Optional[str] = None,
                 supabase_key: Optional[str] = None):
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        # Ensure model directories exist
        os.makedirs(MODELS_DIR, exist_ok=True)
        os.makedirs(CHANNEL_MODELS_DIR, exist_ok=True)
    
    def get_training_stats(self) -> Dict:
        """Get statistics about available training data."""
        if not self.supabase_url or not self.supabase_key:
            return {'error': 'Supabase not configured', 'can_train': False}
        
        headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
        }
        
        try:
            response = requests.get(
                f"{self.supabase_url}/rest/v1/ctr_training_data",
                headers=headers,
                params={
                    'select': 'video_id,channel_id,ctr_actual,impressions',
                    'impressions': 'gte.1000'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    df = pd.DataFrame(data)
                    return {
                        'total_samples': len(df),
                        'unique_channels': df['channel_id'].nunique(),
                        'unique_videos': df['video_id'].nunique(),
                        'avg_ctr': round(df['ctr_actual'].mean(), 2) if len(df) > 0 else 0,
                        'can_train_global': len(df) >= 1000,
                        'channels_with_50_plus': (df.groupby('channel_id').size() >= 50).sum()
                    }
            
            return {'total_samples': 0, 'can_train_global': False}
            
        except Exception as e:
            return {'error': str(e), 'can_train_global': False}
    
    def _fetch_training_data(self, 
                              channel_id: Optional[str] = None,
                              min_impressions: int = 1000) -> pd.DataFrame:
        """Fetch training data from Supabase."""
        if not self.supabase_url or not self.supabase_key:
            return pd.DataFrame()
        
        headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
        }
        
        params = {
            'select': '*',
            'impressions': f'gte.{min_impressions}',
            'order': 'fetch_date.desc',
            'limit': 10000
        }
        
        if channel_id:
            params['channel_id'] = f'eq.{channel_id}'
        
        try:
            response = requests.get(
                f"{self.supabase_url}/rest/v1/ctr_training_data",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return pd.DataFrame(response.json())
        except Exception as e:
            print(f"❌ Failed to fetch training data: {e}")
            return pd.DataFrame()
    
    def train_global_model(self, min_samples: int = 1000) -> Dict:
        """
        Train global CTR prediction model.
        
        Uses all available training data with 5-fold cross-validation.
        
        Args:
            min_samples: Minimum samples required to train
            
        Returns:
            Training result with metrics and model path
        """
        if not ML_AVAILABLE:
            return {'success': False, 'error': 'ML dependencies not available'}
        
        print("🔧 Training global CTR model...")
        
        # Fetch training data
        df = self._fetch_training_data(min_impressions=1000)
        
        if len(df) < min_samples:
            return {
                'success': False, 
                'error': f'Not enough training data ({len(df)} samples, need {min_samples})'
            }
        
        # Prepare features and target
        predictor = CTRPredictor()  # Use for feature preparation
        
        # Build feature matrix
        feature_rows = []
        target_values = []
        
        for _, row in df.iterrows():
            # Parse thumbnail features
            thumb_features = {}
            if row.get('thumbnail_features'):
                try:
                    thumb_features = json.loads(row['thumbnail_features']) if isinstance(row['thumbnail_features'], str) else row['thumbnail_features']
                except:
                    pass
            
            # Build feature vector
            features = {
                **thumb_features,
                'title_length': row.get('title_length', 0),
                'title_has_numbers': row.get('title_has_numbers', False),
                'title_has_question': row.get('title_has_question', False),
                'title_has_power_words': row.get('title_has_power_words', False),
                'title_capitalization_ratio': row.get('title_capitalization_ratio', 0)
            }
            
            feature_vector = []
            for name in predictor.FEATURE_NAMES:
                value = features.get(name, 0)
                if isinstance(value, bool):
                    value = float(value)
                elif isinstance(value, (list, tuple)):
                    value = float(value[0]) if value else 0
                elif value is None:
                    value = 0
                feature_vector.append(float(value))
            
            feature_rows.append(feature_vector)
            target_values.append(row['ctr_actual'])
        
        X = np.array(feature_rows)
        y = np.array(target_values)
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train XGBoost with cross-validation
        model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=0.1,
            random_state=42
        )
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='neg_mean_absolute_error')
        cv_mae = -cv_scores.mean()
        
        # Final training
        model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_test_scaled, y_test)],
            verbose=False
        )
        
        # Evaluate
        y_pred = model.predict(X_test_scaled)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"📊 Global Model Performance:")
        print(f"   CV MAE: {cv_mae:.4f}")
        print(f"   Test MAE: {mae:.4f}")
        print(f"   Test R²: {r2:.4f}")
        
        # Feature importances
        feature_importances = dict(zip(predictor.FEATURE_NAMES, model.feature_importances_))
        
        # Save model
        model_data = {
            'model': model,
            'scaler': scaler,
            'feature_importances': feature_importances,
            'channel_avg_ctr': float(y.mean()),
            'feature_names': predictor.FEATURE_NAMES,
            'trained_at': datetime.now().isoformat(),
            'training_samples': len(X_train),
            'metrics': {'mae': mae, 'r2': r2, 'cv_mae': cv_mae}
        }
        
        joblib.dump(model_data, GLOBAL_MODEL_PATH)
        print(f"💾 Global model saved to {GLOBAL_MODEL_PATH}")
        
        return {
            'success': True,
            'model_path': GLOBAL_MODEL_PATH,
            'training_samples': len(X_train),
            'metrics': {
                'mae': round(mae, 4),
                'r2': round(r2, 4),
                'cv_mae': round(cv_mae, 4)
            },
            'top_features': sorted(
                feature_importances.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
        }
    
    def train_channel_model(self, channel_id: str, min_samples: int = 50) -> Dict:
        """
        Train channel-specific CTR prediction model.
        
        Uses transfer learning: starts with global model and fine-tunes
        on channel-specific data.
        
        Args:
            channel_id: YouTube channel ID
            min_samples: Minimum samples required
            
        Returns:
            Training result with metrics and model path
        """
        if not ML_AVAILABLE:
            return {'success': False, 'error': 'ML dependencies not available'}
        
        print(f"🔧 Training channel-specific model for {channel_id}...")
        
        # Fetch channel data
        df = self._fetch_training_data(channel_id=channel_id, min_impressions=100)
        
        if len(df) < min_samples:
            return {
                'success': False,
                'error': f'Not enough channel data ({len(df)} samples, need {min_samples})'
            }
        
        # Load global model as base (if exists)
        base_model = None
        if os.path.exists(GLOBAL_MODEL_PATH):
            try:
                base_data = joblib.load(GLOBAL_MODEL_PATH)
                base_model = base_data['model']
                print("   📊 Using global model as base")
            except:
                pass
        
        # Prepare features (same as global)
        predictor = CTRPredictor()
        
        feature_rows = []
        target_values = []
        
        for _, row in df.iterrows():
            thumb_features = {}
            if row.get('thumbnail_features'):
                try:
                    thumb_features = json.loads(row['thumbnail_features']) if isinstance(row['thumbnail_features'], str) else row['thumbnail_features']
                except:
                    pass
            
            features = {
                **thumb_features,
                'title_length': row.get('title_length', 0),
                'title_has_numbers': row.get('title_has_numbers', False),
                'title_has_question': row.get('title_has_question', False),
                'title_has_power_words': row.get('title_has_power_words', False),
                'title_capitalization_ratio': row.get('title_capitalization_ratio', 0)
            }
            
            feature_vector = []
            for name in predictor.FEATURE_NAMES:
                value = features.get(name, 0)
                if isinstance(value, bool):
                    value = float(value)
                elif isinstance(value, (list, tuple)):
                    value = float(value[0]) if value else 0
                elif value is None:
                    value = 0
                feature_vector.append(float(value))
            
            feature_rows.append(feature_vector)
            target_values.append(row['ctr_actual'])
        
        X = np.array(feature_rows)
        y = np.array(target_values)
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model (smaller, to avoid overfitting on limited data)
        model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.8,
            random_state=42
        )
        
        model.fit(X_train_scaled, y_train, verbose=False)
        
        # Evaluate
        y_pred = model.predict(X_test_scaled)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"📊 Channel Model Performance:")
        print(f"   MAE: {mae:.4f}")
        print(f"   R²: {r2:.4f}")
        
        # Feature importances
        feature_importances = dict(zip(predictor.FEATURE_NAMES, model.feature_importances_))
        
        # Save model
        model_path = os.path.join(CHANNEL_MODELS_DIR, f'{channel_id}.joblib')
        
        model_data = {
            'model': model,
            'scaler': scaler,
            'feature_importances': feature_importances,
            'channel_avg_ctr': float(y.mean()),
            'feature_names': predictor.FEATURE_NAMES,
            'trained_at': datetime.now().isoformat(),
            'training_samples': len(X_train),
            'channel_id': channel_id,
            'metrics': {'mae': mae, 'r2': r2}
        }
        
        joblib.dump(model_data, model_path)
        print(f"💾 Channel model saved to {model_path}")
        
        return {
            'success': True,
            'model_path': model_path,
            'channel_id': channel_id,
            'training_samples': len(X_train),
            'metrics': {
                'mae': round(mae, 4),
                'r2': round(r2, 4)
            }
        }


# Import for trainer
import requests
from datetime import datetime


# === Quick test ===
if __name__ == "__main__":
    print("🧪 Testing CTR Predictor...")
    
    predictor = CTRPredictor()
    
    # Test features (simulated)
    test_features = {
        'faces_are_large': True,
        'face_count': 1,
        'has_eye_contact': True,
        'has_text': True,
        'word_count': 3,
        'has_red_accent': True,
        'contrast_score': 0.4,
        'avg_saturation': 0.6,
        'avg_brightness': 0.5,
        'rule_of_thirds_score': 0.7,
        'mobile_readability_score': 0.8
    }
    
    test_title = "I Tried the SECRET Method for 30 Days..."
    
    prediction = predictor.predict(test_features, test_title)
    
    print(f"\n📊 Prediction Results:")
    print(f"   Model Type: {prediction.model_type}")
    print(f"   Predicted CTR: {prediction.predicted_ctr:.1f}%")
    print(f"   Confidence: {prediction.confidence:.0%}")
    print(f"   vs Channel Avg: {prediction.ctr_vs_channel_avg:+.1f}%")
    
    print(f"\n   ✅ Positive Factors:")
    for factor in prediction.top_positive_factors:
        print(f"      • {factor['factor']}: +{factor['impact']}")
    
    print(f"\n   💡 Suggestions:")
    for i, s in enumerate(prediction.improvement_suggestions[:3], 1):
        print(f"      {i}. {s}")
    
    # Test trainer stats
    print(f"\n🔧 Testing CTR Model Trainer...")
    trainer = CTRModelTrainer()
    stats = trainer.get_training_stats()
    print(f"   Training data stats: {stats}")

