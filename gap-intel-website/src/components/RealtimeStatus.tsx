"use client";

import { useEffect, useState } from "react";
import { createClient } from "@supabase/supabase-js";
import { Loader2, CheckCircle, XCircle, Clock, Sparkles, Search, FileText, Eye } from "lucide-react";

// Initialize Supabase client for realtime
const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

interface RealtimeStatusProps {
    accessKey: string;
    channelName: string;
    initialStatus: string;
    initialProgress?: number;
    initialPhase?: string;
}

// Analysis phases with their icons and descriptions
const PHASES = [
    { key: "initializing", label: "Initializing", icon: Clock, progress: 10 },
    { key: "fetching_videos", label: "Fetching Videos", icon: Eye, progress: 25 },
    { key: "analyzing_comments", label: "Analyzing Comments", icon: Search, progress: 45 },
    { key: "finding_gaps", label: "Finding Gaps", icon: Sparkles, progress: 65 },
    { key: "generating_report", label: "Generating Report", icon: FileText, progress: 85 },
    { key: "complete", label: "Complete", icon: CheckCircle, progress: 100 },
];

export default function RealtimeStatus({
    accessKey,
    channelName,
    initialStatus,
    initialProgress = 0,
    initialPhase = "Queued"
}: RealtimeStatusProps) {
    const [status, setStatus] = useState(initialStatus);
    const [progress, setProgress] = useState(initialProgress);
    const [phase, setPhase] = useState(initialPhase);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        // Subscribe to realtime changes
        const channel = supabase
            .channel(`report-${accessKey}`)
            .on(
                "postgres_changes",
                {
                    event: "UPDATE",
                    schema: "public",
                    table: "user_reports",
                    filter: `access_key=eq.${accessKey}`,
                },
                (payload) => {
                    console.log("Realtime update:", payload.new);
                    const newData = payload.new as {
                        status: string;
                        progress_percentage?: number;
                        current_phase?: string;
                    };

                    setStatus(newData.status);
                    if (newData.progress_percentage !== undefined) {
                        setProgress(newData.progress_percentage);
                    }
                    if (newData.current_phase) {
                        setPhase(newData.current_phase);
                    }

                    // Auto-refresh page when completed
                    if (newData.status === "completed") {
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    }
                }
            )
            .subscribe((status) => {
                setIsConnected(status === "SUBSCRIBED");
                console.log("Supabase Realtime status:", status);
            });

        return () => {
            supabase.removeChannel(channel);
        };
    }, [accessKey]);

    // Get current phase info
    const currentPhaseInfo = PHASES.find(p =>
        phase?.toLowerCase().includes(p.key.replace("_", " ")) ||
        phase?.toLowerCase().includes(p.key)
    ) || PHASES[0];

    if (status === "failed") {
        return (
            <div className="bg-white rounded-[32px] shadow-xl border border-slate-100 p-12 text-center">
                <div className="w-20 h-20 rounded-full bg-red-50 flex items-center justify-center mx-auto mb-6">
                    <XCircle className="w-10 h-10 text-red-500" />
                </div>
                <h1 className="text-2xl font-bold text-slate-900 mb-4">Analysis Failed</h1>
                <p className="text-slate-500 mb-8">Something went wrong during the analysis.</p>
                <a href="/dashboard" className="text-blue-600 hover:underline">
                    Return to Dashboard
                </a>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-[32px] shadow-xl border border-slate-100 p-12">
            {/* Spinner */}
            <div className="relative w-24 h-24 mx-auto mb-8">
                <div className="w-full h-full border-4 border-slate-100 rounded-full"></div>
                <div
                    className="absolute top-0 left-0 w-full h-full border-4 border-t-blue-500 border-r-blue-500 rounded-full animate-spin"
                    style={{
                        clipPath: `polygon(0 0, 100% 0, 100% 100%, 0 100%)`,
                    }}
                ></div>
                <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-2xl font-bold text-slate-900">{progress}%</span>
                </div>
            </div>

            {/* Status */}
            <h1 className="text-3xl font-serif font-medium text-slate-900 mb-4 text-center">
                Analyzing Content
            </h1>
            <p className="text-slate-500 mb-8 text-center">
                Our AI is watching videos, reading comments, and finding gaps for{" "}
                <strong className="text-slate-900">@{channelName}</strong>.
            </p>

            {/* Progress Bar */}
            <div className="mb-8">
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-500 ease-out"
                        style={{ width: `${progress}%` }}
                    ></div>
                </div>
            </div>

            {/* Current Phase */}
            <div className="bg-slate-50 rounded-2xl p-4 mb-6">
                <div className="flex items-center justify-center gap-3">
                    <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                    <span className="text-sm font-medium text-slate-700">
                        {phase || "Processing..."}
                    </span>
                </div>
            </div>

            {/* Phase Steps */}
            <div className="grid grid-cols-5 gap-2 mb-6">
                {PHASES.slice(0, 5).map((p, i) => {
                    const isActive = progress >= p.progress;
                    const isCurrent = progress >= p.progress && (PHASES[i + 1] ? progress < PHASES[i + 1].progress : true);
                    return (
                        <div
                            key={p.key}
                            className={`flex flex-col items-center gap-1 transition-opacity ${isActive ? "opacity-100" : "opacity-30"
                                }`}
                        >
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${isCurrent ? "bg-blue-500 text-white" : isActive ? "bg-green-500 text-white" : "bg-slate-200 text-slate-400"
                                }`}>
                                <p.icon className="w-4 h-4" />
                            </div>
                            <span className="text-xs text-slate-500 text-center leading-tight">{p.label}</span>
                        </div>
                    );
                })}
            </div>

            {/* Realtime Indicator */}
            <div className="flex items-center justify-center gap-2 text-xs text-slate-400">
                <div className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-500" : "bg-yellow-500"} animate-pulse`}></div>
                {isConnected ? "Live updates enabled" : "Connecting..."}
            </div>
        </div>
    );
}
