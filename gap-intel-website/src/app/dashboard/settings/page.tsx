"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import Navbar from "@/components/Navbar";
import Image from "next/image";
import Link from "next/link";
import { User, Mail, Shield, Trash2, Globe, Check, Loader2, CreditCard, Zap, ArrowUpRight } from "lucide-react";

const LANGUAGE_OPTIONS = [
    { code: "en", name: "English", abbr: "EN" },
    { code: "de", name: "Deutsch", abbr: "DE" },
    { code: "fr", name: "Français", abbr: "FR" },
    { code: "it", name: "Italiano", abbr: "IT" },
    { code: "es", name: "Español", abbr: "ES" },
];

const TIER_LIMITS: Record<string, number> = {
    free: 1,
    starter: 1,
    pro: 5,
    enterprise: 25,
};

const TIER_DISPLAY: Record<string, { name: string; color: string; bgColor: string }> = {
    free: { name: "Free", color: "text-slate-600", bgColor: "bg-slate-100" },
    starter: { name: "Starter", color: "text-blue-600", bgColor: "bg-blue-100" },
    pro: { name: "Pro", color: "text-purple-600", bgColor: "bg-purple-100" },
    enterprise: { name: "Enterprise", color: "text-orange-600", bgColor: "bg-orange-100" },
};

interface SubscriptionData {
    tier: string;
    analyses_this_month: number;
    status: string;
    current_period_end?: string;
}

export default function SettingsPage() {
    const { user, signOut } = useAuth();
    const [deleteConfirm, setDeleteConfirm] = useState(false);
    const [preferredLanguage, setPreferredLanguage] = useState<string | null>(null);
    const [savingLanguage, setSavingLanguage] = useState(false);
    const [languageSaved, setLanguageSaved] = useState(false);
    const [loadingLanguage, setLoadingLanguage] = useState(true);
    const [subscription, setSubscription] = useState<SubscriptionData | null>(null);
    const [loadingSubscription, setLoadingSubscription] = useState(true);

    useEffect(() => {
        // Load preferred language on mount
        setLoadingLanguage(true);
        fetch("/api/user/settings")
            .then(res => res.json())
            .then(data => {
                setPreferredLanguage(data.preferred_language || "en");
            })
            .catch(() => {
                setPreferredLanguage("en");
            })
            .finally(() => {
                setLoadingLanguage(false);
            });

        // Load subscription data
        setLoadingSubscription(true);
        fetch("/api/user/subscription")
            .then(res => res.json())
            .then(data => {
                setSubscription({
                    tier: data.tier || "free",
                    analyses_this_month: data.analyses_this_month || 0,
                    status: data.status || "active",
                    current_period_end: data.current_period_end,
                });
            })
            .catch(() => {
                setSubscription({ tier: "free", analyses_this_month: 0, status: "active" });
            })
            .finally(() => {
                setLoadingSubscription(false);
            });
    }, []);

    const handleLanguageChange = async (langCode: string) => {
        setPreferredLanguage(langCode);
        setSavingLanguage(true);
        setLanguageSaved(false);

        try {
            const res = await fetch("/api/user/settings", {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ preferred_language: langCode }),
            });

            if (res.ok) {
                setLanguageSaved(true);
                setTimeout(() => setLanguageSaved(false), 2000);
            }
        } catch (error) {
            console.error("Error saving language:", error);
        } finally {
            setSavingLanguage(false);
        }
    };

    const handleDeleteAccount = async () => {
        if (!deleteConfirm) {
            setDeleteConfirm(true);
            return;
        }

        try {
            const res = await fetch("/api/user/delete", {
                method: "DELETE",
            });
            if (res.ok) {
                await signOut();
                window.location.href = "/";
            }
        } catch (error) {
            console.error("Error deleting account:", error);
        }
    };

    return (
        <div className="min-h-screen bg-[#fafbfc]">
            <Navbar />

            <main className="pt-24 pb-12 px-6">
                <div className="max-w-2xl mx-auto">
                    {/* Header */}
                    <div className="mb-8">
                        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
                        <p className="text-gray-500 mt-1">Manage your account settings.</p>
                    </div>

                    {/* Profile Section */}
                    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 mb-6">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                            <User className="w-5 h-5" />
                            Profile
                        </h2>

                        <div className="flex items-center gap-4 mb-6">
                            {user?.user_metadata?.avatar_url ? (
                                <Image
                                    src={user.user_metadata.avatar_url}
                                    alt={user.user_metadata.full_name || "User"}
                                    width={64}
                                    height={64}
                                    className="rounded-full"
                                />
                            ) : (
                                <div className="w-16 h-16 rounded-full bg-emerald-500 flex items-center justify-center text-white text-xl font-medium">
                                    {(user?.email?.[0] || "U").toUpperCase()}
                                </div>
                            )}
                            <div>
                                <p className="text-lg font-medium text-gray-900">
                                    {user?.user_metadata?.full_name || "User"}
                                </p>
                                <p className="text-sm text-gray-500">{user?.email}</p>
                            </div>
                        </div>

                        <div className="text-sm text-gray-500">
                            <p>
                                Your profile information is managed by Google. To update your name or picture, visit
                                your{" "}
                                <a
                                    href="https://myaccount.google.com"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-emerald-600 hover:underline"
                                >
                                    Google Account settings
                                </a>
                                .
                            </p>
                        </div>
                    </div>

                    {/* Subscription Section */}
                    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 mb-6">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                            <CreditCard className="w-5 h-5" />
                            Subscription
                        </h2>

                        {loadingSubscription ? (
                            <div className="flex items-center justify-center py-8">
                                <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
                            </div>
                        ) : subscription ? (
                            <div className="space-y-4">
                                {/* Current Plan */}
                                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                                    <div>
                                        <p className="text-sm text-gray-500">Current Plan</p>
                                        <div className="flex items-center gap-2 mt-1">
                                            <span className={`px-2.5 py-1 rounded-full text-sm font-bold ${TIER_DISPLAY[subscription.tier]?.bgColor || "bg-slate-100"} ${TIER_DISPLAY[subscription.tier]?.color || "text-slate-600"}`}>
                                                {TIER_DISPLAY[subscription.tier]?.name || "Free"}
                                            </span>
                                            {subscription.tier !== "enterprise" && (
                                                <Link
                                                    href="/pricing"
                                                    className="text-sm text-emerald-600 hover:text-emerald-700 font-medium flex items-center gap-1"
                                                >
                                                    Upgrade <ArrowUpRight className="w-3.5 h-3.5" />
                                                </Link>
                                            )}
                                        </div>
                                    </div>
                                    <Link
                                        href="/dashboard/billing"
                                        className="px-4 py-2 bg-white border border-gray-200 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition shadow-sm"
                                    >
                                        Manage Billing
                                    </Link>
                                </div>

                                {/* Usage This Month */}
                                <div className="p-4 bg-gray-50 rounded-lg">
                                    <div className="flex items-center justify-between mb-2">
                                        <p className="text-sm text-gray-500">Analyses This Month</p>
                                        <p className="text-sm font-medium text-gray-900">
                                            {subscription.analyses_this_month} / {TIER_LIMITS[subscription.tier] || 1}
                                        </p>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-2">
                                        <div
                                            className={`h-2 rounded-full transition-all ${
                                                subscription.analyses_this_month >= (TIER_LIMITS[subscription.tier] || 1)
                                                    ? "bg-red-500"
                                                    : "bg-emerald-500"
                                            }`}
                                            style={{
                                                width: `${Math.min(100, (subscription.analyses_this_month / (TIER_LIMITS[subscription.tier] || 1)) * 100)}%`
                                            }}
                                        />
                                    </div>
                                    {subscription.analyses_this_month >= (TIER_LIMITS[subscription.tier] || 1) && (
                                        <p className="text-xs text-red-600 mt-2 flex items-center gap-1">
                                            <Zap className="w-3 h-3" />
                                            Limit reached. <Link href="/pricing" className="underline">Upgrade for more analyses</Link>
                                        </p>
                                    )}
                                </div>

                                {/* Renewal Date */}
                                {subscription.current_period_end && subscription.tier !== "free" && (
                                    <div className="p-4 bg-gray-50 rounded-lg">
                                        <p className="text-sm text-gray-500">Next Renewal</p>
                                        <p className="font-medium text-gray-900 mt-1">
                                            {new Date(subscription.current_period_end).toLocaleDateString("en-US", {
                                                year: "numeric",
                                                month: "long",
                                                day: "numeric"
                                            })}
                                        </p>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="p-4 bg-gray-50 rounded-lg text-center">
                                <p className="text-gray-500 mb-3">No active subscription</p>
                                <Link
                                    href="/pricing"
                                    className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500 text-white font-medium rounded-lg hover:bg-emerald-600 transition"
                                >
                                    View Plans <ArrowUpRight className="w-4 h-4" />
                                </Link>
                            </div>
                        )}
                    </div>

                    {/* Report Language Section */}
                    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 mb-6">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                            <Globe className="w-5 h-5" />
                            Report Language
                            {savingLanguage && <Loader2 className="w-4 h-4 animate-spin text-gray-400" />}
                            {languageSaved && <Check className="w-4 h-4 text-emerald-500" />}
                        </h2>

                        <p className="text-sm text-gray-500 mb-4">
                            Choose the language for your analysis reports. All AI-generated insights, titles, and recommendations will be in this language.
                        </p>

                        {loadingLanguage ? (
                            <div className="flex items-center justify-center py-8">
                                <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
                            </div>
                        ) : (
                            <div className="grid grid-cols-5 gap-3">
                                {LANGUAGE_OPTIONS.map((lang) => (
                                    <button
                                        key={lang.code}
                                        onClick={() => handleLanguageChange(lang.code)}
                                        disabled={savingLanguage}
                                        className={`flex flex-col items-center p-4 rounded-xl border-2 transition-all ${preferredLanguage === lang.code
                                            ? 'bg-slate-900 border-slate-900 text-white'
                                            : 'bg-slate-50 border-slate-200 text-slate-600 hover:border-slate-300 hover:bg-slate-100'
                                            } ${savingLanguage ? 'opacity-50 cursor-not-allowed' : ''}`}
                                    >
                                        <span className={`text-sm font-bold mb-1 ${preferredLanguage === lang.code ? 'text-white' : 'text-slate-700'}`}>
                                            {lang.abbr}
                                        </span>
                                        <span className={`text-xs font-medium ${preferredLanguage === lang.code ? 'text-slate-300' : 'text-slate-500'}`}>
                                            {lang.name}
                                        </span>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Email Section */}
                    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 mb-6">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                            <Mail className="w-5 h-5" />
                            Email
                        </h2>

                        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                            <div>
                                <p className="font-medium text-gray-900">{user?.email}</p>
                                <p className="text-sm text-gray-500">Primary email for all communications</p>
                            </div>
                            <span className="px-2 py-1 bg-emerald-100 text-emerald-700 text-xs font-medium rounded-full">
                                Verified
                            </span>
                        </div>
                    </div>

                    {/* Integrations Section */}
                    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 mb-6">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                            <svg className="w-5 h-5 text-red-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2.5 17a24.12 24.12 0 0 1 0-10 2 2 0 0 1 1.4-1.4 49.56 49.56 0 0 1 16.2 0A2 2 0 0 1 21.5 7a24.12 24.12 0 0 1 0 10 2 2 0 0 1-1.4 1.4 49.55 49.55 0 0 1-16.2 0A2 2 0 0 1 2.5 17"></path><path d="m10 15 5-3-5-3z"></path></svg>
                            Integrations
                        </h2>

                        <div className="p-4 bg-gray-50 rounded-lg flex items-center justify-between">
                            <div>
                                <p className="font-medium text-gray-900">YouTube Analytics</p>
                                <p className="text-sm text-gray-500 mt-1">
                                    Connect to enable ML-powered CTR predictions and personalized insights.
                                </p>
                            </div>
                            <a
                                href="/dashboard/connect-analytics"
                                className="px-4 py-2 bg-white border border-gray-200 text-gray-700 font-medium rounded-lg hover:bg-gray-50 hover:text-gray-900 transition shadow-sm"
                            >
                                Manage
                            </a>
                        </div>
                    </div>

                    {/* Security Section */}
                    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 mb-6">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                            <Shield className="w-5 h-5" />
                            Security
                        </h2>

                        <div className="p-4 bg-gray-50 rounded-lg">
                            <p className="font-medium text-gray-900">Google Sign-In</p>
                            <p className="text-sm text-gray-500 mt-1">
                                Your account is secured through Google. Password and 2FA are managed by Google.
                            </p>
                        </div>
                    </div>

                    {/* Danger Zone */}
                    <div className="bg-white rounded-xl border border-red-200 shadow-sm p-6">
                        <h2 className="text-lg font-semibold text-red-600 mb-4 flex items-center gap-2">
                            <Trash2 className="w-5 h-5" />
                            Danger Zone
                        </h2>

                        <p className="text-sm text-gray-600 mb-4">
                            Permanently delete your account and all associated data. This action cannot be undone.
                        </p>

                        <button
                            onClick={handleDeleteAccount}
                            className={`px-4 py-2 text-sm font-medium rounded-lg transition ${deleteConfirm
                                ? "bg-red-600 text-white hover:bg-red-700"
                                : "bg-red-100 text-red-600 hover:bg-red-200"
                                }`}
                        >
                            {deleteConfirm ? "Click again to confirm deletion" : "Delete Account"}
                        </button>

                        {deleteConfirm && (
                            <button
                                onClick={() => setDeleteConfirm(false)}
                                className="ml-3 px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition"
                            >
                                Cancel
                            </button>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
