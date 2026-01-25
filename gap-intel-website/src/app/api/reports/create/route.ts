import { createClient } from "@/lib/supabase-server";
import { NextRequest, NextResponse } from "next/server";
import { nanoid } from "nanoid";

// Tier limits for analyses per month
const TIER_LIMITS: Record<string, number> = {
    free: 1,      // 1 free analysis per month
    starter: 1,
    pro: 5,
    enterprise: 25,
};

// Tier features - aligned with PRICING_PLAN.md
const TIER_FEATURES: Record<string, {
    videoCount: number;
    premium: boolean;
    maxGaps: number | null;      // null = unlimited
    maxComments: number | null;  // null = unlimited
}> = {
    free: {
        videoCount: 3,
        premium: false,
        maxGaps: 3,        // Top 3 gaps only per PRICING_PLAN.md
        maxComments: 100,  // Limited comment analysis per PRICING_PLAN.md
    },
    starter: {
        videoCount: 10,
        premium: false,
        maxGaps: null,     // Unlimited gaps
        maxComments: null, // Unlimited comments
    },
    pro: {
        videoCount: 25,
        premium: true,
        maxGaps: null,
        maxComments: null,
    },
    enterprise: {
        videoCount: 100,
        premium: true,
        maxGaps: null,
        maxComments: null,
    },
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
        const { channelName, channelHandle, channelThumbnail, includeShorts } = body;

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
        const language = subscription?.preferred_language || "en";

        // Check if user has reached their limit
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

        // Create report record - include tier, email, and video_count for recovery purposes
        // These extra columns allow stuck job recovery to re-queue with correct user data
        const reportData: Record<string, unknown> = {
            user_id: user.id,
            access_key: accessKey,
            channel_name: channelName,
            channel_handle: channelHandle || channelName,
            channel_thumbnail: channelThumbnail || null,
            status: "pending",
            // Recovery metadata fields (added Jan 2026)
            tier: tier,
            user_email: user.email,
            video_count: tierFeatures.videoCount,
            include_shorts: includeShorts !== false,
            language: language,
        };

        const { error: reportError } = await supabase
            .from("user_reports")
            .insert(reportData);

        if (reportError) {
            console.error("Error creating report:", reportError);
            return NextResponse.json({
                error: "Failed to create report",
                details: reportError.message,
                code: reportError.code
            }, { status: 500 });
        }

        // Increment usage counter (or create subscription record for free tier)
        if (subscription) {
            await supabase
                .from("user_subscriptions")
                .update({ analyses_this_month: analysesThisMonth + 1 })
                .eq("user_email", user.email);
        } else {
            // Create a free tier subscription record for tracking
            await supabase
                .from("user_subscriptions")
                .insert({
                    user_email: user.email,
                    tier: "free",
                    analyses_this_month: 1,
                    status: "active",
                });
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
                            language: language,
                            max_gaps: tierFeatures.maxGaps,
                            max_comments: tierFeatures.maxComments,
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
            // Fire and don't wait - but handle failure properly
            // If Railway trigger fails after all retries, mark as "awaiting_retry"
            // so the recovery system knows to pick it up
            triggerRailway().then(async (success) => {
                if (!success) {
                    console.error("Railway trigger failed after all retries - marking for recovery");
                    // Update status to indicate Railway needs to pick this up
                    // Keep as "pending" but add retry_count=0 and updated_at so recovery finds it
                    await supabase
                        .from("user_reports")
                        .update({
                            retry_count: 0,
                            updated_at: new Date().toISOString(),
                            current_phase: "Waiting for processing server"
                        })
                        .eq("access_key", accessKey);
                }
            }).catch(err => {
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
