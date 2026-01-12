"""
Premium Analysis - Package Init
Exposes all premium analysis modules.
"""

# Core extractors
from .thumbnail_extractor import ThumbnailFeatureExtractor, ThumbnailFeatures
from .data_collector import YouTubeDataCollector

# ML Models
from .ml_models.ctr_predictor import CTRPredictor
from .ml_models.views_predictor import ViewsVelocityPredictor
from .ml_models.content_clusterer import ContentClusteringEngine

# Intelligence Engines
from .competitor_analyzer import CompetitorAnalyzer
from .thumbnail_optimizer import ThumbnailOptimizer
from .publish_optimizer import PublishTimeOptimizer
from .enhanced_gap_analyzer import EnhancedGapAnalyzer

# Output
from .report_generator import PremiumReportGenerator

__all__ = [
    # Core
    'ThumbnailFeatureExtractor',
    'ThumbnailFeatures',
    'YouTubeDataCollector',
    
    # ML
    'CTRPredictor',
    'ViewsVelocityPredictor',
    'ContentClusteringEngine',
    
    # Engines
    'CompetitorAnalyzer',
    'ThumbnailOptimizer',
    'PublishTimeOptimizer',
    'EnhancedGapAnalyzer',
    
    # Output
    'PremiumReportGenerator'
]

__version__ = '1.0.0'
