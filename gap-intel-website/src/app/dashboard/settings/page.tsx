"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import Navbar from "@/components/Navbar";
import Image from "next/image";
import { User, Mail, Shield, Trash2, Globe, Check, Loader2 } from "lucide-react";

const LANGUAGE_OPTIONS = [
    { code: "en", name: "English", abbr: "EN" },
    { code: "de", name: "Deutsch", abbr: "DE" },
    { code: "fr", name: "Français", abbr: "FR" },
    { code: "it", name: "Italiano", abbr: "IT" },
    { code: "es", name: "Español", abbr: "ES" },
];

export default function SettingsPage() {
    const { user, signOut } = useAuth();
    const [deleteConfirm, setDeleteConfirm] = useState(false);
    const [preferredLanguage, setPreferredLanguage] = useState<string | null>(null);
    const [savingLanguage, setSavingLanguage] = useState(false);
    const [languageSaved, setLanguageSaved] = useState(false);
    const [loadingLanguage, setLoadingLanguage] = useState(true);

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
