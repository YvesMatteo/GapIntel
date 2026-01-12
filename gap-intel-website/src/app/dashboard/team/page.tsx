"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase-browser";

interface TeamMember {
    id: string;
    email: string;
    role: "admin" | "editor" | "viewer";
    status: "pending" | "active" | "revoked";
    invited_at: string;
    accepted_at: string | null;
}

interface Organization {
    id: string;
    name: string;
    max_seats: number;
    subscription_tier: string;
}

export default function TeamPage() {
    const [organization, setOrganization] = useState<Organization | null>(null);
    const [members, setMembers] = useState<TeamMember[]>([]);
    const [loading, setLoading] = useState(true);
    const [inviteEmail, setInviteEmail] = useState("");
    const [inviteRole, setInviteRole] = useState<string>("viewer");
    const [inviting, setInviting] = useState(false);
    const [error, setError] = useState("");

    const supabase = createClient();

    useEffect(() => {
        loadOrganization();
    }, []);

    async function loadOrganization() {
        try {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;

            // Get user's organization
            const { data: org } = await supabase
                .from("organizations")
                .select("*")
                .eq("owner_id", user.id)
                .single();

            if (org) {
                setOrganization(org);

                // Get team members
                const { data: teamMembers } = await supabase
                    .from("team_members")
                    .select("*")
                    .eq("organization_id", org.id)
                    .neq("status", "revoked");

                setMembers(teamMembers || []);
            }
        } catch (err) {
            console.error("Error loading organization:", err);
        } finally {
            setLoading(false);
        }
    }

    async function inviteMember() {
        if (!organization || !inviteEmail) return;

        setInviting(true);
        setError("");

        try {
            const { data: { user } } = await supabase.auth.getUser();

            const { error: inviteError } = await supabase
                .from("team_members")
                .insert({
                    organization_id: organization.id,
                    email: inviteEmail.toLowerCase(),
                    role: inviteRole,
                    status: "pending",
                    invited_by: user?.id
                });

            if (inviteError) throw inviteError;

            setInviteEmail("");
            loadOrganization();
        } catch (err: unknown) {
            const errorMessage = err instanceof Error ? err.message : "Failed to invite member";
            setError(errorMessage);
        } finally {
            setInviting(false);
        }
    }

    async function removeMember(memberId: string) {
        if (!confirm("Remove this team member?")) return;

        await supabase
            .from("team_members")
            .update({ status: "revoked" })
            .eq("id", memberId);

        loadOrganization();
    }

    async function updateRole(memberId: string, newRole: string) {
        await supabase
            .from("team_members")
            .update({ role: newRole })
            .eq("id", memberId);

        loadOrganization();
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

    if (!organization) {
        return (
            <main className="min-h-screen bg-[#fafbfc] p-8">
                <div className="max-w-4xl mx-auto">
                    <div className="card-light p-8 text-center">
                        <h1 className="text-2xl font-bold mb-4">Team Management</h1>
                        <p className="text-gray-600 mb-6">
                            Team management is available for Pro and Enterprise subscribers.
                        </p>
                        <Link href="/pricing" className="btn-primary">
                            Upgrade to Pro
                        </Link>
                    </div>
                </div>
            </main>
        );
    }

    const seatsUsed = members.filter(m => m.status === "active").length + 1; // +1 for owner
    const seatsRemaining = organization.max_seats - seatsUsed;

    return (
        <main className="min-h-screen bg-[#fafbfc] p-8">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <Link href="/dashboard" className="text-indigo-600 hover:underline text-sm mb-4 inline-block">
                        ← Back to Dashboard
                    </Link>
                    <h1 className="text-3xl font-bold">Team Management</h1>
                    <p className="text-gray-600 mt-2">
                        {organization.name} • {seatsUsed}/{organization.max_seats} seats used
                    </p>
                </div>

                {/* Invite Form */}
                {seatsRemaining > 0 && (
                    <div className="card-light p-6 mb-8">
                        <h2 className="text-lg font-semibold mb-4">Invite Team Member</h2>
                        <div className="flex gap-3">
                            <input
                                type="email"
                                value={inviteEmail}
                                onChange={(e) => setInviteEmail(e.target.value)}
                                placeholder="Email address"
                                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            />
                            <select
                                value={inviteRole}
                                onChange={(e) => setInviteRole(e.target.value)}
                                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            >
                                <option value="viewer">Viewer</option>
                                <option value="editor">Editor</option>
                                <option value="admin">Admin</option>
                            </select>
                            <button
                                onClick={inviteMember}
                                disabled={inviting || !inviteEmail}
                                className="btn-primary disabled:opacity-50"
                            >
                                {inviting ? "Inviting..." : "Invite"}
                            </button>
                        </div>
                        {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
                    </div>
                )}

                {seatsRemaining === 0 && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-8">
                        <p className="text-yellow-800">
                            You've used all your seats. <Link href="/pricing" className="underline">Upgrade</Link> for more.
                        </p>
                    </div>
                )}

                {/* Team Members List */}
                <div className="card-light">
                    <div className="p-4 border-b border-gray-200">
                        <h2 className="text-lg font-semibold">Team Members</h2>
                    </div>
                    <div className="divide-y divide-gray-100">
                        {/* Owner (current user) */}
                        <div className="p-4 flex items-center justify-between">
                            <div>
                                <p className="font-medium">You (Owner)</p>
                                <p className="text-sm text-gray-500">Full access</p>
                            </div>
                            <span className="badge-dark">Owner</span>
                        </div>

                        {/* Team members */}
                        {members.map((member) => (
                            <div key={member.id} className="p-4 flex items-center justify-between">
                                <div>
                                    <p className="font-medium">{member.email}</p>
                                    <p className="text-sm text-gray-500">
                                        {member.status === "pending" ? "Invite pending" : `Joined ${new Date(member.accepted_at || "").toLocaleDateString()}`}
                                    </p>
                                </div>
                                <div className="flex items-center gap-3">
                                    <select
                                        value={member.role}
                                        onChange={(e) => updateRole(member.id, e.target.value)}
                                        className="text-sm px-2 py-1 border border-gray-300 rounded"
                                    >
                                        <option value="viewer">Viewer</option>
                                        <option value="editor">Editor</option>
                                        <option value="admin">Admin</option>
                                    </select>
                                    <button
                                        onClick={() => removeMember(member.id)}
                                        className="text-red-600 hover:text-red-800 text-sm"
                                    >
                                        Remove
                                    </button>
                                </div>
                            </div>
                        ))}

                        {members.length === 0 && (
                            <div className="p-8 text-center text-gray-500">
                                No team members yet. Invite someone above!
                            </div>
                        )}
                    </div>
                </div>

                {/* Role Explanations */}
                <div className="mt-8 card-light p-6">
                    <h3 className="font-semibold mb-4">Role Permissions</h3>
                    <div className="grid md:grid-cols-3 gap-4 text-sm">
                        <div>
                            <p className="font-medium text-indigo-600">Viewer</p>
                            <p className="text-gray-600">Can view reports only</p>
                        </div>
                        <div>
                            <p className="font-medium text-indigo-600">Editor</p>
                            <p className="text-gray-600">Can create reports + view</p>
                        </div>
                        <div>
                            <p className="font-medium text-indigo-600">Admin</p>
                            <p className="text-gray-600">Full access + team management</p>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}
