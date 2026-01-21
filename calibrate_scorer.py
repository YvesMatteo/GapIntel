"""
Calibrate Optimization Scorer
=============================

Goal: 
Use Ken Jee's real CTR data (224 videos) to validate/calibrate our RAG-based OptimizationScorer.
We are NOT training an ML model (too little data).
Instead, we are checking if our 'Optimization Score' correlates with actual 'CTR'.

Hypothesis: 
If the RAG rules are good, high Optimization Scores should have higher average CTR.
"""

import pandas as pd
import numpy as np
import sys
import os
from scipy.stats import pearsonr, spearmanr

# Add railway-api to path
current_dir = os.path.dirname(os.path.abspath(__file__))
railway_dir = os.path.join(current_dir, 'railway-api')
if railway_dir not in sys.path:
    sys.path.insert(0, railway_dir)

from premium.ml_models.optimization_scorer import OptimizationScorer

def calibrate():
    print("🧪 Calibrating RAG Scorer against Ken Jee's Data...")
    
    # Load Real Data
    df = pd.read_csv("training_data/kenjee_clean.csv")
    print(f"   Loaded {len(df)} videos. Avg CTR: {df['Impressions click-through rate (%)'].mean():.2f}%")
    
    scorer = OptimizationScorer()
    
    results = []
    
    for _, row in df.iterrows():
        title = str(row['Video title'])
        actual_ctr = row['Impressions click-through rate (%)']
        
        # Scorer evaluates title (we don't have thumbnails for this dataset, so we test title-part only)
        # Note: OptimizationScorer.evaluate does (thumb*0.6 + title*0.4). 
        # We should check just the title_score component since we lack thumbnails.
        score_res = scorer.evaluate(title, None)
        
        results.append({
            'title': title,
            'actual_ctr': actual_ctr,
            'rag_score': score_res.title_score, # Use specific title score
            'rating': score_res.rating
        })
        
    res_df = pd.DataFrame(results)
    
    # Correlation Analysis
    corr, p_value = spearmanr(res_df['rag_score'], res_df['actual_ctr'])
    
    print("\n   📊 Results:")
    print(f"   Correlation (Score vs CTR): {corr:.3f}")
    print(f"   P-value: {p_value:.3f}")
    
    # Bucket Analysis
    print("\n   📈 CTR by RAG Rating Bucket:")
    print(res_df.groupby('rating')['actual_ctr'].agg(['mean', 'count', 'std']))
    
    # Qualitative Check
    print("\n   🔍 Top Scored Titles (Check if they actually did well):")
    top = res_df.sort_values('rag_score', ascending=False).head(5)
    for _, r in top.iterrows():
        print(f"      Score {r['rag_score']:.0f} | CTR {r['actual_ctr']:.1f}%: {r['title'][:50]}...")

    print("\n   🔍 Worst Scored Titles:")
    bottom = res_df.sort_values('rag_score', ascending=True).head(5)
    for _, r in bottom.iterrows():
        print(f"      Score {r['rag_score']:.0f} | CTR {r['actual_ctr']:.1f}%: {r['title'][:50]}...")
        
    return corr

if __name__ == "__main__":
    calibrate()
