# GAP Intel Overview

Master guide for GAP Intel YouTube channel analysis tool. Use this when working on any GAP Intel feature, understanding the 7-skill architecture, or implementing the gap analysis pipeline.

## Instructions

When invoked, provide a comprehensive overview of:

1. **What GAP Intel Does**: YouTube content gap analysis tool that identifies opportunities for creators
2. **The 7-Skill Architecture**:
   - Skill 1: Engagement Quality Analysis (CVR, Question Density, Sentiment)
   - Skill 2: Content Landscape Mapping (Topic Coverage, Saturation)
   - Skill 3: Demand Signal Extraction (Question Frequency, Opportunity Score)
   - Skill 4: Viewer Satisfaction Signals (Satisfaction Index, Clarity Score)
   - Skill 5: Metadata & SEO Analysis (Title Effectiveness, SEO Strength)
   - Skill 6: Growth Pattern Analysis (Series Effectiveness, Consistency)
   - Skill 7: CTR Proxy Analysis (Hook Strength, Title Correlation)

3. **Gap Formula**:
   ```
   Gap Score = (Demand Signals x Competitor Gap) / (Existing Content Coverage)
   ```

4. **Key Files**:
   - `railway-api/GAP_ULTIMATE.py` - Primary analysis engine
   - `railway-api/server.py` - FastAPI server
   - `railway-api/premium/` - Core 7-skill logic
   - `gap-intel-website/` - Next.js frontend

5. **Quality Gates**:
   - Minimum 50 comments for reliable analysis
   - Minimum 20 videos for pattern recognition
   - Confidence threshold: >65% for each skill output

Reference the detailed skill files in `.agent/skills/` for implementation specifics.
