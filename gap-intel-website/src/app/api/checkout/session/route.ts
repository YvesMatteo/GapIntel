import { NextRequest, NextResponse } from 'next/server';
import { createServerClient } from '@/lib/supabase';

export async function GET(req: NextRequest) {
    const { searchParams } = new URL(req.url);
    const sessionId = searchParams.get('session_id');

    if (!sessionId) {
        return NextResponse.json({ error: 'Session ID is required' }, { status: 400 });
    }

    const supabase = createServerClient();

    const { data, error } = await supabase
        .from('analyses')
        .select('access_key, analysis_status, email')
        .eq('stripe_payment_id', sessionId)
        .single();

    if (error || !data) {
        return NextResponse.json({ error: 'Analysis not found' }, { status: 404 });
    }

    return NextResponse.json({
        access_key: data.access_key,
        status: data.analysis_status,
        email: data.email
    });
}
