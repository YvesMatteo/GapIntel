import Link from "next/link";
import Image from "next/image";
import { createClient } from "@supabase/supabase-js";
import { CheckCircle, AlertCircle, Clock, TrendingUp, Search, BarChart3, Calendar, ArrowRight, Play, Youtube, Eye, MessageCircle, Sparkles } from "lucide-react";
import ReportActions from "@/components/ReportActions";

// Initialize Supabase client for server component
const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
);

// Types for the analysis result
interface GapItem {
    rank: number;
    topic: string;
    status: "TRUE_GAP" | "UNDER_EXPLAINED";
    userStruggle: string;
    engagement: number;
    verification: string;
    reasoning: string;
    suggestedTitles: string[];
}

interface AnalysisResult {
    channelName?: string;
    pipeline?: {
        rawComments: number;
        highSignal: number;
        painPoints: number;
        trueGaps: number;
        underExplained: number;
        alreadyCovered: number;
    };
    top_gap?: {
        topic: string;
        title_suggestion: string;
        engagement_score: number;
        reasoning: string;
    };
    verified_gaps?: Array<{
        topic: string;
        status: string;
        user_struggle: string;
        engagement_score: number;
        transcript_evidence: string;
        reasoning: string;
        title_suggestions: string[];
    }>;
    already_covered?: Array<{
        topic: string;
        explanation: string;
    }>;
    videos_analyzed?: Array<{
        title: string;
        comments_count: number;
        video_id: string;
    }>;
    competitors?: string[];
    raw_report?: string;
    error?: string;
    pipeline_stats?: {
        raw_comments: number;
        high_signal_comments: number;
        pain_points_found: number;
        true_gaps: number;
        under_explained: number;
        saturated: number;
    };
    // Premium Analysis Data
    premium?: {
        tier: string;
        ctr_prediction?: {
            channel_avg_predicted_ctr: number;
            video_predictions: Array<{
                video_title: string;
                predicted_ctr: number;
                confidence: number;
                positive_factors: Array<{ factor: string; impact: number }>;
                negative_factors: Array<{ factor: string; impact: number }>;
                suggestions: string[];
            }>;
            top_improvement: string | null;
        };
        thumbnail_analysis?: {
            mode: 'basic' | 'advanced';
            videos_analyzed: Array<{
                video_title: string;
                predicted_ctr: number;
                potential_improvement: string;
                score_breakdown: Record<string, number>;
                issues: Array<{ issue: string; severity: string; fix: string }>;
                ab_test_suggestions?: Array<{ variant: string; description: string; expected_lift: string }>;
                optimized_concept?: Record<string, unknown>;
            }>;
        };
        views_forecast?: {
            forecasts: Array<{
                video_title: string;
                predicted_7d_views: number;
                predicted_30d_views: number;
                viral_probability: number;
                trajectory_type: string;
                vs_channel_avg: string;
            }>;
            avg_viral_probability: number;
        };
        competitor_intel?: {
            competitors_tracked: number;
            max_allowed: number;
            competitors: Array<{
                channel_name: string;
                subscriber_count: number;
                avg_views: number;
                avg_engagement: number;
                upload_frequency_days: number;
                top_formats: string[];
                posting_days: string[];
            }>;
        };
        content_clusters?: {
            clusters: Array<{
                id: number;
                name: string;
                video_count: number;
                avg_views: number;
                avg_engagement: number;
                performance_score: number;
                common_elements: string[];
                best_performer: Record<string, unknown>;
                example_titles: string[];
            }>;
            best_performing: string;
            underperforming: string[];
            gap_opportunities: string[];
            recommendations: string[];
        };
        publish_times?: {
            best_days: string[];
            best_hours_utc: number[];
            recommendations: Array<{ day: string; hour: number; boost: string; reasoning: string }>;
            avoid_times: Array<{ day: string; hour: number; reason: string }>;
            content_advice: Record<string, string>;
        };
        hook_analysis?: {
            videos_analyzed: number;
            avg_hook_score: number;
            best_patterns: Array<{ pattern: string; avg_views: number }>;
            recommendations: string[];
            top_hooks: Array<{ title: string; views: number; patterns: string[]; opening: string }>;
            pattern_performance: Record<string, number>;
        };
        color_insights?: {
            total_videos: number;
            best_color_temperatures: Array<{ temperature: string; avg_views: number }>;
            top_performing_colors: string[];
            color_recommendations: string[];
            temperature_performance: Record<string, number>;
        };
        visual_charts?: {
            hook_patterns?: { chart_type: string; title: string; svg_data_uri: string };
            color_temperature?: { chart_type: string; title: string; svg_data_uri: string };
            top_colors?: { chart_type: string; title: string; svg_data_uri: string };
            ctr_gauge?: { chart_type: string; title: string; svg_data_uri: string };
        };
    };
}

interface AnalysisRow {
    id: string;
    channel_name: string;
    email?: string;
    status: string;
    report_data: AnalysisResult | null;
    created_at: string;
    updated_at: string | null;
}

async function getAnalysis(accessKey: string): Promise<AnalysisRow | null> {
    const { data, error } = await supabase
        .from("user_reports")
        .select("*")
        .eq("access_key", accessKey)
        .single();

    if (error || !data) {
        return null;
    }

    return data as AnalysisRow;
}

function transformToDashboardFormat(result: AnalysisResult, channelName: string) {
    const gaps = result.verified_gaps || [];
    const topGap = result.top_gap || gaps[0];

    return {
        channelName: result.channelName || channelName,
        generatedAt: new Date().toISOString(),
        videosAnalyzed: result.videos_analyzed?.length || 0,
        pipeline: result.pipeline_stats ? {
            rawComments: result.pipeline_stats.raw_comments || 0,
            highSignal: result.pipeline_stats.high_signal_comments || 0,
            painPoints: result.pipeline_stats.pain_points_found || 0,
            trueGaps: result.pipeline_stats.true_gaps || 0,
            underExplained: result.pipeline_stats.under_explained || 0,
            alreadyCovered: result.pipeline_stats.saturated || 0,
        } : {
            rawComments: 0,
            highSignal: 0,
            painPoints: 0,
            trueGaps: gaps.filter(g => g.status === "TRUE_GAP").length,
            underExplained: gaps.filter(g => g.status === "UNDER_EXPLAINED").length,
            alreadyCovered: result.already_covered?.length || 0,
        },
        topOpportunity: topGap ? {
            topic: (topGap as unknown as Record<string, string>).topic || "Analysis pending",
            suggestedTitle: (topGap as unknown as Record<string, string>).title_suggestion || (topGap as unknown as Record<string, string[]>).title_suggestions?.[0] || "",
            engagementPotential: (topGap as unknown as Record<string, number>).engagement_score || 0,
            reasoning: (topGap as unknown as Record<string, string>).reasoning || "",
        } : null,
        contentGaps: gaps.map((gap, i) => ({
            rank: i + 1,
            topic: gap.topic,
            status: gap.status === "TRUE_GAP" ? "TRUE_GAP" : "UNDER_EXPLAINED",
            userStruggle: gap.user_struggle || "",
            engagement: gap.engagement_score || 0,
            verification: gap.transcript_evidence || "",
            reasoning: gap.reasoning || "",
            suggestedTitles: gap.title_suggestions || [],
        })),
        alreadyCovered: result.already_covered || [],
        videosAnalyzedList: result.videos_analyzed?.map(v => ({
            title: v.title,
            comments: v.comments_count,
            url: `https://youtube.com/watch?v=${v.video_id}`,
        })) || [],
        competitors: result.competitors || [],
    };
}

export default async function DashboardPage({ params }: { params: Promise<{ key: string }> }) {
    const { key } = await params;
    const analysis = await getAnalysis(key);

    if (!analysis) {
        return (
            <main className="min-h-screen flex items-center justify-center bg-[#FAFAFA]">
                <div className="text-center max-w-md mx-auto px-6">
                    <div className="bg-white rounded-[32px] shadow-xl border border-slate-100 p-12">
                        <div className="text-6xl mb-6">🔍</div>
                        <h1 className="text-2xl font-serif font-medium text-slate-900 mb-4">Report Not Found</h1>
                        <p className="text-slate-500 mb-6">
                            We couldn't find a report with this access key.
                        </p>
                        <Link href="/dashboard" className="inline-block bg-slate-900 text-white px-8 py-3 rounded-full font-medium hover:bg-slate-800 transition">
                            Back to Dashboard
                        </Link>
                    </div>
                </div>
            </main>
        );
    }

    if (analysis.status === "pending" || analysis.status === "processing") {
        return (
            <main className="min-h-screen flex items-center justify-center bg-[#FAFAFA]">
                <div className="text-center max-w-md mx-auto px-6">
                    <div className="bg-white rounded-[32px] shadow-xl border border-slate-100 p-12">
                        <div className="relative w-20 h-20 mx-auto mb-8">
                            <div className="w-full h-full border-4 border-slate-100 rounded-full animate-pulse"></div>
                            <div className="absolute top-0 left-0 w-full h-full border-4 border-t-blue-500 rounded-full animate-spin"></div>
                        </div>
                        <h1 className="text-3xl font-serif font-medium text-slate-900 mb-4">Analyzing Content</h1>
                        <p className="text-slate-500 mb-8">
                            Our AI is watching videos, reading comments, and finding gaps for <strong className="text-slate-900">@{analysis.channel_name}</strong>.
                        </p>
                        <div className="bg-slate-50 rounded-2xl p-4 mb-6">
                            <span className="text-sm font-medium text-slate-700 uppercase tracking-wider">
                                Status: {analysis.status === "pending" ? "Queued" : "Processing"}
                            </span>
                        </div>
                        <Link href={`/report/${key}`} className="inline-block bg-white border border-slate-200 text-slate-900 px-6 py-3 rounded-full font-medium hover:bg-slate-50 transition shadow-sm">
                            Refresh Status
                        </Link>
                    </div>
                </div>
            </main>
        );
    }

    if (analysis.status === "failed") {
        return (
            <main className="min-h-screen flex items-center justify-center bg-[#FAFAFA]">
                <div className="text-center">
                    <div className="bg-white rounded-[32px] p-12 max-w-md mx-auto border border-slate-100 shadow-xl">
                        <div className="text-6xl mb-6">❌</div>
                        <h1 className="text-2xl font-bold text-slate-900 mb-4">Analysis Failed</h1>
                        <p className="text-slate-500 mb-8">{analysis.report_data?.error || "Unknown error occurred"}</p>
                        <Link href="/dashboard" className="text-blue-600 hover:underline">
                            Return to Dashboard
                        </Link>
                    </div>
                </div>
            </main>
        );
    }

    const report = transformToDashboardFormat(analysis.report_data || {}, analysis.channel_name);

    return (
        <div className="min-h-screen bg-[#FAFAFA] text-slate-900 selection:bg-blue-100 selection:text-blue-900">
            {/* Nav */}
            <header className="fixed top-0 w-full bg-white/80 backdrop-blur-md border-b border-slate-100 z-50">
                <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center text-white font-serif font-bold">G</div>
                        <span className="font-serif text-xl font-medium tracking-tight">GAP Intel</span>
                    </Link>
                    <div className="flex items-center gap-3">
                        <Link href={`/viral-predictor?key=${key}`}>
                            <button className="h-10 px-5 rounded-full bg-purple-600 text-white hover:bg-purple-700 transition font-medium text-sm flex items-center gap-2 shadow-lg shadow-purple-500/20">
                                <Sparkles size={16} /> Predict Viral Video
                            </button>
                        </Link>
                        <Link href="/dashboard">
                            <button className="h-10 px-5 rounded-full bg-slate-100 text-slate-600 hover:bg-slate-200 transition font-medium text-sm">Dashboard</button>
                        </Link>
                    </div>
                </div>
            </header>

            <main className="pt-32 pb-20 px-6">
                <div className="max-w-7xl mx-auto space-y-8">

                    {/* Header Section */}
                    <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                        <div>
                            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-50 border border-green-100 text-green-700 text-xs font-bold uppercase tracking-wider mb-4">
                                Completed Successfully
                            </div>
                            <h1 className="text-4xl md:text-5xl font-serif font-medium text-slate-900 mb-4">
                                Content Strategy Report
                            </h1>
                            <p className="text-lg text-slate-500 max-w-2xl">
                                Detailed analysis of {report.videosAnalyzed} videos, audience sentiment, and missed opportunities.
                            </p>
                        </div>
                        <ReportActions channelName={analysis.channel_name} accessKey={key} />
                    </div>

                    {/* Stats Grid */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                        {[
                            { label: "Comments Analyzed", value: report.pipeline.rawComments.toLocaleString(), icon: MessageCircle, color: "text-blue-600", bg: "bg-blue-50" },
                            { label: "Pain Points Found", value: report.pipeline.painPoints.toLocaleString(), icon: AlertCircle, color: "text-orange-600", bg: "bg-orange-50" },
                            { label: "Content Gaps", value: report.pipeline.trueGaps, icon: Search, color: "text-green-600", bg: "bg-green-50" },
                            { label: "Videos Scanned", value: report.videosAnalyzed, icon: Play, color: "text-purple-600", bg: "bg-purple-50" },
                        ].map((stat, i) => (
                            <div key={i} className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm flex flex-col justify-between h-32">
                                <div className="flex justify-between items-start">
                                    <div className={`w-10 h-10 rounded-xl ${stat.bg} flex items-center justify-center ${stat.color}`}>
                                        <stat.icon className="w-5 h-5" />
                                    </div>
                                </div>
                                <div>
                                    <div className="text-2xl font-bold text-slate-900">{stat.value}</div>
                                    <div className="text-sm text-slate-500 font-medium">{stat.label}</div>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Top Opportunity */}
                    {report.topOpportunity && (
                        <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-[32px] p-8 md:p-12 text-white relative overflow-hidden shadow-2xl shadow-slate-900/20">
                            <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/20 blur-3xl rounded-full -mr-32 -mt-32 pointer-events-none"></div>

                            <div className="relative z-10 grid md:grid-cols-3 gap-12">
                                <div className="md:col-span-2">
                                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/20 text-white text-xs font-bold uppercase tracking-wider mb-6">
                                        Top Opportunity
                                    </div>
                                    <h2 className="text-3xl md:text-4xl font-serif font-medium mb-6 leading-tight">
                                        {report.topOpportunity.topic}
                                    </h2>
                                    <p className="text-slate-300 text-lg leading-relaxed mb-8">
                                        {report.topOpportunity.reasoning}
                                    </p>
                                    <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                                        <div className="text-xs text-slate-400 uppercase tracking-widest font-bold mb-2">SUGGESTED TITLE</div>
                                        <div className="text-xl font-medium">{report.topOpportunity.suggestedTitle}</div>
                                    </div>
                                </div>
                                <div className="flex flex-col justify-center items-center md:items-end border-t md:border-t-0 md:border-l border-white/10 pt-8 md:pt-0 md:pl-12">
                                    <div className="text-center md:text-right">
                                        <div className="text-6xl font-bold text-green-400 mb-2">{report.topOpportunity.engagementPotential}</div>
                                        <div className="text-slate-400 font-medium">Engagement Score</div>
                                        <div className="text-xs text-slate-500 mt-2">out of 100</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Verified Gaps */}
                    <div>
                        <h2 className="text-2xl font-serif font-medium text-slate-900 mb-6">Verified Content Gaps</h2>
                        <div className="grid md:grid-cols-2 gap-6">
                            {report.contentGaps.map((gap, i) => (
                                <div key={i} className="bg-white rounded-[32px] p-8 border border-slate-100 shadow-xl shadow-slate-200/50 hover:border-blue-200 transition-colors group h-full flex flex-col">
                                    <div className="flex justify-between items-start mb-6">
                                        <span className="w-10 h-10 rounded-full bg-slate-50 flex items-center justify-center font-bold text-slate-900 border border-slate-200">
                                            {gap.rank}
                                        </span>
                                        <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${gap.status === 'TRUE_GAP' ? 'bg-green-50 text-green-700 border border-green-100' : 'bg-purple-50 text-purple-700 border border-purple-100'}`}>
                                            {gap.status.replace('_', ' ')}
                                        </span>
                                    </div>
                                    <h3 className="text-xl font-bold text-slate-900 mb-3">{gap.topic}</h3>
                                    <p className="text-slate-600 mb-6 flex-1">{gap.userStruggle}</p>

                                    {gap.suggestedTitles[0] && (
                                        <div className="bg-slate-50 rounded-2xl p-4 mt-auto">
                                            <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                                                <Play className="w-3 h-3" /> Potential Video
                                            </div>
                                            <div className="font-medium text-slate-900 line-clamp-2">{gap.suggestedTitles[0]}</div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Premium Sections using Carousel-like cards */}
                    {analysis.report_data?.premium && (
                        <div className="space-y-12 pt-12 border-t border-slate-200">
                            <div className="flex items-center gap-4">
                                <div className="h-px bg-slate-200 flex-1"></div>
                                <h2 className="text-lg font-bold text-slate-400 uppercase tracking-widest">Premium Intelligence</h2>
                                <div className="h-px bg-slate-200 flex-1"></div>
                            </div>

                            {/* Thumbnail Analysis */}
                            {analysis.report_data.premium.thumbnail_analysis && (
                                <div className="bg-white rounded-[32px] border border-slate-100 shadow-xl shadow-slate-200/50 overflow-hidden">
                                    <div className="p-8 border-b border-slate-100 bg-slate-50/50">
                                        <h3 className="text-2xl font-serif font-medium text-slate-900">Thumbnail Optimization</h3>
                                        <p className="text-slate-500 mt-2">AI-powered analysis of your recent thumbnails to predict click-through rate.</p>
                                    </div>
                                    <div className="grid md:grid-cols-2 divide-y md:divide-y-0 md:divide-x border-slate-100 max-h-[600px] overflow-y-auto">
                                        {analysis.report_data.premium.thumbnail_analysis.videos_analyzed?.map((video, i) => (
                                            <div key={i} className="p-8 hover:bg-slate-50/30 transition-colors">
                                                <div className="flex justify-between items-start mb-4">
                                                    <h4 className="font-bold text-slate-900 line-clamp-1 pr-4">{video.video_title}</h4>
                                                    <div className="text-right">
                                                        <div className="text-2xl font-bold text-purple-600">{video.predicted_ctr}%</div>
                                                        <div className="text-xs text-slate-400 font-bold uppercase">CTR</div>
                                                    </div>
                                                </div>
                                                {video.issues.length > 0 ? (
                                                    <ul className="space-y-3">
                                                        {video.issues.map((issue, j) => (
                                                            <li key={j} className="flex gap-3 text-sm">
                                                                <AlertCircle className="w-5 h-5 text-amber-500 shrink-0" />
                                                                <div>
                                                                    <span className="font-medium text-slate-700">{issue.issue}</span>
                                                                    <p className="text-slate-500 mt-0.5">{issue.fix}</p>
                                                                </div>
                                                            </li>
                                                        ))}
                                                    </ul>
                                                ) : (
                                                    <div className="flex items-center gap-2 text-green-600 font-medium">
                                                        <CheckCircle className="w-5 h-5" /> Excellent thumbnail!
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Views Forecast */}
                            {analysis.report_data.premium.views_forecast && (
                                <div className="grid md:grid-cols-2 gap-8">
                                    <div className="bg-[#1c1c1e] text-white rounded-[32px] p-8 flex flex-col justify-center text-center">
                                        <h3 className="text-2xl font-serif font-medium mb-2">Viral Probability</h3>
                                        <div className="flex-1 flex items-center justify-center py-8">
                                            <div className="relative w-40 h-40">
                                                <svg className="w-full h-full transform -rotate-90">
                                                    <circle
                                                        cx="80"
                                                        cy="80"
                                                        r="70"
                                                        stroke="currentColor"
                                                        strokeWidth="12"
                                                        fill="transparent"
                                                        className="text-white/10"
                                                    />
                                                    <circle
                                                        cx="80"
                                                        cy="80"
                                                        r="70"
                                                        stroke="#22c55e"
                                                        strokeWidth="12"
                                                        fill="transparent"
                                                        strokeDasharray={440}
                                                        strokeDashoffset={440 - (440 * analysis.report_data.premium.views_forecast.avg_viral_probability / 100)}
                                                        strokeLinecap="round"
                                                        className="transition-all duration-1000 ease-out"
                                                    />
                                                </svg>
                                                <div className="absolute inset-0 flex items-center justify-center flex-col">
                                                    <span className="text-5xl font-bold">{analysis.report_data.premium.views_forecast.avg_viral_probability}%</span>
                                                </div>
                                            </div>
                                        </div>
                                        <p className="text-slate-400">Likelihood of outperforming channel average</p>
                                    </div>

                                    <div className="space-y-4">
                                        {analysis.report_data.premium.views_forecast.forecasts.slice(0, 3).map((forecast, i) => (
                                            <div key={i} className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm flex items-center justify-between">
                                                <div className="flex-1 mr-4 overflow-hidden">
                                                    <h4 className="font-medium text-slate-900 truncate mb-1">{forecast.video_title}</h4>
                                                    <span className={`text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded ${forecast.trajectory_type === 'VIRAL' ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-600'}`}>
                                                        {forecast.trajectory_type}
                                                    </span>
                                                </div>
                                                <div className="text-right">
                                                    <div className="text-xl font-bold text-slate-900">{(forecast.predicted_30d_views / 1000).toFixed(1)}k</div>
                                                    <div className="text-xs text-slate-400 uppercase">30 Days</div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Hook Analysis */}
                            {analysis.report_data.premium.hook_analysis && (
                                <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-[32px] p-8 border border-amber-100">
                                    <h3 className="text-2xl font-serif font-medium text-slate-900 mb-2">🎣 Hook Analysis</h3>
                                    <p className="text-sm text-slate-500 mb-6">First 60 seconds patterns that drive views</p>

                                    <div className="grid md:grid-cols-2 gap-6 mb-6">
                                        <div className="bg-white rounded-2xl p-6 border border-amber-100">
                                            <div className="text-4xl font-bold text-amber-600 mb-2">{analysis.report_data.premium.hook_analysis.avg_hook_score}</div>
                                            <div className="text-sm text-slate-500">Average Hook Score</div>
                                        </div>
                                        <div className="bg-white rounded-2xl p-6 border border-amber-100">
                                            <div className="text-4xl font-bold text-slate-900 mb-2">{analysis.report_data.premium.hook_analysis.videos_analyzed}</div>
                                            <div className="text-sm text-slate-500">Videos Analyzed</div>
                                        </div>
                                    </div>

                                    {analysis.report_data.premium.hook_analysis.best_patterns && (
                                        <div className="mb-6">
                                            <h4 className="font-semibold text-slate-900 mb-3">Top Performing Hook Patterns</h4>
                                            <div className="space-y-2">
                                                {analysis.report_data.premium.hook_analysis.best_patterns.map((p, i) => (
                                                    <div key={i} className="flex items-center justify-between bg-white rounded-xl px-4 py-3 border border-amber-100">
                                                        <span className="font-medium text-slate-700 capitalize">{p.pattern}</span>
                                                        <span className="text-sm font-bold text-amber-600">{(p.avg_views / 1000).toFixed(1)}K avg views</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {analysis.report_data.premium.hook_analysis.recommendations && (
                                        <div className="bg-amber-100/50 rounded-xl p-4">
                                            <h4 className="font-semibold text-amber-800 mb-2">💡 Recommendations</h4>
                                            <ul className="space-y-1 text-sm text-amber-900">
                                                {analysis.report_data.premium.hook_analysis.recommendations.map((rec, i) => (
                                                    <li key={i}>• {rec}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Color Insights */}
                            {analysis.report_data.premium.color_insights && (
                                <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-[32px] p-8 border border-purple-100">
                                    <h3 className="text-2xl font-serif font-medium text-slate-900 mb-2">🎨 Thumbnail Color Insights</h3>
                                    <p className="text-sm text-slate-500 mb-6">Color patterns that drive the most views</p>

                                    {analysis.report_data.premium.color_insights.top_performing_colors && (
                                        <div className="mb-6">
                                            <h4 className="font-semibold text-slate-900 mb-3">Top Colors</h4>
                                            <div className="flex gap-3">
                                                {analysis.report_data.premium.color_insights.top_performing_colors.slice(0, 5).map((color, i) => (
                                                    <div key={i} className="flex flex-col items-center">
                                                        <div
                                                            className="w-12 h-12 rounded-xl border-2 border-white shadow-md"
                                                            style={{ backgroundColor: color }}
                                                        />
                                                        <span className="text-xs text-slate-500 mt-1">{color}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {analysis.report_data.premium.color_insights.best_color_temperatures && (
                                        <div className="grid md:grid-cols-3 gap-4 mb-6">
                                            {analysis.report_data.premium.color_insights.best_color_temperatures.map((temp, i) => (
                                                <div key={i} className="bg-white rounded-xl p-4 text-center border border-purple-100">
                                                    <div className="text-lg font-bold text-purple-600 capitalize">{temp.temperature}</div>
                                                    <div className="text-sm text-slate-500">{(temp.avg_views / 1000).toFixed(1)}K avg views</div>
                                                </div>
                                            ))}
                                        </div>
                                    )}

                                    {analysis.report_data.premium.color_insights.color_recommendations && (
                                        <div className="bg-purple-100/50 rounded-xl p-4">
                                            <h4 className="font-semibold text-purple-800 mb-2">💡 Color Recommendations</h4>
                                            <ul className="space-y-1 text-sm text-purple-900">
                                                {analysis.report_data.premium.color_insights.color_recommendations.map((rec, i) => (
                                                    <li key={i}>• {rec}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Visual Charts */}
                            {analysis.report_data.premium.visual_charts && (
                                <div className="grid md:grid-cols-2 gap-6">
                                    {analysis.report_data.premium.visual_charts.hook_patterns && (
                                        <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
                                            <img
                                                src={analysis.report_data.premium.visual_charts.hook_patterns.svg_data_uri}
                                                alt="Hook Patterns Chart"
                                                className="w-full h-auto"
                                            />
                                        </div>
                                    )}
                                    {analysis.report_data.premium.visual_charts.color_temperature && (
                                        <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
                                            <img
                                                src={analysis.report_data.premium.visual_charts.color_temperature.svg_data_uri}
                                                alt="Color Temperature Chart"
                                                className="w-full h-auto"
                                            />
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}

