import { createAdminClient } from "@/lib/supabase-server";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
    try {
        const supabase = createAdminClient(); // Use admin client to bypass RLS

        // List all user_reports - admin view requires bypassing RLS or user being admin?
        // Since we are debugging, regular user can only see their own.
        // We will try to fetch for the current user.

        // const { data: { user } } = await supabase.auth.getUser();
        // if (!user) {
        //     return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        // }

        const { data: reports, error } = await supabase
            .from("user_reports")
            .select("*")
            .order("created_at", { ascending: false })
            .limit(20);

        if (error) {
            return NextResponse.json({ error: error.message }, { status: 500 });
        }

        return NextResponse.json({
            count: reports?.length,
            reports
        });

    } catch (error) {
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
    }
}
