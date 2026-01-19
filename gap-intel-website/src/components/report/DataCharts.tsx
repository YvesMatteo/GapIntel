'use client';

import React from 'react';

interface SentimentData {
    positive: number;
    neutral: number;
    negative: number;
    questions: number;
}

interface SentimentPieChartProps {
    data: SentimentData;
    size?: number;
}

export function SentimentPieChart({ data, size = 160 }: SentimentPieChartProps) {
    const total = data.positive + data.neutral + data.negative + data.questions;
    if (total === 0) return null;

    // Calculate percentages
    const segments = [
        { label: 'Positive', value: data.positive, color: '#22c55e', pct: (data.positive / total) * 100 },
        { label: 'Neutral', value: data.neutral, color: '#94a3b8', pct: (data.neutral / total) * 100 },
        { label: 'Questions', value: data.questions, color: '#3b82f6', pct: (data.questions / total) * 100 },
        { label: 'Negative', value: data.negative, color: '#ef4444', pct: (data.negative / total) * 100 },
    ].filter(s => s.value > 0);

    // Calculate pie segments
    const radius = size / 2 - 10;
    const center = size / 2;
    let currentAngle = -90; // Start from top

    const paths = segments.map((segment, i) => {
        const angle = (segment.value / total) * 360;
        const startAngle = currentAngle;
        const endAngle = currentAngle + angle;
        currentAngle = endAngle;

        const startRad = (startAngle * Math.PI) / 180;
        const endRad = (endAngle * Math.PI) / 180;

        const x1 = center + radius * Math.cos(startRad);
        const y1 = center + radius * Math.sin(startRad);
        const x2 = center + radius * Math.cos(endRad);
        const y2 = center + radius * Math.sin(endRad);

        const largeArc = angle > 180 ? 1 : 0;

        return {
            ...segment,
            path: `M ${center} ${center} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`,
        };
    });

    return (
        <div className="flex items-center gap-6">
            <svg width={size} height={size} className="shrink-0">
                {paths.map((segment, i) => (
                    <path
                        key={i}
                        d={segment.path}
                        fill={segment.color}
                        stroke="white"
                        strokeWidth="2"
                        className="transition-all hover:opacity-80"
                    />
                ))}
                {/* Center hole for donut effect */}
                <circle cx={center} cy={center} r={radius * 0.5} fill="white" />
            </svg>

            <div className="flex flex-col gap-2">
                {segments.map((segment, i) => (
                    <div key={i} className="flex items-center gap-2">
                        <div
                            className="w-3 h-3 rounded-full shrink-0"
                            style={{ backgroundColor: segment.color }}
                        />
                        <span className="text-sm text-slate-600">{segment.label}</span>
                        <span className="text-sm font-semibold text-slate-900">{segment.pct.toFixed(0)}%</span>
                    </div>
                ))}
            </div>
        </div>
    );
}

interface TopicBarChartProps {
    topics: Array<{
        name: string;
        videoCount: number;
        saturation: number;
        status: 'over' | 'balanced' | 'under' | 'gap';
    }>;
}

export function TopicBarChart({ topics }: TopicBarChartProps) {
    const maxCount = Math.max(...topics.map(t => t.videoCount), 1);

    const statusConfig = {
        over: { color: 'bg-blue-500', label: 'Well Covered', textColor: 'text-blue-600' },
        balanced: { color: 'bg-green-500', label: 'Balanced', textColor: 'text-green-600' },
        under: { color: 'bg-orange-500', label: 'Under-covered', textColor: 'text-orange-600' },
        gap: { color: 'bg-red-500', label: 'Gap', textColor: 'text-red-600' },
    };

    return (
        <div className="space-y-3">
            {topics.slice(0, 8).map((topic, i) => {
                const width = Math.max(5, (topic.videoCount / maxCount) * 100);
                const config = statusConfig[topic.status];

                return (
                    <div key={i} className="group">
                        <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium text-slate-700 truncate max-w-[50%]">
                                {topic.name}
                            </span>
                            <div className="flex items-center gap-3">
                                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${config.color} bg-opacity-10 ${config.textColor}`}>
                                    {topic.saturation.toFixed(1)} sat.
                                </span>
                                <span className="text-xs text-slate-500">
                                    {topic.videoCount} videos
                                </span>
                            </div>
                        </div>
                        <div className="h-2 bg-slate-100 rounded-full overflow-hidden relative">
                            {/* Target zone marker (0.8 - 2.0) */}
                            <div className="absolute top-0 bottom-0 left-[20%] right-[30%] bg-green-500/10 border-x border-green-500/20" title="Balanced Zone" />

                            <div
                                className={`h-full ${config.color} rounded-full transition-all group-hover:opacity-80`}
                                style={{ width: `${Math.min(100, (topic.saturation / 3) * 100)}%` }}
                            />
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

interface FormatDiversityProps {
    formats: Array<{ name: string; count: number; icon: string }>;
}

export function FormatDiversity({ formats }: FormatDiversityProps) {
    return (
        <div className="flex flex-wrap gap-2">
            {formats.map((format, i) => (
                <div
                    key={i}
                    className="flex items-center gap-2 px-3 py-2 bg-slate-50 rounded-lg border border-slate-100"
                >
                    <span className="text-lg">{format.icon}</span>
                    <div>
                        <div className="text-sm font-medium text-slate-700">{format.name}</div>
                        <div className="text-xs text-slate-500">{format.count} videos</div>
                    </div>
                </div>
            ))}
        </div>
    );
}
