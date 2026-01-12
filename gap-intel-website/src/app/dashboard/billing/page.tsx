"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import Navbar from "@/components/Navbar";
import { CreditCard, CheckCircle, AlertCircle, ExternalLink, Loader2 } from "lucide-react";
import Link from "next/link";

interface Subscription {
    tier: string;
    status: string;
    analyses_this_month: number;
    current_period_end: string | null;
    stripe_customer_id: string | null;
}

export default function BillingPage() {
    const { user } = useAuth();
    const [subscription, setSubscription] = useState<Subscription | null>(null);
    const [loading, setLoading] = useState(true);
    const [portalLoading, setPortalLoading] = useState(false);

    useEffect(() => {
        fetchSubscription();
    }, []);

    const fetchSubscription = async () => {
        try {
            const res = await fetch("/api/user/subscription");
            if (res.ok) {
                const data = await res.json();
                setSubscription(data);
            }
        } catch (error) {
            console.error("Error fetching subscription:", error);
        } finally {
            setLoading(false);
        }
    };

    const openCustomerPortal = async () => {
        setPortalLoading(true);
        try {
            const res = await fetch("/api/billing/portal", {
                method: "POST",
            });
            const data = await res.json();
            if (data.url) {
                window.location.href = data.url;
            }
        } catch (error) {
            console.error("Error opening customer portal:", error);
        } finally {
            setPortalLoading(false);
        }
    };
    const plans = [
        {
            name: "Starter",
            price: "$29",
            tier: "starter",
            features: ["1 analysis/month", "CTR prediction", "Basic optimizer"],
        },
        {
            name: "Pro",
            price: "$59",
            tier: "pro",
            popular: true,
            features: ["5 analyses/month", "ML-powered insights", "Competitor tracking", "Publish optimizer"],
        },
        {
            name: "Enterprise",
            price: "$129",
            tier: "enterprise",
            features: ["25 analyses/month", "API access", "White-label reports", "Team seats"],
        },
    ];

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

    return (
        <div className="min-h-screen bg-[#FAFAFA] text-slate-900">
            <Navbar />

            <main className="pt-32 pb-12 px-6">
                <div className="max-w-4xl mx-auto">
                    {/* Header */}
                    <div className="mb-12">
                        <h1 className="text-4xl font-serif font-medium text-slate-900 mb-2">Billing & Subscription</h1>
                        <p className="text-lg text-slate-500">Manage your plan, payment methods, and invoices.</p>
                    </div>

                    {/* Current Plan */}
                    <div className="bg-white rounded-[32px] border border-slate-100 shadow-xl shadow-slate-200/50 p-8 mb-12">
                        <div className="flex flex-col md:flex-row items-start justify-between gap-6">
                            <div>
                                <h2 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-2">Current Plan</h2>
                                <div className="flex items-center gap-4 mb-2">
                                    <span className="text-4xl font-serif font-medium text-slate-900 capitalize">
                                        {subscription?.tier || "Free"}
                                    </span>
                                    {subscription?.status === "active" && (
                                        <span className="px-3 py-1 bg-green-50 text-green-700 text-xs font-bold uppercase tracking-wider rounded-full border border-green-100">
                                            Active
                                        </span>
                                    )}
                                    {subscription?.status === "cancelled" && (
                                        <span className="px-3 py-1 bg-red-50 text-red-700 text-xs font-bold uppercase tracking-wider rounded-full border border-red-100">
                                            Cancelled
                                        </span>
                                    )}
                                </div>
                                {subscription?.current_period_end && (
                                    <p className="text-slate-500">
                                        {subscription.status === "cancelled" ? "Access until" : "Renews"}{" "}
                                        {new Date(subscription.current_period_end).toLocaleDateString()}
                                    </p>
                                )}
                            </div>

                            {subscription?.stripe_customer_id && (
                                <button
                                    onClick={openCustomerPortal}
                                    disabled={portalLoading}
                                    className="h-12 px-6 bg-slate-900 text-white rounded-full font-medium hover:bg-slate-800 transition shadow-lg shadow-slate-900/10 flex items-center gap-2 disabled:opacity-70"
                                >
                                    {portalLoading ? (
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                        <ExternalLink className="w-4 h-4" />
                                    )}
                                    Manage Subscription
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Upgrade Options */}
                    {(subscription?.tier === "free" || !subscription) && (
                        <div className="mb-12">
                            <h2 className="text-2xl font-serif font-medium text-slate-900 mb-6">Upgrade Your Plan</h2>
                            <div className="grid md:grid-cols-3 gap-6">
                                {plans.map((plan) => (
                                    <div
                                        key={plan.tier}
                                        className={`relative bg-white rounded-2xl border p-6 ${plan.popular
                                            ? "border-slate-900 shadow-xl"
                                            : "border-slate-100 shadow-sm"
                                            }`}
                                    >
                                        {plan.popular && (
                                            <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-slate-900 text-white text-xs font-bold tracking-wider uppercase rounded-full">
                                                Popular
                                            </span>
                                        )}
                                        <h3 className="text-lg font-medium text-slate-900">{plan.name}</h3>
                                        <div className="flex items-baseline gap-1 mt-2 mb-4">
                                            <span className="text-3xl font-serif font-medium text-slate-900">{plan.price}</span>
                                            <span className="text-slate-500">/mo</span>
                                        </div>
                                        <ul className="space-y-3 mb-6">
                                            {plan.features.map((feature) => (
                                                <li key={feature} className="flex items-center gap-2 text-sm text-slate-600">
                                                    <CheckCircle className="w-4 h-4 text-slate-900" />
                                                    {feature}
                                                </li>
                                            ))}
                                        </ul>
                                        <Link
                                            href="/pricing"
                                            className={`block w-full h-10 flex items-center justify-center rounded-full font-medium transition ${plan.popular
                                                ? "bg-slate-900 text-white hover:bg-slate-800"
                                                : "bg-slate-100 text-slate-900 hover:bg-slate-200"
                                                }`}
                                        >
                                            Upgrade
                                        </Link>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Usage */}
                    <div className="bg-white rounded-[32px] border border-slate-100 shadow-xl shadow-slate-200/50 p-8">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-medium text-slate-900">Monthly Usage</h2>
                            <span className="font-serif text-2xl font-medium text-slate-900">
                                {subscription?.analyses_this_month || 0}
                                <span className="text-slate-300 mx-2">/</span>
                                <span className="text-slate-400">
                                    {subscription?.tier === "starter" ? "1" : subscription?.tier === "pro" ? "5" : subscription?.tier === "enterprise" ? "25" : "0"}
                                </span>
                            </span>
                        </div>
                        <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-slate-900 rounded-full"
                                style={{
                                    width: `${Math.min(
                                        100,
                                        ((subscription?.analyses_this_month || 0) /
                                            (subscription?.tier === "starter"
                                                ? 1
                                                : subscription?.tier === "pro"
                                                    ? 5
                                                    : subscription?.tier === "enterprise"
                                                        ? 25
                                                        : 1)) *
                                        100
                                    )}%`,
                                }}
                            ></div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
