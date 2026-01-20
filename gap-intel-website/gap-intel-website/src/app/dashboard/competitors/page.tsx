"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { MoveLeft, TrendingUp, Users, Video, BarChart3, AlertCircle } from "lucide-react";

interface CompetitorMetrics {
    metrics: {
        avg_views: number;
        avg_cvr_proxy: number;
        avg_duration_sec: number;
        shorts_count: number;
        long_form_count: number;
        format_mix: string;
    };
    meta: {
        subscriber_count: number;
        handle: string;
        channel_id: string;
    };
    recent_videos: any[];
}

function CompetitorIntelligenceContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const accessKey = searchParams.get("key");
    const [data, setData] = useState<Record<string, CompetitorMetrics> | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        if (!accessKey) return;

        // Fetch report status/result to get competitor data
        fetch(`https://thriving-presence-production-ca4a.up.railway.app/status/${accessKey}`)
            .then((res) => res.json())
            .then((data) => {
                if (data.status === "completed" && data.report_data?.competitor_metrics) {
                    setData(data.report_data.competitor_metrics);
                } else if (data.status === "completed") {
                    // Try to see if it's nested or missing
                    console.log("Full report data:", data);
                    setError("No competitor data found in this report. Try running a new analysis.");
                }
                setLoading(false);
            })
            .catch((err) => {
                console.error(err);
                setError("Failed to load competitor data.");
                setLoading(false);
            });
    }, [accessKey]);

    if (!accessKey) {
        return (
            <div className="flex h-screen items-center justify-center bg-[#0B0C15] text-white">
                <p>Missing Report Key. Go back to your dashboard.</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#0B0C15] text-white p-6 md:p-10">
            <div className="max-w-7xl mx-auto space-y-8">

                {/* Header */}
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => router.back()}
                        className="p-2 hover:bg-white/10 rounded-lg transition"
                    >
                        <MoveLeft className="w-5 h-5 text-gray-400" />
                    </button>
                    <div>
                        <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-blue-500 bg-clip-text text-transparent">
                            Competitor Intelligence
                        </h1>
                        <p className="text-gray-400 text-sm">Deep dive into rival strategies</p>
                    </div>
                </div>

                {loading && (
                    <div className="text-center py-20">
                        <div className="animate-spin w-8 h-8 border-t-2 border-purple-500 rounded-full mx-auto mb-4"></div>
                        <p className="text-gray-400">Loading intelligence data...</p>
                    </div>
                )}

                {error && (
                    <div className="bg-red-500/10 border border-red-500/30 p-4 rounded-lg flex items-center gap-3">
                        <AlertCircle className="w-5 h-5 text-red-400" />
                        <p className="text-red-300">{error}</p>
                    </div>
                )}

                {!loading && data && (
                    <div className="space-y-8">

                        {/* HEAD TO HEAD TABLE */}
                        <div className="bg-[#141522] border border-white/5 rounded-2xl overflow-hidden">
                            <div className="p-6 border-b border-white/5">
                                <h2 className="text-lg font-semibold flex items-center gap-2">
                                    <Users className="w-5 h-5 text-purple-400" />
                                    Head-to-Head Comparison
                                </h2>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-left border-collapse">
                                    <thead className="bg-white/5 text-gray-400 text-sm uppercase">
                                        <tr>
                                            <th className="p-4 pl-6">Channel</th>
                                            <th className="p-4">Subscribers</th>
                                            <th className="p-4">Avg Views</th>
                                            <th className="p-4">Est. CVR (%)</th>
                                            <th className="p-4">Format Mix</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-white/5">
                                        {Object.entries(data).map(([name, comp]) => (
                                            <tr key={name} className="hover:bg-white/5 transition group">
                                                <td className="p-4 pl-6 font-medium text-white group-hover:text-purple-300 transition-colors">
                                                    {name}
                                                </td>
                                                <td className="p-4 text-gray-300">{comp.meta.subscriber_count.toLocaleString()}</td>
                                                <td className="p-4 text-gray-300">{comp.metrics.avg_views.toLocaleString()}</td>
                                                <td className="p-4">
                                                    <div className="flex items-center gap-2">
                                                        <span className={`font-bold ${comp.metrics.avg_cvr_proxy > 5 ? 'text-green-400' : 'text-yellow-400'}`}>
                                                            {comp.metrics.avg_cvr_proxy.toFixed(2)}%
                                                        </span>
                                                    </div>
                                                </td>
                                                <td className="p-4">
                                                    <span className={`px-2 py-1 rounded-md text-xs font-medium border
                                                ${comp.metrics.format_mix === 'Shorts' ? 'bg-red-500/10 border-red-500/30 text-red-300' :
                                                            comp.metrics.format_mix === 'Long-form' ? 'bg-blue-500/10 border-blue-500/30 text-blue-300' :
                                                                'bg-purple-500/10 border-purple-500/30 text-purple-300'}`}>
                                                        {comp.metrics.format_mix}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        {/* VISUALIZATIONS GRID */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {/* Format Mix */}
                            <div className="bg-[#141522] border border-white/5 rounded-2xl p-6">
                                <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                                    <Video className="w-5 h-5 text-blue-400" />
                                    Format Strategy
                                </h3>
                                <div className="space-y-4">
                                    {Object.entries(data).map(([name, comp]) => (
                                        <div key={name}>
                                            <div className="flex justify-between text-sm mb-1">
                                                <span className="text-gray-300">{name}</span>
                                                <span className="text-gray-500 text-xs">{(comp.metrics.shorts_count + comp.metrics.long_form_count)} videos</span>
                                            </div>
                                            <div className="h-4 bg-white/5 rounded-full overflow-hidden flex">
                                                <div
                                                    className="h-full bg-blue-500"
                                                    style={{ width: `${(comp.metrics.long_form_count / (comp.metrics.shorts_count + comp.metrics.long_form_count)) * 100}%` }}
                                                />
                                                <div
                                                    className="h-full bg-red-500"
                                                    style={{ width: `${(comp.metrics.shorts_count / (comp.metrics.shorts_count + comp.metrics.long_form_count)) * 100}%` }}
                                                />
                                            </div>
                                            <div className="flex justify-between text-xs mt-1 text-gray-500">
                                                <span>Long-form ({comp.metrics.long_form_count})</span>
                                                <span>Shorts ({comp.metrics.shorts_count})</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Efficiency */}
                            <div className="bg-[#141522] border border-white/5 rounded-2xl p-6">
                                <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                                    <TrendingUp className="w-5 h-5 text-green-400" />
                                    Engagement Efficiency
                                </h3>
                                <div className="flex items-end justify-around h-60 gap-4">
                                    {Object.entries(data).map(([name, comp]) => {
                                        // Scale bar height max 100%
                                        const maxCvr = Math.max(...Object.values(data).map(d => d.metrics.avg_cvr_proxy));
                                        const heightPct = (comp.metrics.avg_cvr_proxy / (maxCvr * 1.2)) * 100;

                                        return (
                                            <div key={name} className="flex flex-col items-center gap-2 w-full">
                                                <div className="text-sm font-bold text-green-400">{comp.metrics.avg_cvr_proxy.toFixed(1)}%</div>
                                                <div
                                                    className="w-full max-w-[60px] bg-gradient-to-t from-green-500/20 to-green-500 rounded-t-md relative group hover:from-green-400/30 hover:to-green-400 transition-all cursor-pointer"
                                                    style={{ height: `${heightPct > 5 ? heightPct : 5}%` }}
                                                >
                                                    <div className="absolute inset-0 bg-green-400/0 group-hover:bg-green-400/20 transition-all" />
                                                </div>
                                                <div className="text-xs text-gray-500 truncate w-20 text-center">{name}</div>
                                            </div>
                                        )
                                    })}
                                </div>
                                <p className="text-center text-xs text-gray-600 mt-4">Viewer Conversion Rate (Views ÷ Subscribers)</p>
                            </div>
                        </div>

                        {/* RECENT VIDEOS */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            {Object.entries(data).map(([name, comp]) => (
                                <div key={name} className="bg-[#141522] border border-white/5 rounded-2xl p-5">
                                    <h4 className="font-semibold text-purple-300 mb-4 flex items-center gap-2">
                                        <div className="w-2 h-2 rounded-full bg-purple-500"></div>
                                        {name}
                                    </h4>
                                    <div className="space-y-3">
                                        {comp.recent_videos.sort((a, b) => b.views - a.views).slice(0, 3).map((v: any) => (
                                            <div key={v.video_id} className="bg-white/5 p-3 rounded-lg border border-white/5 hover:border-purple-500/30 transition">
                                                <div className="text-sm font-medium line-clamp-1" title={v.title}>{v.title}</div>
                                                <div className="flex justify-between mt-2 text-xs text-gray-400">
                                                    <span className="text-blue-300">{v.views.toLocaleString()} views</span>
                                                    <span>CVR: {v.cvr_proxy.toFixed(1)}%</span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>

                    </div>
                )}
            </div>
        </div>
    );
}

export default function CompetitorIntelligencePage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-[#0B0C15] flex items-center justify-center">
                <div className="animate-spin w-8 h-8 border-t-2 border-purple-500 rounded-full"></div>
            </div>
        }>
            <CompetitorIntelligenceContent />
        </Suspense>
    );
}

