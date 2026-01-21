'use client';

import React from 'react';
import { TrendingUp, TrendingDown, Minus, Calendar, Layers, Zap, Clock, ArrowRight } from 'lucide-react';

interface SeriesInfo {
    name: string;
    video_count: number;
    avg_views: number;
    avg_engagement: number;
    performance_vs_standalone: number;
}

interface GrowthPatternsData {
    consistency_index: number;
    avg_days_between_uploads: number;
    upload_variance: number;
    current_streak: number;
    series_detected: SeriesInfo[];
    series_performance_boost: number;
    growth_trajectory: string;
    views_growth_rate: number;
    optimal_frequency: string;
    consistency_impact?: string;
    recommendations?: string[];
}

interface GrowthPatternsSectionProps {
    data: GrowthPatternsData;
}

export function GrowthPatternsSection({ data }: GrowthPatternsSectionProps) {
    const getTrajectoryIcon = () => {
        switch (data.growth_trajectory) {
            case 'accelerating': return <TrendingUp className="w-5 h-5 text-green-500" />;
            case 'declining': return <TrendingDown className="w-5 h-5 text-red-500" />;
            default: return <Minus className="w-5 h-5 text-yellow-500" />;
        }
    };

    const getTrajectoryColor = () => {
        switch (data.growth_trajectory) {
            case 'accelerating': return 'text-green-600 bg-green-50 border-green-200';
            case 'declining': return 'text-red-600 bg-red-50 border-red-200';
            default: return 'text-yellow-600 bg-yellow-50 border-yellow-200';
        }
    };

    const getConsistencyColor = (score: number) => {
        if (score >= 70) return 'text-green-600';
        if (score >= 40) return 'text-yellow-600';
        return 'text-red-600';
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-serif font-medium text-slate-900">Growth Patterns</h2>
                    <p className="text-slate-500 mt-1">Upload consistency and content series performance</p>
                </div>
                <div className={`flex items-center gap-2 px-4 py-2 rounded-full border ${getTrajectoryColor()}`}>
                    {getTrajectoryIcon()}
                    <span className="text-sm font-bold capitalize">
                        {data.growth_trajectory || 'steady'} ({(data.views_growth_rate ?? 0) > 0 ? '+' : ''}{data.views_growth_rate ?? 0}%)
                    </span>
                </div>
            </div>

            {/* Main Metrics Grid */}
            <div className="grid md:grid-cols-4 gap-4">
                <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                        <Calendar className="w-4 h-4 text-blue-500" />
                        <span className="text-sm font-medium text-slate-600">Consistency Index</span>
                    </div>
                    <div className={`text-2xl font-bold ${getConsistencyColor(data.consistency_index)}`}>
                        {data.consistency_index}
                    </div>
                    <p className="text-xs text-slate-400 mt-1">
                        {data.consistency_impact || 'Higher = more regular uploads'}
                    </p>
                </div>

                <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                        <Clock className="w-4 h-4 text-purple-500" />
                        <span className="text-sm font-medium text-slate-600">Upload Frequency</span>
                    </div>
                    <div className="text-2xl font-bold text-slate-900">
                        {(data.avg_days_between_uploads ?? 0).toFixed(0)}d
                    </div>
                    <p className="text-xs text-slate-400 mt-1">Avg days between uploads</p>
                </div>

                <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                        <Layers className="w-4 h-4 text-green-500" />
                        <span className="text-sm font-medium text-slate-600">Series Detected</span>
                    </div>
                    <div className="text-2xl font-bold text-slate-900">
                        {data.series_detected?.length || 0}
                    </div>
                    <p className="text-xs text-slate-400 mt-1">Multi-part content series</p>
                </div>

                <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                        <Zap className="w-4 h-4 text-orange-500" />
                        <span className="text-sm font-medium text-slate-600">Series Boost</span>
                    </div>
                    <div className={`text-2xl font-bold ${data.series_performance_boost > 0 ? 'text-green-600' : 'text-slate-900'}`}>
                        {(data.series_performance_boost ?? 0) > 0 ? '+' : ''}{data.series_performance_boost ?? 0}%
                    </div>
                    <p className="text-xs text-slate-400 mt-1">vs standalone videos</p>
                </div>
            </div>

            {/* Content Series List */}
            {data.series_detected && data.series_detected.length > 0 && (
                <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
                    <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                        <Layers className="w-5 h-5 text-purple-500" />
                        Detected Content Series
                    </h3>
                    <div className="space-y-3">
                        {data.series_detected.slice(0, 5).map((series, i) => (
                            <div key={i} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
                                <div>
                                    <div className="font-medium text-slate-900">{series.name}</div>
                                    <div className="text-sm text-slate-500">{series.video_count} videos</div>
                                </div>
                                <div className="text-right">
                                    <div className="text-sm font-medium text-slate-700">
                                        {series.avg_views?.toLocaleString() || 'N/A'} avg views
                                    </div>
                                    {series.performance_vs_standalone !== 0 && (
                                        <div className={`text-xs ${series.performance_vs_standalone > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                            {series.performance_vs_standalone > 0 ? '+' : ''}{series.performance_vs_standalone}% vs standalone
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Optimal Frequency & Recommendations */}
            <div className="grid md:grid-cols-2 gap-4">
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6 border border-blue-100">
                    <h3 className="text-lg font-semibold text-slate-900 mb-2 flex items-center gap-2">
                        <Calendar className="w-5 h-5 text-blue-500" />
                        Optimal Upload Frequency
                    </h3>
                    <div className="text-2xl font-bold text-blue-600 mb-2">{data.optimal_frequency}</div>
                    <p className="text-sm text-slate-600">
                        Based on your performance data, this frequency correlates with highest views.
                    </p>
                </div>

                {data.recommendations && data.recommendations.length > 0 && (
                    <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-6 border border-green-100">
                        <h3 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
                            <TrendingUp className="w-5 h-5 text-green-500" />
                            Growth Recommendations
                        </h3>
                        <ul className="space-y-2">
                            {data.recommendations.slice(0, 3).map((rec, i) => (
                                <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                                    <ArrowRight className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                                    {rec}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>
        </div>
    );
}
