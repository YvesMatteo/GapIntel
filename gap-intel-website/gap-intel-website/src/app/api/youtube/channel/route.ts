import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest) {
    const { searchParams } = new URL(req.url);
    const input = searchParams.get('query') || searchParams.get('input');

    if (!input) {
        return NextResponse.json({ error: 'Channel input is required' }, { status: 400 });
    }

    const apiKey = process.env.YOUTUBE_API_KEY;
    if (!apiKey) {
        return NextResponse.json({ error: 'YouTube API not configured' }, { status: 500 });
    }

    try {
        // Parse input - could be @handle or URL
        let handle = input.trim();

        // Extract handle from URL if provided
        if (handle.includes('youtube.com') || handle.includes('youtu.be')) {
            // Extract @handle or channel ID from URL
            const urlMatch = handle.match(/@([\w-]+)|\/channel\/(UC[\w-]+)|\/c\/([\w-]+)/);
            if (urlMatch) {
                handle = urlMatch[1] ? `@${urlMatch[1]}` : urlMatch[2] || urlMatch[3];
            }
        }

        // Ensure handle starts with @
        if (!handle.startsWith('@') && !handle.startsWith('UC')) {
            handle = `@${handle}`;
        }

        // Use forHandle parameter for accurate direct lookup (no search needed)
        const handleWithoutAt = handle.replace('@', '');
        const channelUrl = `https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&forHandle=${encodeURIComponent(handleWithoutAt)}&key=${apiKey}`;
        const channelRes = await fetch(channelUrl);
        const channelData = await channelRes.json();

        let channelItem = channelData.items?.[0];

        // Fallback: If handle lookup failed, try search by query
        if (!channelItem) {
            console.log(`Handle lookup failed for ${handle}, trying search fallback...`);
            const searchInput = input.replace("@", "");
            const searchUrl = `https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q=${encodeURIComponent(searchInput)}&key=${apiKey}&maxResults=1`;
            const searchRes = await fetch(searchUrl);
            const searchData = await searchRes.json();

            if (searchData.items && searchData.items.length > 0) {
                const channelId = searchData.items[0].id.channelId; // Search returns snippet with channelId
                // Need to fetch stats now
                const statsUrl = `https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&id=${channelId}&key=${apiKey}`;
                const statsRes = await fetch(statsUrl);
                const statsData = await statsRes.json();
                channelItem = statsData.items?.[0];
            }
        }

        if (!channelItem) {
            // Log the error from Google to help debug quota headers/etc
            if (channelData.error) {
                console.error("Google API Error:", channelData.error);
                return NextResponse.json({ error: channelData.error.message }, { status: channelData.error.code || 400 });
            }
            return NextResponse.json({ error: 'Channel not found' }, { status: 404 });
        }

        const channel = channelItem;
        const subscriberCount = parseInt(channel.statistics.subscriberCount);

        // Format subscriber count (e.g., 1.2M, 50K)
        const formatSubscribers = (count: number) => {
            if (count >= 1000000) {
                return `${(count / 1000000).toFixed(1)}M`;
            } else if (count >= 1000) {
                return `${(count / 1000).toFixed(1)}K`;
            }
            return count.toString();
        };

        return NextResponse.json({
            title: channel.snippet.title,
            subscriberCount: formatSubscribers(subscriberCount),
            subscriberCountRaw: subscriberCount,
            thumbnailUrl: channel.snippet.thumbnails.default.url,
            channelId: channel.id
        });

    } catch (error) {
        console.error('YouTube API error:', error);
        return NextResponse.json({ error: 'Failed to fetch channel info' }, { status: 500 });
    }
}
