"""
Enhanced Model Evaluation with Thumbnail Features
=================================================

This script:
1. Downloads thumbnails from training data
2. Extracts visual features using ThumbnailFeatureExtractor
3. Applies RAG-based CTR scoring using research from thumbnail_rag_context.md
4. Evaluates ML models on views/performance prediction

Uses chronological train/test split (no look-ahead bias).
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
import warnings
import requests
from PIL import Image
from io import BytesIO
import time

warnings.filterwarnings('ignore')

# Add parent path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
premium_dir = os.path.dirname(current_dir)
railway_dir = os.path.dirname(premium_dir)
if railway_dir not in sys.path:
    sys.path.insert(0, railway_dir)

# ML imports
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
from scipy.stats import spearmanr

# Try to import thumbnail extractor
try:
    from premium.thumbnail_extractor import ThumbnailFeatureExtractor, ThumbnailFeatures
    EXTRACTOR_AVAILABLE = True
except ImportError:
    EXTRACTOR_AVAILABLE = False
    print("⚠️ ThumbnailFeatureExtractor not available")


# ============================================================
# RAG-BASED THUMBNAIL SCORING (from thumbnail_rag_context.md)
# ============================================================

@dataclass
class RAGThumbnailScore:
    """Thumbnail score based on RAG research data."""
    total_score: float  # Combined CTR potential score (0-100)
    
    # Component scores
    color_score: float
    face_score: float
    text_score: float
    composition_score: float
    
    # Individual factors
    factors: List[Dict]
    
    def to_dict(self) -> Dict:
        return {
            'total_score': round(self.total_score, 1),
            'color_score': round(self.color_score, 1),
            'face_score': round(self.face_score, 1),
            'text_score': round(self.text_score, 1),
            'composition_score': round(self.composition_score, 1),
            'factors': self.factors
        }


class RAGThumbnailScorer:
    """
    Scores thumbnails based on research metrics from thumbnail_rag_context.md.
    
    Research-backed CTR impacts used:
    - Red/Orange: +21% CTR
    - Yellow: +18% CTR  
    - Blue: +15% watch time
    - Face presence: +20-30% CTR
    - Large face: +38% CTR
    - Strong emotion: +45% CTR
    - Eye contact: additional boost
    - 0-3 words text: optimal
    - 7+ words: underperforms
    - High contrast: +20-40% CTR
    - Rule of thirds: improved composition
    """
    
    # Color CTR impacts from research (converted to score multipliers)
    COLOR_IMPACTS = {
        'red': 21,
        'orange': 21,
        'yellow': 18,
        'blue': 15,
        'green': 12,
        'neon': 15,
        'pink': 17,
        'cyan': 17,
    }
    
    def __init__(self, extractor: Optional['ThumbnailFeatureExtractor'] = None):
        self.extractor = extractor
    
    def score_from_features(self, features: 'ThumbnailFeatures') -> RAGThumbnailScore:
        """Score a thumbnail using extracted features and RAG research data."""
        factors = []
        
        # ================
        # 1. COLOR SCORE
        # ================
        color_score = 50  # Baseline
        
        # High contrast (+20-40% CTR in research)
        contrast = getattr(features, 'contrast_score', 0)
        if contrast > 0.3:
            color_score += 20
            factors.append({'type': 'color', 'factor': 'High contrast', 'impact': +20})
        elif contrast > 0.2:
            color_score += 10
            factors.append({'type': 'color', 'factor': 'Good contrast', 'impact': +10})
        
        # High saturation (vibrant colors)
        saturation = getattr(features, 'avg_saturation', 0)
        if saturation > 0.6:
            color_score += 15
            factors.append({'type': 'color', 'factor': 'Vibrant colors', 'impact': +15})
        elif saturation > 0.4:
            color_score += 8
        
        # Red/Orange accent (research: +21% CTR)
        if getattr(features, 'has_red_accent', False):
            color_score += 15
            factors.append({'type': 'color', 'factor': 'Red/orange accent', 'impact': +15})
        
        # Warm colors (research: higher CTR than cool)
        warm_ratio = getattr(features, 'warm_color_ratio', 0)
        if warm_ratio > 0.5:
            color_score += 8
            factors.append({'type': 'color', 'factor': 'Warm color palette', 'impact': +8})
        
        color_score = min(100, max(0, color_score))
        
        # ================
        # 2. FACE SCORE
        # ================
        face_score = 30  # Baseline (no face is a disadvantage)
        
        face_count = getattr(features, 'face_count', 0)
        
        if face_count > 0:
            # Face presence: +20-30% CTR
            face_score = 60
            factors.append({'type': 'face', 'factor': 'Face present', 'impact': +30})
            
            # Large face: +38% CTR
            if getattr(features, 'faces_are_large', False):
                face_score += 25
                factors.append({'type': 'face', 'factor': 'Large face (>15% area)', 'impact': +25})
            
            # Face in center: better composition
            if getattr(features, 'face_in_center', False):
                face_score += 10
                factors.append({'type': 'face', 'factor': 'Face well-positioned', 'impact': +10})
            
            # Eye contact (if detectable)
            if getattr(features, 'has_eye_contact', False):
                face_score += 10
                factors.append({'type': 'face', 'factor': 'Eye contact', 'impact': +10})
        else:
            factors.append({'type': 'face', 'factor': 'No face detected', 'impact': -20})
        
        face_score = min(100, max(0, face_score))
        
        # ================
        # 3. TEXT SCORE
        # ================
        text_score = 50  # Baseline
        
        has_text = getattr(features, 'has_text', False)
        word_count = getattr(features, 'word_count', 0)
        
        if has_text:
            # Research: 0-3 words optimal, 7+ underperforms
            if word_count <= 3:
                text_score = 85
                factors.append({'type': 'text', 'factor': f'{word_count} words (optimal)', 'impact': +35})
            elif word_count <= 6:
                text_score = 70
                factors.append({'type': 'text', 'factor': f'{word_count} words (acceptable)', 'impact': +20})
            else:
                text_score = 40
                factors.append({'type': 'text', 'factor': f'{word_count} words (too many)', 'impact': -10})
            
            # Uses numbers (research: numbers attract attention)
            if getattr(features, 'uses_numbers', False):
                text_score += 10
                factors.append({'type': 'text', 'factor': 'Contains numbers', 'impact': +10})
            
            # All caps (attention-grabbing but use sparingly)
            if getattr(features, 'uses_all_caps', False):
                text_score += 5
        else:
            # No text is not necessarily bad for some content
            text_score = 50
        
        text_score = min(100, max(0, text_score))
        
        # ================
        # 4. COMPOSITION SCORE
        # ================
        composition_score = 50  # Baseline
        
        # Rule of thirds compliance
        thirds_score = getattr(features, 'rule_of_thirds_score', 0)
        if thirds_score > 0.6:
            composition_score += 20
            factors.append({'type': 'composition', 'factor': 'Good rule of thirds', 'impact': +20})
        elif thirds_score > 0.3:
            composition_score += 10
        
        # Center focus (clear focal point)
        center_focus = getattr(features, 'center_focus_score', 0)
        if center_focus > 0.5:
            composition_score += 15
            factors.append({'type': 'composition', 'factor': 'Clear focal point', 'impact': +15})
        
        # Visual complexity (research: max 3 elements)
        complexity = getattr(features, 'visual_complexity', 0)
        if complexity < 0.3:
            composition_score += 15
            factors.append({'type': 'composition', 'factor': 'Clean, simple design', 'impact': +15})
        elif complexity > 0.7:
            composition_score -= 15
            factors.append({'type': 'composition', 'factor': 'Overcrowded (-23% CTR)', 'impact': -15})
        
        # Mobile readability
        mobile_score = getattr(features, 'mobile_readability_score', 0)
        if mobile_score > 0.7:
            composition_score += 10
        elif mobile_score < 0.3:
            composition_score -= 10
            factors.append({'type': 'composition', 'factor': 'Poor mobile readability', 'impact': -10})
        
        composition_score = min(100, max(0, composition_score))
        
        # ================
        # TOTAL SCORE
        # ================
        # Weighted average based on research importance:
        # - Face: 35% (biggest CTR driver)
        # - Color: 25% (contrast and attention)
        # - Composition: 25% (clarity and professionalism)
        # - Text: 15% (secondary to visuals)
        
        total_score = (
            face_score * 0.35 +
            color_score * 0.25 +
            composition_score * 0.25 +
            text_score * 0.15
        )
        
        return RAGThumbnailScore(
            total_score=total_score,
            color_score=color_score,
            face_score=face_score,
            text_score=text_score,
            composition_score=composition_score,
            factors=factors
        )
    
    def score_from_url(self, url: str) -> Optional[RAGThumbnailScore]:
        """Download thumbnail and score it."""
        if not self.extractor:
            return None
        
        try:
            features = self.extractor.extract_from_url(url)
            return self.score_from_features(features)
        except Exception as e:
            print(f"Error scoring thumbnail: {e}")
            return None


# ============================================================
# DATA LOADING AND PREPROCESSING
# ============================================================

def load_training_data() -> pd.DataFrame:
    """Load all JSON training data."""
    # Find training data directory
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
            filepath = os.path.join(data_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    all_data.extend(data)
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    
    df = pd.DataFrame(all_data)
    print(f"✓ Loaded {len(df)} samples")
    return df


def extract_thumbnail_features_batch(df: pd.DataFrame, 
                                     sample_size: int = 200,
                                     cache_file: str = 'thumbnail_features_cache.json') -> pd.DataFrame:
    """
    Extract thumbnail features for a sample of videos.
    Uses caching to avoid re-downloading.
    """
    cache_path = os.path.join(current_dir, cache_file)
    
    # Load cache if exists
    cached_features = {}
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            cached_features = json.load(f)
        print(f"✓ Loaded {len(cached_features)} cached thumbnail features")
    
    # Filter to videos with thumbnails
    df = df[df['thumbnail_url'].notna()].copy()
    
    # Sample if needed
    if len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=42)
    
    if not EXTRACTOR_AVAILABLE:
        print("⚠️ Thumbnail extractor not available, using cached data only")
        # Add cached features to dataframe
        for idx, row in df.iterrows():
            vid_id = row['video_id']
            if vid_id in cached_features:
                for key, val in cached_features[vid_id].items():
                    df.loc[idx, f'thumb_{key}'] = val
        return df
    
    # Initialize extractor (without face detection to avoid crashes)
    print("🔧 Initializing thumbnail extractor (OCR and color analysis only)...")
    extractor = ThumbnailFeatureExtractor(use_ocr=False, use_face_detection=False)
    scorer = RAGThumbnailScorer(extractor)
    
    # Extract features for uncached videos
    new_features = {}
    processed = 0
    errors = 0
    
    for idx, row in df.iterrows():
        vid_id = row['video_id']
        
        # Use cache if available
        if vid_id in cached_features:
            for key, val in cached_features[vid_id].items():
                df.loc[idx, f'thumb_{key}'] = val
            continue
        
        # Extract new features
        try:
            url = row['thumbnail_url']
            features = extractor.extract_from_url(url)
            rag_score = scorer.score_from_features(features)
            
            # Store key features
            feature_dict = {
                'contrast_score': features.contrast_score,
                'avg_saturation': features.avg_saturation,
                'avg_brightness': features.avg_brightness,
                'has_text': features.has_text,
                'word_count': features.word_count,
                'face_count': features.face_count,
                'visual_complexity': features.visual_complexity,
                'rule_of_thirds_score': features.rule_of_thirds_score,
                'center_focus_score': features.center_focus_score,
                'rag_total_score': rag_score.total_score,
                'rag_color_score': rag_score.color_score,
                'rag_face_score': rag_score.face_score,
                'rag_text_score': rag_score.text_score,
                'rag_composition_score': rag_score.composition_score,
            }
            
            # Add to dataframe
            for key, val in feature_dict.items():
                df.loc[idx, f'thumb_{key}'] = val
            
            # Cache
            new_features[vid_id] = feature_dict
            processed += 1
            
            if processed % 20 == 0:
                print(f"  Processed {processed} thumbnails...")
            
            # Rate limit
            time.sleep(0.1)
            
        except Exception as e:
            errors += 1
            if errors < 5:
                print(f"  Error extracting {vid_id}: {e}")
    
    # Save updated cache
    cached_features.update(new_features)
    with open(cache_path, 'w') as f:
        json.dump(cached_features, f)
    
    print(f"✓ Extracted features for {processed} new thumbnails ({errors} errors)")
    
    return df


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Apply feature engineering."""
    df = df.copy()
    
    # Parse datetime
    df['published_at'] = pd.to_datetime(df['published_at'], utc=True)
    
    # Clean numeric fields
    df['view_count'] = pd.to_numeric(df['view_count'], errors='coerce').fillna(0)
    df['like_count'] = pd.to_numeric(df['like_count'], errors='coerce').fillna(0)
    df['comment_count'] = pd.to_numeric(df['comment_count'], errors='coerce').fillna(0)
    
    # Duration parsing
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
    
    # Power words
    POWER_WORDS = [
        'secret', 'revealed', 'shocking', 'insane', 'ultimate',
        'best', 'worst', 'top', 'how to', 'why', 'tutorial',
        'tips', 'tricks', 'guide', 'review', 'vs'
    ]
    df['title_has_power_words'] = df['title'].apply(
        lambda x: 1 if any(pw in x.lower() for pw in POWER_WORDS) else 0
    )
    
    # Remove zero views
    df = df[df['view_count'] > 100].copy()
    
    return df


def calculate_channel_median_temporal(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate channel median using only historical data (no look-ahead)."""
    df = df.copy().sort_values('published_at')
    
    df['channel_median_views'] = df.groupby('channel_id')['view_count'].transform(
        lambda x: x.expanding(min_periods=1).median().shift(1).fillna(x.iloc[0])
    )
    
    df['performance_ratio'] = df['view_count'] / df['channel_median_views'].clip(lower=1)
    
    return df


def temporal_train_test_split(df: pd.DataFrame, test_ratio: float = 0.2):
    """Split chronologically."""
    df = df.sort_values('published_at')
    split_idx = int(len(df) * (1 - test_ratio))
    return df.iloc[:split_idx].copy(), df.iloc[split_idx:].copy()


# ============================================================
# EVALUATION WITH THUMBNAIL FEATURES
# ============================================================

def evaluate_with_thumbnails(df: pd.DataFrame) -> Dict:
    """
    Evaluate view prediction using title + metadata + thumbnail features.
    """
    # Check for thumbnail features
    thumb_cols = [c for c in df.columns if c.startswith('thumb_')]
    
    if not thumb_cols:
        return {'error': 'No thumbnail features available'}
    
    # Filter to rows with thumbnail data
    df = df.dropna(subset=['thumb_rag_total_score']).copy()
    
    if len(df) < 50:
        return {'error': f'Insufficient data with thumbnail features: {len(df)} samples'}
    
    print(f"📊 Evaluating with {len(df)} videos that have thumbnail features")
    
    # Calculate channel median
    df = calculate_channel_median_temporal(df)
    
    # Temporal split
    train_df, test_df = temporal_train_test_split(df, test_ratio=0.2)
    
    print(f"   Train: {len(train_df)} | Test: {len(test_df)}")
    
    # ================
    # BASELINE: Title + Metadata Only
    # ================
    base_features = ['duration_seconds', 'title_length', 'title_has_question', 
                     'title_has_number', 'tags_count', 'title_has_power_words']
    
    # Add channel baseline (proxy for subscriber count)
    train_df['subscriber_count_log'] = np.log1p(train_df['channel_median_views'])
    test_df['subscriber_count_log'] = np.log1p(test_df['channel_median_views'])
    base_features.append('subscriber_count_log')
    
    X_train_base = train_df[base_features].fillna(0)
    X_test_base = test_df[base_features].fillna(0)
    
    y_train = np.log1p(train_df['view_count'])
    y_test = np.log1p(test_df['view_count'])
    
    # Scale and train baseline
    scaler_base = StandardScaler()
    X_train_base_scaled = scaler_base.fit_transform(X_train_base)
    X_test_base_scaled = scaler_base.transform(X_test_base)
    
    model_base = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
    model_base.fit(X_train_base_scaled, y_train)
    
    y_pred_base = model_base.predict(X_test_base_scaled)
    
    r2_base = r2_score(y_test, y_pred_base)
    mae_base = mean_absolute_error(y_test, y_pred_base)
    corr_base, _ = spearmanr(np.expm1(y_test), np.expm1(y_pred_base))
    
    # Within 2x accuracy
    y_actual = np.expm1(y_test)
    y_pred_actual_base = np.expm1(y_pred_base)
    ratio_base = y_pred_actual_base / y_actual.clip(lower=1)
    within_2x_base = ((ratio_base >= 0.5) & (ratio_base <= 2.0)).mean() * 100
    
    # ================
    # WITH THUMBNAIL: Title + Metadata + RAG Thumbnail Score
    # ================
    thumb_rag_features = ['thumb_rag_total_score', 'thumb_rag_color_score', 
                          'thumb_rag_face_score', 'thumb_rag_text_score',
                          'thumb_rag_composition_score']
    
    # Also include raw thumbnail features
    thumb_raw_features = ['thumb_contrast_score', 'thumb_avg_saturation', 
                          'thumb_avg_brightness', 'thumb_visual_complexity']
    
    all_thumb_features = [f for f in thumb_rag_features + thumb_raw_features if f in df.columns]
    
    enhanced_features = base_features + all_thumb_features
    
    X_train_enhanced = train_df[enhanced_features].fillna(0)
    X_test_enhanced = test_df[enhanced_features].fillna(0)
    
    # Scale and train enhanced
    scaler_enhanced = StandardScaler()
    X_train_enhanced_scaled = scaler_enhanced.fit_transform(X_train_enhanced)
    X_test_enhanced_scaled = scaler_enhanced.transform(X_test_enhanced)
    
    model_enhanced = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
    model_enhanced.fit(X_train_enhanced_scaled, y_train)
    
    y_pred_enhanced = model_enhanced.predict(X_test_enhanced_scaled)
    
    r2_enhanced = r2_score(y_test, y_pred_enhanced)
    mae_enhanced = mean_absolute_error(y_test, y_pred_enhanced)
    corr_enhanced, _ = spearmanr(np.expm1(y_test), np.expm1(y_pred_enhanced))
    
    y_pred_actual_enhanced = np.expm1(y_pred_enhanced)
    ratio_enhanced = y_pred_actual_enhanced / y_actual.clip(lower=1)
    within_2x_enhanced = ((ratio_enhanced >= 0.5) & (ratio_enhanced <= 2.0)).mean() * 100
    
    # Feature importances
    feature_imp = dict(zip(enhanced_features, model_enhanced.feature_importances_))
    top_features = sorted(feature_imp.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        'sample_size': len(df),
        'train_size': len(train_df),
        'test_size': len(test_df),
        'baseline': {
            'features': 'Title + Metadata only',
            'R2': round(r2_base, 4),
            'MAE_log': round(mae_base, 4),
            'Error_Factor': round(np.exp(mae_base), 2),
            'Within_2x_%': round(within_2x_base, 1),
            'Spearman_Corr': round(corr_base, 4),
        },
        'with_thumbnail': {
            'features': 'Title + Metadata + RAG Thumbnail Scores',
            'R2': round(r2_enhanced, 4),
            'MAE_log': round(mae_enhanced, 4),
            'Error_Factor': round(np.exp(mae_enhanced), 2),
            'Within_2x_%': round(within_2x_enhanced, 1),
            'Spearman_Corr': round(corr_enhanced, 4),
        },
        'improvement': {
            'R2_change': round(r2_enhanced - r2_base, 4),
            'MAE_change': round(mae_base - mae_enhanced, 4),
            'Within_2x_change': round(within_2x_enhanced - within_2x_base, 1),
        },
        'top_features': top_features
    }


def run_full_evaluation_with_thumbnails():
    """Run complete evaluation including thumbnail features."""
    print("=" * 70)
    print("   ML MODEL EVALUATION WITH THUMBNAIL FEATURES")
    print("   Using RAG Research Data (thumbnail_rag_context.md)")
    print("=" * 70)
    print()
    
    # Load data
    df = load_training_data()
    df = preprocess_data(df)
    
    print(f"\n📊 Dataset: {len(df)} videos")
    
    # Extract thumbnail features (uses cache)
    print("\n🖼️  Extracting thumbnail features...")
    df = extract_thumbnail_features_batch(df, sample_size=300)
    
    # Run evaluation
    print("\n📈 Running evaluation...")
    results = evaluate_with_thumbnails(df)
    
    if 'error' in results:
        print(f"\n❌ Error: {results['error']}")
        return results
    
    # Print results
    print("\n" + "=" * 70)
    print("RESULTS: Baseline vs. Thumbnail-Enhanced Model")
    print("=" * 70)
    
    print("\n📊 BASELINE (Title + Metadata):")
    for key, val in results['baseline'].items():
        print(f"   {key}: {val}")
    
    print("\n📊 WITH THUMBNAIL FEATURES (RAG-scored):")
    for key, val in results['with_thumbnail'].items():
        print(f"   {key}: {val}")
    
    print("\n📈 IMPROVEMENT:")
    for key, val in results['improvement'].items():
        sign = '+' if val > 0 else ''
        print(f"   {key}: {sign}{val}")
    
    print("\n🔬 TOP PREDICTIVE FEATURES:")
    for feat, imp in results['top_features']:
        print(f"   {feat}: {imp:.3f}")
    
    print("\n" + "=" * 70)
    print("INTERPRETATION")
    print("=" * 70)
    
    r2_base = results['baseline']['R2']
    r2_enhanced = results['with_thumbnail']['R2']
    within_base = results['baseline']['Within_2x_%']
    within_enhanced = results['with_thumbnail']['Within_2x_%']
    
    print(f"""
📊 Adding thumbnail analysis {"IMPROVES" if r2_enhanced > r2_base else "does not improve"} predictions:

   • R² improved from {r2_base:.2f} to {r2_enhanced:.2f}
   • Within-2x accuracy: {within_base:.0f}% → {within_enhanced:.0f}%
   
🔑 The top predictive features show which elements matter most.

⚠️  Note: This evaluation uses color/composition analysis only (no face detection
   to avoid crashes). Full face detection would likely show even more improvement
   since faces are the #1 CTR driver per research (+20-45% CTR).
""")
    
    return results


if __name__ == "__main__":
    results = run_full_evaluation_with_thumbnails()
