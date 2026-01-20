import { NextRequest, NextResponse } from 'next/server';
import { stripe } from '@/lib/stripe';

export async function GET(req: NextRequest) {
    const sessionId = req.nextUrl.searchParams.get('session_id');

    if (!sessionId) {
        return NextResponse.json({ error: 'Missing session_id' }, { status: 400 });
    }

    try {
        const session = await stripe.checkout.sessions.retrieve(sessionId);

        // In a real app, we'd query Supabase for the access key
        // For now, return the session metadata
        return NextResponse.json({
            success: true,
            channelName: session.metadata?.channelName,
            email: session.customer_email,
            // accessKey would come from Supabase lookup
        });
    } catch (error) {
        console.error('Session verification error:', error);
        return NextResponse.json({ error: 'Invalid session' }, { status: 400 });
    }
}
