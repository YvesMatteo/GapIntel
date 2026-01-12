"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase-browser";
import { Loader2, ArrowLeft, Save, Palette, Image as ImageIcon, Type, Link as LinkIcon, CheckCircle } from "lucide-react";
import Navbar from "@/components/Navbar";

interface Branding {
    logo_url: string | null;
    primary_color: string;
    secondary_color: string;
    accent_color: string;
    company_name: string | null;
    custom_footer_text: string | null;
    hide_gap_intel_branding: boolean;
}

const defaultBranding: Branding = {
    logo_url: null,
    primary_color: "#7cffb2",
    secondary_color: "#1a1a2e",
    accent_color: "#b8b8ff",
    company_name: null,
    custom_footer_text: null,
    hide_gap_intel_branding: false
};

export default function BrandingPage() {
    const [branding, setBranding] = useState<Branding>(defaultBranding);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [orgId, setOrgId] = useState<string | null>(null);
    const [isEnterprise, setIsEnterprise] = useState(false);

    const supabase = createClient();

    useEffect(() => {
        loadBranding();
    }, []);

    async function loadBranding() {
        try {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;

            // Check tier
            const { data: sub } = await supabase
                .from("user_subscriptions")
                .select("tier")
                .eq("user_id", user.id)
                .single();

            setIsEnterprise(sub?.tier === "enterprise");

            // Get organization
            const { data: org } = await supabase
                .from("organizations")
                .select("id")
                .eq("owner_id", user.id)
                .single();

            if (org) {
                setOrgId(org.id);

                // Get branding
                const { data: brandingData } = await supabase
                    .from("organization_branding")
                    .select("*")
                    .eq("organization_id", org.id)
                    .single();

                if (brandingData) {
                    setBranding({
                        ...defaultBranding,
                        ...brandingData
                    });
                }
            }
        } catch (err) {
            console.error("Error loading branding:", err);
        } finally {
            setLoading(false);
        }
    }

    async function saveBranding() {
        if (!orgId) return;

        setSaving(true);
        setSaved(false);

        try {
            // Check if record exists
            const { data: existing } = await supabase
                .from("organization_branding")
                .select("id")
                .eq("organization_id", orgId)
                .single();

            if (existing) {
                await supabase
                    .from("organization_branding")
                    .update(branding)
                    .eq("organization_id", orgId);
            } else {
                await supabase
                    .from("organization_branding")
                    .insert({ ...branding, organization_id: orgId });
            }

            setSaved(true);
            setTimeout(() => setSaved(false), 3000);
        } catch (err) {
            console.error("Error saving branding:", err);
        } finally {
            setSaving(false);
        }
    }

    if (loading) {
        return (
            <div className="min-h-screen bg-[#FAFAFA]">
                <Navbar />
                <div className="pt-32 flex items-center justify-center">
                    <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
                </div>
            </div>
        );
    }

    if (!isEnterprise) {
        return (
            <div className="min-h-screen bg-[#FAFAFA]">
                <Navbar />
                <main className="pt-32 pb-12 px-6">
                    <div className="max-w-4xl mx-auto text-center">
                        <div className="bg-white rounded-[32px] p-12 border border-slate-100 shadow-xl">
                            <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-6">
                                <Palette className="w-10 h-10 text-slate-400" />
                            </div>
                            <h1 className="text-3xl font-serif font-medium text-slate-900 mb-4">White-Label Branding</h1>
                            <p className="text-slate-500 mb-8 max-w-lg mx-auto">
                                Customize reports with your own branding, logo, and colors. This feature is exclusively available for Enterprise subscribers.
                            </p>
                            <Link href="/pricing" className="inline-block h-12 px-8 bg-slate-900 text-white rounded-full font-medium hover:bg-slate-800 transition flex items-center justify-center gap-2 mx-auto">
                                Upgrade to Enterprise
                            </Link>
                        </div>
                    </div>
                </main>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#FAFAFA] text-slate-900">
            <Navbar />
            <main className="pt-32 pb-12 px-6">
                <div className="max-w-4xl mx-auto">
                    {/* Header */}
                    <div className="mb-12">
                        <Link href="/dashboard" className="text-slate-500 hover:text-slate-900 text-sm font-medium mb-4 inline-flex items-center gap-1 transition-colors">
                            <ArrowLeft className="w-4 h-4" /> Back to Dashboard
                        </Link>
                        <h1 className="text-4xl font-serif font-medium text-slate-900 mb-2">White-Label Branding</h1>
                        <p className="text-lg text-slate-500">
                            Customize the look and feel of your reports for clients.
                        </p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-8">
                        {/* Branding Form */}
                        <div className="md:col-span-2 space-y-8">
                            <div className="bg-white rounded-[32px] p-8 border border-slate-100 shadow-xl shadow-slate-200/50">
                                <h3 className="text-lg font-medium text-slate-900 mb-6 flex items-center gap-2">
                                    <Type className="w-5 h-5 text-slate-400" /> Company Details
                                </h3>

                                <div className="space-y-6">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-2">Company Name</label>
                                        <input
                                            type="text"
                                            value={branding.company_name || ""}
                                            onChange={(e) => setBranding({ ...branding, company_name: e.target.value || null })}
                                            placeholder="Acme Corp"
                                            className="w-full h-12 px-4 rounded-xl border border-slate-200 focus:border-slate-900 focus:ring-0 transition bg-slate-50/50"
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-2">Logo URL</label>
                                        <div className="flex items-center gap-2">
                                            <input
                                                type="url"
                                                value={branding.logo_url || ""}
                                                onChange={(e) => setBranding({ ...branding, logo_url: e.target.value || null })}
                                                placeholder="https://example.com/logo.png"
                                                className="w-full h-12 px-4 rounded-xl border border-slate-200 focus:border-slate-900 focus:ring-0 transition bg-slate-50/50"
                                            />
                                            {branding.logo_url && (
                                                <div className="w-12 h-12 rounded-xl border border-slate-200 p-2 flex items-center justify-center bg-white">
                                                    <img src={branding.logo_url} alt="Logo" className="max-w-full max-h-full object-contain" />
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-2">Footer Text</label>
                                        <input
                                            type="text"
                                            value={branding.custom_footer_text || ""}
                                            onChange={(e) => setBranding({ ...branding, custom_footer_text: e.target.value || null })}
                                            placeholder="© 2025 Acme Corp. Confidential."
                                            className="w-full h-12 px-4 rounded-xl border border-slate-200 focus:border-slate-900 focus:ring-0 transition bg-slate-50/50"
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="bg-white rounded-[32px] p-8 border border-slate-100 shadow-xl shadow-slate-200/50">
                                <h3 className="text-lg font-medium text-slate-900 mb-6 flex items-center gap-2">
                                    <Palette className="w-5 h-5 text-slate-400" /> Color Theme
                                </h3>

                                <div className="space-y-6">
                                    {/* Primary Color */}
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-2">Primary Color</label>
                                        <div className="flex gap-3">
                                            <div className="relative w-12 h-12 rounded-xl overflow-hidden border border-slate-200 shadow-sm">
                                                <input
                                                    type="color"
                                                    value={branding.primary_color}
                                                    onChange={(e) => setBranding({ ...branding, primary_color: e.target.value })}
                                                    className="absolute inset-0 w-[150%] h-[150%] -top-[25%] -left-[25%] cursor-pointer p-0 border-0"
                                                />
                                            </div>
                                            <input
                                                type="text"
                                                value={branding.primary_color}
                                                onChange={(e) => setBranding({ ...branding, primary_color: e.target.value })}
                                                className="flex-1 h-12 px-4 rounded-xl border border-slate-200 font-mono text-sm uppercase"
                                            />
                                        </div>
                                    </div>

                                    {/* Secondary Color */}
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-2">Secondary Color</label>
                                        <div className="flex gap-3">
                                            <div className="relative w-12 h-12 rounded-xl overflow-hidden border border-slate-200 shadow-sm">
                                                <input
                                                    type="color"
                                                    value={branding.secondary_color}
                                                    onChange={(e) => setBranding({ ...branding, secondary_color: e.target.value })}
                                                    className="absolute inset-0 w-[150%] h-[150%] -top-[25%] -left-[25%] cursor-pointer p-0 border-0"
                                                />
                                            </div>
                                            <input
                                                type="text"
                                                value={branding.secondary_color}
                                                onChange={(e) => setBranding({ ...branding, secondary_color: e.target.value })}
                                                className="flex-1 h-12 px-4 rounded-xl border border-slate-200 font-mono text-sm uppercase"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="bg-white rounded-[32px] p-8 border border-slate-100 shadow-xl shadow-slate-200/50 flex items-center justify-between">
                                <div>
                                    <h3 className="text-lg font-medium text-slate-900 mb-1">Remove GAP Intel Branding</h3>
                                    <p className="text-slate-500 text-sm">Hide "Powered by GAP Intel" from all reports</p>
                                </div>
                                <label className="relative inline-flex items-center cursor-pointer">
                                    <input
                                        type="checkbox"
                                        className="sr-only peer"
                                        checked={branding.hide_gap_intel_branding}
                                        onChange={(e) => setBranding({ ...branding, hide_gap_intel_branding: e.target.checked })}
                                    />
                                    <div className="w-14 h-8 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[4px] after:left-[4px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-slate-900"></div>
                                </label>
                            </div>

                            <div className="flex items-center gap-4 pt-4">
                                <button
                                    onClick={saveBranding}
                                    disabled={saving}
                                    className="h-14 px-8 bg-slate-900 text-white rounded-full font-medium text-lg hover:shadow-xl hover:scale-[1.02] transition-all disabled:opacity-70 disabled:cursor-not-allowed flex items-center gap-2"
                                >
                                    {saving ? <Loader2 className="w-5 h-5 animate-spin" /> : <Save className="w-5 h-5" />}
                                    {saving ? "Saving Changes..." : "Save Changes"}
                                </button>
                                {saved && (
                                    <div className="flex items-center gap-2 text-green-600 font-medium animate-in fade-in slide-in-from-left-4">
                                        <CheckCircle className="w-5 h-5" /> Saved!
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Preview */}
                        <div>
                            <div className="sticky top-32">
                                <h3 className="text-lg font-medium text-slate-900 mb-6">Live Preview</h3>
                                <div className="bg-white rounded-[32px] border border-slate-100 shadow-2xl overflow-hidden min-h-[400px] flex flex-col relative"
                                    style={{ backgroundColor: branding.secondary_color }}
                                >
                                    {/* Mock Report Header */}
                                    <div className="p-8 pb-4">
                                        <div className="flex items-center gap-3 mb-8">
                                            {branding.logo_url ? (
                                                <img
                                                    src={branding.logo_url}
                                                    alt="Logo"
                                                    className="h-8 w-auto object-contain"
                                                    onError={(e) => (e.currentTarget.style.display = "none")}
                                                />
                                            ) : (
                                                <div
                                                    className="w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold"
                                                    style={{ backgroundColor: branding.primary_color, color: "#000" }}
                                                >
                                                    {branding.company_name?.charAt(0) || "C"}
                                                </div>
                                            )}
                                            <span className="font-serif font-bold text-xl text-white">
                                                {branding.company_name || "Company Name"}
                                            </span>
                                        </div>

                                        <div className="space-y-4">
                                            <div className="h-8 w-3/4 bg-white/10 rounded-lg"></div>
                                            <div className="h-4 w-1/2 bg-white/5 rounded-lg"></div>
                                        </div>
                                    </div>

                                    {/* Mock Metric Card */}
                                    <div className="mx-8 p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm">
                                        <div className="text-sm text-slate-400 mb-2 uppercase tracking-wider font-bold">Performance Score</div>
                                        <div className="text-4xl font-bold" style={{ color: branding.primary_color }}>92/100</div>
                                    </div>

                                    <div className="mt-auto p-8 border-t border-white/5">
                                        <div className="flex justify-between items-center text-xs text-slate-500">
                                            <span>{branding.custom_footer_text || "© 2025 Company Name"}</span>
                                            {!branding.hide_gap_intel_branding && (
                                                <span className="opacity-50">Powered by GAP Intel</span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

