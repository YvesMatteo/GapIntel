"""
Premium Analysis - Competitor Analyzer
Discovers and analyzes competitor channels for benchmarking.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


@dataclass
class CompetitorInsight:
    """Analysis results for a competitor channel."""
    channel_id: str
    channel_name: str
    subscriber_count: int
    
    # Performance
    avg_views_per_video: float
    avg_engagement_rate: float
    upload_frequency_days: float
    subscriber_growth_estimate: float  # Based on recent video performance
    
    # Content strategy
    top_formats: List[str]
    avg_video_length_seconds: int
    posting_day_pattern: List[str]
    
    # Top performers
    top_videos: List[Dict]
    
    # Thumbnail patterns
    thumbnail_patterns: Dict
    
    # Title patterns  
    title_patterns: Dict
    
    # Comparison to target
    comparison: Dict = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class CompetitorAnalyzer:
    """
    Discovers and analyzes competitor channels.
    
    Provides:
    - Automatic competitor discovery
    - Deep analysis of competitor strategies
    - Thumbnail and title pattern extraction
    - Comparative benchmarking
    """
    
    def __init__(self, data_collector=None, thumbnail_extractor=None):
        """
        Initialize with optional data collector and thumbnail extractor.
        
        Args:
            data_collector: YouTubeDataCollector instance
            thumbnail_extractor: ThumbnailFeatureExtractor instance
        """
        self.data_collector = data_collector
        self.thumbnail_extractor = thumbnail_extractor
    
    def discover_competitors(self, channel_id: str, 
                             search_terms: List[str] = None,
                             max_competitors: int = 10) -> List[Dict]:
        """
        Discover competitor channels in the same niche.
        
        Uses the data collector's discovery method.
        """
        if self.data_collector is None:
            raise ValueError("Data collector not initialized")
        
        return self.data_collector.discover_competitors(
            channel_id, search_terms, max_competitors
        )
    
    def analyze_competitor(self, channel_id: str, 
                           video_limit: int = 20) -> CompetitorInsight:
        """
        Deep analysis of a single competitor channel.
        """
        if self.data_collector is None:
            raise ValueError("Data collector not initialized")
        
        # Collect channel data
        data = self.data_collector.collect_channel_data(channel_id, video_limit)
        channel = data['channel']
        videos = data['videos']
        
        # Calculate metrics
        avg_views = sum(v['view_count'] for v in videos) / len(videos) if videos else 0
        avg_engagement = sum(v['engagement_rate'] for v in videos) / len(videos) if videos else 0
        avg_duration = sum(v['duration_seconds'] for v in videos) / len(videos) if videos else 0
        
        # Analyze posting patterns
        posting_days = self._analyze_posting_days(videos)
        
        # Identify top formats (from title keywords)
        top_formats = self._identify_formats(videos)
        
        # Get top performers
        top_videos = sorted(videos, key=lambda v: v['view_count'], reverse=True)[:5]
        
        # Analyze thumbnail patterns
        thumbnail_patterns = self._analyze_thumbnail_patterns(videos)
        
        # Analyze title patterns
        title_patterns = self._analyze_title_patterns(videos)
        
        # Estimate subscriber growth
        growth_estimate = self._estimate_growth(videos, channel['subscriber_count'])
        
        return CompetitorInsight(
            channel_id=channel_id,
            channel_name=channel['channel_name'],
            subscriber_count=channel['subscriber_count'],
            avg_views_per_video=avg_views,
            avg_engagement_rate=avg_engagement,
            upload_frequency_days=channel.get('upload_frequency_days', 0),
            subscriber_growth_estimate=growth_estimate,
            top_formats=top_formats,
            avg_video_length_seconds=int(avg_duration),
            posting_day_pattern=posting_days,
            top_videos=top_videos,
            thumbnail_patterns=thumbnail_patterns,
            title_patterns=title_patterns
        )
    
    def comparative_analysis(self, target_channel_id: str,
                             competitor_ids: List[str]) -> Dict:
        """
        Compare target channel against competitors.
        
        Returns benchmarking data showing how target compares.
        """
        if self.data_collector is None:
            raise ValueError("Data collector not initialized")
        
        # Analyze target
        target_data = self.data_collector.collect_channel_data(target_channel_id, 20)
        target_channel = target_data['channel']
        target_videos = target_data['videos']
        
        # Analyze competitors
        competitor_analyses = []
        for comp_id in competitor_ids[:5]:  # Limit to 5 for API efficiency
            try:
                analysis = self.analyze_competitor(comp_id)
                competitor_analyses.append(analysis.to_dict())
            except Exception as e:
                print(f"⚠️ Failed to analyze {comp_id}: {e}")
        
        if not competitor_analyses:
            return {'error': 'No competitor data available'}
        
        # Calculate averages
        avg_competitor_views = sum(c['avg_views_per_video'] for c in competitor_analyses) / len(competitor_analyses)
        avg_competitor_engagement = sum(c['avg_engagement_rate'] for c in competitor_analyses) / len(competitor_analyses)
        
        # Target metrics
        target_avg_views = sum(v['view_count'] for v in target_videos) / len(target_videos) if target_videos else 0
        target_avg_engagement = sum(v['engagement_rate'] for v in target_videos) / len(target_videos) if target_videos else 0
        
        # Comparisons
        comparison = {
            'target_channel': target_channel['channel_name'],
            'competitors_analyzed': len(competitor_analyses),
            
            'views_comparison': {
                'target_avg': target_avg_views,
                'competitor_avg': avg_competitor_views,
                'performance_ratio': target_avg_views / max(avg_competitor_views, 1),
                'verdict': 'outperforming' if target_avg_views > avg_competitor_views else 'underperforming'
            },
            
            'engagement_comparison': {
                'target_avg': target_avg_engagement,
                'competitor_avg': avg_competitor_engagement,
                'performance_ratio': target_avg_engagement / max(avg_competitor_engagement, 0.01),
                'verdict': 'outperforming' if target_avg_engagement > avg_competitor_engagement else 'underperforming'
            },
            
            'competitor_details': competitor_analyses,
            
            'recommendations': self._generate_recommendations(
                target_videos, competitor_analyses
            )
        }
        
        return comparison
    
    def _analyze_posting_days(self, videos: List[Dict]) -> List[str]:
        """Identify which days videos are typically posted."""
        day_counts = {}
        for v in videos:
            try:
                dt = datetime.fromisoformat(v['published_at'].replace('Z', '+00:00'))
                day = dt.strftime('%A')
                day_counts[day] = day_counts.get(day, 0) + 1
            except:
                continue
        
        return sorted(day_counts.keys(), key=lambda d: day_counts[d], reverse=True)[:3]
    
    def _identify_formats(self, videos: List[Dict]) -> List[str]:
        """Identify common video formats from titles."""
        format_keywords = {
            'tutorial': ['how to', 'tutorial', 'guide', 'learn', 'step by step'],
            'review': ['review', 'unboxing', 'first look', 'hands on'],
            'reaction': ['reaction', 'reacting', 'react'],
            'vlog': ['vlog', 'day in', 'behind the scenes'],
            'comparison': ['vs', 'versus', 'compared', 'battle'],
            'listicle': ['top 10', 'top 5', 'best', 'worst'],
            'news': ['breaking', 'update', 'news', 'announcement']
        }
        
        format_counts = {}
        for v in videos:
            title_lower = v['title'].lower()
            for format_name, keywords in format_keywords.items():
                if any(kw in title_lower for kw in keywords):
                    format_counts[format_name] = format_counts.get(format_name, 0) + 1
        
        return sorted(format_counts.keys(), key=lambda f: format_counts[f], reverse=True)[:3]
    
    def _analyze_thumbnail_patterns(self, videos: List[Dict]) -> Dict:
        """Analyze common patterns in thumbnails."""
        patterns = {
            'analyzed_count': 0,
            'common_elements': [],
            'color_trends': [],
            'recommendations': []
        }
        
        if self.thumbnail_extractor is None:
            patterns['note'] = 'Thumbnail extractor not available for deep analysis'
            return patterns
        
        # Sample top performers for analysis
        top_videos = sorted(videos, key=lambda v: v['view_count'], reverse=True)[:5]
        
        face_count = 0
        text_count = 0
        high_contrast = 0
        
        for video in top_videos:
            if not video.get('thumbnail_url'):
                continue
            
            try:
                features = self.thumbnail_extractor.extract_from_url(video['thumbnail_url'])
                patterns['analyzed_count'] += 1
                
                if features.face_count > 0:
                    face_count += 1
                if features.has_text:
                    text_count += 1
                if features.contrast_score > 0.3:
                    high_contrast += 1
            except:
                continue
        
        total = patterns['analyzed_count'] or 1
        
        if face_count / total > 0.6:
            patterns['common_elements'].append('Faces in thumbnails')
        if text_count / total > 0.6:
            patterns['common_elements'].append('Text overlays')
        if high_contrast / total > 0.6:
            patterns['common_elements'].append('High contrast colors')
        
        return patterns
    
    def _analyze_title_patterns(self, videos: List[Dict]) -> Dict:
        """Analyze common patterns in video titles."""
        patterns = {
            'avg_length': 0,
            'common_words': [],
            'uses_numbers_pct': 0,
            'uses_questions_pct': 0,
            'all_caps_pct': 0
        }
        
        if not videos:
            return patterns
        
        total = len(videos)
        total_length = 0
        word_counts = {}
        numbers_count = 0
        questions_count = 0
        caps_count = 0
        
        for v in videos:
            title = v['title']
            total_length += len(title)
            
            if any(c.isdigit() for c in title):
                numbers_count += 1
            if '?' in title:
                questions_count += 1
            if title.isupper():
                caps_count += 1
            
            # Word frequency
            for word in title.lower().split():
                if len(word) > 3:  # Skip short words
                    word_counts[word] = word_counts.get(word, 0) + 1
        
        patterns['avg_length'] = total_length / total
        patterns['uses_numbers_pct'] = (numbers_count / total) * 100
        patterns['uses_questions_pct'] = (questions_count / total) * 100
        patterns['all_caps_pct'] = (caps_count / total) * 100
        
        # Top words
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        patterns['common_words'] = [w[0] for w in sorted_words[:10]]
        
        return patterns
    
    def _estimate_growth(self, videos: List[Dict], subscriber_count: int) -> float:
        """Estimate subscriber growth based on recent video performance."""
        if not videos or subscriber_count == 0:
            return 0.0
        
        # Average CTR proxy as growth indicator
        avg_ctr_proxy = sum(v['ctr_proxy'] for v in videos) / len(videos)
        
        # Rough estimate: high CTR proxy indicates growth
        if avg_ctr_proxy > 1.5:
            return 5.0  # Estimated 5% monthly growth
        elif avg_ctr_proxy > 1.0:
            return 3.0
        elif avg_ctr_proxy > 0.5:
            return 1.0
        else:
            return 0.0
    
    def _generate_recommendations(self, target_videos: List[Dict],
                                   competitor_analyses: List[Dict]) -> List[str]:
        """Generate recommendations based on comparison."""
        recommendations = []
        
        # Check upload frequency
        target_freq = 7  # Default weekly
        if target_videos:
            dates = sorted([v['published_at'] for v in target_videos])
            if len(dates) > 1:
                # Rough calculation
                target_freq = 7  # Placeholder
        
        comp_freq_avg = sum(c['upload_frequency_days'] for c in competitor_analyses) / len(competitor_analyses)
        
        if target_freq > comp_freq_avg * 1.5:
            recommendations.append(
                f"Competitors upload more frequently (every {comp_freq_avg:.0f} days). Consider increasing upload consistency."
            )
        
        # Check formats
        all_formats = []
        for c in competitor_analyses:
            all_formats.extend(c.get('top_formats', []))
        
        common_formats = set(all_formats)
        recommendations.append(
            f"Popular formats in your niche: {', '.join(list(common_formats)[:3])}. Consider experimenting with these."
        )
        
        # Check engagement
        target_engagement = sum(v['engagement_rate'] for v in target_videos) / len(target_videos) if target_videos else 0
        comp_engagement = sum(c['avg_engagement_rate'] for c in competitor_analyses) / len(competitor_analyses)
        
        if target_engagement < comp_engagement:
            recommendations.append(
                "Your engagement rate is below competitor average. Focus on calls-to-action and community interaction."
            )
        
        return recommendations


# === Quick test ===
if __name__ == "__main__":
    print("🧪 Competitor Analyzer module loaded successfully")
    print("   Use with YouTubeDataCollector for full functionality")
