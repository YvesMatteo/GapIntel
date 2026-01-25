# Market Intelligence

Competitor analysis and market trends using Google Trends and niche exploration.

## Instructions

When working on market intelligence features:

1. **Trend Momentum Score (0-100)**:
   ```python
   Trend_Strength = (Current_Score * 0.4) + (Avg_Score * 0.3) + (Momentum_Bonus)
   ```
   - RISING: >25% growth
   - STABLE: -5% to +5%
   - FALLING: <-5% decline

2. **Niche Saturation Score (0-100)**:
   ```python
   Saturation = View_Volume_Score + Channel_Diversity_Score + Recency_Score
   ```
   - HIGH (>70): Hard to rank, established players
   - MEDIUM (40-70): Competitive but accessible
   - LOW (<40): Opportunity for new entrants

3. **Niche Explorer**:
   - Dynamic Queries: "{niche} tutorial", "{niche} guide", "best {niche}"
   - Scan top 10 results for each query
   - Extract patterns: title n-grams, years/numbers, avg video length

4. **Output Format**:
   ```json
   {
     "market_context": {
       "niche": "trading",
       "saturation_score": 75,
       "saturation_level": "HIGH",
       "trending_topics": [{"keyword": "...", "trajectory": "RISING"}]
     },
     "competitor_intelligence": {
       "top_performing_videos": [...],
       "winning_patterns": {"titles_with_money": 85, "titles_with_year": 60}
     }
   }
   ```

5. **Rate Limiting**: 2s sleep for Google Trends API
