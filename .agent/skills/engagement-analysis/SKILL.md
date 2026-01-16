---
name: engagement-analysis
description: Skill 1 of GAP Intel - Engagement Quality Analysis. Use when implementing comment analysis, sentiment classification, or calculating engagement metrics like CVR, question density, and pain point extraction.
---

# Skill 1: Engagement Quality Analysis

Analyzes the quality and depth of viewer engagement beyond raw metrics. Transforms comment data and engagement patterns into actionable insights about content satisfaction and audience loyalty.

## When to Use This Skill

- Implementing or improving comment analysis features
- Working on sentiment classification (NLP)
- Calculating engagement quality metrics
- Extracting pain points and questions from comments
- Building repeat viewer detection

## Core Metrics

### 1. Comment-to-View Ratio (CVR)

```python
CVR = (Total Comments / Total Views) × 100

# Benchmarks:
# - Educational: 1-2% CVR
# - Tutorials: 0.5-1%
# - Entertainment: 0.1-0.5%
# - Top performers: 3-5% (exceptional)

# Interpretation:
# - CVR > 2%: Strong engagement (above average)
# - CVR 0.5-2%: Normal engagement
# - CVR < 0.5%: Low engagement (content quality issue)
```

### 2. Question Density Score

```python
Question_Density = (Question Comments / Total Comments) × 100

# Identify questions containing: "?", "how to", "why", "what", "where", "when"
# Filter out rhetorical questions

# Benchmarks:
# - High-quality educational: 30-40% questions
# - Mixed content: 15-25%
# - Low-quality: <10%

# Interpretation:
# - High = Audience engaging deeply, identifying gaps
# - Low = Content too simple or disengaging
```

### 3. Comment Depth Score

```python
Depth_Score = Reply_Comments / Top_Level_Comments

# Scoring:
# - Score > 0.5: Deep engagement (good community)
# - Score 0.2-0.5: Moderate depth
# - Score < 0.2: Shallow engagement (one-way communication)
```

### 4. Sentiment Distribution

```python
def classify_sentiment(comment_text):
    text = comment_text.lower()
    
    if any(w in text for w in ['thank', 'help', 'great', 'love', 'perfect']):
        return 'positive'
    elif any(w in text for w in ['don\'t understand', 'confused', 'stuck']):
        return 'confusion'
    elif any(w in text for w in ['tried', 'worked for me', 'applied']):
        return 'implementation_success'
    elif any(w in text for w in ['?', 'how', 'what', 'why']):
        return 'inquiry'
    elif any(w in text for w in ['don\'t', 'hate', 'fail', 'wrong']):
        return 'negative'
    return 'neutral'

# Benchmarks:
# - Healthy content: 70%+ positive
# - Mixed feedback: 50-70% positive
# - Poor content: <50% positive
```

### 5. Pain Point Extraction

```python
# High-Value Problem Indicators:
pain_point_keywords = [
    "I don't understand",
    "Didn't work for me",
    "How do I apply this to...",
    "What if [specific scenario]",
    "I'm stuck at..."
]

# Scoring:
# - Problem in 10+ comments = Content gap indicator
# - Problem in 20+ comments = Strong gap signal
# - Problem unique to channel = Under-explanation opportunity
```

### 6. Repeat Engagement Score

```python
Repeat_Score = (Commenters in 2+ videos / Unique Commenters) × 100

# Benchmarks:
# - Score > 20%: Loyal audience
# - Score 10-20%: Moderate loyalty
# - Score < 10%: Transient audience (growth challenge)
```

## Implementation Example

```python
def calculate_engagement_metrics(engagement_data):
    metrics = {}
    
    # 1. CVR
    total_comments = len(engagement_data['comments'])
    total_views = sum(v['view_count'] for v in engagement_data['videos'])
    metrics['cvr'] = (total_comments / total_views) * 100
    
    # 2. Question Density
    questions = [c for c in engagement_data['comments'] if contains_question(c['text'])]
    metrics['question_density'] = (len(questions) / total_comments) * 100
    
    # 3. Depth Score
    top_level = [c for c in engagement_data['comments'] if not c['is_reply']]
    replies = [c for c in engagement_data['comments'] if c['is_reply']]
    metrics['depth_score'] = len(replies) / max(len(top_level), 1)
    
    # 4. Sentiment
    sentiments = [classify_sentiment(c['text']) for c in engagement_data['comments']]
    metrics['sentiment_positive_pct'] = sentiments.count('positive') / len(sentiments) * 100
    
    # 5. Pain Points
    metrics['top_pain_points'] = extract_pain_points(engagement_data['comments'])
    
    # 6. Repeat Score
    authors = [c['author'] for c in engagement_data['comments']]
    unique_authors = set(authors)
    repeat_authors = [a for a in unique_authors if authors.count(a) > 1]
    metrics['repeat_score'] = len(repeat_authors) / len(unique_authors) * 100
    
    return metrics
```

## Output Format

```json
{
  "skill": "engagement_quality_analysis",
  "channel_summary": {
    "total_videos_analyzed": 87,
    "total_comments": 12543,
    "metrics": {
      "cvr": 0.53,
      "question_density": 32.5,
      "depth_score": 0.65,
      "sentiment_positive": 72.3,
      "repeat_score": 18.4
    }
  },
  "gaps_identified": [
    {
      "type": "under_explained",
      "topic": "Keyword research tools",
      "signal": "15 comments asking 'which tool should I use'",
      "confidence": "high"
    }
  ]
}
```

## Integration Points

**This skill feeds into:**
- Skill 3: Demand Signal Extraction (pain points = demand signals)
- Skill 4: Satisfaction Signals (sentiment = satisfaction proxy)
- Gap scoring algorithm
- Report generation (audience sentiment section)

## Validation Checklist

- [ ] Minimum 50 comments for reliable analysis
- [ ] Comment sample from last 90 days
- [ ] Sentiment classification accuracy validated
- [ ] Pain point clustering makes semantic sense
- [ ] Repeat score accounts for API limitations
