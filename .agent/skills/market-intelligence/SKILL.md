---
name: market-intelligence
description: Skill for competitor analysis and market trends. Use when analyzing Google Trends momentum, exploring Niche patterns, or benchmarking competitors.
---

# Market Intelligence (Competitor & Trends)

Provides real-time market context by analyzing Google Trends momentum and discovering niche patterns without needing hardcoded competitor lists.

## When to Use This Skill

- Analyzing keyword momentum (Rising vs. Falling)
- Finding trending videos in a specific niche (Niche Explorer)
- Calculating market saturation scores
- Benchmarking channel performance against niche averages
- Identifying "Blue Ocean" topics with high interest but low competition

## Core Metrics

### 1. Trend Momentum Score (0-100)

Calculates the strength and direction of a topic's interest.

```python
Trend_Strength = (Current_Score * 0.4) + (Avg_Score * 0.3) + (Momentum_Bonus)

# Trajectory Classification:
# - RISING: (>25% growth)
# - STABLE: (-5% to +5%)
# - FALLING: (<-5% decline)
```

### 2. Niche Saturation Score (0-100)

Determines how crowded a topic is based on top search results.

```python
Saturation = View_Volume_Score + Channel_Diversity_Score + Recency_Score

# Classifications:
# - HIGH (>70): Hard to rank, established players dominate
# - MEDIUM (40-70): Competitive but accessible
# - LOW (<40): Opportunity for new entrants
```

## Niche Explorer (`explore_niche`)

Instead of tracking specific competitors, we scan the "Zeitgeist" of the niche:

1.  **Dynamic Queries**: `"{niche} tutorial"`, `"{niche} guide"`, `"best {niche}"`
2.  **Top Video Scan**: Analyze top 10 results for each query
3.  **Pattern Extraction**:
    *   Common title words (n-grams)
    *   Presence of years/money/numbers
    *   Average video length
    *   Visual styles

## Implementation Reference (`market_intel.py`)

### Google Trends Analysis

```python
def analyze_market_trends(keywords, region="GB"):
    """
    Checks specific keywords against Google Trends API.
    Returns score, trajectory (RISING/FALLING), and momentum %.
    """
    # ... pytrends implementation ...
```

### Dynamic Niche Discovery

```python
def explore_niche(youtube, category="finance"):
    """
    Scans YouTube search results to find what's working NOW.
    Returns trending videos and saturation metrics.
    """
    # ... search and statistics implementation ...
```

## Output Format

```json
{
  "market_context": {
    "niche": "trading",
    "saturation_score": 75,
    "saturation_level": "HIGH",
    "trending_topics": [
      {"keyword": "prop firms", "trajectory": "RISING"},
      {"keyword": "forex basics", "trajectory": "STABLE"}
    ]
  },
  "competitor_intelligence": {
    "top_performing_videos": [ ... ],
    "winning_patterns": {
      "titles_with_money": 85,  # 85% of top videos show money
      "titles_with_year": 60,   # 60% include "2025"
      "avg_length_seconds": 950
    }
  }
}
```

## Validation Checklist

- [ ] Are trend keywords cleaned (no emojis/special chars)?
- [ ] Is rate limiting handled for Google Trends (2s sleep)?
- [ ] Does Niche Explorer deduct known "Stop Words" from title analysis?
- [ ] Is saturation score normalized correctly to 0-100?
