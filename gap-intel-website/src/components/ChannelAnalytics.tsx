"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
    Eye, Clock, Users, TrendingUp, TrendingDown,
    Loader2, RefreshCw, Play, BarChart3
} from "lucide-react";

interface AnalyticsData {
    status: string;
    channel_id: string;
    date_range: {
        start: string;
        end: string;
        days: number;
    };
    overview: {
        total_views: number;
        watch_time_hours: number;
        subscribers_gained: number;
        subscribers_lost: number;
        net_subscribers: number;
        avg_view_duration_seconds: number;
    };
    ctr_summary: {
        avg_ctr: number;
        total_impressions: number;
        video_count: number;
    } | null;
    top_videos: Array<{
        video_id: string;
        views: number;
        watch_time_minutes: number;
        avg_view_duration_seconds: number;
        subscribers_gained: number;
    }>;
}

interface ChannelAnalyticsProps {
    userId: string;
}

const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toLocaleString();
};

const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
};

const MetricCard = ({ icon: Icon, label, value, subValue, color, trend }: {
    icon: React.ElementType;
    label: string;
    value: string;
    subValue?: string;
    color: string;
    trend?: "up" | "down" | null;
}) => (
    <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-slate-50/80 rounded-2xl p-5 border border-slate-100"
    >
        <div className="flex items-center gap-3 mb-3">
            <div className={`w-10 h-10 rounded-xl ${color} flex items-center justify-center`}>
                <Icon className="w-5 h-5 text-white" />
            </div>
            <span className="text-sm text-slate-500 font-medium">{label}</span>
            {trend && (
                trend === "up" ? (
                    <TrendingUp className="w-4 h-4 text-emerald-500 ml-auto" />
                ) : (
                    <TrendingDown className="w-4 h-4 text-red-500 ml-auto" />
                )
            )}
        </div>
        <div className="text-2xl font-bold text-slate-900">{value}</div>
        {subValue && <div className="text-xs text-slate-500 mt-1">{subValue}</div>}
    </motion.div>
);

export default function ChannelAnalytics({ userId }: ChannelAnalyticsProps) {
    const [data, setData] = useState<AnalyticsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [days, setDays] = useState(28);

    const fetchAnalytics = async () => {
        setLoading(true);
        setError(null);

        try {
            const res = await fetch(`/api/youtube-analytics/dashboard?user_id=${userId}&days=${days}`);
            const result = await res.json();

            if (result.status === "not_connected") {
                setError("YouTube Analytics not connected");
                return;
            }

            if (result.status === "success") {
                setData(result);
            } else {
                setError(result.error || "Failed to fetch analytics");
            }
        } catch (err) {
            setError("Failed to load analytics data");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAnalytics();
    }, [userId, days]);

    if (loading) {
        return (
            <div className="bg-white rounded-3xl border border-slate-100 shadow-xl p-8">
                <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-white rounded-3xl border border-slate-100 shadow-xl p-8">
                <div className="text-center py-8">
                    <BarChart3 className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                    <p className="text-slate-500">{error}</p>
                </div>
            </div>
        );
    }

    if (!data) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-3xl border border-slate-100 shadow-xl overflow-hidden"
        >
            {/* Header */}
            <div className="p-6 border-b border-slate-100 bg-gradient-to-r from-red-50 to-orange-50">
                <div className="flex items-center justify-between">
                    <div>
                        <h3 className="text-xl font-bold text-slate-900">Channel Analytics</h3>
                        <p className="text-sm text-slate-500 mt-1">
                            {data.date_range.start} to {data.date_range.end}
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        <select
                            value={days}
                            onChange={(e) => setDays(Number(e.target.value))}
                            className="px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-red-500/20"
                        >
                            <option value={7}>Last 7 days</option>
                            <option value={28}>Last 28 days</option>
                            <option value={90}>Last 90 days</option>
                        </select>
                        <button
                            onClick={fetchAnalytics}
                            className="p-2 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition"
                        >
                            <RefreshCw className="w-4 h-4 text-slate-600" />
                        </button>
                    </div>
                </div>
            </div>

            {/* Metrics Grid */}
            <div className="p-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                    <MetricCard
                        icon={Eye}
                        label="Total Views"
                        value={formatNumber(data.overview.total_views)}
                        color="bg-gradient-to-br from-blue-500 to-indigo-500"
                    />
                    <MetricCard
                        icon={Clock}
                        label="Watch Time"
                        value={`${formatNumber(data.overview.watch_time_hours)}h`}
                        subValue="hours watched"
                        color="bg-gradient-to-br from-purple-500 to-pink-500"
                    />
                    <MetricCard
                        icon={Users}
                        label="Subscribers"
                        value={`+${formatNumber(data.overview.net_subscribers)}`}
                        subValue={`${data.overview.subscribers_gained} gained, ${data.overview.subscribers_lost} lost`}
                        color="bg-gradient-to-br from-emerald-500 to-teal-500"
                        trend={data.overview.net_subscribers > 0 ? "up" : "down"}
                    />
                    <MetricCard
                        icon={BarChart3}
                        label="Avg CTR"
                        value={data.ctr_summary ? `${data.ctr_summary.avg_ctr}%` : "N/A"}
                        subValue={data.ctr_summary ? `${data.ctr_summary.video_count} videos` : undefined}
                        color="bg-gradient-to-br from-orange-500 to-red-500"
                    />
                </div>

                {/* Top Videos */}
                {data.top_videos.length > 0 && (
                    <div>
                        <h4 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                            <Play className="w-5 h-5 text-red-500" />
                            Top Performing Videos
                        </h4>
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-slate-100">
                                        <th className="text-left py-3 px-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">Video</th>
                                        <th className="text-right py-3 px-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">Views</th>
                                        <th className="text-right py-3 px-2 text-xs font-semibold text-slate-500 uppercase tracking-wider hidden md:table-cell">Watch Time</th>
                                        <th className="text-right py-3 px-2 text-xs font-semibold text-slate-500 uppercase tracking-wider hidden md:table-cell">Avg Duration</th>
                                        <th className="text-right py-3 px-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">Subs</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {data.top_videos.map((video, i) => (
                                        <motion.tr
                                            key={video.video_id}
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            transition={{ delay: i * 0.05 }}
                                            className="border-b border-slate-50 hover:bg-slate-50/50 transition"
                                        >
                                            <td className="py-3 px-2">
                                                <a
                                                    href={`https://youtube.com/watch?v=${video.video_id}`}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="flex items-center gap-3 group"
                                                >
                                                    <img
                                                        src={`https://i.ytimg.com/vi/${video.video_id}/mqdefault.jpg`}
                                                        alt=""
                                                        className="w-16 h-9 rounded object-cover"
                                                    />
                                                    <span className="text-sm font-medium text-slate-700 group-hover:text-red-600 transition truncate max-w-[200px]">
                                                        {video.video_id}
                                                    </span>
                                                </a>
                                            </td>
                                            <td className="py-3 px-2 text-right text-sm font-semibold text-slate-900">
                                                {formatNumber(video.views)}
                                            </td>
                                            <td className="py-3 px-2 text-right text-sm text-slate-600 hidden md:table-cell">
                                                {formatNumber(Math.round(video.watch_time_minutes / 60))}h
                                            </td>
                                            <td className="py-3 px-2 text-right text-sm text-slate-600 hidden md:table-cell">
                                                {formatDuration(video.avg_view_duration_seconds)}
                                            </td>
                                            <td className="py-3 px-2 text-right">
                                                <span className={`text-sm font-medium ${video.subscribers_gained > 0 ? 'text-emerald-600' : 'text-slate-400'}`}>
                                                    {video.subscribers_gained > 0 ? `+${video.subscribers_gained}` : '-'}
                                                </span>
                                            </td>
                                        </motion.tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </motion.div>
    );
}
