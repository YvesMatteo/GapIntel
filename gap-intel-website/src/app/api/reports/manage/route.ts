import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
);

// DELETE a report (hard delete)
export async function DELETE(req: NextRequest) {
    try {
        const { searchParams } = new URL(req.url);
        const reportId = searchParams.get("id");

        if (!reportId) {
            return NextResponse.json({ error: "Report ID required" }, { status: 400 });
        }

        // Hard delete - actually remove the record from the database
        const { error } = await supabase
            .from("user_reports")
            .delete()
            .eq("id", reportId);

        if (error) {
            console.error("Delete error:", error);
            return NextResponse.json({ error: error.message }, { status: 500 });
        }

        return NextResponse.json({ success: true });
    } catch (error) {
        console.error("Delete report error:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
    }
}

// PATCH to update report (move to folder)
export async function PATCH(req: NextRequest) {
    try {
        const body = await req.json();
        const { reportId, folderId } = body;

        if (!reportId) {
            return NextResponse.json({ error: "Report ID required" }, { status: 400 });
        }

        const { error } = await supabase
            .from("user_reports")
            .update({ folder_id: folderId || null })
            .eq("id", reportId);

        if (error) {
            console.error("Update error:", error);
            return NextResponse.json({ error: error.message }, { status: 500 });
        }

        return NextResponse.json({ success: true });
    } catch (error) {
        console.error("Update report error:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
    }
}
