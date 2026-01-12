"use client";

import { useState, useEffect } from "react";
import {
    BarChart3, TrendingUp, Target, Users, Clock,
    FileText, AlertCircle, CheckCircle2, Loader2,
    ArrowRight, Sparkles, Zap
} from "lucide-react";

interface PremiumDashboardProps {
    channelId?: string;
    channelName?: string;
}

export default function PremiumDashboard({ channelId, channelName }: PremiumDashboardProps) {
    const [loading, setLoading] = useState<string | null>(null);
    const [thumbnailUrl, setThumbnailUrl] = useState("");
    const [title, setTitle] = useState("");
    const [results, setResults] = useState<any>(null);
    const [activeTab, setActiveTab] = useState("thumbnail");

    const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "https://thriving-presence-production-ca4a.up.railway.app";
    const apiKey = process.env.NEXT_PUBLIC_PREMIUM_API_KEY || "";

    const analyzeThumbnail = async () => {
        if (!thumbnailUrl) return;

        setLoading("thumbnail");
        try {
            const response = await fetch(`${apiBaseUrl}/premium/analyze-thumbnail`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-API-Key": apiKey,
                },
                body: JSON.stringify({
                    thumbnail_url: thumbnailUrl,
                    title: title,
                }),
            });

            const data = await response.json();
            setResults({ type: "thumbnail", data: data.thumbnail_analysis });
        } catch (error) {
            console.error("Analysis error:", error);
        } finally {
            setLoading(null);
        }
    };

    const optimizeThumbnail = async () => {
        if (!thumbnailUrl) return;

        setLoading("optimize");
        try {
            const response = await fetch(`${apiBaseUrl}/premium/optimize-thumbnail`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-API-Key": apiKey,
                },
                body: JSON.stringify({
                    thumbnail_url: thumbnailUrl,
                    title: title,
                }),
            });

            const data = await response.json();
            setResults({ type: "optimization", data: data.optimization });
        } catch (error) {
            console.error("Optimization error:", error);
        } finally {
            setLoading(null);
        }
    };

    const getPublishTimes = async () => {
        setLoading("publish");
        try {
            const response = await fetch(`${apiBaseUrl}/premium/optimal-publish-times`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-API-Key": apiKey,
                },
                body: JSON.stringify({
                    content_type: "general",
                }),
            });

            const data = await response.json();
            setResults({ type: "publish", data: data.publish_optimization });
        } catch (error) {
            console.error("Publish time error:", error);
        } finally {
            setLoading(null);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-b from-[#0a0a0a] via-[#0f0f1a] to-[#0a0a0a] text-white p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <div className="flex items-center gap-2 mb-2">
                            <Sparkles className="w-5 h-5 text-emerald-400" />
                            <span className="text-sm text-emerald-400 font-medium">Pro</span>
                        </div>
                        <h1 className="text-3xl font-bold">Premium Analytics</h1>
                        {channelName && (
                            <p className="text-gray-400">for {channelName}</p>
                        )}
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="grid md:grid-cols-4 gap-4 mb-8">
                    <button
                        onClick={() => setActiveTab("thumbnail")}
                        className={`p-4 rounded-lg border transition-all ${activeTab === "thumbnail"
                                ? "bg-emerald-500/20 border-emerald-500/50"
                                : "bg-[#1a1a2e]/50 border-gray-800 hover:border-gray-700"
                            }`}
                    >
                        <BarChart3 className="w-6 h-6 text-emerald-400 mb-2" />
                        <span className="font-medium">CTR Prediction</span>
                    </button>

                    <button
                        onClick={() => setActiveTab("optimize")}
                        className={`p-4 rounded-lg border transition-all ${activeTab === "optimize"
                                ? "bg-purple-500/20 border-purple-500/50"
                                : "bg-[#1a1a2e]/50 border-gray-800 hover:border-gray-700"
                            }`}
                    >
                        <Zap className="w-6 h-6 text-purple-400 mb-2" />
                        <span className="font-medium">Thumbnail Optimizer</span>
                    </button>

                    <button
                        onClick={() => { setActiveTab("publish"); getPublishTimes(); }}
                        className={`p-4 rounded-lg border transition-all ${activeTab === "publish"
                                ? "bg-blue-500/20 border-blue-500/50"
                                : "bg-[#1a1a2e]/50 border-gray-800 hover:border-gray-700"
                            }`}
                    >
                        <Clock className="w-6 h-6 text-blue-400 mb-2" />
                        <span className="font-medium">Publish Times</span>
                    </button>

                    <button
                        onClick={() => setActiveTab("gaps")}
                        className={`p-4 rounded-lg border transition-all ${activeTab === "gaps"
                                ? "bg-orange-500/20 border-orange-500/50"
                                : "bg-[#1a1a2e]/50 border-gray-800 hover:border-gray-700"
                            }`}
                    >
                        <Target className="w-6 h-6 text-orange-400 mb-2" />
                        <span className="font-medium">Gap Analysis</span>
                    </button>
                </div>

                {/* Main Content */}
                <div className="grid lg:grid-cols-3 gap-8">
                    {/* Input Section */}
                    <div className="lg:col-span-1">
                        <div className="bg-[#1a1a2e]/50 border border-gray-800 rounded-xl p-6">
                            <h2 className="font-bold text-lg mb-4">Analyze Your Content</h2>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm text-gray-400 mb-2">Thumbnail URL</label>
                                    <input
                                        type="url"
                                        value={thumbnailUrl}
                                        onChange={(e) => setThumbnailUrl(e.target.value)}
                                        placeholder="https://i.ytimg.com/vi/..."
                                        className="w-full px-4 py-3 bg-[#0a0a0a] border border-gray-700 rounded-lg focus:border-emerald-500 focus:outline-none text-white"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm text-gray-400 mb-2">Video Title</label>
                                    <input
                                        type="text"
                                        value={title}
                                        onChange={(e) => setTitle(e.target.value)}
                                        placeholder="Enter your video title"
                                        className="w-full px-4 py-3 bg-[#0a0a0a] border border-gray-700 rounded-lg focus:border-emerald-500 focus:outline-none text-white"
                                    />
                                </div>

                                {thumbnailUrl && (
                                    <div className="mt-4">
                                        <img
                                            src={thumbnailUrl}
                                            alt="Thumbnail preview"
                                            className="w-full rounded-lg border border-gray-700"
                                            onError={(e) => (e.target as HTMLImageElement).style.display = 'none'}
                                        />
                                    </div>
                                )}

                                <div className="grid grid-cols-2 gap-3 mt-6">
                                    <button
                                        onClick={analyzeThumbnail}
                                        disabled={!thumbnailUrl || loading === "thumbnail"}
                                        className="py-3 bg-emerald-500 hover:bg-emerald-400 disabled:bg-gray-700 disabled:text-gray-500 text-black font-semibold rounded-lg transition-all flex items-center justify-center gap-2"
                                    >
                                        {loading === "thumbnail" ? (
                                            <Loader2 className="w-5 h-5 animate-spin" />
                                        ) : (
                                            <>
                                                <BarChart3 className="w-4 h-4" />
                                                Analyze
                                            </>
                                        )}
                                    </button>

                                    <button
                                        onClick={optimizeThumbnail}
                                        disabled={!thumbnailUrl || loading === "optimize"}
                                        className="py-3 bg-purple-500 hover:bg-purple-400 disabled:bg-gray-700 disabled:text-gray-500 text-white font-semibold rounded-lg transition-all flex items-center justify-center gap-2"
                                    >
                                        {loading === "optimize" ? (
                                            <Loader2 className="w-5 h-5 animate-spin" />
                                        ) : (
                                            <>
                                                <Zap className="w-4 h-4" />
                                                Optimize
                                            </>
                                        )}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Results Section */}
                    <div className="lg:col-span-2">
                        <div className="bg-[#1a1a2e]/50 border border-gray-800 rounded-xl p-6">
                            <h2 className="font-bold text-lg mb-4">Analysis Results</h2>

                            {!results ? (
                                <div className="text-center py-12 text-gray-500">
                                    <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-30" />
                                    <p>Enter a thumbnail URL and click Analyze to see predictions</p>
                                </div>
                            ) : results.type === "thumbnail" ? (
                                <ThumbnailResults data={results.data} />
                            ) : results.type === "optimization" ? (
                                <OptimizationResults data={results.data} />
                            ) : results.type === "publish" ? (
                                <PublishTimeResults data={results.data} />
                            ) : null}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// Results Components
function ThumbnailResults({ data }: { data: any }) {
    const features = data?.features || {};
    const prediction = data?.ctr_prediction || {};

    return (
        <div className="space-y-6">
            {/* CTR Prediction */}
            <div className="flex items-center gap-6">
                <div className="text-center">
                    <div className="text-5xl font-bold text-emerald-400">
                        {prediction.predicted_ctr?.toFixed(1) || "N/A"}%
                    </div>
                    <div className="text-sm text-gray-400 mt-1">Predicted CTR</div>
                </div>

                <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                        <span className="text-sm text-gray-400">Confidence</span>
                        <span className="font-medium">{((prediction.confidence || 0) * 100).toFixed(0)}%</span>
                    </div>
                    <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-emerald-500 rounded-full"
                            style={{ width: `${(prediction.confidence || 0) * 100}%` }}
                        />
                    </div>
                </div>
            </div>

            {/* Features Grid */}
            <div className="grid grid-cols-3 gap-4">
                <div className="bg-[#0a0a0a] rounded-lg p-4">
                    <div className="text-2xl font-bold">{features.face_count || 0}</div>
                    <div className="text-sm text-gray-400">Faces Detected</div>
                </div>
                <div className="bg-[#0a0a0a] rounded-lg p-4">
                    <div className="text-2xl font-bold">{features.word_count || 0}</div>
                    <div className="text-sm text-gray-400">Text Words</div>
                </div>
                <div className="bg-[#0a0a0a] rounded-lg p-4">
                    <div className="text-2xl font-bold">{((features.avg_saturation || 0) * 100).toFixed(0)}%</div>
                    <div className="text-sm text-gray-400">Color Saturation</div>
                </div>
            </div>

            {/* Suggestions */}
            {prediction.improvement_suggestions?.length > 0 && (
                <div>
                    <h3 className="font-medium mb-3">Improvement Suggestions</h3>
                    <ul className="space-y-2">
                        {prediction.improvement_suggestions.map((suggestion: string, i: number) => (
                            <li key={i} className="flex items-start gap-2 text-sm">
                                <AlertCircle className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
                                <span className="text-gray-300">{suggestion}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}

function OptimizationResults({ data }: { data: any }) {
    const issues = data?.issues || [];
    const abTests = data?.ab_test_suggestions || [];

    return (
        <div className="space-y-6">
            {/* Issues */}
            {issues.length > 0 && (
                <div>
                    <h3 className="font-medium mb-3">Issues Found</h3>
                    <div className="space-y-3">
                        {issues.slice(0, 4).map((issue: any, i: number) => (
                            <div key={i} className={`p-4 rounded-lg border ${issue.severity === 'critical' ? 'bg-red-500/10 border-red-500/30' :
                                    issue.severity === 'high' ? 'bg-orange-500/10 border-orange-500/30' :
                                        'bg-yellow-500/10 border-yellow-500/30'
                                }`}>
                                <div className="flex items-center justify-between mb-1">
                                    <span className="font-medium">{issue.issue}</span>
                                    <span className={`text-xs px-2 py-0.5 rounded uppercase ${issue.severity === 'critical' ? 'bg-red-500/20 text-red-400' :
                                            issue.severity === 'high' ? 'bg-orange-500/20 text-orange-400' :
                                                'bg-yellow-500/20 text-yellow-400'
                                        }`}>{issue.severity}</span>
                                </div>
                                <p className="text-sm text-gray-400">{issue.fix}</p>
                                <div className="text-xs text-emerald-400 mt-1">{issue.expected_improvement} improvement</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* A/B Tests */}
            {abTests.length > 0 && (
                <div>
                    <h3 className="font-medium mb-3">A/B Test Suggestions</h3>
                    <div className="space-y-2">
                        {abTests.slice(0, 3).map((test: any, i: number) => (
                            <div key={i} className="flex items-center justify-between p-3 bg-[#0a0a0a] rounded-lg">
                                <div>
                                    <span className="font-medium">{test.variant}</span>
                                    <p className="text-sm text-gray-400">{test.description}</p>
                                </div>
                                <span className="text-emerald-400 font-bold">{test.expected_ctr_lift}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

function PublishTimeResults({ data }: { data: any }) {
    const recommendations = data?.schedule_recommendations || [];
    const bestDays = data?.best_days || [];

    return (
        <div className="space-y-6">
            <div className="flex items-center gap-4">
                <Clock className="w-8 h-8 text-blue-400" />
                <div>
                    <h3 className="font-medium">Best Days to Publish</h3>
                    <p className="text-2xl font-bold text-blue-400">{bestDays.join(", ")}</p>
                </div>
            </div>

            <div>
                <h3 className="font-medium mb-3">Recommended Schedule</h3>
                <div className="space-y-2">
                    {recommendations.slice(0, 5).map((rec: any, i: number) => (
                        <div key={i} className="flex items-center justify-between p-3 bg-[#0a0a0a] rounded-lg">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center">
                                    <span className="text-blue-400 font-bold">{i + 1}</span>
                                </div>
                                <div>
                                    <span className="font-medium">{rec.day} at {rec.hour_utc}:00 UTC</span>
                                    <p className="text-sm text-gray-400">{rec.reasoning}</p>
                                </div>
                            </div>
                            <span className="text-emerald-400 font-bold">{rec.expected_view_boost}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
