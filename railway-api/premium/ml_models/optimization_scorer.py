"""
Optimization Scorer
===================

This module provides a heuristic-based scoring engine for YouTube videos (Title + Thumbnail).
It does NOT predict views/CTR directly (which requires historical data/CTR data).
Instead, it evaluates adherence to proven "Best Practices" derived from extensive research (RAG).

Outputs:
- Optimization Score (0-100)
- Detailed breakdown (Title Score, Thumbnail Score)
- Actionable Recommendations

References:
- thumbnail_rag_context.md (Research on colors, faces, text, composition)
- Title formula research (Transformation, Shock/Curiosity gaps, Lists)
"""

import re
import math
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

@dataclass
class OptimizationResult:
    total_score: float
    title_score: float
    thumbnail_score: float
    rating: str  # "Excellent", "Good", "Needs Improvement", "Poor"
    recommendations: List[str]
    positive_factors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_score': round(self.total_score, 1),
            'title_score': round(self.title_score, 1),
            'thumbnail_score': round(self.thumbnail_score, 1),
            'rating': self.rating,
            'recommendations': self.recommendations,
            'positive_factors': self.positive_factors
        }

class OptimizationScorer:
    """
    Scores video metadata based on RAG research heuristics.
    """
    
    # --- TITLE PATTERNS ---
    TRANSFORMATION_RE = re.compile(r'(\d+\s*→|\d+\s*to\s*\d+|before.+after|from\s+.+\s+to\s+.+)', re.I)
    SHOCKING_RE = re.compile(r'(shock|insane|crazy|never\s+seen|won\'t\s+believe|impossible|wtf)', re.I)
    VERSUS_RE = re.compile(r'(\bvs\.?\b|\bversus\b|compared\s+to|better\s+than)', re.I)
    LIST_RE = re.compile(r'^(\d+|top\s+\d+)\s', re.I)
    QUESTION_RE = re.compile(r'(who|what|when|where|why|how)\b', re.I)
    NEGATIVE_RE = re.compile(r'(stop|don\'t|never|mistake|worst|avoid|warning)', re.I)
    
    POWER_WORDS = {
        'secret', 'revealed', 'truth', 'exposed', 'hidden',
        'best', 'ultimate', 'free', 'proven', 'hacks',
        'mistakes', 'guide', 'tutorial', 'easy', 'fast'
    }

    # Dynamic RAG Path
    RAG_FILE_PATH = "/Users/yvesromano/Documents/Yves Abgabe/YouTube_CTR_Prediction_Guide.md"

    def __init__(self):
        # Defaults
        self.min_title_len = 30
        self.max_title_len = 65
        self.niche_rules = {}  # {niche_name: {power_words: [], patterns: []}}
        
        # Load rules from RAG file if it exists
        self.load_rag_rules()

    def load_rag_rules(self):
        """
        Parses RAG file for:
        1. Global Power Words (Table)
        2. Title Length
        3. Niche-Specific Rules
        """
        try:
            with open(self.RAG_FILE_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
                
            print(f"   📘 Loading RAG Rules from: {self.RAG_FILE_PATH}")
            
            # 1. Global Power Words
            power_matches = re.findall(r'\|\s*\*\*([A-Za-z\-]+)\*\*\s*\|', content)
            if power_matches:
                new_words = set(w.lower() for w in power_matches)
                self.POWER_WORDS.update(new_words)
                
            # 2. Title Length
            len_match = re.search(r'\*\*(\d+)-(\d+)\s*Characters\*\*', content)
            if len_match:
                self.min_title_len = int(len_match.group(1))
                self.max_title_len = int(len_match.group(2))

            # 3. Parse Niches (Simple keyword extraction from headers)
            # Looks for "#### [Niche Name]" followed by "Power Words: ..."
            niche_sections = re.split(r'####\s+', content)
            for section in niche_sections:
                lines = section.split('\n')
                niche_name = lines[0].strip()
                
                # Check if this section has power words
                pw_line = next((l for l in lines if "**Power Words**:" in l), None)
                if pw_line:
                    # Extract words after colon
                    words_str = pw_line.split(':', 1)[1]
                    niche_words = [w.strip().lower() for w in words_str.split(',')]
                    
                    self.niche_rules[niche_name.lower()] = {
                        'power_words': set(niche_words),
                        'name': niche_name
                    }
            
            print(f"      ✓ Loaded rules for {len(self.niche_rules)} niches: {list(self.niche_rules.keys())}")

        except FileNotFoundError:
            print(f"   ⚠️ RAG File not found at {self.RAG_FILE_PATH}. Using defauts.")
        except Exception as e:
            print(f"   ⚠️ Error loading RAG rules: {e}")


    def score_title(self, title: str, niche: str = "General") -> Tuple[float, List[str], List[str]]:
        """
        Score title on 0-100 scale.
        """
        if not title:
            return 0.0, ["Missing title"], []

        score = 60.0
        recs = []
        pros = []
        
        t_clean = title.strip()
        t_lower = t_clean.lower()
        char_count = len(t_clean)

        # 1. Length Optimization (Dynamic from RAG)
        if self.min_title_len <= char_count <= self.max_title_len:
            score += 10
            pros.append(f"Optimal title length ({self.min_title_len}-{self.max_title_len} chars)")
        elif char_count > 70:
            score -= 5
            recs.append(f"Title is too long ({char_count} chars).")
        elif char_count < 20:
            score -= 5
            recs.append("Title is too short.")

        # 2. Power Words (Global + Niche)
        # Check global
        found_power = [w for w in self.POWER_WORDS if w in t_lower]
        
        # Check niche specific
        niche_key = next((k for k in self.niche_rules if k in niche.lower() or niche.lower() in k), None)
        if niche_key:
            niche_data = self.niche_rules[niche_key]
            found_niche_power = [w for w in niche_data['power_words'] if w in t_lower]
            if found_niche_power:
                found_power.extend(found_niche_power)
                score += 10 # Bonus for niche-specific alignment
                pros.append(f"Uses {niche_data['name']} power words: {', '.join(found_niche_power)}")
        
        found_power = list(set(found_power)) # dedup
        
        if found_power:
            score += 5 * min(len(found_power), 2)
            pros.append(f"Uses power words: {', '.join(found_power)}")
        else:
            recs.append("Consider adding 'power words' to increase CTR.")

        # 3. Formulas & Hooks (Standard Checks)
        has_formula = False
        if self.TRANSFORMATION_RE.search(t_clean):
            score += 15
            pros.append("Uses 'Transformation' formula")
            has_formula = True
        elif self.SHOCKING_RE.search(t_clean):
            score += 15
            pros.append("Uses 'Shock/Curiosity' hook")
            has_formula = True
        elif self.VERSUS_RE.search(t_clean):
            score += 10
            pros.append("Uses 'Versus/Comparison' format")
            has_formula = True
        elif self.LIST_RE.search(t_clean):
            score += 10
            pros.append("Uses 'Listicle' format")
            has_formula = True
        elif self.NEGATIVE_RE.search(t_clean):
            score += 15 # Boosted based on Validation findings
            pros.append("Uses 'Negative/Warning' angle (Validated High Performance)")
            has_formula = True
            
        if not has_formula:
            recs.append("Title lacks a clear viral formula.")

        # 4. Formatting
        caps_ratio = sum(1 for c in t_clean if c.isupper()) / max(len(t_clean), 1)
        if caps_ratio > 0.8:
            score -= 5
            recs.append("Avoid ALL CAPS.")
            
        if '?' in t_clean or '!' in t_clean:
             score += 5
             pros.append("Uses punctuation hook")

        return min(max(score, 0), 100), recs, pros


    def score_thumbnail_description(self, desc: str) -> Tuple[float, List[str], List[str]]:
        """
        Score a text description of a thumbnail (Virtual Scoring).
        Used when generating new ideas without actual image files.
        """
        score = 60.0
        recs = []
        pros = []
        d_lower = desc.lower()
        
        # 1. Face Presence
        if 'face' in d_lower or 'person' in d_lower or 'eye contact' in d_lower:
            score += 10
            pros.append("Concept includes human element (face)")
            if 'emotion' in d_lower or 'shock' in d_lower or 'happy' in d_lower:
                score += 5
                pros.append("Concept specifies emotion")
        elif 'no face' not in d_lower:
             # Neutral if not specified, but usually we want faces
             pass

        # 2. Contrast/Color
        if 'contrast' in d_lower or 'bright' in d_lower or 'vibrant' in d_lower or 'red' in d_lower or 'yellow' in d_lower:
            score += 10
            pros.append("Concept specifies high contrast/vibrancy")
            
        # 3. Text
        if 'text' in d_lower:
            score += 5
            pros.append("Concept includes text overlay")
            
        # 4. Composition
        if 'arrow' in d_lower or 'circle' in d_lower:
            score += 5
            pros.append("Concept uses visual cues (arrow/circle)")
            
        return min(score, 95), recs, pros
        
    def score_thumbnail(self, features: Optional[Dict[str, Any]], description: Optional[str] = None) -> Tuple[float, List[str], List[str]]:
        """
        Score thumbnail based on features OR text description.
        """
        # Case A: Virtual Scoring (Description only)
        if not features and description:
            return self.score_thumbnail_description(description)

        # Case B: No Data
        if not features:
            return 50.0, ["Thumbnail data unavailable"], []

        # Case C: Real Feature Scoring (Existing Logic)
        # RAG-based Scoring Logic
        score = 50.0
        recs = []
        pros = []

        # 1. Colors (Contrast & Saturation)
        contrast = features.get('thumb_contrast_score', 0)
        
        if contrast > 0.3:
            score += 10
            pros.append("High contrast (pops on screen)")
        elif contrast < 0.15:
            score -= 10
            recs.append("Low contrast. Increase contrast.")
            
        saturation = features.get('thumb_avg_saturation', 0)
        if saturation > 0.4:
            score += 5
            pros.append("Vibrant colors")
        
        # 2. Composition
        complexity = features.get('thumb_visual_complexity', 0.5)
        if complexity < 0.4:
            score += 10
            pros.append("Clean composition")
        elif complexity > 0.8:
            score -= 10
            recs.append("Thumbnail appears cluttered.")

        # 3. Faces
        face_count = features.get('thumb_face_count', 0)
        if face_count == 1:
            score += 15
            pros.append("Single face focus (Optimal)")
        elif face_count >= 3:
            score -= 5
            recs.append("Too many faces.")
        
        # 4. Text Overlay
        rag_text_score = features.get('thumb_rag_text_score', 0)
        has_text = features.get('thumb_has_text', False)
        
        if rag_text_score > 70:
            score += 10
            pros.append("Text usage is optimized")
        elif rag_text_score < 40 and has_text:
             recs.append("Text might be too long.")

        # Mix RAG total if available
        rag_total = features.get('thumb_rag_total_score', 0)
        if rag_total > 0:
            score = (score * 0.6) + (rag_total * 0.4)

        return min(max(score, 0), 100), recs, pros

    def evaluate(self, title: str, 
                 thumbnail_features: Optional[Dict[str, Any]] = None,
                 thumbnail_description: Optional[str] = None,
                 niche: str = "General") -> OptimizationResult:
        """
        Main entry point for scoring.
        """
        t_score, t_recs, t_pros = self.score_title(title, niche)
        
        thumb_score = 0.0
        thumb_recs = []
        thumb_pros = []
        
        thumb_score, thumb_recs, thumb_pros = self.score_thumbnail(thumbnail_features, thumbnail_description)

        # Weighted Total: 60% Thumbnail, 40% Title
        # If we have EITHER features OR description, we count thumbnail weight
        has_thumb_data = (thumbnail_features and len(thumbnail_features) > 2) or thumbnail_description
        
        if has_thumb_data:
            total_score = (thumb_score * 0.6) + (t_score * 0.4)
        else:
            total_score = t_score # Fallback to title only
            thumb_recs.append("Thumbnail missing - Score based on Title only")
            
        # Rating
        if total_score >= 85: rating = "Excellent"
        elif total_score >= 70: rating = "Good"
        elif total_score >= 50: rating = "Needs Improvement"
        else: rating = "Poor"
        
        return OptimizationResult(
            total_score=total_score,
            title_score=t_score,
            thumbnail_score=thumb_score,
            rating=rating,
            recommendations=t_recs + thumb_recs,
            positive_factors=t_pros + thumb_pros
        )

# Example usage
if __name__ == "__main__":
    scorer = OptimizationScorer()
    
    # Test case
    test_title = "I Spent 50 Hours in VR - You Won't Believe What Happened!"
    test_thumb = {
        'thumb_contrast_score': 0.4,
        'thumb_avg_saturation': 0.5,
        'thumb_visual_complexity': 0.3,
        'thumb_face_count': 1,
        'thumb_rag_total_score': 85
    }
    
    res = scorer.evaluate(test_title, test_thumb)
    print(f"Total Score: {res.total_score} ({res.rating})")
    print(f"Recommendations: {res.recommendations}")
    print(f"Pros: {res.positive_factors}")
