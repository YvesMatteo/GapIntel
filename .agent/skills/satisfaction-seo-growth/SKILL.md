---
name: satisfaction-seo-growth
description: Skills 4, 5, and 6 of GAP Intel - Viewer Satisfaction Signals, Metadata & SEO Analysis, and Growth Pattern Analysis. Use when implementing satisfaction inference, SEO optimization recommendations, or growth pattern detection.
---

# Skills 4, 5, 6: Satisfaction, SEO, and Growth

This skill covers three related analytical components that provide intelligence and optimization insights for GAP Intel.

## When to Use This Skill

- Implementing viewer satisfaction inference
- Building SEO/metadata optimization recommendations
- Analyzing title effectiveness patterns
- Detecting growth-driving patterns
- Working on upload consistency analysis

---

# Skill 4: Viewer Satisfaction Signals

Infers viewer satisfaction from public engagement signals (comment sentiment, ratios, repeat behavior) without access to watch time data.

## Core Metrics

### 1. Satisfaction Index

```python
SI = (Engagement_Quality × 0.6) + (Retention_Proxy × 0.3) + (Implementation_Success × 0.1)

# Components:
# 1. Engagement Quality (60%):
#    - Comment sentiment: % positive comments
#    - Like-to-view ratio vs category average
#    - Comment substance quality

# 2. Retention Proxy (30%):
#    - Comment distribution throughout video
#    - Repeat viewer indicators
#    - Time since publish vs comment recency

# 3. Implementation Success (10%):
#    - "It worked for me" type comments
#    - Question resolution in follow-ups
#    - Positive implementation stories

# Scoring (1-100):
# - 80+: Very satisfied audience
# - 60-80: Satisfied audience
# - 40-60: Mixed satisfaction
# - <40: Dissatisfied audience
```

### 2. Content Clarity Score

```python
CCS = Question_Density - Confusion_Ratio + Implementation_Stories

# Signals:
# + Question Density (engaged, learning)
# - Confusion signals ("I don't understand", "confused", "stuck")
# + Implementation stories (proves clarity leads to results)

# Interpretation:
# - High CCS: Content is clear, actionable
# - Low CCS: Audience confused, needs more explanation
```

### 3. Return Viewer Indicator

```python
RVI = (Commenters_in_2+_Videos / Total_Unique_Commenters) × 100

# Scoring:
# - >25%: Strong retention (audience returns)
# - 15-25%: Moderate retention
# - 5-15%: Weak retention
# - <5%: Very weak retention
```

### Implementation

```python
def classify_sentiment_advanced(comment_text):
    """Multi-class sentiment classification"""
    signals = {
        'positive': ['thank', 'help', 'great', 'love', 'perfect', 'worked'],
        'confusion': ['don\'t understand', 'confused', 'unclear', 'stuck'],
        'implementation': ['tried', 'i did', 'worked for me', 'applied'],
        'question': ['?', 'how', 'what', 'why'],
        'negative': ['don\'t', 'hate', 'fail', 'wrong', 'not working']
    }
    
    text = comment_text.lower()
    detected = [s for s, kw in signals.items() if any(k in text for k in kw)]
    
    if 'confusion' in detected and 'negative' in detected:
        return 'frustrated'
    elif 'implementation' in detected and 'positive' in detected:
        return 'implementation_success'
    elif 'positive' in detected:
        return 'positive'
    elif 'question' in detected:
        return 'inquiry'
    elif 'confusion' in detected:
        return 'confusion'
    return 'neutral'
```

---

# Skill 5: Metadata & SEO Optimization

Analyzes title, description, and tag optimization patterns to identify SEO improvement opportunities.

## Core Metrics

### 1. Title Effectiveness Score

```python
TES = (Keyword_Placement × 0.4) + (Length_Optimization × 0.3) + (Hook_Strength × 0.3)

# Keyword Placement (40%):
# - In first 30 chars: +10
# - In first 50 chars: +8
# - Present anywhere: +5
# - Not present: +0

# Length Optimization (30%):
# - 50-60 characters: +10 (optimal)
# - 40-70 characters: +8
# - 30-80 characters: +5
# - >80 characters: +2

# Hook Strength (30%):
# - Number hook ("7 Ways"): +10
# - Question/curiosity: +8
# - Benefit hook: +7
# - Standard: +5
# - No hook: +2

# Scoring:
# - >8.5: Excellent
# - 7-8.5: Good
# - 5.5-7: Average
# - <5.5: Needs improvement
```

### 2. Description Quality Score

```python
DQS = (Front_Load × 0.4) + (Keyword_Distribution × 0.3) + (Structure × 0.3)

# Front-Load (first 150 chars):
# - Communicates value: +40
# - Includes primary keyword: +30
# - Creates urgency/curiosity: +20
# - Clear benefit: +10

# Structure:
# - Timestamps included: +20
# - Clear sections: +15
# - Links/CTAs: +15
# - Hashtags: +10

# Scoring:
# - >75: Excellent
# - 60-75: Good
# - 40-60: Average
# - <40: Poor
```

### 3. SEO Strength Index

```python
SSI = (Title × 0.35) + (Description × 0.35) + (Tags × 0.3)

# Overall Channel SEO Health:
# - >75: Strong SEO foundation
# - 60-75: Good SEO
# - 40-60: Moderate (improvement needed)
# - <40: Weak SEO
```

## Output Format

```json
{
  "skill": "metadata_seo_analysis",
  "channel_seo_strength": 68,
  "title_analysis": {
    "avg_effectiveness": 72,
    "opportunities": [
      {
        "issue": "Keyword Placement",
        "count": 23,
        "example": {
          "current": "How to Grow Your Channel: YouTube Strategy",
          "improved": "YouTube Growth Strategy: How to Grow Faster"
        }
      }
    ]
  }
}
```

---

# Skill 6: Growth Pattern Analysis

Analyzes patterns that correlate with subscriber growth and retention.

## Core Metrics

### 1. Content Series Effectiveness

```python
Series_Score = (Videos_in_Series × Avg_Engagement) / Total_Videos

# Scoring:
# - Score > 2: Highly effective series
# - Score 1-2: Series boost engagement
# - Score < 1: Minimal series impact

# Research shows:
# - Series increase watch time by 89%
# - Playlist organization: +34% session duration
```

### 2. Upload Consistency Impact

```python
CI = (Days_Between_Uploads - Variance) / Std_Deviation

# Impact on growth (from research):
# - Consistent weekly: 156% higher growth
# - Bi-weekly consistent: 89% higher growth
# - Sporadic uploads: 60% lower growth

# Target: Coefficient of variation < 0.3
```

### 3. Growth Acceleration Correlation

```python
GAC = Topic_Authority × Format_Consistency × Series_Implementation

# Identifies:
# - Topics that drive subscriber growth
# - Formats most effective for growth
# - Series structure impact on retention
```

## Growth Drivers (Research-Backed)

1. **Upload Consistency**: 156% growth improvement
2. **Community Engagement**: 134% improvement
3. **Content Series**: 89% improvement
4. **Multi-Format Strategy**: 156% watch time improvement
5. **Community-First Approach**: 92% engagement improvement

## Integration Points

**Skills 4, 5, 6 together provide:**
- Content quality validation (Skill 4)
- Optimization recommendations (Skill 5)
- Growth acceleration tactics (Skill 6)

**Feed into:**
- Report generation (satisfaction + SEO + growth sections)
- Recommendation engine
- Dashboard metrics display
- Gap validation (is the gap worth pursuing?)

## Validation Checklist

- [ ] Satisfaction scores correlate with engagement metrics
- [ ] SEO recommendations are actionable
- [ ] Growth patterns validated on multiple channels
- [ ] Consistency calculations handle irregular uploads
- [ ] Series detection works across playlists
