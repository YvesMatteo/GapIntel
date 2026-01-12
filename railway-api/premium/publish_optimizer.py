"""
Premium Analysis - Publishing Time Optimizer
Finds optimal posting times based on historical data and competitor analysis.

Analyzes:
- Historical channel performance by day/hour
- Competitor posting schedules
- Audience online patterns
- Topic-specific timing (news vs evergreen)
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np


@dataclass
class TimeSlot:
    """A recommended time slot for publishing."""
    day: str
    hour_utc: int
    expected_view_boost: str
    reasoning: str
    competitor_overlap: bool


@dataclass
class AvoidTime:
    """A time to avoid for publishing."""
    day: str
    hour_utc: int
    reason: str


@dataclass
class PublishTimeResult:
    """Full publishing time analysis."""
    best_days: List[str]
    best_hours_utc: List[int]
    schedule_recommendations: List[TimeSlot]
    avoid_times: List[AvoidTime]
    content_specific: Dict[str, str]
    weekly_heatmap: Dict[str, List[float]]
    
    def to_dict(self) -> Dict:
        return {
            'best_days': self.best_days,
            'best_hours_utc': self.best_hours_utc,
            'schedule_recommendations': [asdict(r) for r in self.schedule_recommendations],
            'avoid_times': [asdict(a) for a in self.avoid_times],
            'content_specific': self.content_specific,
            'weekly_heatmap': self.weekly_heatmap
        }


class PublishTimeOptimizer:
    """
    Finds optimal publishing times for maximum reach.
    
    Analyzes:
    - Historical performance by time
    - Competitor schedules
    - Content type timing
    """
    
    DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Industry benchmarks for YouTube
    GENERAL_BEST_TIMES = {
        'weekday_morning': (9, 11),   # 9-11 AM UTC
        'weekday_afternoon': (14, 16), # 2-4 PM UTC  
        'weekend_morning': (10, 12),   # 10-12 AM UTC
    }
    
    # Content-specific timing recommendations
    CONTENT_TIMING = {
        'news': "Post ASAP when topic is trending - timing is critical",
        'tutorial': "Weekday mornings (9-11 AM) perform best - people learning",
        'entertainment': "Weekend evenings (6-9 PM) - leisure viewing time",
        'vlog': "Consistent schedule matters more than specific time",
        'review': "Tuesday-Thursday afternoons - shopping consideration time",
        'gaming': "Weekend afternoons or weekday evenings - gaming time",
        'educational': "Weekday mornings - study/learning mindset"
    }
    
    def __init__(self):
        self.channel_data = None
        self.competitor_data = None
    
    def analyze_optimal_times(self, 
                              videos: List[Dict] = None,
                              competitor_videos: List[Dict] = None,
                              content_type: str = "general") -> PublishTimeResult:
        """
        Analyze and recommend optimal publishing times.
        
        Args:
            videos: List of channel's past videos with publish times and views
            competitor_videos: List of competitor videos
            content_type: Type of content being planned
            
        Returns:
            PublishTimeResult with recommendations
        """
        # Build performance heatmap
        if videos:
            heatmap = self._build_performance_heatmap(videos)
        else:
            heatmap = self._default_heatmap()
        
        # Find best times from heatmap
        best_slots = self._find_best_slots(heatmap)
        
        # Analyze competitor times
        competitor_schedule = {}
        if competitor_videos:
            competitor_schedule = self._analyze_competitor_schedule(competitor_videos)
        
        # Build recommendations
        recommendations = self._build_recommendations(best_slots, competitor_schedule)
        
        # Find times to avoid
        avoid_times = self._find_avoid_times(heatmap, competitor_schedule)
        
        # Get content-specific advice
        content_advice = self._get_content_advice(content_type)
        
        # Extract best days and hours
        best_days = list(dict.fromkeys([r.day for r in recommendations]))[:3]
        best_hours = list(dict.fromkeys([r.hour_utc for r in recommendations]))[:3]
        
        return PublishTimeResult(
            best_days=best_days,
            best_hours_utc=best_hours,
            schedule_recommendations=recommendations[:5],
            avoid_times=avoid_times[:3],
            content_specific=content_advice,
            weekly_heatmap=heatmap
        )
    
    def _build_performance_heatmap(self, videos: List[Dict]) -> Dict[str, List[float]]:
        """Build a performance heatmap from video data."""
        # Initialize heatmap with zeros
        heatmap = {day: [0.0] * 24 for day in self.DAYS}
        counts = {day: [0] * 24 for day in self.DAYS}
        
        for video in videos:
            try:
                # Parse publish time
                pub_time = video.get('published_at', '')
                if isinstance(pub_time, str):
                    dt = datetime.fromisoformat(pub_time.replace('Z', '+00:00'))
                else:
                    continue
                
                day_name = self.DAYS[dt.weekday()]
                hour = dt.hour
                
                # Normalize views (use view velocity if available)
                views = video.get('view_count', 0)
                
                heatmap[day_name][hour] += views
                counts[day_name][hour] += 1
            except:
                continue
        
        # Calculate averages
        for day in self.DAYS:
            for hour in range(24):
                if counts[day][hour] > 0:
                    heatmap[day][hour] = heatmap[day][hour] / counts[day][hour]
        
        # Normalize to 0-1 scale
        max_val = max(max(hours) for hours in heatmap.values()) or 1
        for day in self.DAYS:
            heatmap[day] = [v / max_val for v in heatmap[day]]
        
        return heatmap
    
    def _default_heatmap(self) -> Dict[str, List[float]]:
        """Return industry-standard heatmap when no data available."""
        heatmap = {day: [0.3] * 24 for day in self.DAYS}
        
        # Peak times based on industry data
        peak_times = [
            ('Monday', 14, 0.8),
            ('Tuesday', 14, 0.9),
            ('Wednesday', 14, 0.85),
            ('Thursday', 14, 0.9),
            ('Thursday', 18, 0.85),
            ('Friday', 14, 0.8),
            ('Friday', 18, 0.75),
            ('Saturday', 10, 0.85),
            ('Saturday', 14, 0.8),
            ('Sunday', 10, 0.8),
            ('Sunday', 14, 0.75),
        ]
        
        for day, hour, score in peak_times:
            heatmap[day][hour] = score
            # Spread to adjacent hours
            if hour > 0:
                heatmap[day][hour-1] = max(heatmap[day][hour-1], score * 0.7)
            if hour < 23:
                heatmap[day][hour+1] = max(heatmap[day][hour+1], score * 0.7)
        
        return heatmap
    
    def _find_best_slots(self, heatmap: Dict[str, List[float]]) -> List[Tuple[str, int, float]]:
        """Find the best performing time slots."""
        slots = []
        
        for day in self.DAYS:
            for hour in range(24):
                score = heatmap[day][hour]
                if score > 0.5:  # Above average threshold
                    slots.append((day, hour, score))
        
        # Sort by score descending
        slots.sort(key=lambda x: x[2], reverse=True)
        
        return slots[:10]
    
    def _analyze_competitor_schedule(self, videos: List[Dict]) -> Dict[str, List[int]]:
        """Analyze when competitors typically publish."""
        schedule = defaultdict(list)
        
        for video in videos:
            try:
                pub_time = video.get('published_at', '')
                if isinstance(pub_time, str):
                    dt = datetime.fromisoformat(pub_time.replace('Z', '+00:00'))
                    day_name = self.DAYS[dt.weekday()]
                    schedule[day_name].append(dt.hour)
            except:
                continue
        
        return dict(schedule)
    
    def _build_recommendations(self, 
                               best_slots: List[Tuple[str, int, float]],
                               competitor_schedule: Dict[str, List[int]]) -> List[TimeSlot]:
        """Build time slot recommendations."""
        recommendations = []
        
        for day, hour, score in best_slots:
            # Check competitor overlap
            competitor_hours = competitor_schedule.get(day, [])
            has_overlap = hour in competitor_hours
            
            # Calculate expected boost
            boost_pct = int((score - 0.5) * 60)  # Convert to percentage
            
            # Reasoning
            if has_overlap:
                reasoning = f"High performance time, but {len([h for h in competitor_hours if h == hour])} competitors also post then"
            elif score > 0.8:
                reasoning = "Peak audience activity time based on your channel's history"
            else:
                reasoning = "Good performance with lower competition"
            
            recommendations.append(TimeSlot(
                day=day,
                hour_utc=hour,
                expected_view_boost=f"+{boost_pct}%" if boost_pct > 0 else "baseline",
                reasoning=reasoning,
                competitor_overlap=has_overlap
            ))
        
        # Prioritize no-overlap high-score slots
        recommendations.sort(key=lambda x: (x.competitor_overlap, -int(x.expected_view_boost.replace('%', '').replace('+', '') or '0')))
        
        return recommendations
    
    def _find_avoid_times(self, 
                          heatmap: Dict[str, List[float]],
                          competitor_schedule: Dict[str, List[int]]) -> List[AvoidTime]:
        """Find times to avoid publishing."""
        avoid = []
        
        # Low performance times
        for day in self.DAYS:
            for hour in range(24):
                if heatmap[day][hour] < 0.3:
                    avoid.append(AvoidTime(
                        day=day,
                        hour_utc=hour,
                        reason="Historically low viewer activity"
                    ))
        
        # High competitor overlap times
        for day, hours in competitor_schedule.items():
            from collections import Counter
            hour_counts = Counter(hours)
            for hour, count in hour_counts.items():
                if count >= 3:
                    avoid.append(AvoidTime(
                        day=day,
                        hour_utc=hour,
                        reason=f"{count} competitors typically post at this time"
                    ))
        
        # Deduplicate and prioritize
        seen = set()
        unique_avoid = []
        for a in avoid:
            key = (a.day, a.hour_utc)
            if key not in seen:
                seen.add(key)
                unique_avoid.append(a)
        
        return unique_avoid
    
    def _get_content_advice(self, content_type: str) -> Dict[str, str]:
        """Get content-specific timing advice."""
        advice = {}
        
        # Specific advice for content type
        if content_type.lower() in self.CONTENT_TIMING:
            advice['primary'] = self.CONTENT_TIMING[content_type.lower()]
        else:
            advice['primary'] = "Consistency matters most - pick a schedule and stick to it"
        
        # General advice
        advice['general'] = [
            "Tuesday and Thursday typically see highest engagement",
            "Avoid Monday mornings and Friday evenings",
            "Consider your primary audience's timezone",
            "Post at least 2 hours before your peak viewing time"
        ]
        
        return advice


# === Quick test ===
if __name__ == "__main__":
    print("🧪 Testing Publish Time Optimizer...")
    
    optimizer = PublishTimeOptimizer()
    
    # Test without data (uses defaults)
    result = optimizer.analyze_optimal_times(content_type="tutorial")
    
    print(f"\n📊 Optimal Publishing Times:")
    print(f"   Best Days: {', '.join(result.best_days)}")
    print(f"   Best Hours (UTC): {result.best_hours_utc}")
    
    print(f"\n   📅 Recommendations:")
    for rec in result.schedule_recommendations[:3]:
        print(f"      {rec.day} at {rec.hour_utc}:00 UTC - {rec.expected_view_boost}")
        print(f"         → {rec.reasoning}")
    
    print(f"\n   ⚠️ Times to Avoid:")
    for avoid in result.avoid_times[:3]:
        print(f"      {avoid.day} at {avoid.hour_utc}:00 - {avoid.reason}")
    
    print(f"\n   📝 Content-Specific Advice:")
    print(f"      {result.content_specific.get('primary', 'N/A')}")
