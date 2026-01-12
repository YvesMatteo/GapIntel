#!/usr/bin/env python3
"""
Scoring Engine - GapIntel v2 Module 3

Weighted scoring system for viral potential calculation.

Formula:
    Viral Score = (Comment_Freq × 0.2) + (Visual_Outlier × 0.2) + 
                  (Trend_Momentum × 0.3) + (Niche_Saturation_Inverse × 0.3)

Usage:
    from scoring_engine import calculate_viral_score, ScoreCalculator
    score = calculate_viral_score(comment_freq=80, visual_outlier=60, 
                                   trend_momentum=90, saturation_inverse=70)
"""

from dataclasses import dataclass
from typing import Optional
import json


@dataclass
class ScoreComponents:
    """Individual score components for transparency."""
    comment_frequency: float
    visual_outlier: float
    trend_momentum: float
    saturation_inverse: float
    
    def to_dict(self) -> dict:
        return {
            "comment_frequency": round(self.comment_frequency, 1),
            "visual_outlier": round(self.visual_outlier, 1),
            "trend_momentum": round(self.trend_momentum, 1),
            "saturation_inverse": round(self.saturation_inverse, 1)
        }


@dataclass
class ViralScore:
    """Complete viral score with breakdown."""
    total_score: float
    components: ScoreComponents
    priority: str  # HIGH, MEDIUM, LOW
    recommendation: str
    
    def to_dict(self) -> dict:
        return {
            "total_score": round(self.total_score, 1),
            "priority": self.priority,
            "components": self.components.to_dict(),
            "recommendation": self.recommendation
        }


# Weights for the scoring formula
WEIGHTS = {
    "comment_frequency": 0.2,
    "visual_outlier": 0.2,
    "trend_momentum": 0.3,
    "saturation_inverse": 0.3
}


def calculate_viral_score(
    comment_freq: float,
    visual_outlier: float,
    trend_momentum: float,
    saturation_inverse: float
) -> float:
    """
    Calculate the Viral Priority Score (0-100).
    
    Args:
        comment_freq: Comment engagement score (0-100)
        visual_outlier: Visual pattern performance vs average (0-100)
        trend_momentum: Google Trends momentum score (0-100)
        saturation_inverse: Inverse niche saturation (0-100, higher = less competition)
    
    Returns:
        Final viral score (0-100)
    """
    # Ensure all inputs are in 0-100 range
    comment_freq = max(0, min(100, comment_freq))
    visual_outlier = max(0, min(100, visual_outlier))
    trend_momentum = max(0, min(100, trend_momentum))
    saturation_inverse = max(0, min(100, saturation_inverse))
    
    # Apply weighted formula
    score = (
        comment_freq * WEIGHTS["comment_frequency"] +
        visual_outlier * WEIGHTS["visual_outlier"] +
        trend_momentum * WEIGHTS["trend_momentum"] +
        saturation_inverse * WEIGHTS["saturation_inverse"]
    )
    
    return round(score, 1)


def calculate_full_viral_score(
    comment_freq: float,
    visual_outlier: float,
    trend_momentum: float,
    saturation_inverse: float
) -> ViralScore:
    """
    Calculate complete viral score with breakdown and recommendations.
    
    Returns:
        ViralScore object with full analysis
    """
    total = calculate_viral_score(comment_freq, visual_outlier, trend_momentum, saturation_inverse)
    
    components = ScoreComponents(
        comment_frequency=comment_freq * WEIGHTS["comment_frequency"],
        visual_outlier=visual_outlier * WEIGHTS["visual_outlier"],
        trend_momentum=trend_momentum * WEIGHTS["trend_momentum"],
        saturation_inverse=saturation_inverse * WEIGHTS["saturation_inverse"]
    )
    
    # Determine priority
    if total >= 70:
        priority = "HIGH"
    elif total >= 45:
        priority = "MEDIUM"
    else:
        priority = "LOW"
    
    # Generate recommendation
    recommendation = generate_recommendation(components, total)
    
    return ViralScore(
        total_score=total,
        components=components,
        priority=priority,
        recommendation=recommendation
    )


def generate_recommendation(components: ScoreComponents, total: float) -> str:
    """Generate actionable recommendation based on score components."""
    recommendations = []
    
    # Find the strongest and weakest factors
    component_values = {
        "comment_frequency": components.comment_frequency,
        "visual_outlier": components.visual_outlier,
        "trend_momentum": components.trend_momentum,
        "saturation_inverse": components.saturation_inverse
    }
    
    strongest = max(component_values.items(), key=lambda x: x[1])
    weakest = min(component_values.items(), key=lambda x: x[1])
    
    if total >= 70:
        recommendations.append("🔥 HIGH PRIORITY: This topic has strong viral potential.")
    elif total >= 45:
        recommendations.append("📈 MEDIUM PRIORITY: Good opportunity with room for optimization.")
    else:
        recommendations.append("⏳ LOW PRIORITY: Consider focusing on higher-scoring opportunities first.")
    
    # Strength callout
    strength_messages = {
        "comment_frequency": "Strong audience demand in comments.",
        "visual_outlier": "Visual style aligns with your top performers.",
        "trend_momentum": "Topic is trending on Google.",
        "saturation_inverse": "Low competition in this niche."
    }
    recommendations.append(f"Strength: {strength_messages.get(strongest[0], 'N/A')}")
    
    # Improvement suggestion
    improvement_messages = {
        "comment_frequency": "Engage more with comments to validate demand.",
        "visual_outlier": "Consider A/B testing thumbnail styles.",
        "trend_momentum": "Monitor Google Trends for timing.",
        "saturation_inverse": "Differentiate from competitors."
    }
    recommendations.append(f"Improve: {improvement_messages.get(weakest[0], 'N/A')}")
    
    return " | ".join(recommendations)


class ScoreCalculator:
    """
    Full scoring calculator that integrates with all GapIntel v2 modules.
    """
    
    def __init__(self):
        self.weights = WEIGHTS.copy()
    
    def score_opportunity(
        self,
        topic: str,
        comment_data: Optional[dict] = None,
        vision_data: Optional[dict] = None,
        trend_data: Optional[dict] = None,
        niche_data: Optional[dict] = None
    ) -> dict:
        """
        Calculate viral score for a content opportunity.
        
        Args:
            topic: The topic/keyword being scored
            comment_data: Output from gap_analyzer (engagement, mentions)
            vision_data: Output from vision_analyzer (winning patterns)
            trend_data: Output from market_intel (trend score, momentum)
            niche_data: Output from market_intel explore_niche (saturation)
        
        Returns:
            Dict with complete score breakdown
        """
        # Extract comment frequency score (0-100)
        if comment_data:
            engagement = comment_data.get("total_engagement", 0)
            mentions = comment_data.get("mention_count", 1)
            # Normalize engagement to 0-100 scale
            comment_freq = min(100, (engagement / 100) + (mentions * 5))
        else:
            comment_freq = 50  # Neutral default
        
        # Extract visual outlier score (0-100)
        if vision_data and vision_data.get("winning_patterns"):
            # Sum of positive impacts from winning patterns
            impacts = []
            for pattern in vision_data["winning_patterns"]:
                impact_str = pattern.get("impact", "+0%")
                try:
                    impact = float(impact_str.replace("%", "").replace("+", "").split()[0])
                    impacts.append(impact)
                except:
                    pass
            visual_outlier = min(100, sum(impacts) + 50) if impacts else 50
        else:
            visual_outlier = 50  # Neutral default
        
        # Extract trend momentum score (0-100)
        if trend_data:
            from market_intel import calculate_trend_momentum_score
            trend_momentum = calculate_trend_momentum_score(trend_data)
        else:
            trend_momentum = 50  # Neutral default
        
        # Extract saturation inverse score (0-100)
        if niche_data and "saturation" in niche_data:
            saturation_inverse = niche_data["saturation"].get("inverse_score", 50)
        else:
            saturation_inverse = 50  # Neutral default
        
        # Calculate final score
        full_score = calculate_full_viral_score(
            comment_freq=comment_freq,
            visual_outlier=visual_outlier,
            trend_momentum=trend_momentum,
            saturation_inverse=saturation_inverse
        )
        
        return {
            "topic": topic,
            "viral_score": full_score.total_score,
            "priority": full_score.priority,
            "components": full_score.components.to_dict(),
            "recommendation": full_score.recommendation,
            "input_data": {
                "comment_freq_raw": comment_freq,
                "visual_outlier_raw": visual_outlier,
                "trend_momentum_raw": trend_momentum,
                "saturation_inverse_raw": saturation_inverse
            }
        }
    
    def rank_opportunities(self, opportunities: list) -> list:
        """
        Rank a list of scored opportunities by viral potential.
        
        Args:
            opportunities: List of dicts from score_opportunity()
        
        Returns:
            Sorted list with rank added
        """
        sorted_opps = sorted(opportunities, key=lambda x: x.get("viral_score", 0), reverse=True)
        
        for i, opp in enumerate(sorted_opps, 1):
            opp["rank"] = i
        
        return sorted_opps
    
    def generate_heatmap_data(self, opportunities: list) -> list:
        """
        Generate data suitable for a heatmap visualization.
        
        Returns:
            List of dicts with topic, score, and color classification
        """
        heatmap = []
        
        for opp in opportunities:
            score = opp.get("viral_score", 0)
            
            if score >= 70:
                color = "hot"
                intensity = "high"
            elif score >= 50:
                color = "warm"
                intensity = "medium"
            elif score >= 30:
                color = "cool"
                intensity = "low"
            else:
                color = "cold"
                intensity = "very_low"
            
            heatmap.append({
                "topic": opp.get("topic", "Unknown"),
                "score": score,
                "priority": opp.get("priority", "LOW"),
                "color": color,
                "intensity": intensity,
                "rank": opp.get("rank", 0)
            })
        
        return heatmap


def score_gap_opportunities(
    verified_gaps: list,
    vision_results: Optional[dict] = None,
    trend_results: Optional[dict] = None,
    niche_results: Optional[dict] = None
) -> list:
    """
    Convenience function to score a list of verified gaps from gap_analyzer.
    
    Args:
        verified_gaps: List of gaps from gap_analyzer output
        vision_results: Output from vision_analyzer
        trend_results: Dict of keyword -> trend data
        niche_results: Output from niche explorer
    
    Returns:
        List of scored opportunities
    """
    calculator = ScoreCalculator()
    scored = []
    
    for gap in verified_gaps:
        topic = gap.get("topic_keyword", "Unknown")
        
        # Get trend data for this topic
        topic_trend = None
        if trend_results:
            topic_trend = trend_results.get(topic) or trend_results.get(topic.lower())
        
        scored_opp = calculator.score_opportunity(
            topic=topic,
            comment_data={
                "total_engagement": gap.get("total_engagement", 0),
                "mention_count": gap.get("mention_count", 1)
            },
            vision_data=vision_results,
            trend_data=topic_trend,
            niche_data=niche_results
        )
        
        # Merge original gap data
        scored_opp["gap_status"] = gap.get("gap_status", "UNKNOWN")
        scored_opp["user_struggle"] = gap.get("user_struggle", "")
        scored_opp["evidence"] = gap.get("verification_evidence", "")
        
        scored.append(scored_opp)
    
    # Rank and return
    return calculator.rank_opportunities(scored)


if __name__ == "__main__":
    # Test the scoring engine
    print("Testing Scoring Engine...")
    
    # Test basic calculation
    score = calculate_viral_score(
        comment_freq=80,
        visual_outlier=60,
        trend_momentum=90,
        saturation_inverse=70
    )
    print(f"✓ Basic score: {score}")
    
    # Test full calculation
    full = calculate_full_viral_score(
        comment_freq=80,
        visual_outlier=60,
        trend_momentum=90,
        saturation_inverse=70
    )
    print(f"✓ Full score: {full.total_score}")
    print(f"  Priority: {full.priority}")
    print(f"  Components: {full.components.to_dict()}")
    print(f"  Recommendation: {full.recommendation}")
    
    # Test calculator class
    calc = ScoreCalculator()
    opp = calc.score_opportunity(
        topic="Day trading for beginners",
        comment_data={"total_engagement": 500, "mention_count": 8},
        trend_data={"score": 75, "momentum": 20, "trajectory": "RISING"}
    )
    print(f"\n✓ Topic: {opp['topic']}")
    print(f"  Viral Score: {opp['viral_score']}")
    print(f"  Priority: {opp['priority']}")
