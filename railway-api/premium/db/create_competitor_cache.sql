-- Competitor Cache Table
-- Stores cached competitor data with 24h TTL
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS competitor_cache (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    channel_id TEXT UNIQUE NOT NULL,
    data JSONB NOT NULL,
    cached_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_competitor_cache_channel_id ON competitor_cache(channel_id);

-- Index for TTL cleanup
CREATE INDEX IF NOT EXISTS idx_competitor_cache_cached_at ON competitor_cache(cached_at);

-- RLS Policies (service role only)
ALTER TABLE competitor_cache ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
CREATE POLICY "Service role full access" ON competitor_cache
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Comment
COMMENT ON TABLE competitor_cache IS 'Caches competitor channel data for 24h to reduce API calls';
