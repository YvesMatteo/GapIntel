"use client";

import Image from "next/image";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { useState, useRef, useEffect } from "react";
import { Sparkles, Menu, X } from "lucide-react";

export default function Navbar() {
    const { user, loading, signOut } = useAuth();
    const [menuOpen, setMenuOpen] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
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
        <>
            <nav className="fixed top-0 left-0 right-0 z-50 bg-white/70 backdrop-blur-xl border-b border-slate-200/50">
                <div className="max-w-7xl mx-auto px-4 md:px-6 py-3 md:py-4 flex items-center justify-between">
                    {/* Logo */}
                    <Link href="/" className="flex items-center gap-2 group">
                        <Image
                            src="/logo.png"
                            alt="GapIntel"
                            width={150}
                            height={40}
                            className="h-8 md:h-10 w-auto object-contain group-hover:scale-105 transition-transform"
                            priority
                        />
                    </Link>

                    {/* Desktop Navigation Links */}
                    <div className="hidden md:flex items-center gap-8">
                        <Link
                            href="/#features"
                            className="text-sm font-medium text-slate-500 hover:text-slate-900 transition"
                        >
                            Features
                        </Link>
                        <Link
                            href="/pricing"
                            className="text-sm font-medium text-slate-500 hover:text-slate-900 transition"
                        >
                            Pricing
                        </Link>
                        <Link
                            href="/viral-predictor"
                            className="text-sm font-medium text-purple-600 hover:text-purple-700 bg-purple-50 px-3 py-1.5 rounded-full transition flex items-center gap-1.5 border border-purple-100"
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

                    {/* Mobile: Account/Login + Hamburger */}
                    <div className="flex md:hidden items-center gap-3">
                        {loading ? (
                            <div className="w-8 h-8 rounded-full bg-slate-100 animate-pulse"></div>
                        ) : user ? (
                            <Link href="/dashboard" className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-slate-200 bg-white text-sm font-medium text-slate-700">
                                {user.user_metadata?.avatar_url ? (
                                    <Image
                                        src={user.user_metadata.avatar_url}
                                        alt=""
                                        width={20}
                                        height={20}
                                        className="rounded-full"
                                    />
                                ) : (
                                    <div className="w-5 h-5 rounded-full bg-slate-900 flex items-center justify-center text-white text-[10px] font-medium">
                                        {(user.email?.[0] || "U").toUpperCase()}
                                    </div>
                                )}
                            </Link>
                        ) : (
                            <Link
                                href="/login"
                                className="text-sm font-medium text-slate-600"
                            >
                                Login
                            </Link>
                        )}
                        <button
                            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                            className="p-2 rounded-lg hover:bg-slate-100 transition"
                            aria-label="Toggle menu"
                        >
                            {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
                        </button>
                    </div>
                </div>
            </nav>

            {/* Mobile Menu Overlay */}
            {mobileMenuOpen && (
                <div className="fixed inset-x-0 top-[57px] bottom-0 z-40 bg-white/95 backdrop-blur-xl md:hidden overflow-y-auto">
                    <div className="p-6 space-y-2">
                        <Link
                            href="/#features"
                            onClick={() => setMobileMenuOpen(false)}
                            className="block py-3 px-4 text-lg font-medium text-slate-700 hover:bg-slate-50 rounded-xl transition"
                        >
                            Features
                        </Link>
                        <Link
                            href="/pricing"
                            onClick={() => setMobileMenuOpen(false)}
                            className="block py-3 px-4 text-lg font-medium text-slate-700 hover:bg-slate-50 rounded-xl transition"
                        >
                            Pricing
                        </Link>
                        <Link
                            href="/viral-predictor"
                            onClick={() => setMobileMenuOpen(false)}
                            className="block py-3 px-4 text-lg font-medium text-purple-600 bg-purple-50 rounded-xl transition"
                        >
                            <span className="flex items-center gap-2">
                                Viral Predictor <Sparkles size={16} fill="currentColor" />
                            </span>
                        </Link>

                        <div className="h-px bg-slate-100 my-4" />

                        {user ? (
                            <>
                                <Link
                                    href="/dashboard"
                                    onClick={() => setMobileMenuOpen(false)}
                                    className="block py-3 px-4 text-lg font-medium text-slate-700 hover:bg-slate-50 rounded-xl transition"
                                >
                                    Dashboard
                                </Link>
                                <Link
                                    href="/dashboard/billing"
                                    onClick={() => setMobileMenuOpen(false)}
                                    className="block py-3 px-4 text-lg font-medium text-slate-700 hover:bg-slate-50 rounded-xl transition"
                                >
                                    Billing
                                </Link>
                                <Link
                                    href="/dashboard/settings"
                                    onClick={() => setMobileMenuOpen(false)}
                                    className="block py-3 px-4 text-lg font-medium text-slate-700 hover:bg-slate-50 rounded-xl transition"
                                >
                                    Settings
                                </Link>
                                <button
                                    onClick={() => { handleSignOut(); setMobileMenuOpen(false); }}
                                    className="w-full text-left py-3 px-4 text-lg font-medium text-red-600 hover:bg-red-50 rounded-xl transition"
                                >
                                    Sign out
                                </button>
                            </>
                        ) : (
                            <div className="pt-4 space-y-3">
                                <Link
                                    href="/signup"
                                    onClick={() => setMobileMenuOpen(false)}
                                    className="block w-full py-3 px-4 text-center text-lg font-medium bg-slate-900 text-white rounded-xl"
                                >
                                    Get Started
                                </Link>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </>
    );
}
