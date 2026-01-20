"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import Navbar from "@/components/Navbar";
import { Users, UserPlus, ArrowLeft, Loader2, Mail, Shield, Trash2 } from "lucide-react";

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
    const { user } = useAuth();
    const [organization, setOrganization] = useState<Organization | null>(null);
    const [members, setMembers] = useState<TeamMember[]>([]);
    const [loading, setLoading] = useState(true);
    const [inviteEmail, setInviteEmail] = useState("");
    const [inviteRole, setInviteRole] = useState<string>("viewer");
    const [inviting, setInviting] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    useEffect(() => {
        loadTeam();
    }, []);

    async function loadTeam() {
        try {
            const res = await fetch("/api/enterprise/team");
            const data = await res.json();

            if (data.organization) {
                setOrganization(data.organization);
                setMembers(data.members || []);
            } else if (data.error) {
                setError(data.error);
            }
        } catch (err) {
            console.error("Error loading team:", err);
            setError("Failed to load team data");
        } finally {
            setLoading(false);
        }
    }

    async function inviteMember() {
        if (!inviteEmail) return;

        setInviting(true);
        setError("");
        setSuccess("");

        try {
            const res = await fetch("/api/enterprise/team", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: inviteEmail, role: inviteRole }),
            });

            const data = await res.json();

            if (res.ok) {
                setSuccess(`Invitation sent to ${inviteEmail}`);
                setInviteEmail("");
                loadTeam();
            } else {
                setError(data.error || "Failed to invite member");
            }
        } catch (err) {
            setError("Failed to send invitation");
        } finally {
            setInviting(false);
        }
    }

    async function updateRole(memberId: string, newRole: string) {
        try {
            await fetch("/api/enterprise/team", {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ memberId, role: newRole }),
            });
            loadTeam();
        } catch (err) {
            console.error("Error updating role:", err);
        }
    }

    async function removeMember(memberId: string) {
        if (!confirm("Remove this team member?")) return;

        try {
            await fetch(`/api/enterprise/team?memberId=${memberId}`, {
                method: "DELETE",
            });
            loadTeam();
        } catch (err) {
            console.error("Error removing member:", err);
        }
    }

    if (loading) {
        return (
            <div className="min-h-screen bg-[#fafbfc]">
                <Navbar />
                <main className="pt-24 pb-12 px-6">
                    <div className="max-w-4xl mx-auto flex items-center justify-center py-20">
                        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
                    </div>
                </main>
            </div>
        );
    }

    if (!organization) {
        return (
            <div className="min-h-screen bg-[#fafbfc]">
                <Navbar />
                <main className="pt-24 pb-12 px-6">
                    <div className="max-w-2xl mx-auto">
                        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-8 text-center">
                            <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                            <h1 className="text-2xl font-bold mb-4">Team Management</h1>
                            <p className="text-gray-600 mb-6">
                                {error || "Team management is available for Pro and Enterprise subscribers."}
                            </p>
                            <Link
                                href="/pricing"
                                className="inline-block px-6 py-3 bg-slate-900 text-white rounded-full font-medium hover:bg-slate-800 transition"
                            >
                                Upgrade to Enterprise
                            </Link>
                        </div>
                    </div>
                </main>
            </div>
        );
    }

    const seatsUsed = members.filter(m => m.status !== "revoked").length + 1; // +1 for owner
    const seatsRemaining = organization.max_seats - seatsUsed;

    return (
        <div className="min-h-screen bg-[#fafbfc]">
            <Navbar />
            <main className="pt-24 pb-12 px-6">
                <div className="max-w-4xl mx-auto">
                    {/* Header */}
                    <div className="mb-8">
                        <Link href="/dashboard" className="inline-flex items-center gap-2 text-gray-500 hover:text-gray-900 text-sm mb-4">
                            <ArrowLeft className="w-4 h-4" />
                            Back to Dashboard
                        </Link>
                        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                            <Users className="w-8 h-8" />
                            Team Management
                        </h1>
                        <p className="text-gray-500 mt-2">
                            {organization.name} • {seatsUsed}/{organization.max_seats} seats used
                        </p>
                    </div>

                    {/* Invite Form */}
                    {seatsRemaining > 0 && (
                        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 mb-6">
                            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                                <UserPlus className="w-5 h-5" />
                                Invite Team Member
                            </h2>
                            <div className="flex gap-3">
                                <input
                                    type="email"
                                    value={inviteEmail}
                                    onChange={(e) => setInviteEmail(e.target.value)}
                                    placeholder="colleague@company.com"
                                    className="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                                <select
                                    value={inviteRole}
                                    onChange={(e) => setInviteRole(e.target.value)}
                                    className="px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="viewer">Viewer</option>
                                    <option value="editor">Editor</option>
                                    <option value="admin">Admin</option>
                                </select>
                                <button
                                    onClick={inviteMember}
                                    disabled={inviting || !inviteEmail}
                                    className="px-6 py-3 bg-slate-900 text-white rounded-xl font-medium hover:bg-slate-800 transition disabled:opacity-50 flex items-center gap-2"
                                >
                                    {inviting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Mail className="w-4 h-4" />}
                                    {inviting ? "Inviting..." : "Send Invite"}
                                </button>
                            </div>
                            {error && <p className="text-red-500 text-sm mt-3">{error}</p>}
                            {success && <p className="text-emerald-600 text-sm mt-3">{success}</p>}
                        </div>
                    )}

                    {seatsRemaining <= 0 && (
                        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6">
                            <p className="text-amber-800">
                                You&apos;ve used all {organization.max_seats} seats.{" "}
                                <Link href="/pricing" className="underline font-medium">
                                    Upgrade for more seats
                                </Link>
                            </p>
                        </div>
                    )}

                    {/* Team Members List */}
                    <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
                        <div className="p-4 border-b border-gray-100">
                            <h2 className="text-lg font-semibold text-gray-900">Team Members</h2>
                        </div>
                        <div className="divide-y divide-gray-100">
                            {/* Owner */}
                            <div className="p-4 flex items-center justify-between bg-gray-50">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-full bg-emerald-500 flex items-center justify-center text-white font-medium">
                                        {(user?.email?.[0] || "U").toUpperCase()}
                                    </div>
                                    <div>
                                        <p className="font-medium text-gray-900">You (Owner)</p>
                                        <p className="text-sm text-gray-500">{user?.email}</p>
                                    </div>
                                </div>
                                <span className="px-3 py-1 bg-slate-900 text-white text-xs font-medium rounded-full">
                                    Owner
                                </span>
                            </div>

                            {/* Team members */}
                            {members.map((member) => (
                                <div key={member.id} className="p-4 flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-medium ${member.status === "pending" ? "bg-gray-400" : "bg-blue-500"
                                            }`}>
                                            {member.email[0].toUpperCase()}
                                        </div>
                                        <div>
                                            <p className="font-medium text-gray-900">{member.email}</p>
                                            <p className="text-sm text-gray-500">
                                                {member.status === "pending"
                                                    ? "Invitation pending"
                                                    : `Joined ${new Date(member.accepted_at || member.invited_at).toLocaleDateString()}`
                                                }
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <select
                                            value={member.role}
                                            onChange={(e) => updateRole(member.id, e.target.value)}
                                            className="text-sm px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        >
                                            <option value="viewer">Viewer</option>
                                            <option value="editor">Editor</option>
                                            <option value="admin">Admin</option>
                                        </select>
                                        <button
                                            onClick={() => removeMember(member.id)}
                                            className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition"
                                            title="Remove member"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            ))}

                            {members.length === 0 && (
                                <div className="p-8 text-center text-gray-500">
                                    <Users className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                                    <p>No team members yet.</p>
                                    <p className="text-sm">Invite colleagues using the form above!</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Role Explanations */}
                    <div className="mt-6 bg-white rounded-xl border border-gray-100 shadow-sm p-6">
                        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                            <Shield className="w-5 h-5" />
                            Role Permissions
                        </h3>
                        <div className="grid md:grid-cols-3 gap-4 text-sm">
                            <div className="p-4 bg-gray-50 rounded-lg">
                                <p className="font-medium text-blue-600 mb-1">Viewer</p>
                                <p className="text-gray-600">Can view all reports</p>
                            </div>
                            <div className="p-4 bg-gray-50 rounded-lg">
                                <p className="font-medium text-blue-600 mb-1">Editor</p>
                                <p className="text-gray-600">View + create new reports</p>
                            </div>
                            <div className="p-4 bg-gray-50 rounded-lg">
                                <p className="font-medium text-blue-600 mb-1">Admin</p>
                                <p className="text-gray-600">Full access + manage team</p>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
