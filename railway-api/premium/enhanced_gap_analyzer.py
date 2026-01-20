"""
Premium Analysis - Enhanced Gap Analyzer
Combines multiple signals for comprehensive content gap discovery.

Sources:
1. Comment analysis (existing)
2. Search demand gaps (YouTube search suggest)
3. Competitor content gaps
4. Trend momentum gaps
5. Semantic clustering gaps
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import re
try:
    from premium.ml_models.viral_predictor import ViralPredictor
    from premium.ml_models.ctr_predictor import CTRPredictor
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("⚠️ ML models not available in EnhancedGapAnalyzer")


@dataclass
class GapOpportunity:
    """A content gap opportunity."""
    topic: str
    opportunity_score: int  # 0-100
    source: str  # comment, search, competitor, trend, semantic
    
    demand_signals: Dict
    estimated_performance: Dict
    execution_guidance: Dict
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class EnhancedGapResult:
    """Full enhanced gap analysis result."""
    gap_sources: Dict[str, List[Dict]]
    prioritized_opportunities: List[GapOpportunity]
    quick_wins: List[str]
    long_term_plays: List[str]
    avoid_topics: List[str]
    
    def to_dict(self) -> Dict:
        return {
            'gap_sources': self.gap_sources,
            'prioritized_opportunities': [o.to_dict() for o in self.prioritized_opportunities],
            'quick_wins': self.quick_wins,
            'long_term_plays': self.long_term_plays,
            'avoid_topics': self.avoid_topics
        }


class EnhancedGapAnalyzer:
    """
    Multi-signal content gap discovery engine.
    
    Combines:
    - Comment-derived gaps (from existing gap analysis)
    - Search demand gaps
    - Competitor content gaps
    - Trending topic gaps
    - Semantic clustering gaps
    """
    
    # Keywords indicating high-demand topics
    DEMAND_SIGNALS = [
        'how to', 'tutorial', 'guide', 'explained', 'for beginners',
        'vs', 'best', 'review', 'tips', 'mistakes', 'secret'
    ]
    
    def __init__(self, data_collector=None, content_clusterer=None):
        self.data_collector = data_collector
        self.content_clusterer = content_clusterer
        
        # Initialize ML predictors
        self.viral_predictor = None
        self.ctr_predictor = None
        
        if ML_AVAILABLE:
            try:
                self.viral_predictor = ViralPredictor()
                self.ctr_predictor = CTRPredictor()
            except Exception as e:
                print(f"⚠️ Failed to init gap analyzer ML: {e}")
    
    def analyze_comprehensive_gaps(self,
                                    channel_videos: List[Dict],
                                    competitor_videos: List[Dict] = None,
                                    comment_gaps: List[Dict] = None,
                                    trends: List[str] = None) -> EnhancedGapResult:
        """
        Perform comprehensive gap analysis.
        
        Args:
            channel_videos: List of channel's existing videos
            competitor_videos: List of competitor videos
            comment_gaps: Gaps from comment analysis (existing feature)
            trends: Current trending topics in niche
            
        Returns:
            EnhancedGapResult with prioritized opportunities
        """
        gap_sources = {
            'comment_derived': [],
            'search_demand': [],
            'competitor_gaps': [],
            'trending_gaps': [],
            'semantic_gaps': []
        }
        
        # 1. Process comment-derived gaps
        if comment_gaps:
            gap_sources['comment_derived'] = self._process_comment_gaps(comment_gaps)
        
        # 2. Identify competitor gaps
        if competitor_videos:
            gap_sources['competitor_gaps'] = self._find_competitor_gaps(
                channel_videos, competitor_videos
            )
        
        # 3. Identify trending gaps
        if trends:
            gap_sources['trending_gaps'] = self._find_trend_gaps(channel_videos, trends)
        
        # 4. Find semantic gaps using clustering
        if channel_videos:
            gap_sources['semantic_gaps'] = self._find_semantic_gaps(channel_videos)
        
        # 5. Generate search demand gaps (simulated - would need API)
        gap_sources['search_demand'] = self._generate_search_gaps(channel_videos)
        
        # Prioritize all opportunities
        all_opportunities = self._prioritize_opportunities(gap_sources, channel_videos)
        
        # Categorize
        quick_wins = self._identify_quick_wins(all_opportunities)
        long_term = self._identify_long_term(all_opportunities)
        avoid = self._identify_saturated(channel_videos, competitor_videos)
        
        return EnhancedGapResult(
            gap_sources=gap_sources,
            prioritized_opportunities=all_opportunities[:10],
            quick_wins=quick_wins,
            long_term_plays=long_term,
            avoid_topics=avoid
        )
    
    def _process_comment_gaps(self, comment_gaps: List[Dict]) -> List[Dict]:
        """Process and score comment-derived gaps."""
        processed = []
        
        for gap in comment_gaps:
            topic = gap.get('topic', gap.get('title', ''))
            mentions = gap.get('mentions', gap.get('comment_count', 1))
            
            # Score based on mentions and sentiment
            score = min(100, mentions * 10)
            
            processed.append({
                'topic': topic,
                'score': score,
                'mentions': mentions,
                'source': 'comment',
                'reasoning': f"Mentioned {mentions} times in comments"
            })
        
        return sorted(processed, key=lambda x: x['score'], reverse=True)[:5]
    
    def _find_competitor_gaps(self, 
                              channel_videos: List[Dict],
                              competitor_videos: List[Dict]) -> List[Dict]:
        """Find topics competitors cover that channel doesn't."""
        gaps = []
        
        # Extract topics from channel
        channel_topics = set()
        for v in channel_videos:
            title = v.get('title', '').lower()
            # Extract key phrases
            words = re.findall(r'\b\w{4,}\b', title)
            channel_topics.update(words)
        
        # Find high-performing competitor topics not in channel
        competitor_topics = {}
        for v in competitor_videos:
            title = v.get('title', '').lower()
            views = v.get('view_count', 0)
            words = re.findall(r'\b\w{4,}\b', title)
            
            for word in words:
                if word not in channel_topics:
                    if word not in competitor_topics:
                        competitor_topics[word] = {'views': 0, 'count': 0}
                    competitor_topics[word]['views'] += views
                    competitor_topics[word]['count'] += 1
        
        # Score and sort
        for topic, stats in competitor_topics.items():
            avg_views = stats['views'] / stats['count'] if stats['count'] > 0 else 0
            if stats['count'] >= 2:  # Topic covered by multiple videos
                gaps.append({
                    'topic': topic.title(),
                    'score': min(100, int(avg_views / 1000)),
                    'competitor_videos': stats['count'],
                    'avg_views': int(avg_views),
                    'source': 'competitor',
                    'reasoning': f"Competitors have {stats['count']} videos averaging {avg_views:,.0f} views"
                })
        
        return sorted(gaps, key=lambda x: x['score'], reverse=True)[:5]
    
    def _find_trend_gaps(self, channel_videos: List[Dict], trends: List[str]) -> List[Dict]:
        """Find trending topics the channel hasn't covered."""
        gaps = []
        
        # Check which trends aren't covered
        channel_text = ' '.join([v.get('title', '').lower() for v in channel_videos])
        
        for trend in trends:
            if trend.lower() not in channel_text:
                gaps.append({
                    'topic': trend,
                    'score': 80,  # Trends get high priority
                    'source': 'trend',
                    'urgency': 'high',
                    'reasoning': "Trending topic not yet covered by your channel"
                })
        
        return gaps[:5]
    
    def _find_semantic_gaps(self, channel_videos: List[Dict]) -> List[Dict]:
        """Find gaps using content clustering analysis."""
        gaps = []
        
        # Identify underserved formats
        format_counts = {}
        for v in channel_videos:
            title = v.get('title', '').lower()
            
            formats = {
                'tutorial': ['how to', 'tutorial', 'guide'],
                'comparison': ['vs', 'versus', 'compared'],
                'listicle': ['top', 'best', 'worst'],
                'review': ['review', 'thoughts on'],
                'news': ['update', 'news', 'announcement']
            }
            
            for fmt, keywords in formats.items():
                if any(kw in title for kw in keywords):
                    format_counts[fmt] = format_counts.get(fmt, 0) + 1
        
        # Suggest missing formats
        all_formats = ['tutorial', 'comparison', 'listicle', 'review', 'news']
        for fmt in all_formats:
            if fmt not in format_counts or format_counts[fmt] < 3:
                gaps.append({
                    'topic': f"Create more '{fmt}' content",
                    'score': 65,
                    'source': 'semantic',
                    'current_count': format_counts.get(fmt, 0),
                    'reasoning': f"Only {format_counts.get(fmt, 0)} {fmt} videos - this format typically performs well"
                })
        
        return gaps[:3]
    
    def _generate_search_gaps(self, channel_videos: List[Dict]) -> List[Dict]:
        """Generate search-based gap suggestions."""
        gaps = []
        
        # Extract main topics from channel
        if channel_videos:
            sample_title = channel_videos[0].get('title', '').lower()
            main_topics = re.findall(r'\b\w{5,}\b', sample_title)[:2]
            
            # Generate search-style suggestions
            templates = [
                "{topic} for beginners",
                "{topic} mistakes to avoid", 
                "{topic} vs alternatives",
                "advanced {topic} tips",
                "{topic} in 2024"
            ]
            
            for topic in main_topics:
                for template in templates[:2]:
                    suggestion = template.format(topic=topic)
                    gaps.append({
                        'topic': suggestion.title(),
                        'score': 55,
                        'source': 'search',
                        'search_volume': 'estimated medium',
                        'reasoning': "Common search pattern in your niche"
                    })
        
        return gaps[:3]
    
    def _prioritize_opportunities(self, gap_sources: Dict, channel_videos: List[Dict] = None) -> List[GapOpportunity]:
        """Combine and prioritize all gap opportunities using ML scoring."""
        all_gaps = []
        
        # Calculate channel stats for relative scoring
        avg_views = 10000
        if channel_videos:
             avg_views = sum(v.get('view_count', 0) for v in channel_videos) / max(1, len(channel_videos))
        
        for source, gaps in gap_sources.items():
            for gap in gaps:
                topic = gap.get('topic', 'Unknown')
                
                # Scientific: Predict performance if ML available
                ml_score = 0.5
                viral_prob = 0.0
                pred_views = 0
                
                if self.viral_predictor and channel_videos:
                    # Simulate a video for this topic to check potential
                    # We assume a "how to" or "guide" format for the title to test topic strength
                    test_title = f"{topic} Guide" if len(topic.split()) < 4 else topic
                    
                    try:
                        pred = self.viral_predictor.predict(
                            title=test_title, 
                            hook_text="", # Neutral hook
                            topic=topic,
                            channel_history=channel_videos
                        )
                        pred_views = pred.predicted_views
                        viral_prob = pred.viral_probability
                        # ML Score: Ratio of predicted / average (normalized)
                        ratio = pred_views / max(avg_views, 1)
                        ml_score = min(0.95, max(0.1, ratio / 3.0)) # 3x avg = 1.0 score roughly
                    except:
                        pass
                
                # Base score from source (still kept as signal)
                source_score = gap.get('score', 50)
                
                # Final Opportunity Score: Weighted blend
                # 60% ML prediction (if available), 40% Source Signal (mentions, search vol, etc)
                if self.viral_predictor:
                    final_score = int((ml_score * 100 * 0.6) + (source_score * 0.4))
                else:
                    final_score = int(source_score)
                
                # Create opportunity object
                opportunity = GapOpportunity(
                    topic=topic,
                    opportunity_score=final_score,
                    source=source,
                    demand_signals={
                        'source_score': source_score,
                        'mentions': gap.get('mentions', 0),
                        'competitor_coverage': gap.get('competitor_videos', 0),
                        'search_volume': gap.get('search_volume', 'unknown')
                    },
                    estimated_performance={
                        'predicted_views': pred_views if pred_views > 0 else None,
                        'viral_probability': round(viral_prob, 2),
                        'view_range': [int(pred_views * 0.8), int(pred_views * 1.5)] if pred_views > 0 else None,
                        'ctr_estimate': None # Could use CTR predictor similarly if we had a thumbnail
                    },
                    execution_guidance={
                        'video_format': self._suggest_format(gap),
                        'ideal_length': '10-15 min',
                        'urgency': gap.get('urgency', 'normal')
                    }
                )
                all_gaps.append(opportunity)
        
        # Sort by score
        all_gaps.sort(key=lambda x: x.opportunity_score, reverse=True)
        
        # Remove duplicates (by similar topic)
        seen_topics = set()
        unique_gaps = []
        for gap in all_gaps:
            topic_key = gap.topic.lower()[:20]
            if topic_key not in seen_topics:
                seen_topics.add(topic_key)
                unique_gaps.append(gap)
        
        return unique_gaps
    
    def _suggest_format(self, gap: Dict) -> str:
        """Suggest video format based on gap type."""
        source = gap.get('source', '')
        topic = gap.get('topic', '').lower()
        
        if 'how' in topic or 'tutorial' in topic:
            return 'step-by-step tutorial'
        elif 'vs' in topic or 'compare' in topic:
            return 'comparison video'
        elif 'top' in topic or 'best' in topic:
            return 'listicle/ranking'
        elif source == 'trend':
            return 'news/reaction'
        else:
            return 'educational explainer'
    
    def _identify_quick_wins(self, opportunities: List[GapOpportunity]) -> List[str]:
        """Identify quick-win opportunities."""
        quick_wins = []
        
        for opp in opportunities[:5]:
            if opp.opportunity_score >= 70:
                quick_wins.append(f"{opp.topic} ({opp.source})")
        
        return quick_wins[:3]
    
    def _identify_long_term(self, opportunities: List[GapOpportunity]) -> List[str]:
        """Identify long-term opportunity plays."""
        long_term = []
        
        for opp in opportunities:
            if opp.source == 'semantic' or 'series' in opp.topic.lower():
                long_term.append(f"Build a {opp.topic} series")
        
        # Add generic long-term suggestions
        long_term.extend([
            "Create a signature series format",
            "Build content pillars around top 3 topics"
        ])
        
        return long_term[:3]
    
    def _identify_saturated(self, 
                            channel_videos: List[Dict],
                            competitor_videos: List[Dict] = None) -> List[str]:
        """Identify oversaturated topics to avoid."""
        avoid = []
        
        # Find overused topics in channel
        topic_counts = {}
        for v in channel_videos:
            title = v.get('title', '').lower()
            words = re.findall(r'\b\w{5,}\b', title)
            for word in words:
                topic_counts[word] = topic_counts.get(word, 0) + 1
        
        for topic, count in topic_counts.items():
            if count >= 5:
                avoid.append(f"'{topic.title()}' - already covered {count} times")
        
        return avoid[:3]


# === Quick test ===
if __name__ == "__main__":
    print("🧪 Testing Enhanced Gap Analyzer...")
    
    analyzer = EnhancedGapAnalyzer()
    
    # Sample data
    channel_videos = [
        {'title': 'Python Tutorial for Beginners', 'view_count': 50000},
        {'title': 'How to Build a Website', 'view_count': 30000},
        {'title': 'JavaScript Basics Explained', 'view_count': 40000},
    ]
    
    competitor_videos = [
        {'title': 'React vs Vue Complete Guide', 'view_count': 100000},
        {'title': 'Docker Tutorial for Beginners', 'view_count': 80000},
        {'title': 'Docker Best Practices', 'view_count': 60000},
    ]
    
    result = analyzer.analyze_comprehensive_gaps(
        channel_videos,
        competitor_videos,
        trends=['AI coding tools', 'GitHub Copilot']
    )
    
    print(f"\n📊 Gap Analysis Results:")
    print(f"   Sources analyzed: {len(result.gap_sources)}")
    
    print(f"\n   🎯 Top Opportunities:")
    for opp in result.prioritized_opportunities[:3]:
        print(f"      • {opp.topic} (Score: {opp.opportunity_score})")
        print(f"        Source: {opp.source}")
    
    print(f"\n   ⚡ Quick Wins: {', '.join(result.quick_wins)}")
    print(f"\n   📈 Long-term Plays: {', '.join(result.long_term_plays)}")
    print(f"\n   ⚠️ Avoid: {', '.join(result.avoid_topics) if result.avoid_topics else 'None'}")
