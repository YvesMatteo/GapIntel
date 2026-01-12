import { createClient } from "@supabase/supabase-js";
import { NextRequest, NextResponse } from "next/server";
import { getStripe } from "@/lib/stripe";
import { createClient as createServerClient } from "@/lib/supabase-server";
import Stripe from "stripe";

export async function POST(req: NextRequest) {
    try {
        const supabase = await createServerClient();
        const stripe = getStripe();

        if (!stripe) {
            return NextResponse.json({ error: "Stripe not configured" }, { status: 500 });
        }

        // Get current user
        const { data: { user }, error: authError } = await supabase.auth.getUser();

        if (authError || !user || !user.email) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        console.log(`Syncing subscription for ${user.email}...`);

        // Check Stripe for customers with this email (Stripe is case-sensitive)
        // Try lowercase first (most likely for Stripe)
        let customers = await stripe.customers.list({
            email: user.email.toLowerCase(),
            limit: 1,
            expand: ["data.subscriptions"],
        });

        // If not found, try exact match if different
        if (customers.data.length === 0 && user.email !== user.email.toLowerCase()) {
            customers = await stripe.customers.list({
                email: user.email,
                limit: 1,
                expand: ["data.subscriptions"],
            });
        }

        if (customers.data.length === 0) {
            return NextResponse.json({ message: "No customer found in Stripe", tier: "free" });
        }

        const customer = customers.data[0];
        const subscriptions = customer.subscriptions?.data || [];

        // Find the first active subscription
        const activeSub = subscriptions.find(sub => sub.status === "active" || sub.status === "trialing");

        if (!activeSub) {
            // Update DB to reflect no active subscription
            const supabaseAdmin = createClient(
                process.env.NEXT_PUBLIC_SUPABASE_URL!,
                process.env.SUPABASE_SERVICE_ROLE_KEY!
            );

            await supabaseAdmin.from("user_subscriptions").upsert({
                user_email: user.email,
                tier: "free",
                status: "cancelled",
                user_id: user.id
            }, { onConflict: "user_email" });

            return NextResponse.json({ message: "No active subscription found", tier: "free" });
        }

        // Determine tier from Product Name first (most robust)
        const price = activeSub.items.data[0].price;
        let tier = "starter"; // Default

        // We need to fetch product details to be sure
        try {
            const productRes = await stripe.products.retrieve(price.product as string);
            const name = (productRes.name || "").toLowerCase();

            if (name.includes("pro")) tier = "pro";
            else if (name.includes("enterprise")) tier = "enterprise";
            else if (name.includes("starter")) tier = "starter";

            console.log(`Sync Tier Detection: Product="${name}" -> Tier="${tier}"`);
        } catch (e) {
            console.error("Error fetching product:", e);
            // Fallback to ID check
            tier = getTierFromPriceId(price.id);
        }

        console.log(`Found active subscription: ${activeSub.id} (${tier})`);

        // Safely parse current_period_end
        let currentPeriodEnd = new Date().toISOString();
        const rawPeriodEnd = (activeSub as any).current_period_end;
        if (rawPeriodEnd && !isNaN(rawPeriodEnd)) {
            try {
                currentPeriodEnd = new Date(rawPeriodEnd * 1000).toISOString();
            } catch (e) {
                console.error("Date parsing error:", e);
            }
        }

        // Update Database (Use Admin Client to bypass RLS for UPSERT)
        const supabaseAdmin = createClient(
            process.env.NEXT_PUBLIC_SUPABASE_URL!,
            process.env.SUPABASE_SERVICE_ROLE_KEY!
        );

        const { error: upsertError } = await supabaseAdmin.from("user_subscriptions").upsert({
            user_id: user.id,
            user_email: user.email,
            stripe_customer_id: customer.id,
            stripe_subscription_id: activeSub.id,
            tier: tier,
            status: activeSub.status,
            current_period_end: currentPeriodEnd,
        }, {
            onConflict: "user_email"
        });

        if (upsertError) {
            console.error("Failed to sync subscription:", upsertError);
            return NextResponse.json({
                error: "Database error",
                details: upsertError.message,
                code: upsertError.code,
                hint: upsertError.hint
            }, { status: 500 });
        }

        return NextResponse.json({
            success: true,
            tier,
            message: "Subscription synced successfully"
        });

    } catch (error: any) {
        console.error("Error syncing subscription:", error);
        return NextResponse.json({
            error: "Internal server error",
            details: error?.message || String(error)
        }, { status: 500 });
    }
}

function getTierFromPriceId(priceId: string): string {
    // Basic ID check fallback
    const starter = process.env.STRIPE_PRICE_STARTER;
    const pro = process.env.STRIPE_PRICE_PRO;
    const enterprise = process.env.STRIPE_PRICE_ENTERPRISE;

    if (priceId === starter) return "starter";
    if (priceId === pro) return "pro";
    if (priceId === enterprise) return "enterprise";

    return "starter";
}
