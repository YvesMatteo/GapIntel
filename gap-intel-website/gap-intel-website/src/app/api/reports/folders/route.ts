import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
);

// GET all folders for user
export async function GET(req: NextRequest) {
    try {
        const { searchParams } = new URL(req.url);
        const userId = searchParams.get("userId");

        if (!userId) {
            return NextResponse.json({ error: "User ID required" }, { status: 400 });
        }

        const { data, error } = await supabase
            .from("report_folders")
            .select("*")
            .eq("user_id", userId)
            .order("name");

        if (error) {
            return NextResponse.json({ error: error.message }, { status: 500 });
        }

        return NextResponse.json({ folders: data || [] });
    } catch (error) {
        console.error("Get folders error:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
    }
}

// POST create new folder
export async function POST(req: NextRequest) {
    try {
        const body = await req.json();
        const { userId, name, color, icon } = body;

        if (!userId || !name) {
            return NextResponse.json({ error: "User ID and name required" }, { status: 400 });
        }

        const { data, error } = await supabase
            .from("report_folders")
            .insert({
                user_id: userId,
                name: name.trim(),
                color: color || "#6366f1",
                icon: icon || "📁"
            })
            .select()
            .single();

        if (error) {
            if (error.code === "23505") {
                return NextResponse.json({ error: "Folder with this name already exists" }, { status: 400 });
            }
            return NextResponse.json({ error: error.message }, { status: 500 });
        }

        return NextResponse.json({ folder: data });
    } catch (error) {
        console.error("Create folder error:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
    }
}

// DELETE folder
export async function DELETE(req: NextRequest) {
    try {
        const { searchParams } = new URL(req.url);
        const folderId = searchParams.get("id");

        if (!folderId) {
            return NextResponse.json({ error: "Folder ID required" }, { status: 400 });
        }

        // First, unassign all reports from this folder
        await supabase
            .from("user_reports")
            .update({ folder_id: null })
            .eq("folder_id", folderId);

        // Then delete the folder
        const { error } = await supabase
            .from("report_folders")
            .delete()
            .eq("id", folderId);

        if (error) {
            return NextResponse.json({ error: error.message }, { status: 500 });
        }

        return NextResponse.json({ success: true });
    } catch (error) {
        console.error("Delete folder error:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
    }
}

// PATCH update folder
export async function PATCH(req: NextRequest) {
    try {
        const body = await req.json();
        const { folderId, name, color, icon } = body;

        if (!folderId) {
            return NextResponse.json({ error: "Folder ID required" }, { status: 400 });
        }

        const updates: Record<string, string> = {};
        if (name) updates.name = name.trim();
        if (color) updates.color = color;
        if (icon) updates.icon = icon;

        const { error } = await supabase
            .from("report_folders")
            .update(updates)
            .eq("id", folderId);

        if (error) {
            return NextResponse.json({ error: error.message }, { status: 500 });
        }

        return NextResponse.json({ success: true });
    } catch (error) {
        console.error("Update folder error:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
    }
}
