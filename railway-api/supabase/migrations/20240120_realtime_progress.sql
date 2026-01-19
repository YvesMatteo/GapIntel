-- Add columns for real-time progress tracking
-- Run this in Supabase SQL Editor

ALTER TABLE user_reports ADD COLUMN IF NOT EXISTS progress_percentage INTEGER DEFAULT 0;
ALTER TABLE user_reports ADD COLUMN IF NOT EXISTS current_phase TEXT DEFAULT NULL;

-- Enable Realtime on user_reports table (if not already enabled)
ALTER PUBLICATION supabase_realtime ADD TABLE user_reports;
