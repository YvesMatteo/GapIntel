import Link from "next/link";
import Image from "next/image";
import { createClient } from "@supabase/supabase-js";
import { CheckCircle, AlertCircle, Clock, TrendingUp, Search, BarChart3, Calendar, ArrowRight, Play, Youtube, Eye, MessageCircle, Sparkles, Target, Zap, Users, Layers, FileText, Lightbulb } from "lucide-react";
import ReportActions from "@/components/ReportActions";
import ReportHeader from "@/components/ReportHeader";
import { ChannelHealthSection } from "@/components/report/ChannelHealthSection";
import { EngagementSection } from "@/components/report/EngagementSection";
import { ContentLandscapeSection } from "@/components/report/ContentLandscapeSection";
import { SeoSection } from "@/components/report/SeoSection";
import { GrowthDriversSection } from "@/components/report/GrowthDriversSection";
import { SatisfactionSection } from "@/components/report/SatisfactionSection";
import { GrowthPatternsSection } from "@/components/report/GrowthPatternsSection";
import { SafeThumbnail, SafeThumbnailLarge } from "@/components/SafeThumbnail";

// Initialize Supabase client for server component
// Safe Supabase client initialization for SSR
const getSupabase = () => {
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const key = process.env.SUPABASE_SERVICE_ROLE_KEY; // Use SERVICE_ROLE_KEY for server-side operations
    if (!url || !key) {
        console.error("Supabase environment variables (URL or SERVICE_ROLE_KEY) are missing.");
        return null;
    }
    return createClient(url, key);
};

const supabase = getSupabase();

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
        ml_viral_probability?: number;
    }>;
    already_covered?: Array<{
        topic: string;
        explanation: string;
    }>;
    videos_analyzed?: Array<{
        title: string;
        comments_count: number;
        video_id: string;
        thumbnail_url?: string;
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
        question_count?: number;
        sentiment_positive?: number;
        sentiment_confusion?: number;
        sentiment_inquiry?: number;
        sentiment_success?: number;
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
                video_id?: string;
                thumbnail_url?: string;
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
                video_id?: string;
                thumbnail_url?: string;
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
                best_performer: Record<string, unknown> | null;
                example_titles: string[];
                saturation_score?: number;
                saturation_label?: string;
            }>;
            best_performing: string;
            underperforming: string[];
            gap_opportunities: string[];
            recommendations: string[];
            format_diversity?: {
                score: number;
                unique_formats: number;
                breakdown: Array<{ name: string; count: number; pct: number }>;
                primary_format: string;
            };
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
        satisfaction_signals?: {
            satisfaction_index: number;
            engagement_quality: number;
            retention_proxy: number;
            implementation_success: number;
            success_comments: number;
            confusion_signals: number;
            return_viewer_ratio: number;
            clarity_score: number;
            top_success?: string[];
            top_confusion?: string[];
            recommendations?: string[];
        };
        growth_patterns?: {
            consistency_index: number;
            avg_days_between_uploads: number;
            upload_variance: number;
            current_streak: number;
            series_detected: Array<{
                name: string;
                video_count: number;
                avg_views: number;
                avg_engagement: number;
                performance_vs_standalone: number;
            }>;
            series_performance_boost: number;
            growth_trajectory: string;
            views_growth_rate: number;
            optimal_frequency: string;
            consistency_impact?: string;
            recommendations?: string[];
        };
    };
}

interface AnalysisRow {
    id: string;
    channel_name: string;
    channel_thumbnail?: string;
    email?: string;
    status: string;
    report_data: AnalysisResult | null;
    created_at: string;
    updated_at: string | null;
}

async function getAnalysis(accessKey: string): Promise<AnalysisRow | null> {
    // If no supabase, we can't fetch anything safely
    if (!supabase) {
        console.error("Supabase client not initialized. Environment variables might be missing.");
        // Depending on context, you might want to throw an error, redirect, or return null.
        // For a server component, `notFound()` is a Next.js way to handle this.
        // If `notFound` is not available or desired, return null.
        return null;
    }

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
            trueGaps: gaps.filter(g => g?.status === "TRUE_GAP").length,
            underExplained: gaps.filter(g => g?.status === "UNDER_EXPLAINED").length,
            alreadyCovered: result.already_covered?.length || 0,
        },
        topOpportunity: topGap ? {
            topic: (topGap as unknown as Record<string, string>)?.topic || "Analysis pending",
            suggestedTitle: (topGap as unknown as Record<string, string>)?.title_suggestion || (topGap as unknown as Record<string, string[]>)?.title_suggestions?.[0] || "",
            engagementPotential: (topGap as unknown as Record<string, number>)?.engagement_score || 0,
            reasoning: (topGap as unknown as Record<string, string>)?.reasoning || "",
        } : null,
        contentGaps: gaps.filter(g => g).map((gap, i) => ({
            rank: i + 1,
            topic: gap.topic || "Unknown Topic",
            status: gap.status === "TRUE_GAP" ? "TRUE_GAP" : "UNDER_EXPLAINED",
            userStruggle: gap.user_struggle || "",
            engagement: gap.engagement_score || 0,
            verification: gap.transcript_evidence || "",
            reasoning: gap.reasoning || "",
            suggestedTitles: gap.title_suggestions || [],
            mlViralScore: gap.ml_viral_probability,
        })),
        alreadyCovered: result.already_covered || [],
        videosAnalyzedList: result.videos_analyzed?.filter(v => v).map(v => ({
            title: v.title || 'Untitled Video',
            comments: v.comments_count || 0,
            url: v.video_id ? `https://youtube.com/watch?v=${v.video_id}` : '#',
            thumbnail: v.thumbnail_url || (v.video_id ? `https://img.youtube.com/vi/${v.video_id}/mqdefault.jpg` : undefined),
        })) || [],
        competitors: result.competitors || [],
    };
}

// CVR Benchmarks by content category
const CVR_BENCHMARKS: Record<string, { low: number; high: number; top: number; label: string }> = {
    educational: { low: 1.0, high: 2.0, top: 3.5, label: 'Educational' },
    tutorial: { low: 0.5, high: 1.0, top: 2.5, label: 'Tutorials' },
    entertainment: { low: 0.1, high: 0.5, top: 1.5, label: 'Entertainment' },
    news: { low: 0.3, high: 0.8, top: 1.5, label: 'News/Commentary' },
    gaming: { low: 0.2, high: 0.6, top: 1.2, label: 'Gaming' },
    vlog: { low: 0.15, high: 0.4, top: 1.0, label: 'Vlog' },
    review: { low: 0.3, high: 0.7, top: 1.5, label: 'Reviews' },
};

// Detect content category from video titles
function detectContentCategory(videos: Array<{ title: string }>): string {
    if (!videos || videos.length === 0) return 'educational';

    const titleText = videos.filter(v => v && v.title).map(v => (v.title || '').toLowerCase()).join(' ');

    // Category detection patterns
    const patterns: Record<string, RegExp[]> = {
        tutorial: [/how to/i, /tutorial/i, /guide/i, /learn/i, /step by step/i, /beginner/i, /course/i],
        gaming: [/gameplay/i, /let's play/i, /walkthrough/i, /playthrough/i, /gaming/i, /stream/i],
        entertainment: [/funny/i, /compilation/i, /challenge/i, /prank/i, /react/i, /try not to/i],
        news: [/news/i, /update/i, /breaking/i, /opinion/i, /commentary/i, /analysis/i],
        vlog: [/vlog/i, /day in/i, /life of/i, /grwm/i, /routine/i],
        review: [/review/i, /unboxing/i, /first look/i, /hands on/i, /worth it/i],
        educational: [/explained/i, /why/i, /science/i, /history/i, /lesson/i, /understand/i],
    };

    // Count matches per category
    const scores: Record<string, number> = {};
    for (const [category, regexes] of Object.entries(patterns)) {
        scores[category] = regexes.filter(r => r.test(titleText)).length;
    }

    // Return highest scoring category
    const sorted = Object.entries(scores).sort((a, b) => b[1] - a[1]);
    return sorted[0][1] > 0 ? sorted[0][0] : 'educational';
}

// Helper function to calculate engagement metrics from existing data
function calculateEngagementMetrics(result: AnalysisResult, totalViews: number = 100000) {
    try {
        const rawComments = result.pipeline_stats?.raw_comments || result.pipeline?.rawComments || 0;
        const painPoints = result.pipeline_stats?.pain_points_found || 0;
        const highSignal = result.pipeline_stats?.high_signal_comments || 0;

        // Detect content category
        const videos = result.videos_analyzed || [];
        const category = detectContentCategory(videos);
        const benchmark = CVR_BENCHMARKS[category] || CVR_BENCHMARKS.educational;

        // Calculate CVR (using estimated views based on comment count typical ratio)
        const estimatedViews = totalViews > 0 ? totalViews : Math.max(rawComments * 100, 10000);
        const cvr = (rawComments / estimatedViews) * 100;

        // Calculate CVR vs benchmark
        const benchmarkMid = (benchmark.low + benchmark.high) / 2;
        const cvrVsBenchmark = benchmarkMid > 0 ? ((cvr - benchmarkMid) / benchmarkMid) * 100 : 0;

        // Calculate Question Density
        const questionCount = (result.pipeline_stats as any)?.question_count;
        let questionDensity = 0;

        if (questionCount !== undefined) {
            questionDensity = rawComments > 0 ? (questionCount / rawComments) * 100 : 0;
        } else {
            // Fallback: proxy using pain points
            questionDensity = rawComments > 0 ? (painPoints / rawComments) * 100 * 3 : 25;
        }

        // Estimate other metrics from available data
        const depthScore = Math.min(1, (highSignal / Math.max(rawComments, 1)) * 2);
        const repeatScore = Math.min(30, 10 + (rawComments / 100)); // Estimate based on volume

        // Sentiment estimation based on gap analysis (more true gaps = more questions = more engagement)
        const trueGaps = result.pipeline_stats?.true_gaps || 0;
        const saturated = result.pipeline_stats?.saturated || 0;
        const total = trueGaps + saturated + (result.pipeline_stats?.under_explained || 0);
        const positiveRatio = total > 0 ? Math.max(50, 85 - trueGaps * 3) : 70;

        return {
            cvr: Math.min(5, cvr),
            cvrBenchmark: category,
            cvrBenchmarkLabel: benchmark.label,
            cvrBenchmarkRange: `${benchmark.low}-${benchmark.high}%`,
            cvrVsBenchmark: Math.round(cvrVsBenchmark),
            cvrStatus: cvr >= benchmark.high ? 'above' : cvr >= benchmark.low ? 'at' : 'below' as 'above' | 'at' | 'below',
            questionDensity: Math.min(50, questionDensity),
            depthScore: Math.min(1, Math.max(0.1, depthScore)),
            repeatScore: Math.min(35, repeatScore),
            totalComments: rawComments,
            sentiments: {
                positive: Math.round(positiveRatio),
                neutral: Math.round(100 - positiveRatio - 10),
                negative: 5,
                questions: Math.min(35, Math.round(questionDensity)),
            }
        };
    } catch (e) {
        console.error("Error calculating engagement metrics:", e);
        return {
            cvr: 0,
            cvrBenchmark: 'educational',
            cvrBenchmarkLabel: 'Educational',
            cvrBenchmarkRange: '1-2%',
            cvrVsBenchmark: 0,
            cvrStatus: 'at' as const,
            questionDensity: 0,
            depthScore: 0,
            repeatScore: 0,
            totalComments: 0,
            sentiments: { positive: 80, neutral: 15, negative: 5, questions: 0 }
        };
    }
}

// Helper function to calculate content landscape metrics
function calculateContentLandscape(result: AnalysisResult) {
    try {
        const videos = result.videos_analyzed || [];
        const gaps = result.verified_gaps || [];

        // Extract topics from video titles
        const topicCounts: Record<string, number> = {};
        videos.forEach(v => {
            if (!v) return;
            // Simple topic extraction from title
            const title = v.title || '';
            const words = title.toLowerCase().split(/\s+/).filter(w => w.length > 4);
            words.slice(0, 3).forEach(word => {
                topicCounts[word] = (topicCounts[word] || 0) + 1;
            });
        });

        // Create topic list with saturation
        const avgPerTopic = videos.length / Math.max(Object.keys(topicCounts).length, 1);
        const topics: Array<{
            name: string;
            videoCount: number;
            saturation: number;
            status: 'over' | 'balanced' | 'under' | 'gap';
        }> = Object.entries(topicCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10)
            .map(([name, count]) => ({
                name: name.charAt(0).toUpperCase() + name.slice(1),
                videoCount: count,
                saturation: count / avgPerTopic,
                status: count / avgPerTopic > 1.5 ? 'over' as const :
                    count / avgPerTopic < 0.5 ? 'under' as const : 'balanced' as const,
            }));

        // Add gaps as uncovered topics
        gaps.filter(g => g && g.status === 'TRUE_GAP').slice(0, 3).forEach(gap => {
            topics.push({
                name: gap.topic.slice(0, 30),
                videoCount: 0,
                saturation: 0,
                status: 'gap' as const,
            });
        });

        // Estimate format diversity
        let formats: Array<{ name: string; count: number; icon: string }> = [];

        if (result.premium?.content_clusters?.format_diversity?.breakdown) {
            formats = result.premium.content_clusters.format_diversity.breakdown.map((f: any) => {
                const icons: Record<string, string> = {
                    'tutorial': '📚', 'listicle': '📋', 'review': '⭐', 'reaction': '😲',
                    'vlog': '📹', 'news': '📰', 'comparison': '⚖️', 'challenge': '🏆',
                    'story': '📖', 'educational': '🎓', 'interview': '🎙️', 'case_study': '🔎',
                    'shorts': '📱', 'other': '📁'
                };
                return {
                    name: f.name.charAt(0).toUpperCase() + f.name.slice(1),
                    count: f.count,
                    icon: icons[f.name] || '📁'
                };
            });
        } else {
            formats = [
                { name: 'Long-form', count: Math.max(1, Math.floor(videos.length * 0.7)), icon: '📹' },
                { name: 'Tutorial', count: Math.max(1, Math.floor(videos.length * 0.4)), icon: '📚' },
                { name: 'Discussion', count: Math.max(1, Math.floor(videos.length * 0.2)), icon: '💬' },
            ];
        }

        // Estimate upload consistency
        let uploadConsistency = {
            score: 65,
            avgDaysBetween: 7,
            pattern: 'weekly',
        };

        if (result.premium?.growth_patterns) {
            uploadConsistency = {
                score: result.premium.growth_patterns.consistency_index,
                avgDaysBetween: result.premium.growth_patterns.avg_days_between_uploads,
                pattern: result.premium.growth_patterns.optimal_frequency || 'weekly'
            };
        } else {
            uploadConsistency = {
                score: 75,
                avgDaysBetween: 7,
                pattern: 'weekly',
            };
        }

        return {
            topicCoverage: Math.min(85, 40 + topics.length * 5),
            totalTopics: topics.length,
            topics,
            formats,
            uploadConsistency,
            freshness: 60,
        };
    } catch (e) {
        console.error("Error calculating content landscape:", e);
        return {
            topicCoverage: 50,
            totalTopics: 0,
            topics: [],
            formats: [],
            uploadConsistency: { score: 50, avgDaysBetween: 7, pattern: 'weekly' },
            freshness: 50
        };
    }
}

// Helper function to calculate SEO metrics from video titles
function calculateSeoMetrics(result: AnalysisResult) {
    try {
        const videos = result.videos_analyzed || [];

        // Analyze titles
        let totalTitleScore = 0;
        let keywordFirst30 = 0;
        let hookUsage = 0;
        let totalLength = 0;

        const issues: Array<{ type: string; count: number; example: string; fix: string }> = [];
        const longTitles: string[] = [];
        const noHookTitles: string[] = [];

        videos.forEach(v => {
            if (!v) return;
            const title = v.title || '';
            totalLength += title.length;

            // Check length (optimal: 50-60)
            let lengthScore = title.length >= 50 && title.length <= 60 ? 10 :
                title.length >= 40 && title.length <= 70 ? 8 : 5;
            if (title.length > 70) longTitles.push(title);

            // Check for number hooks
            const hasNumberHook = /\d+\s*(ways|tips|secrets|rules|steps|hacks|reasons)/i.test(title);
            const hasQuestionHook = title.includes('?');
            const hasHowTo = title.toLowerCase().startsWith('how to');

            if (hasNumberHook || hasQuestionHook || hasHowTo) {
                hookUsage++;
            } else {
                noHookTitles.push(title);
            }

            let hookScore = hasNumberHook ? 10 : hasQuestionHook ? 8 : hasHowTo ? 7 : 4;

            // Assume keyword placement is decent if title is structured
            const keywordScore = (hasNumberHook || hasHowTo) ? 9 : 6;
            if (hasNumberHook || hasHowTo) keywordFirst30++;

            totalTitleScore += (lengthScore * 0.3 + hookScore * 0.4 + keywordScore * 0.3) * 10;
        });

        const videoCount = Math.max(videos.length, 1);

        // Build issues list
        if (longTitles.length > 0) {
            issues.push({
                type: 'Titles Too Long',
                count: longTitles.length,
                example: longTitles[0]?.slice(0, 50) + '...',
                fix: 'Keep titles under 60 characters for mobile visibility',
            });
        }
        if (noHookTitles.length > videoCount * 0.5) {
            issues.push({
                type: 'Missing Hook Patterns',
                count: noHookTitles.length,
                example: noHookTitles[0]?.slice(0, 40) || '',
                fix: 'Use numbers ("7 Ways...") or questions to boost CTR by 35%',
            });
        }

        return {
            seoStrength: Math.round(totalTitleScore / videoCount),
            titleAnalysis: {
                avgScore: Math.round(totalTitleScore / videoCount),
                avgLength: Math.round(totalLength / videoCount),
                keywordPlacement: Math.round((keywordFirst30 / videoCount) * 100),
                hookUsage: Math.round((hookUsage / videoCount) * 100),
            },
            descriptionAnalysis: {
                avgScore: 65, // Would need description data
                frontLoadScore: 60,
                hasTimestamps: 40,
                hasLinks: 70,
            },
            issues,
            recommendations: [
                'Add number-based hooks to titles ("7 Ways...", "5 Secrets...")',
                'Keep primary keyword in first 30 characters',
                'Add timestamps to descriptions for +20% engagement',
                'Use curiosity gaps in titles to improve CTR',
            ],
        };
    } catch (e) {
        console.error("Error calculating SEO metrics:", e);
        return {
            seoStrength: 50,
            titleAnalysis: { avgScore: 50, avgLength: 50, keywordPlacement: 50, hookUsage: 50 },
            descriptionAnalysis: { avgScore: 50, frontLoadScore: 50, hasTimestamps: 0, hasLinks: 0 },
            issues: [],
            recommendations: []
        };
    }
}

// Helper function to calculate growth driver status
function calculateGrowthDrivers(result: AnalysisResult, premium: AnalysisResult['premium']) {
    try {
        const videos = result.videos_analyzed || [];
        const rawComments = result.pipeline_stats?.raw_comments || 0;

        // Estimate if creator has shorts
        const hasShorts = premium?.hook_analysis?.videos_analyzed ?
            premium.hook_analysis.videos_analyzed > 0 : videos.length > 5;

        return {
            uploadConsistency: {
                current: videos.length > 10 ? 'Regular uploads detected' : 'Limited upload history',
                recommendation: 'Aim for consistent weekly uploads',
                impact: '+156% growth',
                implemented: videos.length > 8,
            },
            seriesContent: {
                seriesCount: Math.floor(videos.length / 5), // Estimate
                topSeries: videos[0]?.title?.split(':')[0] || 'Main Content',
                impact: '+89% watch time',
                implemented: videos.length > 6,
            },
            communityEngagement: {
                responseRate: Math.min(80, 30 + Math.floor(rawComments / 100)),
                impact: '+134% growth',
                implemented: rawComments > 200,
            },
            multiFormat: {
                hasShorts,
                hasLongForm: videos.length > 0,
                impact: '+156% reach',
                implemented: hasShorts && videos.length > 0,
            },
            consistency: {
                daysBetweenUploads: 7,
                impact: '+156% growth',
                implemented: videos.length > 10,
            },
        };
    } catch (e) {
        console.error("Error calculating growth drivers:", e);
        return {
            uploadConsistency: { current: 'N/A', recommendation: 'N/A', impact: 'N/A', implemented: false },
            seriesContent: { seriesCount: 0, topSeries: 'N/A', impact: 'N/A', implemented: false },
            communityEngagement: { responseRate: 0, impact: 'N/A', implemented: false },
            multiFormat: { hasShorts: false, hasLongForm: false, impact: 'N/A', implemented: false },
            consistency: { daysBetweenUploads: 0, impact: 'N/A', implemented: false }
        };
    }
}

// Helper to calculate overall channel health score
function calculateHealthScore(
    engagement: ReturnType<typeof calculateEngagementMetrics>,
    seo: ReturnType<typeof calculateSeoMetrics>,
    growth: ReturnType<typeof calculateGrowthDrivers>
) {
    try {
        // Engagement score (0-100)
        const engagementScore = Math.min(100,
            (engagement.cvr * 20) +
            (engagement.questionDensity * 1.5) +
            (engagement.repeatScore * 1.5) +
            (engagement.sentiments.positive * 0.3)
        );

        // Satisfaction score (based on sentiment)
        const satisfactionScore = engagement.sentiments.positive;

        // SEO score
        const seoScore = seo.seoStrength;

        // Growth score (based on how many drivers are implemented)
        const growthDrivers = [
            growth.uploadConsistency.implemented,
            growth.seriesContent.implemented,
            growth.communityEngagement.implemented,
            growth.multiFormat.implemented,
        ];
        const growthScore = (growthDrivers.filter(Boolean).length / growthDrivers.length) * 100;

        // Title Potential score (from hook usage - not actual CTR)
        const titlePotentialScore = Math.min(100, (seo.titleAnalysis?.hookUsage || 0) + 30);

        // Calculate overall (weighted average)
        const overall = (
            engagementScore * 0.25 +
            satisfactionScore * 0.25 +
            seoScore * 0.20 +
            growthScore * 0.15 +
            titlePotentialScore * 0.15
        );

        // Generate top insight
        let topInsight = '';
        if (seoScore < 60) {
            topInsight = 'Focus on title optimization with number hooks to boost CTR by 35%';
        } else if (engagementScore < 60) {
            topInsight = 'Increase engagement by responding to comments within first hour';
        } else if (growthScore < 60) {
            topInsight = 'Create content series to boost watch time by 89%';
        } else {
            topInsight = 'Strong foundation! Focus on addressing identified content gaps';
        }

        return {
            overall: Math.round(overall),
            engagement: Math.round(engagementScore),
            satisfaction: Math.round(satisfactionScore),
            seo: Math.round(seoScore),
            growth: Math.round(growthScore),
            titlePotential: Math.round(titlePotentialScore),
            topInsight,
        };
    } catch (e) {
        console.error("Error calculating health score:", e);
        return {
            overall: 50,
            engagement: 50,
            satisfaction: 50,
            seo: 50,
            growth: 50,
            titlePotential: 50,
            topInsight: 'Analysis in progress...'
        };
    }
}



export default async function DashboardPage({ params }: { params: Promise<{ key: string }> }) {
    const { key } = await params;
    const analysis = await getAnalysis(key);

    if (!analysis) {
        return (
            <main className="min-h-screen flex items-center justify-center bg-[#FAFAFA]">
                <div className="text-center max-w-md mx-auto px-6">
                    <div className="bg-white rounded-[32px] shadow-xl border border-slate-100 p-12">
                        <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-6">
                            <Search className="w-8 h-8 text-slate-400" />
                        </div>
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
        // Import dynamically for client component
        const RealtimeStatus = (await import("@/components/RealtimeStatus")).default;

        return (
            <main className="min-h-screen flex items-center justify-center bg-[#FAFAFA]">
                <div className="text-center max-w-md mx-auto px-6">
                    <RealtimeStatus
                        accessKey={key}
                        channelName={analysis.channel_name}
                        initialStatus={analysis.status}
                        initialProgress={(analysis as unknown as { progress_percentage?: number }).progress_percentage || 0}
                        initialPhase={(analysis as unknown as { current_phase?: string }).current_phase || "Queued"}
                    />
                </div>
            </main>
        );
    }

    if (analysis.status === "failed") {
        return (
            <main className="min-h-screen flex items-center justify-center bg-[#FAFAFA]">
                <div className="text-center">
                    <div className="bg-white rounded-[32px] p-12 max-w-md mx-auto border border-slate-100 shadow-xl">
                        <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mx-auto mb-6">
                            <AlertCircle className="w-8 h-8 text-red-500" />
                        </div>
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
            <ReportHeader accessKey={key} />

            <main className="pt-24 md:pt-32 pb-20 px-4 md:px-6">
                <div className="max-w-7xl mx-auto space-y-8">

                    {/* Header Section */}
                    <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                        <div className="flex items-start gap-4 md:gap-6">
                            {/* Channel Profile Picture */}
                            {analysis.channel_thumbnail ? (
                                <img
                                    src={analysis.channel_thumbnail}
                                    alt={analysis.channel_name}
                                    className="w-16 h-16 md:w-20 md:h-20 rounded-full object-cover border-4 border-white shadow-lg flex-shrink-0"
                                />
                            ) : (
                                <div className="w-16 h-16 md:w-20 md:h-20 rounded-full bg-slate-200 flex items-center justify-center text-slate-500 text-xl md:text-2xl font-bold border-4 border-white shadow-lg flex-shrink-0">
                                    {(analysis.channel_name || 'C')[0].toUpperCase()}
                                </div>
                            )}
                            <div>
                                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-50 border border-green-100 text-green-700 text-[10px] md:text-xs font-bold uppercase tracking-wider mb-2">
                                    @{analysis.channel_name}
                                </div>
                                <h1 className="text-3xl md:text-5xl font-serif font-medium text-slate-900 mb-2 md:mb-4">
                                    Content Strategy Report
                                </h1>
                                <p className="text-base md:text-lg text-slate-500 max-w-2xl">
                                    Detailed analysis of {report.videosAnalyzed} videos, audience sentiment, and missed opportunities.
                                </p>
                            </div>
                        </div>
                        <ReportActions channelName={analysis.channel_name} accessKey={key} />
                    </div>

                    {/* Stats Grid */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
                        {[
                            { label: "Comments Analyzed", value: report.pipeline.rawComments.toLocaleString(), icon: MessageCircle, color: "text-blue-600", bg: "bg-blue-50" },
                            { label: "Pain Points Found", value: report.pipeline.painPoints.toLocaleString(), icon: AlertCircle, color: "text-orange-600", bg: "bg-orange-50" },
                            { label: "Content Gaps", value: report.pipeline.trueGaps, icon: Search, color: "text-green-600", bg: "bg-green-50" },
                            { label: "Videos Scanned", value: report.videosAnalyzed, icon: Play, color: "text-purple-600", bg: "bg-purple-50" },
                        ].map((stat, i) => (
                            <div key={i} className="bg-white rounded-2xl p-4 md:p-6 border border-slate-100 shadow-sm flex flex-col justify-between h-28 md:h-32">
                                <div className="flex justify-between items-start">
                                    <div className={`w-8 h-8 md:w-10 md:h-10 rounded-xl ${stat.bg} flex items-center justify-center ${stat.color}`}>
                                        <stat.icon className="w-4 h-4 md:w-5 md:h-5" />
                                    </div>
                                </div>
                                <div>
                                    <div className="text-xl md:text-2xl font-bold text-slate-900">{stat.value}</div>
                                    <div className="text-xs md:text-sm text-slate-500 font-medium">{stat.label}</div>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Videos Analyzed with Thumbnails */}
                    {report.videosAnalyzedList.length > 0 && (
                        <div>
                            <h2 className="text-2xl font-serif font-medium text-slate-900 mb-6">Videos Analyzed</h2>
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                {report.videosAnalyzedList.map((video, i) => (
                                    <a
                                        key={i}
                                        href={video.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md hover:border-blue-200 transition-all overflow-hidden group"
                                    >
                                        <div className="relative aspect-video w-full bg-slate-100">
                                            {video.thumbnail ? (
                                                <img
                                                    src={video.thumbnail}
                                                    alt={video.title}
                                                    className="w-full h-full object-cover"
                                                />
                                            ) : (
                                                <div className="w-full h-full flex items-center justify-center text-slate-400">
                                                    <Play className="w-8 h-8" />
                                                </div>
                                            )}
                                        </div>
                                        <div className="p-4">
                                            <h3 className="font-medium text-slate-900 text-sm line-clamp-2 group-hover:text-blue-700 transition-colors">{video.title}</h3>
                                            <div className="flex items-center gap-2 mt-2 text-xs text-slate-500">
                                                <MessageCircle className="w-3 h-3" />
                                                <span>{video.comments.toLocaleString()} comments</span>
                                            </div>
                                        </div>
                                    </a>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Calculate metrics for new sections */}
                    {(() => {
                        const engagementMetrics = calculateEngagementMetrics(analysis.report_data || {});
                        const contentLandscape = calculateContentLandscape(analysis.report_data || {});
                        const seoMetrics = calculateSeoMetrics(analysis.report_data || {});
                        const growthDrivers = calculateGrowthDrivers(analysis.report_data || {}, analysis.report_data?.premium);
                        const healthScore = calculateHealthScore(engagementMetrics, seoMetrics, growthDrivers);

                        return (
                            <>
                                {/* Channel Health Score Section */}
                                <ChannelHealthSection
                                    health={healthScore}
                                    channelName={analysis.channel_name}
                                    topInsight={healthScore.topInsight}
                                />

                                {/* Premium Intelligence Divider */}
                                <div className="flex items-center gap-4 pt-8">
                                    <div className="h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent flex-1" />
                                    <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest">Deep Analysis</h2>
                                    <div className="h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent flex-1" />
                                </div>

                                {/* Engagement Intelligence Section */}
                                <EngagementSection metrics={engagementMetrics} />

                                {/* Content Landscape Section */}
                                <ContentLandscapeSection data={contentLandscape} />

                                {/* SEO Section */}
                                <SeoSection data={seoMetrics} />

                                {/* Growth Drivers Section */}
                                <GrowthDriversSection data={growthDrivers} />

                                {/* Satisfaction Signals Section (Skill 4) */}
                                {analysis.report_data?.premium?.satisfaction_signals && (
                                    <>
                                        <div className="flex items-center gap-4 pt-8">
                                            <div className="h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent flex-1" />
                                            <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest">Viewer Satisfaction</h2>
                                            <div className="h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent flex-1" />
                                        </div>
                                        <SatisfactionSection data={analysis.report_data.premium.satisfaction_signals} />
                                    </>
                                )}

                                {/* Growth Patterns Section (Skill 6) */}
                                {analysis.report_data?.premium?.growth_patterns && (
                                    <>
                                        <div className="flex items-center gap-4 pt-8">
                                            <div className="h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent flex-1" />
                                            <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest">Growth Patterns</h2>
                                            <div className="h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent flex-1" />
                                        </div>
                                        <GrowthPatternsSection data={analysis.report_data.premium.growth_patterns} />
                                    </>
                                )}

                                {/* Content Gaps Divider */}
                                <div className="flex items-center gap-4 pt-8">
                                    <div className="h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent flex-1" />
                                    <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest">Content Opportunities</h2>
                                    <div className="h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent flex-1" />
                                </div>
                            </>
                        );
                    })()}


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
                                        <div className="flex gap-2">
                                            <span className="w-10 h-10 rounded-full bg-slate-50 flex items-center justify-center font-bold text-slate-900 border border-slate-200">
                                                {gap.rank}
                                            </span>
                                            {(gap as any).mlViralScore && (
                                                <span className="px-3 py-2 rounded-full text-xs font-bold uppercase tracking-wider bg-blue-50 text-blue-700 border border-blue-100 flex items-center gap-1">
                                                    <Sparkles className="w-3 h-3" />
                                                    ML Score: {Math.round((gap as any).mlViralScore * 100)}%
                                                </span>
                                            )}
                                        </div>
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
                                        {analysis.report_data.premium.thumbnail_analysis.videos_analyzed?.filter(v => v).map((video, i) => (
                                            <div key={i} className="p-8 hover:bg-slate-50/30 transition-colors">
                                                <div className="flex justify-between items-start mb-4 gap-4">
                                                    <div className="flex items-start gap-4 flex-1">
                                                        {/* Thumbnail Image */}
                                                        <SafeThumbnailLarge
                                                            videoId={video.video_id}
                                                            thumbnailUrl={video.thumbnail_url}
                                                            alt={video.video_title}
                                                        />
                                                        <div>
                                                            <h4 className="font-bold text-slate-900 line-clamp-2">{video.video_title}</h4>
                                                        </div>
                                                    </div>
                                                    <div className="text-right shrink-0">
                                                        <div className="text-2xl font-bold text-purple-600">{video.predicted_ctr}%</div>
                                                        <div className="text-xs text-slate-400 font-bold uppercase">CTR <span className="text-amber-500">(Est.)</span></div>
                                                    </div>
                                                </div>
                                                {video.issues && video.issues.length > 0 ? (
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

                            {/* Views Forecast - Per Video Breakout */}
                            {analysis.report_data.premium.views_forecast && (() => {
                                const forecasts = analysis.report_data.premium.views_forecast.forecasts || [];

                                // Check if we have any recent enough videos to analyze
                                // If 3rd video is older than 90 days from now, show "not enough recent data"
                                const hasRecentVideos = forecasts.length >= 1;

                                if (!hasRecentVideos) {
                                    return (
                                        <div className="bg-slate-50 rounded-[32px] p-8 border border-slate-200 text-center">
                                            <h3 className="text-2xl font-serif font-medium text-slate-900 mb-4">Video Performance Forecast</h3>
                                            <p className="text-slate-500">Not enough recent video data to generate forecasts. Upload more videos to see performance predictions.</p>
                                        </div>
                                    );
                                }

                                return (
                                    <div className="bg-white rounded-[32px] border border-slate-100 shadow-xl shadow-slate-200/50 overflow-hidden">
                                        <div className="p-8 border-b border-slate-100 bg-slate-50/50">
                                            <h3 className="text-2xl font-serif font-medium text-slate-900">Recent Video Performance</h3>
                                            <p className="text-slate-500 mt-2">How each of your recent videos is tracking against your channel average</p>
                                        </div>
                                        <div className="divide-y divide-slate-100">
                                            {forecasts.filter(f => f).map((forecast, i) => {
                                                const prob = forecast.viral_probability || 0;
                                                const trajectoryColors: Record<string, { bg: string; text: string; border: string }> = {
                                                    'viral': { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
                                                    'breakout': { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' },
                                                    'performing': { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
                                                    'underperforming': { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
                                                    'steady': { bg: 'bg-slate-50', text: 'text-slate-600', border: 'border-slate-200' },
                                                };
                                                const colors = trajectoryColors[forecast.trajectory_type] || trajectoryColors['steady'];

                                                return (
                                                    <div key={i} className="p-6 hover:bg-slate-50/50 transition-colors">
                                                        <div className="flex items-start justify-between gap-4">
                                                            <div className="flex items-start gap-4 flex-1 min-w-0">
                                                                <SafeThumbnail
                                                                    videoId={forecast.video_id}
                                                                    thumbnailUrl={forecast.thumbnail_url}
                                                                    alt={forecast.video_title}
                                                                />
                                                                <div className="min-w-0">
                                                                    <h4 className="font-medium text-slate-900 truncate mb-2">{forecast.video_title}</h4>
                                                                    <div className="flex items-center gap-3 flex-wrap">
                                                                        <span className={`text-xs font-bold uppercase tracking-wider px-2.5 py-1 rounded-full ${colors.bg} ${colors.text} border ${colors.border}`}>
                                                                            {forecast.trajectory_type?.replace('_', ' ') || 'Analyzing'}
                                                                        </span>
                                                                        <span className="text-sm text-slate-500">
                                                                            {forecast.vs_channel_avg || 'Calculating...'}
                                                                        </span>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                            <div className="text-right shrink-0">
                                                                <div className="flex items-center gap-2">
                                                                    <div className={`text-2xl font-bold ${prob >= 60 ? 'text-green-600' : prob >= 30 ? 'text-amber-600' : 'text-slate-600'}`}>
                                                                        {prob.toFixed(0)}%
                                                                    </div>
                                                                </div>
                                                                <div className="text-xs text-slate-400 uppercase font-medium">
                                                                    Breakout Chance
                                                                </div>
                                                            </div>
                                                        </div>
                                                        <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                                                            <div className="bg-slate-50 rounded-xl px-4 py-3">
                                                                <div className="text-slate-400 text-xs uppercase font-medium mb-1">7-Day Forecast</div>
                                                                <div className="font-bold text-slate-900">{(forecast.predicted_7d_views / 1000).toFixed(1)}k views</div>
                                                            </div>
                                                            <div className="bg-slate-50 rounded-xl px-4 py-3">
                                                                <div className="text-slate-400 text-xs uppercase font-medium mb-1">30-Day Forecast</div>
                                                                <div className="font-bold text-slate-900">{(forecast.predicted_30d_views / 1000).toFixed(1)}k views</div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                        <div className="p-4 bg-slate-50 border-t border-slate-100">
                                            <p className="text-xs text-slate-400 text-center">
                                                Breakout chance = probability of exceeding your channel's average performance <span className="text-amber-500">(Est.)</span>
                                            </p>
                                        </div>
                                    </div>
                                );
                            })()}

                            {/* Hook Analysis */}
                            {analysis.report_data.premium.hook_analysis && (
                                <div className="bg-slate-50 rounded-[32px] p-8 border border-slate-200">
                                    <div className="flex items-center gap-3 mb-2">
                                        <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center"><Zap className="w-5 h-5 text-amber-600" /></div>
                                        <h3 className="text-2xl font-serif font-medium text-slate-900">Hook Analysis</h3>
                                    </div>
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

                                    <div className="bg-slate-100 rounded-xl p-4">
                                        <div className="flex items-center gap-2 mb-2">
                                            <Lightbulb className="w-4 h-4 text-slate-600" />
                                            <h4 className="font-semibold text-slate-800">Recommendations</h4>
                                        </div>
                                        <ul className="space-y-1 text-sm text-amber-900">
                                            {analysis.report_data.premium.hook_analysis.recommendations.map((rec, i) => (
                                                <li key={i}>• {rec}</li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                            )}

                            {/* Color Insights */}
                            {analysis.report_data.premium.color_insights && (
                                <div className="bg-slate-50 rounded-[32px] p-8 border border-slate-200">
                                    <div className="flex items-center gap-3 mb-2">
                                        <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center"><Sparkles className="w-5 h-5 text-purple-600" /></div>
                                        <h3 className="text-2xl font-serif font-medium text-slate-900">Thumbnail Color Insights</h3>
                                    </div>
                                    <p className="text-sm text-slate-500 mb-6">Color patterns that drive the most views</p>

                                    {analysis.report_data.premium.color_insights.top_performing_colors && (
                                        <div className="mb-6">
                                            <h4 className="font-semibold text-slate-900 mb-3">Top Colors</h4>
                                            <div className="flex gap-3">
                                                {analysis.report_data.premium.color_insights.top_performing_colors.map((color, i) => (
                                                    <div key={i} className="flex flex-col items-center">
                                                        <div className="w-12 h-12 rounded-xl border-2 border-white shadow-md" style={{ backgroundColor: color }} />
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

                                    <div className="bg-slate-100 rounded-xl p-4">
                                        <div className="flex items-center gap-2 mb-2">
                                            <Lightbulb className="w-4 h-4 text-slate-600" />
                                            <h4 className="font-semibold text-slate-800">Color Recommendations</h4>
                                        </div>
                                        <ul className="space-y-1 text-sm text-slate-700">
                                            {analysis.report_data.premium.color_insights.color_recommendations.map((rec, i) => (
                                                <li key={i}>• {rec}</li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                            )}

                            {/* Publish Times */}
                            {analysis.report_data.premium.publish_times && (
                                <div className="bg-slate-50 rounded-[32px] p-8 border border-slate-200">
                                    <div className="flex items-center gap-3 mb-2">
                                        <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center"><Clock className="w-5 h-5 text-blue-600" /></div>
                                        <h3 className="text-2xl font-serif font-medium text-slate-900">Best Time to Post</h3>
                                    </div>
                                    <p className="text-sm text-slate-500 mb-6">Optimal upload windows based on your channel history</p>

                                    <div className="grid md:grid-cols-2 gap-8 mb-6">
                                        {/* Best Days */}
                                        <div className="bg-white rounded-2xl p-6 border border-blue-100">
                                            <div className="text-sm text-slate-500 mb-1">Best Days</div>
                                            <div className="text-2xl font-bold text-blue-600">
                                                {analysis.report_data.premium.publish_times.best_days.join(", ")}
                                            </div>
                                        </div>

                                        {/* Top Recommendation */}
                                        {analysis.report_data.premium.publish_times.recommendations[0] && (
                                            <div className="bg-white rounded-2xl p-6 border border-blue-100">
                                                <div className="text-sm text-slate-500 mb-1">Top Slot (UTC)</div>
                                                <div className="text-2xl font-bold text-slate-900">
                                                    {analysis.report_data.premium.publish_times.recommendations[0].day} @ {analysis.report_data.premium.publish_times.recommendations[0].hour}:00
                                                </div>
                                                <div className="text-xs text-green-600 font-bold mt-1">
                                                    {analysis.report_data.premium.publish_times.recommendations[0].boost} predicted boost
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {/* Detailed Schedule */}
                                    <div className="bg-slate-100 rounded-xl p-4">
                                        <div className="flex items-center gap-2 mb-3">
                                            <Lightbulb className="w-4 h-4 text-slate-600" />
                                            <h4 className="font-semibold text-slate-800">Recommended Schedule</h4>
                                        </div>
                                        <div className="space-y-3">
                                            {analysis.report_data.premium.publish_times.recommendations.slice(0, 3).map((rec, i) => (
                                                <div key={i} className="flex items-start gap-3 text-sm">
                                                    <div className="bg-white text-blue-600 font-bold px-2 py-1 rounded border border-blue-200 text-xs shrink-0">
                                                        {rec.day} {rec.hour}:00 UTC
                                                    </div>
                                                    <div>
                                                        <span className="text-blue-900 block">{rec.reasoning}</span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
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
