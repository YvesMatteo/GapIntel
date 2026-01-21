
import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import xgboost as xgb
from sklearn.preprocessing import StandardScaler

DATA_DIR = "training_data"

def run_validation():
    all_data = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(DATA_DIR, filename), 'r') as f:
                data = json.load(f)
                all_data.extend(data)
    
    df = pd.DataFrame(all_data)
    # Filter valid data
    df = df[df['view_count'] > 0].copy()
    df['view_count'] = pd.to_numeric(df['view_count'])
    
    # Feature Engineering (Metadata only for this run to use all 1678 samples)
    df['title_length'] = df['title'].str.len()
    df['title_has_question'] = df['title'].str.contains('\?').astype(int)
    df['tags_count'] = df['tags'].apply(lambda x: len(x) if isinstance(x, list) else 0)
    
    # Target: Log Views (crucial for power-law distributions)
    y = np.log1p(df['view_count'])
    
    # baseline
    channel_medians = df.groupby('channel_id')['view_count'].transform('median')
    
    def evaluate_features(feature_set, name):
        X = feature_set.fillna(0)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.1)
        model.fit(X_train, y_train)
        preds_log = model.predict(X_test)
        
        r2 = r2_score(y_test, preds_log)
        mae_log = mean_absolute_error(y_test, preds_log)
        std_dev_error = np.std(y_test - preds_log)
        avg_error_factor = np.exp(mae_log)

        print(f"\n📊 {name} VALIDATION")
        print(f"R² Score: {r2:.3f}")
        print(f"Log MAE: {mae_log:.3f}")
        print(f"Std Dev Error: {std_dev_error:.3f}")
        print(f"Avg Accuracy Factor: {avg_error_factor:.2f}x")

    # TEST 1: Absolute Views (Full Model)
    evaluate_features(pd.DataFrame({
        'baseline_log': np.log1p(channel_medians),
        'title_len': df['title_length'],
        'has_q': df['title_has_question'],
        'tags': df['tags_count']
    }), "FULL MODEL (Baseline + Metadata)")

    # TEST 2: Pure Metadata (Title/Tags ONLY - Blind to channel size)
    # This shows the "Impossible Case" the user asked for.
    evaluate_features(pd.DataFrame({
        'title_len': df['title_length'],
        'has_q': df['title_has_question'],
        'tags': df['tags_count']
    }), "PURE METADATA (Blind to Channel Size)")

    # TEST 3: Viral Prediction (Predicting Deviation from norm)
    # Target is Residual = Actual - Baseline
    y_residual = y - np.log1p(channel_medians)
    X_metadata = pd.DataFrame({
        'title_len': df['title_length'],
        'has_q': df['title_has_question'],
        'tags': df['tags_count']
    }).fillna(0)
    
    X_train, X_test, y_train, y_test = train_test_split(X_metadata, y_residual, test_size=0.2, random_state=42)
    model = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.1)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    r2_v = r2_score(y_test, preds)
    
    print(f"\n📈 VIRAL PREDICTION (How well metadata explains over/under performance)")
    print(f"R² Score on Residuals: {r2_v:.3f}")
    print(f"Interpretation: Title/Metadata explains {r2_v*100:.1f}% of the 'Viral Variance' on top of your subscriber base.")

if __name__ == "__main__":
    run_validation()
