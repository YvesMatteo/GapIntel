import { NextRequest, NextResponse } from "next/server";

const RAILWAY_API_URL = process.env.RAILWAY_API_URL || "https://thriving-presence-production-ca4a.up.railway.app";
const API_SECRET_KEY = process.env.API_SECRET_KEY || "";

/**
 * DELETE /api/youtube-analytics/disconnect
 * Disconnect YouTube Analytics access for a user
 */
export async function DELETE(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const userId = searchParams.get("user_id");

    if (!userId) {
        return NextResponse.json({ error: "user_id required" }, { status: 400 });
    }

    try {
        const response = await fetch(
            `${RAILWAY_API_URL}/api/youtube-analytics/disconnect?user_id=${userId}`,
            {
                method: "DELETE",
                headers: {
                    "X-API-Key": API_SECRET_KEY,
                },
            }
        );

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("Error disconnecting YouTube Analytics:", error);
        return NextResponse.json(
            { error: "Failed to disconnect" },
            { status: 500 }
        );
    }
}
