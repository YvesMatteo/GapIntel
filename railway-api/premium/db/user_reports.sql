-- User Reports Table - Links reports to authenticated users
-- Run this in Supabase SQL Editor

-- Create user_reports table
CREATE TABLE IF NOT EXISTS user_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    access_key TEXT UNIQUE NOT NULL,
    channel_name TEXT NOT NULL,
    channel_handle TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    report_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add user_id column to existing user_subscriptions table
ALTER TABLE user_subscriptions 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_reports_user ON user_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_access_key ON user_reports(access_key);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON user_subscriptions(user_id);

-- Enable RLS on user_reports
ALTER TABLE user_reports ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own reports
CREATE POLICY "Users can view own reports" 
ON user_reports FOR SELECT 
TO authenticated 
USING (auth.uid() = user_id);

-- Policy: Service role can do everything
CREATE POLICY "Service role full access on reports" 
ON user_reports FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);

-- Add update timestamp trigger to user_reports
CREATE OR REPLACE FUNCTION update_report_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_report_timestamp_trigger ON user_reports;
CREATE TRIGGER update_report_timestamp_trigger
    BEFORE UPDATE ON user_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_report_timestamp();
