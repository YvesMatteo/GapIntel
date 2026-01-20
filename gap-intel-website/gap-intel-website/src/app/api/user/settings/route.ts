import { createClient } from "@/lib/supabase-server";
import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
    try {
        const supabase = await createClient();
        const { data: { user }, error: authError } = await supabase.auth.getUser();

        if (authError || !user) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        const { data: subscription } = await supabase
            .from("user_subscriptions")
            .select("preferred_language")
            .eq("user_email", user.email)
            .single();

        return NextResponse.json({
            preferred_language: subscription?.preferred_language || "en"
        });
    } catch (error) {
        console.error("Error fetching settings:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
    }
}

export async function PATCH(req: NextRequest) {
    try {
        const supabase = await createClient();
        const { data: { user }, error: authError } = await supabase.auth.getUser();

        if (authError || !user) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        const body = await req.json();
        const { preferred_language } = body;

        // Validate language
        const validLanguages = ["en", "de", "fr", "it", "es"];
        if (!validLanguages.includes(preferred_language)) {
            return NextResponse.json({ error: "Invalid language" }, { status: 400 });
        }

        const { error: updateError } = await supabase
            .from("user_subscriptions")
            .update({ preferred_language })
            .eq("user_email", user.email);

        if (updateError) {
            console.error("Error updating language:", updateError);
            return NextResponse.json({ error: "Failed to update" }, { status: 500 });
        }

        return NextResponse.json({ success: true, preferred_language });
    } catch (error) {
        console.error("Error updating settings:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
    }
}
