'use client';

import React from 'react';
import { Users, TrendingUp, Video, BarChart3, Target, Zap, Crown, AlertTriangle } from 'lucide-react';

interface CompetitorData {
    name: string;
    handle?: string;
    subscribers: number;
    avgViews: number;
    cvr: number;
    formatMix: string;
    shortsCount: number;
    longFormCount: number;
    questionDensity?: number;
}

interface CompetitorComparisonProps {
    userChannel: {
        name: string;
        avgViews: number;
        cvr: number;
        formatMix: string;
        shortsCount: number;
        longFormCount: number;
        questionDensity?: number;
        subscribers?: number;
    };
    competitors: CompetitorData[];
    topicsYouMiss?: string[];
    topicsYouDoBetter?: string[];
}

export function CompetitorComparisonSection({ userChannel, competitors, topicsYouMiss = [], topicsYouDoBetter = [] }: CompetitorComparisonProps) {
    // Get max values for scaling bars
    const allCvrs = [userChannel.cvr, ...competitors.map(c => c.cvr)];
    const maxCvr = Math.max(...allCvrs, 1);

    const allViews = [userChannel.avgViews, ...competitors.map(c => c.avgViews)];
    const maxViews = Math.max(...allViews, 1);

    // Determine user's rank
    const sortedByCvr = [...competitors, { name: userChannel.name, cvr: userChannel.cvr, isUser: true }]
        .sort((a, b) => b.cvr - a.cvr);
    const userRank = sortedByCvr.findIndex(c => (c as { isUser?: boolean }).isUser) + 1;

    const getFormatColor = (format: string) => {
        if (format === 'Shorts') return 'bg-red-500/20 text-red-600 border-red-200';
        if (format === 'Long-form') return 'bg-blue-500/20 text-blue-600 border-blue-200';
        return 'bg-purple-500/20 text-purple-600 border-purple-200';
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-serif font-medium text-slate-900">Competitor Comparison</h2>
                    <p className="text-slate-500 mt-1">How you stack up against top channels in your niche</p>
                </div>
                <div className="flex items-center gap-2 px-4 py-2 bg-purple-50 rounded-full">
                    <Users className="w-4 h-4 text-purple-600" />
                    <span className="text-sm font-medium text-purple-700">{competitors.length} competitors analyzed</span>
                </div>
            </div>

            {/* Your Ranking Card */}
            <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-[24px] p-6 text-white relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/20 blur-3xl rounded-full -mr-32 -mt-32 pointer-events-none" />
                <div className="relative z-10 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="w-16 h-16 rounded-2xl bg-white/10 flex items-center justify-center">
                            <Crown className="w-8 h-8 text-amber-400" />
                        </div>
                        <div>
                            <div className="text-sm text-slate-400 font-medium uppercase tracking-wider">Your CVR Rank</div>
                            <div className="text-4xl font-bold">{userRank}/{competitors.length + 1}</div>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className="text-sm text-slate-400">Your CVR</div>
                        <div className="text-3xl font-bold text-green-400">{userChannel.cvr.toFixed(2)}%</div>
                    </div>
                </div>
            </div>

            {/* Side-by-Side Comparison Table */}
            <div className="bg-white rounded-[24px] border border-slate-100 shadow-sm overflow-hidden">
                <div className="p-6 border-b border-slate-100 bg-slate-50/50">
                    <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                        <BarChart3 className="w-5 h-5 text-blue-500" />
                        Head-to-Head Metrics
                    </h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-slate-50 border-b border-slate-100">
                            <tr className="text-left text-sm text-slate-500 font-medium uppercase tracking-wider">
                                <th className="p-4 pl-6">Channel</th>
                                <th className="p-4">Avg Views</th>
                                <th className="p-4">CVR %</th>
                                <th className="p-4">Format</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {/* User row - highlighted */}
                            <tr className="bg-green-50/50 hover:bg-green-50 transition">
                                <td className="p-4 pl-6">
                                    <div className="flex items-center gap-2">
                                        <span className="w-2 h-2 bg-green-500 rounded-full" />
                                        <span className="font-semibold text-slate-900">{userChannel.name}</span>
                                        <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-bold">YOU</span>
                                    </div>
                                </td>
                                <td className="p-4">
                                    <div className="flex items-center gap-2">
                                        <div className="h-2 bg-green-200 rounded-full overflow-hidden w-24">
                                            <div
                                                className="h-full bg-green-500 rounded-full"
                                                style={{ width: `${(userChannel.avgViews / maxViews) * 100}%` }}
                                            />
                                        </div>
                                        <span className="text-slate-700 font-medium">{(userChannel.avgViews / 1000).toFixed(1)}K</span>
                                    </div>
                                </td>
                                <td className="p-4">
                                    <div className="flex items-center gap-2">
                                        <div className="h-2 bg-green-200 rounded-full overflow-hidden w-16">
                                            <div
                                                className="h-full bg-green-500 rounded-full"
                                                style={{ width: `${(userChannel.cvr / maxCvr) * 100}%` }}
                                            />
                                        </div>
                                        <span className="font-bold text-green-600">{userChannel.cvr.toFixed(2)}%</span>
                                    </div>
                                </td>
                                <td className="p-4">
                                    <span className={`px-2 py-1 rounded-md text-xs font-medium border ${getFormatColor(userChannel.formatMix)}`}>
                                        {userChannel.formatMix}
                                    </span>
                                </td>
                            </tr>

                            {/* Competitor rows */}
                            {competitors.map((comp, i) => (
                                <tr key={i} className="hover:bg-slate-50 transition">
                                    <td className="p-4 pl-6">
                                        <div className="flex items-center gap-2">
                                            <span className="w-2 h-2 bg-slate-400 rounded-full" />
                                            <span className="font-medium text-slate-700">{comp.name}</span>
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <div className="flex items-center gap-2">
                                            <div className="h-2 bg-slate-200 rounded-full overflow-hidden w-24">
                                                <div
                                                    className="h-full bg-slate-500 rounded-full"
                                                    style={{ width: `${(comp.avgViews / maxViews) * 100}%` }}
                                                />
                                            </div>
                                            <span className="text-slate-600">{(comp.avgViews / 1000).toFixed(1)}K</span>
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <div className="flex items-center gap-2">
                                            <div className="h-2 bg-slate-200 rounded-full overflow-hidden w-16">
                                                <div
                                                    className="h-full bg-slate-500 rounded-full"
                                                    style={{ width: `${(comp.cvr / maxCvr) * 100}%` }}
                                                />
                                            </div>
                                            <span className={`font-medium ${comp.cvr > userChannel.cvr ? 'text-red-500' : 'text-slate-600'}`}>
                                                {comp.cvr.toFixed(2)}%
                                            </span>
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <span className={`px-2 py-1 rounded-md text-xs font-medium border ${getFormatColor(comp.formatMix)}`}>
                                            {comp.formatMix}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Gap Identification and Opportunities */}
            <div className="grid md:grid-cols-2 gap-6">
                {/* Topics They Cover You Don't */}
                {topicsYouMiss.length > 0 && (
                    <div className="bg-orange-50 rounded-[24px] p-6 border border-orange-100">
                        <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                            <AlertTriangle className="w-5 h-5 text-orange-500" />
                            Topics Competitors Cover
                        </h3>
                        <p className="text-sm text-orange-700 mb-4">Content your competitors are creating that you haven't explored yet.</p>
                        <div className="flex flex-wrap gap-2">
                            {topicsYouMiss.slice(0, 6).map((topic, i) => (
                                <span key={i} className="px-3 py-1.5 bg-white rounded-full text-sm font-medium text-orange-700 border border-orange-200">
                                    {topic}
                                </span>
                            ))}
                        </div>
                    </div>
                )}

                {/* Topics You Cover Better */}
                {topicsYouDoBetter.length > 0 && (
                    <div className="bg-green-50 rounded-[24px] p-6 border border-green-100">
                        <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                            <Zap className="w-5 h-5 text-green-500" />
                            Your Competitive Advantage
                        </h3>
                        <p className="text-sm text-green-700 mb-4">Topics where you outperform the competition.</p>
                        <div className="flex flex-wrap gap-2">
                            {topicsYouDoBetter.slice(0, 6).map((topic, i) => (
                                <span key={i} className="px-3 py-1.5 bg-white rounded-full text-sm font-medium text-green-700 border border-green-200">
                                    {topic}
                                </span>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Format Strategy Comparison */}
            <div className="bg-white rounded-[24px] p-6 border border-slate-100 shadow-sm">
                <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                    <Video className="w-5 h-5 text-purple-500" />
                    Format Strategy Comparison
                </h3>
                <div className="space-y-4">
                    {/* User's format */}
                    <div>
                        <div className="flex justify-between text-sm mb-1">
                            <span className="font-medium text-slate-700">{userChannel.name} <span className="text-green-600">(You)</span></span>
                            <span className="text-slate-500">{userChannel.shortsCount + userChannel.longFormCount} videos</span>
                        </div>
                        <div className="h-4 bg-slate-100 rounded-full overflow-hidden flex">
                            <div
                                className="h-full bg-blue-500"
                                style={{ width: `${(userChannel.longFormCount / (userChannel.shortsCount + userChannel.longFormCount || 1)) * 100}%` }}
                                title="Long-form"
                            />
                            <div
                                className="h-full bg-red-500"
                                style={{ width: `${(userChannel.shortsCount / (userChannel.shortsCount + userChannel.longFormCount || 1)) * 100}%` }}
                                title="Shorts"
                            />
                        </div>
                        <div className="flex justify-between text-xs mt-1 text-slate-500">
                            <span>Long-form ({userChannel.longFormCount})</span>
                            <span>Shorts ({userChannel.shortsCount})</span>
                        </div>
                    </div>

                    {/* Competitors' formats */}
                    {competitors.slice(0, 3).map((comp, i) => (
                        <div key={i}>
                            <div className="flex justify-between text-sm mb-1">
                                <span className="text-slate-600">{comp.name}</span>
                                <span className="text-slate-400">{comp.shortsCount + comp.longFormCount} videos</span>
                            </div>
                            <div className="h-3 bg-slate-100 rounded-full overflow-hidden flex">
                                <div
                                    className="h-full bg-blue-400"
                                    style={{ width: `${(comp.longFormCount / (comp.shortsCount + comp.longFormCount || 1)) * 100}%` }}
                                />
                                <div
                                    className="h-full bg-red-400"
                                    style={{ width: `${(comp.shortsCount / (comp.shortsCount + comp.longFormCount || 1)) * 100}%` }}
                                />
                            </div>
                        </div>
                    ))}
                </div>

                <div className="flex items-center gap-4 mt-4 pt-4 border-t border-slate-100 text-xs">
                    <div className="flex items-center gap-1">
                        <div className="w-3 h-3 bg-blue-500 rounded" />
                        <span className="text-slate-500">Long-form</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-3 h-3 bg-red-500 rounded" />
                        <span className="text-slate-500">Shorts</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
