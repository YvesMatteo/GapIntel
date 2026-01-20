-- Add channel_thumbnail column to user_reports table
-- Run this in Supabase SQL Editor

ALTER TABLE user_reports ADD COLUMN IF NOT EXISTS channel_thumbnail TEXT;

-- This column stores the YouTube channel profile picture URL
-- fetched during report creation
