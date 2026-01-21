"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import Navbar from "@/components/Navbar";
import {
    Youtube, Link2, Unlink, Loader2, CheckCircle, AlertCircle,
    BarChart3, TrendingUp, Shield, ArrowRight, Sparkles, Lock
} from "lucide-react";
import { motion } from "framer-motion";
import Link from "next/link";
import ChannelAnalytics from "@/components/ChannelAnalytics";

interface ConnectionStatus {
    status: "connected" | "not_connected";
    channel_id?: string;
    expires_at?: string;
    scopes?: string[];
}

interface TrainingStats {
    total_samples: number;
    unique_channels: number;
    unique_videos: number;
    avg_ctr: number;
    can_train_global: boolean;
}

interface ModelStats {
    training_data: TrainingStats;
    global_model_exists: boolean;
    can_train: boolean;
}

const FeatureCard = ({ icon: Icon, title, description, color }: any) => (
    <motion.div
        whileHover={{ y: -5 }}
        className="p-6 bg-white rounded-2xl border border-slate-100 shadow-lg"
    >
        <div className={`w-12 h-12 rounded-xl ${color} flex items-center justify-center mb-4`}>
            <Icon className="w-6 h-6 text-white" />
        </div>
        <h3 className="text-lg font-bold text-slate-900 mb-2">{title}</h3>
        <p className="text-sm text-slate-500 leading-relaxed">{description}</p>
    </motion.div>
);

// Component that uses useSearchParams - must be wrapped in Suspense
function SearchParamsHandler({
    setSuccessMessage,
    setError
}: {
    setSuccessMessage: (msg: string | null) => void;
    setError: (msg: string | null) => void;
}) {
    const searchParams = useSearchParams();

    useEffect(() => {
        const status = searchParams.get("status");
        const message = searchParams.get("message");

        if (status === "success") {
            setSuccessMessage("YouTube Analytics connected successfully!");
            window.history.replaceState({}, "", "/dashboard/connect-analytics");
        } else if (status === "error") {
            setError(message || "Failed to connect YouTube Analytics");
            window.history.replaceState({}, "", "/dashboard/connect-analytics");
        }
    }, [searchParams, setSuccessMessage, setError]);

    return null;
}

function ConnectAnalyticsContent() {
    const { user, loading: authLoading } = useAuth();
    const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus | null>(null);
    const [modelStats, setModelStats] = useState<ModelStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [connecting, setConnecting] = useState(false);
    const [disconnecting, setDisconnecting] = useState(false);
    const [collecting, setCollecting] = useState(false);
    const [collectionResult, setCollectionResult] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);


    const fetchStatus = async () => {
        if (!user) return;

        try {
            const [statusRes, statsRes] = await Promise.all([
                fetch(`/api/youtube-analytics/status?user_id=${user.id}`),
                fetch(`/api/ctr-model/stats`)
            ]);

            if (statusRes.ok) {
                const data = await statusRes.json();
                setConnectionStatus(data);
            }

            if (statsRes.ok) {
                const data = await statsRes.json();
                setModelStats(data);
            }
        } catch (err) {
            console.error("Error fetching status:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (!authLoading && user) {
            fetchStatus();
        } else if (!authLoading) {
            setLoading(false);
        }
    }, [user, authLoading]);

    const handleConnect = async () => {
        if (!user) return;
        setConnecting(true);
        setError(null);

        try {
            const res = await fetch(`/api/youtube-analytics/authorize?user_id=${user.id}`);
            const data = await res.json();

            if (data.authorization_url) {
                // Redirect to Google OAuth
                window.location.href = data.authorization_url;
            } else {
                setError("Failed to generate authorization URL");
            }
        } catch (err) {
            setError("Failed to start connection process");
        } finally {
            setConnecting(false);
        }
    };

    const handleDisconnect = async () => {
        if (!user) return;
        if (!confirm("Are you sure you want to disconnect YouTube Analytics?")) return;

        setDisconnecting(true);
        setError(null);

        try {
            await fetch(`/api/youtube-analytics/disconnect?user_id=${user.id}`, {
                method: "DELETE"
            });
            setConnectionStatus({ status: "not_connected" });
            setSuccessMessage("YouTube Analytics disconnected");
        } catch (err) {
            setError("Failed to disconnect");
        } finally {
            setDisconnecting(false);
        }
    };

    const handleCollectData = async () => {
        if (!user) return;
        setCollecting(true);
        setError(null);
        setCollectionResult(null);

        try {
            const res = await fetch(`/api/youtube-analytics/collect?user_id=${user.id}`, {
                method: "POST"
            });
            const data = await res.json();

            if (data.status === "success" || data.status === "partial") {
                setCollectionResult(data.result);
                setSuccessMessage(`Collected CTR data for ${data.result.videos_collected} videos!`);
                // Refresh stats
                await fetchStatus();
            } else {
                setError(data.result?.errors?.[0] || "Data collection failed");
            }
        } catch (err) {
            setError("Failed to collect CTR data");
        } finally {
            setCollecting(false);
        }
    };

    if (authLoading || loading) {
        return (
            <div className="min-h-screen bg-[#FAFAFA]">
                <Navbar />
                <div className="pt-32 flex items-center justify-center">
                    <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
                </div>
            </div>
        );
    }

    if (!user) {
        return (
            <div className="min-h-screen bg-[#FAFAFA]">
                <Navbar />
                <div className="pt-32 flex flex-col items-center justify-center">
                    <Lock className="w-16 h-16 text-slate-300 mb-4" />
                    <h2 className="text-2xl font-bold text-slate-900 mb-2">Sign In Required</h2>
                    <p className="text-slate-500 mb-6">Please sign in to access this feature.</p>
                    <Link href="/login">
                        <button className="px-6 py-3 bg-slate-900 text-white rounded-full font-medium">
                            Sign In
                        </button>
                    </Link>
                </div>
            </div>
        );
    }

    const isConnected = connectionStatus?.status === "connected";

    return (
        <div className="min-h-screen bg-[#FAFAFA] text-slate-900">
            <Navbar />

            {/* Background */}
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-[radial-gradient(circle_at_center,_var(--color-brand-light)_0%,_transparent_70%)] opacity-30 blur-[100px]" />
            </div>

            <main className="pt-32 pb-20 px-6 relative z-10">
                <div className="max-w-4xl mx-auto">
                    {/* Header */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-center mb-12"
                    >
                        <div className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-red-500/10 to-orange-500/10 rounded-full text-red-600 font-medium text-sm mb-6">
                            <Youtube className="w-4 h-4" />
                            Premium Feature
                        </div>

                        <h1 className="text-4xl md:text-5xl font-serif font-medium text-slate-900 mb-4">
                            Connect YouTube Analytics
                        </h1>
                        <p className="text-lg text-slate-500 max-w-2xl mx-auto">
                            Enable ML-powered CTR predictions by sharing your channel analytics.
                            Your data helps train personalized thumbnail optimization models.
                        </p>
                    </motion.div>

                    {/* Status Messages */}
                    {successMessage && (
                        <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="mb-8 p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center gap-3"
                        >
                            <CheckCircle className="w-5 h-5 text-emerald-600" />
                            <span className="text-emerald-700 font-medium">{successMessage}</span>
                            <button
                                onClick={() => setSuccessMessage(null)}
                                className="ml-auto text-emerald-600 hover:text-emerald-800"
                            >
                                ×
                            </button>
                        </motion.div>
                    )}

                    {error && (
                        <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="mb-8 p-4 bg-red-50 border border-red-200 rounded-2xl flex items-center gap-3"
                        >
                            <AlertCircle className="w-5 h-5 text-red-600" />
                            <span className="text-red-700 font-medium">{error}</span>
                            <button
                                onClick={() => setError(null)}
                                className="ml-auto text-red-600 hover:text-red-800"
                            >
                                ×
                            </button>
                        </motion.div>
                    )}

                    {/* Connection Card */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="bg-white rounded-3xl border border-slate-100 shadow-xl overflow-hidden mb-12"
                    >
                        <div className="p-8 border-b border-slate-100 bg-gradient-to-r from-red-50 to-orange-50">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center shadow-lg">
                                        <Youtube className="w-8 h-8 text-white" />
                                    </div>
                                    <div>
                                        <h2 className="text-2xl font-bold text-slate-900">YouTube Analytics</h2>
                                        <div className="flex items-center gap-2 mt-1">
                                            <div className={`w-2 h-2 rounded-full ${isConnected ? "bg-emerald-500" : "bg-slate-300"}`} />
                                            <span className={`text-sm font-medium ${isConnected ? "text-emerald-600" : "text-slate-500"}`}>
                                                {isConnected ? "Connected" : "Not Connected"}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                {isConnected ? (
                                    <button
                                        onClick={handleDisconnect}
                                        disabled={disconnecting}
                                        className="px-6 py-3 bg-white border border-red-200 text-red-600 rounded-full font-medium hover:bg-red-50 transition flex items-center gap-2"
                                    >
                                        {disconnecting ? (
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                        ) : (
                                            <Unlink className="w-4 h-4" />
                                        )}
                                        Disconnect
                                    </button>
                                ) : (
                                    <button
                                        onClick={handleConnect}
                                        disabled={connecting}
                                        className="px-6 py-3 bg-gradient-to-r from-red-500 to-orange-500 text-white rounded-full font-medium hover:shadow-lg transition flex items-center gap-2"
                                    >
                                        {connecting ? (
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                        ) : (
                                            <Link2 className="w-4 h-4" />
                                        )}
                                        Connect Analytics
                                    </button>
                                )}
                            </div>
                        </div>

                        <div className="p-8">
                            {isConnected ? (
                                <div className="space-y-6">
                                    {/* Connected Info */}
                                    <div className="grid grid-cols-2 gap-6">
                                        <div className="p-4 bg-slate-50 rounded-xl">
                                            <div className="text-sm text-slate-500 mb-1">Channel ID</div>
                                            <div className="font-mono text-sm text-slate-700">
                                                {connectionStatus.channel_id || "Unknown"}
                                            </div>
                                        </div>
                                        <div className="p-4 bg-slate-50 rounded-xl">
                                            <div className="text-sm text-slate-500 mb-1">Data Permissions</div>
                                            <div className="text-sm text-slate-700">
                                                Analytics (Read-Only)
                                            </div>
                                        </div>
                                    </div>

                                    {/* Collect Data Button */}
                                    <div className="pt-4 border-t border-slate-100">
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <h3 className="font-bold text-slate-900">Sync CTR Data</h3>
                                                <p className="text-sm text-slate-500">
                                                    Collect thumbnail CTR data from your videos for model training
                                                </p>
                                            </div>
                                            <button
                                                onClick={handleCollectData}
                                                disabled={collecting}
                                                className="px-6 py-3 bg-slate-900 text-white rounded-full font-medium hover:bg-slate-800 transition flex items-center gap-2"
                                            >
                                                {collecting ? (
                                                    <>
                                                        <Loader2 className="w-4 h-4 animate-spin" />
                                                        Collecting...
                                                    </>
                                                ) : (
                                                    <>
                                                        <BarChart3 className="w-4 h-4" />
                                                        Sync Now
                                                    </>
                                                )}
                                            </button>
                                        </div>

                                        {collectionResult && (
                                            <motion.div
                                                initial={{ opacity: 0 }}
                                                animate={{ opacity: 1 }}
                                                className="mt-4 p-4 bg-blue-50 rounded-xl"
                                            >
                                                <div className="grid grid-cols-3 gap-4 text-center">
                                                    <div>
                                                        <div className="text-2xl font-bold text-blue-600">
                                                            {collectionResult.videos_processed}
                                                        </div>
                                                        <div className="text-xs text-blue-700">Processed</div>
                                                    </div>
                                                    <div>
                                                        <div className="text-2xl font-bold text-emerald-600">
                                                            {collectionResult.videos_collected}
                                                        </div>
                                                        <div className="text-xs text-emerald-700">Collected</div>
                                                    </div>
                                                    <div>
                                                        <div className="text-2xl font-bold text-slate-600">
                                                            {collectionResult.duration_seconds?.toFixed(1)}s
                                                        </div>
                                                        <div className="text-xs text-slate-500">Duration</div>
                                                    </div>
                                                </div>
                                            </motion.div>
                                        )}
                                    </div>
                                </div>
                            ) : (
                                // Not Connected - Show Benefits
                                <div className="text-center py-8">
                                    <div className="w-20 h-20 mx-auto bg-slate-100 rounded-full flex items-center justify-center mb-6">
                                        <Youtube className="w-10 h-10 text-slate-400" />
                                    </div>
                                    <h3 className="text-xl font-bold text-slate-900 mb-2">
                                        Unlock ML-Powered CTR Predictions
                                    </h3>
                                    <p className="text-slate-500 max-w-md mx-auto mb-6">
                                        Connect your YouTube Analytics to enable personalized thumbnail optimization
                                        based on your actual channel performance data.
                                    </p>
                                    <button
                                        onClick={handleConnect}
                                        disabled={connecting}
                                        className="px-8 py-4 bg-gradient-to-r from-red-500 to-orange-500 text-white rounded-full font-bold text-lg hover:shadow-xl transition flex items-center gap-2 mx-auto"
                                    >
                                        {connecting ? (
                                            <Loader2 className="w-5 h-5 animate-spin" />
                                        ) : (
                                            <>
                                                Connect YouTube Analytics
                                                <ArrowRight className="w-5 h-5" />
                                            </>
                                        )}
                                    </button>
                                </div>
                            )}
                        </div>
                    </motion.div>

                    {/* Channel Analytics Dashboard */}
                    {isConnected && user && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.15 }}
                            className="mb-12"
                        >
                            <ChannelAnalytics userId={user.id} />
                        </motion.div>
                    )}

                    {/* Model Stats (if connected and has data) */}
                    {modelStats && modelStats.training_data && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                            className="bg-white rounded-3xl border border-slate-100 shadow-xl p-8 mb-12"
                        >
                            <h3 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
                                <Sparkles className="w-5 h-5 text-amber-500" />
                                CTR Prediction Model Status
                            </h3>

                            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                                <div className="text-center p-4 bg-slate-50 rounded-xl">
                                    <div className="text-3xl font-bold text-slate-900">
                                        {modelStats.training_data.total_samples?.toLocaleString() || 0}
                                    </div>
                                    <div className="text-sm text-slate-500">Training Samples</div>
                                </div>
                                <div className="text-center p-4 bg-slate-50 rounded-xl">
                                    <div className="text-3xl font-bold text-slate-900">
                                        {modelStats.training_data.unique_channels || 0}
                                    </div>
                                    <div className="text-sm text-slate-500">Channels</div>
                                </div>
                                <div className="text-center p-4 bg-slate-50 rounded-xl">
                                    <div className="text-3xl font-bold text-slate-900">
                                        {modelStats.training_data.avg_ctr?.toFixed(1) || 0}%
                                    </div>
                                    <div className="text-sm text-slate-500">Avg CTR</div>
                                </div>
                                <div className="text-center p-4 bg-slate-50 rounded-xl">
                                    <div className={`text-3xl font-bold ${modelStats.global_model_exists ? "text-emerald-600" : "text-slate-400"}`}>
                                        {modelStats.global_model_exists ? "Active" : "Pending"}
                                    </div>
                                    <div className="text-sm text-slate-500">ML Model</div>
                                </div>
                            </div>

                            {!modelStats.global_model_exists && modelStats.training_data.total_samples < 1000 && (
                                <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-xl">
                                    <div className="flex items-start gap-3">
                                        <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5" />
                                        <div>
                                            <p className="text-amber-800 font-medium">
                                                {1000 - (modelStats.training_data.total_samples || 0)} more samples needed
                                            </p>
                                            <p className="text-sm text-amber-700 mt-1">
                                                The ML model requires at least 1,000 training samples to be effective.
                                                Connect more channels or wait for more data to be collected.
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </motion.div>
                    )}

                    {/* Benefits Grid */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                    >
                        <h3 className="text-2xl font-serif font-medium text-slate-900 text-center mb-8">
                            What You Get
                        </h3>
                        <div className="grid md:grid-cols-3 gap-6">
                            <FeatureCard
                                icon={TrendingUp}
                                title="85% CTR Accuracy"
                                description="ML-powered predictions trained on real CTR data, up from 60% with rule-based estimates."
                                color="bg-gradient-to-br from-blue-500 to-indigo-500"
                            />
                            <FeatureCard
                                icon={Sparkles}
                                title="Personalized Insights"
                                description="Get thumbnail recommendations tailored to your specific audience and niche."
                                color="bg-gradient-to-br from-purple-500 to-pink-500"
                            />
                            <FeatureCard
                                icon={Shield}
                                title="Privacy Protected"
                                description="Your data is encrypted and used only to improve your predictions. Delete anytime."
                                color="bg-gradient-to-br from-emerald-500 to-teal-500"
                            />
                        </div>
                    </motion.div>

                    {/* Privacy Notice */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.4 }}
                        className="mt-12 text-center text-sm text-slate-500"
                    >
                        <p>
                            We only access read-only analytics data. Your CTR data is aggregated and anonymized
                            for ML training. You can disconnect and delete your data at any time.
                        </p>
                    </motion.div>
                </div>
            </main>
        </div>
    );
}

// Default export with Suspense wrapper for useSearchParams
export default function ConnectAnalyticsPage() {
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    return (
        <Suspense fallback={
            <div className="min-h-screen bg-[#FAFAFA]">
                <Navbar />
                <div className="pt-32 flex items-center justify-center">
                    <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
                </div>
            </div>
        }>
            <SearchParamsHandler
                setSuccessMessage={setSuccessMessage}
                setError={setError}
            />
            <ConnectAnalyticsContent />
        </Suspense>
    );
}
