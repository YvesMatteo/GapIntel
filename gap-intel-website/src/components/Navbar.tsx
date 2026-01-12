"use client";

import Image from "next/image";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { useState, useRef, useEffect } from "react";
import { Sparkles } from "lucide-react";

export default function Navbar() {
    const { user, loading, signOut } = useAuth();
    const [menuOpen, setMenuOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);

    // Close menu when clicking outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setMenuOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const handleSignOut = async () => {
        await signOut();
        window.location.href = "/";
    };

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 bg-white/70 backdrop-blur-xl border-b border-slate-200/50">
            <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                {/* Logo */}
                <Link href="/" className="flex items-center gap-2 group">
                    <Image
                        src="/logo.png"
                        alt="GapIntel"
                        width={150}
                        height={40}
                        className="h-10 w-auto object-contain group-hover:scale-105 transition-transform"
                        priority
                    />
                </Link>

                {/* Navigation Links */}
                <div className="flex items-center gap-8">
                    <Link
                        href="/#features"
                        className="text-sm font-medium text-slate-500 hover:text-slate-900 transition hidden md:block"
                    >
                        Features
                    </Link>
                    <Link
                        href="/pricing"
                        className="text-sm font-medium text-slate-500 hover:text-slate-900 transition hidden md:block"
                    >
                        Pricing
                    </Link>
                    <Link
                        className="text-sm font-medium text-purple-600 hover:text-purple-700 bg-purple-50 px-3 py-1.5 rounded-full transition hidden md:flex items-center gap-1.5 border border-purple-100"
                    >
                        Viral Predictor <Sparkles size={14} fill="currentColor" className="text-purple-500" />
                    </Link>

                    {loading ? (
                        <div className="w-8 h-8 rounded-full bg-slate-100 animate-pulse"></div>
                    ) : user ? (
                        /* User Menu */
                        <div className="relative" ref={menuRef}>
                            <button
                                onClick={() => setMenuOpen(!menuOpen)}
                                className="flex items-center gap-2 p-1 pl-2 pr-1 rounded-full border border-slate-200 hover:bg-slate-50 transition bg-white"
                            >
                                <span className="text-sm font-medium text-slate-700">Account</span>
                                {user.user_metadata?.avatar_url ? (
                                    <Image
                                        src={user.user_metadata.avatar_url}
                                        alt={user.user_metadata.full_name || "User"}
                                        width={28}
                                        height={28}
                                        className="rounded-full"
                                    />
                                ) : (
                                    <div className="w-7 h-7 rounded-full bg-slate-900 flex items-center justify-center text-white text-xs font-medium">
                                        {(user.email?.[0] || "U").toUpperCase()}
                                    </div>
                                )}
                            </button>

                            {menuOpen && (
                                <div className="absolute right-0 mt-2 w-56 bg-white/90 backdrop-blur-xl rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-100 py-2 animate-in fade-in slide-in-from-top-2 duration-200">
                                    <div className="px-4 py-3 border-b border-slate-100/50">
                                        <p className="text-sm font-medium text-slate-900 truncate">
                                            {user.user_metadata?.full_name || "User"}
                                        </p>
                                        <p className="text-xs text-slate-500 truncate">{user.email}</p>
                                    </div>
                                    <Link
                                        href="/dashboard"
                                        className="block px-4 py-2 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition"
                                        onClick={() => setMenuOpen(false)}
                                    >
                                        Dashboard
                                    </Link>
                                    <Link
                                        href="/dashboard/billing"
                                        className="block px-4 py-2 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition"
                                        onClick={() => setMenuOpen(false)}
                                    >
                                        Billing
                                    </Link>
                                    <Link
                                        href="/dashboard/settings"
                                        className="block px-4 py-2 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition"
                                        onClick={() => setMenuOpen(false)}
                                    >
                                        Settings
                                    </Link>
                                    <div className="h-px bg-slate-100 my-2" />
                                    <button
                                        onClick={handleSignOut}
                                        className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition rounded-lg"
                                    >
                                        Sign out
                                    </button>
                                </div>
                            )}
                        </div>
                    ) : (
                        /* Login Button */
                        <div className="flex items-center gap-4">
                            <Link
                                href="/login"
                                className="text-sm font-medium text-slate-600 hover:text-slate-900 transition"
                            >
                                Login
                            </Link>
                            <Link
                                href="/signup"
                                className="px-5 py-2.5 bg-[#1c1c1e] text-white text-sm font-medium rounded-full hover:scale-105 hover:shadow-lg transition-all duration-300"
                            >
                                Get Started
                            </Link>
                        </div>
                    )}
                </div>
            </div>
        </nav>
    );
}
