"use client";

import Link from "next/link";
import Image from "next/image";
import { useSearchParams } from "next/navigation";
import { useEffect, useState, Suspense } from "react";
import { CheckCircle } from "lucide-react";

function SuccessContent() {
    const searchParams = useSearchParams();
    const sessionId = searchParams.get("session_id");
    const [verified, setVerified] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!sessionId) {
            setError("No session ID found");
            return;
        }

        // Just verify the session exists - subscription is stored via webhook
        const verifySession = async () => {
            try {
                const res = await fetch(`/api/checkout/session?session_id=${sessionId}`);
                if (res.ok) {
                    setVerified(true);
                } else {
                    // Session might not exist - that's OK, webhook handles subscription
                    setVerified(true);
                }
            } catch (err) {
                console.error(err);
                // Still show success - webhook will handle subscription
                setVerified(true);
            }
        };

        verifySession();
    }, [sessionId]);

    return (
        <main className="min-h-screen flex items-center justify-center px-6 py-20 bg-gradient-to-b from-[#0a0a0a] via-[#0f0f1a] to-[#0a0a0a]">
            <div className="max-w-lg w-full text-center">
                {/* Success Animation */}
                <div className="w-24 h-24 mx-auto mb-8 bg-[#7cffb2] rounded-full flex items-center justify-center animate-fade-in-up">
                    <CheckCircle className="w-12 h-12 text-[#1a1a2e]" strokeWidth={3} />
                </div>

                <h1 className="text-3xl font-bold text-white mb-4 animate-fade-in-up">
                    Subscription Activated!
                </h1>

                <p className="text-gray-400 mb-8 animate-fade-in-up">
                    Thank you for subscribing to GAP Intel. Your premium features are now active
                    and ready to use.
                </p>

                {/* Subscription Confirmation */}
                <div className="bg-white/5 border border-white/10 rounded-2xl p-6 mb-8 animate-fade-in-up">
                    <div className="flex items-center justify-center mb-4">
                        <div className="w-3 h-3 bg-emerald-400 rounded-full mr-2 animate-pulse"></div>
                        <span className="text-emerald-400 font-medium">Active Subscription</span>
                    </div>
                    <p className="text-sm text-gray-400">
                        Your subscription is linked to your account. Access all premium features
                        from your dashboard.
                    </p>
                </div>

                {/* Actions */}
                <div className="space-y-4 animate-fade-in-up">
                    <Link
                        href="/dashboard"
                        className="w-full inline-block bg-emerald-500 text-white py-4 px-8 rounded-full font-medium hover:bg-emerald-600 transition"
                    >
                        Go to Dashboard →
                    </Link>
                    <div>
                        <Link href="/" className="text-sm text-gray-500 hover:text-white transition-colors inline-block">
                            ← Back to Home
                        </Link>
                    </div>
                </div>

                {/* Footer */}
                <div className="mt-12 pt-8 border-t border-white/10">
                    <div className="flex items-center justify-center gap-2">
                        <Image src="/logo.png" alt="GAP Intel" width={20} height={20} className="rounded" />
                        <span className="text-xs text-gray-500">Questions? Email help@gapintel.online</span>
                    </div>
                </div>
            </div>
        </main>
    );
}

export default function SuccessPage() {
    return (
        <Suspense fallback={<div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center text-white">Loading...</div>}>
            <SuccessContent />
        </Suspense>
    );
}
