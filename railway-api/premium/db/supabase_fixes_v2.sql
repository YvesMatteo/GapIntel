-- ============================================
-- Additional Supabase Fixes - Stricter Policies
-- ============================================

-- Fix 1: Make ml_models more restrictive
-- Only allow SELECT for all, writes only via service role (which bypasses RLS)
DROP POLICY IF EXISTS "Service role access for ml_models" ON ml_models;

CREATE POLICY "ML models are readable" ON ml_models
    FOR SELECT USING (true);

-- No INSERT/UPDATE/DELETE policy = service role only (bypasses RLS)


-- Fix 2: Make ctr_collection_log more restrictive
DROP POLICY IF EXISTS "Service role access for ctr_collection_log" ON ctr_collection_log;

CREATE POLICY "Collection logs are readable" ON ctr_collection_log
    FOR SELECT USING (true);

-- No INSERT/UPDATE/DELETE policy = service role only (bypasses RLS)


-- ============================================
-- INFO: Unused Indexes
-- These are INFO level (not errors/warnings)
-- Keep them - they will be used once the system has data
-- ============================================

-- The 17 unused indexes are expected because:
-- 1. The tables are new (ctr_training_data, ml_models, ctr_collection_log)
-- 2. There's no training data yet
-- 3. Once data collection starts, these indexes will be used

-- If you really want to remove them to clear the INFO messages:
-- DROP INDEX IF EXISTS idx_ctr_training_channel;
-- DROP INDEX IF EXISTS idx_ctr_training_ctr;
-- (etc... but NOT recommended)


-- ============================================
-- MANUAL: Enable Leaked Password Protection
-- ============================================
-- This cannot be done via SQL. Do this in Supabase Dashboard:
-- 1. Go to: Settings > Auth > Security
-- 2. Enable "Leaked Password Protection"
-- 3. Save changes

SELECT 'Additional fixes applied! Remember to enable Leaked Password Protection in Dashboard.' as status;
