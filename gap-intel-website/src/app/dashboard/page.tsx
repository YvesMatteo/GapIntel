"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import Navbar from "@/components/Navbar";
import {
    BarChart3, FileText, CreditCard, TrendingUp, Clock, CheckCircle,
    AlertCircle, Loader2, Plus, X, Search, Trash2, FolderPlus,
    MoreVertical, Key, Users, Palette, ArrowUpRight, Sparkles,
    Zap
} from "lucide-react";
import { motion } from "framer-motion";

// --- Types ---
interface Report {
    id: string;
    access_key: string;
    channel_name: string;
    channel_handle: string;
    channel_thumbnail?: string;
    status: "pending" | "processing" | "completed" | "failed";
    created_at: string;
    folder_id: string | null;
}

interface Folder {
    id: string;
    name: string;
    color: string;
    icon: string;
}

interface Subscription {
    tier: string;
    status: string;
    analyses_this_month: number;
    current_period_end: string | null;
}

// --- Animation Components ---
const FadeIn = ({ children, delay = 0, className = "" }: { children: React.ReactNode, delay?: number, className?: string }) => (
    <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-50px" }}
        transition={{ duration: 0.6, delay, ease: [0.21, 0.47, 0.32, 0.98] }}
        className={className}
    >
        {children}
    </motion.div>
);

const StatCard = ({ icon: Icon, label, value, subtext, color, onClick, delay = 0 }: any) => (
    <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5, delay }}
        whileHover={{ y: -5 }}
        onClick={onClick}
        className={`bg-white p-6 rounded-[24px] border border-slate-100 shadow-xl shadow-slate-200/50 relative overflow-hidden group ${onClick ? 'cursor-pointer' : ''}`}
    >
        <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${color} opacity-[0.08] rounded-full blur-2xl -mr-10 -mt-10 group-hover:scale-110 transition-transform duration-500`} />

        <div className="relative z-10">
            <div className="flex items-center gap-3 mb-4">
                <div className={`w-10 h-10 rounded-xl ${color.replace('from-', 'bg-').replace('to-', 'text-').split(' ')[0]} bg-opacity-10 flex items-center justify-center`}>
                    <Icon className={`w-5 h-5 ${color.replace('from-', 'text-').split(' ')[0]}`} />
                </div>
                <span className="text-sm text-slate-500 font-medium">{label}</span>
            </div>
            <div className="text-2xl font-bold text-slate-900 tracking-tight mb-1">{value}</div>
            {subtext && <div className="text-xs text-slate-500 font-medium">{subtext}</div>}
        </div>
    </motion.div>
);

export default function DashboardPage() {
    const { user, loading: authLoading } = useAuth();
    const [reports, setReports] = useState<Report[]>([]);
    const [subscription, setSubscription] = useState<Subscription | null>(null);
    const [loading, setLoading] = useState(true);

    // Create Report Modal State
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [channelInput, setChannelInput] = useState("");
    const [includeShorts, setIncludeShorts] = useState(true);
    const [verifying, setVerifying] = useState(false);
    const [channelInfo, setChannelInfo] = useState<{ title: string; subscriberCount: string; thumbnailUrl?: string } | null>(null);
    const [creating, setCreating] = useState(false);
    const [createError, setCreateError] = useState<string | null>(null);
    const [syncing, setSyncing] = useState(false);

    // Folder State
    const [folders, setFolders] = useState<Folder[]>([]);
    const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
    const [showNewFolderInput, setShowNewFolderInput] = useState(false);
    const [newFolderName, setNewFolderName] = useState("");
    const newFolderInputRef = useRef<HTMLDivElement>(null);
    const [showFolderMenu, setShowFolderMenu] = useState<string | null>(null);
    const folderMenuRef = useRef<HTMLDivElement>(null);

    // Click outside handler
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (newFolderInputRef.current && !newFolderInputRef.current.contains(event.target as Node)) {
                setShowNewFolderInput(false);
            }
            if (folderMenuRef.current && !folderMenuRef.current.contains(event.target as Node)) {
                setShowFolderMenu(null);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const fetchData = async () => {
        if (!user) return;
        try {
            const [reportsRes, foldersRes, subRes] = await Promise.all([
                fetch("/api/user/reports"),
                fetch(`/api/reports/folders?userId=${user.id}`),
                fetch("/api/user/subscription")
            ]);

            if (reportsRes.ok) setReports(await reportsRes.json());
            if (foldersRes.ok) setFolders(await foldersRes.json());
            if (subRes.ok) setSubscription(await subRes.json());
        } catch (error) {
            console.error("Error fetching dashboard data:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (!authLoading) fetchData();
    }, [user, authLoading]);

    // Computed properties
    const filteredReports = selectedFolder
        ? reports.filter(r => r.folder_id === selectedFolder)
        : reports;

    // Actions
    const handleDeleteReport = async (reportId: string) => {
        if (!confirm("Are you sure you want to delete this report?")) return;
        try {
            await fetch(`/api/reports/manage?id=${reportId}`, { method: "DELETE" });
            setReports(prev => prev.filter(r => r.id !== reportId));
        } catch (error) {
            console.error("Error deleting report:", error);
        }
    };

    const handleMoveToFolder = async (reportId: string, folderId: string | null) => {
        try {
            await fetch("/api/reports/manage", {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ reportId, folderId })
            });
            setReports(prev => prev.map(r => r.id === reportId ? { ...r, folder_id: folderId } : r));
            setShowFolderMenu(null);
        } catch (error) {
            console.error("Error moving report:", error);
        }
    };

    const handleCreateFolder = async () => {
        if (!newFolderName.trim()) return;
        try {
            const res = await fetch("/api/reports/folders", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name: newFolderName, icon: "📁", color: "blue" })
            });
            if (res.ok) {
                const newFolder = await res.json();
                setFolders(prev => [...prev, newFolder]);
                setNewFolderName("");
                setShowNewFolderInput(false);
            }
        } catch (error) {
            console.error("Error creating folder:", error);
        }
    };

    const handleSyncSubscription = async () => {
        setSyncing(true);
        try {
            await fetch("/api/user/sync-subscription", { method: "POST" });
            await fetchData(); // Refresh data
        } catch (error) {
            console.error("Error syncing subscription:", error);
        } finally {
            setSyncing(false);
        }
    };

    const verifyChannel = async () => {
        if (!channelInput) return;
        setVerifying(true);
        setChannelInfo(null);
        setCreateError(null);
        try {
            const res = await fetch(`/api/youtube/channel?query=${encodeURIComponent(channelInput)}`);
            const data = await res.json();
            if (res.ok) {
                setChannelInfo(data);
            } else {
                setCreateError(data.error || "Channel not found");
            }
        } catch (err) {
            setCreateError("Failed to verify channel");
        } finally {
            setVerifying(false);
        }
    };

    const handleCreateReport = async () => {
        if (!channelInfo) return;
        setCreating(true);
        try {
            const res = await fetch("/api/reports/create", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    channelId: channelInput, // Using input as ID/Handle locator
                    channelName: channelInfo.title,
                    channelThumbnail: channelInfo.thumbnailUrl,
                    includeShorts
                })
            });

            if (res.ok) {
                await fetchData(); // Refresh list
                setShowCreateModal(false);
                setChannelInput("");
                setChannelInfo(null);
            } else {
                const data = await res.json();
                setCreateError(data.error || "Failed to create report");
            }
        } catch (err) {
            setCreateError("An unexpected error occurred");
        } finally {
            setCreating(false);
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case "completed": return <CheckCircle className="w-5 h-5 text-emerald-500" />;
            case "processing": return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
            case "failed": return <AlertCircle className="w-5 h-5 text-red-500" />;
            default: return <Clock className="w-5 h-5 text-slate-400" />;
        }
    };

    const getTierLimit = (tier: string) => {
        const limits: Record<string, number> = { free: 0, starter: 1, pro: 5, enterprise: 25 };
        return limits[tier] || 0;
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

    return (
        <div className="min-h-screen bg-[#FAFAFA] text-slate-900 selection:bg-blue-100 selection:text-blue-900 overflow-x-hidden">
            <Navbar />

            {/* Background Gradients */}
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute top-0 opacity-30 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-[radial-gradient(circle_at_center,_var(--color-brand-light)_0%,_transparent_70%)] blur-[100px]" />
                <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-blue-50/50 rounded-full blur-3xl opacity-40 mix-blend-multiply" />
                <div className="absolute top-40 left-0 w-[400px] h-[400px] bg-purple-50/50 rounded-full blur-3xl opacity-40 mix-blend-multiply" />
            </div>

            <main className="pt-32 pb-20 px-6 relative z-10">
                <div className="max-w-7xl mx-auto">
                    {/* Header Section */}
                    <FadeIn>
                        <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 mb-12">
                            <div>
                                <h1 className="text-4xl md:text-5xl font-serif font-medium text-slate-900 mb-2 tracking-tight">
                                    Welcome back, <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">
                                        {user?.user_metadata?.full_name?.split(' ')[0] || "Creator"}
                                    </span>
                                </h1>
                                <p className="text-lg text-slate-500">Here's your channel intelligence overview.</p>
                            </div>

                            {subscription && subscription.tier !== "free" && (
                                <motion.button
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    onClick={() => setShowCreateModal(true)}
                                    className="h-12 px-6 bg-[#1c1c1e] text-white rounded-full font-medium shadow-xl shadow-slate-900/10 hover:shadow-2xl transition-all flex items-center gap-2 group"
                                >
                                    <Plus className="w-5 h-5 group-hover:rotate-90 transition-transform" />
                                    New Analysis
                                </motion.button>
                            )}
                        </div>
                    </FadeIn>

                    {/* Stats Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
                        {/* Current Plan Card */}
                        <FadeIn delay={0.1}>
                            <motion.div
                                whileHover={{ y: -5 }}
                                className="bg-white p-6 rounded-[24px] border border-slate-100 shadow-xl shadow-slate-200/50 relative overflow-hidden group h-full"
                            >
                                <div className="absolute top-0 right-0 w-32 h-32 bg-blue-50/80 rounded-full blur-2xl -mr-10 -mt-10 group-hover:scale-110 transition-transform duration-500" />
                                <div className="relative z-10">
                                    <div className="flex items-center gap-3 mb-4">
                                        <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
                                            <CreditCard className="w-5 h-5" />
                                        </div>
                                        <span className="text-sm text-slate-500 font-medium">Current Plan</span>
                                    </div>
                                    <div className="text-2xl font-bold text-slate-900 capitalize mb-2">
                                        {subscription?.tier || "Free"}
                                    </div>

                                    <div className="mt-4">
                                        <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
                                            <span>Usage</span>
                                            <span className="font-medium">{subscription?.analyses_this_month || 0}/{getTierLimit(subscription?.tier || "free")}</span>
                                        </div>
                                        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                                            <motion.div
                                                initial={{ width: 0 }}
                                                animate={{ width: `${Math.min(100, ((subscription?.analyses_this_month || 0) / (getTierLimit(subscription?.tier || 'free') || 1)) * 100)}%` }}
                                                className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full"
                                            />
                                        </div>
                                    </div>

                                    <div className="mt-4 pt-4 border-t border-slate-50">
                                        <Link href="/pricing" className="text-xs font-bold text-blue-600 hover:text-blue-800 flex items-center gap-1">
                                            {subscription?.tier === "free" ? "Upgrade to Pro" : "Manage Subscription"}
                                            <ArrowUpRight className="w-3 h-3" />
                                        </Link>
                                    </div>
                                </div>
                            </motion.div>
                        </FadeIn>

                        {/* Viral Predictor Card */}
                        <StatCard
                            icon={Sparkles}
                            label="Viral Predictor"
                            value="New Tool"
                            subtext="Test titles & hooks before filming"
                            color="from-pink-500 to-rose-500"
                            onClick={() => window.location.href = '/viral-predictor'}
                            delay={0.2}
                        />

                        {/* Total Analyses */}
                        <StatCard
                            icon={FileText}
                            label="Total Reports"
                            value={reports.length}
                            subtext="Lifetime analyses created"
                            color="from-purple-500 to-violet-500"
                            delay={0.3}
                        />

                        {/* API / Upgrade Card */}
                        <FadeIn delay={0.4}>
                            <motion.div
                                whileHover={{ y: -5 }}
                                className="bg-white p-6 rounded-[24px] border border-slate-100 shadow-xl shadow-slate-200/50 relative overflow-hidden group h-full cursor-pointer"
                                onClick={() => subscription?.tier === "enterprise" ? window.location.href = '/dashboard/api' : window.location.href = '/pricing'}
                            >
                                <div className={`absolute top-0 right-0 w-32 h-32 rounded-full blur-2xl -mr-10 -mt-10 group-hover:scale-110 transition-transform duration-500 ${subscription?.tier === "enterprise" ? "bg-orange-50/80" : "bg-emerald-50/80"}`} />
                                <div className="relative z-10">
                                    <div className="flex items-center gap-3 mb-4">
                                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${subscription?.tier === "enterprise" ? "bg-orange-50 text-orange-600" : "bg-emerald-50 text-emerald-600"}`}>
                                            {subscription?.tier === "enterprise" ? <Key className="w-5 h-5" /> : <TrendingUp className="w-5 h-5" />}
                                        </div>
                                        <span className="text-sm text-slate-500 font-medium">{subscription?.tier === "enterprise" ? "Developer API" : "Growth Tools"}</span>
                                    </div>

                                    {subscription?.tier === "enterprise" ? (
                                        <>
                                            <div className="text-lg font-bold text-slate-900 mb-1">API Active</div>
                                            <p className="text-xs text-slate-500 mb-3">Manage your API keys</p>
                                        </>
                                    ) : (
                                        <>
                                            <div className="text-lg font-bold text-slate-900 mb-1">Unlock API</div>
                                            <p className="text-xs text-slate-500 mb-3">Get API access & team seats</p>
                                        </>
                                    )}

                                    <div className={`mt-auto inline-flex items-center gap-1 text-xs font-bold ${subscription?.tier === "enterprise" ? "text-orange-600" : "text-emerald-600"}`}>
                                        {subscription?.tier === "enterprise" ? "Manage Keys" : "View Plans"}
                                        <ArrowUpRight className="w-3 h-3" />
                                    </div>
                                </div>
                            </motion.div>
                        </FadeIn>
                    </div>

                    {/* Reports Section */}
                    <FadeIn delay={0.5}>
                        <div className="bg-white rounded-[32px] border border-slate-100 shadow-xl shadow-slate-200/50 overflow-hidden">
                            <div className="p-8 border-b border-slate-50 bg-slate-50/30 flex flex-col md:flex-row md:items-center justify-between gap-6">
                                <div>
                                    <h2 className="text-2xl font-serif font-medium text-slate-900">Recent Reports</h2>
                                    <p className="text-sm text-slate-500 mt-1">Manage and organize your channel analyses</p>
                                </div>

                                {/* Folder Tabs */}
                                <div className="flex items-center gap-2 flex-wrap">
                                    <button
                                        onClick={() => setSelectedFolder(null)}
                                        className={`px-4 py-2 text-sm rounded-full transition-all font-medium ${selectedFolder === null ? "bg-slate-900 text-white shadow-lg shadow-slate-900/10" : "text-slate-500 hover:bg-slate-100"}`}
                                    >
                                        All Reports
                                    </button>
                                    {folders.map(folder => (
                                        <button
                                            key={folder.id}
                                            onClick={() => setSelectedFolder(folder.id)}
                                            className={`px-4 py-2 text-sm rounded-full transition-all font-medium flex items-center gap-2 ${selectedFolder === folder.id ? "bg-slate-900 text-white shadow-lg shadow-slate-900/10" : "text-slate-500 hover:bg-slate-100"}`}
                                        >
                                            <span>{folder.icon}</span> {folder.name}
                                        </button>
                                    ))}
                                    {showNewFolderInput ? (
                                        <motion.div
                                            initial={{ opacity: 0, width: 0 }}
                                            animate={{ opacity: 1, width: "auto" }}
                                            ref={newFolderInputRef}
                                            className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-full border border-slate-200 shadow-sm"
                                        >
                                            <input
                                                autoFocus
                                                className="bg-transparent border-none outline-none text-sm w-32 px-1 text-slate-700 placeholder:text-slate-400"
                                                placeholder="Folder name..."
                                                value={newFolderName}
                                                onChange={(e) => setNewFolderName(e.target.value)}
                                                onKeyDown={(e) => e.key === "Enter" && handleCreateFolder()}
                                            />
                                            <button onClick={handleCreateFolder} className="text-emerald-500 hover:text-emerald-600"><CheckCircle className="w-5 h-5" /></button>
                                        </motion.div>
                                    ) : (
                                        <button
                                            onClick={() => setShowNewFolderInput(true)}
                                            className="w-9 h-9 rounded-full border border-dashed border-slate-300 flex items-center justify-center text-slate-400 hover:border-blue-400 hover:text-blue-500 hover:bg-blue-50 transition-all"
                                            title="Create Folder"
                                        >
                                            <Plus className="w-4 h-4" />
                                        </button>
                                    )}
                                </div>
                            </div>

                            <div className="min-h-[300px]">
                                {reports.length === 0 ? (
                                    <div className="flex flex-col items-center justify-center py-20">
                                        <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center text-slate-300 mb-6">
                                            <FileText className="w-10 h-10" />
                                        </div>
                                        <h3 className="text-xl font-medium text-slate-900 mb-2">No reports yet</h3>
                                        <p className="text-slate-500 mb-8 max-w-sm text-center">
                                            Start tracking your first channel to get AI-powered insights and gap detection.
                                        </p>
                                        <motion.button
                                            whileHover={{ scale: 1.05 }}
                                            whileTap={{ scale: 0.95 }}
                                            onClick={() => subscription?.tier === "free" && reports.length >= 1 ? window.location.href = '/pricing' : setShowCreateModal(true)}
                                            className="h-12 px-8 bg-slate-900 text-white rounded-full font-medium hover:bg-slate-800 transition shadow-lg shadow-slate-900/10"
                                        >
                                            {subscription?.tier === "free" && reports.length >= 1 ? "Upgrade for More" : "Create First Report"}
                                        </motion.button>
                                    </div>
                                ) : (
                                    <div className="divide-y divide-slate-50">
                                        {filteredReports?.slice(0, 50).map((report, i) => (
                                            <motion.div
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                transition={{ delay: i * 0.05 }}
                                                key={report.id}
                                                className="p-6 hover:bg-slate-50/50 transition-colors flex items-center justify-between group"
                                            >
                                                <div className="flex items-center gap-5">
                                                    <div className="relative">
                                                        <motion.div whileHover={{ scale: 1.1 }} className="relative z-10">
                                                            {report.channel_thumbnail ? (
                                                                <img
                                                                    src={report.channel_thumbnail}
                                                                    alt={report.channel_name}
                                                                    className="w-14 h-14 rounded-full object-cover border-2 border-white shadow-md"
                                                                />
                                                            ) : (
                                                                <div className="w-14 h-14 rounded-full bg-gradient-to-br from-slate-100 to-slate-200 border-2 border-white shadow-md flex items-center justify-center text-slate-400 text-lg font-bold">
                                                                    {(report.channel_name || 'C')[0].toUpperCase()}
                                                                </div>
                                                            )}
                                                        </motion.div>
                                                        <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-white flex items-center justify-center shadow-sm z-20">
                                                            {getStatusIcon(report.status)}
                                                        </div>
                                                    </div>

                                                    <div>
                                                        <h4 className="text-lg font-semibold text-slate-900 mb-1 group-hover:text-blue-600 transition-colors">
                                                            {report.channel_name}
                                                            <span className="text-slate-400 font-normal text-sm ml-2">@{report.channel_handle}</span>
                                                        </h4>
                                                        <div className="flex items-center gap-3 text-sm text-slate-500">
                                                            <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${report.status === 'completed' ? 'bg-emerald-50 text-emerald-600 border-emerald-100' :
                                                                report.status === 'processing' ? 'bg-blue-50 text-blue-600 border-blue-100' :
                                                                    report.status === 'failed' ? 'bg-red-50 text-red-600 border-red-100' :
                                                                        'bg-slate-50 text-slate-600 border-slate-100'
                                                                }`}>
                                                                {report.status.charAt(0).toUpperCase() + report.status.slice(1)}
                                                            </span>
                                                            <span className="flex items-center gap-1">
                                                                <Clock className="w-3 h-3" />
                                                                {new Date(report.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}
                                                            </span>
                                                            {report.folder_id && folders.find(f => f.id === report.folder_id) && (
                                                                <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 text-xs font-medium">
                                                                    {folders.find(f => f.id === report.folder_id)?.icon} {folders.find(f => f.id === report.folder_id)?.name}
                                                                </span>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>

                                                <div className="flex items-center gap-3 opacity-0 group-hover:opacity-100 transition-opacity translate-x-4 group-hover:translate-x-0 duration-300">
                                                    {/* Folder Menu */}
                                                    <div ref={showFolderMenu === report.id ? folderMenuRef : undefined} className="relative">
                                                        <button
                                                            onClick={() => setShowFolderMenu(showFolderMenu === report.id ? null : report.id)}
                                                            className="p-2.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all"
                                                            title="Move to Folder"
                                                        >
                                                            <FolderPlus className="w-5 h-5" />
                                                        </button>
                                                        {showFolderMenu === report.id && (
                                                            <motion.div
                                                                initial={{ opacity: 0, scale: 0.95 }}
                                                                animate={{ opacity: 1, scale: 1 }}
                                                                className="absolute right-0 top-full mt-2 w-48 bg-white rounded-xl shadow-2xl border border-slate-100 overflow-hidden z-30"
                                                            >
                                                                <div className="px-3 py-2 bg-slate-50 border-b border-slate-100 text-xs font-bold text-slate-500 uppercase tracking-wider">Move to</div>
                                                                <button onClick={() => handleMoveToFolder(report.id, null)} className="w-full text-left px-4 py-2.5 hover:bg-slate-50 text-sm text-slate-600 transition-colors">No Folder</button>
                                                                {folders.map(f => (
                                                                    <button key={f.id} onClick={() => handleMoveToFolder(report.id, f.id)} className="w-full text-left px-4 py-2.5 hover:bg-slate-50 text-sm text-slate-600 transition-colors">
                                                                        {f.icon} {f.name}
                                                                    </button>
                                                                ))}
                                                            </motion.div>
                                                        )}
                                                    </div>

                                                    <button
                                                        onClick={() => handleDeleteReport(report.id)}
                                                        className="p-2.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all"
                                                        title="Delete Report"
                                                    >
                                                        <Trash2 className="w-5 h-5" />
                                                    </button>

                                                    {report.status === "completed" && (
                                                        <Link href={`/report/${report.access_key}`}>
                                                            <motion.button
                                                                whileHover={{ scale: 1.05 }}
                                                                whileTap={{ scale: 0.95 }}
                                                                className="h-10 px-6 bg-white border border-slate-200 text-slate-900 rounded-full text-sm font-bold hover:bg-slate-50 hover:border-slate-300 transition-all shadow-sm flex items-center gap-2"
                                                            >
                                                                View Report <ArrowUpRight className="w-3 h-3" />
                                                            </motion.button>
                                                        </Link>
                                                    )}
                                                </div>
                                            </motion.div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </FadeIn>
                </div>
            </main>

            {/* Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-slate-900/40 backdrop-blur-md">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="bg-white rounded-[40px] w-full max-w-lg p-10 shadow-2xl relative overflow-hidden"
                    >
                        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-50/50 rounded-full blur-3xl -mr-32 -mt-32 pointer-events-none" />

                        <div className="relative z-10">
                            <div className="flex justify-between items-center mb-10">
                                <div>
                                    <h2 className="text-3xl font-serif font-medium text-slate-900 mb-1">New Analysis</h2>
                                    <p className="text-slate-500 text-sm">Scan a channel for growth opportunities</p>
                                </div>
                                <button
                                    onClick={() => setShowCreateModal(false)}
                                    className="p-2 bg-slate-50 rounded-full hover:bg-slate-100 transition-colors"
                                >
                                    <X className="w-6 h-6 text-slate-400" />
                                </button>
                            </div>

                            <div className="space-y-8">
                                <div>
                                    <label className="block text-sm font-bold text-slate-700 mb-3 ml-1">YouTube Channel URL</label>
                                    <div className="flex gap-3 relative">
                                        <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
                                            <Search className="w-5 h-5 text-slate-400" />
                                        </div>
                                        <input
                                            type="text"
                                            value={channelInput}
                                            onChange={(e) => { setChannelInput(e.target.value); setChannelInfo(null); setCreateError(null); }}
                                            placeholder="youtube.com/@channel"
                                            className="flex-1 h-14 pl-12 pr-4 rounded-2xl border border-slate-200 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all bg-slate-50/50 text-lg"
                                            onKeyDown={(e) => e.key === 'Enter' && verifyChannel()}
                                        />
                                        <button
                                            onClick={verifyChannel}
                                            disabled={verifying || !channelInput}
                                            className="h-14 w-14 flex items-center justify-center bg-slate-900 text-white rounded-2xl hover:scale-105 active:scale-95 disabled:opacity-50 disabled:scale-100 transition-all shadow-lg shadow-slate-900/10"
                                        >
                                            {verifying ? <Loader2 className="w-6 h-6 animate-spin" /> : <Search className="w-6 h-6" />}
                                        </button>
                                    </div>
                                </div>

                                {channelInfo && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        className="p-4 bg-emerald-50/50 border border-emerald-100 rounded-2xl flex items-center gap-4"
                                    >
                                        {channelInfo.thumbnailUrl ? (
                                            <img
                                                src={channelInfo.thumbnailUrl}
                                                alt={channelInfo.title}
                                                className="w-14 h-14 rounded-full object-cover border-2 border-emerald-200 shadow-sm"
                                            />
                                        ) : (
                                            <div className="w-14 h-14 bg-emerald-100 rounded-full flex items-center justify-center text-emerald-600">
                                                <CheckCircle className="w-6 h-6" />
                                            </div>
                                        )}
                                        <div>
                                            <p className="font-bold text-lg text-emerald-900">{channelInfo.title}</p>
                                            <p className="text-sm text-emerald-700 font-medium">{channelInfo.subscriberCount} subscribers</p>
                                        </div>
                                        <div className="ml-auto">
                                            <CheckCircle className="w-6 h-6 text-emerald-500" />
                                        </div>
                                    </motion.div>
                                )}

                                {createError && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        className="p-4 bg-red-50/50 border border-red-100 rounded-2xl flex items-center gap-3"
                                    >
                                        <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center shrink-0">
                                            <AlertCircle className="w-5 h-5 text-red-600" />
                                        </div>
                                        <p className="text-sm font-medium text-red-700">{createError}</p>
                                    </motion.div>
                                )}

                                {/* Options */}
                                <div className="p-5 bg-slate-50 border border-slate-100 rounded-2xl">
                                    <div className="flex items-center justify-between">
                                        <div className="flex gap-3">
                                            <div className="mt-0.5">
                                                <Zap className="w-5 h-5 text-amber-500 fill-amber-500" />
                                            </div>
                                            <div>
                                                <p className="font-bold text-slate-900">Include Shorts Analysis</p>
                                                <p className="text-sm text-slate-500 mt-0.5">Analyze vertical short-form (&lt; 60s)</p>
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => setIncludeShorts(!includeShorts)}
                                            className={`w-14 h-8 rounded-full transition-colors relative ${includeShorts ? 'bg-amber-500' : 'bg-slate-300'}`}
                                        >
                                            <motion.div
                                                animate={{ x: includeShorts ? 26 : 4 }}
                                                className="absolute top-1 w-6 h-6 bg-white rounded-full shadow-md"
                                            />
                                        </button>
                                    </div>
                                </div>

                                <div className="pt-4">
                                    <button
                                        onClick={handleCreateReport}
                                        disabled={!channelInfo || creating}
                                        className="w-full h-16 bg-[#1c1c1e] text-white rounded-full font-bold text-lg hover:shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-70 disabled:cursor-not-allowed disabled:scale-100 flex items-center justify-center gap-3"
                                    >
                                        {creating ? (
                                            <>
                                                <Loader2 className="w-6 h-6 animate-spin" />
                                                Analyzing Channel...
                                            </>
                                        ) : (
                                            <>
                                                Start Deep Analysis
                                                <ArrowUpRight className="w-5 h-5" />
                                            </>
                                        )}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </div>
            )}
        </div>
    );
}
