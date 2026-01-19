'use client';

import React from 'react';
import { MetricCard } from './MetricCard';
import { SentimentPieChart } from './DataCharts';
import { MessageCircle, HelpCircle, Reply, Users, ThumbsUp } from 'lucide-react';

interface EngagementMetrics {
    cvr: number;
    cvrBenchmark: string;
    questionDensity: number;
    depthScore: number;
    repeatScore: number;
    totalComments: number;
    sentiments: {
        positive: number;
        neutral: number;
        negative: number;
        questions: number;
    };
}

interface EngagementSectionProps {
    metrics: EngagementMetrics;
}

export function EngagementSection({ metrics }: EngagementSectionProps) {
    // Determine status based on benchmarks
    const getCvrStatus = (cvr: number, type: string): 'above' | 'at' | 'below' => {
        const benchmarks: Record<string, { low: number; high: number }> = {
            educational: { low: 1.0, high: 2.0 },
            tutorial: { low: 0.5, high: 1.0 },
            entertainment: { low: 0.1, high: 0.5 },
        };
        const bench = benchmarks[type] || benchmarks.educational;
        if (cvr >= bench.high) return 'above';
        if (cvr >= bench.low) return 'at';
        return 'below';
    };

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

    const getRepeatStatus = (rs: number): 'above' | 'at' | 'below' => {
        if (rs >= 20) return 'above';
        if (rs >= 10) return 'at';
        return 'below';
    };

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
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                <MetricCard
                    label="Comment-to-View Ratio"
                    value={`${metrics.cvr.toFixed(2)}%`}
                    benchmark={`${(metrics as unknown as { cvrBenchmarkLabel?: string }).cvrBenchmarkLabel || metrics.cvrBenchmark}: ${(metrics as unknown as { cvrBenchmarkRange?: string }).cvrBenchmarkRange || '1-2%'}`}
                    status={getCvrStatus(metrics.cvr, metrics.cvrBenchmark)}
                    icon={<MessageCircle className="w-5 h-5" />}
                    color="blue"
                    description={`${(metrics as unknown as { cvrVsBenchmark?: number }).cvrVsBenchmark !== undefined
                        ? `${(metrics as unknown as { cvrVsBenchmark: number }).cvrVsBenchmark > 0 ? '+' : ''}${(metrics as unknown as { cvrVsBenchmark: number }).cvrVsBenchmark}% vs benchmark. `
                        : ''}Higher CVR indicates more engaging content`}
                />

                <MetricCard
                    label="Audience Engagement Depth"
                    value={`${metrics.questionDensity.toFixed(1)}%`}
                    benchmark="High quality: 30-40%"
                    status={getQuestionStatus(metrics.questionDensity)}
                    icon={<HelpCircle className="w-5 h-5" />}
                    color="purple"
                    description="Percentage of comments that are questions, indicating engaged learning"
                />

                <MetricCard
                    label="Comment Depth"
                    value={metrics.depthScore.toFixed(2)}
                    benchmark="Good community: >0.5"
                    status={getDepthStatus(metrics.depthScore)}
                    icon={<Reply className="w-5 h-5" />}
                    color="green"
                    description="Ratio of replies to top-level comments, showing conversation depth"
                />

                <MetricCard
                    label="Audience Loyalty"
                    value={`${metrics.repeatScore.toFixed(1)}%`}
                    benchmark="Loyal audience: >20%"
                    status={getRepeatStatus(metrics.repeatScore)}
                    icon={<Users className="w-5 h-5" />}
                    color="orange"
                    description="Viewers who comment on multiple videos, showing true fans"
                />
            </div>

            {/* Sentiment Analysis */}
            <div className="bg-white rounded-[24px] p-6 border border-slate-100 shadow-sm">
                <h3 className="text-lg font-semibold text-slate-900 mb-4">Audience Sentiment Distribution</h3>
                <SentimentPieChart data={metrics.sentiments} size={140} />

                <div className="mt-4 pt-4 border-t border-slate-100">
                    <div className="flex items-center gap-2 text-sm text-slate-600">
                        <ThumbsUp className="w-4 h-4 text-green-500" />
                        <span>
                            {metrics.sentiments.positive > 70
                                ? "Your audience sentiment is highly positive — great job!"
                                : metrics.sentiments.positive > 50
                                    ? "Your sentiment is balanced. Consider addressing common frustrations."
                                    : "There are opportunities to improve audience satisfaction."}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}
