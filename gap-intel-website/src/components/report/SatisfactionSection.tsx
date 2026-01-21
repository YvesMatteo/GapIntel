'use client';

import React from 'react';
import { Smile, Frown, Users, MessageCircle, Lightbulb, CheckCircle, AlertCircle } from 'lucide-react';

interface SatisfactionData {
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
}

interface SatisfactionSectionProps {
    data: SatisfactionData;
}

export function SatisfactionSection({ data }: SatisfactionSectionProps) {
    const getSIColor = (score: number) => {
        if (score >= 70) return 'text-green-600';
        if (score >= 50) return 'text-yellow-600';
        return 'text-red-600';
    };

    const getSIBg = (score: number) => {
        if (score >= 70) return 'bg-green-50 border-green-200';
        if (score >= 50) return 'bg-yellow-50 border-yellow-200';
        return 'bg-red-50 border-red-200';
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-serif font-medium text-slate-900">Viewer Satisfaction</h2>
                    <p className="text-slate-500 mt-1">How well your content meets audience expectations</p>
                </div>
                <div className={`flex items-center gap-2 px-4 py-2 rounded-full border ${getSIBg(data.satisfaction_index ?? 0)}`}>
                    <Smile className={`w-4 h-4 ${getSIColor(data.satisfaction_index ?? 0)}`} />
                    <span className={`text-sm font-bold ${getSIColor(data.satisfaction_index ?? 0)}`}>
                        SI: {data.satisfaction_index ?? 0}
                    </span>
                </div>
            </div>

            {/* Main Metrics Grid */}
            <div className="grid md:grid-cols-4 gap-4">
                <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span className="text-sm font-medium text-slate-600">Success Comments</span>
                    </div>
                    <div className="text-2xl font-bold text-slate-900">{data.success_comments}</div>
                    <p className="text-xs text-slate-400 mt-1">"It worked!" type comments</p>
                </div>

                <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                        <AlertCircle className="w-4 h-4 text-orange-500" />
                        <span className="text-sm font-medium text-slate-600">Confusion Signals</span>
                    </div>
                    <div className="text-2xl font-bold text-slate-900">{data.confusion_signals}</div>
                    <p className="text-xs text-slate-400 mt-1">"I don't understand" comments</p>
                </div>

                <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                        <Users className="w-4 h-4 text-blue-500" />
                        <span className="text-sm font-medium text-slate-600">Return Viewers</span>
                    </div>
                    <div className="text-2xl font-bold text-slate-900">{((data.return_viewer_ratio ?? 0) * 100).toFixed(0)}%</div>
                    <p className="text-xs text-slate-400 mt-1">Comment on multiple videos</p>
                </div>

                <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                        <Lightbulb className="w-4 h-4 text-purple-500" />
                        <span className="text-sm font-medium text-slate-600">Clarity Score</span>
                    </div>
                    <div className="text-2xl font-bold text-slate-900">{data.clarity_score}</div>
                    <p className="text-xs text-slate-400 mt-1">Lower confusion = higher clarity</p>
                </div>
            </div>

            {/* Success vs Confusion Comparison */}
            <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
                <h3 className="text-lg font-semibold text-slate-900 mb-4">Success vs Confusion Ratio</h3>
                <div className="flex items-center gap-4 mb-4">
                    <div className="flex-1">
                        <div className="flex justify-between text-sm mb-1">
                            <span className="text-green-600 font-medium">Success</span>
                            <span className="text-slate-500">{data.success_comments}</span>
                        </div>
                        <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-green-400 to-green-600 rounded-full"
                                style={{ width: `${Math.min(100, (data.success_comments / (data.success_comments + data.confusion_signals || 1)) * 100)}%` }}
                            />
                        </div>
                    </div>
                    <div className="flex-1">
                        <div className="flex justify-between text-sm mb-1">
                            <span className="text-orange-600 font-medium">Confusion</span>
                            <span className="text-slate-500">{data.confusion_signals}</span>
                        </div>
                        <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-orange-400 to-orange-600 rounded-full"
                                style={{ width: `${Math.min(100, (data.confusion_signals / (data.success_comments + data.confusion_signals || 1)) * 100)}%` }}
                            />
                        </div>
                    </div>
                </div>
                <p className="text-sm text-slate-500">
                    {data.success_comments > data.confusion_signals
                        ? "✓ More success signals than confusion — content is well-received"
                        : "⚠️ More confusion than success — consider clearer explanations"}
                </p>
            </div>

            {/* Recommendations */}
            {data.recommendations && data.recommendations.length > 0 && (
                <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-2xl p-6 border border-purple-100">
                    <h3 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
                        <Lightbulb className="w-5 h-5 text-purple-500" />
                        Satisfaction Recommendations
                    </h3>
                    <ul className="space-y-2">
                        {data.recommendations.map((rec, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                                <span className="text-purple-500 mt-0.5">•</span>
                                {rec}
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}
