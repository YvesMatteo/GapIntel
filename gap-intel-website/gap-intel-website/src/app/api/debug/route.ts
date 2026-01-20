import { NextResponse } from 'next/server';

export async function GET() {
    // Check which env vars are set (without exposing values)
    const envCheck = {
        STRIPE_SECRET_KEY: !!process.env.STRIPE_SECRET_KEY ? `set (starts with ${process.env.STRIPE_SECRET_KEY?.substring(0, 8)}...)` : 'NOT SET',
        STRIPE_PRICE_ID: !!process.env.STRIPE_PRICE_ID ? `set (${process.env.STRIPE_PRICE_ID})` : 'NOT SET',
        NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL || 'NOT SET',
        NEXT_PUBLIC_SUPABASE_URL: !!process.env.NEXT_PUBLIC_SUPABASE_URL ? 'set' : 'NOT SET',
    };

    return NextResponse.json(envCheck);
}
