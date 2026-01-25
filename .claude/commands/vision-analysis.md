# Vision Analysis (Thumbnails)

Analyze video thumbnails using Computer Vision to identify winning visual patterns.

## Instructions

When working on thumbnail analysis features:

1. **Dominant Color & Saturation**:
   - Use K-Means clustering to find top 5 colors
   - Vibrant: High saturation (>50%)
   - Dark/Bright: Based on luminance values

2. **Face Detection**:
   - Use OpenCV Haar Cascades
   - Track: Face Count (0, 1, 2+), Face Area %, Position (L/R/Center)

3. **Text Density**:
   - Horizontal Edge Density = Strong text indicator
   - Canny Edge Detection for general complexity

4. **Correlation Engine**:
   - Compare visual features against views vs channel_average
   - Example: "Red thumbnails get +40% more views than Blue"

5. **Winning Pattern Logic**:
   ```
   Pattern is "Winning" if:
   Avg_Views(Pattern) > Channel_Avg_Views * 1.10 (10% uplift)
   ```

6. **Common Winning Patterns**:
   - Face-Forward: Single large face on right side
   - High-Contrast: Bright text on dark background
   - Vibrant: High saturation (Red/Yellow)
   - Minimalist: Low text density, single focal point

7. **Output Format**:
   ```json
   {
     "thumbnail_analysis": {
       "total_analyzed": 50,
       "winning_patterns": [
         {"type": "faces", "finding": "1 face", "impact": "+45%"},
         {"type": "color", "finding": "Yellow dominant", "impact": "+22%"}
       ]
     },
     "visual_style": "vibrant, face-forward, text-heavy"
   }
   ```
