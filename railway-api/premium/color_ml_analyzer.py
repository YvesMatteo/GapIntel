"""
Premium Analysis - Color ML Analyzer
Analyzes thumbnail color patterns to find what colors drive the most views.

Features:
- Extracts dominant colors from thumbnails
- Correlates color palettes with view performance
- Tracks warm/cool, contrast, saturation patterns
- Recommends optimal color palette based on top performers
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from collections import Counter
import colorsys


@dataclass
class ColorProfile:
    """Color analysis for a single thumbnail."""
    video_id: str
    video_title: str
    view_count: int
    dominant_colors: List[Tuple[int, int, int]]  # RGB tuples
    color_temperature: str  # 'warm', 'cool', 'neutral'
    saturation_level: str  # 'high', 'medium', 'low'
    brightness_level: str  # 'bright', 'medium', 'dark'
    contrast_score: float  # 0-1
    color_diversity: int  # Number of distinct colors
    
    def to_dict(self) -> dict:
        return {
            'video_id': self.video_id,
            'video_title': self.video_title,
            'view_count': self.view_count,
            'dominant_colors': [self._rgb_to_hex(c) for c in self.dominant_colors],
            'color_temperature': self.color_temperature,
            'saturation_level': self.saturation_level,
            'brightness_level': self.brightness_level,
            'contrast_score': self.contrast_score,
            'color_diversity': self.color_diversity,
        }
    
    @staticmethod
    def _rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


@dataclass
class ColorInsights:
    """Aggregated color performance insights."""
    total_videos: int
    best_color_temperatures: List[Dict]  # temp -> avg views
    best_saturation_levels: List[Dict]
    top_performing_colors: List[str]  # Hex colors
    color_recommendations: List[str]
    temperature_performance: Dict[str, float]
    saturation_performance: Dict[str, float]
    brightness_performance: Dict[str, float]
    # Enhanced: Video examples for each color category
    video_examples: List[Dict] = None  # [{video_id, title, views, thumbnail_url, colors, temperature}]
    
    def __post_init__(self):
        if self.video_examples is None:
            self.video_examples = []
    
    def to_dict(self) -> dict:
        result = {
            'total_videos': self.total_videos,
            'best_color_temperatures': self.best_color_temperatures,
            'best_saturation_levels': self.best_saturation_levels,
            'top_performing_colors': self.top_performing_colors,
            'color_recommendations': self.color_recommendations,
            'temperature_performance': self.temperature_performance,
            'saturation_performance': self.saturation_performance,
            'brightness_performance': self.brightness_performance,
            'video_examples': self.video_examples or [],
        }
        # Include comparison data if available
        if hasattr(self, '_comparison'):
            result['comparison'] = self._comparison
        return result


class ColorMLAnalyzer:
    """
    Analyzes thumbnail colors and correlates with view performance.
    
    Usage:
        analyzer = ColorMLAnalyzer()
        profiles = analyzer.analyze_thumbnails(videos_with_features)
        insights = analyzer.generate_insights(profiles)
    """
    
    # Color temperature classification (based on hue)
    WARM_HUES = [(0, 60), (300, 360)]  # Red, orange, yellow, pink/magenta
    COOL_HUES = [(180, 300)]  # Cyan, blue, purple
    
    def __init__(self):
        pass
    
    def classify_temperature(self, rgb: Tuple[int, int, int]) -> str:
        """Classify a color as warm, cool, or neutral."""
        r, g, b = rgb
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        hue = h * 360
        
        # Low saturation = neutral (gray-ish)
        if s < 0.15:
            return 'neutral'
        
        # Check warm hues
        for start, end in self.WARM_HUES:
            if start <= hue <= end:
                return 'warm'
        
        # Check cool hues
        for start, end in self.COOL_HUES:
            if start <= hue <= end:
                return 'cool'
        
        return 'neutral'
    
    def classify_saturation(self, rgb: Tuple[int, int, int]) -> str:
        """Classify saturation level."""
        r, g, b = rgb
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        
        if s > 0.7:
            return 'high'
        elif s > 0.35:
            return 'medium'
        else:
            return 'low'
    
    def classify_brightness(self, rgb: Tuple[int, int, int]) -> str:
        """Classify brightness level."""
        r, g, b = rgb
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        
        if l > 0.65:
            return 'bright'
        elif l > 0.35:
            return 'medium'
        else:
            return 'dark'
    
    def calculate_contrast(self, colors: List[Tuple[int, int, int]]) -> float:
        """Calculate contrast between dominant colors."""
        if len(colors) < 2:
            return 0.0
        
        max_contrast = 0
        for i, c1 in enumerate(colors):
            for c2 in colors[i+1:]:
                # Calculate relative luminance difference
                l1 = (0.299 * c1[0] + 0.587 * c1[1] + 0.114 * c1[2]) / 255
                l2 = (0.299 * c2[0] + 0.587 * c2[1] + 0.114 * c2[2]) / 255
                contrast = abs(l1 - l2)
                max_contrast = max(max_contrast, contrast)
        
        return round(max_contrast, 2)
    
    def analyze_thumbnail_colors(self, video_data: dict, thumbnail_features: dict) -> ColorProfile:
        """
        Analyze colors from extracted thumbnail features.
        
        Args:
            video_data: Dict with video_id, title, view_count
            thumbnail_features: Dict from ThumbnailFeatureExtractor
            
        Returns:
            ColorProfile analysis
        """
        # Extract dominant colors from features
        dominant_colors = []
        for key in ['dominant_color_1', 'dominant_color_2', 'dominant_color_3']:
            if key in thumbnail_features:
                color = thumbnail_features[key]
                if isinstance(color, (list, tuple)) and len(color) == 3:
                    dominant_colors.append(tuple(color))
        
        if not dominant_colors:
            # Default fallback
            dominant_colors = [(128, 128, 128)]
        
        # Classify using first dominant color
        primary_color = dominant_colors[0]
        
        return ColorProfile(
            video_id=video_data.get('video_id', ''),
            video_title=video_data.get('title', ''),
            view_count=video_data.get('view_count', 0),
            dominant_colors=dominant_colors,
            color_temperature=self.classify_temperature(primary_color),
            saturation_level=self.classify_saturation(primary_color),
            brightness_level=self.classify_brightness(primary_color),
            contrast_score=self.calculate_contrast(dominant_colors),
            color_diversity=len(set(dominant_colors)),
        )
    
    def analyze_thumbnails(self, videos_with_features: List[Dict]) -> List[ColorProfile]:
        """
        Analyze colors for multiple videos.
        
        Args:
            videos_with_features: List of dicts with video_data and thumbnail_features
            
        Returns:
            List of ColorProfile
        """
        profiles = []
        for item in videos_with_features:
            video_data = item.get('video_data', item)
            features = item.get('thumbnail_features', {})
            
            profile = self.analyze_thumbnail_colors(video_data, features)
            profiles.append(profile)
        
        return profiles
    
    def generate_insights(self, profiles: List[ColorProfile]) -> ColorInsights:
        """
        Generate aggregated color performance insights.
        Enhanced to compare top 25% vs bottom 25% performers.
        
        Args:
            profiles: List of ColorProfile analyses
            
        Returns:
            ColorInsights with recommendations
        """
        if not profiles:
            return ColorInsights(
                total_videos=0,
                best_color_temperatures=[],
                best_saturation_levels=[],
                top_performing_colors=[],
                color_recommendations=[],
                temperature_performance={},
                saturation_performance={},
                brightness_performance={},
            )
        
        # Sort profiles by view count to compare top vs bottom
        sorted_profiles = sorted(profiles, key=lambda p: p.view_count, reverse=True)
        n = len(sorted_profiles)
        quartile_size = max(1, n // 4)
        
        top_performers = sorted_profiles[:quartile_size]  # Top 25%
        bottom_performers = sorted_profiles[-quartile_size:] if n > 1 else []  # Bottom 25%
        
        # Group by temperature
        temp_views = {'warm': [], 'cool': [], 'neutral': []}
        sat_views = {'high': [], 'medium': [], 'low': []}
        bright_views = {'bright': [], 'medium': [], 'dark': []}
        
        all_colors = []
        color_views = {}  # hex -> [views]
        
        # Track colors for top vs bottom comparison
        top_colors_list = []
        bottom_colors_list = []
        top_temps = []
        bottom_temps = []
        
        for profile in profiles:
            temp_views[profile.color_temperature].append(profile.view_count)
            sat_views[profile.saturation_level].append(profile.view_count)
            bright_views[profile.brightness_level].append(profile.view_count)
            
            for color in profile.dominant_colors:
                hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                all_colors.append(hex_color)
                if hex_color not in color_views:
                    color_views[hex_color] = []
                color_views[hex_color].append(profile.view_count)
        
        # Analyze top performers specifically
        for profile in top_performers:
            top_temps.append(profile.color_temperature)
            for color in profile.dominant_colors:
                hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                top_colors_list.append(hex_color)
        
        # Analyze bottom performers
        for profile in bottom_performers:
            bottom_temps.append(profile.color_temperature)
            for color in profile.dominant_colors:
                hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                bottom_colors_list.append(hex_color)
        
        # Calculate averages
        def avg_views(views_list):
            return sum(views_list) / len(views_list) if views_list else 0
        
        temperature_performance = {k: avg_views(v) for k, v in temp_views.items() if v}
        saturation_performance = {k: avg_views(v) for k, v in sat_views.items() if v}
        brightness_performance = {k: avg_views(v) for k, v in bright_views.items() if v}
        
        # Sort by performance
        best_temps = sorted(
            [{'temperature': k, 'avg_views': v} for k, v in temperature_performance.items()],
            key=lambda x: x['avg_views'], reverse=True
        )
        
        best_sats = sorted(
            [{'saturation': k, 'avg_views': v} for k, v in saturation_performance.items()],
            key=lambda x: x['avg_views'], reverse=True
        )
        
        # Top performing individual colors
        color_avg = {k: avg_views(v) for k, v in color_views.items()}
        top_colors = sorted(color_avg.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Count most common patterns in top vs bottom
        top_temp_counts = Counter(top_temps)
        bottom_temp_counts = Counter(bottom_temps)
        top_color_counts = Counter(top_colors_list)
        bottom_color_counts = Counter(bottom_colors_list)
        
        # Generate recommendations with comparison
        recommendations = []
        
        # Compare temperatures
        if top_temp_counts and bottom_temp_counts:
            winner_temp = top_temp_counts.most_common(1)[0][0] if top_temp_counts else 'neutral'
            loser_temp = bottom_temp_counts.most_common(1)[0][0] if bottom_temp_counts else 'neutral'
            if winner_temp != loser_temp:
                recommendations.append(f"Use {winner_temp} colors - top videos prefer {winner_temp} while underperformers use {loser_temp}")
        elif best_temps:
            recommendations.append(f"Use {best_temps[0]['temperature']} colors - they average {best_temps[0]['avg_views']:,.0f} views")
        
        if best_sats:
            recommendations.append(f"Prefer {best_sats[0]['saturation']} saturation thumbnails")
        
        if top_colors:
            recommendations.append(f"Top color: {top_colors[0][0]} ({top_colors[0][1]:,.0f} avg views)")
            
        # Build video examples (top 3 winners per temperature category)
        video_examples = []
        for temp in ['warm', 'cool', 'neutral']:
            # Find videos with this temp
            temp_profiles = [p for p in profiles if p.color_temperature == temp]
            if not temp_profiles:
                continue
                
            # Sort by views
            temp_profiles.sort(key=lambda p: p.view_count, reverse=True)
            
            # Add top 2
            for p in temp_profiles[:2]:
                video_examples.append({
                    'video_id': p.video_id,
                    'title': p.video_title,
                    'views': p.view_count,
                    'thumbnail_url': f"https://img.youtube.com/vi/{p.video_id}/maxresdefault.jpg",
                    'colors': [self._rgb_to_hex(c) for c in p.dominant_colors[:3]],
                    'temperature': p.color_temperature,
                })
        
        # Add comparison data to the result
        insights = ColorInsights(
            total_videos=len(profiles),
            best_color_temperatures=best_temps,
            best_saturation_levels=best_sats,
            top_performing_colors=[c[0] for c in top_colors],
            color_recommendations=recommendations,
            temperature_performance=temperature_performance,
            saturation_performance=saturation_performance,
            brightness_performance=brightness_performance,
            video_examples=video_examples,
        )
        
        # Add extra comparison data
        insights_dict = insights.to_dict()
        insights_dict['comparison'] = {
            'top_25_percent': {
                'count': len(top_performers),
                'avg_views': avg_views([p.view_count for p in top_performers]),
                'dominant_temperatures': dict(top_temp_counts),
                'top_colors': [c[0] for c in top_color_counts.most_common(3)]
            },
            'bottom_25_percent': {
                'count': len(bottom_performers),
                'avg_views': avg_views([p.view_count for p in bottom_performers]),
                'dominant_temperatures': dict(bottom_temp_counts),
                'top_colors': [c[0] for c in bottom_color_counts.most_common(3)]
            }
        }
        
        # Return enriched insights (duck-type compatible)
        insights._comparison = insights_dict['comparison']
        return insights


# === Quick test ===
if __name__ == "__main__":
    analyzer = ColorMLAnalyzer()
    
    # Test color classification
    test_colors = [
        (255, 0, 0),    # Red - warm
        (0, 0, 255),    # Blue - cool
        (0, 255, 0),    # Green - neutral/warm
        (255, 200, 0),  # Yellow - warm
        (128, 128, 128),# Gray - neutral
    ]
    
    print("🎨 Testing color classification:")
    for rgb in test_colors:
        temp = analyzer.classify_temperature(rgb)
        sat = analyzer.classify_saturation(rgb)
        bright = analyzer.classify_brightness(rgb)
        print(f"  RGB{rgb} → Temp: {temp}, Sat: {sat}, Bright: {bright}")
