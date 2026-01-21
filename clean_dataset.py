import pandas as pd
import os

def clean_dataset():
    path = "training_data/external/Aggregated_Metrics_By_Video.csv"
    output_path = "training_data/kenjee_clean.csv"
    
    try:
        df = pd.read_csv(path)
        
        # Clean columns (remove \xad and whitespace)
        df.columns = [c.replace('\xad', '').strip() for c in df.columns]
        
        print("Cleaned Columns:", df.columns.tolist())
        
        # Check for key columns
        target_col = 'Impressions click-through rate (%)'
        title_col = 'Video title'
        
        if target_col in df.columns and title_col in df.columns:
            print(f"✅ Found key columns: '{title_col}' and '{target_col}'")
            print(f"   Rows: {len(df)}")
            print(f"   Avg CTR: {df[target_col].mean():.2f}%")
            
            df.to_csv(output_path, index=False)
            print(f"💾 Saved clean dataset to {output_path}")
        else:
            print("❌ Key columns missing after cleaning.")
            
    except Exception as e:
        print(f"❌ Error cleaning: {e}")

if __name__ == "__main__":
    clean_dataset()
