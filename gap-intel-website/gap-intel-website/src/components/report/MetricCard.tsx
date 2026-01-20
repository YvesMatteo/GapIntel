'use client';

import React from 'react';
import { TrendingUp, TrendingDown, Minus, Info } from 'lucide-react';

interface MetricCardProps {
    label: string;
    value: string | number;
    benchmark?: string;
    status?: 'above' | 'at' | 'below';
    trend?: 'up' | 'down' | 'stable';
    description?: string;
    icon?: React.ReactNode;
    color?: 'blue' | 'green' | 'purple' | 'orange' | 'slate';
}

export function MetricCard({
    label,
    value,
    benchmark,
    status,
    trend,
    description,
    icon,
    color = 'blue'
}: MetricCardProps) {
    const colorConfig = {
        blue: { bg: 'bg-blue-50', border: 'border-blue-100', text: 'text-blue-600', light: 'text-blue-400' },
        green: { bg: 'bg-green-50', border: 'border-green-100', text: 'text-green-600', light: 'text-green-400' },
        purple: { bg: 'bg-purple-50', border: 'border-purple-100', text: 'text-purple-600', light: 'text-purple-400' },
        orange: { bg: 'bg-orange-50', border: 'border-orange-100', text: 'text-orange-600', light: 'text-orange-400' },
        slate: { bg: 'bg-slate-50', border: 'border-slate-100', text: 'text-slate-600', light: 'text-slate-400' },
    };

    const colors = colorConfig[color];

    const statusConfig = {
        above: { label: 'Above Benchmark', color: 'text-green-600', bg: 'bg-green-50' },
        at: { label: 'At Benchmark', color: 'text-slate-600', bg: 'bg-slate-50' },
        below: { label: 'Below Benchmark', color: 'text-orange-600', bg: 'bg-orange-50' },
    };

    return (
        <div className={`${colors.bg} rounded-2xl p-6 border ${colors.border} hover:shadow-lg transition-shadow`}>
            <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                    {icon && <div className={colors.light}>{icon}</div>}
                    <span className="text-sm font-medium text-slate-600">{label}</span>
                </div>
                {trend && (
                    <div className={`flex items-center gap-1 ${trend === 'up' ? 'text-green-500' : trend === 'down' ? 'text-red-500' : 'text-slate-400'}`}>
                        {trend === 'up' && <TrendingUp className="w-4 h-4" />}
                        {trend === 'down' && <TrendingDown className="w-4 h-4" />}
                        {trend === 'stable' && <Minus className="w-4 h-4" />}
                    </div>
                )}
            </div>

            <div className={`text-3xl font-bold ${colors.text} mb-2`}>
                {value}
            </div>

            {benchmark && (
                <div className="text-xs text-slate-500 mb-2">
                    Benchmark: {benchmark}
                </div>
            )}

            {status && (
                <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${statusConfig[status].bg} ${statusConfig[status].color}`}>
                    {statusConfig[status].label}
                </div>
            )}

            {description && (
                <div className="mt-3 pt-3 border-t border-slate-100 flex items-start gap-2">
                    <Info className="w-3 h-3 text-slate-400 mt-0.5 shrink-0" />
                    <p className="text-xs text-slate-500">{description}</p>
                </div>
            )}
        </div>
    );
}

interface StatCardProps {
    label: string;
    value: string | number;
    subtitle?: string;
    icon?: React.ReactNode;
    color?: string;
}

export function StatCard({ label, value, subtitle, icon, color = 'text-slate-900' }: StatCardProps) {
    return (
        <div className="bg-white rounded-xl p-4 border border-slate-100 shadow-sm">
            <div className="flex items-center gap-3">
                {icon && (
                    <div className="w-10 h-10 rounded-lg bg-slate-50 flex items-center justify-center text-slate-500">
                        {icon}
                    </div>
                )}
                <div>
                    <div className={`text-xl font-bold ${color}`}>{value}</div>
                    <div className="text-xs text-slate-500">{label}</div>
                    {subtitle && <div className="text-xs text-slate-400">{subtitle}</div>}
                </div>
            </div>
        </div>
    );
}
