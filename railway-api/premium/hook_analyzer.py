"""
Premium Analysis - Hook Analyzer
Analyzes the first 60 seconds of videos to identify patterns that drive views.

Features:
- Uses YouTube captions (instant, no audio download needed)
- Extracts hook patterns (questions, statements, teasers, CTAs)
- Correlates hook style with view performance using ML
- Skips videos without captions (no transcription fallback)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# Try to import youtube-transcript-api
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    CAPTIONS_AVAILABLE = True
except ImportError:
    CAPTIONS_AVAILABLE = False
    print("⚠️ youtube-transcript-api not available, hook analysis will be limited")


@dataclass
class HookPattern:
    """Identified hook pattern from video opening."""
    pattern_type: str  # 'question', 'statement', 'teaser', 'story', 'cta', 'shock'
    text: str
    confidence: float = 0.0


@dataclass
class HookAnalysisResult:
    """Complete hook analysis for a single video."""
    video_id: str
    video_title: str
    view_count: int
    hook_transcript: str
    patterns: List[HookPattern] = field(default_factory=list)
    hook_score: float = 0.0
    opening_words: List[str] = field(default_factory=list)
    hook_duration_seconds: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            'video_id': self.video_id,
            'video_title': self.video_title,
            'view_count': self.view_count,
            'hook_transcript': self.hook_transcript,
            'patterns': [{'type': p.pattern_type, 'text': p.text, 'confidence': p.confidence} for p in self.patterns],
            'hook_score': self.hook_score,
            'opening_words': self.opening_words,
            'hook_duration_seconds': self.hook_duration_seconds,
        }


@dataclass 
class HookInsights:
    """Aggregated insights from all hook analyses."""
    total_videos: int
    avg_hook_score: float
    best_patterns: List[Dict]  # Pattern type -> avg views correlation
    recommended_hooks: List[str]
    opening_word_frequency: Dict[str, int]
    pattern_performance: Dict[str, float]  # Pattern type -> avg view score
    top_performing_hooks: List[Dict]
    pattern_examples: Dict[str, List[Dict]] = None  # Pattern type -> [example hooks with quotes]
    
    def __post_init__(self):
        if self.pattern_examples is None:
            self.pattern_examples = {}
    
    def to_dict(self) -> dict:
        return {
            'total_videos': self.total_videos,
            'avg_hook_score': self.avg_hook_score,
            'best_patterns': self.best_patterns,
            'recommended_hooks': self.recommended_hooks,
            'opening_word_frequency': self.opening_word_frequency,
            'pattern_performance': self.pattern_performance,
            'top_performing_hooks': self.top_performing_hooks,
            'pattern_examples': self.pattern_examples or {},
        }


class HookAnalyzer:
    """
    Analyzes video hooks (first 60 seconds) to find patterns that drive views.
    
    Usage:
        analyzer = HookAnalyzer()
        results = analyzer.analyze_videos(videos_data)
        insights = analyzer.generate_insights(results)
    """
    
    # Hook pattern detection regexes - comprehensive patterns for YouTube hooks
    HOOK_PATTERNS = {
        'question': [
            r'^(what|why|how|when|where|who|which|can|do|does|did|is|are|was|were|have|has|will|would|could|should)\b',
            r'\?',  # Contains a question mark
            r'^(ever wonder|have you ever|did you know|do you know|want to know)',
        ],
        'statement': [
            r'^(today|in this video|i\'m going to|let me show|here\'s|this is)',
            r'^(the truth|the secret|the real|the best|the worst)',
            r'^(i\'ve|i have|we\'re|we have|this video is about)',
        ],
        'teaser': [
            r'^(you won\'t believe|wait until|by the end|stick around|don\'t go)',
            r'(reveal|secret|hidden|trick|hack|nobody tells you)',
            r'(at the end|stay tuned|keep watching)',
        ],
        'story': [
            r'^(so|okay so|alright so|yesterday|last week|i was|the other day)',
            r'^(imagine|picture this|let me tell you|story time)',
            r'^(this happened|something happened|i need to tell you)',
        ],
        'cta': [
            r'\b(subscribe|like the video|comment below|hit the bell|notification)',
            r'(before we start|quick reminder|make sure to)',
            r'(drop a like|smash that|leave a comment)',
        ],
        'shock': [
            r'^(oh my|what the|holy|insane|crazy|unbelievable|no way)',
            r'(broke|destroyed|ruined|exposed|called out|went wrong)',
            r'(can\'t believe|never expected|shocked|speechless)',
        ],
        'challenge': [
            r'(i tried|i tested|i attempted|challenge|experiment)',
            r'(for 24 hours|for a week|for a month|for one day)',
            r'(only using|without|i bet|dare)',
        ],
        'bold_claim': [
            r'(best|worst|biggest|smallest|fastest|easiest|hardest) (way|method|mistake)',
            r'(number one|#1|\d+\s*(ways|tips|secrets|reasons|mistakes|things))',
            r'(you need to|you must|you should|everyone should)',
        ],
        'personal': [
            r'^(i|my|me|we|our)\b',
            r'(my experience|my story|my journey|my take|my opinion)',
            r'(personal|honest|real talk|real thoughts)',
        ],
        'urgency': [
            r'(right now|immediately|asap|urgent|hurry|limited)',
            r'(before it\'s too late|don\'t miss|last chance|only today)',
            r'(breaking|just happened|just dropped|just released)',
        ],
        'educational': [
            r'(learn|teach|explain|understand|guide|tutorial|how to)',
            r'(step by step|complete guide|everything you need)',
            r'(beginner|advanced|pro tips|masterclass)',
        ],
        'controversy': [
            r'(unpopular opinion|hot take|controversial|debate)',
            r'(wrong|lying|scam|fraud|fake|overrated|underrated)',
            r'(rant|truth about|expose|the problem with)',
        ],
    }
    
    def __init__(self, whisper_model: str = 'tiny'):
        """
        Initialize the hook analyzer.
        
        Args:
            whisper_model: Ignored (kept for API compatibility)
        """
        # Note: whisper_model is ignored - we only use YouTube captions now
        pass
    
    def fetch_captions(self, video_id: str, max_chars: int = 500) -> Optional[str]:
        """
        Fetch YouTube captions for a video (first ~60 seconds based on char count).
        
        Args:
            video_id: YouTube video ID
            max_chars: Maximum characters to fetch (approx first 60 seconds)
            
        Returns:
            Caption text or None if no captions available
        """
        if not CAPTIONS_AVAILABLE:
            return None
            
        try:
            # New API (v1.2.3+): Create instance and fetch directly
            api = YouTubeTranscriptApi()
            transcript = api.fetch(video_id)
            
            # Build the hook text (first ~60 seconds / max_chars)
            hook_text = ""
            for snippet in transcript:
                # Stop after roughly 60 seconds of content
                if snippet.start > 60:
                    break
                hook_text += snippet.text + " "
                if len(hook_text) > max_chars:
                    break
            
            return hook_text.strip() if hook_text.strip() else None
            
        except Exception as e:
            # Handle various error cases (no captions, disabled, etc.)
            error_str = str(e).lower()
            if 'disabled' in error_str or 'not found' in error_str or 'no transcript' in error_str:
                return None
            print(f"⚠️ Caption fetch error for {video_id}: {e}")
            return None
    
    def detect_patterns(self, transcript: str) -> List[HookPattern]:
        """
        Detect hook patterns in the transcript.
        
        Args:
            transcript: Hook transcript text
            
        Returns:
            List of detected HookPattern objects
        """
        patterns = []
        transcript_lower = transcript.lower()
        
        for pattern_type, regexes in self.HOOK_PATTERNS.items():
            for regex in regexes:
                if re.search(regex, transcript_lower, re.IGNORECASE):
                    # Extract matching text
                    match = re.search(regex, transcript_lower, re.IGNORECASE)
                    matched_text = match.group(0) if match else ""
                    
                    patterns.append(HookPattern(
                        pattern_type=pattern_type,
                        text=matched_text,
                        confidence=0.8  # Base confidence
                    ))
                    break  # Only count each pattern type once
                    
        return patterns
    
    def extract_opening_words(self, transcript: str, n_words: int = 8) -> List[str]:
        """Extract the first N meaningful words of the hook, filtering out noise."""
        # Filter out common caption noise patterns
        noise_patterns = [
            r'\[.*?\]',  # [music], [applause], etc.
            r'\(.*?\)',  # (music), etc.
            r'♪.*?♪',   # music notes
            r'^\s*$',   # empty lines
        ]
        
        cleaned = transcript
        for pattern in noise_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Split and filter
        words = cleaned.split()[:n_words]
        # Filter out single-character words and clean up
        meaningful_words = [
            w.lower().strip('.,!?:;-"\'')
            for w in words
            if len(w.strip('.,!?:;-"\'')) > 1
        ]
        return meaningful_words[:5]  # Return max 5 words
    
    def calculate_hook_score(self, patterns: List[HookPattern], view_count: int, avg_views: float) -> float:
        """
        Calculate a hook effectiveness score.
        
        Uses pattern diversity and view performance.
        """
        if avg_views == 0:
            view_ratio = 1.0
        else:
            view_ratio = view_count / avg_views
            
        # Pattern diversity score (0-1)
        unique_patterns = len(set(p.pattern_type for p in patterns))
        pattern_score = min(unique_patterns / 3, 1.0)  # Optimal: 3 different patterns
        
        # Combined score
        hook_score = (pattern_score * 0.4 + min(view_ratio, 2.0) / 2 * 0.6) * 100
        
        return round(hook_score, 1)
    
    def analyze_single_video(self, video_data: dict, avg_views: float) -> Optional[HookAnalysisResult]:
        """
        Analyze a single video's hook using YouTube captions.
        
        Args:
            video_data: Dict with video_id, title, view_count
            avg_views: Channel average views for scoring
            
        Returns:
            HookAnalysisResult or None if no captions available
        """
        video_id = video_data.get('video_id')
        if not video_id:
            return None
        
        # Fetch captions (instant - no audio download needed)
        caption_text = self.fetch_captions(video_id)
        if not caption_text:
            print(f"   ⚠️ No captions for {video_id} - skipping")
            return None
            
        # Detect patterns
        patterns = self.detect_patterns(caption_text)
        
        # Extract opening words
        opening_words = self.extract_opening_words(caption_text)
        
        # Calculate score
        view_count = video_data.get('view_count', 0)
        hook_score = self.calculate_hook_score(patterns, view_count, avg_views)
        
        return HookAnalysisResult(
            video_id=video_id,
            video_title=video_data.get('title', ''),
            view_count=view_count,
            hook_transcript=caption_text[:300],  # First 300 chars as hook
            patterns=patterns,
            hook_score=hook_score,
            opening_words=opening_words,
            hook_duration_seconds=60.0,  # Approximate
        )
    
    def analyze_videos(self, videos_data: List[dict], max_videos: int = 20) -> List[HookAnalysisResult]:
        """
        Analyze hooks for multiple videos using YouTube captions.
        
        Videos without captions are skipped (no transcription fallback).
        
        Args:
            videos_data: List of video dicts
            max_videos: Maximum videos to analyze
            
        Returns:
            List of HookAnalysisResult (only for videos with captions)
        """
        videos = videos_data[:max_videos]
        
        # Calculate average views
        total_views = sum(v.get('view_count', 0) for v in videos)
        avg_views = total_views / len(videos) if videos else 1
        
        results = []
        skipped = 0
        
        # Helper for parallel execution
        def process_one(idx, video):
            print(f"🎣 Analyzing hook {idx+1}/{len(videos)}: {video.get('title', '')[:50]}...")
            return self.analyze_single_video(video, avg_views)

        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(process_one, i, v): i for i, v in enumerate(videos)}
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                    else:
                        skipped += 1
                except Exception as e:
                    print(f"   ⚠️ Hook analysis error: {e}")
                    skipped += 1
        
        if skipped > 0:
            print(f"   ℹ️ Skipped {skipped} videos (no captions available)")
                
        return results
    
    def analyze_from_transcript(self, video_data: dict, avg_views: float) -> Optional[HookAnalysisResult]:
        """
        Analyze hook from existing transcript data (fallback when audio unavailable).
        
        Args:
            video_data: Dict with video_id, title, view_count, transcript
            avg_views: Channel average views for scoring
            
        Returns:
            HookAnalysisResult or None
        """
        transcript = video_data.get('transcript', '')
        if not transcript:
            return None
        
        # Use first ~500 chars as hook (approximately first 60 seconds)
        hook_text = transcript[:500]
        
        # Detect patterns
        patterns = self.detect_patterns(hook_text)
        
        # Extract opening words
        opening_words = self.extract_opening_words(hook_text)
        
        # Calculate score
        view_count = video_data.get('view_count', 0)
        hook_score = self.calculate_hook_score(patterns, view_count, avg_views)
        
        return HookAnalysisResult(
            video_id=video_data.get('video_id', ''),
            video_title=video_data.get('title', ''),
            view_count=view_count,
            hook_transcript=hook_text,
            patterns=patterns,
            hook_score=hook_score,
            opening_words=opening_words,
            hook_duration_seconds=60.0,  # Estimated
        )
    
    def generate_insights(self, results: List[HookAnalysisResult]) -> HookInsights:
        """
        Generate aggregated insights from all hook analyses.
        
        Args:
            results: List of HookAnalysisResult
            
        Returns:
            HookInsights with recommendations
        """
        if not results:
            return HookInsights(
                total_videos=0,
                avg_hook_score=0,
                best_patterns=[],
                recommended_hooks=[],
                opening_word_frequency={},
                pattern_performance={},
                top_performing_hooks=[],
            )
        
        # Calculate averages
        avg_score = sum(r.hook_score for r in results) / len(results)
        
        # Pattern performance analysis
        pattern_views = {}  # pattern_type -> [view_counts]
        for result in results:
            for pattern in result.patterns:
                if pattern.pattern_type not in pattern_views:
                    pattern_views[pattern.pattern_type] = []
                pattern_views[pattern.pattern_type].append(result.view_count)
        
        # Average views per pattern
        pattern_performance = {
            ptype: sum(views) / len(views) 
            for ptype, views in pattern_views.items()
        }
        
        # Sort patterns by performance
        best_patterns = sorted(
            [{'pattern': k, 'avg_views': v} for k, v in pattern_performance.items()],
            key=lambda x: x['avg_views'],
            reverse=True
        )
        
        # Opening word frequency
        word_freq = {}
        for result in results:
            for word in result.opening_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Top performing hooks with full transcripts for examples
        top_hooks = sorted(results, key=lambda x: x.view_count, reverse=True)[:5]
        top_performing = [
            {
                'video_id': h.video_id,
                'title': h.video_title,
                'views': h.view_count,
                'hook_score': h.hook_score,
                'patterns': [p.pattern_type for p in h.patterns],
                'opening': ' '.join(h.opening_words),
                'hook_transcript': h.hook_transcript[:300],  # First 300 chars as example
                'thumbnail_url': f"https://img.youtube.com/vi/{h.video_id}/maxresdefault.jpg",
            }
            for h in top_hooks
        ]
        
        # Add pattern examples with exact quotes
        pattern_examples = {}  # pattern_type -> [example hooks]
        for result in results:
            for pattern in result.patterns:
                ptype = pattern.pattern_type
                if ptype not in pattern_examples:
                    pattern_examples[ptype] = []
                if len(pattern_examples[ptype]) < 3:  # Keep top 3 examples per pattern
                    pattern_examples[ptype].append({
                        'video_title': result.video_title,
                        'views': result.view_count,
                        'hook_quote': result.hook_transcript[:200],  # Exact quote
                        'video_id': result.video_id,
                    })
        
        # Generate recommendations - more comprehensive and actionable
        recommendations = []
        
        # 1. Best performing pattern
        if best_patterns:
            top_pattern = best_patterns[0]['pattern']
            recommendations.append(f"Use '{top_pattern}' hooks - they average {best_patterns[0]['avg_views']:,.0f} views")
        
        # 2. Top opening words (filter out noise)
        if word_freq:
            # Filter noise words
            noise_words = {'um', 'uh', 'like', 'so', 'and', 'the', 'a', 'to', 'i', 'you', 'we', 'it', 'is', 'ok', 'okay'}
            clean_freq = {w: c for w, c in word_freq.items() if w not in noise_words and len(w) > 2}
            if clean_freq:
                top_words = sorted(clean_freq.items(), key=lambda x: x[1], reverse=True)[:3]
                recommendations.append(f"Strong opening words: {', '.join(w[0] for w in top_words)}")
        
        # 3. Pattern-specific actionable tips
        pattern_tips = {
            'question': "Ask a direct question to hook viewers emotionally",
            'teaser': "Use teasers like 'by the end of this video...' to boost retention",
            'story': "Start with 'So...' to trigger storytelling mode in viewers",
            'bold_claim': "Make a bold claim in the first 5 seconds to stop scrollers",
            'challenge': "Challenge formats drive high engagement and shares",
            'shock': "Shock hooks work well but use sparingly to maintain authenticity",
            'personal': "Personal hooks ('I tried...') build connection with viewers",
            'urgency': "Urgency hooks drive immediate action but don't overuse",
            'educational': "Educational hooks work best with a clear promise of value",
            'controversy': "Controversial takes drive comments but manage expectations",
        }
        
        # Suggest underused patterns that typically perform well
        used_patterns = set(p['pattern'] for p in best_patterns) if best_patterns else set()
        high_value_patterns = ['question', 'teaser', 'bold_claim', 'story']
        missing = [p for p in high_value_patterns if p not in used_patterns]
        if missing:
            tip = pattern_tips.get(missing[0], f"Try using '{missing[0]}' hooks")
            recommendations.append(f"Try adding: {tip}")
        
        # 4. Hook score feedback
        if avg_score < 40:
            recommendations.append("Hook diversity is low - try combining 2-3 hook types per video")
        elif avg_score > 70:
            recommendations.append("Strong hook game! Your hooks are well-structured")
        
        return HookInsights(
            total_videos=len(results),
            avg_hook_score=round(avg_score, 1),
            best_patterns=best_patterns,
            recommended_hooks=recommendations,
            opening_word_frequency=word_freq,
            pattern_performance=pattern_performance,
            top_performing_hooks=top_performing,
            pattern_examples=pattern_examples,
        )


# === Quick test ===
if __name__ == "__main__":
    analyzer = HookAnalyzer(whisper_model='tiny')
    
    # Test pattern detection
    test_hooks = [
        "What if I told you that everything you know about trading is wrong?",
        "Today I'm going to show you the secret strategy that made me $10,000",
        "So yesterday something crazy happened...",
        "Before we start, make sure to subscribe and hit that bell!",
        "Oh my god, you guys won't believe what just happened",
    ]
    
    print("🧪 Testing pattern detection:")
    for hook in test_hooks:
        patterns = analyzer.detect_patterns(hook)
        print(f"\n  '{hook[:50]}...'")
        print(f"  → Patterns: {[p.pattern_type for p in patterns]}")
