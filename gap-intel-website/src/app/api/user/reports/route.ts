import { createClient } from "@/lib/supabase-server";
import { NextResponse } from "next/server";

export async function GET() {
    try {
        const supabase = await createClient();

        // Get current user
        const { data: { user }, error: authError } = await supabase.auth.getUser();

        if (authError || !user) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        // Get user's reports
        const { data: reports, error: reportsError } = await supabase
            .from("user_reports")
            .select("*")
            .eq("user_id", user.id)
            .order("created_at", { ascending: false });

        if (reportsError) {
            // Table might not exist yet - return empty array
            console.error("Error fetching reports:", reportsError);
            return NextResponse.json({ reports: [] });
        }

        return NextResponse.json({ reports });
    } catch (error) {
        console.error("Error in user reports API:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
    }
}
