# Demand Signal Extraction (Skill 3)

Extract high-demand topics from public signals without watch time data.

## Instructions

When working on demand signal features:

1. **Core Metrics**:
   - **Question Frequency Score (QFS)**: `(Topic_Mentions / Total_Comments) x 100`
     - >5%: High demand, 2-5%: Moderate, <0.5%: Minimal
   - **Demand Confidence Score**: Weighted signals validation
     - questions_in_comments: 1.0x
     - same_question_multiple_videos: 1.5x
     - competitor_high_engagement: 1.5x
     - search_volume_confirmed: 2.0x
   - **Opportunity Score**: `(Demand_Strength x Competitor_Gap x Audience_Interest) / 3`
     - 8-10: Huge opportunity, 6-8: Good, <2: Not worth pursuing

2. **Pain Point Severity**: `(Frequency x Emotional_Intensity x Recency) / 1000`
   - Pain Types: procedural, technical, understanding, resource, context

3. **Question Type Categories**:
   | Type | Example | Content Needed |
   |------|---------|----------------|
   | "How do I...?" | Procedural gap | Tutorial |
   | "Why does...?" | Understanding gap | Explainer |
   | "X vs Y?" | Comparison gap | Comparison |
   | "Is it possible...?" | Advanced gap | Advanced tutorial |

4. **Integration**: This provides the DEMAND side of gap scoring
   - Gap = Skill 3 (Demand) vs Skill 2 (Supply)

5. **Minimum**: 100+ comments for demand analysis
