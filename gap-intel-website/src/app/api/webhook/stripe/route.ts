import { NextRequest, NextResponse } from 'next/server';
import { getStripe } from '@/lib/stripe';
import { createServerClient } from '@/lib/supabase';
import Stripe from 'stripe';

export async function POST(req: NextRequest) {
    const body = await req.text();
    const signature = req.headers.get('stripe-signature');

    if (!signature) {
        return NextResponse.json({ error: 'No signature' }, { status: 400 });
    }

    let event: Stripe.Event;

    const stripe = getStripe();
    if (!stripe) {
        return NextResponse.json({ error: 'Stripe not configured' }, { status: 500 });
    }

    try {
        event = stripe.webhooks.constructEvent(
            body,
            signature,
            process.env.STRIPE_WEBHOOK_SECRET!
        );
    } catch (err) {
        console.error('Webhook signature verification failed:', err);
        return NextResponse.json({ error: 'Invalid signature' }, { status: 400 });
    }

    const supabase = createServerClient();

    // Handle checkout.session.completed - New subscription
    if (event.type === 'checkout.session.completed') {
        const session = event.data.object as Stripe.Checkout.Session;
        const email = session.customer_email || '';
        const tier = session.metadata?.tier || 'pro';
        const userId = session.metadata?.userId; // Read userId attached from client
        const subscriptionId = session.subscription as string;
        const customerId = session.customer as string;

        console.log(`✅ Checkout completed for ${email}, tier: ${tier}`);

        // Create Organization if userId exists and org doesn't exist
        if (userId) {
            const { data: existingOrg } = await supabase
                .from('organizations')
                .select('id')
                .eq('owner_id', userId)
                .single();

            if (!existingOrg) {
                const orgName = email.split('@')[0] + "'s Team";
                const { error: orgError } = await supabase.from('organizations').insert({
                    owner_id: userId,
                    name: orgName,
                    max_seats: tier === 'enterprise' ? 10 : tier === 'pro' ? 3 : 1,
                    subscription_tier: tier
                });

                if (orgError) console.error("Failed to create organization:", orgError);
                else console.log(`✅ Organization created for ${userId}`);
            }
        } else {
            console.warn("⚠️ No userId in metadata, skipping Organization creation.");
        }

        // Get subscription details for period end
        let periodEnd = null;
        if (subscriptionId) {
            const subscriptionData = await stripe.subscriptions.retrieve(subscriptionId) as any;
            periodEnd = new Date(subscriptionData.current_period_end * 1000).toISOString();
        }

        // Upsert into user_subscriptions table
        const { error } = await supabase
            .from('user_subscriptions')
            .upsert({
                user_email: email,
                stripe_customer_id: customerId,
                stripe_subscription_id: subscriptionId,
                tier: tier,
                status: 'active',
                current_period_end: periodEnd,
                analyses_this_month: 0,
            }, {
                onConflict: 'user_email'
            });

        if (error) {
            console.error('Database upsert error:', error);
            return NextResponse.json({ error: 'Database error' }, { status: 500 });
        }

        console.log(`✅ Subscription activated for ${email}`);
        return NextResponse.json({ received: true });
    }

    // Handle subscription updates (renewal, plan change, upgrade/downgrade)
    if (event.type === 'customer.subscription.updated') {
        const subscription = event.data.object as Stripe.Subscription;
        const customerId = subscription.customer as string;

        // Get customer email
        const customer = await stripe.customers.retrieve(customerId) as Stripe.Customer;
        const email = customer.email;

        if (!email) {
            console.error('No email found for customer:', customerId);
            return NextResponse.json({ received: true });
        }

        const subData = subscription as Stripe.Subscription & { current_period_end: number };
        const status = subData.status === 'active' ? 'active' :
            subData.status === 'trialing' ? 'trialing' :
                subData.status === 'past_due' ? 'past_due' : 'cancelled';

        const periodEnd = new Date(subData.current_period_end * 1000).toISOString();

        // Get tier from subscription metadata or price lookup
        let tier = subscription.metadata?.tier;

        // If no tier in metadata, try to determine from price
        if (!tier && subscription.items?.data?.[0]?.price) {
            const priceId = subscription.items.data[0].price.id;
            // Map price IDs to tiers (check against env vars)
            if (priceId === process.env.STRIPE_STARTER_MONTHLY_PRICE_ID ||
                priceId === process.env.STRIPE_STARTER_ANNUAL_PRICE_ID) {
                tier = 'starter';
            } else if (priceId === process.env.STRIPE_PRO_MONTHLY_PRICE_ID ||
                       priceId === process.env.STRIPE_PRO_ANNUAL_PRICE_ID) {
                tier = 'pro';
            } else if (priceId === process.env.STRIPE_ENTERPRISE_MONTHLY_PRICE_ID ||
                       priceId === process.env.STRIPE_ENTERPRISE_ANNUAL_PRICE_ID) {
                tier = 'enterprise';
            }
        }

        // Build update object
        const updateData: Record<string, string | number> = {
            status: status,
            current_period_end: periodEnd,
        };

        // Only update tier if we determined one (for upgrades/downgrades)
        if (tier) {
            updateData.tier = tier;
            // Reset usage on tier change (giving them fresh start on new tier)
            updateData.analyses_this_month = 0;
        }

        const { error } = await supabase
            .from('user_subscriptions')
            .update(updateData)
            .eq('stripe_subscription_id', subscription.id);

        if (error) {
            console.error('Database update error:', error);
        } else {
            console.log(`✅ Subscription updated for ${email}: ${status}${tier ? `, tier: ${tier}` : ''}`);
        }

        return NextResponse.json({ received: true });
    }

    // Handle invoice payment succeeded (monthly renewal - reset usage)
    if (event.type === 'invoice.payment_succeeded') {
        const invoice = event.data.object as Stripe.Invoice & { subscription?: string; billing_reason?: string };

        // Only process subscription invoices (not one-time payments)
        if (invoice.subscription && invoice.billing_reason === 'subscription_cycle') {
            const subscriptionId = invoice.subscription;

            // Reset monthly usage on successful renewal
            const { error } = await supabase
                .from('user_subscriptions')
                .update({
                    analyses_this_month: 0,
                    analyses_reset_at: new Date().toISOString(),
                })
                .eq('stripe_subscription_id', subscriptionId);

            if (error) {
                console.error('Failed to reset monthly usage:', error);
            } else {
                console.log(`✅ Monthly usage reset for subscription: ${subscriptionId}`);
            }
        }

        return NextResponse.json({ received: true });
    }

    // Handle subscription cancellation/deletion
    if (event.type === 'customer.subscription.deleted') {
        const subscription = event.data.object as Stripe.Subscription;

        const { error } = await supabase
            .from('user_subscriptions')
            .update({
                status: 'cancelled',
                tier: 'free',
            })
            .eq('stripe_subscription_id', subscription.id);

        if (error) {
            console.error('Database update error:', error);
        } else {
            console.log(`✅ Subscription cancelled: ${subscription.id}`);
        }

        return NextResponse.json({ received: true });
    }

    return NextResponse.json({ received: true });
}
