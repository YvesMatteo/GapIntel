# Gap Report Generation

Synthesize analytical data into the final GAP Report with verified opportunities.

## Instructions

When generating gap reports:

1. **Core Logic**:
   ```
   Verified Gap = (High Demand Signal) AND (No Transcript Evidence)
   ```
   - TRUE_GAP: Not found in transcripts
   - UNDER_EXPLAINED: Found but brief/unclear
   - SATURATED: Found and detailed

2. **Opportunity Scoring Algorithm**:
   ```python
   Overall_Score = (
       (Gap_Severity * 0.4) +       # TRUE_GAP=100, UNDER_EXPLAINED=60
       (Trend_Score * 0.3) +        # Google Trends (0-100)
       (Comment_Engagement * 0.2) + # Normalized engagement
       (Competitor_Opp * 0.1)       # Do competitors miss this too?
   )
   ```

3. **Report Structure**:
   1. Header: Channel Name + Date
   2. Pipeline Stats: Raw -> High Signal -> Pain Points -> Verified Gaps
   3. #1 Top Opportunity: The "Hero" recommendation
   4. Verified Gaps (Actionable): True/Under-explained with evidence
   5. Already Covered: What NOT to make (Saturated)
   6. Videos Analyzed: Reference list
   7. Competitors: Who was benchmarked

4. **JSON Schema**:
   ```json
   {
     "pipeline_stats": { "raw_comments", "high_signal", "pain_points", "true_gaps" },
     "top_opportunity": { "topic_keyword", "best_title", "reason" },
     "opportunities": [{ "topic_keyword", "gap_status", "influence_scores", "viral_titles" }]
   }
   ```

5. **Validation**: Top opportunity must have TRUE_GAP status
