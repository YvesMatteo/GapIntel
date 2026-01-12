import { createClient } from "@/lib/supabase-server";
import { NextResponse } from "next/server";
import Stripe from "stripe";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
    apiVersion: "2024-12-18.acacia" as any,
});

export async function POST() {
    try {
        const supabase = await createClient();

        // Get current user
        const { data: { user }, error: authError } = await supabase.auth.getUser();

        if (authError || !user) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        // Get subscription to find Stripe customer ID
        const { data: subscription } = await supabase
            .from("user_subscriptions")
            .select("stripe_customer_id")
            .eq("user_email", user.email)
            .single();

        if (!subscription?.stripe_customer_id) {
            return NextResponse.json(
                { error: "No billing account found. Please subscribe first." },
                { status: 400 }
            );
        }

        // Create Stripe Customer Portal session
        const session = await stripe.billingPortal.sessions.create({
            customer: subscription.stripe_customer_id,
            return_url: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard/billing`,
        });

        return NextResponse.json({ url: session.url });
    } catch (error) {
        console.error("Error creating billing portal session:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
    }
}
