'use client';

import React from 'react';
import { TopicBarChart, FormatDiversity } from './DataCharts';
import { Map, Layers, Calendar, Clock, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';

interface ContentLandscapeData {
    topicCoverage: number;
    totalTopics: number;
    topics: Array<{
        name: string;
        videoCount: number;
        saturation: number;
        status: 'over' | 'balanced' | 'under' | 'gap';
    }>;
    formats: Array<{ name: string; count: number; icon: string }>;
    uploadConsistency: {
        score: number;
        avgDaysBetween: number;
        pattern: string;
    };
    freshness: number;
}

interface ContentLandscapeSectionProps {
    data: ContentLandscapeData;
}

export function ContentLandscapeSection({ data }: ContentLandscapeSectionProps) {
    const getConsistencyLabel = (score: number) => {
        if (score >= 80) return { label: 'Highly Consistent', color: 'text-green-600', bg: 'bg-green-50' };
        if (score >= 60) return { label: 'Fairly Consistent', color: 'text-blue-600', bg: 'bg-blue-50' };
        if (score >= 40) return { label: 'Somewhat Irregular', color: 'text-orange-600', bg: 'bg-orange-50' };
        return { label: 'Highly Irregular', color: 'text-red-600', bg: 'bg-red-50' };
    };

    const consistency = getConsistencyLabel(data.uploadConsistency.score);

    const underCoveredTopics = data.topics.filter(t => t.status === 'under' || t.status === 'gap');
    const overCoveredTopics = data.topics.filter(t => t.status === 'over');

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-serif font-medium text-slate-900">Content Landscape</h2>
                <p className="text-slate-500 mt-1">Map of your existing content ecosystem and coverage</p>
            </div>

            {/* Top Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                        <Map className="w-4 h-4 text-blue-500" />
                        <span className="text-xs text-slate-500 font-medium">Topic Coverage</span>
                    </div>
                    <div className="text-2xl font-bold text-slate-900">{data.topicCoverage}%</div>
                    <div className="text-xs text-slate-400">{data.totalTopics} topics detected</div>
                </div>

                <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                        <Layers className="w-4 h-4 text-purple-500" />
                        <span className="text-xs text-slate-500 font-medium">Format Diversity</span>
                    </div>
                    <div className="text-2xl font-bold text-slate-900">{data.formats.length}</div>
                    <div className="text-xs text-slate-400">content formats used</div>
                </div>

                <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                        <Calendar className="w-4 h-4 text-green-500" />
                        <span className="text-xs text-slate-500 font-medium">Upload Consistency</span>
                    </div>
                    <div className={`text-lg font-bold ${consistency.color}`}>{consistency.label}</div>
                    <div className="text-xs text-slate-400">~{data.uploadConsistency.avgDaysBetween} days between uploads</div>
                </div>

                <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                        <Clock className="w-4 h-4 text-orange-500" />
                        <span className="text-xs text-slate-500 font-medium">Content Freshness</span>
                    </div>
                    <div className="text-2xl font-bold text-slate-900">{data.freshness}%</div>
                    <div className="text-xs text-slate-400">published in last 90 days</div>
                </div>
            </div>

            {/* Topic Coverage Chart */}
            <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-white rounded-[24px] p-6 border border-slate-100 shadow-sm">
                    <h3 className="text-lg font-semibold text-slate-900 mb-4">Topic Saturation</h3>
                    <TopicBarChart topics={data.topics} />
                </div>

                <div className="space-y-4">
                    {/* Under-covered Alert */}
                    {underCoveredTopics.length > 0 && (
                        <div className="bg-orange-50 rounded-2xl p-4 border border-orange-100">
                            <div className="flex items-center gap-2 mb-2">
                                <AlertCircle className="w-4 h-4 text-orange-600" />
                                <span className="font-medium text-orange-800">Under-covered Topics</span>
                            </div>
                            <ul className="space-y-1 text-sm text-orange-700">
                                {underCoveredTopics.slice(0, 4).map((t, i) => (
                                    <li key={i}>• {t.name} ({t.videoCount} video{t.videoCount !== 1 ? 's' : ''})</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* Well-covered Note */}
                    {overCoveredTopics.length > 0 && (
                        <div className="bg-blue-50 rounded-2xl p-4 border border-blue-100">
                            <div className="flex items-center gap-2 mb-2">
                                <CheckCircle className="w-4 h-4 text-blue-600" />
                                <span className="font-medium text-blue-800">Well-covered Topics</span>
                            </div>
                            <ul className="space-y-1 text-sm text-blue-700">
                                {overCoveredTopics.slice(0, 4).map((t, i) => (
                                    <li key={i}>• {t.name} ({t.videoCount} videos)</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* Format Diversity */}
                    <div className="bg-white rounded-2xl p-4 border border-slate-100">
                        <h4 className="font-medium text-slate-900 mb-3">Content Formats</h4>
                        <FormatDiversity formats={data.formats} />
                    </div>
                </div>
            </div>

            {/* Growth Impact Note */}
            <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-2xl p-4 border border-green-100">
                <div className="flex items-start gap-3">
                    <TrendingUp className="w-5 h-5 text-green-600 mt-0.5" />
                    <div>
                        <h4 className="font-medium text-green-800">Upload Consistency Impact</h4>
                        <p className="text-sm text-green-700 mt-1">
                            Research shows consistent weekly uploads lead to <strong>156% higher growth</strong>.
                            {data.uploadConsistency.score >= 70
                                ? " You're doing great — keep it up!"
                                : " Consider establishing a more regular schedule."}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
