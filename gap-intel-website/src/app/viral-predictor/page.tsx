"use client";

import { useState, Suspense, useEffect, useMemo } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
    Sparkles, TrendingUp, AlertCircle, ArrowRight, Zap, Target, PenTool,
    Type, BarChart3, Lightbulb, CheckCircle, XCircle, Info, RefreshCw,
    ChevronRight, Copy, Check, Ruler, MousePointerClick, Crosshair
} from "lucide-react";
import {
    analyzeTitle,
    generateAlternativeTitles,
    predictViewRange,
    HOOK_PATTERNS,
    AUDIENCE_BENCHMARKS,
    type TitleAnalysis,
    type AlternativeTitle
} from "@/lib/titleAnalyzer";

export default function ViralPredictorPage() {
    return (
        <Suspense fallback={<LoadingState />}>
            <ViralPredictorContent />
        </Suspense>
    );
}

function LoadingState() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-[#FAFAFA]">
            <div className="w-6 h-6 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
        </div>
    );
}

function ViralPredictorContent() {
    const [title, setTitle] = useState("");
    const [hook, setHook] = useState("");
    const [audienceSize, setAudienceSize] = useState<keyof typeof AUDIENCE_BENCHMARKS>("medium");
    const [topic, setTopic] = useState("General");
    const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
    const [isMLPredicting, setIsMLPredicting] = useState(false);
    const [mlPrediction, setMLPrediction] = useState<{
        predicted_views: number;
        viral_probability: number;
        confidence: number;
        factors: Record<string, number>;
        tips: string[];
    } | null>(null);

    const searchParams = useSearchParams();
    const accessKey = searchParams.get("key");

    // Real-time analysis
    const analysis = useMemo(() => analyzeTitle(title), [title]);
    const alternatives = useMemo(() => generateAlternativeTitles(title, topic), [title, topic]);
    const viewPrediction = useMemo(
        () => predictViewRange(analysis.overallScore, audienceSize, analysis.ctrBoost),
        [analysis.overallScore, audienceSize, analysis.ctrBoost]
    );

    // Backend ML Prediction
    useEffect(() => {
        const fetchMLPrediction = async () => {
            if (!title || title.length < 5) {
                setMLPrediction(null);
                return;
            }

            setIsMLPredicting(true);
            try {
                const response = await fetch('https://thriving-presence-production-ca4a.up.railway.app/api/predict-video', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        title,
                        hook,
                        topic,
                        access_key: accessKey
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    setMLPrediction(data);
                }
            } catch (err) {
                console.error("ML Prediction failed:", err);
            } finally {
                setIsMLPredicting(false);
            }
        };

        const timer = setTimeout(fetchMLPrediction, 1000); // Debounce
        return () => clearTimeout(timer);
    }, [title, hook, topic, accessKey]);

    const handleCopyTitle = (altTitle: string, index: number) => {
        navigator.clipboard.writeText(altTitle);
        setCopiedIndex(index);
        setTimeout(() => setCopiedIndex(null), 2000);
    };

    const getScoreColor = (score: number) => {
        if (score >= 75) return 'text-green-600';
        if (score >= 50) return 'text-yellow-600';
        if (score >= 25) return 'text-orange-600';
        return 'text-red-600';
    };

    const getScoreLabel = (score: number) => {
        if (score >= 80) return 'High Viral Potential';
        if (score >= 65) return 'Strong Potential';
        if (score >= 50) return 'Moderate Potential';
        if (score >= 30) return 'Needs Optimization';
        return 'Low Potential';
    };

    const getScoreBg = (score: number) => {
        if (score >= 75) return 'from-green-500 to-emerald-500';
        if (score >= 50) return 'from-yellow-500 to-orange-500';
        if (score >= 25) return 'from-orange-500 to-red-500';
        return 'from-red-500 to-red-600';
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
                    <Link href="/dashboard" className="inline-block w-full bg-slate-900 text-white font-medium py-4 rounded-full hover:bg-slate-800 transition">
                        Go to Dashboard
                    </Link>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-[#FAFAFA] pt-24 pb-20">
            <div className="max-w-6xl mx-auto px-6">

                {/* Header */}
                <div className="mb-12 text-center">
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-slate-100 text-slate-700 text-sm font-medium mb-4 border border-slate-200">
                        <Sparkles className="w-4 h-4" /> Premium Tool
                    </div>
                    <h1 className="text-4xl md:text-5xl font-serif font-medium text-slate-900 mb-4">
                        Viral Title Predictor
                    </h1>
                    <p className="text-lg text-slate-500 max-w-2xl mx-auto">
                        Test your video titles before you film. Our AI analyzes title patterns, hook strength,
                        and CTR factors to predict viral potential.
                    </p>
                </div>

                <div className="grid lg:grid-cols-5 gap-8 items-start">

                    {/* Input Panel */}
                    <div className="lg:col-span-2 space-y-6">
                        <div className="bg-white rounded-[32px] shadow-xl shadow-slate-200/50 border border-slate-100 p-8 sticky top-24">
                            <div className="space-y-6">

                                {/* Title Input with Live Counter */}
                                <div>
                                    <div className="flex items-center justify-between mb-2">
                                        <label className="text-sm font-medium text-slate-700">
                                            Video Title
                                        </label>
                                        <span className={`text-xs font-medium ${title.length >= 50 && title.length <= 60
                                            ? 'text-green-600'
                                            : title.length > 70
                                                ? 'text-red-600'
                                                : 'text-slate-400'
                                            }`}>
                                            {title.length}/60 chars
                                            {title.length >= 50 && title.length <= 60 && <Check className="w-3 h-3 text-green-500 ml-1 inline" />}
                                        </span>
                                    </div>
                                    <input
                                        type="text"
                                        value={title}
                                        onChange={(e) => setTitle(e.target.value)}
                                        className="w-full px-4 py-3.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500 transition text-lg"
                                        placeholder="Enter your video title..."
                                    />

                                    {/* Live Hook Detection */}
                                    {title.length > 0 && (
                                        <div className="mt-3 flex items-center gap-2">
                                            <span className="text-lg">{analysis.hookEmoji}</span>
                                            <span className="text-sm text-slate-600">
                                                Detected: <span className="font-medium text-purple-600">{analysis.hookName}</span>
                                            </span>
                                            {analysis.ctrBoost > 0 && (
                                                <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs font-bold rounded-full">
                                                    +{analysis.ctrBoost}% CTR
                                                </span>
                                            )}
                                        </div>
                                    )}
                                </div>

                                {/* Opening Hook */}
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-2">
                                        Opening Hook (First Sentence)
                                    </label>
                                    <textarea
                                        rows={3}
                                        value={hook}
                                        onChange={(e) => setHook(e.target.value)}
                                        className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500 transition resize-none"
                                        placeholder="What's the first line of your video?"
                                    />
                                </div>

                                {/* Audience Size */}
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-2">
                                        Channel Size
                                    </label>
                                    <select
                                        value={audienceSize}
                                        onChange={(e) => setAudienceSize(e.target.value as keyof typeof AUDIENCE_BENCHMARKS)}
                                        className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500 transition appearance-none bg-white"
                                    >
                                        {Object.entries(AUDIENCE_BENCHMARKS).map(([key, value]) => (
                                            <option key={key} value={key}>{value.label}</option>
                                        ))}
                                    </select>
                                </div>

                                {/* Topic */}
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-2">
                                        Topic / Niche
                                    </label>
                                    <select
                                        value={topic}
                                        onChange={(e) => setTopic(e.target.value)}
                                        className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500 transition appearance-none bg-white"
                                    >
                                        <option>General</option>
                                        <option>Gaming</option>
                                        <option>Education</option>
                                        <option>Entertainment</option>
                                        <option>Tech / Review</option>
                                        <option>Finance / Business</option>
                                        <option>Vlog / Lifestyle</option>
                                    </select>
                                </div>

                                {/* Research Note */}
                                <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
                                    <div className="flex items-start gap-2">
                                        <Lightbulb className="w-4 h-4 text-slate-600 mt-0.5 shrink-0" />
                                        <p className="text-xs text-slate-600">
                                            <strong>Pro Tip:</strong> Number hooks ("7 Ways...") get 3× better CTR.
                                            Keep titles 50-60 characters for optimal display.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Results Panel */}
                    <div className="lg:col-span-3 space-y-6">

                        {/* Empty State */}
                        {title.length === 0 && (
                            <div className="bg-white/50 border border-slate-200/50 rounded-[32px] p-12 text-center flex flex-col items-center justify-center min-h-[400px]">
                                <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center text-slate-300 mb-6">
                                    <Type className="w-10 h-10" />
                                </div>
                                <h3 className="text-xl font-medium text-slate-900 mb-2">Start Typing</h3>
                                <p className="text-slate-500 max-w-sm">
                                    Enter your video title to get instant AI-powered analysis and optimization suggestions.
                                </p>
                            </div>
                        )}

                        {/* Live Results */}
                        {title.length > 0 && (
                            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-300">

                                {/* Viral Score Hero */}
                                <div className="bg-slate-900 rounded-[32px] p-8 text-white relative overflow-hidden shadow-2xl">
                                    <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 blur-3xl rounded-full -mr-32 -mt-32" />

                                    <div className="relative z-10 grid md:grid-cols-2 gap-8 items-center">
                                        <div className="text-center md:text-left">
                                            <div className="flex items-center gap-2 justify-center md:justify-start mb-2">
                                                <p className="text-white/80 text-sm font-medium uppercase tracking-wider">
                                                    Heuristic Viral Score
                                                </p>
                                                <Info className="w-3 h-3 text-white/50 cursor-help" />
                                            </div>
                                            <div className="flex items-baseline gap-2 justify-center md:justify-start">
                                                <span className="text-7xl font-bold">{analysis.overallScore}</span>
                                                <span className="text-3xl text-white/60">/100</span>
                                            </div>
                                            <p className="text-xl font-medium mt-2 text-white/90">
                                                {getScoreLabel(analysis.overallScore)}
                                            </p>
                                        </div>

                                        <div className="space-y-4">
                                            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
                                                <div className="flex items-center gap-2 mb-3">
                                                    <TrendingUp className="w-5 h-5" />
                                                    <span className="font-medium">Standard Prediction</span>
                                                </div>
                                                <div className="text-3xl font-bold mb-1">
                                                    {viewPrediction.display}
                                                </div>
                                                <p className="text-sm text-white/70">
                                                    Based on {AUDIENCE_BENCHMARKS[audienceSize].label}
                                                </p>
                                            </div>

                                            {/* ML Prediction Overlay/Card */}
                                            <div className={`transition-all duration-500 rounded-2xl p-6 border ${mlPrediction ? 'bg-white/20 border-white/40 shadow-lg scale-105' : 'bg-white/5 border-white/10 opacity-60'
                                                }`}>
                                                <div className="flex items-center justify-between mb-3">
                                                    <div className="flex items-center gap-2">
                                                        <Zap className={`w-5 h-5 ${mlPrediction ? 'text-yellow-300 animate-pulse' : 'text-white/40'}`} />
                                                        <span className="font-bold text-white">Scientific ML Analysis</span>
                                                    </div>
                                                    {isMLPredicting && (
                                                        <RefreshCw className="w-4 h-4 text-white/60 animate-spin" />
                                                    )}
                                                </div>

                                                {mlPrediction ? (
                                                    <div className="grid grid-cols-2 gap-4">
                                                        <div>
                                                            <div className="text-2xl font-bold">
                                                                {(mlPrediction.viral_probability * 100).toFixed(0)}%
                                                            </div>
                                                            <p className="text-[10px] text-white/70 uppercase font-bold">Viral Prob.</p>
                                                        </div>
                                                        <div>
                                                            <div className="text-2xl font-bold text-green-300">
                                                                {mlPrediction.predicted_views > 1000000
                                                                    ? `${(mlPrediction.predicted_views / 1000000).toFixed(1)}M`
                                                                    : mlPrediction.predicted_views > 1000
                                                                        ? `${(mlPrediction.predicted_views / 1000).toFixed(1)}K`
                                                                        : mlPrediction.predicted_views
                                                                }
                                                            </div>
                                                            <p className="text-[10px] text-white/70 uppercase font-bold">ML Pred. Views</p>
                                                        </div>
                                                    </div>
                                                ) : (
                                                    <p className="text-xs text-white/60">
                                                        {isMLPredicting ? 'AI is analyzing your title...' : 'Enter title for data-driven prediction'}
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Factor Breakdown */}
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    {/* Title Hook */}
                                    <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
                                        <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center mb-2"><Sparkles className="w-4 h-4 text-slate-600" /></div>
                                        <p className="text-sm text-slate-500 mb-1">Hook Strength</p>
                                        <div className="text-2xl font-bold text-slate-900">
                                            {analysis.thss.toFixed(1)}<span className="text-sm text-slate-400 font-normal">/10</span>
                                        </div>
                                        <div className="mt-2 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-slate-700 rounded-full transition-all"
                                                style={{ width: `${analysis.thss * 10}%` }}
                                            />
                                        </div>
                                    </div>

                                    {/* CTR Boost */}
                                    <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
                                        <div className="w-8 h-8 rounded-lg bg-green-50 flex items-center justify-center mb-2"><TrendingUp className="w-4 h-4 text-green-600" /></div>
                                        <p className="text-sm text-slate-500 mb-1">CTR Boost</p>
                                        <div className="text-2xl font-bold text-green-600">
                                            +{analysis.ctrBoost}%
                                        </div>
                                        <p className="text-xs text-slate-400 mt-2">vs standard titles</p>
                                    </div>

                                    {/* Length Score */}
                                    <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
                                        <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center mb-2"><Ruler className="w-4 h-4 text-blue-600" /></div>
                                        <p className="text-sm text-slate-500 mb-1">Title Length</p>
                                        <div className={`text-2xl font-bold ${analysis.lengthStatus === 'optimal' ? 'text-green-600' :
                                            analysis.lengthStatus === 'truncated' ? 'text-red-600' : 'text-yellow-600'
                                            }`}>
                                            {analysis.lengthValue} chars
                                        </div>
                                        <p className="text-xs text-slate-400 mt-2">
                                            {analysis.lengthStatus === 'optimal' ? (
                                                <span className="flex items-center gap-1.5"><CheckCircle className="w-4 h-4" /> Perfect</span>
                                            ) : analysis.lengthStatus === 'truncated' ? (
                                                <span className="flex items-center gap-1.5"><AlertCircle className="w-4 h-4" /> Will truncate</span>
                                            ) : analysis.lengthStatus === 'short' ? (
                                                '↑ Could be longer'
                                            ) : (
                                                '↓ Slightly long'
                                            )}
                                        </p>
                                    </div>

                                    {/* Structure */}
                                    <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
                                        <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center mb-2"><Target className="w-4 h-4 text-indigo-600" /></div>
                                        <p className="text-sm text-slate-500 mb-1">Structure</p>
                                        <div className="text-2xl font-bold text-slate-900">
                                            {analysis.tse.toFixed(1)}<span className="text-sm text-slate-400 font-normal">/10</span>
                                        </div>
                                        <div className="mt-2 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-blue-500 rounded-full transition-all"
                                                style={{ width: `${analysis.tse * 10}%` }}
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* Issues & Strengths */}
                                {(analysis.issues.length > 0 || analysis.strengths.length > 0) && (
                                    <div className="grid md:grid-cols-2 gap-4">
                                        {analysis.strengths.length > 0 && (
                                            <div className="bg-green-50 rounded-2xl p-5 border border-green-100">
                                                <div className="flex items-center gap-2 mb-3">
                                                    <CheckCircle className="w-5 h-5 text-green-600" />
                                                    <span className="font-medium text-green-800">Strengths</span>
                                                </div>
                                                <ul className="space-y-2">
                                                    {analysis.strengths.map((s, i) => (
                                                        <li key={i} className="flex items-start gap-2 text-sm text-green-700">
                                                            <ChevronRight className="w-4 h-4 mt-0.5 shrink-0" />
                                                            <span>{s}</span>
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}

                                        {analysis.issues.length > 0 && (
                                            <div className="bg-orange-50 rounded-2xl p-5 border border-orange-100">
                                                <div className="flex items-center gap-2 mb-3">
                                                    <AlertCircle className="w-5 h-5 text-orange-600" />
                                                    <span className="font-medium text-orange-800">Improvements</span>
                                                </div>
                                                <ul className="space-y-2">
                                                    {analysis.issues.map((issue, i) => (
                                                        <li key={i} className="flex items-start gap-2 text-sm text-orange-700">
                                                            <ChevronRight className="w-4 h-4 mt-0.5 shrink-0" />
                                                            <span>{issue}</span>
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Alternative Titles */}
                                {alternatives.length > 0 && (
                                    <div className="bg-white rounded-[24px] p-6 border border-slate-100 shadow-sm">
                                        <div className="flex items-center gap-3 mb-5">
                                            <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center">
                                                <RefreshCw className="w-5 h-5 text-slate-600" />
                                            </div>
                                            <div>
                                                <h3 className="text-lg font-semibold text-slate-900">Alternative Titles</h3>
                                                <p className="text-sm text-slate-500">AI-generated variants with different hooks</p>
                                            </div>
                                        </div>

                                        <div className="space-y-4">
                                            {/* Original */}
                                            <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                                                <div className="flex items-center justify-between mb-2">
                                                    <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Your Title</span>
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-xs px-2 py-0.5 bg-slate-200 text-slate-600 rounded-full">
                                                            {analysis.hookName}
                                                        </span>
                                                    </div>
                                                </div>
                                                <p className="text-slate-900 font-medium">{title}</p>
                                                <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                                                    <span>THSS: {analysis.thss.toFixed(1)}</span>
                                                    <span>CTR: +{analysis.ctrBoost}%</span>
                                                </div>
                                            </div>

                                            {/* Alternatives */}
                                            {alternatives.map((alt, i) => (
                                                <div
                                                    key={i}
                                                    className="bg-slate-50 rounded-xl p-4 border border-slate-200 hover:bg-slate-100 transition group"
                                                >
                                                    <div className="flex items-center justify-between mb-2">
                                                        <div className="flex items-center gap-2">
                                                            <div className="w-6 h-6 rounded-md bg-slate-200 flex items-center justify-center"><Sparkles className="w-3 h-3 text-slate-600" /></div>
                                                            <span className="text-xs font-medium text-slate-600 uppercase tracking-wider">
                                                                {alt.hookName}
                                                            </span>
                                                        </div>
                                                        <button
                                                            onClick={() => handleCopyTitle(alt.title, i)}
                                                            className="opacity-0 group-hover:opacity-100 transition p-2 hover:bg-slate-200 rounded-lg"
                                                        >
                                                            {copiedIndex === i ? (
                                                                <Check className="w-4 h-4 text-green-600" />
                                                            ) : (
                                                                <Copy className="w-4 h-4 text-slate-600" />
                                                            )}
                                                        </button>
                                                    </div>
                                                    <p className="text-slate-900 font-medium">{alt.title}</p>
                                                    <div className="flex items-center gap-4 mt-2 text-xs">
                                                        <span className="text-slate-500">THSS: {alt.thss.toFixed(1)}</span>
                                                        <span className="text-green-600 font-medium">{alt.improvement}</span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Research Insights */}
                                <div className="bg-slate-50 rounded-[24px] p-6 border border-slate-100">
                                    <div className="flex items-center gap-2 mb-4">
                                        <BarChart3 className="w-5 h-5 text-slate-600" />
                                        <h3 className="font-semibold text-slate-900">Research-Backed Insights</h3>
                                    </div>
                                    <div className="grid md:grid-cols-2 gap-4 text-sm">
                                        <div className="flex items-start gap-2">
                                            <Info className="w-4 h-4 text-blue-500 mt-0.5 shrink-0" />
                                            <span className="text-slate-600">Number hooks get <strong>3× better CTR</strong> than standard titles</span>
                                        </div>
                                        <div className="flex items-start gap-2">
                                            <Info className="w-4 h-4 text-blue-500 mt-0.5 shrink-0" />
                                            <span className="text-slate-600">Optimal title length: <strong>50-60 characters</strong></span>
                                        </div>
                                        <div className="flex items-start gap-2">
                                            <Info className="w-4 h-4 text-blue-500 mt-0.5 shrink-0" />
                                            <span className="text-slate-600">Keyword in first 30 chars = <strong>+15% CTR</strong></span>
                                        </div>
                                        <div className="flex items-start gap-2">
                                            <Info className="w-4 h-4 text-blue-500 mt-0.5 shrink-0" />
                                            <span className="text-slate-600">Year reference (2025) adds <strong>+15% relevance</strong></span>
                                        </div>
                                    </div>
                                </div>

                            </div>
                        )}
                    </div>
                </div>
            </div>
        </main>
    );
}
