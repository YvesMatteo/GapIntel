import { NextRequest, NextResponse } from "next/server";

const RAILWAY_API_URL = process.env.RAILWAY_API_URL || "https://thriving-presence-production-ca4a.up.railway.app";
const API_SECRET_KEY = process.env.API_SECRET_KEY || "";

/**
 * GET /api/youtube-analytics/dashboard
 * Get channel analytics dashboard data for a connected user
 */
export async function GET(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const userId = searchParams.get("user_id");
    const days = searchParams.get("days") || "28";

    if (!userId) {
        return NextResponse.json({ error: "user_id required" }, { status: 400 });
    }

    try {
        const response = await fetch(
            `${RAILWAY_API_URL}/api/youtube-analytics/dashboard?user_id=${userId}&days=${days}`,
            {
                headers: {
                    "X-API-Key": API_SECRET_KEY,
                },
            }
        );

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("Error fetching YouTube Analytics dashboard:", error);
        return NextResponse.json(
            { error: "Failed to fetch analytics" },
            { status: 500 }
        );
    }
}
