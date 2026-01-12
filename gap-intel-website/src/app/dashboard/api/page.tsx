"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase-browser";

interface APIKey {
    id: string;
    name: string;
    key_prefix: string;
    calls_today: number;
    calls_total: number;
    is_active: boolean;
    created_at: string;
}

export default function APIKeysPage() {
    const [keys, setKeys] = useState<APIKey[]>([]);
    const [loading, setLoading] = useState(true);
    const [orgId, setOrgId] = useState<string | null>(null);
    const [newKeyName, setNewKeyName] = useState("");
    const [createdKey, setCreatedKey] = useState<string | null>(null);
    const [creating, setCreating] = useState(false);
    const [isEnterprise, setIsEnterprise] = useState(false);

    const supabase = createClient();

    useEffect(() => {
        loadAPIKeys();
    }, []);

    async function loadAPIKeys() {
        try {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;

            // Check if user has enterprise subscription
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

                // Get API keys
                const { data: apiKeys } = await supabase
                    .from("api_keys")
                    .select("*")
                    .eq("organization_id", org.id)
                    .eq("is_active", true);

                setKeys(apiKeys || []);
            }
        } catch (err) {
            console.error("Error loading API keys:", err);
        } finally {
            setLoading(false);
        }
    }

    async function createKey() {
        if (!newKeyName) {
            alert("Please enter a name for your API key");
            return;
        }

        setCreating(true);
        try {
            // Call server-side API which uses service role to bypass RLS
            const response = await fetch("/api/enterprise/create-api-key", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name: newKeyName })
            });

            const data = await response.json();

            if (!response.ok) {
                alert(data.error || "Failed to create API key");
                return;
            }

            if (data.api_key) {
                setCreatedKey(data.api_key);
                setNewKeyName("");
                loadAPIKeys();
            }
        } catch (err) {
            console.error("Error creating key:", err);
            alert("Error creating key: " + (err as Error).message);
        } finally {
            setCreating(false);
        }
    }

    async function revokeKey(keyId: string) {
        if (!confirm("Revoke this API key? This cannot be undone.")) return;

        await supabase
            .from("api_keys")
            .update({ is_active: false })
            .eq("id", keyId);

        loadAPIKeys();
    }

    function copyToClipboard(text: string) {
        navigator.clipboard.writeText(text);
        alert("Copied to clipboard!");
    }

    if (loading) {
        return (
            <main className="min-h-screen bg-[#fafbfc] p-8">
                <div className="max-w-4xl mx-auto">
                    <div className="animate-pulse">Loading...</div>
                </div>
            </main>
        );
    }

    if (!isEnterprise) {
        return (
            <main className="min-h-screen bg-[#fafbfc] p-8">
                <div className="max-w-4xl mx-auto">
                    <div className="card-light p-8 text-center">
                        <div className="text-6xl mb-6">🔑</div>
                        <h1 className="text-2xl font-bold mb-4">API Access</h1>
                        <p className="text-gray-600 mb-6">
                            Programmatic API access is available exclusively for Enterprise subscribers.
                        </p>
                        <p className="text-sm text-gray-500 mb-6">
                            Enterprise API includes:<br />
                            • 500 API calls per day<br />
                            • Full JSON response with all premium data<br />
                            • Webhook support for async notifications<br />
                            • White-label branding
                        </p>
                        <Link href="/pricing" className="btn-primary">
                            Upgrade to Enterprise
                        </Link>
                    </div>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-[#fafbfc] p-8">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <Link href="/dashboard" className="text-indigo-600 hover:underline text-sm mb-4 inline-block">
                        ← Back to Dashboard
                    </Link>
                    <h1 className="text-3xl font-bold">API Keys</h1>
                    <p className="text-gray-600 mt-2">
                        Manage your API keys for programmatic access
                    </p>
                </div>

                {/* Newly Created Key Alert */}
                {createdKey && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-8">
                        <p className="text-green-800 font-medium mb-2">✅ API Key Created!</p>
                        <p className="text-sm text-green-700 mb-2">
                            Copy this key now. It will not be shown again.
                        </p>
                        <div className="flex gap-2">
                            <code className="flex-1 bg-white px-3 py-2 rounded border border-green-300 text-sm font-mono break-all">
                                {createdKey}
                            </code>
                            <button
                                onClick={() => copyToClipboard(createdKey)}
                                className="btn-primary text-sm"
                            >
                                Copy
                            </button>
                        </div>
                        <button
                            onClick={() => setCreatedKey(null)}
                            className="text-sm text-green-600 mt-2 hover:underline"
                        >
                            I've saved it, dismiss
                        </button>
                    </div>
                )}

                {/* Create Key Form */}
                <div className="card-light p-6 mb-8">
                    <h2 className="text-lg font-semibold mb-4">Create New API Key</h2>
                    <div className="flex gap-3">
                        <input
                            type="text"
                            value={newKeyName}
                            onChange={(e) => setNewKeyName(e.target.value)}
                            placeholder="Key name (e.g., Production)"
                            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                        <button
                            onClick={createKey}
                            disabled={creating || !newKeyName}
                            className="btn-primary disabled:opacity-50"
                        >
                            {creating ? "Creating..." : "Create Key"}
                        </button>
                    </div>
                </div>

                {/* API Keys List */}
                <div className="card-light">
                    <div className="p-4 border-b border-gray-200">
                        <h2 className="text-lg font-semibold">Your API Keys</h2>
                    </div>
                    <div className="divide-y divide-gray-100">
                        {keys.map((key) => (
                            <div key={key.id} className="p-4 flex items-center justify-between">
                                <div>
                                    <p className="font-medium">{key.name}</p>
                                    <p className="text-sm text-gray-500 font-mono">{key.key_prefix}...</p>
                                    <p className="text-xs text-gray-400 mt-1">
                                        {key.calls_today} calls today • {key.calls_total} total • Created {new Date(key.created_at).toLocaleDateString()}
                                    </p>
                                </div>
                                <button
                                    onClick={() => revokeKey(key.id)}
                                    className="text-red-600 hover:text-red-800 text-sm"
                                >
                                    Revoke
                                </button>
                            </div>
                        ))}

                        {keys.length === 0 && (
                            <div className="p-8 text-center text-gray-500">
                                No API keys yet. Create one above to get started.
                            </div>
                        )}
                    </div>
                </div>

                {/* API Documentation */}
                <div className="mt-8 card-light p-6">
                    <h3 className="font-semibold mb-4">Quick Start</h3>
                    <pre className="bg-gray-900 text-green-400 p-4 rounded-lg text-sm overflow-x-auto">
                        {`curl -X POST https://api.gapintel.online/api/v1/analyze \\
  -H "X-GAP-API-Key: YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"channel_name": "mkbhd", "video_count": 10}'`}
                    </pre>
                    <p className="text-sm text-gray-600 mt-4">
                        Check status: <code className="bg-gray-100 px-2 py-1 rounded">GET /api/v1/status/ANALYSIS_ID</code>
                    </p>
                    <p className="text-sm text-gray-600 mt-2">
                        View usage: <code className="bg-gray-100 px-2 py-1 rounded">GET /api/v1/usage</code>
                    </p>
                </div>
            </div>
        </main>
    );
}
