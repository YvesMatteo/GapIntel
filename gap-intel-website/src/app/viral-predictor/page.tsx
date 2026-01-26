"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import {
  Sparkles, TrendingUp, AlertCircle, Zap, Target,
  BarChart3, Lightbulb, CheckCircle, Info, RefreshCw,
  ChevronRight, Copy, Check, Image as ImageIcon, Brain,
  Eye, MousePointerClick, Clock, Shield, AlertTriangle
} from "lucide-react";
import ThumbnailUpload from "@/components/ThumbnailUpload";

const API_URL = "https://thriving-presence-production-ca4a.up.railway.app";

// Types matching the backend response
interface ThumbnailAnalysis {
  score: number;
  ctr_impact: string;
  visual_contrast: number;
  face_presence: number;
  emotion_intensity: number;
  text_readability: number;
  color_vibrancy: number;
  alignment_with_content: number;
  analysis_notes: string;
}

interface HookAnalysis {
  score: number;
  avd_impact: string;
  information_gap: number;
  emotional_authenticity: number;
  open_loop_clarity: number;
  personal_relevance: number;
  value_proposition: number;
  processing_ease: number;
  psychological_triggers: string[];
  analysis_notes: string;
}

interface TitleAnalysis {
  score: number;
  ctr_impact: string;
  specificity: number;
  number_inclusion: number;
  curiosity_words: number;
  personal_pronoun: number;
  keyword_relevance: number;
  title_hook_coherence: number;
  analysis_notes: string;
}

interface AlternativeTitle {
  title: string;
  hook_type: string;
  expected_ctr_boost: string;
  rationale: string;
}

interface ViralAnalysisResult {
  title: string;
  niche: string;
  niche_confidence: number;
  channel_size: string;
  channel_multiplier: number;
  thumbnail: ThumbnailAnalysis | null;
  hook: HookAnalysis;
  title_analysis: TitleAnalysis;
  predicted_views: number;
  confidence_interval: string;
  view_range_low: number;
  view_range_high: number;
  predicted_ctr: string;
  predicted_avd: string;
  phase_1_success_index: number;
  thumbnail_recommendations: string[];
  hook_recommendations: string[];
  title_recommendations: string[];
  strategy_recommendations: string[];
  alternative_titles: AlternativeTitle[];
  vs_niche_average: string;
  competitive_positioning: string;
  click_to_content_mismatch_risk: string;
  saturation_risk: string;
  algorithmic_risk: string;
  overall_viral_score: number;
  analysis_summary: string;
}

const CHANNEL_SIZES = [
  { value: "nano", label: "Nano (0-10K subs)" },
  { value: "micro", label: "Micro (10K-100K subs)" },
  { value: "small", label: "Small (100K-1M subs)" },
  { value: "large", label: "Large (1M-10M subs)" },
  { value: "mega", label: "Mega (10M+ subs)" },
];

const NICHES = [
  { value: "gaming", label: "Gaming" },
  { value: "education", label: "Education" },
  { value: "entertainment", label: "Entertainment" },
  { value: "tech", label: "Tech" },
  { value: "review", label: "Review" },
  { value: "finance", label: "Finance" },
  { value: "vlog", label: "Vlog / Lifestyle" },
];

export default function ViralPredictorPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <ViralPredictorContent />
    </Suspense>
  );
}

function LoadingState() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0a0a0f]">
      <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

function ViralPredictorContent() {
  const [title, setTitle] = useState("");
  const [hook, setHook] = useState("");
  const [channelSize, setChannelSize] = useState("micro");
  const [niche, setNiche] = useState("entertainment");
  const [thumbnail, setThumbnail] = useState<File | null>(null);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<ViralAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const handleAnalyze = async () => {
    if (!title || title.length < 3) {
      setError("Please enter a title (at least 3 characters)");
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("title", title);
      formData.append("hook", hook || "");
      formData.append("niche", niche);
      formData.append("channel_size", channelSize);

      if (thumbnail) {
        formData.append("thumbnail", thumbnail);
      }

      const response = await fetch(`${API_URL}/api/v2/predict-viral`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Analysis failed (${response.status})`);
      }

      const data: ViralAnalysisResult = await response.json();
      setResult(data);
    } catch (err) {
      console.error("Analysis failed:", err);
      setError(err instanceof Error ? err.message : "Analysis failed. Please try again.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleCopyTitle = (altTitle: string, index: number) => {
    navigator.clipboard.writeText(altTitle);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const getScoreColor = (score: number) => {
    if (score >= 7) return "text-green-400";
    if (score >= 5) return "text-yellow-400";
    if (score >= 3) return "text-orange-400";
    return "text-red-400";
  };

  const getViralScoreLabel = (score: number) => {
    if (score >= 80) return "Viral Potential";
    if (score >= 65) return "Strong Potential";
    if (score >= 50) return "Moderate Potential";
    if (score >= 30) return "Needs Work";
    return "Low Potential";
  };

  const getRiskColor = (risk: string) => {
    if (risk === "Low") return "text-green-400 bg-green-500/10";
    if (risk === "Medium") return "text-yellow-400 bg-yellow-500/10";
    return "text-red-400 bg-red-500/10";
  };

  const formatViews = (views: number) => {
    if (views >= 1000000) return `${(views / 1000000).toFixed(1)}M`;
    if (views >= 1000) return `${(views / 1000).toFixed(1)}K`;
    return views.toString();
  };

  return (
    <main className="min-h-screen bg-[#0a0a0f] pt-24 pb-20">
      <div className="max-w-7xl mx-auto px-6">
        {/* Header */}
        <div className="mb-12 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-purple-500/10 text-purple-400 text-sm font-medium mb-4 border border-purple-500/20">
            <Brain className="w-4 h-4" /> Gemini 2.5 Flash Powered
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Viral Title Predictor
          </h1>
          <p className="text-lg text-white/60 max-w-2xl mx-auto">
            AI-powered analysis using psychological triggers, CTR patterns, and the YouTube algorithm.
            Upload a thumbnail for 25% more accurate predictions.
          </p>
        </div>

        <div className="grid lg:grid-cols-5 gap-8 items-start">
          {/* Input Panel */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6 sticky top-24">
              <div className="space-y-5">
                {/* Thumbnail Upload */}
                <ThumbnailUpload
                  onFileSelect={setThumbnail}
                  disabled={isAnalyzing}
                />

                {/* Title Input */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-white/90">
                      Video Title
                    </label>
                    <span className={`text-xs font-medium ${title.length >= 50 && title.length <= 70
                      ? "text-green-400"
                      : title.length > 70
                        ? "text-red-400"
                        : "text-white/40"
                      }`}>
                      {title.length}/70 chars
                      {title.length >= 50 && title.length <= 70 && (
                        <Check className="w-3 h-3 text-green-400 ml-1 inline" />
                      )}
                    </span>
                  </div>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    disabled={isAnalyzing}
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition disabled:opacity-50"
                    placeholder="Enter your video title..."
                  />
                </div>

                {/* Opening Hook */}
                <div>
                  <label className="block text-sm font-medium text-white/90 mb-2">
                    Opening Hook (First Sentence)
                    <span className="text-white/50 ml-2 font-normal">(Optional)</span>
                  </label>
                  <textarea
                    rows={3}
                    value={hook}
                    onChange={(e) => setHook(e.target.value)}
                    disabled={isAnalyzing}
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition resize-none disabled:opacity-50"
                    placeholder="What's the first line of your video?"
                  />
                </div>

                {/* Channel Size & Niche */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-white/90 mb-2">
                      Channel Size
                    </label>
                    <select
                      value={channelSize}
                      onChange={(e) => setChannelSize(e.target.value)}
                      disabled={isAnalyzing}
                      className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition appearance-none disabled:opacity-50"
                    >
                      {CHANNEL_SIZES.map((size) => (
                        <option key={size.value} value={size.value} className="bg-[#1a1a2e]">
                          {size.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-white/90 mb-2">
                      Niche
                    </label>
                    <select
                      value={niche}
                      onChange={(e) => setNiche(e.target.value)}
                      disabled={isAnalyzing}
                      className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition appearance-none disabled:opacity-50"
                    >
                      {NICHES.map((n) => (
                        <option key={n.value} value={n.value} className="bg-[#1a1a2e]">
                          {n.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Analyze Button */}
                <button
                  onClick={handleAnalyze}
                  disabled={isAnalyzing || !title || title.length < 3}
                  className="w-full py-4 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold text-lg hover:from-purple-500 hover:to-pink-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isAnalyzing ? (
                    <>
                      <RefreshCw className="w-5 h-5 animate-spin" />
                      Analyzing with Gemini...
                    </>
                  ) : (
                    <>
                      <Zap className="w-5 h-5" />
                      Analyze Viral Potential
                    </>
                  )}
                </button>

                {/* Error */}
                {error && (
                  <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-red-400 text-sm flex items-start gap-2">
                    <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                    {error}
                  </div>
                )}

                {/* Pro Tips */}
                <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                  <div className="flex items-start gap-2">
                    <Lightbulb className="w-4 h-4 text-yellow-400 mt-0.5 shrink-0" />
                    <p className="text-xs text-white/60">
                      <strong className="text-white/80">Pro Tip:</strong> Upload a thumbnail for
                      multi-modal AI analysis. Thumbnails account for 25-30% of view prediction accuracy.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-3 space-y-6">
            {/* Empty State */}
            {!result && !isAnalyzing && (
              <div className="bg-white/5 border border-white/10 rounded-2xl p-12 text-center flex flex-col items-center justify-center min-h-[400px]">
                <div className="w-20 h-20 bg-white/5 rounded-full flex items-center justify-center text-white/30 mb-6">
                  <Brain className="w-10 h-10" />
                </div>
                <h3 className="text-xl font-medium text-white mb-2">Ready to Analyze</h3>
                <p className="text-white/50 max-w-sm">
                  Enter your video title and click "Analyze" for AI-powered viral potential prediction.
                </p>
              </div>
            )}

            {/* Loading State */}
            {isAnalyzing && (
              <div className="bg-white/5 border border-white/10 rounded-2xl p-12 text-center flex flex-col items-center justify-center min-h-[400px]">
                <div className="w-20 h-20 bg-purple-500/10 rounded-full flex items-center justify-center mb-6">
                  <Brain className="w-10 h-10 text-purple-400 animate-pulse" />
                </div>
                <h3 className="text-xl font-medium text-white mb-2">Gemini is Analyzing...</h3>
                <p className="text-white/50 max-w-sm mb-4">
                  Evaluating psychological triggers, CTR patterns, and content alignment.
                </p>
                <div className="flex items-center gap-2 text-sm text-white/40">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  This takes 2-5 seconds
                </div>
              </div>
            )}

            {/* Results */}
            {result && !isAnalyzing && (
              <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
                {/* Viral Score Hero */}
                <div className="bg-gradient-to-br from-[#1a1a2e] to-[#0f0f1a] rounded-2xl p-8 text-white relative overflow-hidden border border-white/10">
                  <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/10 blur-3xl rounded-full -mr-32 -mt-32" />

                  <div className="relative z-10 grid md:grid-cols-2 gap-8 items-center">
                    <div className="text-center md:text-left">
                      <p className="text-white/60 text-sm font-medium uppercase tracking-wider mb-2">
                        Overall Viral Score
                      </p>
                      <div className="flex items-baseline gap-2 justify-center md:justify-start">
                        <span className="text-7xl font-bold">{result.overall_viral_score}</span>
                        <span className="text-3xl text-white/40">/100</span>
                      </div>
                      <p className="text-xl font-medium mt-2 text-purple-400">
                        {getViralScoreLabel(result.overall_viral_score)}
                      </p>
                      <p className="text-sm text-white/50 mt-2">
                        Confidence: {result.confidence_interval}
                      </p>
                    </div>

                    <div className="space-y-4">
                      {/* View Prediction */}
                      <div className="bg-white/5 backdrop-blur-sm rounded-xl p-5 border border-white/10">
                        <div className="flex items-center gap-2 mb-2">
                          <Eye className="w-5 h-5 text-green-400" />
                          <span className="font-medium text-white/90">Predicted Views</span>
                        </div>
                        <div className="text-3xl font-bold text-green-400">
                          {formatViews(result.view_range_low)} - {formatViews(result.view_range_high)}
                        </div>
                        <p className="text-sm text-white/50 mt-1">
                          Expected: {formatViews(result.predicted_views)}
                        </p>
                      </div>

                      {/* Key Metrics */}
                      <div className="grid grid-cols-2 gap-3">
                        <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                          <p className="text-xs text-white/50 mb-1">Predicted CTR</p>
                          <p className="text-xl font-bold text-white">{result.predicted_ctr}</p>
                        </div>
                        <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                          <p className="text-xs text-white/50 mb-1">Predicted AVD</p>
                          <p className="text-xl font-bold text-white">{result.predicted_avd}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Component Analysis */}
                <div className="grid md:grid-cols-3 gap-4">
                  {/* Thumbnail Score */}
                  <div className="bg-white/5 rounded-xl p-5 border border-white/10">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center">
                        <ImageIcon className="w-4 h-4 text-purple-400" />
                      </div>
                      <span className="font-medium text-white/90">Thumbnail</span>
                    </div>
                    {result.thumbnail ? (
                      <>
                        <div className="flex items-baseline gap-2 mb-2">
                          <span className={`text-3xl font-bold ${getScoreColor(result.thumbnail.score)}`}>
                            {result.thumbnail.score.toFixed(1)}
                          </span>
                          <span className="text-white/40">/10</span>
                        </div>
                        <p className="text-sm text-green-400 mb-3">CTR Impact: {result.thumbnail.ctr_impact}</p>
                        <div className="space-y-2 text-xs">
                          <ScoreBar label="Contrast" value={result.thumbnail.visual_contrast} />
                          <ScoreBar label="Face" value={result.thumbnail.face_presence} />
                          <ScoreBar label="Emotion" value={result.thumbnail.emotion_intensity} />
                          <ScoreBar label="Text" value={result.thumbnail.text_readability} />
                        </div>
                      </>
                    ) : (
                      <div className="text-white/40 text-sm">
                        No thumbnail uploaded
                        <p className="text-xs mt-1">Upload for +25% accuracy</p>
                      </div>
                    )}
                  </div>

                  {/* Hook Score */}
                  <div className="bg-white/5 rounded-xl p-5 border border-white/10">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
                        <Sparkles className="w-4 h-4 text-blue-400" />
                      </div>
                      <span className="font-medium text-white/90">Hook</span>
                    </div>
                    <div className="flex items-baseline gap-2 mb-2">
                      <span className={`text-3xl font-bold ${getScoreColor(result.hook.score)}`}>
                        {result.hook.score.toFixed(1)}
                      </span>
                      <span className="text-white/40">/10</span>
                    </div>
                    <p className="text-sm text-green-400 mb-3">AVD Impact: {result.hook.avd_impact}</p>
                    <div className="space-y-2 text-xs">
                      <ScoreBar label="Info Gap" value={result.hook.information_gap} />
                      <ScoreBar label="Emotion" value={result.hook.emotional_authenticity} />
                      <ScoreBar label="Open Loop" value={result.hook.open_loop_clarity} />
                      <ScoreBar label="Relevance" value={result.hook.personal_relevance} />
                    </div>
                    {result.hook.psychological_triggers.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-1">
                        {result.hook.psychological_triggers.map((trigger, i) => (
                          <span key={i} className="px-2 py-0.5 bg-blue-500/20 text-blue-300 text-[10px] rounded-full">
                            {trigger}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Title Score */}
                  <div className="bg-white/5 rounded-xl p-5 border border-white/10">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center">
                        <Target className="w-4 h-4 text-green-400" />
                      </div>
                      <span className="font-medium text-white/90">Title</span>
                    </div>
                    <div className="flex items-baseline gap-2 mb-2">
                      <span className={`text-3xl font-bold ${getScoreColor(result.title_analysis.score)}`}>
                        {result.title_analysis.score.toFixed(1)}
                      </span>
                      <span className="text-white/40">/10</span>
                    </div>
                    <p className="text-sm text-green-400 mb-3">CTR Impact: {result.title_analysis.ctr_impact}</p>
                    <div className="space-y-2 text-xs">
                      <ScoreBar label="Specificity" value={result.title_analysis.specificity} />
                      <ScoreBar label="Numbers" value={result.title_analysis.number_inclusion} />
                      <ScoreBar label="Curiosity" value={result.title_analysis.curiosity_words} />
                      <ScoreBar label="Coherence" value={result.title_analysis.title_hook_coherence} />
                    </div>
                  </div>
                </div>

                {/* Recommendations */}
                <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Lightbulb className="w-5 h-5 text-yellow-400" />
                    Optimization Recommendations
                  </h3>
                  <div className="grid md:grid-cols-2 gap-4">
                    {result.thumbnail_recommendations.length > 0 && (
                      <RecommendationList
                        title="Thumbnail"
                        items={result.thumbnail_recommendations}
                        icon={<ImageIcon className="w-4 h-4" />}
                        color="purple"
                      />
                    )}
                    {result.hook_recommendations.length > 0 && (
                      <RecommendationList
                        title="Hook"
                        items={result.hook_recommendations}
                        icon={<Sparkles className="w-4 h-4" />}
                        color="blue"
                      />
                    )}
                    {result.title_recommendations.length > 0 && (
                      <RecommendationList
                        title="Title"
                        items={result.title_recommendations}
                        icon={<Target className="w-4 h-4" />}
                        color="green"
                      />
                    )}
                    {result.strategy_recommendations.length > 0 && (
                      <RecommendationList
                        title="Strategy"
                        items={result.strategy_recommendations}
                        icon={<TrendingUp className="w-4 h-4" />}
                        color="orange"
                      />
                    )}
                  </div>
                </div>

                {/* Alternative Titles */}
                {result.alternative_titles.length > 0 && (
                  <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                    <div className="flex items-center gap-3 mb-5">
                      <div className="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center">
                        <RefreshCw className="w-5 h-5 text-purple-400" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-white">Alternative Titles</h3>
                        <p className="text-sm text-white/50">AI-generated variants with different hooks</p>
                      </div>
                    </div>

                    <div className="space-y-3">
                      {result.alternative_titles.map((alt, i) => (
                        <div
                          key={i}
                          className="bg-white/5 rounded-xl p-4 border border-white/10 hover:bg-white/10 transition group"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <span className="px-2 py-0.5 bg-purple-500/20 text-purple-300 text-xs rounded-full">
                                {alt.hook_type}
                              </span>
                              <span className="text-xs text-green-400 font-medium">
                                {alt.expected_ctr_boost}
                              </span>
                            </div>
                            <button
                              onClick={() => handleCopyTitle(alt.title, i)}
                              className="opacity-0 group-hover:opacity-100 transition p-2 hover:bg-white/10 rounded-lg"
                            >
                              {copiedIndex === i ? (
                                <Check className="w-4 h-4 text-green-400" />
                              ) : (
                                <Copy className="w-4 h-4 text-white/60" />
                              )}
                            </button>
                          </div>
                          <p className="text-white font-medium">{alt.title}</p>
                          <p className="text-xs text-white/50 mt-2">{alt.rationale}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Benchmarks & Risks */}
                <div className="grid md:grid-cols-2 gap-4">
                  {/* Benchmarks */}
                  <div className="bg-white/5 rounded-xl p-5 border border-white/10">
                    <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                      <BarChart3 className="w-5 h-5 text-blue-400" />
                      Benchmark Comparison
                    </h3>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-white/60">vs Niche Average</span>
                        <span className={`font-bold ${result.vs_niche_average.startsWith("+") ? "text-green-400" : "text-red-400"
                          }`}>
                          {result.vs_niche_average}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-white/60">Competitive Position</span>
                        <span className={`font-bold ${result.competitive_positioning === "Strong"
                          ? "text-green-400"
                          : result.competitive_positioning === "Average"
                            ? "text-yellow-400"
                            : "text-red-400"
                          }`}>
                          {result.competitive_positioning}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-white/60">Phase 1 Success Index</span>
                        <span className="font-bold text-white">
                          {result.phase_1_success_index}/10
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Risk Factors */}
                  <div className="bg-white/5 rounded-xl p-5 border border-white/10">
                    <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                      <Shield className="w-5 h-5 text-orange-400" />
                      Risk Factors
                    </h3>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-white/60">Click-to-Content Mismatch</span>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getRiskColor(result.click_to_content_mismatch_risk)}`}>
                          {result.click_to_content_mismatch_risk}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-white/60">Saturation Risk</span>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getRiskColor(result.saturation_risk)}`}>
                          {result.saturation_risk}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-white/60">Algorithmic Risk</span>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getRiskColor(result.algorithmic_risk)}`}>
                          {result.algorithmic_risk}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Summary */}
                <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-xl p-6 border border-purple-500/20">
                  <h3 className="font-semibold text-white mb-2 flex items-center gap-2">
                    <Brain className="w-5 h-5 text-purple-400" />
                    AI Analysis Summary
                  </h3>
                  <p className="text-white/70">{result.analysis_summary}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

// Helper Components
function ScoreBar({ label, value }: { label: string; value: number }) {
  const getColor = (v: number) => {
    if (v >= 7) return "bg-green-500";
    if (v >= 5) return "bg-yellow-500";
    if (v >= 3) return "bg-orange-500";
    return "bg-red-500";
  };

  return (
    <div className="flex items-center gap-2">
      <span className="text-white/50 w-16 truncate">{label}</span>
      <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
        <div
          className={`h-full ${getColor(value)} rounded-full transition-all`}
          style={{ width: `${value * 10}%` }}
        />
      </div>
      <span className="text-white/70 w-6 text-right">{value.toFixed(0)}</span>
    </div>
  );
}

function RecommendationList({
  title,
  items,
  icon,
  color
}: {
  title: string;
  items: string[];
  icon: React.ReactNode;
  color: string;
}) {
  const colorClasses: Record<string, string> = {
    purple: "bg-purple-500/20 text-purple-400",
    blue: "bg-blue-500/20 text-blue-400",
    green: "bg-green-500/20 text-green-400",
    orange: "bg-orange-500/20 text-orange-400",
  };

  return (
    <div>
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-6 h-6 rounded-md flex items-center justify-center ${colorClasses[color]}`}>
          {icon}
        </div>
        <span className="text-sm font-medium text-white/80">{title}</span>
      </div>
      <ul className="space-y-1.5">
        {items.slice(0, 3).map((item, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-white/60">
            <ChevronRight className="w-4 h-4 mt-0.5 shrink-0 text-white/40" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
