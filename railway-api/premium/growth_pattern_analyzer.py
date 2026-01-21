"""
Premium Analysis - Skill 6: Growth Pattern Analyzer

Analyzes upload consistency, content series detection, and growth trajectory.
Correlates posting patterns with engagement to find optimal strategies.

Formulas:
CI (Consistency Index) = 1 - (Std_Deviation / Mean_Days_Between_Uploads)
Series Detection: Title pattern matching (Part 1, Episode 2, etc.)
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import numpy as np


@dataclass
class SeriesInfo:
    """Information about a detected content series."""
    name: str
    video_count: int
    avg_views: float
    avg_engagement: float
    first_video_date: str
    latest_video_date: str
    performance_vs_standalone: float  # % difference
    video_ids: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class GrowthPatternResult:
    """Result of growth pattern analysis."""
    consistency_index: float  # 0-100 (higher = more consistent)
    avg_days_between_uploads: float
    upload_variance: float
    upload_streak_current: int  # Days since regular pattern broken
    series_detected: List[SeriesInfo]
    series_performance_boost: float  # % boost vs standalone
    growth_trajectory: str  # accelerating, stable, declining
    views_growth_rate: float  # % change over period
    optimal_upload_frequency: str
    consistency_impact: str # Impact description based on research
    recommendations: List[str]
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['series_detected'] = [s.to_dict() for s in self.series_detected]
        return result


class GrowthPatternAnalyzer:
    """
    Skill 6: Growth Pattern Analyzer
    
    Analyzes:
    - Upload consistency and its impact on performance
    - Content series detection (Part 1, Episode 2, etc.)
    - Series vs standalone video performance
    - Views/engagement growth trajectory over time
    """
    
    # Patterns indicating series content
    SERIES_PATTERNS = [
        r'(part|pt\.?)\s*(\d+)',           # Part 1, Pt. 2
        r'(episode|ep\.?)\s*(\d+)',        # Episode 1, Ep. 2
        r'#(\d+)',                          # #1, #2
        r'\b(\d+)\s*[-/]\s*(\d+)',          # 1/10, 1-10
        r'(chapter|ch\.?)\s*(\d+)',        # Chapter 1
        r'(day|week)\s*(\d+)',             # Day 1, Week 2
        r'\((\d+)\)',                       # (1), (2)
        r'\[(\d+)\]',                       # [1], [2]
        r':\s*(\d+)',                       # : 1, : 2 (at end of title)
    ]
    
    def __init__(self):
        self.series_regex = [re.compile(p, re.IGNORECASE) for p in self.SERIES_PATTERNS]
    
    def analyze_growth_patterns(self, videos: List[Dict]) -> GrowthPatternResult:
        """
        Analyze growth patterns from video data.
        
        Args:
            videos: List of video dicts with 'published_at', 'view_count', 'engagement_rate', 'title'
            
        Returns:
            GrowthPatternResult with comprehensive growth metrics
        """
        if not videos or len(videos) < 2:
            return self._empty_result()
        
        # Sort videos by publish date
        sorted_videos = self._sort_by_date(videos)
        
        # 1. Calculate upload consistency
        consistency, avg_days, variance = self._calculate_consistency(sorted_videos)
        
        # 2. Detect content series
        series_list = self._detect_series(sorted_videos)
        
        # 3. Calculate series performance boost
        series_boost = self._calculate_series_boost(sorted_videos, series_list)
        
        # 4. Analyze growth trajectory
        trajectory, growth_rate = self._analyze_trajectory(sorted_videos)
        
        # 5. Calculate current streak
        streak = self._calculate_upload_streak(sorted_videos, avg_days)
        
        # 6. Determine optimal frequency
        optimal_freq = self._determine_optimal_frequency(sorted_videos)
        
        # 7. Determine research impact
        impact = self._determine_impact(consistency, avg_days)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            consistency, series_boost, trajectory, avg_days, len(series_list)
        )
        
        return GrowthPatternResult(
            consistency_index=round(consistency, 1),
            avg_days_between_uploads=round(avg_days, 1),
            upload_variance=round(variance, 2),
            upload_streak_current=streak,
            series_detected=series_list,
            series_performance_boost=round(series_boost, 1),
            growth_trajectory=trajectory,
            views_growth_rate=round(growth_rate, 1),
            optimal_upload_frequency=optimal_freq,
            consistency_impact=impact,
            recommendations=recommendations
        )
    
    def _sort_by_date(self, videos: List[Dict]) -> List[Dict]:
        """Sort videos by publish date (oldest first)."""
        def get_date(v):
            # Handle multiple date formats
            date_str = v.get('published_at') or v.get('video_info', {}).get('upload_date', '')
            if not date_str:
                return datetime.min
            try:
                # Try ISO format
                if 'T' in str(date_str):
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                # Try YYYYMMDD
                return datetime.strptime(str(date_str)[:8], '%Y%m%d')
            except:
                return datetime.min
        
        return sorted(videos, key=get_date)
    
    def _calculate_consistency(self, sorted_videos: List[Dict]) -> Tuple[float, float, float]:
        """
        Calculate upload consistency index.
        CI = 1 - (std_dev / mean) * 100, clamped to 0-100
        """
        if len(sorted_videos) < 2:
            return 50.0, 7.0, 0.0
        
        # Calculate days between uploads
        gaps = []
        for i in range(1, len(sorted_videos)):
            date1 = self._get_date(sorted_videos[i-1])
            date2 = self._get_date(sorted_videos[i])
            if date1 and date2:
                gap = (date2 - date1).days
                if gap > 0:  # Ignore same-day uploads
                    gaps.append(gap)
        
        if not gaps:
            return 50.0, 7.0, 0.0
        
        mean_gap = np.mean(gaps)
        std_gap = np.std(gaps) if len(gaps) > 1 else 0
        
        # Coefficient of variation (lower = more consistent)
        cv = std_gap / mean_gap if mean_gap > 0 else 0
        
        # Convert to 0-100 scale (100 = perfectly consistent)
        consistency = max(0, min(100, (1 - cv) * 100))
        
        return consistency, mean_gap, std_gap
    
    def _get_date(self, video: Dict) -> Optional[datetime]:
        """Extract datetime from video dict."""
        date_str = video.get('published_at') or video.get('video_info', {}).get('upload_date', '')
        if not date_str:
            return None
        try:
            if 'T' in str(date_str):
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return datetime.strptime(str(date_str)[:8], '%Y%m%d')
        except:
            return None
    
    def _detect_series(self, videos: List[Dict]) -> List[SeriesInfo]:
        """Detect content series from title patterns."""
        # Group videos by potential series
        series_groups = defaultdict(list)
        
        for video in videos:
            title = video.get('title', '') or video.get('video_info', {}).get('title', '')
            
            # Try each series pattern
            for regex in self.series_regex:
                match = regex.search(title)
                if match:
                    # Extract series name (title without the number part)
                    series_name = regex.sub('', title).strip()
                    # Clean up the name
                    series_name = re.sub(r'\s+', ' ', series_name)
                    series_name = re.sub(r'[-:|]\s*$', '', series_name).strip()
                    
                    if len(series_name) > 5:  # Minimum length to be meaningful
                        series_groups[series_name.lower()].append(video)
                    break
        
        # FALLBACK: If no regex matches, try fuzzy title prefix matching
        # This catches recurring formats like "TOGI VS CABO", "REACT TO", etc.
        if not series_groups:
            title_prefixes = defaultdict(list)
            for video in videos:
                title = video.get('title', '') or video.get('video_info', {}).get('title', '')
                if not title:
                    continue
                # Extract first 3-4 words as potential series prefix
                words = title.split()[:4]
                for length in [4, 3, 2]:  # Try longest prefixes first
                    if len(words) >= length:
                        prefix = ' '.join(words[:length]).lower()
                        # Skip very short or common prefixes
                        if len(prefix) > 8 and prefix not in ['how to', 'why i', 'the best', 'my new']:
                            title_prefixes[prefix].append(video)
                            break
            
            # Only keep prefixes with 2+ videos
            for prefix, vids in title_prefixes.items():
                if len(vids) >= 2:
                    series_groups[prefix] = vids
        
        # Convert to SeriesInfo objects (only series with 2+ videos)
        series_list = []
        for name, vids in series_groups.items():
            if len(vids) >= 2:
                views = [v.get('view_count', 0) or v.get('video_info', {}).get('view_count', 0) for v in vids]
                engagements = [v.get('engagement_rate', 0) for v in vids]
                
                # Get dates
                dates = [self._get_date(v) for v in vids]
                dates = [d for d in dates if d]
                
                series_list.append(SeriesInfo(
                    name=name.title(),
                    video_count=len(vids),
                    avg_views=np.mean(views) if views else 0,
                    avg_engagement=np.mean(engagements) if engagements else 0,
                    first_video_date=min(dates).isoformat() if dates else '',
                    latest_video_date=max(dates).isoformat() if dates else '',
                    performance_vs_standalone=0,  # Calculated later
                    video_ids=[v.get('video_id', '') or v.get('video_info', {}).get('id', '') for v in vids]
                ))
        
        return series_list
    
    def _calculate_series_boost(self, videos: List[Dict], 
                                 series_list: List[SeriesInfo]) -> float:
        """Calculate % performance boost of series vs standalone videos."""
        # Get all video IDs in series
        series_ids = set()
        for series in series_list:
            series_ids.update(series.video_ids)
        
        # Calculate standalone vs series averages
        series_views = []
        standalone_views = []
        
        for video in videos:
            vid = video.get('video_id', '') or video.get('video_info', {}).get('id', '')
            views = video.get('view_count', 0) or video.get('video_info', {}).get('view_count', 0)
            
            if vid in series_ids:
                series_views.append(views)
            else:
                standalone_views.append(views)
        
        if not standalone_views or not series_views:
            return 0.0
        
        avg_series = np.mean(series_views)
        avg_standalone = np.mean(standalone_views)
        
        if avg_standalone == 0:
            return 0.0
        
        boost = ((avg_series - avg_standalone) / avg_standalone) * 100
        return boost
    
    def _analyze_trajectory(self, sorted_videos: List[Dict]) -> Tuple[str, float]:
        """Analyze views growth trajectory over time."""
        if len(sorted_videos) < 3:
            return 'stable', 0.0
        
        # Split into first half and second half
        mid = len(sorted_videos) // 2
        first_half = sorted_videos[:mid]
        second_half = sorted_videos[mid:]
        
        def avg_views(vids):
            views = [v.get('view_count', 0) or v.get('video_info', {}).get('view_count', 0) for v in vids]
            return np.mean(views) if views else 0
        
        avg_first = avg_views(first_half)
        avg_second = avg_views(second_half)
        
        if avg_first == 0:
            return 'stable', 0.0
        
        growth_rate = ((avg_second - avg_first) / avg_first) * 100
        
        # Determine trajectory
        if growth_rate > 20:
            trajectory = 'accelerating'
        elif growth_rate < -20:
            trajectory = 'declining'
        else:
            trajectory = 'stable'
        
        return trajectory, growth_rate
    
    def _calculate_upload_streak(self, sorted_videos: List[Dict], 
                                  avg_days: float) -> int:
        """Calculate how long the current upload streak has been maintained."""
        if len(sorted_videos) < 2:
            return 0
        
        tolerance = avg_days * 1.5  # Allow 50% variance
        streak = 0
        
        # Work backwards from most recent
        for i in range(len(sorted_videos) - 1, 0, -1):
            date1 = self._get_date(sorted_videos[i-1])
            date2 = self._get_date(sorted_videos[i])
            
            if date1 and date2:
                gap = (date2 - date1).days
                if gap <= tolerance:
                    streak += 1
                else:
                    break
        
        return streak
    
    def _determine_optimal_frequency(self, sorted_videos: List[Dict]) -> str:
        """Determine optimal upload frequency based on performance."""
        if len(sorted_videos) < 5:
            return "Not enough data"
        
        # Group by upload gap
        freq_performance = defaultdict(list)
        
        for i in range(1, len(sorted_videos)):
            date1 = self._get_date(sorted_videos[i-1])
            date2 = self._get_date(sorted_videos[i])
            views = sorted_videos[i].get('view_count', 0) or sorted_videos[i].get('video_info', {}).get('view_count', 0)
            
            if date1 and date2 and views > 0:
                gap = (date2 - date1).days
                # Bucket gaps
                if gap <= 3:
                    freq_performance['2-3 days'].append(views)
                elif gap <= 7:
                    freq_performance['weekly'].append(views)
                elif gap <= 14:
                    freq_performance['bi-weekly'].append(views)
                else:
                    freq_performance['monthly+'].append(views)
        
        # Find best performing frequency
        best_freq = None
        best_avg = 0
        
        for freq, views in freq_performance.items():
            if len(views) >= 2:  # Need at least 2 data points
                avg = np.mean(views)
                if avg > best_avg:
                    best_avg = avg
                    best_freq = freq
        
        return best_freq or "weekly"
    
    def _determine_impact(self, consistency: float, avg_days: float) -> str:
        """Determine growth impact based on consistency research."""
        if consistency < 45:
            return "Sporadic uploads linked to 60% lower growth"
        
        # Consistent
        if 6 <= avg_days <= 8: # Weekly
            return "Consistent weekly uploads linked to 156% higher growth"
        elif 12 <= avg_days <= 16: # Bi-weekly
            return "Consistent bi-weekly schedule linked to 89% higher growth"
        elif avg_days <= 2: # Daily
            return "High frequency can trigger 200%+ faster growth if quality maintained"
        else:
             return "Consistent schedule builds audience habit"
    
    def _generate_recommendations(self, consistency: float, series_boost: float,
                                    trajectory: str, avg_days: float,
                                    series_count: int) -> List[str]:
        """Generate actionable recommendations."""
        recs = []
        
        if consistency < 50:
            recs.append(f"Upload consistency is low ({consistency:.0f}%). Aim for regular {avg_days:.0f}-day schedule")
        
        if series_boost > 20 and series_count > 0:
            recs.append(f"Series content performs {series_boost:.0f}% better - create more series")
        elif series_count == 0:
            recs.append("No content series detected - consider creating multi-part content")
        
        if trajectory == 'declining':
            recs.append("Views trending down - analyze recent content for format changes")
        elif trajectory == 'accelerating':
            recs.append("Growth accelerating! Continue current strategy")
        
        if avg_days > 14:
            recs.append(f"Uploading every {avg_days:.0f} days may be too infrequent")
        
        if not recs:
            recs.append("Growth patterns are healthy - maintain current approach")
        
        return recs
    
    def _empty_result(self) -> GrowthPatternResult:
        """Return empty result when no data available."""
        return GrowthPatternResult(
            consistency_index=0,
            avg_days_between_uploads=0,
            upload_variance=0,
            upload_streak_current=0,
            series_detected=[],
            series_performance_boost=0,
            growth_trajectory='unknown',
            views_growth_rate=0,
            optimal_upload_frequency='unknown',
            consistency_impact="Not enough data",
            recommendations=["Not enough data for growth pattern analysis"]
        )


# === Quick test ===
if __name__ == "__main__":
    print("🧪 Testing Growth Pattern Analyzer...")
    
    analyzer = GrowthPatternAnalyzer()
    
    # Sample data
    test_videos = [
        {'video_id': '1', 'title': 'Python Tutorial Part 1', 'published_at': '2024-01-01T10:00:00Z', 'view_count': 10000},
        {'video_id': '2', 'title': 'Python Tutorial Part 2', 'published_at': '2024-01-08T10:00:00Z', 'view_count': 12000},
        {'video_id': '3', 'title': 'Random Vlog', 'published_at': '2024-01-15T10:00:00Z', 'view_count': 5000},
        {'video_id': '4', 'title': 'Python Tutorial Part 3', 'published_at': '2024-01-22T10:00:00Z', 'view_count': 15000},
        {'video_id': '5', 'title': 'Best Practices in Code', 'published_at': '2024-01-29T10:00:00Z', 'view_count': 8000},
    ]
    
    result = analyzer.analyze_growth_patterns(test_videos)
    
    print(f"\n📊 Results:")
    print(f"   Consistency Index: {result.consistency_index}")
    print(f"   Avg Days Between: {result.avg_days_between_uploads}")
    print(f"   Trajectory: {result.growth_trajectory}")
    print(f"   Series Found: {len(result.series_detected)}")
    if result.series_detected:
        for s in result.series_detected:
            print(f"      • {s.name}: {s.video_count} videos")
    print(f"   Series Boost: {result.series_performance_boost}%")
    print(f"\n   Recommendations:")
    for rec in result.recommendations:
        print(f"      • {rec}")
