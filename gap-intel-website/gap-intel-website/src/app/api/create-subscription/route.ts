import { NextResponse } from "next/server";
import { createServerClient } from "@/lib/supabase";
import Stripe from "stripe";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
    apiVersion: "2024-12-18.acacia" as any,
});

// Price IDs - these are created in Stripe Dashboard
const PRICE_IDS = {
    starter_monthly: process.env.STRIPE_PRICE_STARTER || "price_starter_placeholder",
    starter_annual: process.env.STRIPE_PRICE_STARTER_ANNUAL || "price_starter_annual_placeholder",
    pro_monthly: process.env.STRIPE_PRICE_PRO_MONTHLY || "price_pro_monthly_placeholder",
    pro_annual: process.env.STRIPE_PRICE_PRO_ANNUAL || "price_pro_annual_placeholder",
    enterprise_monthly: process.env.STRIPE_PRICE_ENTERPRISE_MONTHLY || "price_enterprise_monthly_placeholder",
    enterprise_annual: process.env.STRIPE_PRICE_ENTERPRISE_ANNUAL || "price_enterprise_annual_placeholder",
};

export async function POST(request: Request) {
    try {
        const body = await request.json();
        const { priceId, isAnnual, email, userId } = body;

        // Check format
        if (!email) throw new Error("Email is required");

        console.log("Creating subscription for:", { priceId, isAnnual, email, userId });

        // Check for existing active subscription
        // Note: Using a direct check here (assuming createServerClient works without cookies for simple select if RLS allows or we use service role).
        // Standard createServerClient in this route likely uses service role or anon. 
        // If anon, we might not see it if RLS blocks. 
        // But preventing double-sub via email is good.
        // We really should use Service Role to be sure. 
        // Let's defer strict check if RLS is an issue, but we can try.
        // Actually, let's just use userId in metadata for now and assume the Stripe Customer Portal handles upgrade/downgrade.
        // But user said "once you bought... you can only upgrade".
        // This means we shouldn't create a NEW checkout session. We should redirect to billing portal?
        // But "Upgrade" might need a new checkout with `subscription_data.trial_period_days` etc?
        // For simplicity: If active, error out.

        // Note: Importing createServerClient here requires importing from correct path.
        // But this file only imports NextResponse and Stripe.
        // Need to add import.

        console.log("Creating subscription for:", { priceId, isAnnual, email });

        // Determine actual Stripe price ID
        let stripePriceId: string;

        switch (priceId) {
            case "price_starter":
                stripePriceId = isAnnual ? PRICE_IDS.starter_annual : PRICE_IDS.starter_monthly;
                break;
            case "price_pro":
                stripePriceId = isAnnual ? PRICE_IDS.pro_annual : PRICE_IDS.pro_monthly;
                break;
            case "price_enterprise":
                stripePriceId = isAnnual ? PRICE_IDS.enterprise_annual : PRICE_IDS.enterprise_monthly;
                break;
            default:
                console.error("Invalid price ID:", priceId);
                return NextResponse.json({ error: "Invalid price ID" }, { status: 400 });
        }

        const supabase = createServerClient();
        const { data: existingSub } = await supabase
            .from("user_subscriptions")
            .select("status, stripe_customer_id")
            .eq("user_email", email)
            .single();

        if (existingSub && (existingSub.status === 'active' || existingSub.status === 'trialing')) {
            // If user wants to UPGRADE, we should normally use billing portal or a specific upgrade flow.
            // But existing code creates a NEW checkout session which might create a DUPLICATE subscription object on the SAME customer.
            // We should force them to use billing portal.
            return NextResponse.json({ error: "You already have an active subscription. Please manage it in Settings > Billing." }, { status: 400 });
        }

        console.log("Using Stripe price ID:", stripePriceId);

        // Create Checkout Session - all plans are subscriptions
        const session = await stripe.checkout.sessions.create({
            payment_method_types: ["card"],
            line_items: [
                {
                    price: stripePriceId,
                    quantity: 1,
                },
            ],
            mode: "subscription",
            success_url: `${process.env.NEXT_PUBLIC_APP_URL}/success?session_id={CHECKOUT_SESSION_ID}`,
            cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/pricing`,
            customer_email: email,
            metadata: {
                tier: priceId.replace("price_", ""),
                isAnnual: String(isAnnual),
                userId: userId, // Pass userId for webhook
            },
            allow_promotion_codes: true,
            payment_method_options: {
                card: {
                    request_three_d_secure: "automatic",
                },
            },
        });

        console.log("Checkout session created:", session.url);
        return NextResponse.json({ url: session.url });
    } catch (error) {
        console.error("Subscription creation error:", error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : "Failed to create checkout session" },
            { status: 500 }
        );
    }
}

