'use client';

import React from 'react';
import { TrendingUp, Calendar, Layers, Users, Video, CheckCircle, Circle, Info } from 'lucide-react';

interface GrowthDriversData {
    uploadConsistency: {
        current: string;
        recommendation: string;
        impact: string | null;
        implemented: boolean;
        realScore?: number | null;
    };
    seriesContent: {
        seriesCount: number;
        topSeries: string | null;
        boost?: number | null;
        implemented: boolean;
    };
    communityEngagement: {
        totalComments?: number;
        responseRate: number | null;
        implemented: boolean;
    };
    multiFormat: {
        formatCount?: number | null;
        hasLongForm: boolean;
        implemented: boolean;
    };
    consistency: {
        daysBetweenUploads: number | null;
        consistencyIndex?: number | null;
        implemented: boolean;
    };
    hasRealGrowthData?: boolean;
}

interface GrowthDriversSectionProps {
    data: GrowthDriversData;
}

export function GrowthDriversSection({ data }: GrowthDriversSectionProps) {
    const drivers = [
        {
            title: 'Upload Consistency',
            description: data.consistency.daysBetweenUploads !== null
                ? `Uploading every ~${data.consistency.daysBetweenUploads} days`
                : data.uploadConsistency.current,
            recommendation: data.uploadConsistency.recommendation,
            metric: data.consistency.consistencyIndex !== null
                ? `${data.consistency.consistencyIndex}% consistency`
                : null,
            implemented: data.uploadConsistency.implemented,
            icon: <Calendar className="w-5 h-5" />,
            bgColor: 'bg-blue-50',
            borderColor: 'border-blue-100',
            metricColor: 'text-blue-600',
        },
        {
            title: 'Content Series',
            description: data.seriesContent.seriesCount > 0
                ? `${data.seriesContent.seriesCount} series detected${data.seriesContent.topSeries ? ` (top: ${data.seriesContent.topSeries})` : ''}`
                : 'No content series detected yet',
            recommendation: 'Create related video series to encourage binge-watching',
            metric: data.seriesContent.boost !== null
                ? `+${data.seriesContent.boost}% vs standalone`
                : null,
            implemented: data.seriesContent.implemented,
            icon: <Layers className="w-5 h-5" />,
            bgColor: 'bg-purple-50',
            borderColor: 'border-purple-100',
            metricColor: 'text-purple-600',
        },
        {
            title: 'Community Engagement',
            description: data.communityEngagement.totalComments
                ? `${data.communityEngagement.totalComments.toLocaleString()} comments received`
                : 'Building community through comments',
            recommendation: 'Reply to comments within the first hour for better engagement',
            metric: null, // Response rate not tracked
            implemented: data.communityEngagement.implemented,
            icon: <Users className="w-5 h-5" />,
            bgColor: 'bg-orange-50',
            borderColor: 'border-orange-100',
            metricColor: 'text-orange-600',
        },
        {
            title: 'Content Diversity',
            description: data.multiFormat.formatCount !== null
                ? `${data.multiFormat.formatCount} different formats used`
                : data.multiFormat.hasLongForm
                    ? 'Long-form content present'
                    : 'Limited format diversity',
            recommendation: 'Experiment with different content formats',
            metric: null,
            implemented: data.multiFormat.implemented,
            icon: <Video className="w-5 h-5" />,
            bgColor: 'bg-pink-50',
            borderColor: 'border-pink-100',
            metricColor: 'text-pink-600',
        },
    ];

    const implementedCount = drivers.filter(d => d.implemented).length;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-serif font-medium text-slate-900">Growth Drivers</h2>
                    <p className="text-slate-500 mt-1">Key factors influencing channel performance</p>
                </div>
                <div className="flex items-center gap-2 px-4 py-2 bg-green-50 rounded-full">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    <span className="text-sm font-medium text-green-700">{implementedCount}/{drivers.length} Active</span>
                </div>
            </div>

            {/* Driver Cards */}
            <div className="grid md:grid-cols-2 gap-4">
                {drivers.map((driver, i) => (
                    <div
                        key={i}
                        className={`${driver.bgColor} rounded-[24px] p-6 border ${driver.borderColor} relative overflow-hidden`}
                    >
                        {/* Status Indicator */}
                        <div className="absolute top-4 right-4">
                            {driver.implemented ? (
                                <div className="flex items-center gap-1 px-2 py-1 bg-green-100 rounded-full">
                                    <CheckCircle className="w-3 h-3 text-green-600" />
                                    <span className="text-xs font-medium text-green-700">Active</span>
                                </div>
                            ) : (
                                <div className="flex items-center gap-1 px-2 py-1 bg-slate-100 rounded-full">
                                    <Circle className="w-3 h-3 text-slate-400" />
                                    <span className="text-xs font-medium text-slate-500">Opportunity</span>
                                </div>
                            )}
                        </div>

                        <div className="flex items-start gap-3">
                            <div className="w-10 h-10 rounded-xl bg-white/60 flex items-center justify-center text-slate-600">
                                {driver.icon}
                            </div>
                            <div className="flex-1">
                                <h3 className="font-semibold text-slate-900">{driver.title}</h3>
                                <p className="text-sm text-slate-600 mt-1">{driver.description}</p>
                            </div>
                        </div>

                        <div className="mt-4 pt-4 border-t border-white/50">
                            {driver.metric ? (
                                <div className="flex items-center">
                                    <span className={`text-sm font-bold ${driver.metricColor}`}>
                                        <TrendingUp className="w-4 h-4 inline mr-1" />
                                        {driver.metric}
                                    </span>
                                </div>
                            ) : null}
                            {!driver.implemented && (
                                <p className="text-xs text-slate-500 mt-2">
                                    💡 {driver.recommendation}
                                </p>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Info Note */}
            {!data.hasRealGrowthData && (
                <div className="bg-slate-50 rounded-2xl p-4 border border-slate-100">
                    <div className="flex items-start gap-3">
                        <Info className="w-5 h-5 text-slate-400 mt-0.5" />
                        <div className="text-sm text-slate-600">
                            <strong>Note:</strong> Detailed growth metrics require analyzing upload patterns over time.
                            As more data becomes available, you&apos;ll see specific performance metrics for each driver.
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
