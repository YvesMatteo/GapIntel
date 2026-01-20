'use client';

import React from 'react';

interface HealthScoreGaugeProps {
    score: number;
    size?: 'sm' | 'md' | 'lg';
    showLabel?: boolean;
}

export function HealthScoreGauge({ score, size = 'lg', showLabel = true }: HealthScoreGaugeProps) {
    const sizeConfig = {
        sm: { width: 100, strokeWidth: 8, fontSize: 'text-2xl' },
        md: { width: 140, strokeWidth: 10, fontSize: 'text-4xl' },
        lg: { width: 180, strokeWidth: 12, fontSize: 'text-5xl' },
    };

    const config = sizeConfig[size];
    const radius = (config.width - config.strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (circumference * Math.min(100, Math.max(0, score))) / 100;

    // Color based on score
    const getColor = (score: number) => {
        if (score >= 70) return { stroke: '#22c55e', bg: 'bg-green-50', text: 'text-green-600' };
        if (score >= 40) return { stroke: '#eab308', bg: 'bg-yellow-50', text: 'text-yellow-600' };
        return { stroke: '#ef4444', bg: 'bg-red-50', text: 'text-red-600' };
    };

    const colors = getColor(score);

    const getLabel = (score: number) => {
        if (score >= 80) return 'Excellent';
        if (score >= 70) return 'Strong';
        if (score >= 55) return 'Good';
        if (score >= 40) return 'Fair';
        return 'Needs Work';
    };

    return (
        <div className="flex flex-col items-center">
            <div className="relative" style={{ width: config.width, height: config.width }}>
                <svg className="w-full h-full transform -rotate-90">
                    {/* Background circle */}
                    <circle
                        cx={config.width / 2}
                        cy={config.width / 2}
                        r={radius}
                        stroke="currentColor"
                        strokeWidth={config.strokeWidth}
                        fill="transparent"
                        className="text-slate-100"
                    />
                    {/* Progress circle */}
                    <circle
                        cx={config.width / 2}
                        cy={config.width / 2}
                        r={radius}
                        stroke={colors.stroke}
                        strokeWidth={config.strokeWidth}
                        fill="transparent"
                        strokeDasharray={circumference}
                        strokeDashoffset={strokeDashoffset}
                        strokeLinecap="round"
                        className="transition-all duration-1000 ease-out"
                    />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center flex-col">
                    <span className={`${config.fontSize} font-bold ${colors.text}`}>{Math.round(score)}</span>
                    {size === 'lg' && <span className="text-xs text-slate-400 uppercase tracking-wider">/ 100</span>}
                </div>
            </div>
            {showLabel && (
                <div className={`mt-2 px-3 py-1 rounded-full ${colors.bg} ${colors.text} text-sm font-semibold`}>
                    {getLabel(score)}
                </div>
            )}
        </div>
    );
}

interface MiniGaugeProps {
    label: string;
    score: number;
    maxScore?: number;
}

export function MiniGauge({ label, score, maxScore = 100 }: MiniGaugeProps) {
    const percentage = (score / maxScore) * 100;
    const getColor = (pct: number) => {
        if (pct >= 70) return 'bg-green-500';
        if (pct >= 40) return 'bg-yellow-500';
        return 'bg-red-500';
    };

    return (
        <div className="flex flex-col items-center">
            <div className="text-xs text-slate-500 mb-1 text-center">{label}</div>
            <div className="w-12 h-12 relative">
                <svg className="w-full h-full transform -rotate-90">
                    <circle cx="24" cy="24" r="20" stroke="#e5e7eb" strokeWidth="4" fill="transparent" />
                    <circle
                        cx="24"
                        cy="24"
                        r="20"
                        stroke={percentage >= 70 ? '#22c55e' : percentage >= 40 ? '#eab308' : '#ef4444'}
                        strokeWidth="4"
                        fill="transparent"
                        strokeDasharray={126}
                        strokeDashoffset={126 - (126 * percentage) / 100}
                        strokeLinecap="round"
                    />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-xs font-bold text-slate-700">{Math.round(score)}</span>
                </div>
            </div>
        </div>
    );
}
