#!/usr/bin/env python3
"""
Vision Analyzer - GapIntel v2 Module 1

Analyzes YouTube thumbnails to extract visual patterns and correlate with performance.
Uses OpenCV and PIL for local processing (no API costs).

Features:
- Dominant color extraction
- Face detection
- Text density estimation
- Brightness/contrast analysis
- Performance correlation

Usage:
    from vision_analyzer import analyze_channel_thumbnails
    results = analyze_channel_thumbnails(youtube, channel_id, num_videos=50)
"""

import os
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from pathlib import Path
from collections import Counter
import requests
from typing import Optional
import colorsys

# Try to import optional face detection
try:
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    FACE_DETECTION_AVAILABLE = True
except:
    FACE_DETECTION_AVAILABLE = False
    print("⚠️ Face detection not available (missing cascade file)")


def download_thumbnail(video_id: str, quality: str = "maxresdefault") -> Optional[np.ndarray]:
    """
    Download a YouTube thumbnail and return as OpenCV image array.
    
    Args:
        video_id: YouTube video ID
        quality: Thumbnail quality (maxresdefault, hqdefault, mqdefault, default)
    
    Returns:
        OpenCV image array (BGR) or None if failed
    """
    qualities = [quality, "hqdefault", "mqdefault", "default"]
    
    for q in qualities:
        url = f"https://i.ytimg.com/vi/{video_id}/{q}.jpg"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200 and len(response.content) > 1000:
                img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                if img is not None:
                    return img
        except Exception as e:
            continue
    
    return None


def extract_dominant_colors(img: np.ndarray, num_colors: int = 5) -> list[dict]:
    """
    Extract dominant colors from an image using k-means clustering.
    
    Returns:
        List of dicts with hex, rgb, percentage, and color_name
    """
    # Resize for faster processing
    img_small = cv2.resize(img, (150, 150))
    img_rgb = cv2.cvtColor(img_small, cv2.COLOR_BGR2RGB)
    
    # Reshape to list of pixels
    pixels = img_rgb.reshape(-1, 3).astype(np.float32)
    
    # K-means clustering
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixels, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    
    # Count occurrences
    label_counts = Counter(labels.flatten())
    total_pixels = len(labels)
    
    colors = []
    for i, center in enumerate(centers):
        r, g, b = int(center[0]), int(center[1]), int(center[2])
        hex_code = f"#{r:02x}{g:02x}{b:02x}"
        percentage = (label_counts[i] / total_pixels) * 100
        
        colors.append({
            "hex": hex_code,
            "rgb": (r, g, b),
            "percentage": round(percentage, 1),
            "color_name": classify_color(r, g, b),
            "saturation": get_saturation(r, g, b)
        })
    
    # Sort by percentage
    colors.sort(key=lambda x: x["percentage"], reverse=True)
    return colors


def classify_color(r: int, g: int, b: int) -> str:
    """Classify RGB color into named category."""
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    h = h * 360
    s = s * 100
    v = v * 100
    
    if v < 20:
        return "black"
    elif s < 15 and v > 80:
        return "white"
    elif s < 15:
        return "gray"
    elif h < 15 or h >= 345:
        return "red"
    elif h < 45:
        return "orange"
    elif h < 70:
        return "yellow"
    elif h < 150:
        return "green"
    elif h < 200:
        return "cyan"
    elif h < 260:
        return "blue"
    elif h < 290:
        return "purple"
    else:
        return "pink"


def get_saturation(r: int, g: int, b: int) -> float:
    """Get saturation value (0-100)."""
    _, s, _ = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    return round(s * 100, 1)


def detect_faces(img: np.ndarray) -> dict:
    """
    Detect faces in the image.
    
    Returns:
        Dict with face_count, face_area_percentage, face_positions
    """
    if not FACE_DETECTION_AVAILABLE:
        return {"face_count": 0, "face_area_percentage": 0, "positions": [], "available": False}
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    img_area = img.shape[0] * img.shape[1]
    total_face_area = sum(w * h for (x, y, w, h) in faces)
    
    positions = []
    for (x, y, w, h) in faces:
        cx, cy = x + w//2, y + h//2
        # Classify position (left, center, right)
        if cx < img.shape[1] * 0.33:
            pos = "left"
        elif cx > img.shape[1] * 0.66:
            pos = "right"
        else:
            pos = "center"
        positions.append(pos)
    
    return {
        "face_count": len(faces),
        "face_area_percentage": round((total_face_area / img_area) * 100, 1),
        "positions": positions,
        "available": True
    }


def analyze_brightness_contrast(img: np.ndarray) -> dict:
    """
    Analyze image brightness and contrast.
    
    Returns:
        Dict with brightness (0-255), contrast (0-100), is_dark, is_high_contrast
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    brightness = np.mean(gray)
    contrast = np.std(gray)
    
    return {
        "brightness": round(brightness, 1),
        "contrast": round(contrast, 1),
        "is_dark": brightness < 100,
        "is_high_contrast": contrast > 60,
        "brightness_category": "dark" if brightness < 85 else ("bright" if brightness > 170 else "medium")
    }


def estimate_text_density(img: np.ndarray) -> dict:
    """
    Estimate text presence using edge detection heuristics.
    (Full OCR would require pytesseract, this is a lightweight alternative)
    
    Returns:
        Dict with text_density_score (0-100), has_significant_text
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Edge detection
    edges = cv2.Canny(gray, 50, 150)
    
    # Calculate edge density
    edge_density = (np.count_nonzero(edges) / edges.size) * 100
    
    # Text typically creates horizontal edge patterns
    # Detect horizontal lines which often indicate text
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
    detect_horizontal = cv2.morphologyEx(edges, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    horizontal_density = (np.count_nonzero(detect_horizontal) / detect_horizontal.size) * 100
    
    # Normalize to 0-100 score
    text_score = min(100, (edge_density * 0.5 + horizontal_density * 10))
    
    return {
        "text_density_score": round(text_score, 1),
        "has_significant_text": text_score > 15,
        "edge_density": round(edge_density, 1)
    }


def analyze_thumbnail(video_id: str) -> Optional[dict]:
    """
    Full analysis of a single thumbnail.
    
    Args:
        video_id: YouTube video ID
    
    Returns:
        Dict with all visual analysis results, or None if download failed
    """
    img = download_thumbnail(video_id)
    if img is None:
        return None
    
    colors = extract_dominant_colors(img)
    faces = detect_faces(img)
    brightness = analyze_brightness_contrast(img)
    text = estimate_text_density(img)
    
    # Calculate high-saturation color percentage
    high_sat_colors = [c for c in colors if c["saturation"] > 50]
    high_sat_percentage = sum(c["percentage"] for c in high_sat_colors)
    
    return {
        "video_id": video_id,
        "dominant_colors": colors,
        "primary_color": colors[0]["color_name"] if colors else "unknown",
        "primary_hex": colors[0]["hex"] if colors else "#000000",
        "high_saturation_percentage": round(high_sat_percentage, 1),
        "faces": faces,
        "brightness": brightness,
        "text": text,
        "visual_style": classify_visual_style(colors, brightness, faces, text)
    }


def classify_visual_style(colors: list, brightness: dict, faces: dict, text: dict) -> str:
    """Classify the overall visual style of the thumbnail."""
    styles = []
    
    # Color-based styles
    primary_color = colors[0]["color_name"] if colors else "unknown"
    high_sat = sum(c["percentage"] for c in colors if c["saturation"] > 50) > 40
    
    if high_sat:
        styles.append("vibrant")
    if brightness["is_dark"]:
        styles.append("dark")
    if brightness["is_high_contrast"]:
        styles.append("high-contrast")
    if faces["face_count"] > 0:
        styles.append("face-forward")
    if text["has_significant_text"]:
        styles.append("text-heavy")
    if primary_color in ["red", "orange", "yellow"]:
        styles.append("warm-tones")
    elif primary_color in ["blue", "cyan", "purple"]:
        styles.append("cool-tones")
    
    return ", ".join(styles) if styles else "neutral"


def analyze_channel_thumbnails(youtube, channel_id: str, num_videos: int = 50) -> dict:
    """
    Analyze thumbnails for a channel's recent videos and correlate with view counts.
    
    Args:
        youtube: YouTube API client
        channel_id: Channel ID
        num_videos: Number of videos to analyze
    
    Returns:
        Dict with thumbnail_analyses, performance_correlations, winning_patterns
    """
    print(f"\n🎨 VISION ANALYZER: Analyzing {num_videos} thumbnails...")
    
    # Get uploads playlist
    ch_response = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    ).execute()
    
    uploads_id = ch_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    
    # Fetch videos
    videos = []
    next_page = None
    
    while len(videos) < num_videos:
        pl_response = youtube.playlistItems().list(
            part="snippet",
            playlistId=uploads_id,
            maxResults=min(50, num_videos - len(videos)),
            pageToken=next_page
        ).execute()
        
        video_ids = [item["snippet"]["resourceId"]["videoId"] for item in pl_response["items"]]
        
        # Get view counts
        stats_response = youtube.videos().list(
            part="statistics,contentDetails",
            id=",".join(video_ids)
        ).execute()
        
        stats_map = {v["id"]: int(v["statistics"].get("viewCount", 0)) for v in stats_response["items"]}
        
        for item in pl_response["items"]:
            vid = item["snippet"]["resourceId"]["videoId"]
            videos.append({
                "video_id": vid,
                "title": item["snippet"]["title"],
                "views": stats_map.get(vid, 0)
            })
        
        next_page = pl_response.get("nextPageToken")
        if not next_page:
            break
    
    # Analyze thumbnails
    analyses = []
    for i, video in enumerate(videos[:num_videos]):
        print(f"   📸 [{i+1}/{num_videos}] Analyzing: {video['title'][:40]}...")
        analysis = analyze_thumbnail(video["video_id"])
        if analysis:
            analysis["views"] = video["views"]
            analysis["title"] = video["title"]
            analyses.append(analysis)
    
    # Calculate performance correlations
    correlations = calculate_performance_correlations(analyses)
    
    # Find winning patterns
    winning_patterns = find_winning_patterns(analyses, correlations)
    
    print(f"   ✓ Analyzed {len(analyses)} thumbnails")
    
    return {
        "thumbnail_analyses": analyses,
        "performance_correlations": correlations,
        "winning_patterns": winning_patterns,
        "total_analyzed": len(analyses)
    }


def calculate_performance_correlations(analyses: list) -> dict:
    """
    Calculate correlations between visual features and view performance.
    """
    if len(analyses) < 5:
        return {"error": "Not enough data for correlations"}
    
    avg_views = np.mean([a["views"] for a in analyses])
    
    # Group by visual features
    correlations = {
        "by_primary_color": {},
        "by_brightness": {},
        "by_face_count": {},
        "by_text_presence": {},
        "by_saturation": {}
    }
    
    # Color correlations
    color_groups = {}
    for a in analyses:
        color = a["primary_color"]
        if color not in color_groups:
            color_groups[color] = []
        color_groups[color].append(a["views"])
    
    for color, views in color_groups.items():
        if len(views) >= 2:
            avg = np.mean(views)
            correlations["by_primary_color"][color] = {
                "avg_views": int(avg),
                "vs_channel_avg": round(((avg - avg_views) / avg_views) * 100, 1),
                "sample_size": len(views)
            }
    
    # Brightness correlations
    for category in ["dark", "medium", "bright"]:
        views = [a["views"] for a in analyses if a["brightness"]["brightness_category"] == category]
        if len(views) >= 2:
            avg = np.mean(views)
            correlations["by_brightness"][category] = {
                "avg_views": int(avg),
                "vs_channel_avg": round(((avg - avg_views) / avg_views) * 100, 1),
                "sample_size": len(views)
            }
    
    # Face correlations
    for fc in [0, 1, 2]:
        views = [a["views"] for a in analyses if a["faces"]["face_count"] == fc]
        if len(views) >= 2:
            avg = np.mean(views)
            correlations["by_face_count"][str(fc)] = {
                "avg_views": int(avg),
                "vs_channel_avg": round(((avg - avg_views) / avg_views) * 100, 1),
                "sample_size": len(views)
            }
    
    # Text presence
    for has_text in [True, False]:
        views = [a["views"] for a in analyses if a["text"]["has_significant_text"] == has_text]
        if len(views) >= 2:
            avg = np.mean(views)
            label = "with_text" if has_text else "no_text"
            correlations["by_text_presence"][label] = {
                "avg_views": int(avg),
                "vs_channel_avg": round(((avg - avg_views) / avg_views) * 100, 1),
                "sample_size": len(views)
            }
    
    # High saturation
    high_sat = [a for a in analyses if a["high_saturation_percentage"] > 40]
    low_sat = [a for a in analyses if a["high_saturation_percentage"] <= 40]
    
    if len(high_sat) >= 2:
        avg = np.mean([a["views"] for a in high_sat])
        correlations["by_saturation"]["high"] = {
            "avg_views": int(avg),
            "vs_channel_avg": round(((avg - avg_views) / avg_views) * 100, 1),
            "sample_size": len(high_sat)
        }
    
    if len(low_sat) >= 2:
        avg = np.mean([a["views"] for a in low_sat])
        correlations["by_saturation"]["low"] = {
            "avg_views": int(avg),
            "vs_channel_avg": round(((avg - avg_views) / avg_views) * 100, 1),
            "sample_size": len(low_sat)
        }
    
    correlations["channel_avg_views"] = int(avg_views)
    
    return correlations


def find_winning_patterns(analyses: list, correlations: dict) -> list:
    """
    Identify the top-performing visual patterns.
    """
    patterns = []
    
    # Find best color
    color_data = correlations.get("by_primary_color", {})
    if color_data:
        best_color = max(color_data.items(), key=lambda x: x[1].get("vs_channel_avg", 0))
        if best_color[1]["vs_channel_avg"] > 10:
            patterns.append({
                "type": "color",
                "finding": f"{best_color[0].capitalize()} thumbnails",
                "impact": f"+{best_color[1]['vs_channel_avg']}% vs average",
                "recommendation": f"Use {best_color[0]} as the dominant color"
            })
    
    # Find best brightness
    brightness_data = correlations.get("by_brightness", {})
    if brightness_data:
        best_brightness = max(brightness_data.items(), key=lambda x: x[1].get("vs_channel_avg", 0))
        if best_brightness[1]["vs_channel_avg"] > 10:
            patterns.append({
                "type": "brightness",
                "finding": f"{best_brightness[0].capitalize()} backgrounds",
                "impact": f"+{best_brightness[1]['vs_channel_avg']}% vs average",
                "recommendation": f"Use {best_brightness[0]} background tones"
            })
    
    # Face presence
    face_data = correlations.get("by_face_count", {})
    if face_data:
        best_faces = max(face_data.items(), key=lambda x: x[1].get("vs_channel_avg", 0))
        if best_faces[1]["vs_channel_avg"] > 10:
            face_text = "with a face" if best_faces[0] != "0" else "without faces"
            patterns.append({
                "type": "faces",
                "finding": f"Thumbnails {face_text}",
                "impact": f"+{best_faces[1]['vs_channel_avg']}% vs average",
                "recommendation": f"Include {best_faces[0]} face(s) in thumbnails"
            })
    
    # Text presence
    text_data = correlations.get("by_text_presence", {})
    if text_data:
        best_text = max(text_data.items(), key=lambda x: x[1].get("vs_channel_avg", 0))
        if best_text[1]["vs_channel_avg"] > 10:
            patterns.append({
                "type": "text",
                "finding": f"Thumbnails {best_text[0].replace('_', ' ')}",
                "impact": f"+{best_text[1]['vs_channel_avg']}% vs average",
                "recommendation": "Add text overlays to thumbnails" if "with" in best_text[0] else "Keep thumbnails clean without text"
            })
    
    # Saturation
    sat_data = correlations.get("by_saturation", {})
    if sat_data:
        best_sat = max(sat_data.items(), key=lambda x: x[1].get("vs_channel_avg", 0))
        if best_sat[1]["vs_channel_avg"] > 10:
            patterns.append({
                "type": "saturation",
                "finding": f"{best_sat[0].capitalize()} saturation colors",
                "impact": f"+{best_sat[1]['vs_channel_avg']}% vs average",
                "recommendation": f"Use {best_sat[0]}-saturation, vibrant colors" if best_sat[0] == "high" else "Use muted, desaturated colors"
            })
    
    return patterns


def generate_thumbnail_recommendation(winning_patterns: list, topic: str) -> str:
    """
    Generate a specific thumbnail recommendation based on winning patterns.
    """
    if not winning_patterns:
        return "Use a clean, high-contrast thumbnail with your face visible"
    
    elements = []
    
    for pattern in winning_patterns:
        if pattern["type"] == "color":
            elements.append(pattern["recommendation"])
        elif pattern["type"] == "brightness":
            elements.append(pattern["recommendation"])
        elif pattern["type"] == "faces":
            elements.append(pattern["recommendation"])
        elif pattern["type"] == "saturation":
            elements.append(pattern["recommendation"])
    
    recommendation = f"For '{topic}': " + "; ".join(elements)
    
    # Add impact summary
    total_impact = sum(float(p["impact"].replace("%", "").replace("+", "").split()[0]) for p in winning_patterns if "%" in p["impact"])
    if total_impact > 0:
        recommendation += f". This visual style has shown +{total_impact:.0f}% combined performance uplift."
    
    return recommendation


if __name__ == "__main__":
    # Test with a sample video
    print("Testing Vision Analyzer...")
    result = analyze_thumbnail("dQw4w9WgXcQ")  # Rick Astley for testing
    if result:
        print(f"✓ Primary color: {result['primary_color']}")
        print(f"✓ Visual style: {result['visual_style']}")
        print(f"✓ Face count: {result['faces']['face_count']}")
        print(f"✓ Brightness: {result['brightness']['brightness_category']}")
    else:
        print("✗ Failed to analyze thumbnail")
