---
name: content-landscape
description: Skill 2 of GAP Intel - Content Landscape Mapping. Use when implementing topic extraction, analyzing channel content coverage, identifying format gaps, or mapping existing content ecosystem.
---

# Skill 2: Content Landscape Mapping

Maps the existing content ecosystem on a channel to identify true gaps vs. under-explained topics. Creates a data representation of what has been covered and at what depth.

## When to Use This Skill

- Implementing topic extraction from video titles/descriptions
- Analyzing content coverage across a channel
- Identifying format gaps (tutorial vs. review, etc.)
- Calculating upload consistency
- Comparing channel coverage to niche standards

## Core Metrics

### 1. Topic Coverage Index

```python
Coverage_Index = (Topics Covered / Total Possible Topics in Niche) × 100

# Process:
# 1. Define all topics in creator's niche (research + keyword analysis)
# 2. Scan channel video catalog for coverage
# 3. Count distinct topics covered
# 4. Calculate percentage

# Example - YouTube SEO Niche:
# Total topics: 50 (keyword research, metadata, CTR, retention, tags, etc.)
# Topics covered: 34
# Coverage Index = (34/50) × 100 = 68%

# Interpretation:
# - >80%: Comprehensive coverage (few gaps)
# - 60-80%: Good coverage (some gaps)
# - 40-60%: Selective coverage (many gaps)
# - <40%: Narrow focus (significant opportunity)
```

### 2. Topic Saturation Score

```python
Saturation = Videos_Per_Topic / Avg_Videos_Per_Topic

# Scoring:
# - Saturation > 2.0: Over-covered (audience knows this well)
# - Saturation 0.8-2.0: Well-balanced coverage
# - Saturation 0.3-0.8: Light coverage (opportunity to expand)
# - Saturation < 0.3: Minimal coverage (gap candidate)

# Example:
# Topic "Keyword Research": 12 videos → Saturation 2.26 (over-covered)
# Topic "Title Optimization": 3 videos → Saturation 0.57 (under-covered)
# Topic "Tag Strategy": 1 video → Saturation 0.19 (minimal)
```

### 3. Format Diversity Index

```python
# Format Types to track:
FORMATS = [
    "Tutorial/How-to",
    "Review/Comparison",
    "Explanation/Educational",
    "Vlog/Behind-the-scenes",
    "Interview",
    "Case study/Story",
    "List/Roundup",
    "Live/Premiere",
    "Short-form/Shorts",
    "Podcast/Audio"
]

# Scoring:
# - 5+ formats: Diverse portfolio
# - 3-4 formats: Good variety
# - 1-2 formats: Limited range (missing audience segments)
```

### 4. Upload Consistency Score

```python
# Calculate coefficient of variation (CV) in upload intervals
Consistency = Variance_in_Upload_Gaps / Average_Interval

# Scoring:
# - CV < 0.2: Highly consistent
# - CV 0.2-0.4: Fairly consistent
# - CV 0.4-0.6: Somewhat irregular
# - CV > 0.6: Highly irregular

# Impact on growth:
# - Consistent weekly uploads: 156% higher growth
# - Irregular uploads: 60% lower growth
```

### 5. Content Age Score (Freshness)

```python
Freshness = (Videos_Updated_Last_90_Days / Total_Videos) × 100

# Scoring:
# - >30% recent: Fresh, actively maintained
# - 10-30% recent: Somewhat dated
# - <10% recent: Old content (refresh opportunity)
```

## Implementation Example

```python
def extract_topics_from_catalog(videos):
    """Extract topics from video titles and descriptions"""
    topics = {}
    
    for video in videos:
        primary_topic = extract_primary_topic(video['title'])
        secondary_topics = extract_keywords(video['description'])
        
        if primary_topic not in topics:
            topics[primary_topic] = {
                'videos': [],
                'subtopics': set(),
                'formats': [],
                'publish_dates': []
            }
        
        topics[primary_topic]['videos'].append(video['id'])
        topics[primary_topic]['subtopics'].update(secondary_topics)
        topics[primary_topic]['formats'].append(classify_format(video))
        topics[primary_topic]['publish_dates'].append(video['publishedAt'])
    
    return topics

def analyze_content_landscape(topics, niche_reference):
    """Analyze landscape against complete niche taxonomy"""
    landscape = {
        'coverage_index': 0,
        'saturation_by_topic': {},
        'gaps': [],
        'over_covered': []
    }
    
    # Coverage Index
    covered = len(topics)
    total_niche = len(niche_reference['topics'])
    landscape['coverage_index'] = (covered / total_niche) * 100
    
    # Saturation scores
    avg_videos = sum(len(t['videos']) for t in topics.values()) / len(topics)
    
    for topic, data in topics.items():
        saturation = len(data['videos']) / avg_videos
        landscape['saturation_by_topic'][topic] = saturation
        
        if saturation > 1.5:
            landscape['over_covered'].append({
                'topic': topic,
                'video_count': len(data['videos']),
                'saturation': saturation
            })
    
    # Identify gaps
    for niche_topic in niche_reference['topics']:
        if niche_topic not in topics:
            landscape['gaps'].append({
                'topic': niche_topic,
                'reason': 'Not covered',
                'opportunity_size': estimate_opportunity(niche_topic)
            })
    
    return landscape
```

## Output Format

```json
{
  "skill": "content_landscape_mapping",
  "summary": {
    "total_videos": 87,
    "topics_covered": 34,
    "unique_formats": 4,
    "coverage_index": 68,
    "freshness_score": 22
  },
  "topic_breakdown": [
    {
      "topic": "Keyword Research",
      "video_count": 12,
      "saturation_score": 2.26,
      "classification": "over_covered",
      "formats_used": ["Tutorial", "Case Study"],
      "most_recent": "2025-01-10",
      "recommended_action": "No new content needed"
    },
    {
      "topic": "Title Optimization",
      "video_count": 3,
      "saturation_score": 0.57,
      "classification": "under_covered",
      "recommended_action": "Expand with examples, comparison videos"
    }
  ],
  "identified_gaps": [
    {
      "gap_type": "missing_topic",
      "topic": "Competitor Analysis",
      "competitor_coverage": "45 creators cover this",
      "channel_coverage": "0 videos",
      "gap_severity": "high"
    }
  ]
}
```

## Integration Points

**This skill feeds into:**
- Gap identification engine (supply-side of supply/demand analysis)
- Content recommendations (format and topic suggestions)
- Skill 3: Demand Signals (supply vs. demand matching)

**Gap Score Formula:**
```
Gap = Skill 3 (Demand) vs Skill 2 (Supply)
High Demand + Low Supply = TRUE GAP
```

## Topic Extraction Techniques

1. **Title Parsing**: Extract main topic from video titles using NLP
2. **Keyword Extraction**: Pull keywords from descriptions
3. **Tag Analysis**: Use video tags for topic categorization
4. **Semantic Clustering**: Group similar topics together

## Validation Checklist

- [ ] Minimum 20 videos for pattern recognition
- [ ] Topic extraction accuracy >85%
- [ ] Niche reference taxonomy is comprehensive
- [ ] Format classification covers all video types
- [ ] Upload dates parsed correctly
