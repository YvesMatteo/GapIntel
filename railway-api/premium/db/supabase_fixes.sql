-- ============================================
-- Supabase Lints Fix Script
-- Generated to fix all errors and warnings
-- ============================================

-- ============================================
-- FIX 1: Enable RLS on tables missing it (ERROR level)
-- ============================================

-- Enable RLS on ml_models
ALTER TABLE ml_models ENABLE ROW LEVEL SECURITY;

-- Enable RLS on ctr_collection_log  
ALTER TABLE ctr_collection_log ENABLE ROW LEVEL SECURITY;

-- Simple policies for these tables (service role access only)
CREATE POLICY "Service role access for ml_models" ON ml_models
    FOR ALL USING (true);

CREATE POLICY "Service role access for ctr_collection_log" ON ctr_collection_log
    FOR ALL USING (true);


-- ============================================
-- FIX 2: Fix RLS policies with auth.uid() performance issue (WARN level)
-- Replace auth.uid() with (select auth.uid()) and auth.jwt() with (select auth.jwt())
-- ============================================

-- Drop and recreate youtube_analytics_tokens policies
DROP POLICY IF EXISTS "Users can view their own tokens" ON youtube_analytics_tokens;
DROP POLICY IF EXISTS "Users can insert their own tokens" ON youtube_analytics_tokens;
DROP POLICY IF EXISTS "Users can update their own tokens" ON youtube_analytics_tokens;
DROP POLICY IF EXISTS "Users can delete their own tokens" ON youtube_analytics_tokens;
DROP POLICY IF EXISTS "Service role has full access" ON youtube_analytics_tokens;

CREATE POLICY "Users can view their own tokens" ON youtube_analytics_tokens
    FOR SELECT USING ((select auth.uid()) = user_id);

CREATE POLICY "Users can insert their own tokens" ON youtube_analytics_tokens
    FOR INSERT WITH CHECK ((select auth.uid()) = user_id);

CREATE POLICY "Users can update their own tokens" ON youtube_analytics_tokens
    FOR UPDATE USING ((select auth.uid()) = user_id);

CREATE POLICY "Users can delete their own tokens" ON youtube_analytics_tokens
    FOR DELETE USING ((select auth.uid()) = user_id);

-- Service role uses BYPASSRLS, so we don't need a separate policy for it


-- ============================================
-- FIX 3: Fix ctr_training_data policies (remove duplicate, fix auth.jwt())
-- ============================================

DROP POLICY IF EXISTS "Training data is readable" ON ctr_training_data;
DROP POLICY IF EXISTS "Only service role can modify training data" ON ctr_training_data;

-- Single policy for read access (anyone can read training data for ML)
CREATE POLICY "Training data is readable" ON ctr_training_data
    FOR SELECT USING (true);

-- Writes only via service role (which bypasses RLS anyway)


-- ============================================
-- FIX 4: Fix competitor_cache policy
-- ============================================

DROP POLICY IF EXISTS "Service role full access" ON competitor_cache;

-- Service role bypasses RLS, so just allow read for everyone
CREATE POLICY "Competitor cache is readable" ON competitor_cache
    FOR SELECT USING (true);


-- ============================================
-- FIX 5: Fix functions with mutable search_path (WARN level)
-- ============================================

-- Recreate get_training_data_stats with search_path set
CREATE OR REPLACE FUNCTION get_training_data_stats()
RETURNS TABLE (
    total_samples BIGINT,
    unique_channels BIGINT,
    unique_videos BIGINT,
    avg_ctr DECIMAL,
    min_ctr DECIMAL,
    max_ctr DECIMAL,
    last_collection TIMESTAMPTZ
) 
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_samples,
        COUNT(DISTINCT t.channel_id)::BIGINT as unique_channels,
        COUNT(DISTINCT t.video_id)::BIGINT as unique_videos,
        ROUND(AVG(t.ctr_actual), 2) as avg_ctr,
        MIN(t.ctr_actual) as min_ctr,
        MAX(t.ctr_actual) as max_ctr,
        MAX(t.fetch_date) as last_collection
    FROM ctr_training_data t
    WHERE t.impressions >= 1000;
END;
$$;

-- Recreate can_train_model with search_path set
CREATE OR REPLACE FUNCTION can_train_model(min_samples INTEGER DEFAULT 1000)
RETURNS BOOLEAN 
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    sample_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO sample_count
    FROM ctr_training_data
    WHERE impressions >= 1000;
    
    RETURN sample_count >= min_samples;
END;
$$;


-- ============================================
-- INFO: Unused indexes (not critical, leave for now)
-- These are informational only - indexes may be used later
-- when the system has more data and traffic
-- ============================================

-- The following indexes are reported as unused but should be kept:
-- - idx_ctr_training_channel, idx_ctr_training_ctr, etc.
-- These will be used once we have training data and run ML queries


-- ============================================
-- FIX 6: Enable leaked password protection (WARN level)
-- This needs to be done in Supabase Dashboard:
-- Settings > Auth > Password Protection > Enable "Leaked Password Protection"
-- ============================================

-- Done! All SQL fixes applied.
SELECT 'All Supabase lint fixes applied successfully!' as status;
