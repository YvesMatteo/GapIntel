-- FIX USER REPORTS PERMISSIONS
-- Run this in Supabase SQL Editor

-- 1. Create table if missing
CREATE TABLE IF NOT EXISTS user_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    access_key TEXT UNIQUE NOT NULL,
    channel_name TEXT NOT NULL,
    channel_handle TEXT,
    report_data JSONB,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Enable RLS
ALTER TABLE user_reports ENABLE ROW LEVEL SECURITY;

-- 3. Policy: User can INSERT their own reports
DROP POLICY IF EXISTS "Users can create their own reports" ON user_reports;
CREATE POLICY "Users can create their own reports" 
ON user_reports FOR INSERT 
TO authenticated 
WITH CHECK (auth.uid() = user_id);

-- 4. Policy: User can SELECT their own reports
DROP POLICY IF EXISTS "Users can view their own reports" ON user_reports;
CREATE POLICY "Users can view their own reports" 
ON user_reports FOR SELECT 
TO authenticated 
USING (auth.uid() = user_id);

-- 5. Policy: Service Role full access
DROP POLICY IF EXISTS "Service role full access on reports" ON user_reports;
CREATE POLICY "Service role full access on reports" 
ON user_reports FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);
