import { NextRequest, NextResponse } from "next/server";

const RAILWAY_API_URL = process.env.RAILWAY_API_URL || "https://thriving-presence-production-ca4a.up.railway.app";
const API_SECRET_KEY = process.env.API_SECRET_KEY || "";

/**
 * GET /api/youtube-analytics/callback
 * Handle OAuth callback from Google
 */
export async function GET(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const code = searchParams.get("code");
    const state = searchParams.get("state");
    const error = searchParams.get("error");

    // Handle OAuth errors
    if (error) {
        return NextResponse.redirect(
            new URL(`/dashboard/connect-analytics?status=error&message=${encodeURIComponent(error)}`, request.url)
        );
    }

    if (!code || !state) {
        return NextResponse.redirect(
            new URL(`/dashboard/connect-analytics?status=error&message=${encodeURIComponent("Missing code or state")}`, request.url)
        );
    }

    try {
        // Forward the callback to the Railway backend
        const response = await fetch(
            `${RAILWAY_API_URL}/api/youtube-analytics/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`,
            {
                headers: {
                    "X-API-Key": API_SECRET_KEY,
                },
            }
        );

        const data = await response.json();

        if (response.ok && data.status === "success") {
            return NextResponse.redirect(
                new URL("/dashboard/connect-analytics?status=success", request.url)
            );
        } else {
            const errorMsg = data.message || data.error || "Failed to complete authorization";
            return NextResponse.redirect(
                new URL(`/dashboard/connect-analytics?status=error&message=${encodeURIComponent(errorMsg)}`, request.url)
            );
        }
    } catch (error) {
        console.error("Error in YouTube Analytics callback:", error);
        return NextResponse.redirect(
            new URL(`/dashboard/connect-analytics?status=error&message=${encodeURIComponent("Server error during authorization")}`, request.url)
        );
    }
}
