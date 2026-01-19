import { NextRequest, NextResponse } from "next/server";

const RAILWAY_API_URL = process.env.RAILWAY_API_URL || "https://renewed-comfort-production.up.railway.app";
const API_SECRET_KEY = process.env.API_SECRET_KEY || "";

/**
 * GET /api/ctr-model/stats
 * Get CTR model training statistics
 */
export async function GET(request: NextRequest) {
    try {
        const response = await fetch(
            `${RAILWAY_API_URL}/api/ctr-model/stats`,
            {
                headers: {
                    "X-API-Key": API_SECRET_KEY,
                },
            }
        );

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("Error fetching CTR model stats:", error);
        return NextResponse.json(
            { error: "Failed to fetch stats" },
            { status: 500 }
        );
    }
}
