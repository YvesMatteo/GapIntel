# Skill 3: Demand Signal Extraction

## Overview
Extracts high-demand topics from public signals without using watchtime data. Identifies what viewers want through question mining, competitor analysis, and trend detection.

## Core Metrics

### 1. Question Frequency Score
```
QFS = (Specific topic mentioned in comments) / (Total comments) × 100

Process:
1. Mine all questions from comment sections
2. Extract topic/subject of each question
3. Tally frequency of each topic
4. Score by percentage of total comments

Scoring:
- QFS > 5%: High demand (topic asked about frequently)
- QFS 2-5%: Moderate demand
- QFS 0.5-2%: Low demand
- QFS < 0.5%: Minimal demand

Example:
Total comments: 1000
"How do I rank faster?" mentions: 47
"What tools should I use?" mentions: 34
QFS for ranking: 4.7% (high demand)
QFS for tools: 3.4% (moderate demand)
```

### 2. Demand Confidence Score
```
Confidence = (Signal Validation Count) / (Total possible signals) × 100

Signals that validate demand:
1. Questions in comments (weight: 1x)
2. Same question in multiple videos (weight: 1.5x)
3. Competitor videos on topic get high engagement (weight: 1.5x)
4. Topic appears in trending keywords (weight: 1.2x)
5. Search volume data confirms demand (weight: 2x)

Calculation:
- Count all signals pointing to demand
- Weight each signal
- Confidence = (Weighted signals / max possible) × 100

Interpretation:
- >80% confidence: Strong demand validation
- 60-80% confidence: Moderate validation
- 40-60% confidence: Weak validation (needs more signals)
- <40% confidence: Insufficient evidence
```

### 3. Opportunity Size Estimation
```
OpportunitySizeis = (Demand Signal Strength × Competitor Gap × Audience Interest)

Factors:
- Demand Signal Strength: QFS + confidence
- Competitor Gap: (Videos that don't cover well / total competitor videos)
- Audience Interest: Engagement on similar topics

Scoring (1-10 scale):
- Score 8-10: Huge opportunity (high demand, low supply, big audience)
- Score 6-8: Good opportunity (solid demand and gap)
- Score 4-6: Medium opportunity
- Score 2-4: Small opportunity
- Score <2: Minimal opportunity (not worth pursuing)

Example calculation:
Topic: "YouTube Algorithm Updates 2025"
- Demand strength: 7.2 (mentioned in 32 comments)
- Competitor gap: 6.5 (only 3 of 20 competitors cover recent updates)
- Audience interest: 8.1 (related videos get high engagement)
Average opportunity: (7.2 + 6.5 + 8.1) / 3 = 7.3 = Good opportunity
```

### 4. Pain Point Extraction
```
Pain Point Severity = (Mention Frequency × Emotional Intensity × Recency)

Classification:
- Procedural pain: "How do I..."
- Technical pain: "This doesn't work because..."
- Understanding pain: "I don't understand..."
- Resource pain: "I can't find..."
- Context pain: "How do I apply this in...?"

Scoring each pain point:
1. Frequency: How often mentioned (1-10)
2. Emotional Intensity: How urgent/frustrated (1-10)
3. Recency: How recent (1-10, recent = higher)

Example:
"I can't get my videos ranked"
- Frequency: 14 mentions (score: 7)
- Intensity: Very frustrated tone (score: 8)
- Recency: All within last 2 months (score: 9)
Severity = (7 × 8 × 9) / 1000 = 0.504 = HIGH PRIORITY

Top pain points scored and ranked
```

## Implementation Workflow

### Step 1: Question Mining
```python
def extract_and_classify_questions(comments_data):
    """
    Extract questions and classify by topic/intent
    """
    questions = []
    
    for comment in comments_data:
        # Identify questions
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
    """
    Extract main topic from question
    """
    # Using NLP or keyword matching
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
```

### Step 2: Demand Aggregation
```python
def aggregate_demand_signals(questions, competitor_data, trends_data):
    """
    Combine multiple demand signals
    """
    demand_signals = {}
    
    # Process extracted questions
    for question in questions:
        topic = question['topic']
        
        if topic not in demand_signals:
            demand_signals[topic] = {
                'comment_questions': 0,
                'total_mentions': 0,
                'urgency_score': 0,
                'competitor_coverage': 0,
                'trend_signals': 0
            }
        
        demand_signals[topic]['comment_questions'] += 1
        demand_signals[topic]['total_mentions'] += 1
        demand_signals[topic]['urgency_score'] += question['urgency']
    
    # Add competitor signals
    for topic, coverage_data in competitor_data.items():
        if topic in demand_signals:
            demand_signals[topic]['competitor_coverage'] = coverage_data['video_count']
        else:
            demand_signals[topic] = {
                'comment_questions': 0,
                'competitor_coverage': coverage_data['video_count'],
                'trend_signals': 0
            }
    
    # Add trending signals
    for trend_topic, trend_data in trends_data.items():
        if trend_topic in demand_signals:
            demand_signals[trend_topic]['trend_signals'] = trend_data['trending_score']
    
    return demand_signals
```

### Step 3: Opportunity Scoring
```python
def score_opportunities(demand_signals, channel_coverage):
    """
    Score each demand signal as opportunity
    """
    opportunities = []
    
    for topic, signals in demand_signals.items():
        # Calculate demand strength (1-10)
        demand_strength = min(10, signals['comment_questions'] / 5)
        
        # Calculate competitor gap (1-10)
        competitor_gap = max(0, 10 - signals['competitor_coverage'] / 2)
        
        # Calculate audience interest
        audience_interest = signals['urgency_score'] / len([s for s in demand_signals.values()])
        
        # Overall score
        opportunity_score = (demand_strength + competitor_gap + audience_interest) / 3
        
        # Check if channel already covers this
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

## Output Format

### Demand Signals Report
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
      "signals": {
        "questions_count": 47,
        "avg_urgency": 7.9,
        "competitor_coverage": "3/20 videos",
        "trending_score": 7.5
      },
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
      "recency_score": 9,
      "severity": 0.612,
      "content_gap": "Detailed troubleshooting/diagnosis guide"
    }
  ]
}
```

## Gap Intel Integration

**Feeds into:**
- Gap scoring (demand-side of supply/demand)
- Content recommendations (what to create)
- Report generation (opportunity list)