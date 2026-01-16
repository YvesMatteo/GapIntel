---
name: vision-analysis
description: Skill for thumbnail visual analysis. Use to extract dominant colors, detect faces, analyze text density, and find winning visual patterns.
---

# Vision Analysis (Thumbnails)

Analyzes video thumbnails using Computer Vision (OpenCV/PIL) to identify visual patterns that correlate with high performance (views).

## When to Use This Skill

- Analyzing thumbnail composition (Faces, Text, Brightness)
- Extracting color palettes and dominant hex codes
- Correlating visual features with view counts
- Generating specific design recommendations
- Checking "Face-Forward" vs. "Text-Heavy" styles

## Core Analysis Features (`vision_analyzer.py`)

### 1. Dominant Color & Saturation
Uses K-Means clustering to find the top 5 colors.
*   **Vibrant**: High saturation (>50%)
*   **Dark/Bright**: Based on luminance values

### 2. Face Detection
Uses OpenCV Haar Cascades to detect:
*   Face Count (0, 1, 2+)
*   Face Area % (How big is the face?)
*   Position (Left/Right/Center)

### 3. Text Density
Heuristic edge detection to guess if text is present:
*   **Horizontal Edge Density**: Strong indicator of text
*   **Canny Edge Detection**: General complexity

### 4. Correlation Engine
Compares visual features against `views` vs `channel_average`.
*   *Example*: "Red thumbnails get +40% more views than Blue ones on this channel."

## Implementation Reference

```python
def analyze_thumbnail(video_id):
    """
    Downloads thumb, runs CV pipelines.
    Returns: colors, face_count, brightness, text_score
    """
```

```python
def find_winning_patterns(analyses, correlations):
    """
    Identifies features with >10% uplift vs channel average.
    """
```

## Winning Pattern Logic

A pattern is "Winning" if:
`Avg_Views(Pattern) > Channel_Avg_Views * 1.10` (10% uplift)

**Common Winning Patterns:**
1.  **Face-Forward**: Single large face on right side
2.  **High-Contrast**: Bright text on dark background
3.  **Vibrant**: High saturation primary colors (Red/Yellow)
4.  **Minimalist**: Low text density, single focal point

## Output Format

```json
{
  "thumbnail_analysis": {
    "total_analyzed": 50,
    "winning_patterns": [
      {
        "type": "faces",
        "finding": "Thumbnails with 1 face",
        "impact": "+45% vs average",
        "recommendation": "Always include a single face"
      },
      {
        "type": "color",
        "finding": "Yellow dominant color",
        "impact": "+22% vs average",
        "recommendation": "Use Yellow background/accents"
      }
    ]
  },
  "visual_style": "vibrant, face-forward, text-heavy"
}
```

## Validation Checklist

- [ ] Is Face Detection available (Haar cascades loaded)?
- [ ] Are images resized (e.g., to 150px) for fast K-Means?
- [ ] Do correlations require min sample size (e.g., 5 videos)?
- [ ] Is text density normalized (0-100)?
