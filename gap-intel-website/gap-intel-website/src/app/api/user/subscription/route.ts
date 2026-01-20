import { createClient } from "@/lib/supabase-server";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
    try {
        const supabase = await createClient();

        // Get current user
        const { data: { user }, error: authError } = await supabase.auth.getUser();

        if (authError || !user) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        // Get subscription by email (current schema uses email, not user_id)
        const { data: subscription, error: subError } = await supabase
            .from("user_subscriptions")
            .select("*")
            .eq("user_email", user.email)
            .single();

        if (subError && subError.code !== "PGRST116") {
            // PGRST116 = no rows returned - that's ok, means free tier
            console.error("Error fetching subscription:", subError);
        }

        return NextResponse.json({
            tier: subscription?.tier || "free",
            status: subscription?.status || "active",
            analyses_this_month: subscription?.analyses_this_month || 0,
            current_period_end: subscription?.current_period_end || null,
            stripe_customer_id: subscription?.stripe_customer_id || null,
        });
    } catch (error) {
        console.error("Error in subscription API:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
    }
}
