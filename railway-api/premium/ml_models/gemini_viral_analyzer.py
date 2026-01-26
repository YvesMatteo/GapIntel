"""
Gemini Viral Analyzer - RAG-Based YouTube View Prediction

Uses Gemini 2.5 Flash for multi-modal analysis of:
- Thumbnail (visual analysis)
- Title (text analysis)
- Hook (psychological trigger detection)

Based on the YouTube View Prediction RAG methodology.
"""

import os
import json
import base64
import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GENERATIVE_AI_API_KEY"))


@dataclass
class ThumbnailAnalysis:
    score: float  # 0-10
    ctr_impact: str  # e.g., "+4%"
    visual_contrast: float
    face_presence: float
    emotion_intensity: float
    text_readability: float
    color_vibrancy: float
    alignment_with_content: float
    analysis_notes: str


@dataclass
class HookAnalysis:
    score: float  # 0-10
    avd_impact: str  # e.g., "+12%"
    information_gap: float
    emotional_authenticity: float
    open_loop_clarity: float
    personal_relevance: float
    value_proposition: float
    processing_ease: float
    psychological_triggers: List[str]
    analysis_notes: str


@dataclass
class TitleAnalysis:
    score: float  # 0-10
    ctr_impact: str  # e.g., "+2%"
    specificity: float
    number_inclusion: float
    curiosity_words: float
    personal_pronoun: float
    keyword_relevance: float
    title_hook_coherence: float
    analysis_notes: str


@dataclass
class AlternativeTitle:
    title: str
    hook_type: str
    expected_ctr_boost: str
    rationale: str


@dataclass
class ViralAnalysisResult:
    # Video details
    title: str
    niche: str
    niche_confidence: float
    channel_size: str
    channel_multiplier: float

    # Component analysis
    thumbnail: Optional[ThumbnailAnalysis]
    hook: HookAnalysis
    title_analysis: TitleAnalysis

    # Predicted performance
    predicted_views: int
    confidence_interval: str
    view_range_low: int
    view_range_high: int
    predicted_ctr: str
    predicted_avd: str
    phase_1_success_index: float

    # Recommendations
    thumbnail_recommendations: List[str]
    hook_recommendations: List[str]
    title_recommendations: List[str]
    strategy_recommendations: List[str]

    # Alternative titles
    alternative_titles: List[AlternativeTitle]

    # Benchmarks
    vs_niche_average: str
    competitive_positioning: str

    # Risks
    click_to_content_mismatch_risk: str
    saturation_risk: str
    algorithmic_risk: str

    # Meta
    overall_viral_score: int  # 0-100
    analysis_summary: str


# Channel size multipliers from RAG document
CHANNEL_SIZE_CONFIG = {
    "nano": {
        "range": "0-10K",
        "multiplier_low": 0.5,
        "multiplier_high": 0.8,
        "baseline_impressions": 100,
        "baseline_views_low": 10,
        "baseline_views_high": 500
    },
    "micro": {
        "range": "10K-100K",
        "multiplier_low": 0.8,
        "multiplier_high": 1.0,
        "baseline_impressions": 500,
        "baseline_views_low": 100,
        "baseline_views_high": 3000
    },
    "small": {
        "range": "100K-1M",
        "multiplier_low": 1.0,
        "multiplier_high": 1.5,
        "baseline_impressions": 2500,
        "baseline_views_low": 2000,
        "baseline_views_high": 20000
    },
    "large": {
        "range": "1M-10M",
        "multiplier_low": 1.5,
        "multiplier_high": 2.5,
        "baseline_impressions": 25000,
        "baseline_views_low": 20000,
        "baseline_views_high": 500000
    },
    "mega": {
        "range": "10M+",
        "multiplier_low": 2.0,
        "multiplier_high": 4.0,
        "baseline_impressions": 250000,
        "baseline_views_low": 500000,
        "baseline_views_high": 5000000
    }
}

# Niche-specific benchmarks from RAG document
NICHE_BENCHMARKS = {
    "gaming": {
        "baseline_ctr_low": 3,
        "baseline_ctr_avg": 8,
        "baseline_ctr_high": 14,
        "baseline_avd": 45,
        "engagement_factor": 1.0,
        "saturation_index": 1.2
    },
    "education": {
        "baseline_ctr_low": 4,
        "baseline_ctr_avg": 7,
        "baseline_ctr_high": 12,
        "baseline_avd": 55,
        "engagement_factor": 1.1,
        "saturation_index": 0.9
    },
    "entertainment": {
        "baseline_ctr_low": 5,
        "baseline_ctr_avg": 10,
        "baseline_ctr_high": 16,
        "baseline_avd": 35,
        "engagement_factor": 0.9,
        "saturation_index": 1.4
    },
    "tech": {
        "baseline_ctr_low": 3,
        "baseline_ctr_avg": 8,
        "baseline_ctr_high": 13,
        "baseline_avd": 50,
        "engagement_factor": 1.0,
        "saturation_index": 1.0
    },
    "review": {
        "baseline_ctr_low": 4,
        "baseline_ctr_avg": 9,
        "baseline_ctr_high": 14,
        "baseline_avd": 60,
        "engagement_factor": 1.05,
        "saturation_index": 1.1
    },
    "finance": {
        "baseline_ctr_low": 3,
        "baseline_ctr_avg": 7,
        "baseline_ctr_high": 12,
        "baseline_avd": 55,
        "engagement_factor": 1.05,
        "saturation_index": 0.95
    },
    "vlog": {
        "baseline_ctr_low": 4,
        "baseline_ctr_avg": 10,
        "baseline_ctr_high": 16,
        "baseline_avd": 50,
        "engagement_factor": 0.95,
        "saturation_index": 1.3
    }
}


class GeminiViralAnalyzer:
    """
    Multi-modal viral potential analyzer using Gemini 2.5 Flash.
    Implements the YouTube View Prediction RAG methodology.
    """

    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    async def analyze(
        self,
        title: str,
        hook: str,
        niche: str,
        channel_size: str,
        thumbnail_base64: Optional[str] = None
    ) -> ViralAnalysisResult:
        """
        Perform comprehensive viral potential analysis.

        Args:
            title: Video title (50-70 chars optimal)
            hook: Opening hook/first sentence
            niche: One of: gaming, education, entertainment, tech, review, finance, vlog
            channel_size: One of: nano, micro, small, large, mega
            thumbnail_base64: Optional base64-encoded thumbnail image

        Returns:
            ViralAnalysisResult with complete analysis
        """
        niche = niche.lower()
        channel_size = channel_size.lower()

        # Validate inputs
        if niche not in NICHE_BENCHMARKS:
            niche = "entertainment"  # Default fallback
        if channel_size not in CHANNEL_SIZE_CONFIG:
            channel_size = "micro"  # Default fallback

        # Build and execute the analysis prompt
        prompt = self._build_analysis_prompt(title, hook, niche, channel_size, thumbnail_base64 is not None)

        try:
            if thumbnail_base64:
                # Multi-modal analysis with image
                image_data = {
                    "mime_type": "image/jpeg",
                    "data": thumbnail_base64
                }
                response = self.model.generate_content([prompt, image_data])
            else:
                # Text-only analysis
                response = self.model.generate_content(prompt)

            # Parse the JSON response
            analysis_json = self._extract_json(response.text)

            # Calculate view predictions using RAG formulas
            result = self._build_result(analysis_json, title, niche, channel_size, thumbnail_base64 is not None)

            return result

        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            # Return a fallback result
            return self._build_fallback_result(title, hook, niche, channel_size)

    def _build_analysis_prompt(
        self,
        title: str,
        hook: str,
        niche: str,
        channel_size: str,
        has_thumbnail: bool
    ) -> str:
        """Build the comprehensive RAG-based analysis prompt."""

        niche_config = NICHE_BENCHMARKS[niche]
        channel_config = CHANNEL_SIZE_CONFIG[channel_size]

        thumbnail_instructions = """
## THUMBNAIL ANALYSIS (Score each 0-10)

Analyze the provided thumbnail image:

1. **Visual Contrast** (0-10): How well does the thumbnail stand out? High contrast = pattern interruption
2. **Face Presence** (0-10): 0=None, 5=Background face, 10=Large clear face with eye contact
3. **Emotion Intensity** (0-10): 0=Neutral, 5=Moderate, 10=Extreme (optimal is 7-8, peaked curve)
4. **Text Readability** (0-10): Can text be read clearly at 200px mobile thumbnail size?
5. **Color Vibrancy** (0-10): 0=Dull/muted, 10=Bright, saturated colors
6. **Alignment with Content** (0-10): Does thumbnail accurately represent the title/hook content?

**CTR Impact Calculation:**
- Each point in Visual Contrast: +0.1-0.2% CTR
- Each point in Face Presence: +0.2-0.2% CTR
- Each point in Emotion (peaked at 7-8): +0.2-0.15% CTR
- Each point in Text Readability: +0.1-0.08% CTR
- Each point in Color Vibrancy: +0.2-0.1% CTR
- Each point in Alignment: +0.1-0.05% CTR

Total possible CTR boost from thumbnail: +2% to +8%
""" if has_thumbnail else """
## THUMBNAIL ANALYSIS
No thumbnail provided. Thumbnail analysis will be skipped.
Assume baseline thumbnail (score 5/10, +0% CTR impact).
"""

        prompt = f"""You are a YouTube video performance analyst using a scientific, data-driven methodology.

# ANALYSIS TASK

Analyze the following video content and predict its viral potential:

**Title:** {title}
**Opening Hook:** {hook}
**Niche:** {niche.capitalize()} (CTR baseline: {niche_config['baseline_ctr_avg']}%, AVD baseline: {niche_config['baseline_avd']}%)
**Channel Size:** {channel_size.capitalize()} ({channel_config['range']} subscribers)

{thumbnail_instructions}

## HOOK ANALYSIS (Score each 0-10)

Evaluate the opening hook using psychological trigger framework:

1. **Information Gap Creation** (0-10): Does it create cognitive discomfort between "what viewer knows" and "what they want to know"?
   - 10/10 example: "You've been doing this wrong your entire life"
   - 3/10 example: "Here are some tips"

2. **Emotional Authenticity** (0-10): Would this trigger mirror neuron activation?
   - 10/10: Genuine shock/surprise expression implied
   - 3/10: Reading script with fake emotion

3. **Open Loop Clarity** (0-10): Does it create unresolved tension (Zeigarnik Effect)?
   - 10/10 example: "Wait until you see #3" (specific)
   - 3/10 example: "Wait until the end" (vague)

4. **Personal Relevance** (0-10): Does it target a specific audience?
   - 10/10 example: "If you have oily skin..." (specific)
   - 3/10 example: "If you have skin..." (too vague)

5. **Value Proposition** (0-10): Is the benefit clear and specific?
   - 10/10 example: "Save 2 hours per day"
   - 3/10 example: "Save time"

6. **Processing Ease** (0-10): Is it simple and clear, not confusing?
   - 10/10: Simple language, clear structure
   - 3/10: Complex jargon, confusing setup

**Psychological Triggers to Detect:**
- Information Gap (curiosity)
- Zeigarnik Effect (open loops)
- Mirror Neuron Activation (emotional resonance)
- Contrast Principle (before/after, vs comparisons)
- Social Proof (numbers, authority)
- Urgency/Scarcity

**AVD Impact Formula:**
AVD_Lift = 5% + (Hook_Score × 1.2%)
- Hook Score 3/10 → +8.6% AVD
- Hook Score 7/10 → +13.4% AVD
- Hook Score 10/10 → +17% AVD

## TITLE ANALYSIS (Score each 0-10)

1. **Specificity** (0-10): "3 Proven Systems" beats "Great Tips"
2. **Number Inclusion** (0-10): Does it use numbers? "5 Ways..." beats "Ways..."
3. **Curiosity/Power Words** (0-10): "Revealed," "Secret," "Proven," "Simple," "Fast"
4. **Personal Pronoun** (0-10): Uses "You" or "I" vs impersonal framing
5. **Keyword Relevance** (0-10): Are search-relevant keywords present?
6. **Title-Hook Coherence** (0-10): Does title promise match hook delivery?

**Title CTR Boost:**
- Specificity: +0.1-0.15% per point
- Number inclusion: +0.05-0.12% per point
- Curiosity words: +0.05-0.1% per point
- Personal pronoun: +0.03-0.08% per point
- Keyword relevance: varies
- Coherence: +0.01-0.05% per point

## ALTERNATIVE TITLES

Generate exactly 3 alternative titles using DIFFERENT hook types:
1. One using a **Number Hook** (e.g., "7 Ways...", "3 Secrets...")
2. One using a **Question Hook** (e.g., "Why does...?", "What if...?")
3. One using a **Curiosity Gap** (e.g., "The truth about...", "What nobody tells you about...")

Each alternative must:
- Be contextually relevant to the original topic
- Be 50-70 characters (optimal length)
- Have a unique approach (no templates!)
- Include estimated CTR boost

## OUTPUT FORMAT

Respond with ONLY valid JSON (no markdown, no explanation):

{{
  "thumbnail_analysis": {{
    "score": 0.0,
    "visual_contrast": 0.0,
    "face_presence": 0.0,
    "emotion_intensity": 0.0,
    "text_readability": 0.0,
    "color_vibrancy": 0.0,
    "alignment_with_content": 0.0,
    "ctr_impact_percent": 0.0,
    "notes": "string"
  }},
  "hook_analysis": {{
    "score": 0.0,
    "information_gap": 0.0,
    "emotional_authenticity": 0.0,
    "open_loop_clarity": 0.0,
    "personal_relevance": 0.0,
    "value_proposition": 0.0,
    "processing_ease": 0.0,
    "psychological_triggers": ["trigger1", "trigger2"],
    "avd_impact_percent": 0.0,
    "notes": "string"
  }},
  "title_analysis": {{
    "score": 0.0,
    "specificity": 0.0,
    "number_inclusion": 0.0,
    "curiosity_words": 0.0,
    "personal_pronoun": 0.0,
    "keyword_relevance": 0.0,
    "title_hook_coherence": 0.0,
    "ctr_impact_percent": 0.0,
    "notes": "string"
  }},
  "alternative_titles": [
    {{
      "title": "string",
      "hook_type": "Number Hook",
      "expected_ctr_boost": "+X%",
      "rationale": "string"
    }},
    {{
      "title": "string",
      "hook_type": "Question Hook",
      "expected_ctr_boost": "+X%",
      "rationale": "string"
    }},
    {{
      "title": "string",
      "hook_type": "Curiosity Gap",
      "expected_ctr_boost": "+X%",
      "rationale": "string"
    }}
  ],
  "recommendations": {{
    "thumbnail": ["recommendation 1", "recommendation 2"],
    "hook": ["recommendation 1", "recommendation 2"],
    "title": ["recommendation 1", "recommendation 2"],
    "strategy": ["recommendation 1", "recommendation 2"]
  }},
  "risk_assessment": {{
    "click_to_content_mismatch": "Low|Medium|High",
    "saturation_risk": "Low|Medium|High",
    "algorithmic_risk": "Low|Medium|High",
    "risk_notes": "string"
  }},
  "overall_assessment": {{
    "viral_potential": "Low|Medium|High|Very High",
    "confidence": 0.0,
    "summary": "string"
  }}
}}
"""
        return prompt

    def _extract_json(self, response_text: str) -> dict:
        """Extract JSON from Gemini response, handling markdown code blocks."""
        text = response_text.strip()

        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Response text: {text[:500]}...")
            raise

    def _build_result(
        self,
        analysis: dict,
        title: str,
        niche: str,
        channel_size: str,
        has_thumbnail: bool
    ) -> ViralAnalysisResult:
        """Build the final result using RAG formulas for view prediction."""

        niche_config = NICHE_BENCHMARKS[niche]
        channel_config = CHANNEL_SIZE_CONFIG[channel_size]

        # Extract scores
        thumbnail_data = analysis.get("thumbnail_analysis", {})
        hook_data = analysis.get("hook_analysis", {})
        title_data = analysis.get("title_analysis", {})

        thumbnail_score = thumbnail_data.get("score", 5.0) if has_thumbnail else 5.0
        hook_score = hook_data.get("score", 5.0)
        title_score = title_data.get("score", 5.0)

        # Calculate CTR prediction using RAG formula
        baseline_ctr = niche_config["baseline_ctr_avg"]
        thumbnail_ctr_boost = thumbnail_data.get("ctr_impact_percent", 0) if has_thumbnail else 0
        title_ctr_boost = title_data.get("ctr_impact_percent", 0)
        predicted_ctr = baseline_ctr + thumbnail_ctr_boost + title_ctr_boost
        predicted_ctr = max(2, min(20, predicted_ctr))  # Clamp to reasonable range

        # Calculate AVD prediction using RAG formula
        baseline_avd = niche_config["baseline_avd"]
        hook_avd_boost = 5 + (hook_score * 1.2)  # From RAG: AVD_Lift = 5% + (Hook_Score × 1.2%)
        predicted_avd = baseline_avd + hook_avd_boost
        predicted_avd = max(20, min(85, predicted_avd))  # Clamp to reasonable range

        # Calculate view prediction using RAG master formula
        # PREDICTED_VIEWS = (IMPRESSIONS × CTR%) × AVD_FACTOR × NICHE_FACTOR × CHANNEL_FACTOR

        initial_impressions = channel_config["baseline_impressions"]
        initial_views = initial_impressions * (predicted_ctr / 100)

        # AVD Factor
        avd_factor = predicted_avd / baseline_avd

        # Niche Factor
        niche_factor = niche_config["engagement_factor"] * (1 / niche_config["saturation_index"])

        # Channel Factor (use middle of range)
        channel_multiplier = (channel_config["multiplier_low"] + channel_config["multiplier_high"]) / 2

        # Calculate Phase 1 Success Index (0-10 scale)
        # Phase_1_Success_Index = (CTR × 0.40) + (AVD × 0.35) + (Engagement × 0.15) + (Satisfaction × 0.10)
        ctr_normalized = min(10, predicted_ctr / 1.5)  # Normalize CTR to ~0-10
        avd_normalized = min(10, predicted_avd / 8)  # Normalize AVD to ~0-10
        engagement_estimate = (thumbnail_score + hook_score + title_score) / 3
        satisfaction_estimate = 7.0  # Assume good satisfaction for quality content

        phase_1_success = (ctr_normalized * 0.40) + (avd_normalized * 0.35) + (engagement_estimate * 0.15) + (satisfaction_estimate * 0.10)
        phase_1_success = min(10, max(0, phase_1_success))

        # Algorithmic Boost based on Phase 1 success
        algorithmic_boost = 1.0 + (phase_1_success - 6.0) * 0.25
        algorithmic_boost = max(0.5, min(2.0, algorithmic_boost))

        # Final view prediction
        predicted_views = int(initial_views * avd_factor * niche_factor * channel_multiplier * algorithmic_boost)

        # Calculate confidence interval (±30-50% based on input quality)
        confidence_percent = 40 if has_thumbnail else 50
        view_range_low = int(predicted_views * (1 - confidence_percent / 100))
        view_range_high = int(predicted_views * (1 + confidence_percent / 100))

        # Overall viral score (0-100)
        # Weighted: Thumbnail 25%, Hook 35%, Title 20%, Channel potential 20%
        thumbnail_weight = 0.25 if has_thumbnail else 0
        hook_weight = 0.35 + (0.25 if not has_thumbnail else 0)  # Hook gets extra weight if no thumbnail
        title_weight = 0.20
        channel_weight = 0.20

        channel_score = min(10, channel_multiplier * 5)  # Convert multiplier to 0-10 score

        overall_score = (
            (thumbnail_score * thumbnail_weight) +
            (hook_score * hook_weight) +
            (title_score * title_weight) +
            (channel_score * channel_weight)
        ) * 10  # Scale to 0-100

        overall_score = int(min(100, max(0, overall_score)))

        # Benchmark comparison
        niche_avg_views = (channel_config["baseline_views_low"] + channel_config["baseline_views_high"]) / 2
        vs_niche_pct = ((predicted_views - niche_avg_views) / niche_avg_views) * 100
        vs_niche_str = f"+{vs_niche_pct:.0f}%" if vs_niche_pct > 0 else f"{vs_niche_pct:.0f}%"

        # Competitive positioning
        if overall_score >= 75:
            positioning = "Strong"
        elif overall_score >= 50:
            positioning = "Average"
        else:
            positioning = "Below Average"

        # Build alternative titles
        alt_titles = []
        for alt in analysis.get("alternative_titles", []):
            alt_titles.append(AlternativeTitle(
                title=alt.get("title", ""),
                hook_type=alt.get("hook_type", ""),
                expected_ctr_boost=alt.get("expected_ctr_boost", "+0%"),
                rationale=alt.get("rationale", "")
            ))

        # Build recommendations
        recommendations = analysis.get("recommendations", {})
        risk_assessment = analysis.get("risk_assessment", {})
        overall_assessment = analysis.get("overall_assessment", {})

        return ViralAnalysisResult(
            title=title,
            niche=niche,
            niche_confidence=0.95,
            channel_size=channel_size,
            channel_multiplier=channel_multiplier,

            thumbnail=ThumbnailAnalysis(
                score=thumbnail_score,
                ctr_impact=f"+{thumbnail_ctr_boost:.1f}%",
                visual_contrast=thumbnail_data.get("visual_contrast", 5.0),
                face_presence=thumbnail_data.get("face_presence", 5.0),
                emotion_intensity=thumbnail_data.get("emotion_intensity", 5.0),
                text_readability=thumbnail_data.get("text_readability", 5.0),
                color_vibrancy=thumbnail_data.get("color_vibrancy", 5.0),
                alignment_with_content=thumbnail_data.get("alignment_with_content", 5.0),
                analysis_notes=thumbnail_data.get("notes", "No thumbnail provided" if not has_thumbnail else "")
            ) if has_thumbnail else None,

            hook=HookAnalysis(
                score=hook_score,
                avd_impact=f"+{hook_avd_boost:.1f}%",
                information_gap=hook_data.get("information_gap", 5.0),
                emotional_authenticity=hook_data.get("emotional_authenticity", 5.0),
                open_loop_clarity=hook_data.get("open_loop_clarity", 5.0),
                personal_relevance=hook_data.get("personal_relevance", 5.0),
                value_proposition=hook_data.get("value_proposition", 5.0),
                processing_ease=hook_data.get("processing_ease", 5.0),
                psychological_triggers=hook_data.get("psychological_triggers", []),
                analysis_notes=hook_data.get("notes", "")
            ),

            title_analysis=TitleAnalysis(
                score=title_score,
                ctr_impact=f"+{title_ctr_boost:.1f}%",
                specificity=title_data.get("specificity", 5.0),
                number_inclusion=title_data.get("number_inclusion", 5.0),
                curiosity_words=title_data.get("curiosity_words", 5.0),
                personal_pronoun=title_data.get("personal_pronoun", 5.0),
                keyword_relevance=title_data.get("keyword_relevance", 5.0),
                title_hook_coherence=title_data.get("title_hook_coherence", 5.0),
                analysis_notes=title_data.get("notes", "")
            ),

            predicted_views=predicted_views,
            confidence_interval=f"±{confidence_percent}%",
            view_range_low=view_range_low,
            view_range_high=view_range_high,
            predicted_ctr=f"{predicted_ctr:.1f}%",
            predicted_avd=f"{predicted_avd:.0f}%",
            phase_1_success_index=round(phase_1_success, 1),

            thumbnail_recommendations=recommendations.get("thumbnail", []) if has_thumbnail else ["Upload a thumbnail for better predictions"],
            hook_recommendations=recommendations.get("hook", []),
            title_recommendations=recommendations.get("title", []),
            strategy_recommendations=recommendations.get("strategy", []),

            alternative_titles=alt_titles,

            vs_niche_average=vs_niche_str,
            competitive_positioning=positioning,

            click_to_content_mismatch_risk=risk_assessment.get("click_to_content_mismatch", "Medium"),
            saturation_risk=risk_assessment.get("saturation_risk", "Medium"),
            algorithmic_risk=risk_assessment.get("algorithmic_risk", "Medium"),

            overall_viral_score=overall_score,
            analysis_summary=overall_assessment.get("summary", "Analysis complete.")
        )

    def _build_fallback_result(
        self,
        title: str,
        hook: str,
        niche: str,
        channel_size: str
    ) -> ViralAnalysisResult:
        """Build a basic fallback result when Gemini fails."""

        channel_config = CHANNEL_SIZE_CONFIG.get(channel_size, CHANNEL_SIZE_CONFIG["micro"])
        niche_config = NICHE_BENCHMARKS.get(niche, NICHE_BENCHMARKS["entertainment"])

        # Basic heuristic scoring
        title_len = len(title)
        title_score = 7.0 if 50 <= title_len <= 70 else 5.0
        hook_score = 6.0 if len(hook) > 20 else 4.0

        baseline_views = (channel_config["baseline_views_low"] + channel_config["baseline_views_high"]) / 2

        return ViralAnalysisResult(
            title=title,
            niche=niche,
            niche_confidence=0.5,
            channel_size=channel_size,
            channel_multiplier=(channel_config["multiplier_low"] + channel_config["multiplier_high"]) / 2,

            thumbnail=None,

            hook=HookAnalysis(
                score=hook_score,
                avd_impact=f"+{5 + hook_score * 1.2:.1f}%",
                information_gap=5.0,
                emotional_authenticity=5.0,
                open_loop_clarity=5.0,
                personal_relevance=5.0,
                value_proposition=5.0,
                processing_ease=5.0,
                psychological_triggers=[],
                analysis_notes="Fallback analysis - Gemini unavailable"
            ),

            title_analysis=TitleAnalysis(
                score=title_score,
                ctr_impact="+0%",
                specificity=5.0,
                number_inclusion=5.0,
                curiosity_words=5.0,
                personal_pronoun=5.0,
                keyword_relevance=5.0,
                title_hook_coherence=5.0,
                analysis_notes="Fallback analysis - Gemini unavailable"
            ),

            predicted_views=int(baseline_views),
            confidence_interval="±70%",
            view_range_low=int(baseline_views * 0.3),
            view_range_high=int(baseline_views * 1.7),
            predicted_ctr=f"{niche_config['baseline_ctr_avg']}%",
            predicted_avd=f"{niche_config['baseline_avd']}%",
            phase_1_success_index=5.0,

            thumbnail_recommendations=["Upload a thumbnail for AI analysis"],
            hook_recommendations=["Unable to analyze - please try again"],
            title_recommendations=["Unable to analyze - please try again"],
            strategy_recommendations=["Unable to analyze - please try again"],

            alternative_titles=[],

            vs_niche_average="0%",
            competitive_positioning="Unknown",

            click_to_content_mismatch_risk="Unknown",
            saturation_risk="Unknown",
            algorithmic_risk="Unknown",

            overall_viral_score=50,
            analysis_summary="Fallback analysis - AI service temporarily unavailable. Please try again."
        )


def result_to_dict(result: ViralAnalysisResult) -> dict:
    """Convert ViralAnalysisResult to a JSON-serializable dictionary."""
    data = asdict(result)

    # Handle None thumbnail
    if data["thumbnail"] is None:
        data["thumbnail"] = None

    return data
