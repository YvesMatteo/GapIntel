"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Check, Star, Zap, Shield, Crown, BarChart3, Sparkles, TrendingUp, ArrowRight, CheckCircle2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import Navbar from "@/components/Navbar";
import { motion, useScroll, useTransform } from "framer-motion";

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
    color: string;
    glowColor: string;
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
        priceId: "price_starter",
        color: "blue",
        glowColor: "bg-blue-500/20"
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
        priceId: "price_pro",
        color: "purple",
        glowColor: "bg-purple-500/20"
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
        priceId: "price_enterprise",
        color: "orange",
        glowColor: "bg-orange-500/20"
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

export default function PricingPage() {
    const { user } = useAuth();
    const router = useRouter();
    const [isAnnual, setIsAnnual] = useState(false);
    const [loading, setLoading] = useState<string | null>(null);
    const [currency, setCurrency] = useState<'USD' | 'EUR' | 'GBP' | 'CHF' | 'AUD' | 'CAD'>('USD');
    const { scrollY } = useScroll();
    const y1 = useTransform(scrollY, [0, 500], [0, 100]);
    const y2 = useTransform(scrollY, [0, 500], [0, -100]);

    // Currency Detection
    useEffect(() => {
        try {
            const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

            if (timeZone === 'Europe/London' || timeZone === 'Europe/Dublin') setCurrency('GBP');
            else if (timeZone === 'Europe/Zurich' || timeZone.includes('Zurich')) setCurrency('CHF');
            else if (timeZone.startsWith('Australia/')) setCurrency('AUD');
            else if (timeZone.includes('Canada') || timeZone.startsWith('America/Toronto')) setCurrency('CAD');
            else if (timeZone.startsWith('Europe/')) setCurrency('EUR');
            else setCurrency('USD');
        } catch (e) {
            console.error("Currency detection failed:", e);
            setCurrency('USD');
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
        if (!user) {
            router.push("/login?redirect=/pricing");
            return;
        }

        setLoading(tier.name);
        try {
            const response = await fetch("/api/checkout", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    tier: tier.name.toLowerCase(),
                    isAnnual,
                    email: user.email,
                    channelName: user.user_metadata?.channel_name || 'unknown'
                }),
            });

            const data = await response.json();
            if (data.url) window.location.href = data.url;
        } catch (error) {
            console.error("Subscription error:", error);
        } finally {
            setLoading(null);
        }
    };

    return (
        <div className="min-h-screen bg-[#FAFAFA] text-slate-900 selection:bg-purple-100 selection:text-purple-900 overflow-x-hidden">
            <Navbar />

            {/* Background Gradients */}
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute top-0 opacity-30 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-[radial-gradient(circle_at_center,_var(--color-brand-light)_0%,_transparent_70%)] blur-[100px]" />
                <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-blue-50/50 rounded-full blur-3xl opacity-40 mix-blend-multiply" />
                <div className="absolute top-40 left-0 w-[400px] h-[400px] bg-purple-50/50 rounded-full blur-3xl opacity-40 mix-blend-multiply" />
            </div>

            {/* Header */}
            <div className="pt-40 pb-20 px-6 text-center relative z-10">
                <FadeIn>
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/60 border border-slate-200/60 shadow-lg shadow-slate-200/20 text-sm font-medium text-slate-600 mb-8 backdrop-blur-md mx-auto"
                    >
                        <Sparkles className="w-4 h-4 text-purple-500 fill-purple-500" />
                        <span className="bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent font-bold">Premium Intelligence</span>
                    </motion.div>

                    <h1 className="text-5xl md:text-7xl font-serif font-medium tracking-tight text-slate-900 mb-6">
                        Choose your <span className="text-transparent bg-clip-text bg-gradient-to-r from-slate-900 to-slate-700">growth plan</span>
                    </h1>

                    <p className="text-xl text-slate-500 max-w-2xl mx-auto mb-12 leading-relaxed font-light">
                        Unlock data-driven insights to outperform your niche <br className="hidden md:block" /> and scale your channel faster.
                    </p>

                    {/* Annual Toggle */}
                    <div className="flex justify-center">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="flex items-center justify-center gap-1 bg-white p-1.5 rounded-full border border-slate-200 shadow-xl shadow-slate-200/40"
                        >
                            <button
                                className={`text-sm font-bold px-6 py-2.5 rounded-full transition-all duration-300 ${!isAnnual ? "bg-slate-900 text-white shadow-md" : "text-slate-500 hover:text-slate-900 hover:bg-slate-50"}`}
                                onClick={() => setIsAnnual(false)}
                            >
                                Monthly
                            </button>
                            <button
                                className={`text-sm font-bold px-6 py-2.5 rounded-full transition-all duration-300 flex items-center gap-2 ${isAnnual ? "bg-slate-900 text-white shadow-md" : "text-slate-500 hover:text-slate-900 hover:bg-slate-50"}`}
                                onClick={() => setIsAnnual(true)}
                            >
                                Annual <span className={`text-[10px] uppercase tracking-wider font-extrabold px-1.5 py-0.5 rounded ${isAnnual ? "bg-emerald-500 text-white" : "bg-emerald-100 text-emerald-700"}`}>-20%</span>
                            </button>
                        </motion.div>
                    </div>
                </FadeIn>
            </div>

            {/* Pricing Cards */}
            <div className="max-w-7xl mx-auto px-6 pb-32 relative z-10">
                <div className="grid md:grid-cols-3 gap-8 items-start">
                    {pricingTiers.map((tier, index) => (
                        <FadeIn key={tier.name} delay={index * 0.1}>
                            <motion.div
                                whileHover={{ y: -8 }}
                                className={`relative rounded-[40px] p-8 flex flex-col h-full transition-all duration-500 group ${tier.highlighted
                                        ? "bg-slate-900 text-white shadow-2xl shadow-slate-900/30 md:-mt-8 md:mb-8 ring-1 ring-slate-800"
                                        : "bg-white/80 backdrop-blur-sm border border-slate-100 shadow-xl shadow-slate-200/50 text-slate-900 hover:shadow-2xl hover:shadow-slate-200/60 hover:bg-white"
                                    }`}
                            >
                                {/* Glow Effect for Highlighted Card */}
                                {tier.highlighted && (
                                    <div className="absolute inset-0 bg-gradient-to-b from-slate-800 to-transparent rounded-[40px] opacity-20 pointer-events-none" />
                                )}

                                {/* Background Gradient Blob */}
                                {!tier.highlighted && (
                                    <div className={`absolute top-0 right-0 w-64 h-64 ${tier.glowColor} rounded-full blur-3xl -mr-20 -mt-20 opacity-0 group-hover:opacity-100 transition-opacity duration-700`} />
                                )}

                                {tier.badge && (
                                    <div className="absolute -top-5 left-1/2 -translate-x-1/2 w-max z-20">
                                        <div className="px-4 py-1.5 bg-gradient-to-r from-purple-500 to-indigo-500 text-white text-xs font-bold tracking-wider uppercase rounded-full shadow-lg shadow-purple-500/30 flex items-center gap-1.5 border border-white/10">
                                            <Crown className="w-3.5 h-3.5 fill-white" />
                                            {tier.badge}
                                        </div>
                                    </div>
                                )}

                                <div className="mb-8 relative z-10">
                                    <h3 className={`text-2xl font-serif font-medium mb-2 ${tier.highlighted ? "text-white" : "text-slate-900"}`}>{tier.name}</h3>
                                    <div className="flex items-baseline gap-1 mb-4">
                                        <span className={`text-6xl font-medium tracking-tight ${tier.highlighted ? "text-white" : "text-slate-900"}`}>
                                            {getPrice(tier.name)}
                                        </span>
                                        <span className={`text-lg font-medium ${tier.highlighted ? "text-slate-400" : "text-slate-400"}`}>{tier.period}</span>
                                    </div>
                                    <p className={`text-sm leading-relaxed font-medium ${tier.highlighted ? "text-slate-300" : "text-slate-500"}`}>{tier.description}</p>
                                </div>

                                <div className={`h-px w-full mb-8 ${tier.highlighted ? "bg-slate-800" : "bg-slate-100"}`} />

                                <ul className="space-y-4 mb-10 flex-1 relative z-10">
                                    {tier.features.map((feature, i) => (
                                        <motion.li
                                            key={i}
                                            initial={{ opacity: 0, x: -10 }}
                                            whileInView={{ opacity: 1, x: 0 }}
                                            transition={{ delay: 0.2 + (i * 0.05) }}
                                            className="flex items-start gap-3"
                                        >
                                            <div className={`mt-0.5 rounded-full p-0.5 shrink-0 ${tier.highlighted ? "bg-emerald-500/20 text-emerald-400" : "bg-slate-100 text-slate-700"}`}>
                                                <Check className="w-3.5 h-3.5" strokeWidth={3} />
                                            </div>
                                            <span className={`text-sm font-medium ${tier.highlighted ? "text-slate-200" : "text-slate-600 group-hover:text-slate-900 transition-colors"}`}>{feature}</span>
                                        </motion.li>
                                    ))}
                                </ul>

                                <button
                                    onClick={() => handleSubscribe(tier)}
                                    disabled={loading === tier.name}
                                    className={`w-full h-14 rounded-full font-bold text-base transition-all duration-300 relative overflow-hidden group/btn ${tier.highlighted
                                        ? "bg-white text-slate-900 hover:bg-slate-50 shadow-lg shadow-white/10"
                                        : "bg-slate-900 text-white hover:bg-slate-800 hover:shadow-lg hover:shadow-slate-900/20"
                                        } disabled:opacity-70 disabled:cursor-not-allowed z-20`}
                                >
                                    <span className="relative z-10 flex items-center justify-center gap-2">
                                        {loading === tier.name ? (
                                            <>
                                                <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
                                                Processing...
                                            </>
                                        ) : (
                                            <>
                                                {tier.cta} <ArrowRight className="w-4 h-4 transition-transform group-hover/btn:translate-x-1" />
                                            </>
                                        )}
                                    </span>
                                </button>
                            </motion.div>
                        </FadeIn>
                    ))}
                </div>
            </div>

            {/* Feature Comparison Table */}
            <div className="max-w-5xl mx-auto px-6 pb-32 relative z-10">
                <FadeIn>
                    <div className="text-center mb-16">
                        <h2 className="text-3xl font-serif font-medium text-slate-900 mb-4">Detailed Feature Comparison</h2>
                        <p className="text-slate-500">Everything you need to know about our plans.</p>
                    </div>

                    <div className="bg-white rounded-[40px] border border-slate-100 shadow-2xl shadow-slate-200/50 overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full min-w-[700px]">
                                <thead>
                                    <tr className="border-b border-slate-100 bg-slate-50/50">
                                        <th className="text-left py-6 px-8 text-slate-500 font-medium font-serif italic text-lg w-1/4">Feature</th>
                                        <th className="text-center py-6 px-8 text-slate-900 font-bold w-1/4">Starter</th>
                                        <th className="text-center py-6 px-8 text-purple-600 font-bold bg-purple-50/30 w-1/4 relative">
                                            Pro
                                            <div className="absolute top-0 right-0 bottom-0 w-px bg-purple-100" />
                                            <div className="absolute top-0 left-0 bottom-0 w-px bg-purple-100" />
                                        </th>
                                        <th className="text-center py-6 px-8 text-slate-900 font-bold w-1/4">Enterprise</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {featureComparison.map((row, i) => (
                                        <tr key={i} className="border-b border-slate-50 last:border-0 hover:bg-slate-50/50 transition-colors group">
                                            <td className="py-5 px-8 text-slate-700 font-medium group-hover:text-slate-900 transition-colors">{row.feature}</td>
                                            <td className="text-center py-5 px-8 text-slate-500">{row.starter}</td>
                                            <td className="text-center py-5 px-8 text-slate-900 font-medium bg-purple-50/10 border-x border-purple-50/40 relative">
                                                {row.pro === "Included" ? (
                                                    <div className="flex justify-center"><CheckCircle2 className="w-5 h-5 text-purple-600 fill-purple-100" /></div>
                                                ) : row.pro}
                                            </td>
                                            <td className="text-center py-5 px-8 text-slate-500">
                                                {row.enterprise === "Included" ? (
                                                    <div className="flex justify-center"><CheckCircle2 className="w-5 h-5 text-slate-900 fill-slate-100" /></div>
                                                ) : row.enterprise}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </FadeIn>
            </div>

            <footer className="py-12 px-6 border-t border-slate-200 bg-white relative z-10">
                <div className="max-w-7xl mx-auto">
                    <div className="flex flex-col md:flex-row justify-between items-center gap-6">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-slate-900 flex items-center justify-center text-white font-serif font-bold text-xl shadow-lg shadow-slate-900/20">G</div>
                            <span className="font-serif text-2xl font-medium tracking-tight text-slate-900">GAP Intel</span>
                        </div>
                        <div className="text-sm text-slate-400 font-medium">
                            © 2024 GAP Intel. All rights reserved.
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    );
}
