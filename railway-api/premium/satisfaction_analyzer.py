"""
Premium Analysis - Skill 4: Satisfaction Signals Analyzer

Calculates viewer satisfaction index from comments and engagement data.
Detects success signals ("it worked", "thanks this helped") and confusion signals.

Formula:
SI = (Engagement_Quality × 0.6) + (Retention_Proxy × 0.3) + (Implementation_Success × 0.1)
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import Counter


@dataclass
class SatisfactionResult:
    """Result of satisfaction analysis."""
    satisfaction_index: float  # 0-100 score
    engagement_quality_score: float
    retention_proxy_score: float
    implementation_success_score: float
    success_comment_count: int
    confusion_signal_count: int
    return_viewer_ratio: float
    clarity_score: float
    top_success_comments: List[str]
    top_confusion_comments: List[str]
    recommendations: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class SatisfactionAnalyzer:
    """
    Skill 4: Viewer Satisfaction Signal Analyzer
    
    Measures how satisfied viewers are with the content by analyzing:
    - Success indicators ("it worked", "finally understood")
    - Confusion signals ("I don't get it", "what do you mean")
    - Return viewers (same person commenting on multiple videos)
    - Engagement quality (likes/comments ratio, response depth)
    """
    
    # Patterns indicating successful implementation/understanding
    SUCCESS_PATTERNS = [
        r'\b(it\s+work(s|ed)?)\b',
        r'\b(this\s+work(s|ed)?)\b',
        r'\b(finally\s+(understand|got it|works))\b',
        r'\b(thank(s| you).*help(ed)?)\b',
        r'\b(solved\s+(my|the)\s+problem)\b',
        r'\b(exactly\s+what\s+i\s+need(ed)?)\b',
        r'\b(life\s*saver)\b',
        r'\b(game\s*changer)\b',
        r'\b(this\s+is\s+(exactly|perfect))\b',
        r'\b(saved\s+(me|my))\b',
        r'\b(now\s+i\s+(understand|get it))\b',
        r'\b(best\s+explanation)\b',
        r'\b(clear(ly)?\s+explain(ed)?)\b',
    ]
    
    # Patterns indicating confusion/frustration
    CONFUSION_PATTERNS = [
        r'\b(i\s+don\'?t\s+(understand|get it))\b',
        r'\b(what\s+do\s+you\s+mean)\b',
        r'\b(confus(ed|ing))\b',
        r'\b(lost\s+me)\b',
        r'\b(too\s+fast)\b',
        r'\b(can\'?t\s+follow)\b',
        r'\b(not\s+clear)\b',
        r'\b(doesn\'?t\s+(work|make sense))\b',
        r'\b(still\s+(confused|don\'t understand))\b',
        r'\b(where\s+did\s+you)\b',
        r'\b(how\s+did\s+you)\b',  # Indicates missing step
        r'\b(skip(ped)?.*step)\b',
    ]
    
    def __init__(self):
        # Compile regex patterns for performance
        self.success_regex = [re.compile(p, re.IGNORECASE) for p in self.SUCCESS_PATTERNS]
        self.confusion_regex = [re.compile(p, re.IGNORECASE) for p in self.CONFUSION_PATTERNS]
    
    def analyze_satisfaction(self, 
                            videos_data: List[Dict],
                            channel_engagement_rate: float = 5.0) -> SatisfactionResult:
        """
        Analyze satisfaction signals across all videos.
        
        Args:
            videos_data: List of video dicts with 'comments', 'view_count', 'like_count'
            channel_engagement_rate: Average channel engagement rate for comparison
            
        Returns:
            SatisfactionResult with comprehensive satisfaction metrics
        """
        all_comments = []
        author_video_map = {}  # Track authors across videos
        total_views = 0
        total_likes = 0
        total_comment_count = 0
        
        # Collect all comments and track authors
        for video in videos_data:
            video_id = video.get('video_info', {}).get('id', video.get('video_id', ''))
            comments = video.get('comments', [])
            
            total_views += video.get('video_info', {}).get('view_count', 0) or video.get('view_count', 0)
            total_likes += video.get('video_info', {}).get('like_count', 0) or video.get('like_count', 0)
            total_comment_count += len(comments)
            
            for comment in comments:
                all_comments.append(comment)
                author = comment.get('author', '')
                if author:
                    if author not in author_video_map:
                        author_video_map[author] = set()
                    author_video_map[author].add(video_id)
        
        if not all_comments:
            return self._empty_result()
        
        # 1. Detect success comments
        success_comments = self._detect_success_comments(all_comments)
        
        # 2. Detect confusion signals
        confusion_comments = self._detect_confusion_comments(all_comments)
        
        # 3. Calculate return viewer ratio
        return_viewer_ratio = self._calculate_return_viewer_ratio(author_video_map)
        
        # 4. Calculate engagement quality score (0-100)
        engagement_quality = self._calculate_engagement_quality(
            total_views, total_likes, total_comment_count, 
            len(success_comments), channel_engagement_rate
        )
        
        # 5. Calculate retention proxy (based on return viewers and comment depth)
        retention_proxy = self._calculate_retention_proxy(
            return_viewer_ratio, all_comments
        )
        
        # 6. Calculate implementation success score
        implementation_success = self._calculate_implementation_score(
            len(success_comments), len(confusion_comments), len(all_comments)
        )
        
        # 7. Calculate clarity score
        clarity_score = self._calculate_clarity_score(
            len(confusion_comments), len(all_comments)
        )
        
        # 8. Final Satisfaction Index formula
        si = (engagement_quality * 0.6) + (retention_proxy * 0.3) + (implementation_success * 0.1)
        si = min(100, max(0, si))  # Clamp to 0-100
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            si, clarity_score, return_viewer_ratio, 
            len(success_comments), len(confusion_comments)
        )
        
        return SatisfactionResult(
            satisfaction_index=round(si, 1),
            engagement_quality_score=round(engagement_quality, 1),
            retention_proxy_score=round(retention_proxy, 1),
            implementation_success_score=round(implementation_success, 1),
            success_comment_count=len(success_comments),
            confusion_signal_count=len(confusion_comments),
            return_viewer_ratio=round(return_viewer_ratio, 2),
            clarity_score=round(clarity_score, 1),
            top_success_comments=[c['text'][:100] for c in success_comments[:5]],
            top_confusion_comments=[c['text'][:100] for c in confusion_comments[:5]],
            recommendations=recommendations
        )
    
    def _detect_success_comments(self, comments: List[Dict]) -> List[Dict]:
        """Find comments indicating successful understanding/implementation."""
        success = []
        for comment in comments:
            text = comment.get('text', '')
            for regex in self.success_regex:
                if regex.search(text):
                    success.append(comment)
                    break
        # Sort by likes for most impactful
        success.sort(key=lambda c: c.get('likes', 0), reverse=True)
        return success
    
    def _detect_confusion_comments(self, comments: List[Dict]) -> List[Dict]:
        """Find comments indicating confusion or frustration."""
        confused = []
        for comment in comments:
            text = comment.get('text', '')
            for regex in self.confusion_regex:
                if regex.search(text):
                    confused.append(comment)
                    break
        confused.sort(key=lambda c: c.get('likes', 0), reverse=True)
        return confused
    
    def _calculate_return_viewer_ratio(self, author_video_map: Dict[str, set]) -> float:
        """Calculate what % of commenters appear on multiple videos."""
        if not author_video_map:
            return 0.0
        
        return_viewers = sum(1 for videos in author_video_map.values() if len(videos) > 1)
        return return_viewers / len(author_video_map)
    
    def _calculate_engagement_quality(self, views: int, likes: int, 
                                       comments: int, success_count: int,
                                       benchmark_rate: float) -> float:
        """Calculate engagement quality score (0-100)."""
        if views == 0:
            return 0.0
        
        # Like-to-view ratio
        like_ratio = (likes / views) * 100
        
        # Comment-to-view ratio
        comment_ratio = (comments / views) * 1000  # Per 1000 views
        
        # Success signal density
        success_ratio = (success_count / max(comments, 1)) * 100
        
        # Compare to benchmark
        relative_engagement = min(100, (like_ratio / max(benchmark_rate, 1)) * 50)
        
        # Weighted combination
        score = (relative_engagement * 0.4) + (min(50, comment_ratio * 5) * 0.3) + (success_ratio * 0.3)
        return min(100, score)
    
    def _calculate_retention_proxy(self, return_ratio: float, 
                                   comments: List[Dict]) -> float:
        """Estimate retention from return viewers and comment depth."""
        # Return viewer contribution (up to 50 points)
        return_score = return_ratio * 100
        
        # Comment depth (longer comments = more engaged viewers)
        if comments:
            avg_length = sum(len(c.get('text', '')) for c in comments) / len(comments)
            depth_score = min(50, avg_length / 2)  # Cap at 50
        else:
            depth_score = 0
        
        return (return_score * 0.6) + (depth_score * 0.4)
    
    def _calculate_implementation_score(self, success: int, confusion: int, 
                                         total: int) -> float:
        """Score based on success vs confusion ratio."""
        if total == 0:
            return 50.0  # Neutral
        
        # Success ratio weighted heavily
        success_rate = (success / total) * 100
        confusion_rate = (confusion / total) * 100
        
        # Net score: success minus confusion penalty
        score = 50 + (success_rate * 2) - (confusion_rate * 3)
        return max(0, min(100, score))
    
    def _calculate_clarity_score(self, confusion_count: int, total: int) -> float:
        """Score content clarity (inverse of confusion)."""
        if total == 0:
            return 80.0
        
        confusion_rate = confusion_count / total
        # Low confusion = high clarity
        return max(0, 100 - (confusion_rate * 500))
    
    def _generate_recommendations(self, si: float, clarity: float,
                                   return_ratio: float, success: int,
                                   confusion: int) -> List[str]:
        """Generate actionable recommendations."""
        recs = []
        
        if clarity < 60:
            recs.append("High confusion signals detected - consider adding more step-by-step breakdowns")
        
        if return_ratio < 0.05:
            recs.append("Low return viewer ratio - create series content to build habit")
        
        if confusion > success:
            recs.append("More confusion than success signals - slow down explanations")
        
        if si < 50:
            recs.append("Satisfaction index below average - focus on addressing common pain points")
        elif si > 80:
            recs.append("Excellent satisfaction! Replicate this format in future content")
        
        if not recs:
            recs.append("Satisfaction metrics are healthy - maintain current approach")
        
        return recs
    
    def _empty_result(self) -> SatisfactionResult:
        """Return empty result when no data available."""
        return SatisfactionResult(
            satisfaction_index=0,
            engagement_quality_score=0,
            retention_proxy_score=0,
            implementation_success_score=0,
            success_comment_count=0,
            confusion_signal_count=0,
            return_viewer_ratio=0,
            clarity_score=0,
            top_success_comments=[],
            top_confusion_comments=[],
            recommendations=["Not enough data for satisfaction analysis"]
        )


# === Quick test ===
if __name__ == "__main__":
    print("🧪 Testing Satisfaction Analyzer...")
    
    analyzer = SatisfactionAnalyzer()
    
    # Sample data
    test_data = [
        {
            'video_info': {'id': '1', 'view_count': 10000, 'like_count': 500},
            'comments': [
                {'author': 'User1', 'text': 'This finally works! Thank you so much!', 'likes': 50},
                {'author': 'User2', 'text': 'Best explanation I have ever seen', 'likes': 30},
                {'author': 'User3', 'text': 'I dont understand the second part', 'likes': 5},
                {'author': 'User1', 'text': 'Great follow up video', 'likes': 10},
            ]
        },
        {
            'video_info': {'id': '2', 'view_count': 8000, 'like_count': 400},
            'comments': [
                {'author': 'User1', 'text': 'Another great one!', 'likes': 20},
                {'author': 'User4', 'text': 'Saved me hours of work', 'likes': 40},
            ]
        }
    ]
    
    result = analyzer.analyze_satisfaction(test_data)
    
    print(f"\n📊 Results:")
    print(f"   Satisfaction Index: {result.satisfaction_index}")
    print(f"   Success Comments: {result.success_comment_count}")
    print(f"   Confusion Signals: {result.confusion_signal_count}")
    print(f"   Return Viewer Ratio: {result.return_viewer_ratio:.0%}")
    print(f"   Clarity Score: {result.clarity_score}")
    print(f"\n   Recommendations:")
    for rec in result.recommendations:
        print(f"      • {rec}")
