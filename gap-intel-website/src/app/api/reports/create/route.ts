import { createClient } from "@/lib/supabase-server";
import { NextRequest, NextResponse } from "next/server";
import { nanoid } from "nanoid";

// Tier limits for analyses per month
const TIER_LIMITS: Record<string, number> = {
    free: 0,
    starter: 5,
    pro: 999999, // Unlimited
    enterprise: 999999, // Unlimited
};

// Tier features
const TIER_FEATURES: Record<string, { videoCount: number; premium: boolean }> = {
    free: { videoCount: 1, premium: false },
    starter: { videoCount: 5, premium: false },
    pro: { videoCount: 20, premium: true },
    enterprise: { videoCount: 50, premium: true },
};

export async function POST(req: NextRequest) {
    try {
        const supabase = await createClient();

        // Get current user
        const { data: { user }, error: authError } = await supabase.auth.getUser();

        if (authError || !user) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        const body = await req.json();
        const { channelName, channelHandle, includeShorts } = body;

        if (!channelName) {
            return NextResponse.json({ error: "Channel name is required" }, { status: 400 });
        }

        // Get user's subscription
        const { data: subscription, error: subError } = await supabase
            .from("user_subscriptions")
            .select("*")
            .eq("user_email", user.email)
            .single();

        // Default to free tier if no subscription
        const tier = subscription?.tier || "free";
        const analysesThisMonth = subscription?.analyses_this_month || 0;
        const limit = TIER_LIMITS[tier] || 0;

        // Check if user has reached their limit
        if (tier === "free") {
            return NextResponse.json(
                { error: "Please subscribe to create reports", requiresSubscription: true },
                { status: 403 }
            );
        }

        if (analysesThisMonth >= limit) {
            return NextResponse.json(
                { error: `You've reached your monthly limit of ${limit} reports`, limitReached: true },
                { status: 403 }
            );
        }

        // Check for existing running analysis for this channel
        const { data: existingReport } = await supabase
            .from("user_reports")
            .select("id, status")
            .eq("user_id", user.id)
            .ilike("channel_name", channelName) // Case-insensitive check
            .in("status", ["pending", "processing"])
            .single();

        if (existingReport) {
            return NextResponse.json({
                error: `An analysis for ${channelName} is already ${existingReport.status}. Please wait for it to complete.`,
                existingReport: true
            }, { status: 409 });
        }

        // Generate access key
        const accessKey = `GAP-${nanoid(12)}`;
        const tierFeatures = TIER_FEATURES[tier] || TIER_FEATURES.starter;

        // Create report record
        const { error: reportError } = await supabase
            .from("user_reports")
            .insert({
                user_id: user.id,
                access_key: accessKey,
                channel_name: channelName,
                channel_handle: channelHandle || channelName,
                status: "pending",
            });

        if (reportError) {
            console.error("Error creating report:", reportError);
            return NextResponse.json({
                error: "Failed to create report",
                details: reportError.message,
                code: reportError.code
            }, { status: 500 });
        }

        // Increment usage counter
        if (subscription) {
            await supabase
                .from("user_subscriptions")
                .update({ analyses_this_month: analysesThisMonth + 1 })
                .eq("user_email", user.email);
        }

        // Trigger Railway API with retry logic for cold starts
        const railwayUrl = process.env.RAILWAY_API_URL;
        const apiSecretKey = process.env.API_SECRET_KEY;

        const triggerRailway = async (retries = 3, delayMs = 2000): Promise<boolean> => {
            for (let attempt = 1; attempt <= retries; attempt++) {
                try {
                    console.log(`Railway trigger attempt ${attempt}/${retries}`);

                    // Use AbortController for timeout (30s to allow Railway to wake up)
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 30000);

                    const response = await fetch(`${railwayUrl}/analyze`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-API-Key": apiSecretKey || "",
                        },
                        body: JSON.stringify({
                            channel_name: channelHandle || channelName,
                            access_key: accessKey,
                            email: user.email,
                            video_count: tierFeatures.videoCount,
                            tier: tier,
                            include_shorts: includeShorts,
                        }),
                        signal: controller.signal,
                    });

                    clearTimeout(timeoutId);

                    if (response.ok) {
                        console.log("Railway API triggered successfully");
                        return true;
                    }

                    const errorText = await response.text();
                    console.error(`Railway API error (attempt ${attempt}):`, errorText);

                } catch (error) {
                    const errorMessage = error instanceof Error ? error.message : "Unknown error";
                    console.error(`Railway trigger failed (attempt ${attempt}):`, errorMessage);
                }

                // Wait before retrying (exponential backoff)
                if (attempt < retries) {
                    await new Promise(resolve => setTimeout(resolve, delayMs * attempt));
                }
            }
            return false;
        };

        if (railwayUrl) {
            // Fire and don't wait - let the response return immediately
            // The retry logic runs in the background
            triggerRailway().catch(err => {
                console.error("Background Railway trigger failed:", err);
            });
        }

        return NextResponse.json({
            success: true,
            accessKey,
            message: "Report creation started",
        });

    } catch (error) {
        console.error("Error in create report API:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
    }
}
