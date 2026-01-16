---
name: demand-signals
description: Skill 3 of GAP Intel - Demand Signal Extraction. Use when implementing question mining from comments, calculating opportunity scores, or identifying what viewers want without access to watch time data.
---

# Skill 3: Demand Signal Extraction

Extracts high-demand topics from public signals without using watchtime data. Identifies what viewers want through question mining, competitor analysis, and trend detection.

## When to Use This Skill

- Implementing question mining from comments
- Building demand/opportunity scoring algorithms
- Extracting pain points from viewer comments
- Comparing demand signals to content supply (for gap scoring)
- Implementing competitor gap analysis

## Core Metrics

### 1. Question Frequency Score (QFS)

```python
QFS = (Topic_Mentions_in_Comments / Total_Comments) × 100

# Process:
# 1. Mine all questions from comment sections
# 2. Extract topic/subject of each question
# 3. Tally frequency of each topic
# 4. Score by percentage

# Scoring:
# - QFS > 5%: High demand (topic asked frequently)
# - QFS 2-5%: Moderate demand
# - QFS 0.5-2%: Low demand
# - QFS < 0.5%: Minimal demand

# Example:
# Total comments: 1000
# "How do I rank faster?" mentions: 47
# QFS for ranking: 4.7% (high demand)
```

### 2. Demand Confidence Score

```python
# Signals that validate demand (with weights):
SIGNAL_WEIGHTS = {
    'questions_in_comments': 1.0,
    'same_question_multiple_videos': 1.5,
    'competitor_high_engagement': 1.5,
    'trending_keywords': 1.2,
    'search_volume_confirmed': 2.0
}

Confidence = (Weighted_Signals / Max_Possible_Signals) × 100

# Interpretation:
# - >80%: Strong demand validation
# - 60-80%: Moderate validation
# - 40-60%: Weak validation (needs more signals)
# - <40%: Insufficient evidence
```

### 3. Opportunity Size Estimation

```python
Opportunity_Score = (Demand_Strength × Competitor_Gap × Audience_Interest) / 3

# Scale: 1-10

# Factors:
# - Demand Strength: QFS + confidence (1-10)
# - Competitor Gap: Topics competitors don't cover well (1-10)
# - Audience Interest: Engagement on similar topics (1-10)

# Scoring:
# - 8-10: Huge opportunity (high demand, low supply)
# - 6-8: Good opportunity
# - 4-6: Medium opportunity
# - 2-4: Small opportunity
# - <2: Not worth pursuing
```

### 4. Pain Point Severity

```python
Pain_Severity = (Frequency × Emotional_Intensity × Recency) / 1000

# Classification types:
PAIN_TYPES = {
    'procedural': "How do I...",
    'technical': "This doesn't work because...",
    'understanding': "I don't understand...",
    'resource': "I can't find...",
    'context': "How do I apply this in...?"
}

# Scoring each dimension (1-10):
# - Frequency: How often mentioned
# - Intensity: How urgent/frustrated the tone
# - Recency: How recent (recent = higher)

# Example:
# "I can't get my videos ranked"
# - Frequency: 14 mentions (score: 7)
# - Intensity: Very frustrated (score: 8)
# - Recency: Last 2 months (score: 9)
# Severity = (7 × 8 × 9) / 1000 = 0.504 = HIGH PRIORITY
```

## Implementation Example

```python
def extract_and_classify_questions(comments_data):
    """Extract questions and classify by topic/intent"""
    questions = []
    
    for comment in comments_data:
        if '?' in comment['text'] or contains_question_keywords(comment['text']):
            question = {
                'text': comment['text'],
                'author': comment['author'],
                'timestamp': comment['timestamp'],
                'question_type': classify_question_type(comment['text']),
                'topic': extract_topic(comment['text']),
                'urgency': score_urgency(comment['text']),
                'like_count': comment.get('like_count', 0)
            }
            questions.append(question)
    
    return questions

def extract_topic(question_text):
    """Extract main topic from question"""
    topics = {
        'ranking': ['rank', 'ranking', 'algorithm', 'visibility'],
        'tools': ['tool', 'software', 'recommend', 'use'],
        'timing': ['how long', 'how many days', 'when'],
        'implementation': ['apply', 'implement', 'specific', 'niche'],
        'troubleshooting': ['error', 'doesn\'t work', 'bug', 'not working']
    }
    
    question_lower = question_text.lower()
    for topic_name, keywords in topics.items():
        if any(kw in question_lower for kw in keywords):
            return topic_name
    return 'other'

def score_opportunities(demand_signals, channel_coverage):
    """Score each demand signal as opportunity"""
    opportunities = []
    
    for topic, signals in demand_signals.items():
        demand_strength = min(10, signals['comment_questions'] / 5)
        competitor_gap = max(0, 10 - signals['competitor_coverage'] / 2)
        audience_interest = signals['urgency_score'] / len(demand_signals)
        
        opportunity_score = (demand_strength + competitor_gap + audience_interest) / 3
        channel_coverage_score = channel_coverage.get(topic, 0)
        
        opportunities.append({
            'topic': topic,
            'opportunity_score': opportunity_score,
            'demand_strength': demand_strength,
            'competitor_gap': competitor_gap,
            'audience_interest': audience_interest,
            'channel_coverage': channel_coverage_score,
            'confidence': calculate_confidence(signals),
            'recommended_action': 'create' if opportunity_score > 6 and channel_coverage_score < 1 else 'expand'
        })
    
    return sorted(opportunities, key=lambda x: x['opportunity_score'], reverse=True)
```

## Question Type Categories

| Question Type | Example | Gap Indicator | Content Needed |
|--------------|---------|---------------|----------------|
| "How do I...?" | "How do I rank faster?" | Procedural gap | Tutorial |
| "Why does...?" | "Why doesn't SEO work?" | Understanding gap | Explainer |
| "What's the difference...?" | "SEO vs ASO?" | Comparison gap | Comparison |
| "Is it possible to...?" | "Can I rank with no subs?" | Advanced gap | Advanced tutorial |
| "[Problem] how to fix?" | "Not indexed, how to fix?" | Problem gap | Troubleshooting |

## Output Format

```json
{
  "skill": "demand_signal_extraction",
  "summary": {
    "total_demand_signals": 247,
    "unique_topics": 18,
    "high_opportunity_count": 5,
    "total_questions_mined": 1847,
    "confidence_avg": 73.5
  },
  "top_opportunities": [
    {
      "rank": 1,
      "topic": "YouTube Algorithm 2025 Updates",
      "opportunity_score": 8.4,
      "demand_strength": 8.2,
      "competitor_gap": 7.8,
      "audience_interest": 8.3,
      "confidence": 86,
      "top_questions": [
        "How does the new algorithm prioritize satisfaction?",
        "Will my old videos rank differently now?",
        "What metadata changed in 2025?"
      ],
      "recommended_action": "Create comprehensive guide + 2-3 related videos"
    }
  ],
  "pain_points": [
    {
      "pain_point": "Can't get videos ranked",
      "frequency": 34,
      "emotional_intensity": 8.1,
      "severity": 0.612,
      "content_gap": "Detailed troubleshooting/diagnosis guide"
    }
  ]
}
```

## Integration Points

**This skill provides the DEMAND side of gap scoring:**
```
Gap Score = Skill 3 (Demand) vs Skill 2 (Supply)
```

**Feeds into:**
- Gap identification engine
- Content recommendations (what to create)
- Report generation (opportunity list)
- Priority ranking for content calendar

## Validation Checklist

- [ ] Minimum 100 comments for demand analysis
- [ ] Question extraction accuracy >80%
- [ ] Topic classification validated
- [ ] Confidence scores reflect uncertainty
- [ ] Competitor coverage data is recent
