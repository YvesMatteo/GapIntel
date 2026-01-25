'use client';

import React from 'react';
import { HealthScoreGauge, MiniGauge } from './HealthScoreGauge';
import { Sparkles, TrendingUp, Target, Zap, BarChart3 } from 'lucide-react';

interface ChannelHealthData {
    overall: number;
    engagement: number;
    satisfaction: number | null;
    seo: number;
    growth: number;
    titlePotential: number;
}

interface ChannelHealthSectionProps {
    health: ChannelHealthData;
    channelName: string;
    topInsight?: string;
}

export function ChannelHealthSection({ health, channelName, topInsight }: ChannelHealthSectionProps) {
    // Build components array, only including those with actual data
    const components: Array<{ label: string; score: number; icon: React.ReactNode }> = [
        { label: 'Engagement', score: health.engagement, icon: <BarChart3 className="w-4 h-4" /> },
    ];

    // Only add satisfaction if we have real data
    if (health.satisfaction !== null) {
        components.push({ label: 'Satisfaction', score: health.satisfaction, icon: <Sparkles className="w-4 h-4" /> });
    }

    components.push(
        { label: 'SEO', score: health.seo, icon: <Target className="w-4 h-4" /> },
        { label: 'Growth', score: health.growth, icon: <TrendingUp className="w-4 h-4" /> },
        { label: 'Title Potential', score: health.titlePotential, icon: <Zap className="w-4 h-4" /> }
    );

    return (
        <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-[32px] p-6 md:p-12 text-white relative overflow-hidden shadow-2xl">
            {/* Background decorations */}
            <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/10 blur-3xl rounded-full -mr-32 -mt-32 pointer-events-none" />
            <div className="absolute bottom-0 left-0 w-64 h-64 bg-purple-500/10 blur-3xl rounded-full -ml-16 -mb-16 pointer-events-none" />

            <div className="relative z-10">
                {/* Header */}
                <div className="flex items-center gap-3 mb-8">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                        <Sparkles className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-serif font-medium">Channel Health Score</h2>
                        <p className="text-slate-400 text-sm">Comprehensive analysis of {channelName}</p>
                    </div>
                </div>

                <div className="grid md:grid-cols-2 gap-8 items-center">
                    {/* Main Score */}
                    <div className="flex flex-col items-center text-center">
                        <HealthScoreGauge score={health.overall} size="lg" />
                        <p className="mt-4 text-slate-300 text-sm max-w-xs">
                            Based on engagement quality, SEO strength, and growth potential
                        </p>
                    </div>

                    {/* Component Breakdown */}
                    <div className="space-y-6">
                        <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider">Score Breakdown</h3>
                        <div className={`grid grid-cols-2 sm:grid-cols-${Math.min(components.length, 4)} gap-4`}>
                            {components.map((comp, i) => (
                                <MiniGauge key={i} label={comp.label} score={comp.score} />
                            ))}
                        </div>

                        {topInsight && (
                            <div className="bg-white/5 rounded-2xl p-4 border border-white/10">
                                <div className="text-xs text-slate-400 uppercase tracking-wider mb-2">Top Priority</div>
                                <p className="text-white">{topInsight}</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
