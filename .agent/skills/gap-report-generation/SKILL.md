---
name: gap-report-generation
description: Skill for synthesizing analytical data into the final GAP Report. Use when generating JSON/Markdown reports, scoring opportunities, or verifying gaps against transcripts.
---

# Gap Report Generation

Synthesizes data from all analytical skills into a cohesive, verified GAP Report. Matches demand signals against supply (transcripts) to prove opportunities are real.

## When to Use This Skill

- Generating the final `GAP_REPORT.md` or JSON output
- Verifying "True Gaps" by checking transcripts
- Ranking opportunities by potential impact
- Generating viral titles for identified gaps
- Summarizing pipeline statistics

## Core Process: The Gap Logic

```
Verified Gap = (High Demand Signal) AND (No Transcript Evidence)
```

1.  **Demand**: Extracted from comments (Skill 3)
2.  **Supply**: Transcripts of last 20 videos
3.  **Verification**: AI cross-references demand vs. supply
4.  **Result**:
    *   `TRUE_GAP`: Not found in transcripts
    *   `UNDER_EXPLAINED`: Found but brief/unclear
    *   `SATURATED`: Found and detailed

## Opportunity Scoring Algorithm

The `influence_scores` determine the ranking of opportunities:

```python
Overall_Score = (
    (Gap_Severity * 0.4) +       # TRUE_GAP=100, UNDER_EXPLAINED=60
    (Trend_Score * 0.3) +        # Google Trends (0-100)
    (Comment_Engagement * 0.2) + # Normalized engagement
    (Competitor_Opp * 0.1)       # Do competitors miss this too?
)
```

## Report Structure (Markdown)

The standard GAP Intel report structure:

1.  **Header**: Channel Name + Date
2.  **Pipeline Stats**: Table showing specific funnel (Raw -> High Signal -> Pain Points -> Verified Gaps)
3.  **#1 Top Opportunity**: The "Hero" recommendation
4.  **Verified Gaps (Actionable)**: List of True/Under-explained gaps with evidence
5.  **Already Covered**: What the creator *doesn't* need to make (Saturated)
6.  **Videos Analyzed**: Reference list
7.  **Competitors**: Who was benchmarked

## Implementation Reference (`gap_analyzer.py`)

### Phase 3: Gap Verification

```python
def verify_gaps_against_content(pain_points, transcripts):
    """
    Cross-reference user pain points against video transcripts.
    Strictly filters out hallucinations.
    """
    # ... logic using AI to check transcripts ...
    return verified_gaps_list
```

### Phase 4: Title Generation

```python
title_prompt = """
For each verified gap, generate 3 viral title ideas.
INFLUENCE SCORING:
- comment_influence
- competitor_influence
- trend_influence
- gap_severity_influence
...
"""
```

## JSON Output Schema

```json
{
  "pipeline_stats": {
    "raw_comments": 1500,
    "high_signal_comments": 450,
    "pain_points_found": 15,
    "true_gaps": 3,
    "under_explained": 5,
    "saturated": 7
  },
  "top_opportunity": {
    "topic_keyword": "Algorithm Changes 2026",
    "best_title": "YouTube's New 'Satisfaction' Metric Changes Everything",
    "reason": "High trend volume + recurring user confusion + zero channel coverage"
  },
  "opportunities": [
    {
      "topic_keyword": "...",
      "gap_status": "TRUE_GAP",
      "influence_scores": { ... },
      "viral_titles": [...]
    }
  ]
}
```

## Validation Checklist

- [ ] Does the Top Opportunity have a `TRUE_GAP` status?
- [ ] Are "Saturated" topics clearly marked to avoid redundant work?
- [ ] Do titles follow the CTR Proxy (Skill 7) rules?
- [ ] Are pipeline stats consistent (e.g., true_gaps <= pain_points)?
