"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { Eye, EyeOff, Check, X, Loader2 } from "lucide-react";

// Password strength checker
function getPasswordStrength(password: string): { score: number; feedback: string[] } {
    const feedback: string[] = [];
    let score = 0;

    if (password.length >= 8) score++;
    else feedback.push("At least 8 characters");

    if (/[a-z]/.test(password)) score++;
    else feedback.push("Lowercase letter");

    if (/[A-Z]/.test(password)) score++;
    else feedback.push("Uppercase letter");

    if (/[0-9]/.test(password)) score++;
    else feedback.push("Number");

    if (/[^a-zA-Z0-9]/.test(password)) score++;
    else feedback.push("Special character");

    return { score, feedback };
}

function AuthContent() {
    const { user, loading, signInWithGoogle, signUpWithEmail, signInWithEmail, resetPassword } = useAuth();
    const router = useRouter();
    const searchParams = useSearchParams();

    const [mode, setMode] = useState<"register" | "login" | "forgot">("register");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const redirect = searchParams.get("redirect") || "/dashboard";
    const fromPricing = redirect === "/pricing";
    const passwordStrength = getPasswordStrength(password);

    useEffect(() => {
        if (!loading && user) {
            router.push(redirect);
        }
    }, [user, loading, router, redirect]);

    const handleEmailAuth = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        setError(null);
        setSuccess(null);

        try {
            if (mode === "register") {
                // Validate password strength
                if (passwordStrength.score < 3) {
                    setError("Please use a stronger password");
                    setIsSubmitting(false);
                    return;
                }

                // Check password match
                if (password !== confirmPassword) {
                    setError("Passwords do not match");
                    setIsSubmitting(false);
                    return;
                }

                const { error } = await signUpWithEmail(email, password);
                if (error) {
                    setError(error.message);
                } else {
                    setSuccess("Check your email to verify your account!");
                }
            } else if (mode === "login") {
                const { error } = await signInWithEmail(email, password);
                if (error) {
                    if (error.message.includes("Email not confirmed")) {
                        setError("Please verify your email before signing in");
                    } else if (error.message.includes("Invalid login credentials")) {
                        setError("Invalid email or password");
                    } else {
                        setError(error.message);
                    }
                }
            } else if (mode === "forgot") {
                const { error } = await resetPassword(email);
                if (error) {
                    setError(error.message);
                } else {
                    setSuccess("Check your email for a password reset link");
                }
            }
        } catch (err) {
            setError("An unexpected error occurred");
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleGoogleSignIn = async () => {
        setIsSubmitting(true);
        setError(null);
        try {
            await signInWithGoogle();
        } catch (err) {
            setError("Failed to sign in with Google");
            setIsSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-[#fafbfc] flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-slate-900" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-b from-[#fafbfc] to-white flex items-center justify-center px-4 py-12">
            <div className="max-w-md w-full">
                {/* Logo */}
                <div className="text-center mb-8">
                    <Link href="/" className="inline-flex items-center gap-2">
                        <Image
                            src="/logo.png"
                            alt="GAP Intel"
                            width={48}
                            height={48}
                            className="rounded-lg"
                        />
                        <span className="text-2xl font-bold text-gray-900">GAP Intel</span>
                    </Link>
                </div>

                {/* Auth Card */}
                <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
                    {/* Title */}
                    <h1 className="text-2xl font-bold text-gray-900 text-center mb-2">
                        {mode === "register" ? "Create your account" : mode === "login" ? "Welcome back" : "Reset password"}
                    </h1>
                    <p className="text-gray-500 text-center mb-6">
                        {mode === "register"
                            ? "Start discovering your content gaps"
                            : mode === "login"
                                ? "Sign in to access your dashboard"
                                : "Enter your email to reset your password"}
                    </p>

                    {/* Redirect Notice */}
                    {fromPricing && (
                        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-blue-700 text-sm">
                            Please sign in to complete your purchase.
                        </div>
                    )}

                    {/* Error/Success Messages */}
                    {error && (
                        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                            {error}
                        </div>
                    )}
                    {success && (
                        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
                            {success}
                        </div>
                    )}

                    {/* Google Sign In */}
                    <button
                        onClick={handleGoogleSignIn}
                        disabled={isSubmitting}
                        className="w-full flex items-center justify-center gap-3 px-4 py-3 bg-white border-2 border-gray-200 rounded-xl text-gray-700 font-medium hover:bg-gray-50 hover:border-gray-300 transition-all disabled:opacity-50 disabled:cursor-not-allowed mb-6"
                    >
                        {isSubmitting ? (
                            <Loader2 className="h-5 w-5 animate-spin" />
                        ) : (
                            <svg className="w-5 h-5" viewBox="0 0 24 24">
                                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                            </svg>
                        )}
                        <span>Continue with Google</span>
                    </button>

                    {/* Divider */}
                    <div className="relative mb-6">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-gray-200"></div>
                        </div>
                        <div className="relative flex justify-center text-sm">
                            <span className="px-4 bg-white text-gray-500">or continue with email</span>
                        </div>
                    </div>

                    {/* Email Form */}
                    <form onSubmit={handleEmailAuth} className="space-y-4">
                        {/* Email */}
                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                                Email
                            </label>
                            <input
                                id="email"
                                type="email"
                                required
                                autoComplete="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-slate-900 focus:border-transparent transition"
                                placeholder="you@example.com"
                            />
                        </div>

                        {/* Password (not for forgot mode) */}
                        {mode !== "forgot" && (
                            <div>
                                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                                    Password
                                </label>
                                <div className="relative">
                                    <input
                                        id="password"
                                        type={showPassword ? "text" : "password"}
                                        required
                                        autoComplete={mode === "register" ? "new-password" : "current-password"}
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-slate-900 focus:border-transparent transition pr-12"
                                        placeholder="••••••••"
                                        minLength={8}
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                                    >
                                        {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                    </button>
                                </div>

                                {/* Password Strength (register only) */}
                                {mode === "register" && password && (
                                    <div className="mt-2">
                                        <div className="flex gap-1 mb-1">
                                            {[1, 2, 3, 4, 5].map((level) => (
                                                <div
                                                    key={level}
                                                    className={`h-1 flex-1 rounded-full transition-colors ${passwordStrength.score >= level
                                                        ? level <= 2
                                                            ? "bg-red-400"
                                                            : level <= 3
                                                                ? "bg-transparent"
                                                                : "bg-green-500"
                                                        : "bg-gray-200"
                                                        }`}
                                                />
                                            ))}
                                        </div>
                                        {passwordStrength.feedback.length > 0 && (
                                            <p className="text-xs text-gray-500">
                                                Missing: {passwordStrength.feedback.join(", ")}
                                            </p>
                                        )}
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Confirm Password (register only) */}
                        {mode === "register" && (
                            <div>
                                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
                                    Confirm Password
                                </label>
                                <div className="relative">
                                    <input
                                        id="confirmPassword"
                                        type={showPassword ? "text" : "password"}
                                        required
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        className={`w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-slate-900 focus:border-transparent transition pr-12 ${confirmPassword && password !== confirmPassword
                                            ? "border-red-300"
                                            : confirmPassword && password === confirmPassword
                                                ? "border-green-500"
                                                : "border-gray-200"
                                            }`}
                                        placeholder="••••••••"
                                    />
                                    {confirmPassword && (
                                        <span className="absolute right-3 top-1/2 -translate-y-1/2">
                                            {password === confirmPassword ? (
                                                <Check className="w-5 h-5 text-green-500" />
                                            ) : (
                                                <X className="w-5 h-5 text-red-500" />
                                            )}
                                        </span>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Forgot Password Link (login only) */}
                        {mode === "login" && (
                            <div className="text-right">
                                <button
                                    type="button"
                                    onClick={() => { setMode("forgot"); setError(null); setSuccess(null); }}
                                    className="text-sm text-slate-600 hover:text-slate-900 hover:underline"
                                >
                                    Forgot password?
                                </button>
                            </div>
                        )}

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="w-full py-3 bg-[#1c1c1e] text-white font-medium rounded-full hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg shadow-slate-900/10"
                        >
                            {isSubmitting && <Loader2 className="h-5 w-5 animate-spin" />}
                            {mode === "register" ? "Create Account" : mode === "login" ? "Sign In" : "Send Reset Link"}
                        </button>
                    </form>

                    {/* Mode Toggle */}
                    <div className="mt-6 text-center text-sm text-gray-600">
                        {mode === "register" ? (
                            <>
                                Already have an account?{" "}
                                <button
                                    onClick={() => { setMode("login"); setError(null); setSuccess(null); }}
                                    className="text-slate-900 font-bold hover:underline"
                                >
                                    Sign in
                                </button>
                            </>
                        ) : mode === "login" ? (
                            <>
                                Don&apos;t have an account?{" "}
                                <button
                                    onClick={() => { setMode("register"); setError(null); setSuccess(null); }}
                                    className="text-slate-900 font-bold hover:underline"
                                >
                                    Create one
                                </button>
                            </>
                        ) : (
                            <>
                                Remember your password?{" "}
                                <button
                                    onClick={() => { setMode("login"); setError(null); setSuccess(null); }}
                                    className="text-slate-900 font-bold hover:underline"
                                >
                                    Sign in
                                </button>
                            </>
                        )}
                    </div>
                </div>

                {/* Security Notice */}
                <div className="mt-6 text-center">
                    <p className="text-xs text-gray-400">
                        🔒 Your data is encrypted and securely stored
                    </p>
                </div>
            </div>
        </div>
    );
}

export default function LoginPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-[#fafbfc] flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-slate-900" />
            </div>
        }>
            <AuthContent />
        </Suspense>
    );
}
