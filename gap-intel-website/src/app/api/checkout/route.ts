import { NextRequest, NextResponse } from 'next/server';
import { getStripe } from '@/lib/stripe';
import { checkRateLimit, getClientIP } from '@/lib/rate-limit';
import { checkoutInputSchema, validateInput, sanitizeString } from '@/lib/validation';

// Tier pricing configuration
const TIER_CONFIG = {
    basic: {
        price: 4900, // in cents
        priceId: 'price_1SlZpw31NKbNsvqrHaQ785Ty',
        name: 'GapIntel Basic Analysis',
        description: '15 videos • 3 video ideas • Basic gap analysis'
    },
    premium: {
        price: 7900, // in cents
        priceId: 'price_1SlwZT31NKbNsvqrQtuIb277',
        name: 'GapIntel Premium Analysis',
        description: '50 videos • ML thumbnail analysis • Trend insights • 5 packages'
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
        // SECURITY: Input Validation
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

        const validation = validateInput(checkoutInputSchema, body);
        if (!validation.success) {
            console.warn(`Invalid checkout input: ${validation.error}`);
            return NextResponse.json(
                { error: validation.error },
                { status: 400 }
            );
        }

        // Sanitize and extract validated data
        const { channelName: rawChannelName, email: rawEmail, tier } = validation.data;
        const channelName = sanitizeString(rawChannelName);
        const email = sanitizeString(rawEmail);
        const selectedTier = tier;
        const tierConfig = TIER_CONFIG[selectedTier];

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
        // Create Stripe Checkout Session
        // ============================================
        const lineItem = {
            price_data: {
                currency: 'usd',
                product_data: {
                    name: tierConfig.name,
                    description: tierConfig.description,
                },
                unit_amount: tierConfig.price,
            },
            quantity: 1,
        };

        const session = await stripe.checkout.sessions.create({
            payment_method_types: ['card'],
            line_items: [lineItem],
            mode: 'payment',
            success_url: `${process.env.NEXT_PUBLIC_APP_URL}/success?session_id={CHECKOUT_SESSION_ID}`,
            cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/?canceled=true`,
            customer_email: email,
            metadata: {
                channelName: channelName.replace('@', ''),
                email: email,
                tier: selectedTier,
            },
            payment_method_options: {
                card: {
                    setup_future_usage: undefined,
                },
            },
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
