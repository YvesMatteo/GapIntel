import { NextRequest, NextResponse } from "next/server";

const RAILWAY_API_URL = process.env.RAILWAY_API_URL || "https://renewed-comfort-production.up.railway.app";
const API_SECRET_KEY = process.env.API_SECRET_KEY || "";

/**
 * GET /api/youtube-analytics/authorize
 * Start OAuth flow for YouTube Analytics
 */
export async function GET(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const userId = searchParams.get("user_id");

    if (!userId) {
        return NextResponse.json({ error: "user_id required" }, { status: 400 });
    }

    // Use the production callback URL
    const redirectUri = `${process.env.NEXT_PUBLIC_SITE_URL || "https://gapintel.online"}/api/youtube-analytics/callback`;

    try {
        const response = await fetch(
            `${RAILWAY_API_URL}/api/youtube-analytics/authorize?user_id=${userId}&redirect_uri=${encodeURIComponent(redirectUri)}`,
            {
                headers: {
                    "X-API-Key": API_SECRET_KEY,
                },
            }
        );

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("Error starting YouTube Analytics OAuth:", error);
        return NextResponse.json(
            { error: "Failed to start authorization" },
            { status: 500 }
        );
    }
}
