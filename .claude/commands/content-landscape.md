# Content Landscape Mapping (Skill 2)

Map existing channel content to identify true gaps vs under-explained topics.

## Instructions

When working on content landscape features:

1. **Core Metrics**:
   - **Topic Coverage Index**: `(Topics Covered / Total Possible Topics) x 100`
     - >80%: Comprehensive, 60-80%: Good, <40%: Narrow focus
   - **Topic Saturation Score**: `Videos_Per_Topic / Avg_Videos_Per_Topic`
     - >2.0: Over-covered, 0.3-0.8: Under-covered, <0.3: Gap candidate
   - **Format Diversity**: Track Tutorial, Review, Educational, Vlog, Interview, etc.
     - 5+ formats = Diverse, 1-2 = Limited range
   - **Upload Consistency**: Coefficient of variation in upload intervals
     - CV < 0.2 = Highly consistent (156% higher growth)
   - **Content Freshness**: `(Videos Last 90 Days / Total Videos) x 100`

2. **Topic Extraction Techniques**:
   - Parse video titles for main topics using NLP
   - Extract keywords from descriptions
   - Use video tags for categorization
   - Cluster similar topics semantically

3. **Gap Identification**:
   ```
   Gap = Skill 3 (Demand) vs Skill 2 (Supply)
   High Demand + Low Supply = TRUE GAP
   ```

4. **Minimum Requirements**:
   - 20+ videos for pattern recognition
   - 85%+ topic extraction accuracy
