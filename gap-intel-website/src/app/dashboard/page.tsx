"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import Navbar from "@/components/Navbar";
import { BarChart3, FileText, CreditCard, TrendingUp, Clock, CheckCircle, AlertCircle, Loader2, Plus, X, Search, Trash2, FolderPlus, MoreVertical, Key, Users, Palette, ArrowUpRight, Sparkles } from "lucide-react";
import { motion } from "framer-motion";

interface Report {
    id: string;
    access_key: string;
    channel_name: string;
    channel_handle: string;
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
    const [channelInfo, setChannelInfo] = useState<{ title: string; subscriberCount: string } | null>(null);
    const [creating, setCreating] = useState(false);
    const [createError, setCreateError] = useState<string | null>(null);
    const [syncing, setSyncing] = useState(false);

    // Folder and delete state
    const [folders, setFolders] = useState<Folder[]>([]);
    const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
    const [showFolderMenu, setShowFolderMenu] = useState<string | null>(null);
    const [newFolderName, setNewFolderName] = useState("");
    const [showNewFolderInput, setShowNewFolderInput] = useState(false);

    // Refs for click-outside handling
    const folderMenuRef = useRef<HTMLDivElement>(null);
    const newFolderInputRef = useRef<HTMLDivElement>(null);

    // Click outside handler to close dropdowns
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (folderMenuRef.current && !folderMenuRef.current.contains(event.target as Node)) {
                setShowFolderMenu(null);
            }
            if (newFolderInputRef.current && !newFolderInputRef.current.contains(event.target as Node)) {
                setShowNewFolderInput(false);
                setNewFolderName("");
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    useEffect(() => {
        if (user) {
            fetchData();
        }
    }, [user]);

    const fetchData = async () => {
        try {
            const reportsRes = await fetch("/api/user/reports");
            if (reportsRes.ok) {
                const reportsData = await reportsRes.json();
                setReports(reportsData.reports || []);
            }

            const subRes = await fetch("/api/user/subscription");
            if (subRes.ok) {
                const subData = await subRes.json();
                setSubscription(subData);
            }

            if (user?.id) {
                const foldersRes = await fetch(`/api/reports/folders?userId=${user.id}`);
                if (foldersRes.ok) {
                    const foldersData = await foldersRes.json();
                    setFolders(foldersData.folders || []);
                }
            }
        } catch (error) {
            console.error("Error fetching dashboard data:", error);
        } finally {
            setLoading(false);
        }
    };

    // Polling mechanism
    useEffect(() => {
        const hasProcessingReports = reports.some(r => r.status === "processing" || r.status === "pending");
        if (!hasProcessingReports) return;

        const RAILWAY_API_URL = process.env.NEXT_PUBLIC_API_URL || "https://thriving-presence-production-ca4a.up.railway.app";
        const pollInterval = setInterval(async () => {
            // Keep alive ping
            try { await fetch(`${RAILWAY_API_URL}/health`, { mode: "no-cors" }); } catch (e) { }

            try {
                const reportsRes = await fetch("/api/user/reports");
                if (reportsRes.ok) {
                    const reportsData = await reportsRes.json();
                    setReports(reportsData.reports || []);
                }
            } catch (error) { console.error("Error refreshing reports:", error); }
        }, 30000);

        fetch(`${RAILWAY_API_URL}/health`, { mode: "no-cors" }).catch(() => { });
        return () => clearInterval(pollInterval);
    }, [reports]);

    const handleDeleteReport = async (reportId: string) => {
        if (!confirm("Are you sure you want to delete this report?")) return;
        try {
            const res = await fetch(`/api/reports/manage?id=${reportId}`, { method: "DELETE" });
            if (res.ok) {
                setReports(reports.filter(r => r.id !== reportId));
            }
        } catch (error) { console.error("Delete failed:", error); }
    };

    const handleMoveToFolder = async (reportId: string, folderId: string | null) => {
        try {
            const res = await fetch("/api/reports/manage", {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ reportId, folderId })
            });
            if (res.ok) {
                setReports(reports.map(r => r.id === reportId ? { ...r, folder_id: folderId } : r));
                setShowFolderMenu(null);
            }
        } catch (error) { console.error("Move failed:", error); }
    };

    const handleCreateFolder = async () => {
        if (!newFolderName.trim() || !user?.id) return;
        try {
            const res = await fetch("/api/reports/folders", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ userId: user.id, name: newFolderName.trim() })
            });
            if (res.ok) {
                const data = await res.json();
                setFolders([...folders, data.folder]);
                setNewFolderName("");
                setShowNewFolderInput(false);
            }
        } catch (error) { console.error("Create folder failed:", error); }
    };

    const filteredReports = selectedFolder
        ? reports.filter(r => r.folder_id === selectedFolder)
        : reports;

    const handleSyncSubscription = async () => {
        setSyncing(true);
        try {
            const res = await fetch("/api/user/sync-subscription", { method: "POST" });
            const data = await res.json();
            if (res.ok && data.success) {
                await fetchData();
            } else {
                alert(`Sync failed: ${data.details || data.error || "Unknown error"}`);
            }
        } catch (error) { alert("Sync failed: Network error"); } finally { setSyncing(false); }
    };

    const verifyChannel = async () => {
        if (!channelInput.trim()) return;
        setVerifying(true);
        setChannelInfo(null);
        setCreateError(null);
        try {
            const res = await fetch(`/api/youtube/channel?input=${encodeURIComponent(channelInput)}`);
            if (res.ok) {
                const data = await res.json();
                setChannelInfo(data);
            } else {
                const data = await res.json();
                setCreateError(data.error || "Channel not found. Please check the name or URL.");
            }
        } catch (error) { setCreateError("Failed to verify channel"); } finally { setVerifying(false); }
    };

    const handleCreateReport = async () => {
        if (!channelInfo) return;
        setCreating(true);
        setCreateError(null);
        try {
            const res = await fetch("/api/reports/create", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    channelName: channelInfo.title,
                    channelHandle: channelInput,
                    includeShorts: includeShorts,
                }),
            });
            const data = await res.json();
            if (res.ok) {
                setShowCreateModal(false);
                setChannelInput("");
                setChannelInfo(null);
                fetchData();
            } else if (data.requiresSubscription) {
                setCreateError("Please subscribe to create reports.");
            } else if (data.limitReached) {
                setCreateError(data.error);
            } else {
                setCreateError(data.details || data.error || "Failed to create report");
            }
        } catch (error) { setCreateError("Failed to create report"); } finally { setCreating(false); }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case "completed": return <CheckCircle className="w-5 h-5 text-emerald-500" />;
            case "processing": return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
            case "failed": return <AlertCircle className="w-5 h-5 text-red-500" />;
            default: return <Clock className="w-5 h-5 text-slate-400" />;
        }
    };

    const getTierBadge = (tier: string) => {
        switch (tier) {
            case "starter": return "bg-blue-50 text-blue-700 border-blue-100";
            case "pro": return "bg-emerald-50 text-emerald-700 border-emerald-100";
            case "enterprise": return "bg-purple-50 text-purple-700 border-purple-100";
            default: return "bg-slate-50 text-slate-600 border-slate-100";
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
        <div className="min-h-screen bg-[#FAFAFA] text-slate-900 selection:bg-blue-100 selection:text-blue-900">
            <Navbar />

            <main className="pt-32 pb-20 px-6">
                <div className="max-w-7xl mx-auto">
                    {/* Header */}
                    <div className="flex justify-between items-center mb-10">
                        <div>
                            <h1 className="text-3xl font-serif font-medium text-slate-900 mb-1">
                                Welcome back, {user?.user_metadata?.full_name?.split(' ')[0] || "User"}
                            </h1>
                            <p className="text-slate-500">Here is what's happening with your channel evaluations.</p>
                        </div>
                        {subscription && subscription.tier !== "free" && (
                            <button
                                onClick={() => setShowCreateModal(true)}
                                className="px-6 py-3 bg-slate-900 rounded-full text-white text-sm font-medium shadow-lg shadow-slate-900/10 hover:bg-slate-800 transition-colors flex items-center gap-2"
                            >
                                <Plus className="w-4 h-4" /> Create New Report
                            </button>
                        )}
                    </div>

                    {/* Stats Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
                        {/* Plan & Usage Card */}
                        <div className="bg-white p-6 rounded-[2rem] border border-slate-100 shadow-sm relative overflow-hidden group">
                            <div className="absolute top-0 right-0 w-24 h-24 bg-blue-50/50 rounded-full -mr-10 -mt-10 group-hover:scale-110 transition-transform" />
                            <div className="relative z-10">
                                <div className="flex items-center gap-3 mb-4">
                                    <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center text-blue-600 font-bold text-xs"><CreditCard size={18} /></div>
                                    <span className="text-sm text-slate-500 font-medium">Current Plan</span>
                                </div>
                                <div className="text-2xl font-bold text-slate-900 capitalize mb-1">{subscription?.tier || "Free"}</div>
                                <div className="flex items-center gap-2 mb-3">
                                    <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                                        <div className="h-full bg-blue-500 rounded-full transition-all duration-1000" style={{ width: `${Math.min(100, ((subscription?.analyses_this_month || 0) / getTierLimit(subscription?.tier || 'free')) * 100)}%` }} />
                                    </div>
                                    <span className="text-xs font-medium text-slate-500">{subscription?.analyses_this_month || 0}/{getTierLimit(subscription?.tier || "free")} used</span>
                                </div>
                                <Link href="/pricing" className="text-xs font-medium text-blue-600 hover:text-blue-800">
                                    {subscription?.tier === "free" ? "Upgrade to Pro" : "Manage Subscription"}
                                </Link>
                            </div>
                        </div>

                        {/* Viral Predictor Card (NEW) */}
                        <div className="bg-white p-6 rounded-[2rem] border border-slate-100 shadow-sm relative overflow-hidden group cursor-pointer" onClick={() => window.location.href = '/viral-predictor'}>
                            <div className="absolute top-0 right-0 w-24 h-24 bg-pink-50/50 rounded-full -mr-10 -mt-10 group-hover:scale-110 transition-transform" />
                            <div className="relative z-10">
                                <div className="flex items-center gap-3 mb-4">
                                    <div className="w-10 h-10 rounded-full bg-pink-50 flex items-center justify-center text-pink-600 font-bold text-xs"><Sparkles size={18} /></div>
                                    <span className="text-sm text-slate-500 font-medium">New Tool</span>
                                </div>
                                <div className="text-2xl font-bold text-slate-900 mb-1">Viral Predictor</div>
                                <p className="text-xs text-slate-400 mt-1 mb-3">Predict views & virality</p>
                                <Link href="/viral-predictor" className="text-xs font-medium text-pink-600 hover:text-pink-800 flex items-center gap-1">
                                    Try Now <ArrowUpRight className="w-3 h-3" />
                                </Link>
                            </div>
                        </div>

                        {/* Total Reports Card */}
                        <div className="bg-white p-6 rounded-[2rem] border border-slate-100 shadow-sm relative overflow-hidden group">
                            <div className="absolute top-0 right-0 w-24 h-24 bg-purple-50/50 rounded-full -mr-10 -mt-10 group-hover:scale-110 transition-transform" />
                            <div className="relative z-10">
                                <div className="flex items-center gap-3 mb-4">
                                    <div className="w-10 h-10 rounded-full bg-purple-50 flex items-center justify-center text-purple-600 font-bold text-xs"><FileText size={18} /></div>
                                    <span className="text-sm text-slate-500 font-medium">Total Analyses</span>
                                </div>
                                <div className="text-3xl font-bold text-slate-900">{reports.length}</div>
                                <p className="text-xs text-slate-400 mt-1">Lifetime reports generated</p>
                            </div>
                        </div>

                        {/* Quick Action / Latest or API */}
                        <div className="bg-white p-6 rounded-[2rem] border border-slate-100 shadow-sm relative overflow-hidden group">
                            {subscription?.tier === "enterprise" ? (
                                <>
                                    <div className="absolute top-0 right-0 w-24 h-24 bg-orange-50/50 rounded-full -mr-10 -mt-10 group-hover:scale-110 transition-transform" />
                                    <div className="relative z-10">
                                        <div className="flex items-center gap-3 mb-4">
                                            <div className="w-10 h-10 rounded-full bg-orange-50 flex items-center justify-center text-orange-600 font-bold text-xs"><Key size={18} /></div>
                                            <span className="text-sm text-slate-500 font-medium">API Access</span>
                                        </div>
                                        <div className="text-lg font-bold text-slate-900 mb-1">Active</div>
                                        <Link href="/dashboard/api" className="text-xs font-medium text-orange-600 hover:text-orange-800 flex items-center gap-1">
                                            Manage Keys <ArrowUpRight className="w-3 h-3" />
                                        </Link>
                                    </div>
                                </>
                            ) : (
                                <>
                                    <div className="absolute top-0 right-0 w-24 h-24 bg-slate-50 rounded-full -mr-10 -mt-10 group-hover:scale-110 transition-transform" />
                                    <div className="relative z-10">
                                        <div className="flex items-center gap-3 mb-4">
                                            <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-600 font-bold text-xs"><TrendingUp size={18} /></div>
                                            <span className="text-sm text-slate-500 font-medium">Unlock More</span>
                                        </div>
                                        <div className="text-base font-medium text-slate-900 mb-2">Get API access & teams</div>
                                        <Link href="/pricing" className="text-xs font-bold px-3 py-1.5 bg-slate-900 text-white rounded-lg hover:bg-slate-800 inline-block">
                                            Upgrade Plan
                                        </Link>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>

                    {/* Enterprise Features */}
                    {subscription?.tier === "enterprise" && (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                            <Link href="/dashboard/api" className="bg-white rounded-2xl p-6 border border-slate-100 hover:shadow-lg transition-shadow flex items-center gap-4 group">
                                <div className="w-12 h-12 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600 group-hover:scale-110 transition-transform">
                                    <Key className="w-6 h-6" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-slate-900">API Access</h3>
                                    <p className="text-sm text-slate-500">Manage keys & usage</p>
                                </div>
                            </Link>
                            <Link href="/dashboard/team" className="bg-white rounded-2xl p-6 border border-slate-100 hover:shadow-lg transition-shadow flex items-center gap-4 group">
                                <div className="w-12 h-12 rounded-xl bg-violet-50 flex items-center justify-center text-violet-600 group-hover:scale-110 transition-transform">
                                    <Users className="w-6 h-6" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-slate-900">Team Members</h3>
                                    <p className="text-sm text-slate-500">Manage 10 seats</p>
                                </div>
                            </Link>
                            <Link href="/dashboard/branding" className="bg-white rounded-2xl p-6 border border-slate-100 hover:shadow-lg transition-shadow flex items-center gap-4 group">
                                <div className="w-12 h-12 rounded-xl bg-orange-50 flex items-center justify-center text-orange-600 group-hover:scale-110 transition-transform">
                                    <Palette className="w-6 h-6" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-slate-900">Branding</h3>
                                    <p className="text-sm text-slate-500">Custom white-label</p>
                                </div>
                            </Link>
                        </div>
                    )}

                    {/* Reports Section */}
                    <div className="bg-white rounded-[32px] border border-slate-100 shadow-xl shadow-slate-200/50 overflow-hidden">
                        <div className="p-8 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-6">
                            <h2 className="text-2xl font-serif font-medium text-slate-900">Recent Reports</h2>

                            {/* Folder Tabs */}
                            <div className="flex items-center gap-2 flex-wrap">
                                <button
                                    onClick={() => setSelectedFolder(null)}
                                    className={`px-4 py-2 text-sm rounded-full transition font-medium ${selectedFolder === null ? "bg-slate-900 text-white shadow-lg shadow-slate-900/10" : "text-slate-500 hover:bg-slate-50"}`}
                                >
                                    All
                                </button>
                                {folders.map(folder => (
                                    <button
                                        key={folder.id}
                                        onClick={() => setSelectedFolder(folder.id)}
                                        className={`px-4 py-2 text-sm rounded-full transition font-medium flex items-center gap-2 ${selectedFolder === folder.id ? "bg-slate-900 text-white shadow-lg shadow-slate-900/10" : "text-slate-500 hover:bg-slate-50"}`}
                                    >
                                        <span>{folder.icon}</span> {folder.name}
                                    </button>
                                ))}
                                {showNewFolderInput ? (
                                    <div ref={newFolderInputRef} className="flex items-center gap-2 bg-slate-50 px-2 py-1 rounded-full border border-slate-200">
                                        <input
                                            autoFocus
                                            className="bg-transparent border-none outline-none text-sm w-24 px-2"
                                            placeholder="Folder name"
                                            value={newFolderName}
                                            onChange={(e) => setNewFolderName(e.target.value)}
                                            onKeyDown={(e) => e.key === "Enter" && handleCreateFolder()}
                                        />
                                        <button onClick={handleCreateFolder} className="text-slate-900 hover:text-green-600"><CheckCircle className="w-4 h-4" /></button>
                                    </div>
                                ) : (
                                    <button onClick={() => setShowNewFolderInput(true)} className="w-8 h-8 rounded-full border border-dashed border-slate-300 flex items-center justify-center text-slate-400 hover:border-slate-400 hover:text-slate-600 transition">
                                        <Plus className="w-4 h-4" />
                                    </button>
                                )}
                            </div>
                        </div>

                        {reports.length === 0 ? (
                            <div className="p-16 text-center">
                                <FileText className="w-16 h-16 text-slate-200 mx-auto mb-6" />
                                <h3 className="text-xl font-medium text-slate-900 mb-2">No reports yet</h3>
                                <p className="text-slate-500 mb-8 max-w-md mx-auto">
                                    Start tracking your first channel to get AI-powered insights.
                                </p>
                                {subscription?.tier === "free" ? (
                                    <Link href="/pricing">
                                        <button className="h-12 px-8 bg-slate-900 text-white rounded-full font-medium hover:bg-slate-800 transition">
                                            View Plans
                                        </button>
                                    </Link>
                                ) : (
                                    <button onClick={() => setShowCreateModal(true)} className="h-12 px-8 bg-slate-900 text-white rounded-full font-medium hover:bg-slate-800 transition">
                                        Create Report
                                    </button>
                                )}
                            </div>
                        ) : (
                            <div>
                                {filteredReports.slice(0, 50).map((report) => (
                                    <div key={report.id} className="p-6 border-b border-slate-50 last:border-0 hover:bg-slate-50/50 transition flex items-center justify-between group">
                                        <div className="flex items-center gap-6">
                                            <div className="w-12 h-12 rounded-2xl bg-white border border-slate-100 shadow-sm flex items-center justify-center">
                                                {getStatusIcon(report.status)}
                                            </div>
                                            <div>
                                                <h4 className="text-lg font-medium text-slate-900 mb-1">
                                                    @{report.channel_handle || report.channel_name}
                                                </h4>
                                                <div className="flex items-center gap-3 text-sm text-slate-500">
                                                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${report.status === 'completed' ? 'bg-emerald-50 text-emerald-700 border-emerald-100' :
                                                        report.status === 'processing' ? 'bg-blue-50 text-blue-700 border-blue-100' :
                                                            report.status === 'failed' ? 'bg-red-50 text-red-700 border-red-100' :
                                                                'bg-slate-50 text-slate-700 border-slate-100'
                                                        }`}>
                                                        {report.status.charAt(0).toUpperCase() + report.status.slice(1)}
                                                    </span>
                                                    <span>{new Date(report.created_at).toLocaleDateString()}</span>
                                                    {report.folder_id && folders.find(f => f.id === report.folder_id) && (
                                                        <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 text-xs">
                                                            {folders.find(f => f.id === report.folder_id)?.icon} {folders.find(f => f.id === report.folder_id)?.name}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-3">
                                            {/* Folder Menu */}
                                            <div ref={showFolderMenu === report.id ? folderMenuRef : undefined} className="relative">
                                                <button onClick={() => setShowFolderMenu(showFolderMenu === report.id ? null : report.id)} className="p-2 text-slate-300 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition">
                                                    <FolderPlus className="w-5 h-5" />
                                                </button>
                                                {showFolderMenu === report.id && (
                                                    <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-xl shadow-xl border border-slate-100 overflow-hidden z-20">
                                                        <button onClick={() => handleMoveToFolder(report.id, null)} className="w-full text-left px-4 py-3 hover:bg-slate-50 text-sm text-slate-600">None</button>
                                                        {folders.map(f => (
                                                            <button key={f.id} onClick={() => handleMoveToFolder(report.id, f.id)} className="w-full text-left px-4 py-3 hover:bg-slate-50 text-sm text-slate-600">
                                                                {f.icon} {f.name}
                                                            </button>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>

                                            <button onClick={() => handleDeleteReport(report.id)} className="p-2 text-slate-300 hover:text-red-600 hover:bg-red-50 rounded-lg transition">
                                                <Trash2 className="w-5 h-5" />
                                            </button>

                                            {report.status === "completed" && (
                                                <Link href={`/report/${report.access_key}`}>
                                                    <button className="h-10 px-5 bg-white border border-slate-200 text-slate-900 rounded-full text-sm font-medium hover:bg-slate-50 transition shadow-sm">
                                                        View Report
                                                    </button>
                                                </Link>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </main>

            {/* Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-slate-900/20 backdrop-blur-sm">
                    <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="bg-white rounded-[32px] w-full max-w-lg p-8 shadow-2xl">
                        <div className="flex justify-between items-center mb-8">
                            <h2 className="text-2xl font-serif font-medium text-slate-900">New Analysis</h2>
                            <button onClick={() => setShowCreateModal(false)} className="p-2 bg-slate-50 rounded-full hover:bg-slate-100 transition"><X className="w-5 h-5 text-slate-500" /></button>
                        </div>

                        <div className="space-y-6">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">YouTube Channel URL</label>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={channelInput}
                                        onChange={(e) => { setChannelInput(e.target.value); setChannelInfo(null); setCreateError(null); }}
                                        placeholder="youtube.com/@channel"
                                        className="flex-1 h-12 px-4 rounded-xl border border-slate-200 outline-none focus:border-slate-900 transition bg-slate-50/50"
                                    />
                                    <button
                                        onClick={verifyChannel}
                                        disabled={verifying || !channelInput}
                                        className="h-12 w-12 flex items-center justify-center bg-slate-900 text-white rounded-xl hover:bg-slate-800 disabled:opacity-50 transition"
                                    >
                                        {verifying ? <Loader2 className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
                                    </button>
                                </div>
                            </div>

                            {channelInfo && (
                                <div className="p-4 bg-green-50 border border-green-100 rounded-xl flex items-center gap-3">
                                    <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center text-green-600">
                                        <CheckCircle className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <p className="font-medium text-green-900">{channelInfo.title}</p>
                                        <p className="text-sm text-green-700">{channelInfo.subscriberCount} subscribers</p>
                                    </div>
                                </div>
                            )}

                            {createError && (
                                <div className="p-4 bg-red-50 border border-red-100 rounded-xl flex items-center gap-3">
                                    <AlertCircle className="w-5 h-5 text-red-600" />
                                    <p className="text-sm text-red-700">{createError}</p>
                                </div>
                            )}

                            {/* Skip Shorts Toggle */}
                            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl">
                                <div>
                                    <p className="font-medium text-slate-900">Include Shorts</p>
                                    <p className="text-sm text-slate-500">Analyze short-form videos (≤60s)</p>
                                </div>
                                <button
                                    onClick={() => setIncludeShorts(!includeShorts)}
                                    className={`w-12 h-7 rounded-full transition-colors relative ${includeShorts ? 'bg-blue-500' : 'bg-slate-300'}`}
                                >
                                    <div className={`absolute top-1 w-5 h-5 bg-white rounded-full shadow transition-transform ${includeShorts ? 'left-6' : 'left-1'}`} />
                                </button>
                            </div>

                            <div className="pt-4 border-t border-slate-100">
                                <button
                                    onClick={handleCreateReport}
                                    disabled={!channelInfo || creating}
                                    className="w-full h-14 bg-[#1c1c1e] text-white rounded-full font-medium text-lg hover:shadow-xl hover:scale-[1.02] transition-all disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                >
                                    {creating ? "Analyzing..." : "Start Analysis"}
                                </button>
                            </div>
                        </div>
                    </motion.div>
                </div>
            )}
        </div>
    );
}

