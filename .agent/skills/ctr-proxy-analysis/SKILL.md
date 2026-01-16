---
name: ctr-proxy-analysis
description: Skill 7 of GAP Intel - Click-Through Rate Proxy Analysis. Use when analyzing title effectiveness, hook patterns, or implementing competitive title benchmarking without direct CTR access.
---

# Skill 7: CTR Proxy Analysis

Infers title and thumbnail effectiveness from available signals. Since we can't directly measure CTR without analytics access, we use engagement patterns and metadata analysis as proxies.

## When to Use This Skill

- Analyzing title patterns and hook effectiveness
- Comparing title strategies to competitors
- Generating title improvement recommendations
- Building A/B testing suggestions
- Implementing engagement-based CTR proxies

## Core Metrics

### 1. Title Hook Strength Score (THSS)

```python
THSS = Hook_Type_Score + Hook_Uniqueness + Keyword_Integration

# Hook Types (by CTR effectiveness):
HOOK_SCORES = {
    'number': 10,      # "7 Ways to...", "5 Secrets of..." - 3x better CTR
    'question': 8,     # "Why YouTube Won't Tell You This" - 2x better CTR
    'how_to': 7,       # "How to Grow YouTube Fast 2025" - 1.8x better CTR
    'comparison': 6,   # "YouTube vs TikTok Algorithm" - 1.5x better CTR
    'authority': 5,    # "Ultimate Guide to..." 
    'standard': 3      # Direct title without hook
}

# Scoring:
# - Score > 8: Excellent hook strength
# - Score 6-8: Good hook strength
# - Score 4-6: Average
# - < 4: Weak hook strength

# Example calculation:
# Title: "7 YouTube SEO Tips You Didn't Know"
# - Number hook: +10
# - Curiosity ("didn't know"): +2
# - Keyword integrated: +2
# THSS = 8.7 = Excellent
```

### 2. Title-to-Engagement Correlation (TEC)

```python
TEC = (Titles_With_Pattern_X / Total_Videos) × Avg_Engagement_Pattern_X

# Process:
# 1. Categorize all titles by hook type
# 2. Calculate average engagement for each category
# 3. Determine which patterns correlate with higher engagement
# 4. Identify underutilized high-performing patterns

# Example analysis:
# Number hook (12 videos): Avg CVR 1.2% ✓ High
# Question hook (8 videos): Avg CVR 0.8%
# How-to hook (34 videos): Avg CVR 0.5%
# Standard (33 videos): Avg CVR 0.3% ✗ Low
#
# Recommendation: Increase number-based hooks (4x better performance)
```

### 3. Title Structure Effectiveness (TSE)

```python
TSE = Keyword_Position + Length_Score + Clarity_Score

# Keyword Position:
# - Position 1-5 words: +10 (upfront = better CTR)
# - Position 6-10 words: +7
# - Position 11+ words: +3

# Length Optimization:
# - 50-60 chars: +10 (optimal for mobile + desktop)
# - 40-50 chars: +8
# - 60-70 chars: +8
# - 70+ chars: +4 (truncated on mobile)

# Clarity:
# - Clear, readable: +10
# - Some special chars: +7
# - Keyword stuffed: +2

# Total Score:
# - > 25: Excellent structure
# - 20-25: Good structure
# - 15-20: Average
# - < 15: Poor structure
```

### 4. Description First-Line Impact (DFI)

```python
DFI = First_150_Chars_Value / Total_Description_Quality

# Scoring Line 1 (before "Show More"):
# - States clear benefit: +10
# - Includes primary keyword: +8
# - Creates curiosity/urgency: +7
# - Mentions specific value: +6
# - Generic introduction: +2

# Example - Good vs Bad:
# ❌ "In this video I talk about YouTube. You'll learn stuff..."
#    Score: 8/30 = Poor
#
# ✓ "Master YouTube Algorithm 2025: Learn exactly how satisfaction 
#    signals work (not watch time) and increase your CTR by 40%."
#    Score: 28/30 = Excellent
```

### 5. Competitive Title Analysis (CTA)

```python
CTA = Your_Pattern_Usage vs Top_Performers × Your_Performance_on_Pattern

# Process:
# 1. Identify top-performing videos in niche
# 2. Analyze their title patterns
# 3. Compare to your patterns
# 4. Identify gaps in your approach

# Example:
# Top competitor patterns:
# - 70% use number hooks
# - 40% use curiosity elements
# - 60% use current year
# - 85% keep titles <60 chars
#
# Your patterns:
# - 25% number hooks (GAP: +45%)
# - 10% curiosity (GAP: +30%)
# - 50% year reference (close match)
# - 60% under 60 chars (GAP: +25%)
```

## Implementation Example

```python
import re

def analyze_title_patterns(videos):
    """Analyze title patterns and their correlation with engagement"""
    patterns = {
        'number_hook': [],
        'question_hook': [],
        'how_to_hook': [],
        'comparison_hook': [],
        'authority_hook': [],
        'standard': []
    }
    
    for video in videos:
        title = video['title']
        engagement = (video['likes'] + video['comments']) / video['views'] * 100
        
        # Classify hook type
        if re.search(r'\d+\s+(ways|tips|secrets|rules|steps|hacks)', title.lower()):
            pattern = 'number_hook'
        elif '?' in title:
            pattern = 'question_hook'
        elif title.lower().startswith('how to'):
            pattern = 'how_to_hook'
        elif 'vs' in title.lower():
            pattern = 'comparison_hook'
        elif 'ultimate' in title.lower() or 'complete' in title.lower():
            pattern = 'authority_hook'
        else:
            pattern = 'standard'
        
        patterns[pattern].append({
            'title': title,
            'engagement': engagement,
            'length': len(title),
            'views': video['views']
        })
    
    # Calculate averages per pattern
    for pattern, videos in patterns.items():
        if videos:
            avg_engagement = sum(v['engagement'] for v in videos) / len(videos)
            patterns[pattern] = {
                'count': len(videos),
                'avg_engagement': avg_engagement,
                'avg_length': sum(v['length'] for v in videos) / len(videos)
            }
    
    return patterns

def score_ctr_proxy(video_title):
    """Score title effectiveness as CTR proxy"""
    score = {
        'hook_strength': 0,
        'length_optimization': 0,
        'keyword_placement': 0,
        'overall_score': 0
    }
    
    # Hook Strength
    if re.search(r'\d+\s+(ways|tips|secrets)', video_title.lower()):
        score['hook_strength'] = 10
    elif '?' in video_title:
        score['hook_strength'] = 8
    elif video_title.lower().startswith('how to'):
        score['hook_strength'] = 7
    else:
        score['hook_strength'] = 3
    
    # Length Optimization
    length = len(video_title)
    if 50 <= length <= 60:
        score['length_optimization'] = 10
    elif 40 <= length <= 70:
        score['length_optimization'] = 8
    else:
        score['length_optimization'] = 4
    
    # Overall score (weighted)
    score['overall_score'] = (
        score['hook_strength'] * 0.4 +
        score['length_optimization'] * 0.3 +
        score['keyword_placement'] * 0.3
    )
    
    return score
```

## Output Format

```json
{
  "skill": "ctr_proxy_analysis",
  "channel_ctr_health": {
    "avg_title_strength": 7.2,
    "avg_front_load_score": 18.2,
    "pattern_effectiveness": {
      "number_hook": {
        "usage_percent": 25,
        "avg_engagement": 1.2,
        "rank": 1
      },
      "how_to_hook": {
        "usage_percent": 40,
        "avg_engagement": 0.6,
        "rank": 3
      }
    }
  },
  "opportunities": [
    {
      "opportunity": "Increase Number-Based Hooks",
      "current_usage": "25%",
      "competitor_usage": "70%",
      "gap": "+45%",
      "engagement_boost_potential": "340%",
      "examples": [
        {
          "topic": "YouTube Algorithm",
          "current_title": "How the YouTube Algorithm Works 2025",
          "suggested_title": "7 YouTube Algorithm Changes 2025 That Affect Your Rankings"
        }
      ]
    }
  ]
}
```

## CTR Improvement Patterns (Research-Backed)

| Pattern | Formula | CTR Boost |
|---------|---------|-----------|
| Number List | "[Number] [Benefit] [Keyword]" | +35% |
| How-To | "How to [Action] [Keyword]" | +28% |
| Question | "[Question] about [Keyword]?" | +20% |
| Comparison | "[Topic 1] vs [Topic 2]" | +18% |
| Guide | "Ultimate Guide to [Keyword]" | +22% |
| Urgency | "[Keyword] [Year/Trend]" | +15% |

## Integration Points

**This skill feeds into:**
- Title/description recommendations in gap reports
- A/B testing suggestions for creators
- SEO optimization section of reports

**Used by:**
- Content recommendations (title suggestions for gaps)
- Growth acceleration tactics
- Report generation (CTR improvement opportunities)

## Validation Checklist

- [ ] Hook classification covers all common patterns
- [ ] Engagement correlation is statistically significant
- [ ] Competitor data is from same niche
- [ ] Title improvement suggestions are natural language
- [ ] Length recommendations account for mobile truncation
