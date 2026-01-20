import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest) {
    const { searchParams } = new URL(req.url);
    const input = searchParams.get('input') || 'Trymacs';
    const apiKey = process.env.YOUTUBE_API_KEY;

    if (!apiKey) {
        return NextResponse.json({ error: 'No API Key' });
    }

    const log = [];

    // 1. Try Handle Lookup
    let handle = input.trim();
    if (!handle.startsWith('@') && !handle.startsWith('UC')) handle = `@${handle}`;
    const handleWithoutAt = handle.replace('@', '');

    const handleUrl = `https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&forHandle=${encodeURIComponent(handleWithoutAt)}&key=${apiKey}`;
    log.push(`Fetching Handle: ${handleUrl.replace(apiKey, 'HIDDEN_KEY')}`);

    const handleRes = await fetch(handleUrl);
    const handleData = await handleRes.json();
    log.push({ step: 'Handle Lookup', status: handleRes.status, data: handleData });

    // 2. Try Search Lookup
    const searchUrl = `https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q=${encodeURIComponent(input)}&key=${apiKey}&maxResults=1`;
    log.push(`Fetching Search: ${searchUrl.replace(apiKey, 'HIDDEN_KEY')}`);

    const searchRes = await fetch(searchUrl);
    const searchData = await searchRes.json();
    log.push({ step: 'Search Lookup', status: searchRes.status, data: searchData });

    return NextResponse.json({
        input,
        log,
        finalDecision: (handleData.items?.length > 0) ? "Handle Found" : (searchData.items?.length > 0 ? "Search Found" : "Nothing Found")
    });
}
