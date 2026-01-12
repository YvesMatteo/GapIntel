-- EMERGENCY FIX SCRIPT
-- Run this in Supabase SQL Editor to unblock subscription syncing

-- 1. Ensure user_id column exists (Critical for sync)
ALTER TABLE user_subscriptions 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

-- 2. Drop restrictive constraints to prevent sync failures on unexpected statuses
ALTER TABLE user_subscriptions DROP CONSTRAINT IF EXISTS user_subscriptions_tier_check;
ALTER TABLE user_subscriptions DROP CONSTRAINT IF EXISTS user_subscriptions_status_check;

-- 3. Ensure Service Role has full access (fixing potential RLS lockout)
DROP POLICY IF EXISTS "Service role full access on subscriptions" ON user_subscriptions;
CREATE POLICY "Service role full access on subscriptions" 
ON user_subscriptions FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);

-- 4. Ensure Users can view their own subscription (fixing "Free" display issue)
DROP POLICY IF EXISTS "Users can view own subscriptions" ON user_subscriptions;
CREATE POLICY "Users can view own subscriptions" 
ON user_subscriptions FOR SELECT 
TO authenticated 
USING (user_email = (auth.jwt() ->> 'email'));
