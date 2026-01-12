"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Check, Star, Zap, Shield, Crown, BarChart3, Sparkles, TrendingUp } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import Navbar from "@/components/Navbar";
import { motion } from "framer-motion";

interface PricingTier {
    name: string;
    price: string;
    period: string;
    description: string;
    features: string[];
    highlighted?: boolean;
    badge?: string;
    cta: string;
    priceId?: string;
}

const pricingTiers: PricingTier[] = [
    {
        name: "Starter",
        price: "$29",
        period: "/month",
        description: "Perfect for new creators testing the waters",
        features: [
            "1 analysis per month",
            "CTR prediction engine",
            "Thumbnail optimization tips",
            "3 competitor channels",
            "10 gap opportunities per video",
            "Email support"
        ],
        cta: "Start Free Trial",
        priceId: "price_starter"
    },
    {
        name: "Pro",
        price: "$59",
        period: "/month",
        description: "For growing creators serious about growth",
        badge: "MOST POPULAR",
        highlighted: true,
        features: [
            "5 analyses per month",
            "ML-powered CTR prediction",
            "Advanced thumbnail optimizer",
            "Views velocity forecasting",
            "10 competitor channels",
            "Content clustering insights",
            "Optimal publish time recommendations",
            "Priority email support"
        ],
        cta: "Start Pro Trial",
        priceId: "price_pro"
    },
    {
        name: "Enterprise",
        price: "$129",
        period: "/month",
        description: "For agencies and multi-channel creators",
        badge: "BEST VALUE",
        features: [
            "25 analyses per month",
            "Everything in Pro, plus:",
            "100 competitor channels",
            "Team collaboration (10 seats)",
            "Full API access",
            "White-label reports",
            "Custom branding",
            "Priority support"
        ],
        cta: "Start Enterprise",
        priceId: "price_enterprise"
    }
];

const featureComparison = [
    { feature: "Video Analyses", starter: "1/month", pro: "5/month", enterprise: "25/month" },
    { feature: "Gap Opportunities", starter: "10/video", pro: "Unlimited", enterprise: "Unlimited" },
    { feature: "CTR Prediction", starter: "Included", pro: "Included", enterprise: "Included" },
    { feature: "Thumbnail Optimizer", starter: "Basic", pro: "Advanced", enterprise: "Advanced" },
    { feature: "Views Forecasting", starter: "—", pro: "Included", enterprise: "Included" },
    { feature: "Competitor Tracking", starter: "3 channels", pro: "10 channels", enterprise: "100 channels" },
    { feature: "Content Clustering", starter: "—", pro: "Included", enterprise: "Included" },
    { feature: "Publish Time Optimizer", starter: "—", pro: "Included", enterprise: "Included" },
    { feature: "Team Members", starter: "—", pro: "—", enterprise: "10 seats" },
    { feature: "API Access", starter: "—", pro: "—", enterprise: "Included" },
    { feature: "White-label Reports", starter: "—", pro: "—", enterprise: "Included" },
];

export default function PricingPage() {
    const { user } = useAuth();
    const router = useRouter();
    const [isAnnual, setIsAnnual] = useState(false);
    const [loading, setLoading] = useState<string | null>(null);
    const [currency, setCurrency] = useState<'USD' | 'EUR' | 'GBP' | 'CHF' | 'AUD' | 'CAD'>('USD');

    // Currency Detection
    useEffect(() => {
        try {
            const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
            console.log("Detected Timezone:", timeZone);

            // Specific overrides first
            if (timeZone === 'Europe/London' || timeZone === 'Europe/Dublin') {
                setCurrency('GBP');
            } else if (timeZone === 'Europe/Zurich' || timeZone.includes('Zurich')) {
                setCurrency('CHF');
            } else if (timeZone.startsWith('Australia/')) {
                setCurrency('AUD');
            } else if (timeZone.startsWith('America/Toronto') || timeZone.startsWith('America/Vancouver') || timeZone.startsWith('America/Edmonton') || timeZone.includes('Canada')) {
                setCurrency('CAD');
            }
            // Broad regions last
            else if (timeZone.startsWith('Europe/')) {
                setCurrency('EUR');
            } else {
                setCurrency('USD');
            }
        } catch (e) {
            console.error("Currency detection failed:", e);
            setCurrency('USD'); // Fallback
        }
    }, []);

    const PRICING_MAP = {
        USD: { symbol: '$', Starter: 29, Pro: 59, Enterprise: 129 },
        EUR: { symbol: '€', Starter: 29, Pro: 59, Enterprise: 129 },
        GBP: { symbol: '£', Starter: 25, Pro: 49, Enterprise: 109 },
        CHF: { symbol: 'CHF ', Starter: 29, Pro: 59, Enterprise: 129 },
        AUD: { symbol: 'A$', Starter: 45, Pro: 89, Enterprise: 199 },
        CAD: { symbol: 'C$', Starter: 39, Pro: 79, Enterprise: 179 },
    };

    const getPrice = (tierName: string) => {
        const config = PRICING_MAP[currency];
        const basePrice = config[tierName as keyof typeof config] as number;

        if (isAnnual) {
            return `${config.symbol}${Math.round(basePrice * 0.8)}`;
        }
        return `${config.symbol}${basePrice}`;
    };

    const handleSubscribe = async (tier: PricingTier) => {
        // Require authentication before checkout
        if (!user) {
            router.push("/login?redirect=/pricing");
            return;
        }

        setLoading(tier.name);

        try {
            const response = await fetch("/api/checkout", { // Fixed endpoint from create-subscription to checkout
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    tier: tier.name.toLowerCase(), // Use sanitized tier name for API
                    isAnnual,
                    email: user.email,
                    channelName: user.user_metadata?.channel_name || 'unknown'
                }),
            });

            const data = await response.json();

            if (data.url) {
                window.location.href = data.url;
            } else {
                console.error("No checkout URL returned", data);
            }
        } catch (error) {
            console.error("Subscription error:", error);
        } finally {
            setLoading(null);
        }
    };

    return (
        <div className="min-h-screen bg-[#FAFAFA] text-slate-900 selection:bg-blue-100 selection:text-blue-900">
            <Navbar />

            {/* Header */}
            <div className="pt-32 pb-20 px-6 text-center">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8 }}
                >
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white border border-slate-200 shadow-sm text-sm font-medium text-slate-600 mb-8 backdrop-blur-sm mx-auto">
                        <Sparkles className="w-4 h-4 text-purple-500" />
                        <span className="bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent font-semibold">Premium Intelligence</span>
                    </div>

                    <h1 className="text-5xl md:text-6xl font-serif font-medium tracking-tight text-slate-900 mb-6">
                        Choose your growth plan
                    </h1>

                    <p className="text-xl text-slate-500 max-w-2xl mx-auto mb-12 leading-relaxed font-light">
                        Unlock data-driven insights to outperform your niche <br className="hidden md:block" /> and scale your channel faster.
                    </p>

                    {/* Annual Toggle */}
                    <div className="flex items-center justify-center gap-4 bg-white p-2 rounded-full border border-slate-100 shadow-sm w-fit mx-auto">
                        <span className={`text-sm font-medium px-4 py-1.5 rounded-full transition-colors cursor-pointer ${!isAnnual ? "bg-slate-900 text-white" : "text-slate-500 hover:text-slate-700"}`} onClick={() => setIsAnnual(false)}>Monthly</span>
                        <span className={`text-sm font-medium px-4 py-1.5 rounded-full transition-colors cursor-pointer ${isAnnual ? "bg-slate-900 text-white" : "text-slate-500 hover:text-slate-700"}`} onClick={() => setIsAnnual(true)}>
                            Annual <span className="text-emerald-500 font-normal ml-1 text-xs">(-20%)</span>
                        </span>
                    </div>
                </motion.div>
            </div>

            {/* Pricing Cards */}
            <div className="max-w-7xl mx-auto px-6 pb-20">
                <div className="grid md:grid-cols-3 gap-8 items-start">
                    {pricingTiers.map((tier, index) => (
                        <motion.div
                            key={tier.name}
                            initial={{ opacity: 0, y: 30 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: index * 0.1 }}
                            viewport={{ once: true }}
                            className={`relative rounded-[32px] p-8 flex flex-col h-full ${tier.highlighted
                                ? "bg-slate-900 text-white shadow-2xl shadow-slate-900/10 md:-mt-8 md:mb-8 ring-1 ring-white/10"
                                : "bg-white border border-slate-100 shadow-xl shadow-slate-200/50 text-slate-900"
                                }`}
                        >
                            {tier.badge && (
                                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                                    <span className="px-4 py-1 bg-gradient-to-r from-purple-500 to-indigo-500 text-white text-xs font-bold tracking-wider uppercase rounded-full shadow-lg">
                                        {tier.badge}
                                    </span>
                                </div>
                            )}

                            <div className="mb-8">
                                <h3 className={`text-2xl font-serif font-medium mb-2 ${tier.highlighted ? "text-white" : "text-slate-900"}`}>{tier.name}</h3>
                                <div className="flex items-baseline gap-1 mb-4">
                                    <span className={`text-5xl font-medium tracking-tight ${tier.highlighted ? "text-white" : "text-slate-900"}`}>
                                        {getPrice(tier.name)}
                                    </span>
                                    <span className={`text-lg ${tier.highlighted ? "text-slate-400" : "text-slate-400"}`}>{tier.period}</span>
                                </div>
                                <p className={`text-sm leading-relaxed ${tier.highlighted ? "text-slate-300" : "text-slate-500"}`}>{tier.description}</p>
                            </div>

                            <ul className="space-y-4 mb-8 flex-1">
                                {tier.features.map((feature, i) => (
                                    <li key={i} className="flex items-start gap-3">
                                        <div className={`mt-0.5 rounded-full p-0.5 ${tier.highlighted ? "bg-white/10 text-white" : "bg-slate-100 text-slate-700"}`}>
                                            <Check className="w-3.5 h-3.5" strokeWidth={3} />
                                        </div>
                                        <span className={`text-sm font-medium ${tier.highlighted ? "text-slate-200" : "text-slate-600"}`}>{feature}</span>
                                    </li>
                                ))}
                            </ul>

                            <button
                                onClick={() => handleSubscribe(tier)}
                                disabled={loading === tier.name}
                                className={`w-full h-14 rounded-full font-medium text-lg transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] ${tier.highlighted
                                    ? "bg-white text-slate-900 hover:bg-slate-100 border border-transparent"
                                    : "bg-slate-900 text-white hover:bg-slate-800 hover:shadow-lg"
                                    } disabled:opacity-70 disabled:cursor-not-allowed`}
                            >
                                {loading === tier.name ? (
                                    <span className="flex items-center justify-center gap-2">
                                        <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
                                        Processing...
                                    </span>
                                ) : tier.cta}
                            </button>
                        </motion.div>
                    ))}
                </div>
            </div>

            {/* Feature Comparison Table */}
            <div className="max-w-5xl mx-auto px-6 pb-32">
                <div className="text-center mb-16">
                    <h2 className="text-3xl font-serif font-medium text-slate-900 mb-4">Detailed Feature Comparison</h2>
                    <p className="text-slate-500">Everything you need to know about our plans.</p>
                </div>

                <div className="bg-white rounded-[32px] border border-slate-100 shadow-xl shadow-slate-200/50 overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-slate-100 bg-slate-50/50">
                                    <th className="text-left py-6 px-8 text-slate-500 font-medium font-serif italic">Feature</th>
                                    <th className="text-center py-6 px-8 text-slate-900 font-medium">Starter</th>
                                    <th className="text-center py-6 px-8 text-purple-600 font-medium">Pro</th>
                                    <th className="text-center py-6 px-8 text-slate-900 font-medium">Enterprise</th>
                                </tr>
                            </thead>
                            <tbody>
                                {featureComparison.map((row, i) => (
                                    <tr key={i} className="border-b border-slate-50 last:border-0 hover:bg-slate-50/30 transition-colors">
                                        <td className="py-5 px-8 text-slate-600 font-medium">{row.feature}</td>
                                        <td className="text-center py-5 px-8 text-slate-500">{row.starter}</td>
                                        <td className="text-center py-5 px-8 text-slate-900 font-medium bg-purple-50/20">{row.pro}</td>
                                        <td className="text-center py-5 px-8 text-slate-500">{row.enterprise}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <footer className="py-12 px-6 border-t border-slate-200 bg-white">
                <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center text-white font-serif font-bold">G</div>
                        <span className="font-serif text-xl font-medium tracking-tight">GAP Intel</span>
                    </div>
                    <div className="text-sm text-slate-400">
                        © 2024 GAP Intel. All rights reserved.
                    </div>
                </div>
            </footer>
        </div>
    );
}
