import { NextRequest, NextResponse } from 'next/server';
import { getStripe } from '@/lib/stripe';
import { checkRateLimit, getClientIP } from '@/lib/rate-limit';

// Subscription tier pricing configuration
// Price IDs should be set in environment variables after creating products in Stripe
const TIER_CONFIG: Record<string, {
    monthlyPriceId: string;
    annualPriceId: string;
    name: string;
    description: string;
}> = {
    starter: {
        monthlyPriceId: process.env.STRIPE_STARTER_MONTHLY_PRICE_ID || '',
        annualPriceId: process.env.STRIPE_STARTER_ANNUAL_PRICE_ID || '',
        name: 'GAP Intel Starter',
        description: '1 analysis/month • Full Gap Analysis • 3 competitor channels'
    },
    pro: {
        monthlyPriceId: process.env.STRIPE_PRO_MONTHLY_PRICE_ID || '',
        annualPriceId: process.env.STRIPE_PRO_ANNUAL_PRICE_ID || '',
        name: 'GAP Intel Pro',
        description: '5 analyses/month • CTR Prediction • Advanced Thumbnail AI • 10 competitors'
    },
    enterprise: {
        monthlyPriceId: process.env.STRIPE_ENTERPRISE_MONTHLY_PRICE_ID || '',
        annualPriceId: process.env.STRIPE_ENTERPRISE_ANNUAL_PRICE_ID || '',
        name: 'GAP Intel Enterprise',
        description: '25 analyses/month • Team collaboration • API Access • 100 competitors'
    }
};

// Rate limit: 5 checkout attempts per minute per IP
const CHECKOUT_RATE_LIMIT = {
    maxRequests: 5,
    windowMs: 60 * 1000,
    keyPrefix: 'checkout'
};

export async function POST(req: NextRequest) {
    try {
        // ============================================
        // SECURITY: Rate Limiting
        // ============================================
        const clientIP = getClientIP(req);
        const rateLimitResult = checkRateLimit(clientIP, CHECKOUT_RATE_LIMIT);

        if (!rateLimitResult.success) {
            console.warn(`Rate limit exceeded for IP: ${clientIP}`);
            return NextResponse.json(
                {
                    error: 'Too many requests. Please try again in a minute.',
                    retryAfter: Math.ceil((rateLimitResult.resetTime - Date.now()) / 1000)
                },
                {
                    status: 429,
                    headers: {
                        'Retry-After': String(Math.ceil((rateLimitResult.resetTime - Date.now()) / 1000)),
                        'X-RateLimit-Remaining': '0',
                        'X-RateLimit-Reset': String(rateLimitResult.resetTime)
                    }
                }
            );
        }

        // ============================================
        // Input Validation
        // ============================================
        let body;
        try {
            body = await req.json();
        } catch {
            return NextResponse.json(
                { error: 'Invalid JSON body' },
                { status: 400 }
            );
        }

        const { tier, isAnnual, email, channelName } = body;

        // Validate tier
        if (!tier || !TIER_CONFIG[tier]) {
            return NextResponse.json(
                { error: 'Invalid subscription tier' },
                { status: 400 }
            );
        }

        // Validate email
        if (!email || typeof email !== 'string' || !email.includes('@')) {
            return NextResponse.json(
                { error: 'Valid email is required' },
                { status: 400 }
            );
        }

        const tierConfig = TIER_CONFIG[tier];
        const priceId = isAnnual ? tierConfig.annualPriceId : tierConfig.monthlyPriceId;

        // Check if price ID is configured
        if (!priceId) {
            console.error(`Price ID not configured for tier: ${tier}, isAnnual: ${isAnnual}`);
            return NextResponse.json(
                { error: 'Subscription pricing not configured. Please contact support.' },
                { status: 500 }
            );
        }

        // ============================================
        // Stripe Configuration Check
        // ============================================
        const stripeSecretKey = process.env.STRIPE_SECRET_KEY;

        if (!stripeSecretKey) {
            console.error('STRIPE_SECRET_KEY is not set');
            return NextResponse.json(
                { error: 'Payment system not configured' },
                { status: 500 }
            );
        }

        const stripe = getStripe();
        if (!stripe) {
            console.error('Failed to initialize Stripe client');
            return NextResponse.json(
                { error: 'Payment initialization failed' },
                { status: 500 }
            );
        }

        // ============================================
        // Create Stripe Checkout Session (Subscription Mode)
        // ============================================
        const session = await stripe.checkout.sessions.create({
            payment_method_types: ['card'],
            line_items: [
                {
                    price: priceId,
                    quantity: 1,
                },
            ],
            mode: 'subscription', // Changed from 'payment' to 'subscription'
            success_url: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard?subscription=success&tier=${tier}`,
            cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/pricing?canceled=true`,
            customer_email: email,
            metadata: {
                channelName: channelName ? String(channelName).replace('@', '') : '',
                email: email,
                tier: tier,
                isAnnual: String(isAnnual),
            },
            subscription_data: {
                metadata: {
                    tier: tier,
                    email: email,
                },
            },
            allow_promotion_codes: true, // Enable promo codes
        });

        // Add rate limit headers to successful response
        return NextResponse.json(
            { url: session.url },
            {
                headers: {
                    'X-RateLimit-Remaining': String(rateLimitResult.remaining),
                    'X-RateLimit-Reset': String(rateLimitResult.resetTime)
                }
            }
        );
    } catch (error: unknown) {
        console.error('Checkout error:', error);
        // Don't expose internal error details to client
        return NextResponse.json(
            { error: 'Failed to create checkout session. Please try again.' },
            { status: 500 }
        );
    }
}
