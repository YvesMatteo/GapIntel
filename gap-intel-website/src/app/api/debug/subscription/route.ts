import { createClient } from "@supabase/supabase-js";
import { NextResponse } from "next/server";

export async function GET() {
    // Admin client to bypass RLS
    const supabaseAdmin = createClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.SUPABASE_SERVICE_ROLE_KEY!
    );

    // Fetch all subscriptions to see what is stuck in there
    const { data: subscriptions, error } = await supabaseAdmin
        .from("user_subscriptions")
        .select("*")
        .order('created_at', { ascending: false })
        .limit(10);

    return NextResponse.json({
        message: "Debug 4.0 - Post-Fix State",
        subscriptions: subscriptions || [],
        error,
        count: subscriptions?.length || 0
    });
}
