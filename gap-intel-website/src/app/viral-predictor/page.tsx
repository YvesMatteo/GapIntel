"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { Sparkles, TrendingUp, AlertCircle, ArrowRight, Zap, Target, PenTool } from "lucide-react";

export default function ViralPredictorPage() {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [formData, setFormData] = useState({
        title: "",
        hook: "",
        topic: "General",
    });

    const searchParams = useSearchParams();
    const accessKey = searchParams.get("key");
    const [channelContext, setChannelContext] = useState<string>("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setResult(null);

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/predict-video`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    ...formData,
                    access_key: accessKey,
                    // Pass empty history for now, backend will fetch if access_key exists
                    history: []
                }),
            });

            if (!response.ok) throw new Error("Prediction failed");

            const data = await response.json();
            setResult(data);
            if (data.channel_context) {
                setChannelContext(data.channel_context);
            }
        } catch (error) {
            console.error(error);
            alert("Failed to generate prediction. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    if (!accessKey) {
        return (
            <main className="min-h-screen bg-[#FAFAFA] flex items-center justify-center p-6">
                <div className="bg-white rounded-[32px] shadow-xl border border-slate-100 p-12 text-center max-w-lg w-full">
                    <div className="w-20 h-20 bg-purple-50 rounded-full flex items-center justify-center text-purple-600 mx-auto mb-6">
                        <Sparkles className="w-10 h-10" />
                    </div>
                    <h1 className="text-2xl font-serif font-medium text-slate-900 mb-4">Select a Report</h1>
                    <p className="text-slate-500 mb-8">
                        The Viral Predictor needs channel history to be accurate. Please open a report from your dashboard and click "Viral Predictor".
                    </p>
                    <a href="/dashboard" className="inline-block w-full bg-slate-900 text-white font-medium py-4 rounded-full hover:bg-slate-800 transition">
                        Go to Dashboard
                    </a>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-[#FAFAFA] pt-24 pb-20">
            <div className="max-w-4xl mx-auto px-6">

                {/* Header */}
                <div className="mb-12 text-center">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-100 text-purple-700 text-sm font-medium mb-4">
                        <Sparkles className="w-4 h-4" /> Pro Feature
                    </div>
                    <h1 className="text-4xl md:text-5xl font-serif font-medium text-slate-900 mb-4">
                        Viral Probability Predictor
                    </h1>
                    <p className="text-lg text-slate-500 max-w-2xl mx-auto">
                        Validate your video ideas before you film. Our AI analyzes your title and hook against millions of data points to predict performance.
                        {channelContext && <span className="block mt-2 font-medium text-purple-600">Analyzing for channel: @{channelContext}</span>}
                    </p>
                </div>

                <div className="grid lg:grid-cols-5 md:grid-cols-2 gap-8 items-start">

                    {/* Input Form */}
                    <div className="lg:col-span-2 md:col-span-1 space-y-6">
                        <div className="bg-white rounded-[32px] shadow-xl shadow-slate-200/50 border border-slate-100 p-8 sticky top-32">
                            <form onSubmit={handleSubmit} className="space-y-6">
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-2">
                                        Video Title
                                    </label>
                                    <input
                                        required
                                        type="text"
                                        value={formData.title}
                                        onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                                        className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500 transition"
                                        placeholder="e.g., I Built a House in 24 Hours"
                                    />
                                    <p className="text-xs text-slate-400 mt-2">Make it punchy and under 60 chars.</p>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-2">
                                        Opening Hook (First Sentence)
                                    </label>
                                    <textarea
                                        required
                                        rows={3}
                                        value={formData.hook}
                                        onChange={(e) => setFormData({ ...formData, hook: e.target.value })}
                                        className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500 transition resize-none"
                                        placeholder="e.g., You won't believe what happened when..."
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-2">
                                        Topic / Niche
                                    </label>
                                    <select
                                        value={formData.topic}
                                        onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                                        className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500 transition appearance-none bg-white"
                                    >
                                        <option>General</option>
                                        <option>Gaming</option>
                                        <option>Education</option>
                                        <option>Entertainment</option>
                                        <option>Tech / Review</option>
                                        <option>Vlog / Lifestyle</option>
                                    </select>
                                </div>

                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full h-14 bg-slate-900 text-white font-medium rounded-full hover:bg-slate-800 transition shadow-lg shadow-slate-900/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                >
                                    {loading ? (
                                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                    ) : (
                                        <>
                                            <Zap className="w-5 h-5" /> Predict Performance
                                        </>
                                    )}
                                </button>
                            </form>
                        </div>
                    </div>

                    {/* Results Area */}
                    <div className="lg:col-span-3 md:col-span-1">
                        {!result && !loading && (
                            <div className="bg-white/50 border border-slate-200/50 rounded-[32px] p-12 text-center h-full flex flex-col items-center justify-center min-h-[400px]">
                                <div className="w-20 h-20 bg-purple-50 rounded-full flex items-center justify-center text-purple-200 mb-6">
                                    <Target className="w-10 h-10" />
                                </div>
                                <h3 className="text-xl font-medium text-slate-900 mb-2">Ready to Analyze</h3>
                                <p className="text-slate-500 max-w-sm">
                                    Enter your video details on the left to get instant AI-powered performance predictions.
                                </p>
                            </div>
                        )}

                        {result && (
                            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                                {/* Score Card */}
                                <div className="bg-white rounded-[32px] shadow-xl shadow-slate-200/50 border border-slate-100 p-8 overflow-hidden relative">
                                    <div className="absolute top-0 right-0 p-8 opacity-5">
                                        <Sparkles className="w-48 h-48" />
                                    </div>

                                    <div className="relative z-10 grid md:grid-cols-2 gap-8 items-center">
                                        <div>
                                            <p className="text-sm font-medium text-slate-500 uppercase tracking-wider mb-2">Viral Probability</p>
                                            <div className="flex items-baseline gap-2">
                                                <span className={`text-6xl font-bold ${result.viral_probability > 0.7 ? 'text-green-600' :
                                                    result.viral_probability > 0.4 ? 'text-yellow-600' : 'text-slate-600'
                                                    }`}>
                                                    {(result.viral_probability * 100).toFixed(0)}%
                                                </span>
                                                <span className="text-slate-400 font-medium">chance</span>
                                            </div>
                                            <div className="w-full bg-slate-100 h-3 rounded-full mt-4 overflow-hidden">
                                                <div
                                                    className={`h-full rounded-full transition-all duration-1000 ${result.viral_probability > 0.7 ? 'bg-green-500' :
                                                        result.viral_probability > 0.4 ? 'bg-yellow-500' : 'bg-slate-500'
                                                        }`}
                                                    style={{ width: `${result.viral_probability * 100}%` }}
                                                />
                                            </div>
                                        </div>

                                        <div className="bg-slate-50 rounded-2xl p-6 border border-slate-100">
                                            <p className="text-sm font-medium text-slate-500 mb-1">Predicted Views</p>
                                            <div className="text-3xl font-bold text-slate-900 mb-4">
                                                {result.predicted_views.toLocaleString()}
                                            </div>
                                            <div className="flex items-center gap-2 text-sm text-slate-600">
                                                <Target className="w-4 h-4 text-purple-500" />
                                                <span>Based on topic benchmarks</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Factor Breakdown */}
                                <div className="grid md:grid-cols-3 gap-6">
                                    {Object.entries(result.factors).map(([key, value]: [string, any]) => (
                                        <div key={key} className="bg-white p-6 rounded-[24px] border border-slate-100 shadow-sm">
                                            <p className="text-sm text-slate-500 capitalize mb-2">{key} Score</p>
                                            <div className="text-2xl font-bold text-slate-900 mb-2">
                                                {(value * 10).toFixed(1)}<span className="text-sm text-slate-400 font-normal">/10</span>
                                            </div>
                                            <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-slate-900 rounded-full"
                                                    style={{ width: `${value * 100}%` }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                {/* Actionable Tips */}
                                {result.tips && result.tips.length > 0 && (
                                    <div className="bg-purple-50 rounded-[32px] p-8 border border-purple-100">
                                        <div className="flex items-center gap-3 mb-6">
                                            <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center text-purple-600 shadow-sm">
                                                <PenTool className="w-5 h-5" />
                                            </div>
                                            <h3 className="text-xl font-medium text-slate-900">Optimization Tips</h3>
                                        </div>
                                        <ul className="space-y-4">
                                            {result.tips.map((tip: string, i: number) => (
                                                <li key={i} className="flex gap-3 text-slate-600 bg-white/60 p-4 rounded-xl">
                                                    <ArrowRight className="w-5 h-5 text-purple-500 shrink-0 mt-0.5" />
                                                    <span>{tip}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </main>
    );
}
