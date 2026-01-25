# CTR Proxy Analysis (Skill 7)

Infer title and thumbnail effectiveness without direct CTR access.

## Instructions

When working on CTR proxy features:

1. **Title Hook Strength Score (THSS)**:
   ```python
   HOOK_SCORES = {
       'number': 10,      # "7 Ways to..." - 3x better CTR
       'question': 8,     # "Why YouTube Won't..." - 2x better
       'how_to': 7,       # "How to Grow..." - 1.8x better
       'comparison': 6,   # "X vs Y" - 1.5x better
       'authority': 5,    # "Ultimate Guide to..."
       'standard': 3      # No hook
   }
   ```

2. **Title-to-Engagement Correlation (TEC)**:
   - Categorize all titles by hook type
   - Calculate average engagement per category
   - Identify underutilized high-performing patterns

3. **Title Structure Effectiveness**:
   - Keyword Position 1-5 words: +10
   - Length 50-60 chars: +10 (optimal for mobile + desktop)
   - Clear, readable: +10

4. **Description First-Line Impact**:
   - First 150 chars must: State benefit, include keyword, create curiosity

5. **Competitive Title Analysis**:
   - Compare your patterns to top performers
   - Identify gaps: "You use 25% number hooks, competitors use 70%"

6. **CTR Improvement Patterns**:
   | Pattern | Formula | CTR Boost |
   |---------|---------|-----------|
   | Number List | "[N] [Benefit] [Keyword]" | +35% |
   | How-To | "How to [Action] [Keyword]" | +28% |
   | Question | "[Question]?" | +20% |
   | Comparison | "[X] vs [Y]" | +18% |
