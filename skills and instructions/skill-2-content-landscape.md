# Skill 2: Content Landscape Mapping

## Overview
Maps the existing content ecosystem on a channel to identify true gaps vs. under-explained topics. Creates a visual/data representation of what has been covered and at what depth.

## Business Value
- **Supply-side analysis**: What content already exists on channel
- **Format analysis**: What content types are being used
- **Consistency gaps**: Where publishing is inconsistent
- **Depth detection**: Topics covered shallowly vs. comprehensively

## Core Metrics

### 1. Topic Coverage Index
```
Coverage Index = (Topics Covered / Total Possible Topics in Niche) × 100

Process:
1. Define all topics in creator's niche (research, keyword analysis)
2. Scan channel video catalog for coverage
3. Count distinct topics covered
4. Calculate percentage

Example - YouTube SEO Niche:
Total topics: 50 (keyword research, metadata, CTR, retention, tags, etc.)
Topics covered by channel: 34
Coverage Index = (34/50) × 100 = 68%

Interpretation:
- >80%: Comprehensive coverage (few gaps remain)
- 60-80%: Good coverage (some significant gaps)
- 40-60%: Selective coverage (many gaps)
- <40%: Narrow focus (significant opportunity)
```

### 2. Topic Saturation Score
```
Saturation = (Videos per Topic) / (Average Videos per Topic)

Calculation:
- Count how many videos address each major topic
- Calculate average coverage
- Identify over-saturated vs. under-covered topics

Scoring:
- Saturation >2.0: Over-covered topic (audience knows this well)
- Saturation 0.8-2.0: Well-balanced coverage
- Saturation 0.3-0.8: Light coverage (opportunity to expand)
- Saturation <0.3: Minimal coverage (gap candidate)

Example:
Topic "Keyword Research": 12 videos
Topic "Title Optimization": 3 videos
Topic "Tag Strategy": 1 video
Average = 5.3 videos per topic

Saturation scores:
- Keyword Research: 2.26 (over-covered)
- Title Optimization: 0.57 (under-covered)
- Tag Strategy: 0.19 (minimal coverage)
```

### 3. Format Diversity Index
```
Format Diversity = (Number of Different Formats) / (Total Videos) × 100

Format Types:
- Tutorial/How-to
- Review/Comparison
- Explanation/Educational
- Vlog/Behind-the-scenes
- Interview
- Case study/Story
- List/Roundup
- Live/Premiere
- Short-form/Shorts
- Podcast/Audio

Scoring:
- Using 5+ formats: Diverse portfolio
- Using 3-4 formats: Good variety
- Using 1-2 formats: Limited format range

Example:
Total videos: 100
Unique formats: 4
Format Diversity = 4%

Interpretation:
- High diversity: Appeals to different learning styles
- Low diversity: May miss audience segments preferring other formats
```

### 4. Upload Consistency Score
```
Consistency = (Variance in upload gaps) / (Average interval)

Process:
1. Calculate days between consecutive uploads
2. Find variance in those intervals
3. Lower variance = more consistent

Scoring:
- Coefficient of Variation (CV) <0.2: Highly consistent
- CV 0.2-0.4: Fairly consistent
- CV 0.4-0.6: Somewhat irregular
- CV >0.6: Highly irregular

Benchmark (for growth impact):
- Consistent weekly uploads: 156% higher growth
- Irregular uploads: 60% lower growth
```

### 5. Content Age Score (Freshness)
```
Freshness = (Videos updated in last 90 days) / (Total videos) × 100

Calculation:
- Track publish date of all videos
- Identify "evergreen" topics that need periodic updates
- Flag outdated content

Scoring:
- >30% recent: Fresh, actively maintained
- 10-30% recent: Somewhat dated
- <10% recent: Old content (potential refresh opportunity)
```

## Implementation Workflow

### Step 1: Topic Extraction
```python
def extract_topics_from_catalog(videos):
    """
    Extract topics from video titles and descriptions
    """
    topics = {}
    
    for video in videos:
        # Extract primary topic
        primary_topic = extract_primary_topic(video['title'])
        
        # Extract secondary topics
        secondary_topics = extract_keywords(video['description'])
        
        # Record topic mapping
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
```

### Step 2: Landscape Analysis
```python
def analyze_content_landscape(topics, niche_reference):
    """
    Analyze landscape against complete niche taxonomy
    """
    landscape = {
        'coverage_index': 0,
        'saturation_by_topic': {},
        'format_diversity': {},
        'gaps': [],
        'over_covered': []
    }
    
    # Coverage Index
    covered_topics = len(topics)
    total_niche_topics = len(niche_reference['topics'])
    landscape['coverage_index'] = (covered_topics / total_niche_topics) * 100
    
    # Saturation scores
    avg_videos_per_topic = sum(len(t['videos']) for t in topics.values()) / len(topics)
    
    for topic, data in topics.items():
        saturation = len(data['videos']) / avg_videos_per_topic
        landscape['saturation_by_topic'][topic] = saturation
        
        if saturation > 1.5:
            landscape['over_covered'].append({
                'topic': topic,
                'video_count': len(data['videos']),
                'saturation': saturation
            })
    
    # Identify gaps (topics in niche but not on channel)
    for niche_topic in niche_reference['topics']:
        if niche_topic not in topics:
            landscape['gaps'].append({
                'topic': niche_topic,
                'reason': 'Not covered',
                'opportunity_size': estimate_opportunity(niche_topic)
            })
    
    return landscape
```

### Step 3: Format Analysis
```python
def analyze_format_distribution(videos):
    """
    Analyze format diversity and effectiveness
    """
    format_data = {}
    
    for video in videos:
        video_format = classify_format(video)
        
        if video_format not in format_data:
            format_data[video_format] = {
                'count': 0,
                'total_views': 0,
                'avg_engagement': 0
            }
        
        format_data[video_format]['count'] += 1
        format_data[video_format]['total_views'] += video['viewCount']
        format_data[video_format]['avg_engagement'] += (video['likeCount'] + video['commentCount'])
    
    # Calculate metrics
    for format_type, data in format_data.items():
        data['avg_views'] = data['total_views'] / data['count']
        data['avg_engagement'] = data['avg_engagement'] / data['count']
        data['percentage'] = (data['count'] / len(videos)) * 100
    
    return format_data
```

## Output Format

### Content Landscape Report
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
      "recommended_action": "No new content needed, but could deepen with case studies"
    },
    {
      "topic": "Title Optimization",
      "video_count": 3,
      "saturation_score": 0.57,
      "classification": "under_covered",
      "formats_used": ["Tutorial"],
      "most_recent": "2024-11-15",
      "recommended_action": "Expand with examples, comparison videos, A/B testing guide"
    }
  ],
  "format_analysis": [
    {
      "format": "Tutorial",
      "video_count": 45,
      "percentage": 52,
      "avg_views": 18500,
      "avg_engagement": 42
    },
    {
      "format": "Case Study",
      "video_count": 18,
      "percentage": 21,
      "avg_views": 9200,
      "avg_engagement": 28
    }
  ],
  "identified_gaps": [
    {
      "gap_type": "missing_topic",
      "topic": "Competitor Analysis",
      "niche_reference_search_volume": "12000/month",
      "competitor_coverage": "45 creators cover this",
      "channel_coverage": "0 videos",
      "gap_severity": "high"
    },
    {
      "gap_type": "format_missing",
      "format": "Comparison Video",
      "similar_formats_on_channel": 0,
      "competitor_using": "78%",
      "recommendation": "Create comparison-based content (e.g., Tool A vs Tool B)"
    }
  ]
}
```

## Gap Intel Integration

**Feeds into:**
1. Gap identification engine (supply-side analysis)
2. Content recommendations (format and topic suggestions)
3. Growth acceleration (consistency analysis)

**Used by:**
- Gap scoring algorithm
- Content strategy recommendations
- Freshness/update suggestions