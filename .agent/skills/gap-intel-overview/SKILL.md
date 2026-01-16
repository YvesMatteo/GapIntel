---
name: gap-intel-overview
description: Master guide for GAP Intel YouTube channel analysis tool. Use when working on any GAP Intel feature, understanding the 7-skill architecture, or implementing the gap analysis pipeline. Essential reading for all GAP Intel development work.
---

# GAP Intel: Complete Overview

This skill provides comprehensive understanding of the GAP Intel YouTube channel analysis tool - a SaaS platform that identifies content gaps and opportunities for YouTube creators.

## When to Use This Skill

- Starting any new GAP Intel feature development
- Understanding how the 7 analytical skills work together
- Debugging or improving the analysis pipeline
- Working on the report generation or dashboard
- Need context on what data is available via YouTube API

## What Is GAP Intel?

GAP Intel is a YouTube content gap analysis tool that:
1. Accepts a YouTube channel name + email from users
2. Processes payment via Stripe
3. Runs an AI-powered analysis identifying content opportunities
4. Sends users a unique access key to view their personalized GAP Report

## The 7-Skill Architecture

GAP Intel uses 7 parallel analytical skills that feed into a synthesis engine:

```
YouTube Channel Data
       ↓
┌──────────────────────────────────────────────────────────┐
│              7 Parallel Skills                            │
├──────────┬──────────┬──────────┬──────────────────────────┤
│ Skill 1  │ Skill 2  │ Skill 3  │ Skills 4/5/6/7          │
│ Engage   │ Content  │ Demand   │ Satisfaction/SEO/Growth │
└──────────┴──────────┴──────────┴──────────────────────────┘
       ↓
┌──────────────────────────────────────┐
│   Results Synthesis Engine           │
│ - Gap Identification                 │
│ - Opportunity Ranking                │
│ - Recommendation Generation          │
└──────────────────────────────────────┘
       ↓
    GAP Report Dashboard
```

### Skill Summary

| Skill | Purpose | Key Metrics |
|-------|---------|-------------|
| **1. Engagement Quality** | Analyze comment depth and quality | CVR, Question Density, Sentiment |
| **2. Content Landscape** | Map existing channel content | Topic Coverage, Saturation |
| **3. Demand Signals** | Extract what viewers want | Question Frequency, Opportunity Score |
| **4. Satisfaction Signals** | Infer viewer satisfaction | Satisfaction Index, Clarity Score |
| **5. Metadata & SEO** | Evaluate optimization | Title Effectiveness, SEO Strength |
| **6. Growth Patterns** | Identify growth drivers | Series Effectiveness, Consistency |
| **7. CTR Proxy** | Analyze title effectiveness | Hook Strength, Title Correlation |

## Gap Identification Formula

```
Gap Score = (Demand Signals × Competitor Gap) / (Existing Content Coverage)

Where:
- High demand + Low supply = TRUE GAP (create new content)
- High demand + Poor coverage = UNDER_EXPLAINED (expand existing)
- Low demand + High coverage = Low priority (avoid)
```

## Data Available (Public YouTube API)

✅ **Can Collect:**
- Video titles, descriptions, tags
- View counts, like counts, comment counts
- Comments (text, author, timestamp, likes, replies)
- Subscriber counts
- Upload dates

❌ **Cannot Collect:**
- Watch time or retention curves
- Audience demographics
- Revenue data
- Click-through rates

**Solution**: Use engagement proxies and comment sentiment analysis instead.

## Tech Stack

- **Frontend**: Next.js 14 (App Router) + Tailwind CSS
- **Backend**: Railway API (Python)
- **Database**: Supabase (PostgreSQL)
- **Payments**: Stripe Payment Links + Webhooks
- **Email**: Resend

## Key Files

- `gap_analyzer.py` - Main analysis engine
- `youtube_processor.py` - YouTube API data collection
- `scoring_engine.py` - Gap scoring algorithm
- `vision_analyzer.py` - Thumbnail analysis
- `gap-intel-website/` - Next.js frontend

## Implementation Phases

1. **Foundation**: Skills 1-3 (core gap identification)
2. **Intelligence**: Skills 4-5 (validation + optimization)
3. **Growth**: Skills 6-7 (growth acceleration insights)

## Quality Gates

- Minimum 50 comments per channel for reliable analysis
- Minimum 20 videos for pattern recognition
- Confidence threshold: >65% for each skill output
- Analysis completion target: <5 minutes per channel

## Related Skills

For detailed implementation of each skill, see:
- `engagement-analysis` - Skill 1 implementation
- `content-landscape` - Skill 2 implementation
- `demand-signals` - Skill 3 implementation
- `satisfaction-seo-growth` - Skills 4, 5, 6 implementation
- `ctr-proxy-analysis` - Skill 7 implementation
- `youtube-research` - Research foundation and benchmarks
