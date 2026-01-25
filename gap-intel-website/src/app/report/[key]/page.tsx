import Link from "next/link";
import { createClient } from "@supabase/supabase-js";
import { AlertCircle, Search, Sparkles, Zap, Eye, Clock, TrendingUp, CheckCircle } from "lucide-react";
import ReportActions from "@/components/ReportActions";
import ReportHeader from "@/components/ReportHeader";
import { SafeThumbnail } from "@/components/SafeThumbnail";
import { VideoCarousel } from "@/components/VideoCarousel";

const getSupabase = () => {
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
    if (!url || !key) return null;
    return createClient(url, key);
};

const supabase = getSupabase();

interface AnalysisResult {
    channelName?: string;
    pipeline?: { rawComments: number; highSignal: number; painPoints: number; trueGaps: number; underExplained: number; alreadyCovered: number; };
    top_gap?: { topic: string; title_suggestion: string; engagement_score: number; reasoning: string; };
    verified_gaps?: Array<{ topic: string; status: string; user_struggle: string; engagement_score: number; transcript_evidence: string; reasoning: string; title_suggestions: string[]; ml_viral_probability?: number; }>;
    already_covered?: Array<{ topic: string; explanation: string; }>;
    videos_analyzed?: Array<{ title: string; comments_count: number; video_id: string; thumbnail_url?: string; }>;
    competitors?: string[];
    error?: string;
    pipeline_stats?: { raw_comments: number; high_signal_comments: number; pain_points_found: number; true_gaps: number; under_explained: number; saturated: number; };
    premium?: {
        tier: string;
        thumbnail_analysis?: { mode: string; videos_analyzed: Array<{ video_title: string; video_id?: string; thumbnail_url?: string; predicted_ctr: number; potential_improvement: string; score_breakdown: Record<string, number>; issues: Array<{ issue: string; severity: string; fix: string }>; }>; };
        views_forecast?: { forecasts: Array<{ video_title: string; video_id?: string; thumbnail_url?: string; predicted_7d_views: number; predicted_30d_views: number; viral_probability: number; trajectory_type: string; vs_channel_avg: string; }>; avg_viral_probability: number; };
        publish_times?: { best_days: string[]; best_hours_utc: number[]; recommendations: Array<{ day: string; hour: number; boost: string; reasoning: string }>; };
        hook_analysis?: { videos_analyzed: number; avg_hook_score: number; best_patterns: Array<{ pattern: string; avg_views: number }>; recommendations: string[]; };
        color_insights?: { total_videos: number; best_color_temperatures: Array<{ temperature: string; avg_views: number }>; top_performing_colors: string[]; color_recommendations: string[]; };
        satisfaction_signals?: { satisfaction_index: number; success_comments: number; confusion_signals: number; clarity_score: number; };
        growth_patterns?: { consistency_index: number; avg_days_between_uploads: number; growth_trajectory: string; optimal_frequency: string; };
    };
}

interface AnalysisRow {
    id: string;
    channel_name: string;
    channel_thumbnail?: string;
    status: string;
    report_data: AnalysisResult | null;
    created_at: string;
}

async function getAnalysis(accessKey: string): Promise<AnalysisRow | null> {
    if (!supabase) return null;
    const { data, error } = await supabase.from("user_reports").select("*").eq("access_key", accessKey).single();
    if (error || !data) return null;
    return data as AnalysisRow;
}

function transformData(result: AnalysisResult, channelName: string) {
    const gaps = result.verified_gaps || [];
    const topGap = result.top_gap || gaps[0];
    return {
        channelName: result.channelName || channelName,
        videosAnalyzed: result.videos_analyzed?.length || 0,
        pipeline: result.pipeline_stats ? {
            rawComments: result.pipeline_stats.raw_comments || 0,
            painPoints: result.pipeline_stats.pain_points_found || 0,
            trueGaps: result.pipeline_stats.true_gaps || 0,
        } : { rawComments: 0, painPoints: 0, trueGaps: gaps.filter(g => g?.status === "TRUE_GAP").length },
        topOpportunity: topGap ? {
            topic: (topGap as any)?.topic || "Analysis pending",
            suggestedTitle: (topGap as any)?.title_suggestion || (topGap as any)?.title_suggestions?.[0] || "",
            engagementPotential: (topGap as any)?.engagement_score || 0,
            reasoning: (topGap as any)?.reasoning || "",
        } : null,
        contentGaps: gaps.filter(g => g).map((gap, i) => ({
            rank: i + 1,
            topic: gap.topic || "Unknown Topic",
            status: gap.status === "TRUE_GAP" ? "TRUE_GAP" : "UNDER_EXPLAINED",
            userStruggle: gap.user_struggle || "",
            suggestedTitles: gap.title_suggestions || [],
            mlViralScore: gap.ml_viral_probability,
        })),
        videosAnalyzedList: result.videos_analyzed?.filter(v => v).map(v => ({
            title: v.title || 'Untitled Video',
            comments: v.comments_count || 0,
            url: v.video_id ? `https://youtube.com/watch?v=${v.video_id}` : '#',
            videoId: v.video_id,
            thumbnail: v.thumbnail_url,
        })) || [],
    };
}

export default async function ReportPage({ params }: { params: Promise<{ key: string }> }) {
    const { key } = await params;
    const analysis = await getAnalysis(key);

    if (!analysis) {
        return (
            <main className="min-h-screen flex items-center justify-center bg-slate-50">
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-10 max-w-sm text-center">
                    <div className="w-14 h-14 rounded-xl bg-slate-100 flex items-center justify-center mx-auto mb-5">
                        <Search className="w-6 h-6 text-slate-400" />
                    </div>
                    <h1 className="text-xl font-semibold text-slate-900 mb-2">Report Not Found</h1>
                    <p className="text-slate-500 text-sm mb-6">Check your access key and try again.</p>
                    <Link href="/dashboard" className="inline-block bg-slate-900 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-slate-800">
                        Back to Dashboard
                    </Link>
                </div>
            </main>
        );
    }

    if (analysis.status === "pending" || analysis.status === "processing") {
        const RealtimeStatus = (await import("@/components/RealtimeStatus")).default;
        return (
            <main className="min-h-screen flex items-center justify-center bg-slate-50">
                <RealtimeStatus
                    accessKey={key}
                    channelName={analysis.channel_name}
                    initialStatus={analysis.status}
                    initialProgress={(analysis as any).progress_percentage || 0}
                    initialPhase={(analysis as any).current_phase || "Queued"}
                />
            </main>
        );
    }

    if (analysis.status === "failed") {
        return (
            <main className="min-h-screen flex items-center justify-center bg-slate-50">
                <div className="bg-white rounded-2xl p-10 max-w-sm text-center border border-slate-200">
                    <div className="w-14 h-14 rounded-xl bg-red-50 flex items-center justify-center mx-auto mb-5">
                        <AlertCircle className="w-6 h-6 text-red-500" />
                    </div>
                    <h1 className="text-xl font-semibold text-slate-900 mb-2">Analysis Failed</h1>
                    <p className="text-slate-500 text-sm mb-6">{analysis.report_data?.error || "Unknown error"}</p>
                    <Link href="/dashboard" className="text-slate-600 text-sm hover:underline">Return to Dashboard</Link>
                </div>
            </main>
        );
    }

    const report = transformData(analysis.report_data || {}, analysis.channel_name);
    const premium = analysis.report_data?.premium;

    return (
        <div className="min-h-screen bg-slate-50">
            <ReportHeader accessKey={key} />

            <main className="pt-20 pb-16">
                <div className="max-w-5xl mx-auto px-4 sm:px-6">

                    {/* Header */}
                    <header className="py-8 border-b border-slate-200 mb-8">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                {analysis.channel_thumbnail ? (
                                    <img src={analysis.channel_thumbnail} alt="" className="w-16 h-16 rounded-xl object-cover" />
                                ) : (
                                    <div className="w-16 h-16 rounded-xl bg-slate-200 flex items-center justify-center text-slate-500 text-xl font-semibold">
                                        {analysis.channel_name[0]?.toUpperCase()}
                                    </div>
                                )}
                                <div>
                                    <p className="text-xs text-slate-500 uppercase tracking-wide font-medium mb-1">Channel Report</p>
                                    <h1 className="text-2xl font-semibold text-slate-900">@{analysis.channel_name}</h1>
                                </div>
                            </div>
                            <ReportActions channelName={analysis.channel_name} accessKey={key} />
                        </div>
                    </header>

                    {/* Key Metrics */}
                    <section className="grid grid-cols-4 gap-4 mb-10">
                        <MetricCard label="Comments" value={report.pipeline.rawComments.toLocaleString()} />
                        <MetricCard label="Pain Points" value={report.pipeline.painPoints.toLocaleString()} />
                        <MetricCard label="Gaps Found" value={report.pipeline.trueGaps.toString()} highlight />
                        <MetricCard label="Videos" value={report.videosAnalyzed.toString()} />
                    </section>

                    {/* Videos Carousel */}
                    {report.videosAnalyzedList.length > 0 && (
                        <section className="mb-10">
                            <SectionHeader title="Videos Analyzed" count={report.videosAnalyzedList.length} />
                            <VideoCarousel videos={report.videosAnalyzedList} />
                        </section>
                    )}

                    {/* Top Opportunity */}
                    {report.topOpportunity && (
                        <section className="mb-10">
                            <SectionHeader title="Top Opportunity" />
                            <div className="bg-slate-900 rounded-xl p-6 text-white">
                                <div className="flex items-start justify-between gap-6">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-3">
                                            <Sparkles className="w-4 h-4 text-amber-400" />
                                            <span className="text-xs text-slate-400 uppercase tracking-wide font-medium">Highest Potential</span>
                                        </div>
                                        <h3 className="text-xl font-semibold mb-2">{report.topOpportunity.topic}</h3>
                                        <p className="text-slate-400 text-sm mb-4 line-clamp-2">{report.topOpportunity.reasoning}</p>
                                        <div className="bg-slate-800 rounded-lg px-4 py-3">
                                            <p className="text-xs text-slate-500 mb-1">Suggested Title</p>
                                            <p className="text-sm font-medium">{report.topOpportunity.suggestedTitle}</p>
                                        </div>
                                    </div>
                                    <div className="text-center px-6 border-l border-slate-700">
                                        <div className="text-4xl font-bold text-emerald-400">{report.topOpportunity.engagementPotential}</div>
                                        <div className="text-xs text-slate-500 mt-1">Score</div>
                                    </div>
                                </div>
                            </div>
                        </section>
                    )}

                    {/* Content Gaps */}
                    {report.contentGaps.length > 0 && (
                        <section className="mb-10">
                            <SectionHeader title="Content Gaps" count={report.contentGaps.length} />
                            <div className="grid sm:grid-cols-2 gap-4">
                                {report.contentGaps.slice(0, 6).map((gap, i) => (
                                    <div key={i} className="bg-white rounded-xl border border-slate-200 p-5 hover:border-slate-300 transition-colors">
                                        <div className="flex items-center justify-between mb-3">
                                            <div className="flex items-center gap-2">
                                                <span className="w-6 h-6 rounded-full bg-slate-100 flex items-center justify-center text-xs font-semibold text-slate-600">{gap.rank}</span>
                                                {gap.mlViralScore && (
                                                    <span className="text-[10px] font-medium text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                                                        {Math.round(gap.mlViralScore * 100)}%
                                                    </span>
                                                )}
                                            </div>
                                            <span className={`text-[10px] font-medium px-2 py-0.5 rounded ${gap.status === 'TRUE_GAP' ? 'bg-emerald-50 text-emerald-600' : 'bg-violet-50 text-violet-600'}`}>
                                                {gap.status === 'TRUE_GAP' ? 'Gap' : 'Under-explained'}
                                            </span>
                                        </div>
                                        <h4 className="font-medium text-slate-900 mb-1 text-sm">{gap.topic}</h4>
                                        <p className="text-xs text-slate-500 line-clamp-2 mb-3">{gap.userStruggle}</p>
                                        {gap.suggestedTitles[0] && (
                                            <div className="bg-slate-50 rounded-lg px-3 py-2">
                                                <p className="text-[10px] text-slate-400 mb-0.5">Video idea</p>
                                                <p className="text-xs text-slate-700 line-clamp-1">{gap.suggestedTitles[0]}</p>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </section>
                    )}

                    {/* Premium Intelligence */}
                    {premium && (
                        <>
                            <div className="border-t border-slate-200 my-10" />
                            <p className="text-xs text-slate-400 uppercase tracking-wide font-medium mb-6">Premium Intelligence</p>

                            <div className="grid sm:grid-cols-2 gap-4 mb-6">
                                {/* Thumbnail Analysis */}
                                {premium.thumbnail_analysis?.videos_analyzed && premium.thumbnail_analysis.videos_analyzed.length > 0 && (
                                    <Card icon={Eye} iconBg="bg-purple-50" iconColor="text-purple-600" title="Thumbnail Analysis">
                                        <div className="space-y-4">
                                            {premium.thumbnail_analysis.videos_analyzed.slice(0, 3).map((v, i) => (
                                                <div key={i} className="flex gap-3">
                                                    <SafeThumbnail videoId={v.video_id} thumbnailUrl={v.thumbnail_url} alt={v.video_title} />
                                                    <div className="flex-1 min-w-0">
                                                        <p className="text-xs text-slate-700 font-medium line-clamp-1 mb-1">{v.video_title}</p>
                                                        <p className="text-lg font-bold text-purple-600">{v.predicted_ctr}% <span className="text-xs font-normal text-slate-400">CTR</span></p>
                                                        {v.issues?.[0] && (
                                                            <p className="text-[10px] text-slate-500 mt-1 line-clamp-1">{v.issues[0].issue}</p>
                                                        )}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </Card>
                                )}

                                {/* Views Forecast */}
                                {premium.views_forecast?.forecasts && premium.views_forecast.forecasts.length > 0 && (
                                    <Card icon={TrendingUp} iconBg="bg-emerald-50" iconColor="text-emerald-600" title="Performance Forecast">
                                        <div className="space-y-4">
                                            {premium.views_forecast.forecasts.slice(0, 3).map((f, i) => (
                                                <div key={i} className="flex gap-3">
                                                    <SafeThumbnail videoId={f.video_id} thumbnailUrl={f.thumbnail_url} alt={f.video_title} />
                                                    <div className="flex-1 min-w-0">
                                                        <p className="text-xs text-slate-700 font-medium line-clamp-1 mb-1">{f.video_title}</p>
                                                        <div className="flex items-center gap-3">
                                                            <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${f.trajectory_type === 'viral' || f.trajectory_type === 'breakout' ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-100 text-slate-600'}`}>
                                                                {f.trajectory_type}
                                                            </span>
                                                            <span className="text-xs text-slate-400">{f.vs_channel_avg}</span>
                                                        </div>
                                                        <div className="flex gap-4 mt-1.5 text-[10px] text-slate-500">
                                                            <span>7d: {(f.predicted_7d_views / 1000).toFixed(1)}k</span>
                                                            <span>30d: {(f.predicted_30d_views / 1000).toFixed(1)}k</span>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </Card>
                                )}

                                {/* Hook Analysis */}
                                {premium.hook_analysis && (
                                    <Card icon={Zap} iconBg="bg-amber-50" iconColor="text-amber-600" title="Hook Analysis">
                                        <div className="flex items-center gap-4 mb-4">
                                            <div>
                                                <p className="text-2xl font-bold text-amber-600">{premium.hook_analysis.avg_hook_score}</p>
                                                <p className="text-[10px] text-slate-400">Avg Score</p>
                                            </div>
                                            <div>
                                                <p className="text-2xl font-bold text-slate-900">{premium.hook_analysis.videos_analyzed}</p>
                                                <p className="text-[10px] text-slate-400">Analyzed</p>
                                            </div>
                                        </div>
                                        {premium.hook_analysis.best_patterns?.slice(0, 3).map((p, i) => (
                                            <div key={i} className="flex justify-between items-center py-2 border-t border-slate-100 text-xs">
                                                <span className="text-slate-600 capitalize">{p.pattern}</span>
                                                <span className="font-medium text-amber-600">{(p.avg_views / 1000).toFixed(1)}K</span>
                                            </div>
                                        ))}
                                    </Card>
                                )}

                                {/* Best Time to Post */}
                                {premium.publish_times && (
                                    <Card icon={Clock} iconBg="bg-blue-50" iconColor="text-blue-600" title="Best Time to Post">
                                        <div className="mb-4">
                                            <p className="text-lg font-bold text-blue-600">{premium.publish_times.best_days.join(', ')}</p>
                                            <p className="text-[10px] text-slate-400">Best days</p>
                                        </div>
                                        {premium.publish_times.recommendations?.slice(0, 3).map((r, i) => (
                                            <div key={i} className="flex items-center gap-2 py-2 border-t border-slate-100 text-xs">
                                                <span className="bg-blue-50 text-blue-600 px-2 py-0.5 rounded font-medium">{r.day} {r.hour}:00</span>
                                                <span className="text-slate-500 flex-1 line-clamp-1">{r.reasoning}</span>
                                            </div>
                                        ))}
                                    </Card>
                                )}

                                {/* Color Insights */}
                                {premium.color_insights && (
                                    <Card icon={Sparkles} iconBg="bg-violet-50" iconColor="text-violet-600" title="Color Insights">
                                        {premium.color_insights.top_performing_colors && (
                                            <div className="flex gap-2 mb-4">
                                                {premium.color_insights.top_performing_colors.slice(0, 6).map((c, i) => (
                                                    <div key={i} className="w-8 h-8 rounded-lg shadow-sm" style={{ backgroundColor: c }} title={c} />
                                                ))}
                                            </div>
                                        )}
                                        {premium.color_insights.best_color_temperatures?.slice(0, 2).map((t, i) => (
                                            <div key={i} className="flex justify-between items-center py-2 border-t border-slate-100 text-xs">
                                                <span className="text-slate-600 capitalize">{t.temperature}</span>
                                                <span className="font-medium text-violet-600">{(t.avg_views / 1000).toFixed(1)}K avg</span>
                                            </div>
                                        ))}
                                    </Card>
                                )}

                                {/* Satisfaction */}
                                {premium.satisfaction_signals && (
                                    <Card icon={CheckCircle} iconBg="bg-green-50" iconColor="text-green-600" title="Viewer Satisfaction">
                                        <div className="grid grid-cols-2 gap-4">
                                            <StatBlock label="Satisfaction" value={premium.satisfaction_signals.satisfaction_index} suffix="%" color="text-green-600" />
                                            <StatBlock label="Clarity" value={premium.satisfaction_signals.clarity_score} suffix="%" color="text-slate-900" />
                                            <StatBlock label="Success" value={premium.satisfaction_signals.success_comments} color="text-emerald-600" />
                                            <StatBlock label="Confusion" value={premium.satisfaction_signals.confusion_signals} color="text-amber-600" />
                                        </div>
                                    </Card>
                                )}
                            </div>
                        </>
                    )}
                </div>
            </main>
        </div>
    );
}

// Components
function MetricCard({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
    return (
        <div className={`rounded-xl p-4 ${highlight ? 'bg-emerald-50 border border-emerald-100' : 'bg-white border border-slate-200'}`}>
            <p className="text-[10px] text-slate-500 uppercase tracking-wide font-medium mb-1">{label}</p>
            <p className={`text-2xl font-semibold ${highlight ? 'text-emerald-600' : 'text-slate-900'}`}>{value}</p>
        </div>
    );
}

function SectionHeader({ title, count }: { title: string; count?: number }) {
    return (
        <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
            {count !== undefined && <span className="text-xs text-slate-400">{count} items</span>}
        </div>
    );
}

function Card({ icon: Icon, iconBg, iconColor, title, children }: { icon: any; iconBg: string; iconColor: string; title: string; children: React.ReactNode }) {
    return (
        <div className="bg-white rounded-xl border border-slate-200 p-5">
            <div className="flex items-center gap-2 mb-4">
                <div className={`w-8 h-8 rounded-lg ${iconBg} flex items-center justify-center`}>
                    <Icon className={`w-4 h-4 ${iconColor}`} />
                </div>
                <h3 className="font-medium text-slate-900 text-sm">{title}</h3>
            </div>
            {children}
        </div>
    );
}

function StatBlock({ label, value, suffix, color }: { label: string; value: number; suffix?: string; color: string }) {
    return (
        <div>
            <p className={`text-xl font-bold ${color}`}>{value}{suffix}</p>
            <p className="text-[10px] text-slate-400">{label}</p>
        </div>
    );
}
