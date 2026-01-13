import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import { cookies } from "next/headers";
import { createServerClient } from "@supabase/ssr";

// Service role client - bypasses RLS
const supabaseAdmin = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
);

// Get current user from session
async function getCurrentUser() {
    const cookieStore = await cookies();
    const supabase = createServerClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
        {
            cookies: {
                getAll() {
                    return cookieStore.getAll();
                },
            },
        }
    );
    return supabase.auth.getUser();
}

// GET - Fetch organization and team members
export async function GET(req: NextRequest) {
    try {
        const { data: { user } } = await getCurrentUser();
        if (!user) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        // Check if user is enterprise tier
        const { data: sub } = await supabaseAdmin
            .from("user_subscriptions")
            .select("tier")
            .eq("user_email", user.email)
            .single();

        if (!sub || (sub.tier !== "enterprise" && sub.tier !== "pro")) {
            return NextResponse.json({
                error: "Team management requires Pro or Enterprise subscription",
                organization: null,
                members: []
            });
        }

        // Get or create organization
        let { data: org } = await supabaseAdmin
            .from("organizations")
            .select("*")
            .eq("owner_id", user.id)
            .single();

        if (!org) {
            // Create org if doesn't exist
            const maxSeats = sub.tier === "enterprise" ? 10 : sub.tier === "pro" ? 3 : 1;
            const { data: newOrg, error: orgError } = await supabaseAdmin
                .from("organizations")
                .insert({
                    owner_id: user.id,
                    name: `${user.email?.split('@')[0]}'s Team`,
                    subscription_tier: sub.tier,
                    max_seats: maxSeats,
                    max_api_calls_per_day: sub.tier === "enterprise" ? 500 : 0
                })
                .select()
                .single();

            if (orgError) {
                console.error("Error creating org:", orgError);
                return NextResponse.json({
                    error: "Failed to create organization",
                    organization: null,
                    members: []
                });
            }
            org = newOrg;
        }

        // Get team members
        const { data: members } = await supabaseAdmin
            .from("team_members")
            .select("*")
            .eq("organization_id", org.id)
            .neq("status", "revoked");

        return NextResponse.json({
            organization: org,
            members: members || []
        });

    } catch (error) {
        console.error("Error fetching team:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
    }
}

// POST - Invite a new team member
export async function POST(req: NextRequest) {
    try {
        const { data: { user } } = await getCurrentUser();
        if (!user) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        const body = await req.json();
        const { email, role = "viewer" } = body;

        if (!email) {
            return NextResponse.json({ error: "Email is required" }, { status: 400 });
        }

        // Get user's organization
        const { data: org } = await supabaseAdmin
            .from("organizations")
            .select("*")
            .eq("owner_id", user.id)
            .single();

        if (!org) {
            return NextResponse.json({ error: "No organization found" }, { status: 404 });
        }

        // Check seat limits
        const { data: currentMembers } = await supabaseAdmin
            .from("team_members")
            .select("id")
            .eq("organization_id", org.id)
            .in("status", ["active", "pending"]);

        const seatsUsed = (currentMembers?.length || 0) + 1; // +1 for owner
        if (seatsUsed >= org.max_seats) {
            return NextResponse.json({
                error: `Seat limit reached (${org.max_seats} max). Upgrade to add more team members.`
            }, { status: 403 });
        }

        // Check if already invited
        const { data: existing } = await supabaseAdmin
            .from("team_members")
            .select("id, status")
            .eq("organization_id", org.id)
            .eq("email", email.toLowerCase())
            .single();

        if (existing) {
            if (existing.status === "revoked") {
                // Re-invite revoked member
                await supabaseAdmin
                    .from("team_members")
                    .update({ status: "pending", role })
                    .eq("id", existing.id);
                return NextResponse.json({ success: true, message: "Member re-invited" });
            }
            return NextResponse.json({ error: "This email is already invited" }, { status: 400 });
        }

        // Insert new team member
        const { error: inviteError } = await supabaseAdmin
            .from("team_members")
            .insert({
                organization_id: org.id,
                email: email.toLowerCase(),
                role,
                status: "pending",
                invited_by: user.id,
                invited_at: new Date().toISOString()
            });

        if (inviteError) {
            console.error("Error inviting member:", inviteError);
            return NextResponse.json({ error: inviteError.message }, { status: 500 });
        }

        // TODO: Send invitation email here

        return NextResponse.json({ success: true, message: "Invitation sent" });

    } catch (error) {
        console.error("Error inviting member:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
    }
}

// PATCH - Update team member role
export async function PATCH(req: NextRequest) {
    try {
        const { data: { user } } = await getCurrentUser();
        if (!user) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        const body = await req.json();
        const { memberId, role } = body;

        if (!memberId || !role) {
            return NextResponse.json({ error: "memberId and role are required" }, { status: 400 });
        }

        // Verify user owns the organization
        const { data: org } = await supabaseAdmin
            .from("organizations")
            .select("id")
            .eq("owner_id", user.id)
            .single();

        if (!org) {
            return NextResponse.json({ error: "Not authorized" }, { status: 403 });
        }

        // Update role
        const { error } = await supabaseAdmin
            .from("team_members")
            .update({ role })
            .eq("id", memberId)
            .eq("organization_id", org.id);

        if (error) {
            return NextResponse.json({ error: error.message }, { status: 500 });
        }

        return NextResponse.json({ success: true });

    } catch (error) {
        console.error("Error updating member:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
    }
}

// DELETE - Remove team member
export async function DELETE(req: NextRequest) {
    try {
        const { data: { user } } = await getCurrentUser();
        if (!user) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        const { searchParams } = new URL(req.url);
        const memberId = searchParams.get("memberId");

        if (!memberId) {
            return NextResponse.json({ error: "memberId is required" }, { status: 400 });
        }

        // Verify user owns the organization
        const { data: org } = await supabaseAdmin
            .from("organizations")
            .select("id")
            .eq("owner_id", user.id)
            .single();

        if (!org) {
            return NextResponse.json({ error: "Not authorized" }, { status: 403 });
        }

        // Revoke member (soft delete)
        const { error } = await supabaseAdmin
            .from("team_members")
            .update({ status: "revoked" })
            .eq("id", memberId)
            .eq("organization_id", org.id);

        if (error) {
            return NextResponse.json({ error: error.message }, { status: 500 });
        }

        return NextResponse.json({ success: true });

    } catch (error) {
        console.error("Error removing member:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
    }
}
