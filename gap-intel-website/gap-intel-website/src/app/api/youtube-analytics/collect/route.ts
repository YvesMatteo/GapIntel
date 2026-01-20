import { NextRequest, NextResponse } from "next/server";

const RAILWAY_API_URL = process.env.RAILWAY_API_URL || "https://thriving-presence-production-ca4a.up.railway.app";
const API_SECRET_KEY = process.env.API_SECRET_KEY || "";

/**
 * POST /api/youtube-analytics/collect
 * Trigger CTR data collection for a connected channel
 */
export async function POST(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const userId = searchParams.get("user_id");
    const maxVideos = searchParams.get("max_videos") || "100";

    if (!userId) {
        return NextResponse.json({ error: "user_id required" }, { status: 400 });
    }

    try {
        const response = await fetch(
            `${RAILWAY_API_URL}/api/youtube-analytics/collect?user_id=${userId}&max_videos=${maxVideos}`,
            {
                method: "POST",
                headers: {
                    "X-API-Key": API_SECRET_KEY,
                },
            }
        );

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("Error collecting CTR data:", error);
        return NextResponse.json(
            { error: "Failed to collect data" },
            { status: 500 }
        );
    }
}
