"""
Thumbnail Analyzer using Gemini AI Vision
Uses gemini-2.0-flash for cost-effective, accurate thumbnail analysis.
"""

import json
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class ThumbnailAnalysis:
    """Results from AI thumbnail analysis."""
    has_face: bool = False
    face_count: int = 0
    face_is_large: bool = False
    has_eye_contact: bool = False
    face_expression: str = ""
    
    has_text: bool = False
    text_content: str = ""
    word_count: int = 0
    text_is_readable: bool = False
    
    has_bright_colors: bool = False
    has_high_contrast: bool = False
    dominant_colors: List[str] = None
    
    issues: List[Dict] = None
    strengths: List[str] = None
    
    overall_score: int = 0
    predicted_ctr: float = 4.0
    
    def __post_init__(self):
        if self.dominant_colors is None:
            self.dominant_colors = []
        if self.issues is None:
            self.issues = []
        if self.strengths is None:
            self.strengths = []
    
    def to_dict(self) -> Dict:
        return asdict(self)


def analyze_thumbnail_with_gemini(
    thumbnail_url: str,
    video_title: str,
    ai_client,
    model: str = "gemini-2.0-flash"
) -> ThumbnailAnalysis:
    """
    Analyze a YouTube thumbnail using Gemini Vision.
    
    Args:
        thumbnail_url: URL of the thumbnail image
        video_title: Title of the video (for context)
        ai_client: Gemini client instance
        model: Gemini model to use (default: gemini-2.0-flash for cost)
    
    Returns:
        ThumbnailAnalysis with detected features and issues
    """
    
    prompt = f"""Analyze this YouTube thumbnail for the video titled: "{video_title}"

Return a JSON object with these exact fields:
{{
    "has_face": true/false (is there a human face visible?),
    "face_count": number (how many faces),
    "face_is_large": true/false (does face take up >15% of image?),
    "has_eye_contact": true/false (is face looking at camera?),
    "face_expression": "neutral/happy/surprised/excited/serious/none",
    
    "has_text": true/false (is there text overlay on the image?),
    "text_content": "the text you can read" or "",
    "word_count": number (words in text overlay),
    "text_is_readable": true/false (would text be readable on mobile?),
    
    "has_bright_colors": true/false,
    "has_high_contrast": true/false (good subject/background separation),
    "dominant_colors": ["color1", "color2"],
    
    "issues": [
        {{"issue": "description", "severity": "high/medium/low", "fix": "how to fix"}}
    ],
    "strengths": ["strength1", "strength2"],
    
    "overall_score": 1-100 (thumbnail quality score),
    "predicted_ctr": 1.0-12.0 (estimated click-through rate %)
}}

Be accurate and specific. Only report issues that actually exist in this thumbnail.
Return ONLY the JSON object, no other text."""

    try:
        # Download image for Gemini
        response = requests.get(thumbnail_url, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ Failed to download thumbnail: {response.status_code}")
            return ThumbnailAnalysis()
        
        import base64
        image_data = base64.b64encode(response.content).decode('utf-8')
        
        # Call Gemini with image
        gemini_model = ai_client.GenerativeModel(model)
        
        gemini_response = gemini_model.generate_content([
            prompt,
            {
                "mime_type": "image/jpeg",
                "data": image_data
            }
        ])
        
        # Parse response
        response_text = gemini_response.text.strip()
        
        # Clean up response if wrapped in markdown
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        data = json.loads(response_text)
        
        return ThumbnailAnalysis(
            has_face=data.get("has_face", False),
            face_count=data.get("face_count", 0),
            face_is_large=data.get("face_is_large", False),
            has_eye_contact=data.get("has_eye_contact", False),
            face_expression=data.get("face_expression", ""),
            has_text=data.get("has_text", False),
            text_content=data.get("text_content", ""),
            word_count=data.get("word_count", 0),
            text_is_readable=data.get("text_is_readable", False),
            has_bright_colors=data.get("has_bright_colors", False),
            has_high_contrast=data.get("has_high_contrast", False),
            dominant_colors=data.get("dominant_colors", []),
            issues=data.get("issues", []),
            strengths=data.get("strengths", []),
            overall_score=data.get("overall_score", 50),
            predicted_ctr=data.get("predicted_ctr", 4.0)
        )
        
    except json.JSONDecodeError as e:
        print(f"⚠️ Failed to parse Gemini response: {e}")
        return ThumbnailAnalysis()
    except Exception as e:
        print(f"⚠️ Thumbnail analysis failed: {e}")
        return ThumbnailAnalysis()


def analyze_thumbnails_batch(
    videos: List[Dict],
    ai_client,
    model: str = "gemini-2.0-flash",
    max_videos: int = 5
) -> List[Dict]:
    """
    Analyze multiple thumbnails and return formatted results.
    
    Args:
        videos: List of video dicts with 'title' and 'thumbnail_url' or 'video_id'
        ai_client: Gemini client
        model: Gemini model to use
        max_videos: Maximum videos to analyze (cost control)
    
    Returns:
        List of analysis results formatted for frontend
    """
    results = []
    
    for video in videos[:max_videos]:
        video_info = video.get('video_info', video)
        title = video_info.get('title', 'Unknown')
        video_id = video_info.get('video_id', '')
        
        # Get thumbnail URL
        thumbnail_url = video_info.get('thumbnail_url') or \
                       f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        
        print(f"   🖼️ Analyzing: {title[:50]}...")
        
        analysis = analyze_thumbnail_with_gemini(
            thumbnail_url=thumbnail_url,
            video_title=title,
            ai_client=ai_client,
            model=model
        )
        
        # Format for frontend
        formatted_issues = []
        for issue in analysis.issues:
            formatted_issues.append({
                "issue": issue.get("issue", "Unknown issue"),
                "severity": issue.get("severity", "medium"),
                "fix": issue.get("fix", "Review thumbnail")
            })
        
        # Calculate potential improvement
        if analysis.overall_score < 50:
            potential = "+50%"
        elif analysis.overall_score < 70:
            potential = "+30%"
        elif analysis.overall_score < 85:
            potential = "+15%"
        else:
            potential = "+5%"
        
        results.append({
            "video_title": title,
            "predicted_ctr": round(analysis.predicted_ctr, 1),
            "potential_improvement": potential,
            "score_breakdown": {
                "face_impact": 90 if analysis.face_is_large else (60 if analysis.has_face else 20),
                "text_readability": 80 if analysis.text_is_readable else (50 if analysis.has_text else 30),
                "color_contrast": 80 if analysis.has_high_contrast else 40,
                "overall": analysis.overall_score
            },
            "issues": formatted_issues,
            "strengths": analysis.strengths,
            "ab_test_suggestions": []  # Can add later
        })
    
    return results


# Quick test
if __name__ == "__main__":
    print("🧪 Thumbnail Analyzer AI - requires Gemini client to test")
