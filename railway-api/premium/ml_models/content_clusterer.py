"""
Premium Analysis - Content Clustering Engine
Discovers patterns in what content performs best using semantic clustering.

Uses sentence embeddings to:
- Cluster videos by topic/format
- Find winning content formulas
- Identify underserved topic areas
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import Counter
import re
import warnings
import os
import json

warnings.filterwarnings('ignore')

# ML imports
try:
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# Supabase imports
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# Sentence transformers (optional)
try:
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


@dataclass 
class ContentCluster:
    """A cluster of similar content."""
    id: int
    name: str
    video_count: int
    avg_views: float
    avg_engagement: float
    performance_score: float
    common_elements: List[str]
    best_performer: Dict
    example_titles: List[str]
    # Enhanced: Full video examples with metadata
    example_videos: List[Dict] = None  # [{video_id, title, views, thumbnail_url}]
    
    def __post_init__(self):
        if self.example_videos is None:
            self.example_videos = []
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        # Ensure example_videos is a list, not None
        if result.get('example_videos') is None:
            result['example_videos'] = []
        return result


@dataclass
class ClusteringResult:
    """Full clustering analysis result."""
    clusters: List[ContentCluster]
    recommendations: List[str]
    best_performing_cluster: str
    underperforming_clusters: List[str]
    gap_opportunities: List[str]
    
    def to_dict(self) -> Dict:
        return {
            'clusters': [c.to_dict() for c in self.clusters],
            'recommendations': self.recommendations,
            'best_performing_cluster': self.best_performing_cluster,
            'underperforming_clusters': self.underperforming_clusters,
            'gap_opportunities': self.gap_opportunities
        }


class ContentClusteringEngine:
    """
    Clusters videos by topic/format to find winning formulas.
    
    Uses semantic embeddings of:
    - Video titles
    - Video descriptions  
    - Tags
    
    Then correlates clusters with performance metrics.
    """
    
    # Common video format patterns
    FORMAT_PATTERNS = {
        'tutorial': ['how to', 'tutorial', 'guide', 'learn', 'step by step', 'beginner', 'complete'],
        'listicle': ['top 10', 'top 5', 'best', 'worst', 'ranking', 'tier list'],
        'review': ['review', 'unboxing', 'first look', 'hands on', 'worth it'],
        'reaction': ['reaction', 'reacting', 'react to', 'watching'],
        'vlog': ['vlog', 'day in', 'grwm', 'routine', 'a day'],
        'news': ['breaking', 'update', 'news', 'leaked', 'confirmed', 'announcement'],
        'comparison': ['vs', 'versus', 'compared', 'battle', 'which is better'],
        'challenge': ['challenge', 'i tried', 'for 24 hours', 'experiment'],
        'story': ['storytime', 'story time', 'what happened', 'my experience'],
        'educational': ['explained', 'why', 'science', 'how', 'the truth about']
    }
    
    def __init__(self, use_embeddings: bool = True):
        self.use_embeddings = use_embeddings and TRANSFORMERS_AVAILABLE
        self.model = None
        self.supabase: Optional[Client] = None
        
        # Initialize Supabase
        if SUPABASE_AVAILABLE:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_SERVICE_KEY")
            if url and key:
                self.supabase = create_client(url, key)

        if self.use_embeddings:
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
            except:
                self.use_embeddings = False

    def _get_cached_embeddings(self, video_ids: List[str]) -> Dict[str, List[float]]:
        """Retrieve embeddings from Supabase cache."""
        if not self.supabase or not video_ids:
            return {}
        
        try:
            # Supabase doesn't support "IN" query easily on all clients, 
            # but we can try to fetch them. For now, fetch all matching IDs.
            # Using filter('video_id', 'in', video_ids) if supported or individual queries
            # For simplicity in this env, we'll try the 'in' filter which is standard PostgREST
            
            response = self.supabase.table("video_embeddings")\
                .select("video_id, embedding")\
                .in_("video_id", video_ids)\
                .execute()
                
            cache = {}
            if response.data:
                for row in response.data:
                    # Convert valid JSON string or list back to numpy/list
                    emb = row.get('embedding')
                    if isinstance(emb, str):
                        emb = json.loads(emb)
                    cache[row['video_id']] = emb
            return cache
        except Exception as e:
            print(f"⚠️ Cache lookup failed: {e}")
            return {}

    def _cache_embeddings(self, embeddings_map: Dict[str, List[float]]):
        """Store new embeddings in Supabase."""
        if not self.supabase or not embeddings_map:
            return
            
        try:
            data = []
            for vid, emb in embeddings_map.items():
                data.append({
                    "video_id": vid,
                    "embedding": emb, # pgvector handles list -> vector
                    "model_version": "all-MiniLM-L6-v2"
                })
            
            # Upsert in batches of 50
            batch_size = 50
            data_list = list(data)
            for i in range(0, len(data_list), batch_size):
                batch = data_list[i:i+batch_size]
                self.supabase.table("video_embeddings").upsert(batch).execute()
                
        except Exception as e:
            print(f"⚠️ Cache update failed: {e}")
    
    def cluster_channel_content(self, videos: List[Dict], 
                                 n_clusters: int = 5) -> ClusteringResult:
        """
        Cluster videos and analyze performance by cluster.
        
        Args:
            videos: List of video dicts with 'title', 'view_count', 'engagement_rate'
            n_clusters: Number of clusters to create
            
        Returns:
            ClusteringResult with cluster analysis
        """
        if not videos:
            return self._empty_result()
        
        # Adjust clusters based on video count
        n_clusters = min(n_clusters, max(2, len(videos) // 3))
        
        # Extract features
        if self.use_embeddings:
            clusters_data = self._cluster_with_embeddings(videos, n_clusters)
        else:
            clusters_data = self._cluster_with_keywords(videos, n_clusters)
        
        # Analyze each cluster
        clusters = []
        for cluster_id, cluster_videos in clusters_data.items():
            cluster = self._analyze_cluster(cluster_id, cluster_videos)
            clusters.append(cluster)
        
        # Sort by performance
        clusters.sort(key=lambda c: c.performance_score, reverse=True)
        
        # Generate insights
        recommendations = self._generate_recommendations(clusters)
        best = clusters[0].name if clusters else "Unknown"
        underperforming = [c.name for c in clusters if c.performance_score < 0.5]
        gaps = self._identify_gaps(videos, clusters)
        
        return ClusteringResult(
            clusters=clusters,
            recommendations=recommendations,
            best_performing_cluster=best,
            underperforming_clusters=underperforming,
            gap_opportunities=gaps
        )
    
    def _cluster_with_embeddings(self, videos: List[Dict], 
                                  n_clusters: int) -> Dict[int, List[Dict]]:
        """Cluster using sentence embeddings."""
        # Get video IDs
        video_ids = [v.get('video_id', f"unknown_{i}") for i, v in enumerate(videos)]
        
        # 1. Check cache
        cached_map = self._get_cached_embeddings(video_ids)
        
        # 2. Identify missing
        missing_indices = []
        missing_texts = []
        final_embeddings = np.zeros((len(videos), 384)) # 384-d for MiniLM
        
        for i, vid in enumerate(video_ids):
            if vid in cached_map:
                final_embeddings[i] = cached_map[vid]
            else:
                missing_indices.append(i)
                # Combine title + description for better context
                text = videos[i].get('title', '')
                if videos[i].get('description'):
                    text += " " + videos[i].get('description', '')[:200]
                missing_texts.append(text)
        
        # 3. Compute missing
        if missing_texts:
            print(f"   Generating embeddings for {len(missing_texts)} new videos...")
            new_embeddings = self.model.encode(missing_texts)
            
            # 4. Update cache and final array
            to_cache = {}
            for idx, emb in zip(missing_indices, new_embeddings):
                final_embeddings[idx] = emb
                to_cache[video_ids[idx]] = emb.tolist()
            
            self._cache_embeddings(to_cache)
        
        embeddings = final_embeddings
        
        # Reduce dimensionality if needed
        if embeddings.shape[1] > 50:
            pca = PCA(n_components=50)
            embeddings = pca.fit_transform(embeddings)
        
        # Cluster
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        
        # Group videos
        clusters = {}
        for i, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(videos[i])
        
        return clusters
    
    def _cluster_with_keywords(self, videos: List[Dict], 
                                n_clusters: int) -> Dict[int, List[Dict]]:
        """Cluster based on keyword matching (fallback method)."""
        clusters = {}
        unassigned = []
        
        for video in videos:
            title = video.get('title', '').lower()
            assigned = False
            
            # Check against format patterns
            for format_id, (format_name, keywords) in enumerate(self.FORMAT_PATTERNS.items()):
                if any(kw in title for kw in keywords):
                    if format_id not in clusters:
                        clusters[format_id] = []
                    clusters[format_id].append(video)
                    assigned = True
                    break
            
            if not assigned:
                unassigned.append(video)
        
        # Add unassigned to "General" cluster
        if unassigned:
            general_id = len(self.FORMAT_PATTERNS)
            clusters[general_id] = unassigned
        
        return clusters
    
    def _analyze_cluster(self, cluster_id: int, videos: List[Dict]) -> ContentCluster:
        """Analyze a single cluster."""
        if not videos:
            return ContentCluster(
                id=cluster_id, name="Empty", video_count=0,
                avg_views=0, avg_engagement=0, performance_score=0,
                common_elements=[], best_performer={}, example_titles=[],
                example_videos=[]
            )
        
        # Calculate averages
        avg_views = np.mean([v.get('view_count', 0) for v in videos])
        avg_engagement = np.mean([v.get('engagement_rate', 0) for v in videos])
        
        # Sort by views to get best examples
        sorted_videos = sorted(videos, key=lambda v: v.get('view_count', 0), reverse=True)
        best = sorted_videos[0]
        
        # Find common elements in titles
        common_elements = self._find_common_elements(videos)
        
        # Determine cluster name from patterns or common words
        name = self._determine_cluster_name(videos, common_elements)
        
        # Performance score (normalized)
        performance_score = min(1.0, (avg_views / 100000) * (1 + avg_engagement / 10))
        
        # Build example videos with full metadata (top 5 performers)
        example_videos = []
        for v in sorted_videos[:5]:
            example_videos.append({
                'video_id': v.get('video_id', ''),
                'title': v.get('title', ''),
                'views': v.get('view_count', 0),
                'thumbnail_url': v.get('thumbnail_url', f"https://img.youtube.com/vi/{v.get('video_id', '')}/maxresdefault.jpg"),
                'engagement_rate': v.get('engagement_rate', 0),
            })
        
        return ContentCluster(
            id=cluster_id,
            name=name,
            video_count=len(videos),
            avg_views=round(avg_views, 0),
            avg_engagement=round(avg_engagement, 2),
            performance_score=round(performance_score, 2),
            common_elements=common_elements[:5],
            best_performer={
                'title': best.get('title', ''),
                'views': best.get('view_count', 0),
                'video_id': best.get('video_id', ''),
                'thumbnail_url': best.get('thumbnail_url', f"https://img.youtube.com/vi/{best.get('video_id', '')}/maxresdefault.jpg"),
            },
            example_titles=[v.get('title', '')[:50] for v in sorted_videos[:3]],
            example_videos=example_videos,
        )
    
    def _find_common_elements(self, videos: List[Dict]) -> List[str]:
        """Find common words/phrases in video titles."""
        all_words = []
        for v in videos:
            title = v.get('title', '').lower()
            # Clean and split
            words = re.findall(r'\b[a-z]{3,}\b', title)
            all_words.extend(words)
        
        # Count and filter stopwords
        stopwords = {'the', 'and', 'for', 'you', 'this', 'that', 'with', 'are', 'was', 'has'}
        counter = Counter(w for w in all_words if w not in stopwords)
        
        return [word for word, count in counter.most_common(10) if count > 1]
    
    def _determine_cluster_name(self, videos: List[Dict], common_elements: List[str]) -> str:
        """Determine a descriptive name for the cluster."""
        # Check format patterns
        titles_lower = ' '.join([v.get('title', '').lower() for v in videos])
        
        for format_name, keywords in self.FORMAT_PATTERNS.items():
            matches = sum(1 for kw in keywords if kw in titles_lower)
            if matches >= 2:
                return format_name.title() + "s"
        
        # Use most common element
        if common_elements:
            return f"'{common_elements[0].title()}' Content"
        
        return "General Content"
    
    def _generate_recommendations(self, clusters: List[ContentCluster]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        if not clusters:
            return ["Not enough data for recommendations"]
        
        # Best format recommendation
        best = clusters[0]
        recommendations.append(
            f"Your '{best.name}' content performs best with {best.avg_views:,.0f} avg views. "
            f"Consider making more of this type."
        )
        
        # Underperforming format
        if len(clusters) > 1:
            worst = clusters[-1]
            if worst.performance_score < best.performance_score * 0.5:
                recommendations.append(
                    f"'{worst.name}' underperforms significantly. "
                    f"Consider reducing or improving this content type."
                )
        
        # High engagement but low views
        for c in clusters:
            if c.avg_engagement > 5 and c.avg_views < best.avg_views * 0.3:
                recommendations.append(
                    f"'{c.name}' has high engagement ({c.avg_engagement:.1f}%) but low views. "
                    f"Improve thumbnails/titles to increase reach."
                )
        
        return recommendations[:5]
    
    def _identify_gaps(self, videos: List[Dict], clusters: List[ContentCluster]) -> List[str]:
        """Identify content format gaps."""
        gaps = []
        
        # Check which formats are missing
        existing_formats = set()
        for v in videos:
            title = v.get('title', '').lower()
            for format_name, keywords in self.FORMAT_PATTERNS.items():
                if any(kw in title for kw in keywords):
                    existing_formats.add(format_name)
        
        # Suggest missing high-performing formats
        high_performing_formats = ['tutorial', 'listicle', 'comparison']
        for fmt in high_performing_formats:
            if fmt not in existing_formats:
                gaps.append(f"Consider creating '{fmt}' content - typically high-performing format")
        
        return gaps[:3]
    
    def _empty_result(self) -> ClusteringResult:
        """Return empty result when no data."""
        return ClusteringResult(
            clusters=[],
            recommendations=["Not enough videos for clustering analysis"],
            best_performing_cluster="N/A",
            underperforming_clusters=[],
            gap_opportunities=[]
        )


# === Quick test ===
if __name__ == "__main__":
    print("🧪 Testing Content Clustering Engine...")
    
    # Use keyword-based clustering for test
    engine = ContentClusteringEngine(use_embeddings=False)
    
    # Sample video data
    test_videos = [
        {'title': 'How to Build a Website - Complete Tutorial', 'view_count': 50000, 'engagement_rate': 4.5},
        {'title': 'Tutorial: Python for Beginners', 'view_count': 75000, 'engagement_rate': 5.0},
        {'title': 'Step by Step Guide to React', 'view_count': 45000, 'engagement_rate': 4.2},
        {'title': 'Top 10 Programming Languages 2024', 'view_count': 120000, 'engagement_rate': 3.8},
        {'title': 'Best 5 Coding Tools', 'view_count': 80000, 'engagement_rate': 3.5},
        {'title': 'React vs Vue - Which is Better?', 'view_count': 95000, 'engagement_rate': 4.8},
        {'title': 'My Reaction to AI Taking Jobs', 'view_count': 30000, 'engagement_rate': 6.5},
        {'title': 'Day in the Life of a Developer', 'view_count': 25000, 'engagement_rate': 7.0},
    ]
    
    result = engine.cluster_channel_content(test_videos)
    
    print(f"\n📊 Clustering Results:")
    print(f"   Clusters Found: {len(result.clusters)}")
    print(f"   Best Performing: {result.best_performing_cluster}")
    
    for cluster in result.clusters:
        print(f"\n   📁 {cluster.name}:")
        print(f"      Videos: {cluster.video_count}")
        print(f"      Avg Views: {cluster.avg_views:,.0f}")
        print(f"      Score: {cluster.performance_score:.2f}")
    
    print(f"\n   💡 Recommendations:")
    for rec in result.recommendations:
        print(f"      • {rec}")
