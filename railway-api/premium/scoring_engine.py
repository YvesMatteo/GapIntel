#!/usr/bin/env python3
"""
Scoring Engine - GapIntel v2 Module 3
Scientific Scoring System using XGBoost Benchmark Models.
"""

from dataclasses import dataclass
from typing import Optional, Dict
import math
import logging
from premium.ml_models.inference_engine import ScientificInference

# Initialize Inference Engine
# (Lazy load happens inside the class to avoid import loops if any)
scientific_inference = ScientificInference()

@dataclass
class ScoreComponents:
    """Individual score components for transparency."""
    predicted_views: int
    channel_avg: float
    uplift_factor: float
    trend_momentum: float
    saturation_inverse: float
    ml_confidence_score: float
    
    def to_dict(self) -> dict:
        return {
            "predicted_views": self.predicted_views,
            "channel_avg": round(self.channel_avg, 1),
            "uplift_factor": round(self.uplift_factor, 2),
            "trend_momentum": round(self.trend_momentum, 1),
            "saturation_inverse": round(self.saturation_inverse, 1),
            "ml_confidence_score": round(self.ml_confidence_score, 2)
        }

@dataclass
class ViralScore:
    """Complete viral score with breakdown."""
    total_score: float
    components: ScoreComponents
    priority: str  # HIGH, MEDIUM, LOW
    recommendation: str
    niche_used: str
    
    def to_dict(self) -> dict:
        return {
            "total_score": round(self.total_score, 1),
            "priority": self.priority,
            "components": self.components.to_dict(),
            "recommendation": self.recommendation,
            "niche_used": self.niche_used
        }

def calculate_ml_viral_score(
    topic: str,
    channel_stats: Dict,
    trend_momentum: float,
    saturation_inverse: float,
    niche: str = None
) -> ViralScore:
    """
    Calculate Viral Score using Scientific ML Models.
    """
    
    # 1. Scientific Prediction
    if not niche:
        from premium.ml_models.inference_engine import detect_niche
        niche = detect_niche(topic)
        
    prediction = scientific_inference.predict_expected_views(
        niche=niche,
        video_metadata={'title': topic, 'duration_seconds': 600}, # Assume 10m avg
        channel_stats=channel_stats
    )
    
    expected_views = prediction.get('expected_views', 0)
    channel_avg = channel_stats.get('view_average', 1000)
    if channel_avg == 0: channel_avg = 1000
    
    # Uplift Factor (Multiplier)
    uplift = 0
    if channel_avg > 0:
        uplift = expected_views / channel_avg
    
    # 2. Base Score from Uplift
    if uplift <= 0:
        base_score = 0
    else:
        # Scale: log2(uplift) centered at 50
        # 1.0x = 50, 2.0x = 80, 0.5x = 20
        base_score = 50 + (math.log2(uplift) * 30)
    
    base_score = max(0, min(100, base_score))
    
    # 3. Apply Multipliers (External Factors)
    trend_impact = (trend_momentum - 50) * 0.4 
    saturation_impact = (saturation_inverse - 50) * 0.2
    
    final_score = base_score + trend_impact + saturation_impact
    final_score = max(0, min(100, final_score))
    
    # Priority
    if final_score >= 80: priority = "HIGH"
    elif final_score >= 60: priority = "MEDIUM"
    else: priority = "LOW"
    
    # Recommendation
    rec = []
    if uplift > 1.5: rec.append(f"Expected to outperform avg by {uplift:.1f}x")
    elif uplift < 0.8: rec.append("Likely to underperform channel avg")
    else: rec.append("Expected to perform near average")
    
    if trend_momentum > 70: rec.append("Strong market trend")
    if saturation_inverse > 70: rec.append("Low competition gap")
    
    return ViralScore(
        total_score=final_score,
        components=ScoreComponents(
            predicted_views=expected_views,
            channel_avg=channel_avg,
            uplift_factor=uplift,
            trend_momentum=trend_momentum,
            saturation_inverse=saturation_inverse,
            ml_confidence_score=0.85
        ),
        priority=priority,
        recommendation=" | ".join(rec),
        niche_used=niche
    )


class ScoreCalculator:
    """
    Scientific Scoring Calculator v2.
    """
    def score_opportunity(
        self,
        topic: str,
        channel_context: Dict, 
        trend_data: Optional[dict] = None,
        niche_data: Optional[dict] = None,
        vision_data: Optional[dict] = None # Unused
    ) -> dict:
        
        trend_score = 50
        if trend_data:
             trend_score = trend_data.get('momentum', 50)
             
        saturation_score = 50
        if niche_data and "saturation" in niche_data:
            saturation_score = niche_data["saturation"].get("inverse_score", 50)
            
        niche = channel_context.get('niche')
        
        # Calculate
        viral_result = calculate_ml_viral_score(
            topic=topic,
            channel_stats=channel_context,
            trend_momentum=trend_score,
            saturation_inverse=saturation_score,
            niche=niche
        )
        
        return {
            "topic": topic,
            "viral_score": viral_result.total_score,
            "priority": viral_result.priority,
            "components": viral_result.components.to_dict(),
            "recommendation": viral_result.recommendation,
            "niche": viral_result.niche_used,
            "is_scientific": True
        }
    
    def rank_opportunities(self, opportunities: list) -> list:
        sorted_opps = sorted(opportunities, key=lambda x: x.get("viral_score", 0), reverse=True)
        for i, opp in enumerate(sorted_opps, 1):
            opp["rank"] = i
        return sorted_opps

def score_gap_opportunities(
    verified_gaps: list,
    channel_info: Dict, 
    trend_results: Optional[dict] = None,
    niche_results: Optional[dict] = None
) -> list:
    """
    Score verified gaps using Scientific ML. 
    Requires channel_info to Baseline the predictions.
    """
    calculator = ScoreCalculator()
    scored = []
    
    for gap in verified_gaps:
        topic = gap.get("topic_keyword", "Unknown")
        topic_trend = None
        if trend_results:
            topic_trend = trend_results.get(topic) or trend_results.get(topic.lower())
            
        score = calculator.score_opportunity(
            topic=topic,
            channel_context=channel_info, 
            trend_data=topic_trend,
            niche_data=niche_results
        )
        
        # Merge metadata
        score["gap_status"] = gap.get("gap_status")
        score["evidence"] = gap.get("verification_evidence")
        scored.append(score)
        
    return calculator.rank_opportunities(scored)

if __name__ == "__main__":
    print("Testing Scientific Scoring Engine...")
    # Mock data for testing
    channel_ctx = {"view_average": 5000, "subscriber_count": 50000, "niche": "Gaming"}
    
    calc = ScoreCalculator()
    opp = calc.score_opportunity(
        topic="Minecraft Speedrun Secrets",
        channel_context=channel_ctx,
        trend_data={"momentum": 80}
    )
    print(f"Topic: {opp['topic']}")
    print(f"Viral Score: {opp['viral_score']}")
    print(f"Components: {opp['components']}")
    print(f"Recommendation: {opp['recommendation']}")
