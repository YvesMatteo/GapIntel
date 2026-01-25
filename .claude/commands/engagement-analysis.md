# Engagement Quality Analysis (Skill 1)

Analyze comment depth and quality to identify engagement patterns and pain points.

## Instructions

When working on engagement analysis features:

1. **Core Metrics to Implement**:
   - **CVR** (Comment-to-View Ratio): `(Total Comments / Total Views) x 100`
     - Educational: 1-2% baseline, 3-5% exceptional
     - Tutorials: 0.5-1% baseline
   - **Question Density**: `(Question Comments / Total Comments) x 100`
     - High-quality: 30-40% questions
   - **Comment Depth Score**: `Reply_Comments / Top_Level_Comments`
     - Score > 0.5 = Deep engagement
   - **Repeat Engagement**: `(Commenters in 2+ videos / Unique Commenters) x 100`
     - Score > 20% = Loyal audience

2. **Sentiment Classification**:
   - Positive: "thank", "help", "great", "love", "perfect"
   - Confusion: "don't understand", "confused", "stuck"
   - Implementation: "tried", "worked for me", "applied"
   - Inquiry: Contains "?", "how", "what", "why"
   - Negative: "don't", "hate", "fail", "wrong"

3. **Pain Point Extraction**:
   - Look for: "I don't understand", "Didn't work for me", "How do I apply this to..."
   - Problem in 10+ comments = Content gap indicator
   - Problem in 20+ comments = Strong gap signal

4. **Output feeds into**: Skill 3 (Demand Signals), Skill 4 (Satisfaction), Gap scoring
