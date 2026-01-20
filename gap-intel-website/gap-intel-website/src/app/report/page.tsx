"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";

export default function ReportPage() {
    const [accessKey, setAccessKey] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError("");

        // Validate format
        if (!accessKey.startsWith("GAP-") || accessKey.length < 10) {
            setError("Invalid access key format. Keys start with GAP-");
            setIsLoading(false);
            return;
        }

        // Redirect to the dashboard with the key
        window.location.href = `/report/${accessKey}`;
    };

    return (
        <main className="min-h-screen flex items-center justify-center px-6 py-20">
            <div className="max-w-md w-full">
                {/* Header */}
                <div className="text-center mb-8">
                    <Link href="/" className="inline-flex items-center gap-2 mb-6">
                        <Image src="/logo.png" alt="GAP Intel" width={40} height={40} className="rounded-lg" />
                        <span className="text-xl font-bold text-[#1a1a2e]">GAP Intel</span>
                    </Link>
                    <h1 className="heading-lg mb-2">Access Your Report</h1>
                    <p className="text-[#6b7280]">
                        Enter your access key to view your GAP analysis
                    </p>
                </div>

                {/* Access Key Form */}
                <form onSubmit={handleSubmit} className="card-glass p-8">
                    <div className="space-y-4">
                        <div>
                            <label htmlFor="accessKey" className="block text-sm font-medium mb-2">
                                Access Key
                            </label>
                            <input
                                id="accessKey"
                                type="text"
                                placeholder="GAP-XXXXXXXXXXXX"
                                value={accessKey}
                                onChange={(e) => setAccessKey(e.target.value)}
                                className="input-field font-mono text-center text-lg tracking-wider"
                                required
                            />
                        </div>

                        {error && (
                            <div className="bg-red-50 border border-red-200 text-red-600 text-sm rounded-lg p-3">
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            className="btn-primary w-full"
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <span className="flex items-center justify-center gap-2">
                                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                    </svg>
                                    Loading...
                                </span>
                            ) : (
                                "View Report"
                            )}
                        </button>
                    </div>
                </form>

                {/* Help */}
                <div className="mt-8 text-center">
                    <p className="text-sm text-[#6b7280]">
                        Lost your key? Check your email or{" "}
                        <a href="mailto:help@gapintel.online" className="text-[#9d94ff] hover:underline">
                            contact support
                        </a>
                    </p>
                </div>

                {/* Back link */}
                <div className="mt-6 text-center">
                    <Link href="/" className="text-sm text-[#6b7280] hover:text-[#1a1a2e] transition-colors">
                        ← Back to Home
                    </Link>
                </div>
            </div>
        </main>
    );
}
