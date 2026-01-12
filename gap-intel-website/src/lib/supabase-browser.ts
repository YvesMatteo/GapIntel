'use client';

import { createBrowserClient } from '@supabase/ssr';

export function createClient() {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

    if (!supabaseUrl || !supabaseAnonKey) {
        // Return a mock client during build if env vars not available
        console.warn('Supabase credentials not configured');
        return null as any;
    }

    return createBrowserClient(supabaseUrl, supabaseAnonKey);
}
