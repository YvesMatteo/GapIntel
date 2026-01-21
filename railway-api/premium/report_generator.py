"""
Premium Analysis - Report Generator
Generates comprehensive PDF/HTML reports for premium analysis.

Report Sections:
1. Executive Summary
2. Channel Health Score
3. Content Performance Analysis
4. Thumbnail Science Results
5. Competitor Benchmark Report
6. Gap Analysis & Opportunities
7. Next 30-Day Content Calendar
8. Specific Action Items
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json


@dataclass
class ReportSection:
    """A section of the premium report."""
    title: str
    content: str
    charts: List[Dict]
    key_metrics: List[Dict]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class PremiumReportGenerator:
    """
    Generates comprehensive premium analysis reports.
    
    Formats:
    - HTML (for web display)
    - JSON (for API responses)
    """
    
    def __init__(self):
        self.report_sections = []
    
    def generate_premium_report(self, analysis_results: Dict) -> Dict:
        """
        Generate a full premium report from analysis results.
        
        Args:
            analysis_results: Combined results from all analysis modules
            
        Returns:
            Complete report as structured dict (easily convertible to HTML/PDF)
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'report_type': 'premium_analysis',
            'version': '1.0',
            'sections': []
        }
        
        # 1. Executive Summary
        report['sections'].append(
            self._generate_executive_summary(analysis_results)
        )
        
        # 2. Channel Health Score
        report['sections'].append(
            self._generate_health_score(analysis_results)
        )
        
        # 3. Content Performance Analysis
        report['sections'].append(
            self._generate_content_analysis(analysis_results)
        )
        
        # 4. Thumbnail Analysis
        report['sections'].append(
            self._generate_thumbnail_section(analysis_results)
        )
        
        # 5. Competitor Benchmark
        report['sections'].append(
            self._generate_competitor_section(analysis_results)
        )
        
        # 6. Gap Analysis
        report['sections'].append(
            self._generate_gap_section(analysis_results)
        )
        
        # 7. Content Calendar
        report['sections'].append(
            self._generate_content_calendar(analysis_results)
        )
        
        # 8. Action Items
        report['sections'].append(
            self._generate_action_items(analysis_results)
        )
        
        return report
    
    def _generate_executive_summary(self, results: Dict) -> Dict:
        """Generate executive summary section."""
        channel = results.get('channel', {})
        
        # Calculate overall health
        health_score = self._calculate_health_score(results)
        
        # Key findings
        findings = []
        
        if results.get('thumbnail_analysis'):
            score = results['thumbnail_analysis'].get('avg_quality_score')
            if score:
                findings.append(f"Average Thumbnail Quality: {score:.1f}/100")
        
        if results.get('competitor_analysis'):
            comp_count = len(results['competitor_analysis'].get('competitors', []))
            findings.append(f"Analyzed {comp_count} competitor channels")
        
        if results.get('gap_analysis'):
            gaps = len(results['gap_analysis'].get('opportunities', []))
            findings.append(f"Found {gaps} content opportunities")
        
        return {
            'title': 'Executive Summary',
            'type': 'summary',
            'content': {
                'channel_name': channel.get('channel_name', 'Unknown'),
                'health_score': health_score,
                'health_grade': self._score_to_grade(health_score),
                'key_findings': findings,
                'primary_recommendation': self._get_primary_recommendation(results),
                'analysis_date': datetime.now().strftime('%B %d, %Y')
            }
        }
    
    def _generate_health_score(self, results: Dict) -> Dict:
        """Generate channel health score section."""
        scores = {
            'content_quality': 0,
            'posting_consistency': 0,
            'engagement_rate': 0,
            'growth_trajectory': 0,
            'thumbnail_effectiveness': 0,
            'competitive_position': 0
        }
        
        # Calculate individual scores
        channel = results.get('channel', {})
        
        # Content quality from clustering
        if results.get('content_clustering'):
            top_cluster = results['content_clustering'].get('clusters', [{}])[0]
            scores['content_quality'] = int(top_cluster.get('performance_score', 0.5) * 100)
        else:
            scores['content_quality'] = 60
        
        # Posting consistency
        freq = channel.get('upload_frequency_days', 7)
        if freq <= 3:
            scores['posting_consistency'] = 90
        elif freq <= 7:
            scores['posting_consistency'] = 70
        else:
            scores['posting_consistency'] = max(30, 100 - freq * 3)
        
        # Engagement from videos
        if results.get('videos'):
            avg_engagement = sum(v.get('engagement_rate', 0) for v in results['videos']) / len(results['videos'])
            scores['engagement_rate'] = min(100, int(avg_engagement * 15))
        else:
            scores['engagement_rate'] = 50
        
        # Growth trajectory (requires historical data)
        # scores['growth_trajectory'] = 65  # Removed placeholder
        
        # Thumbnail effectiveness
        if results.get('thumbnail_analysis'):
            ctr_score = results['thumbnail_analysis'].get('quality_score', 0)
            scores['thumbnail_effectiveness'] = ctr_score
        else:
            scores['thumbnail_effectiveness'] = 50
        
        # Competitive position
        if results.get('competitor_analysis'):
            comp = results['competitor_analysis']
            if comp.get('views_comparison', {}).get('verdict') == 'outperforming':
                scores['competitive_position'] = 80
            else:
                scores['competitive_position'] = 50
        else:
            scores['competitive_position'] = 60
        
        overall = int(sum(scores.values()) / len(scores))
        
        return {
            'title': 'Channel Health Score',
            'type': 'health_score',
            'content': {
                'overall_score': overall,
                'overall_grade': self._score_to_grade(overall),
                'breakdown': scores,
                'strengths': [k for k, v in scores.items() if v >= 70],
                'improvements_needed': [k for k, v in scores.items() if v < 50]
            }
        }
    
    def _generate_content_analysis(self, results: Dict) -> Dict:
        """Generate content performance analysis section."""
        videos = results.get('videos', [])
        clustering = results.get('content_clustering', {})
        
        # Top performers
        top_videos = sorted(videos, key=lambda v: v.get('view_count', 0), reverse=True)[:5]
        
        # Format distribution
        clusters = clustering.get('clusters', [])
        
        return {
            'title': 'Content Performance Analysis',
            'type': 'content_analysis',
            'content': {
                'total_videos_analyzed': len(videos),
                'avg_views': int(sum(v.get('view_count', 0) for v in videos) / len(videos)) if videos else 0,
                'avg_engagement': round(sum(v.get('engagement_rate', 0) for v in videos) / len(videos), 2) if videos else 0,
                'top_performers': [
                    {'title': v.get('title', '')[:50], 'views': v.get('view_count', 0)}
                    for v in top_videos
                ],
                'content_clusters': [
                    {'name': c.get('name', ''), 'videos': c.get('video_count', 0), 'avg_views': c.get('avg_views', 0)}
                    for c in clusters[:5]
                ],
                'recommendations': clustering.get('recommendations', [])
            }
        }
    
    def _generate_thumbnail_section(self, results: Dict) -> Dict:
        """Generate thumbnail analysis section."""
        thumb = results.get('thumbnail_analysis', {})
        
        return {
            'title': 'Thumbnail Science Analysis',
            'type': 'thumbnail_analysis',
            'content': {
                'analyzed_thumbnails': thumb.get('count', 0),
                'avg_quality_score': thumb.get('avg_quality_score', 0),
                'common_patterns': thumb.get('patterns', []),
                'improvement_opportunities': thumb.get('improvements', []),
                'best_practices': [
                    "Use high contrast text for readability",
                    "Ensure main subject is clearly visible",
                    "Use complementary colors to make elements pop",
                    "Test readability at mobile scale"
                ],
                'ab_test_suggestions': thumb.get('ab_suggestions', [])
            }
        }
    
    def _generate_competitor_section(self, results: Dict) -> Dict:
        """Generate competitor benchmark section."""
        comp = results.get('competitor_analysis', {})
        
        return {
            'title': 'Competitor Benchmark Report',
            'type': 'competitor_analysis',
            'content': {
                'competitors_analyzed': len(comp.get('competitors', [])),
                'your_position': comp.get('views_comparison', {}).get('verdict', 'N/A'),
                'view_comparison': comp.get('views_comparison', {}),
                'engagement_comparison': comp.get('engagement_comparison', {}),
                'competitor_details': [
                    {
                        'name': c.get('channel_name', ''),
                        'subscribers': c.get('subscriber_count', 0),
                        'avg_views': c.get('avg_views_per_video', 0)
                    }
                    for c in comp.get('competitors', [])[:5]
                ],
                'competitive_advantages': comp.get('advantages', []),
                'areas_to_improve': comp.get('improvements', [])
            }
        }
    
    def _generate_gap_section(self, results: Dict) -> Dict:
        """Generate gap analysis section."""
        gaps = results.get('gap_analysis', {})
        
        return {
            'title': 'Gap Analysis & Opportunities',
            'type': 'gap_analysis',
            'content': {
                'total_opportunities': len(gaps.get('opportunities', [])),
                'top_opportunities': [
                    {
                        'topic': opp.get('topic', ''),
                        'score': opp.get('opportunity_score', 0),
                        'source': opp.get('source', '')
                    }
                    for opp in gaps.get('opportunities', [])[:5]
                ],
                'quick_wins': gaps.get('quick_wins', []),
                'long_term_plays': gaps.get('long_term_plays', []),
                'topics_to_avoid': gaps.get('avoid_topics', [])
            }
        }
    
    def _generate_content_calendar(self, results: Dict) -> Dict:
        """Generate 30-day content calendar suggestion."""
        opportunities = results.get('gap_analysis', {}).get('opportunities', [])
        publish_times = results.get('publish_optimization', {})
        
        # Generate calendar entries
        calendar = []
        base_date = datetime.now()
        
        for i, opp in enumerate(opportunities[:8]):
            pub_date = base_date + timedelta(days=(i * 4) + 1)
            
            calendar.append({
                'week': (i // 2) + 1,
                'date': pub_date.strftime('%B %d'),
                'topic': opp.get('topic', f'Video {i+1}'),
                'format': opp.get('execution_guidance', {}).get('video_format', 'video'),
                'priority': 'high' if i < 3 else 'medium'
            })
        
        return {
            'title': 'Next 30-Day Content Calendar',
            'type': 'content_calendar',
            'content': {
                'suggested_uploads': calendar,
                'recommended_frequency': '2-3 videos per week',
                'best_publish_times': publish_times.get('schedule_recommendations', [
                    {'day': 'Tuesday', 'hour_utc': 14},
                    {'day': 'Thursday', 'hour_utc': 14},
                    {'day': 'Saturday', 'hour_utc': 10}
                ]),
                'content_mix': {}  # Dynamic mix removed until sufficient data available
            }
        }
    
    def _generate_action_items(self, results: Dict) -> Dict:
        """Generate prioritized action items."""
        actions = []
        
        # Thumbnail actions
        if results.get('thumbnail_analysis', {}).get('improvements'):
            for imp in results['thumbnail_analysis']['improvements'][:2]:
                actions.append({
                    'priority': 1,
                    'category': 'Thumbnails',
                    'action': imp,
                    'impact': 'High',
                    'effort': 'Low'
                })
        
        # Content actions
        if results.get('gap_analysis', {}).get('quick_wins'):
            for win in results['gap_analysis']['quick_wins'][:2]:
                actions.append({
                    'priority': 2,
                    'category': 'Content',
                    'action': f"Create video: {win}",
                    'impact': 'High',
                    'effort': 'Medium'
                })
        
        # Competitor actions
        if results.get('competitor_analysis', {}).get('improvements'):
            for comp_action in results['competitor_analysis']['improvements'][:1]:
                actions.append({
                    'priority': 3,
                    'category': 'Strategy',
                    'action': comp_action,
                    'impact': 'Medium',
                    'effort': 'Medium'
                })
        
        # Default actions if none generated
        if not actions:
            actions = [
                {'priority': 1, 'category': 'Thumbnails', 'action': 'Add faces to all thumbnails', 'impact': 'High', 'effort': 'Low'},
                {'priority': 2, 'category': 'Content', 'action': 'Post consistently 2-3x per week', 'impact': 'High', 'effort': 'Medium'},
                {'priority': 3, 'category': 'Engagement', 'action': 'Respond to comments within 24h', 'impact': 'Medium', 'effort': 'Low'}
            ]
        
        return {
            'title': 'Priority Action Items',
            'type': 'action_items',
            'content': {
                'total_actions': len(actions),
                'immediate_actions': [a for a in actions if a['priority'] == 1],
                'this_week': [a for a in actions if a['priority'] == 2],
                'this_month': [a for a in actions if a['priority'] == 3],
                'estimated_impact': "Implementing these changes can significantly improve channel performance."
            }
        }
    
    def _calculate_health_score(self, results: Dict) -> int:
        """Calculate overall channel health score."""
        scores = []
        
        if results.get('channel', {}).get('subscriber_count', 0) > 0:
            scores.append(60)
        
        if results.get('videos'):
            avg_views = sum(v.get('view_count', 0) for v in results['videos']) / len(results['videos'])
            scores.append(min(100, int(avg_views / 1000)))
        
        if results.get('thumbnail_analysis'):
            scores.append(results['thumbnail_analysis'].get('quality_score', 50))
        
        return int(sum(scores) / len(scores)) if scores else 50
    
    def _score_to_grade(self, score: int) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        elif score >= 50:
            return 'D'
        else:
            return 'F'
    
    def _get_primary_recommendation(self, results: Dict) -> str:
        """Get the single most important recommendation."""
        # Check for low-hanging fruit
        if results.get('thumbnail_analysis', {}).get('avg_quality_score', 50) < 60:
            return "Focus on improving thumbnails - high quality thumbnails are crucial for growth"
        
        if results.get('gap_analysis', {}).get('quick_wins'):
            return f"Create content on: {results['gap_analysis']['quick_wins'][0]}"
        
        return "Maintain consistency - post 2-3 videos per week on a regular schedule"
    
    def to_html(self, report: Dict) -> str:
        """Convert report dict to HTML format."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Premium Analysis Report - {report['sections'][0]['content'].get('channel_name', 'Channel')}</title>
    <style>
        body {{ font-family: 'Inter', sans-serif; max-width: 900px; margin: 0 auto; padding: 40px; background: #0a0a0a; color: #fff; }}
        .section {{ background: #1a1a2e; border-radius: 12px; padding: 24px; margin-bottom: 24px; }}
        .section h2 {{ color: #22c55e; margin-top: 0; }}
        .metric {{ display: inline-block; background: #16213e; padding: 12px 20px; border-radius: 8px; margin: 8px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #22c55e; }}
        .metric-label {{ font-size: 12px; color: #aaa; }}
        .grade {{ font-size: 48px; font-weight: bold; color: #22c55e; }}
        .action-item {{ background: #16213e; padding: 12px; border-radius: 8px; margin: 8px 0; border-left: 4px solid #22c55e; }}
        .high-priority {{ border-left-color: #ef4444; }}
        ul {{ padding-left: 20px; }}
        li {{ margin: 8px 0; }}
    </style>
</head>
<body>
    <h1>🚀 Premium Analysis Report</h1>
    <p>Generated: {report['generated_at']}</p>
"""
        
        for section in report['sections']:
            html += f"""
    <div class="section">
        <h2>{section['title']}</h2>
        <pre>{json.dumps(section['content'], indent=2)}</pre>
    </div>
"""
        
        html += """
</body>
</html>
"""
        return html


# === Quick test ===
if __name__ == "__main__":
    print("🧪 Testing Premium Report Generator...")
    
    generator = PremiumReportGenerator()
    
    # Sample analysis results
    sample_results = {
        'channel': {
            'channel_name': 'Test Channel',
            'subscriber_count': 50000,
            'upload_frequency_days': 5
        },
        'videos': [
            {'title': 'Video 1', 'view_count': 25000, 'engagement_rate': 4.5},
            {'title': 'Video 2', 'view_count': 35000, 'engagement_rate': 5.0},
        ],
        'thumbnail_analysis': {
            'count': 10,
            'avg_ctr': 5.2,
            'patterns': ['faces', 'text overlay'],
            'improvements': ['Add more contrast', 'Use bolder text']
        },
        'gap_analysis': {
            'opportunities': [
                {'topic': 'Tutorial Series', 'opportunity_score': 85, 'source': 'comment'}
            ],
            'quick_wins': ['How-to Guide', 'Comparison Video'],
            'long_term_plays': ['Build a course']
        }
    }
    
    report = generator.generate_premium_report(sample_results)
    
    print(f"\n📊 Report Generated:")
    print(f"   Sections: {len(report['sections'])}")
    print(f"   Generated at: {report['generated_at']}")
    
    for section in report['sections']:
        print(f"\n   📄 {section['title']}")
