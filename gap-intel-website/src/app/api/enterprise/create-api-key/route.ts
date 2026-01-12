import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import { cookies } from "next/headers";
import { createServerClient } from "@supabase/ssr";

// Service role client - bypasses RLS
const supabaseAdmin = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export async function POST(req: NextRequest) {
    try {
        const body = await req.json();
        const { name } = body;

        if (!name) {
            return NextResponse.json(
                { error: "name is required" },
                { status: 400 }
            );
        }

        // Get current user from session
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

        const { data: { user } } = await supabase.auth.getUser();
        if (!user) {
            return NextResponse.json(
                { error: "Unauthorized" },
                { status: 401 }
            );
        }

        // Check if user is enterprise tier
        const { data: sub } = await supabaseAdmin
            .from("user_subscriptions")
            .select("tier")
            .eq("user_id", user.id)
            .single();

        if (sub?.tier !== "enterprise") {
            return NextResponse.json(
                { error: "API keys require Enterprise subscription" },
                { status: 403 }
            );
        }

        // Get or create organization using admin client (bypasses RLS)
        let { data: org } = await supabaseAdmin
            .from("organizations")
            .select("id")
            .eq("owner_id", user.id)
            .single();

        if (!org) {
            // Create org using admin client
            const { data: newOrg, error: orgError } = await supabaseAdmin
                .from("organizations")
                .insert({
                    owner_id: user.id,
                    name: `${user.email}'s Organization`,
                    subscription_tier: "enterprise",
                    max_seats: 10,
                    max_api_calls_per_day: 500
                })
                .select()
                .single();

            if (orgError) {
                console.error("Error creating org:", orgError);
                return NextResponse.json(
                    { error: "Failed to create organization: " + orgError.message },
                    { status: 500 }
                );
            }
            org = newOrg;
        }

        // Generate API key
        const apiKey = `gap_${crypto.randomUUID().replace(/-/g, '')}`;
        const keyPrefix = apiKey.substring(0, 12);

        // Insert API key using admin client
        const { error: keyError } = await supabaseAdmin
            .from("api_keys")
            .insert({
                organization_id: org!.id,
                name: name,
                key_hash: apiKey,
                key_prefix: keyPrefix,
                is_active: true,
                calls_today: 0,
                calls_total: 0
            });

        if (keyError) {
            console.error("Error creating key:", keyError);
            return NextResponse.json(
                { error: "Failed to create API key: " + keyError.message },
                { status: 500 }
            );
        }

        return NextResponse.json({ api_key: apiKey, success: true });

    } catch (error) {
        console.error("Error creating API key:", error);
        return NextResponse.json(
            { error: "Internal server error" },
            { status: 500 }
        );
    }
}
