"use client";

import { useState } from "react";
import Link from "next/link";
import { Sparkles, Menu, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface ReportHeaderProps {
    accessKey: string;
}

export default function ReportHeader({ accessKey }: ReportHeaderProps) {
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    return (
        <>
            <header className="fixed top-0 w-full bg-white/80 backdrop-blur-md border-b border-slate-100 z-50">
                <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center text-white font-serif font-bold">G</div>
                        <span className="font-serif text-xl font-medium tracking-tight">GAP Intel</span>
                    </Link>

                    {/* Desktop Nav */}
                    <div className="hidden md:flex items-center gap-3">
                        <Link href={`/viral-predictor?key=${accessKey}`}>
                            <button className="h-10 px-5 rounded-full bg-purple-600 text-white hover:bg-purple-700 transition font-medium text-sm flex items-center gap-2 shadow-lg shadow-purple-500/20">
                                <Sparkles size={16} /> Predict Viral Video
                            </button>
                        </Link>
                        <Link href="/dashboard">
                            <button className="h-10 px-5 rounded-full bg-slate-100 text-slate-600 hover:bg-slate-200 transition font-medium text-sm">Dashboard</button>
                        </Link>
                    </div>

                    {/* Mobile Hamburger */}
                    <button
                        className="md:hidden p-2 -mr-2 text-slate-600 hover:bg-slate-50 rounded-lg transition"
                        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                        aria-label="Toggle menu"
                    >
                        {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
                    </button>
                </div>
            </header>

            {/* Mobile Menu Overlay */}
            <AnimatePresence>
                {mobileMenuOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ duration: 0.2 }}
                        className="fixed inset-x-0 top-16 z-40 bg-white/95 backdrop-blur-xl md:hidden border-b border-slate-100 shadow-xl"
                    >
                        <div className="p-6 flex flex-col gap-4">
                            <Link href={`/viral-predictor?key=${accessKey}`} onClick={() => setMobileMenuOpen(false)}>
                                <button className="w-full h-12 rounded-xl bg-purple-600 text-white font-medium text-lg flex items-center justify-center gap-2 shadow-lg shadow-purple-500/20 active:scale-[0.98] transition">
                                    <Sparkles size={20} /> Predict Viral Video
                                </button>
                            </Link>
                            <Link href="/dashboard" onClick={() => setMobileMenuOpen(false)}>
                                <button className="w-full h-12 rounded-xl bg-slate-100 text-slate-900 font-medium text-lg active:scale-[0.98] transition">
                                    Dashboard
                                </button>
                            </Link>
                            <Link href="/" onClick={() => setMobileMenuOpen(false)}>
                                <button className="w-full h-12 rounded-xl border border-slate-200 text-slate-600 font-medium text-lg active:scale-[0.98] transition">
                                    Home
                                </button>
                            </Link>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
}
