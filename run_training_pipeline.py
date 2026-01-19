
import os
import sys
import pandas as pd
from dotenv import load_dotenv

# Add railway-api directory to path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
railway_api_path = os.path.join(current_dir, 'railway-api')
sys.path.append(railway_api_path)

from premium.ml_models.training_pipeline import ModelTrainingPipeline

def run_training():
    print("🚀 Starting Manual Training Run...")
    
    # Load environment variables
    load_dotenv()
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found in environment.")
        return

    pipeline = ModelTrainingPipeline()
    
    print("📥 Fetching training data from Supabase...")
    # 1. Fetch performance data usually implies fetching from video_performance or similar
    # The pipeline has a helper for this
    video_data = pipeline.load_training_data_from_supabase(supabase_url, supabase_key)
    
    # 2. Fetch thumbnail features (if separate, but usually joined or in same table for some architectures)
    # The training pipeline signature is: train_all_models(video_data, thumbnail_features)
    # Let's see if we can get everything from one table or if we need another fetch.
    # Looking at ctr_data_collector, it stores to 'ctr_training_data' table which has features JSON.
    # training_pipeline.load_training_data_from_supabase fetches 'video_performance'.
    # This might be a mismatch. 
    # Let's check ctr_data_collector -> stores to `ctr_training_data`
    # Let's check `training_pipeline.py` -> `_train_ctr_model` logic expects data.
    
    # UPDATE: creating a better fetch logic here directly to ensure we get what we need.
    from premium.ml_models.ctr_data_collector import CTRDataCollector
    collector = CTRDataCollector()
    
    # Use collector to get training dataset (it likely has a method or we fetch manually)
    print("   Fetching CTR training data (including thumbnails)...")
    ctr_df = collector.prepare_training_dataset(min_impressions=50)
    
    # Backfill missing columns for legacy data
    if not ctr_df.empty:
        print("   Backfilling missing columns for model compatibility...")
        if 'view_count' not in ctr_df.columns:
            if 'clicks' in ctr_df.columns:
                print("   - filled 'view_count' from 'clicks'")
                ctr_df['view_count'] = ctr_df['clicks']
            else:
                ctr_df['view_count'] = 0
                
        if 'subscriber_count' not in ctr_df.columns:
            print("   - filled 'subscriber_count' with default (1000)")
            ctr_df['subscriber_count'] = 1000
            
        if 'channel_median_views' not in ctr_df.columns:
            print("   - filled 'channel_median_views' with batch median")
            # Calculate per channel median from the current batch
            if 'channel_id' in ctr_df.columns and 'view_count' in ctr_df.columns:
                medians = ctr_df.groupby('channel_id')['view_count'].transform('median')
                ctr_df['channel_median_views'] = medians
            else:
                ctr_df['channel_median_views'] = ctr_df['view_count'] # Fallback
                
        # Required columns for views_predictor
        if 'views_24h' not in ctr_df.columns:
             ctr_df['views_24h'] = ctr_df['view_count'] * 0.2
        if 'views_7d' not in ctr_df.columns:
             ctr_df['views_7d'] = ctr_df['view_count']
    
    if ctr_df.empty:
        print("⚠️ No training data found. Using synthetic data for demonstration/initialization only.")
        # Create dummy data so we at least have a model file
        import numpy as np
        import json
        ctr_df = pd.DataFrame({
            'video_id': [f'mock_{i}' for i in range(50)],
            'channel_id': ['mock_channel'] * 50,
            'view_count': np.random.randint(1000, 50000, 50),
            'impressions': np.random.randint(2000, 100000, 50),
            'ctr_actual': np.random.uniform(2.0, 10.0, 50),
            'title': ['Mock Video Title ' + str(i) for i in range(50)],
            'thumbnail_features': [json.dumps({'face_count': 1, 'contrast_score': 0.5}) for _ in range(50)],
            'subscriber_count': [10000] * 50,
            'channel_median_views': [5000] * 50
        })
        # Add required columns for all models
        ctr_df['views_24h'] = ctr_df['view_count'] * 0.2
        ctr_df['views_7d'] = ctr_df['view_count']
        ctr_df['like_count'] = ctr_df['view_count'] * 0.05
        ctr_df['comment_count'] = ctr_df['view_count'] * 0.01

    print(f"   Got {len(ctr_df)} training samples.")
    
    print("🧠 Training models...")
    results = pipeline.train_all_models(ctr_df, None) # thumbnail features often already in ctr_df
    
    print("\n📊 Results:")
    for name, res in results.items():
        status = "✅ Success" if res.success else f"❌ Failed: {res.error}"
        print(f"   {name}: {status}")
        if res.success:
            print(f"     Saved to: {res.model_path}")
            print(f"     Metrics: {res.metrics}")

if __name__ == "__main__":
    run_training()
