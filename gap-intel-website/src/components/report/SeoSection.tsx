'use client';

import React from 'react';
import { Search, Type, FileText, AlertTriangle, Lightbulb, ArrowRight, Info } from 'lucide-react';

interface SeoData {
    seoStrength: number;
    titleAnalysis: {
        avgScore: number;
        avgLength: number;
        keywordPlacement: number;
        hookUsage: number;
    };
    descriptionAnalysis: {
        avgScore: number;
        frontLoadScore: number;
        hasTimestamps: number;
        hasLinks: number;
    } | null;
    issues: Array<{
        type: string;
        count: number;
        example: string;
        fix: string;
    }>;
    recommendations: string[];
}

interface SeoSectionProps {
    data: SeoData;
}

export function SeoSection({ data }: SeoSectionProps) {
    const getScoreColor = (score: number) => {
        if (score >= 75) return 'text-green-600';
        if (score >= 50) return 'text-orange-600';
        return 'text-red-600';
    };

    const getScoreLabel = (score: number) => {
        if (score >= 80) return 'Excellent';
        if (score >= 65) return 'Good';
        if (score >= 50) return 'Average';
        return 'Needs Work';
    };

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-serif font-medium text-slate-900">SEO & Metadata Optimization</h2>
                <p className="text-slate-500 mt-1">How well your content is optimized for discovery</p>
            </div>

            {/* SEO Strength Overview */}
            <div className="bg-gradient-to-br from-emerald-50 to-teal-50 rounded-[24px] p-6 border border-emerald-100">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-emerald-100 flex items-center justify-center">
                            <Search className="w-6 h-6 text-emerald-600" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-slate-900">Title SEO Score</h3>
                            <p className="text-sm text-slate-500">Based on title length, hooks, and keyword placement</p>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className={`text-4xl font-bold ${getScoreColor(data.seoStrength)}`}>
                            {data.seoStrength}
                        </div>
                        <div className="text-sm text-slate-500">/ 100 • {getScoreLabel(data.seoStrength)}</div>
                    </div>
                </div>

                {/* Progress bar */}
                <div className="h-3 bg-white/60 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-gradient-to-r from-emerald-400 to-teal-500 rounded-full transition-all"
                        style={{ width: `${data.seoStrength}%` }}
                    />
                </div>
            </div>

            {/* Analysis Breakdown */}
            <div className="grid md:grid-cols-2 gap-6">
                {/* Title Analysis */}
                <div className="bg-white rounded-[24px] p-6 border border-slate-100 shadow-sm">
                    <div className="flex items-center gap-2 mb-4">
                        <Type className="w-5 h-5 text-blue-600" />
                        <h3 className="text-lg font-semibold text-slate-900">Title Effectiveness</h3>
                    </div>

                    <div className="space-y-4">
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-slate-600">Average Score</span>
                            <span className={`font-bold ${getScoreColor(data.titleAnalysis.avgScore)}`}>
                                {data.titleAnalysis.avgScore.toFixed(0)}/100
                            </span>
                        </div>

                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-500">Avg Length</span>
                                <span className={data.titleAnalysis.avgLength >= 50 && data.titleAnalysis.avgLength <= 60 ? 'text-green-600' : 'text-orange-600'}>
                                    {data.titleAnalysis.avgLength} chars
                                </span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-500">Keyword in first 30 chars</span>
                                <span className={data.titleAnalysis.keywordPlacement >= 70 ? 'text-green-600' : 'text-orange-600'}>
                                    {data.titleAnalysis.keywordPlacement}%
                                </span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-500">Hook pattern usage</span>
                                <span className={data.titleAnalysis.hookUsage >= 50 ? 'text-green-600' : 'text-orange-600'}>
                                    {data.titleAnalysis.hookUsage}%
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Description Analysis - only show if available */}
                {data.descriptionAnalysis ? (
                    <div className="bg-white rounded-[24px] p-6 border border-slate-100 shadow-sm">
                        <div className="flex items-center gap-2 mb-4">
                            <FileText className="w-5 h-5 text-purple-600" />
                            <h3 className="text-lg font-semibold text-slate-900">Description Quality</h3>
                        </div>

                        <div className="space-y-4">
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-slate-600">Average Score</span>
                                <span className={`font-bold ${getScoreColor(data.descriptionAnalysis.avgScore)}`}>
                                    {data.descriptionAnalysis.avgScore.toFixed(0)}/100
                                </span>
                            </div>

                            <div className="space-y-2">
                                <div className="flex justify-between text-sm">
                                    <span className="text-slate-500">Front-loaded value</span>
                                    <span className={data.descriptionAnalysis.frontLoadScore >= 70 ? 'text-green-600' : 'text-orange-600'}>
                                        {data.descriptionAnalysis.frontLoadScore}%
                                    </span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-slate-500">Has timestamps</span>
                                    <span className={data.descriptionAnalysis.hasTimestamps >= 50 ? 'text-green-600' : 'text-orange-600'}>
                                        {data.descriptionAnalysis.hasTimestamps}% of videos
                                    </span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-slate-500">Has links/CTAs</span>
                                    <span className={data.descriptionAnalysis.hasLinks >= 50 ? 'text-green-600' : 'text-orange-600'}>
                                        {data.descriptionAnalysis.hasLinks}% of videos
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="bg-slate-50 rounded-[24px] p-6 border border-slate-200">
                        <div className="flex items-center gap-2 mb-4">
                            <FileText className="w-5 h-5 text-slate-400" />
                            <h3 className="text-lg font-semibold text-slate-700">Description Quality</h3>
                        </div>
                        <div className="flex items-center gap-3 text-slate-500">
                            <Info className="w-5 h-5" />
                            <p className="text-sm">Description analysis requires additional data collection.</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Issues & Fixes */}
            {data.issues.length > 0 && (
                <div className="bg-orange-50 rounded-[24px] p-6 border border-orange-100">
                    <div className="flex items-center gap-2 mb-4">
                        <AlertTriangle className="w-5 h-5 text-orange-600" />
                        <h3 className="text-lg font-semibold text-orange-800">Optimization Opportunities</h3>
                    </div>

                    <div className="space-y-4">
                        {data.issues.slice(0, 3).map((issue, i) => (
                            <div key={i} className="bg-white rounded-xl p-4">
                                <div className="flex items-start gap-3">
                                    <div className="w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center shrink-0">
                                        <span className="text-sm font-bold text-orange-600">{issue.count}</span>
                                    </div>
                                    <div className="flex-1">
                                        <h4 className="font-medium text-slate-900">{issue.type}</h4>
                                        <p className="text-sm text-slate-500 mt-1">Example: &quot;{issue.example}&quot;</p>
                                        <div className="flex items-center gap-1 mt-2 text-sm text-green-600">
                                            <Lightbulb className="w-4 h-4" />
                                            <span>{issue.fix}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Recommendations */}
            {data.recommendations.length > 0 && (
                <div className="bg-blue-50 rounded-[24px] p-6 border border-blue-100">
                    <div className="flex items-center gap-2 mb-4">
                        <Lightbulb className="w-5 h-5 text-blue-600" />
                        <h3 className="text-lg font-semibold text-blue-800">Recommendations</h3>
                    </div>
                    <ul className="space-y-2">
                        {data.recommendations.slice(0, 4).map((rec, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm text-blue-700">
                                <ArrowRight className="w-4 h-4 mt-0.5 shrink-0" />
                                <span>{rec}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}
