import { NextRequest, NextResponse } from "next/server";

const RAILWAY_API_URL = process.env.RAILWAY_API_URL || "https://thriving-presence-production-ca4a.up.railway.app";
const API_SECRET_KEY = process.env.API_SECRET_KEY || "";

/**
 * GET /api/youtube-analytics/status
 * Check YouTube Analytics connection status for a user
 */
export async function GET(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const userId = searchParams.get("user_id");

    if (!userId) {
        return NextResponse.json({ error: "user_id required" }, { status: 400 });
    }

    try {
        const response = await fetch(
            `${RAILWAY_API_URL}/api/youtube-analytics/status?user_id=${userId}`,
            {
                headers: {
                    "X-API-Key": API_SECRET_KEY,
                },
            }
        );

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("Error fetching YouTube Analytics status:", error);
        return NextResponse.json(
            { error: "Failed to fetch status" },
            { status: 500 }
        );
    }
}
