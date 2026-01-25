'use client';

import React from 'react';
import { MetricCard } from './MetricCard';
import { SentimentPieChart } from './DataCharts';
import { MessageCircle, HelpCircle, Reply, Users, ThumbsUp, AlertCircle } from 'lucide-react';

interface EngagementMetrics {
    cvr: number | null;
    cvrBenchmark: string;
    cvrBenchmarkLabel?: string;
    cvrBenchmarkRange?: string;
    cvrVsBenchmark?: number | null;
    cvrStatus?: 'above' | 'at' | 'below' | null;
    questionDensity: number | null;
    depthScore: number | null;
    repeatScore: number | null;
    totalComments: number;
    sentiments: {
        positive: number | null;
        neutral: number | null;
        negative: number | null;
        questions: number | null;
    };
    hasRealSentiment?: boolean;
    hasRealQuestionData?: boolean;
}

interface EngagementSectionProps {
    metrics: EngagementMetrics;
}

export function EngagementSection({ metrics }: EngagementSectionProps) {
    const getQuestionStatus = (qd: number): 'above' | 'at' | 'below' => {
        if (qd >= 30) return 'above';
        if (qd >= 15) return 'at';
        return 'below';
    };

    const getDepthStatus = (ds: number): 'above' | 'at' | 'below' => {
        if (ds >= 0.5) return 'above';
        if (ds >= 0.2) return 'at';
        return 'below';
    };

    // Check if we have real sentiment data
    const hasRealSentiment = metrics.hasRealSentiment &&
        metrics.sentiments.positive !== null;

    // Convert sentiments for pie chart, using 0s if not available
    const sentimentData = hasRealSentiment ? {
        positive: metrics.sentiments.positive || 0,
        neutral: metrics.sentiments.neutral || 0,
        negative: metrics.sentiments.negative || 0,
        questions: metrics.sentiments.questions || 0,
    } : null;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-serif font-medium text-slate-900">Engagement Intelligence</h2>
                    <p className="text-slate-500 mt-1">How deeply your audience connects with your content</p>
                </div>
                <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 rounded-full">
                    <MessageCircle className="w-4 h-4 text-blue-600" />
                    <span className="text-sm font-medium text-blue-700">{metrics.totalComments.toLocaleString()} comments analyzed</span>
                </div>
            </div>

            {/* Metrics Grid */}
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* CVR - Only show if we had view data (currently not available) */}
                {metrics.cvr !== null ? (
                    <MetricCard
                        label="Comment-to-View Ratio"
                        value={`${metrics.cvr.toFixed(2)}%`}
                        benchmark={`${metrics.cvrBenchmarkLabel || metrics.cvrBenchmark}: ${metrics.cvrBenchmarkRange || '1-2%'}`}
                        status={metrics.cvrStatus || 'at'}
                        icon={<MessageCircle className="w-5 h-5" />}
                        color="blue"
                        description="Higher CVR indicates more engaging content"
                    />
                ) : null}

                {/* Question Density - Only show if we have real data */}
                {metrics.questionDensity !== null ? (
                    <MetricCard
                        label="Audience Engagement Depth"
                        value={`${metrics.questionDensity.toFixed(1)}%`}
                        benchmark="High quality: 30-40%"
                        status={getQuestionStatus(metrics.questionDensity)}
                        icon={<HelpCircle className="w-5 h-5" />}
                        color="purple"
                        description="Percentage of comments that are questions, indicating engaged learning"
                    />
                ) : null}

                {/* Comment Depth - Based on real high signal ratio */}
                {metrics.depthScore !== null ? (
                    <MetricCard
                        label="Signal Quality"
                        value={metrics.depthScore.toFixed(2)}
                        benchmark="Good quality: >0.5"
                        status={getDepthStatus(metrics.depthScore)}
                        icon={<Reply className="w-5 h-5" />}
                        color="green"
                        description="Ratio of high-signal comments showing meaningful engagement"
                    />
                ) : null}

                {/* Repeat commenters - Only show if available (currently not tracked) */}
                {metrics.repeatScore !== null ? (
                    <MetricCard
                        label="Audience Loyalty"
                        value={`${metrics.repeatScore.toFixed(1)}%`}
                        benchmark="Loyal audience: >20%"
                        status={metrics.repeatScore >= 20 ? 'above' : metrics.repeatScore >= 10 ? 'at' : 'below'}
                        icon={<Users className="w-5 h-5" />}
                        color="orange"
                        description="Viewers who comment on multiple videos, showing true fans"
                    />
                ) : null}
            </div>

            {/* Sentiment Analysis */}
            {hasRealSentiment && sentimentData ? (
                <div className="bg-white rounded-[24px] p-6 border border-slate-100 shadow-sm">
                    <h3 className="text-lg font-semibold text-slate-900 mb-4">Audience Sentiment Distribution</h3>
                    <SentimentPieChart data={sentimentData} size={140} />

                    <div className="mt-4 pt-4 border-t border-slate-100">
                        <div className="flex items-center gap-2 text-sm text-slate-600">
                            <ThumbsUp className="w-4 h-4 text-green-500" />
                            <span>
                                {sentimentData.positive > 70
                                    ? "Your audience sentiment is highly positive — great job!"
                                    : sentimentData.positive > 50
                                        ? "Your sentiment is balanced. Consider addressing common frustrations."
                                        : "There are opportunities to improve audience satisfaction."}
                            </span>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="bg-slate-50 rounded-[24px] p-6 border border-slate-200">
                    <div className="flex items-center gap-3 text-slate-500">
                        <AlertCircle className="w-5 h-5" />
                        <div>
                            <h3 className="font-medium text-slate-700">Sentiment Analysis Unavailable</h3>
                            <p className="text-sm">Detailed sentiment analysis requires processing more comment data.</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
