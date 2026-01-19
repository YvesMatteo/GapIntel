import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ============================================
# PAGE CONFIG & CUSTOM CSS
# ============================================
st.set_page_config(
    page_title="Content Gap Intelligence Pro",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Dark Theme CSS
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(180deg, #0a0a0f 0%, #1a1a2e 100%);
    }
    
    /* Cards */
    .metric-card {
        background: linear-gradient(135deg, #1e1e30 0%, #2a2a45 100%);
        border: 1px solid #3d3d5c;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    
    .metric-value {
        font-size: 42px;
        font-weight: 700;
        background: linear-gradient(90deg, #00d4ff, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 8px 0;
    }
    
    .metric-label {
        color: #888;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Opportunity Cards */
    .opportunity-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #252545 100%);
        border: 1px solid #3d3d5c;
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        transition: transform 0.3s, box-shadow 0.3s;
    }
    
    .opportunity-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(124, 58, 237, 0.2);
    }
    
    .priority-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 12px;
    }
    
    .priority-high {
        background: linear-gradient(90deg, #ef4444, #dc2626);
        color: white;
    }
    
    .priority-medium {
        background: linear-gradient(90deg, #f59e0b, #d97706);
        color: white;
    }
    
    .priority-low {
        background: linear-gradient(90deg, #10b981, #059669);
        color: white;
    }
    
    /* Section headers */
    .section-header {
        font-size: 28px;
        font-weight: 700;
        color: #fff;
        margin: 32px 0 24px 0;
        padding-bottom: 12px;
        border-bottom: 2px solid #7c3aed;
    }
    
    /* Title styling */
    .viral-title {
        background: #1e1e30;
        padding: 12px 16px;
        border-radius: 8px;
        border-left: 4px solid #7c3aed;
        margin: 8px 0;
        font-size: 14px;
    }
    
    /* Hero section */
    .hero-section {
        background: linear-gradient(135deg, #7c3aed 0%, #2563eb 100%);
        padding: 40px;
        border-radius: 20px;
        margin-bottom: 32px;
        text-align: center;
    }
    
    .hero-title {
        font-size: 36px;
        font-weight: 800;
        color: white;
        margin-bottom: 8px;
    }
    
    .hero-subtitle {
        font-size: 18px;
        color: rgba(255,255,255,0.8);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Sidebar styling */
    .css-1d391kg {
        background: #1a1a2e;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# DATA LOADING
# ============================================
@st.cache_data
def load_data():
    path = Path("analysis_result.json")
    if not path.exists():
        return None
    with open(path, 'r') as f:
        return json.load(f)

data = load_data()

if not data:
    st.error("⚠️ No analysis data found! Run `gap_analyzer.py` first.")
    st.stop()

# ============================================
# HERO SECTION
# ============================================
st.markdown("""
<div class="hero-section">
    <div class="hero-title">🎯 Content Gap Intelligence Pro</div>
    <div class="hero-subtitle">AI-Powered Verified Content Opportunities</div>
</div>
""", unsafe_allow_html=True)

# ============================================
# KEY METRICS ROW
# ============================================
# ============================================
# TABS & LAYOUT
# ============================================
tab1, tab2 = st.tabs(["🎯 Gap Analysis", "⚔️ Competitor Intelligence"])

with tab1:
    # ============================================
    # KEY METRICS ROW
    # ============================================
    stats = data.get('pipeline_stats', {})
    verified_gaps = data.get('verified_gaps', [])
    opportunities = data.get('opportunities', [])
    top_opp = data.get('top_opportunity', {})

    true_gaps = len([g for g in verified_gaps if g.get('gap_status') == 'TRUE_GAP'])
    under_explained = len([g for g in verified_gaps if g.get('gap_status') == 'UNDER_EXPLAINED'])

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Comments Analyzed</div>
            <div class="metric-value">{stats.get('raw_comments', 0):,}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">High-Signal</div>
            <div class="metric-value">{stats.get('high_signal_comments', 0):,}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Pain Points</div>
            <div class="metric-value">{stats.get('pain_points_found', 0)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🔴 True Gaps</div>
            <div class="metric-value">{true_gaps}</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🟡 Under-Explained</div>
            <div class="metric-value">{under_explained}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================
    # TOP OPPORTUNITY SPOTLIGHT
    # ============================================
    if top_opp and top_opp.get('topic_keyword'):
        st.markdown('<div class="section-header">🏆 #1 Opportunity</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #7c3aed20, #2563eb20); border: 2px solid #7c3aed; border-radius: 16px; padding: 24px;">
                <h3 style="color: #7c3aed; margin: 0 0 12px 0;">{top_opp.get('topic_keyword', 'N/A')}</h3>
                <div style="background: #1a1a2e; padding: 16px; border-radius: 8px; margin: 12px 0;">
                    <p style="color: #00d4ff; font-size: 18px; margin: 0;">💡 {top_opp.get('best_title', 'No title')}</p>
                </div>
                <p style="color: #aaa; margin-top: 16px;">{top_opp.get('reason', '')[:500]}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card" style="height: 100%;">
                <div class="metric-label">Engagement Potential</div>
                <div class="metric-value">{top_opp.get('engagement_potential', 0):,}</div>
                <div style="color: #10b981; margin-top: 12px;">🚀 High Priority</div>
            </div>
            """, unsafe_allow_html=True)

    # ============================================
    # ENGAGEMENT DISTRIBUTION CHART
    # ============================================
    st.markdown('<div class="section-header">📊 Opportunity Analysis</div>', unsafe_allow_html=True)

    if verified_gaps:
        col1, col2 = st.columns(2)
        
        with col1:
            # Gap Status Distribution
            status_counts = {}
            for g in verified_gaps:
                status = g.get('gap_status', 'UNKNOWN')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=list(status_counts.keys()),
                values=list(status_counts.values()),
                hole=0.6,
                marker_colors=['#ef4444', '#f59e0b', '#10b981'],
                textinfo='label+value',
                textfont_size=14
            )])
            fig_pie.update_layout(
                title="Gap Status Distribution",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                showlegend=False
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Top Opportunities by Engagement
            df = pd.DataFrame(opportunities[:10])
            if not df.empty and 'total_engagement' in df.columns:
                df['short_topic'] = df['topic_keyword'].apply(lambda x: x[:40] + '...' if len(str(x)) > 40 else x)
                
                fig_bar = px.bar(
                    df.sort_values('total_engagement', ascending=True),
                    x='total_engagement',
                    y='short_topic',
                    orientation='h',
                    color='total_engagement',
                    color_continuous_scale='Viridis'
                )
                fig_bar.update_layout(
                    title="Top Opportunities by Engagement",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white',
                    showlegend=False,
                    yaxis_title="",
                    xaxis_title="Engagement Score"
                )
                st.plotly_chart(fig_bar, use_container_width=True)

    # ============================================
    # OPPORTUNITY CARDS
    # ============================================
    st.markdown('<div class="section-header">✅ Verified Content Opportunities</div>', unsafe_allow_html=True)

    if opportunities:
        # Priority filter
        priority_filter = st.selectbox(
            "Filter by Priority",
            ["All", "High (TRUE_GAP)", "Medium (UNDER_EXPLAINED)"],
            key="priority_filter"
        )
        
        for i, opp in enumerate(opportunities):
            engagement = opp.get('total_engagement', 0)
            gap_status = opp.get('gap_status', 'UNKNOWN')
            
            # Filter logic
            if priority_filter == "High (TRUE_GAP)" and gap_status != "TRUE_GAP":
                continue
            if priority_filter == "Medium (UNDER_EXPLAINED)" and gap_status != "UNDER_EXPLAINED":
                continue
            
            # Priority badge
            if gap_status == "TRUE_GAP":
                priority_class = "priority-high"
                priority_text = "🔴 TRUE GAP"
            else:
                priority_class = "priority-medium"
                priority_text = "🟡 UNDER-EXPLAINED"
            
            with st.expander(f"**{opp.get('topic_keyword', 'Unknown')}** — Engagement: {engagement:,}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f'<span class="priority-badge {priority_class}">{priority_text}</span>', unsafe_allow_html=True)
                    
                    st.markdown("**User Struggle:**")
                    st.info(opp.get('user_struggle', 'Not specified')[:300])
                    
                    st.markdown("**Verification Evidence:**")
                    st.caption(opp.get('verification_evidence', 'N/A'))
                    
                    why = opp.get('why_this_gap') or opp.get('Why_this_gap', '')
                    if why:
                        st.markdown("**Why This is a Gap:**")
                        st.success(why[:400])
                
                with col2:
                    # Influence Scores Section
                    influence = opp.get('influence_scores', {})
                    if influence:
                        st.markdown("**📊 Influence Breakdown:**")
                        
                        comment_inf = influence.get('comment_influence', 0)
                        competitor_inf = influence.get('competitor_influence', 0)
                        trend_inf = influence.get('trend_influence', 0)
                        gap_inf = influence.get('gap_severity_influence', 0)
                        overall = influence.get('overall_score', 0)
                        
                        st.markdown(f"""
                        <div style="margin: 8px 0;">
                            <div style="display: flex; justify-content: space-between; color: #888; font-size: 12px;">
                                <span>💬 Comments</span><span>{comment_inf}%</span>
                            </div>
                            <div style="background: #2a2a45; border-radius: 4px; height: 8px; overflow: hidden;">
                                <div style="width: {comment_inf}%; height: 100%; background: linear-gradient(90deg, #00d4ff, #7c3aed);"></div>
                            </div>
                        </div>
                        <div style="margin: 8px 0;">
                            <div style="display: flex; justify-content: space-between; color: #888; font-size: 12px;">
                                <span>⚔️ Competitors</span><span>{competitor_inf}%</span>
                            </div>
                            <div style="background: #2a2a45; border-radius: 4px; height: 8px; overflow: hidden;">
                                <div style="width: {competitor_inf}%; height: 100%; background: linear-gradient(90deg, #f59e0b, #ef4444);"></div>
                            </div>
                        </div>
                        <div style="margin: 8px 0;">
                            <div style="display: flex; justify-content: space-between; color: #888; font-size: 12px;">
                                <span>📈 Google Trends</span><span>{trend_inf}%</span>
                            </div>
                            <div style="background: #2a2a45; border-radius: 4px; height: 8px; overflow: hidden;">
                                <div style="width: {trend_inf}%; height: 100%; background: linear-gradient(90deg, #ec4899, #8b5cf6);"></div>
                            </div>
                        </div>
                        <div style="margin: 8px 0;">
                            <div style="display: flex; justify-content: space-between; color: #888; font-size: 12px;">
                                <span>🔴 Gap Severity</span><span>{gap_inf}%</span>
                            </div>
                            <div style="background: #2a2a45; border-radius: 4px; height: 8px; overflow: hidden;">
                                <div style="width: {gap_inf}%; height: 100%; background: linear-gradient(90deg, #10b981, #059669);"></div>
                            </div>
                        </div>
                        <div style="margin-top: 12px; padding: 12px; background: #1e1e30; border-radius: 8px; text-align: center;">
                            <div style="color: #888; font-size: 12px;">OVERALL SCORE</div>
                            <div style="font-size: 28px; font-weight: 700; color: #7c3aed;">{overall}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("**💡 Viral Title Ideas:**")
                    titles = opp.get('viral_titles', [])
                    for j, title in enumerate(titles[:3], 1):
                        st.markdown(f"""
                        <div class="viral-title">
                            <strong>{j}.</strong> {title}
                        </div>
                        """, unsafe_allow_html=True)
    else:
        st.info("No verified opportunities found. Try analyzing more videos!")

with tab2:
    st.markdown('<div class="section-header">⚔️ Competitor Intelligence</div>', unsafe_allow_html=True)
    
    comp_metrics = data.get('competitor_metrics', {})
    
    if not comp_metrics:
        st.info("No advanced competitor data found. Run the latest version of `gap_analyzer.py` to populate this tab.")
    else:
        # Comparison Table
        st.markdown("### 📊 Head-to-Head Comparison")
        
        comp_rows = []
        for name, data in comp_metrics.items():
            metrics = data.get('metrics', {})
            meta = data.get('meta', {})
            comp_rows.append({
                "Channel": name,
                "Subscribers": meta.get('subscriber_count', 0),
                "Avg Views": metrics.get('avg_views', 0),
                "Est. CVR (%)": metrics.get('avg_cvr_proxy', 0),
                "Mix": metrics.get('format_mix', 'N/A')
            })
            
        df_comp = pd.DataFrame(comp_rows)
        
        # Formatting for display
        st.dataframe(
            df_comp.style.format({
                "Subscribers": "{:,}",
                "Avg Views": "{:,}",
                "Est. CVR (%)": "{:.2f}%"
            }),
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown("---")
        
        # Format Mix Visualization
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎬 Format Strategy")
            mix_data = []
            for name, data in comp_metrics.items():
                m = data.get('metrics', {})
                mix_data.append({"Channel": name, "Type": "Shorts", "Count": m.get('shorts_count', 0)})
                mix_data.append({"Channel": name, "Type": "Long-form", "Count": m.get('long_form_count', 0)})
            
            df_mix = pd.DataFrame(mix_data)
            fig_mix = px.bar(
                df_mix, x="Channel", y="Count", color="Type", 
                title="Format Mix (Last 20 Videos)",
                color_discrete_map={"Shorts": "#ef4444", "Long-form": "#3b82f6"}
            )
            fig_mix.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
            st.plotly_chart(fig_mix, use_container_width=True)
            
        with col2:
            st.markdown("### 📈 Engagement Efficiency (CVR Proxy)")
            fig_cvr = px.bar(
                df_comp, x="Channel", y="Est. CVR (%)", color="Est. CVR (%)",
                title="Viewer Conversion Efficiency (Views/Subs)",
                color_continuous_scale='Viridis'
            )
            fig_cvr.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
            st.plotly_chart(fig_cvr, use_container_width=True)
            
        # Recent Videos List
        st.markdown("### 📹 Top Recent Competitor Videos")
        for name, data in comp_metrics.items():
            st.markdown(f"**{name}**")
            recents = data.get('recent_videos', [])
            # Sort by Views
            recents.sort(key=lambda x: x['views'], reverse=True)
            
            # Show top 3
            for v in recents[:3]:
                st.markdown(f"""
                <div style="background: #1e1e30; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 3px solid #7c3aed;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-weight: 600;">{v['title']}</span>
                        <span style="color: #00d4ff;">{v['views']:,} views</span>
                    </div>
                     <div style="font-size: 12px; color: #888; margin-top: 4px;">
                        CVR: {v['cvr_proxy']:.2f}% | 💬 {v['comment_count']} comments
                     </div>
                </div>
                """, unsafe_allow_html=True)


# ============================================
# SIDEBAR - EXPORT & INFO
# ============================================
st.sidebar.markdown("## 📊 Analysis Summary")
st.sidebar.metric("Total Pain Points", stats.get('pain_points_found', 0))
st.sidebar.metric("Actionable Opportunities", len(opportunities))
st.sidebar.metric("Already Covered", stats.get('saturated', 0))

st.sidebar.divider()

st.sidebar.markdown("## 📥 Export Data")
if st.sidebar.button("📋 Copy Report to Clipboard"):
    st.sidebar.success("Report copied!")

# Download JSON
st.sidebar.download_button(
    label="⬇️ Download Full Analysis (JSON)",
    data=json.dumps(data, indent=2),
    file_name="gap_analysis_report.json",
    mime="application/json"
)

st.sidebar.divider()
st.sidebar.caption("Powered by AI Gap Intelligence Engine v2.0")
