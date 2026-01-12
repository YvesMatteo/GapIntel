"""
Premium Analysis - Hook Analyzer
Analyzes the first 60 seconds of videos to identify patterns that drive views.

Features:
- Downloads only first minute of audio (fast)
- Transcribes hooks using Whisper tiny model
- Extracts hook patterns (questions, statements, teasers, CTAs)
- Correlates hook style with view performance using ML
"""

import os
import re
import tempfile
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import numpy as np

# Try to import whisper, handle if not available
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️ Whisper not available, hook analysis will be limited")


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
    
    # Hook pattern detection regexes
    HOOK_PATTERNS = {
        'question': [
            r'^(what|why|how|when|where|who|which|can|do|does|did|is|are|was|were|have|has|will|would|could|should)\b',
            r'\?$',
        ],
        'statement': [
            r'^(today|in this video|i\'m going to|let me show|here\'s|this is)',
            r'^(the truth|the secret|the real|the best|the worst)',
        ],
        'teaser': [
            r'^(you won\'t believe|wait until|by the end|stick around|don\'t go)',
            r'(reveal|secret|hidden|trick|hack)',
        ],
        'story': [
            r'^(so|okay so|alright so|yesterday|last week|i was)',
            r'^(imagine|picture this|let me tell you)',
        ],
        'cta': [
            r'(subscribe|like|comment|hit the bell|notification)',
            r'(before we start|quick reminder)',
        ],
        'shock': [
            r'^(oh my|what the|holy|insane|crazy|unbelievable)',
            r'(broke|destroyed|ruined|exposed|called out)',
        ],
    }
    
    def __init__(self, whisper_model: str = 'tiny'):
        """
        Initialize the hook analyzer.
        
        Args:
            whisper_model: Whisper model size ('tiny', 'base', 'small')
        """
        self.whisper_model_name = whisper_model
        self._whisper_model = None
        
    def _get_whisper_model(self):
        """Lazy load whisper model."""
        if self._whisper_model is None and WHISPER_AVAILABLE:
            print(f"📥 Loading Whisper {self.whisper_model_name} model...")
            self._whisper_model = whisper.load_model(self.whisper_model_name)
        return self._whisper_model
    
    def download_first_minute(self, video_id: str, output_dir: str = None) -> Optional[str]:
        """
        Download only the first 60 seconds of audio from a YouTube video.
        
        Args:
            video_id: YouTube video ID
            output_dir: Directory to save audio file
            
        Returns:
            Path to audio file or None if failed
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
            
        output_path = Path(output_dir) / f"{video_id}_hook.mp3"
        
        try:
            # Use yt-dlp with duration limit
            cmd = [
                'yt-dlp',
                '-x',  # Extract audio
                '--audio-format', 'mp3',
                '--audio-quality', '5',  # Lower quality = faster
                '--download-sections', '*0:00-1:00',  # First minute only
                '-o', str(output_path),
                f'https://youtube.com/watch?v={video_id}'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            if output_path.exists():
                return str(output_path)
            else:
                print(f"⚠️ Failed to download hook for {video_id}")
                return None
                
        except subprocess.TimeoutExpired:
            print(f"⏱️ Timeout downloading hook for {video_id}")
            return None
        except Exception as e:
            print(f"❌ Error downloading hook for {video_id}: {e}")
            return None
    
    def transcribe_hook(self, audio_path: str) -> Tuple[str, float]:
        """
        Transcribe the hook audio using Whisper.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Tuple of (transcript, duration_seconds)
        """
        model = self._get_whisper_model()
        if model is None:
            return "", 0.0
            
        try:
            result = model.transcribe(audio_path, language='en', fp16=False)
            transcript = result.get('text', '').strip()
            
            # Calculate actual duration from segments
            segments = result.get('segments', [])
            duration = segments[-1]['end'] if segments else 0.0
            
            return transcript, duration
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return "", 0.0
    
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
    
    def extract_opening_words(self, transcript: str, n_words: int = 5) -> List[str]:
        """Extract the first N words of the hook."""
        words = transcript.split()[:n_words]
        return [w.lower().strip('.,!?') for w in words]
    
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
        Analyze a single video's hook.
        
        Args:
            video_data: Dict with video_id, title, view_count
            avg_views: Channel average views for scoring
            
        Returns:
            HookAnalysisResult or None if analysis failed
        """
        video_id = video_data.get('video_id')
        
        # Download first minute
        audio_path = self.download_first_minute(video_id)
        if not audio_path:
            return None
            
        try:
            # Transcribe
            transcript, duration = self.transcribe_hook(audio_path)
            if not transcript:
                return None
                
            # Detect patterns
            patterns = self.detect_patterns(transcript)
            
            # Extract opening words
            opening_words = self.extract_opening_words(transcript)
            
            # Calculate score
            view_count = video_data.get('view_count', 0)
            hook_score = self.calculate_hook_score(patterns, view_count, avg_views)
            
            return HookAnalysisResult(
                video_id=video_id,
                video_title=video_data.get('title', ''),
                view_count=view_count,
                hook_transcript=transcript,
                patterns=patterns,
                hook_score=hook_score,
                opening_words=opening_words,
                hook_duration_seconds=duration,
            )
            
        finally:
            # Cleanup
            if audio_path and Path(audio_path).exists():
                try:
                    Path(audio_path).unlink()
                except:
                    pass
    
    def analyze_videos(self, videos_data: List[dict], max_videos: int = 20) -> List[HookAnalysisResult]:
        """
        Analyze hooks for multiple videos.
        
        Args:
            videos_data: List of video dicts (can include 'transcript' for fallback)
            max_videos: Maximum videos to analyze
            
        Returns:
            List of HookAnalysisResult
        """
        videos = videos_data[:max_videos]
        
        # Calculate average views
        total_views = sum(v.get('view_count', 0) for v in videos)
        avg_views = total_views / len(videos) if videos else 1
        
        results = []
        for i, video in enumerate(videos):
            print(f"🎣 Analyzing hook {i+1}/{len(videos)}: {video.get('title', '')[:50]}...")
            
            # Try audio-based analysis first (if Whisper available)
            result = None
            if WHISPER_AVAILABLE:
                result = self.analyze_single_video(video, avg_views)
            
            # Fallback: Use existing transcript if available
            if result is None and video.get('transcript'):
                result = self.analyze_from_transcript(video, avg_views)
                
            if result:
                results.append(result)
                
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
        
        # Generate recommendations
        recommendations = []
        if best_patterns:
            top_pattern = best_patterns[0]['pattern']
            recommendations.append(f"Use '{top_pattern}' hooks - they average {best_patterns[0]['avg_views']:,.0f} views")
        
        if word_freq:
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:3]
            recommendations.append(f"Popular opening words: {', '.join(w[0] for w in top_words)}")
        
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
