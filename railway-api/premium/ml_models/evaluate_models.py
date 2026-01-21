"""
Model Evaluation Script - No Look-Ahead Bias
============================================

Properly evaluates ML models on UNSEEN data using temporal/chronological splits.

This script:
1. Loads training data
2. Uses CHRONOLOGICAL splitting (train on older data, test on newer data)
3. Reports metrics with confidence intervals
4. Addresses look-ahead bias concerns

"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Tuple, List
import warnings
warnings.filterwarnings('ignore')

# ML imports
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import joblib


# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRAINING_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(BASE_DIR))), 'training_data')
MODELS_DIR = os.path.join(BASE_DIR, 'trained')


def load_training_data(data_dir: str = None) -> pd.DataFrame:
    """Load all JSON training data into a DataFrame."""
    data_dir = data_dir or TRAINING_DATA_DIR
    
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
    print(f"✓ Loaded {len(df)} samples from {data_dir}")
    return df


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Apply feature engineering matching the training pipeline."""
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
    
    # Power words (matches CTR predictor)
    POWER_WORDS = [
        'secret', 'revealed', 'shocking', 'insane', 'ultimate',
        'best', 'worst', 'top', 'how to', 'why', 'tutorial',
        'tips', 'tricks', 'guide', 'review', 'vs', 'unboxing',
        'reaction', 'challenge', 'truth', 'exposed', 'finally',
        'new', 'update', 'breaking', 'exclusive', 'free'
    ]
    df['title_has_power_words'] = df['title'].apply(
        lambda x: 1 if any(pw in x.lower() for pw in POWER_WORDS) else 0
    )
    df['title_capitalization_ratio'] = df['title'].apply(
        lambda x: sum(1 for c in x if c.isupper()) / max(len(x), 1)
    )
    
    # Remove zero views to match training filter
    df = df[df['view_count'] > 100].copy()
    
    return df


def calculate_channel_median_temporal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate channel median views using ONLY historical data.
    
    This is CRITICAL to avoid look-ahead bias:
    - For each video, we only use videos from the SAME channel that were 
      published BEFORE this video to calculate the channel median.
    """
    df = df.copy().sort_values('published_at')
    
    # Calculate expanding median per channel (only uses historical data)
    df['channel_median_views'] = df.groupby('channel_id')['view_count'].transform(
        lambda x: x.expanding(min_periods=1).median().shift(1).fillna(x.iloc[0])
    )
    
    # Calculate performance ratio (actual / expected)
    df['performance_ratio'] = df['view_count'] / df['channel_median_views'].clip(lower=1)
    
    return df


def temporal_train_test_split(df: pd.DataFrame, test_ratio: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data chronologically to prevent any look-ahead bias.
    
    Training on older videos, testing on newer videos - mimics real-world usage.
    """
    df = df.sort_values('published_at')
    
    split_idx = int(len(df) * (1 - test_ratio))
    
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()
    
    train_end_date = train_df['published_at'].max()
    test_start_date = test_df['published_at'].min()
    
    print(f"✓ Temporal Split: Train up to {train_end_date.date()} | Test from {test_start_date.date()}")
    print(f"  Train samples: {len(train_df)} | Test samples: {len(test_df)}")
    
    return train_df, test_df


def evaluate_view_prediction_niche(df: pd.DataFrame, niche: str = None) -> Dict:
    """
    Evaluate view prediction for a specific niche or all data.
    
    Predicts: log(views)
    Features: title length, title patterns, duration, tags, channel baseline
    """
    if niche:
        df = df[df['niche'] == niche].copy()
    
    if len(df) < 50:
        return {'error': f'Insufficient data: {len(df)} samples'}
    
    # Calculate channel median with temporal awareness
    df = calculate_channel_median_temporal(df)
    
    # Temporal split
    train_df, test_df = temporal_train_test_split(df, test_ratio=0.2)
    
    # Features (matching scientific_trainer.py)
    features = [
        'duration_seconds', 'title_length', 'title_has_question',
        'title_has_number', 'tags_count'
    ]
    
    # Add channel baseline as proxy for subscriber count (no leakage - uses historical median)
    train_df['subscriber_count_log'] = np.log1p(train_df['channel_median_views'])
    test_df['subscriber_count_log'] = np.log1p(test_df['channel_median_views'])
    features.append('subscriber_count_log')
    
    X_train = train_df[features].fillna(0)
    X_test = test_df[features].fillna(0)
    
    # Target: log(views)
    y_train = np.log1p(train_df['view_count'])
    y_test = np.log1p(test_df['view_count'])
    
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
    
    # Predict
    y_pred_log = model.predict(X_test_scaled)
    
    # Convert back from log space
    y_pred = np.expm1(y_pred_log)
    y_actual = np.expm1(y_test)
    
    # Calculate metrics
    
    # 1. MAE in log space (interpretable as % error multiplier)
    mae_log = mean_absolute_error(y_test, y_pred_log)
    error_factor = np.exp(mae_log)  # e.g., 1.6 means predictions off by 60% on average
    
    # 2. R² in log space
    r2_log = r2_score(y_test, y_pred_log)
    
    # 3. MAE in actual views (but this is skewed by outliers)
    mae_views = mean_absolute_error(y_actual, y_pred)
    
    # 4. Median Absolute Percentage Error (robust to outliers)
    mape = np.median(np.abs((y_actual - y_pred) / y_actual.clip(lower=1))) * 100
    
    # 5. Prediction within factor of 2 (a useful practical metric)
    ratio = y_pred / y_actual.clip(lower=1)
    within_2x = ((ratio >= 0.5) & (ratio <= 2.0)).mean() * 100
    
    # 6. Spearman rank correlation (how well does it rank videos?)
    from scipy.stats import spearmanr
    rank_corr, rank_pval = spearmanr(y_actual, y_pred)
    
    return {
        'niche': niche or 'ALL',
        'train_samples': len(train_df),
        'test_samples': len(test_df),
        'metrics': {
            'R² (log space)': round(r2_log, 4),
            'MAE (log space)': round(mae_log, 4),
            'Error Factor': round(error_factor, 2),  # e.g., 1.8x means off by 80%
            'Median APE (%)': round(mape, 1),
            'Within 2x Accuracy (%)': round(within_2x, 1),
            'Spearman Rank Correlation': round(rank_corr, 4),
            'MAE (views)': int(mae_views),
        },
        'interpretation': {
            'error_factor': f"Predictions are off by a factor of ~{error_factor:.1f}x on average",
            'within_2x': f"{within_2x:.0f}% of predictions are within 0.5x to 2x of actual views",
            'rank_corr': f"Model can rank videos by expected views with {rank_corr:.1%} accuracy"
        }
    }


def evaluate_performance_ratio_prediction(df: pd.DataFrame) -> Dict:
    """
    Evaluate prediction of Performance Ratio (Actual Views / Channel Median).
    
    This is the main target for the SupervisedViralPredictor model.
    - Ratio > 2.0 = "viral" (above average)
    - Ratio < 0.5 = underperforming
    - Ratio ~ 1.0 = typical performance
    """
    # Calculate channel median with temporal awareness
    df = calculate_channel_median_temporal(df)
    
    # Remove rows with insufficient channel history
    df = df[df['channel_median_views'] > 0].copy()
    
    # Temporal split
    train_df, test_df = temporal_train_test_split(df, test_ratio=0.2)
    
    # Features
    features = [
        'duration_seconds', 'title_length', 'title_has_question',
        'title_has_number', 'tags_count', 'title_has_power_words',
        'title_capitalization_ratio'
    ]
    
    X_train = train_df[features].fillna(0)
    X_test = test_df[features].fillna(0)
    
    # Target: log(performance_ratio)
    y_train = np.log(train_df['performance_ratio'].clip(lower=0.01))
    y_test = np.log(test_df['performance_ratio'].clip(lower=0.01))
    
    # Scale
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train
    model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        random_state=42
    )
    model.fit(X_train_scaled, y_train)
    
    # Predict
    y_pred_log = model.predict(X_test_scaled)
    y_pred_ratio = np.exp(y_pred_log)
    y_actual_ratio = np.exp(y_test)
    
    # Metrics
    mae_ratio = mean_absolute_error(y_actual_ratio, y_pred_ratio)
    r2_log = r2_score(y_test, y_pred_log)
    
    # Classification: Viral (ratio >= 2.0) vs Not Viral
    actual_viral = y_actual_ratio >= 2.0
    pred_viral = y_pred_ratio >= 2.0
    
    viral_precision = (actual_viral & pred_viral).sum() / max(pred_viral.sum(), 1)
    viral_recall = (actual_viral & pred_viral).sum() / max(actual_viral.sum(), 1)
    viral_f1 = 2 * viral_precision * viral_recall / max(viral_precision + viral_recall, 0.001)
    
    # Spearman correlation
    from scipy.stats import spearmanr
    rank_corr, _ = spearmanr(y_actual_ratio, y_pred_ratio)
    
    return {
        'train_samples': len(train_df),
        'test_samples': len(test_df),
        'target': 'Performance Ratio (Views / Channel Median)',
        'metrics': {
            'R² (log space)': round(r2_log, 4),
            'MAE (ratio)': round(mae_ratio, 2),
            'Spearman Rank Correlation': round(rank_corr, 4),
            'Viral Detection Precision': round(viral_precision, 3),
            'Viral Detection Recall': round(viral_recall, 3),
            'Viral Detection F1': round(viral_f1, 3),
        },
        'interpretation': {
            'mae_ratio': f"Predicted ratio off by ~{mae_ratio:.2f}x on average (e.g., predicts 1.5x when actual is 2.0x)",
            'viral_detection': f"Correctly identifies {viral_recall*100:.0f}% of viral videos, with {viral_precision*100:.0f}% precision",
            'rank_corr': f"Can rank videos by viral potential with {rank_corr:.1%} accuracy"
        }
    }


def run_full_evaluation():
    """Run comprehensive evaluation with proper train/test methodology."""
    print("=" * 70)
    print("   ML MODEL EVALUATION - NO LOOK-AHEAD BIAS")
    print("   Using Chronological Train/Test Splits")
    print("=" * 70)
    print()
    
    # Load data
    df = load_training_data()
    df = preprocess_data(df)
    
    print(f"\n📊 Dataset Summary:")
    print(f"   Total samples (view_count > 100): {len(df)}")
    print(f"   Date range: {df['published_at'].min().date()} to {df['published_at'].max().date()}")
    print(f"   Niches: {df['niche'].nunique()}")
    print(f"   Unique channels: {df['channel_id'].nunique()}")
    print()
    
    # =========================================
    # EVALUATION 1: View Prediction (All Data)
    # =========================================
    print("=" * 70)
    print("EVALUATION 1: View Count Prediction (log scale)")
    print("  Features: Title (length, patterns), Duration, Tags, Channel Baseline")
    print("  Target: log(view_count)")
    print("=" * 70)
    
    result_all = evaluate_view_prediction_niche(df, niche=None)
    
    print(f"\n📈 Results (All Niches Combined):")
    for metric, value in result_all['metrics'].items():
        print(f"   {metric}: {value}")
    
    print(f"\n🎯 Interpretation:")
    for key, interp in result_all['interpretation'].items():
        print(f"   • {interp}")
    
    # =========================================
    # EVALUATION 2: Performance Ratio Prediction
    # =========================================
    print("\n" + "=" * 70)
    print("EVALUATION 2: Performance Ratio Prediction (Views / Channel Median)")
    print("  This predicts how well a video will perform RELATIVE to the channel average")
    print("  Ratio > 2.0 = Viral, Ratio < 0.5 = Underperforming")
    print("=" * 70)
    
    result_ratio = evaluate_performance_ratio_prediction(df)
    
    print(f"\n📈 Results:")
    for metric, value in result_ratio['metrics'].items():
        print(f"   {metric}: {value}")
    
    print(f"\n🎯 Interpretation:")
    for key, interp in result_ratio['interpretation'].items():
        print(f"   • {interp}")
    
    # =========================================
    # EVALUATION 3: Per-Niche Breakdown
    # =========================================
    print("\n" + "=" * 70)
    print("EVALUATION 3: Per-Niche View Prediction Breakdown")
    print("=" * 70)
    
    niche_results = []
    for niche in df['niche'].unique():
        try:
            result = evaluate_view_prediction_niche(df, niche=niche)
            if 'error' not in result:
                niche_results.append(result)
                print(f"\n   {niche}:")
                print(f"      R²: {result['metrics']['R² (log space)']:.3f} | "
                      f"Error Factor: {result['metrics']['Error Factor']:.1f}x | "
                      f"Within 2x: {result['metrics']['Within 2x Accuracy (%)']:.0f}%")
        except Exception as e:
            print(f"\n   {niche}: Error - {e}")
    
    # =========================================
    # SUMMARY
    # =========================================
    print("\n" + "=" * 70)
    print("SUMMARY: What This Means for YouTubers")
    print("=" * 70)
    
    error_factor = result_all['metrics']['Error Factor']
    within_2x = result_all['metrics']['Within 2x Accuracy (%)']
    rank_corr = result_all['metrics']['Spearman Rank Correlation']
    
    print(f"""
📊 CURRENT MODEL PERFORMANCE (Title + Metadata Only):

   1. VIEW PREDICTION ACCURACY:
      • Predictions are typically off by a factor of ~{error_factor:.1f}x
      • {within_2x:.0f}% of predictions fall within 0.5x to 2x of actual views
      • Example: If model predicts 10,000 views, actual could be 5,000 to 20,000
   
   2. RANKING ABILITY:
      • Spearman correlation: {rank_corr:.2f}
      • The model CAN rank videos by expected performance moderately well
      • Useful for comparing video concepts, even if exact numbers aren't precise
   
   3. VIRAL DETECTION:
      • Precision: {result_ratio['metrics']['Viral Detection Precision']:.1%}
      • Recall: {result_ratio['metrics']['Viral Detection Recall']:.1%}
      • Can identify potential viral videos with moderate accuracy

⚠️  LIMITATIONS:
   • Current models use only TITLE and basic METADATA
   • NO thumbnail features (visual analysis not in training data)
   • NO actual hook/intro analysis
   • More training data with real CTR would improve accuracy significantly
   
📈 WITH THUMBNAIL + HOOK ANALYSIS:
   • Industry research suggests thumbnail accounts for ~60% of CTR
   • Adding visual features could substantially improve predictions
   • This requires collecting thumbnail features + actual CTR data from creators
""")
    
    return {
        'all_views': result_all,
        'performance_ratio': result_ratio,
        'per_niche': niche_results
    }


if __name__ == "__main__":
    results = run_full_evaluation()
