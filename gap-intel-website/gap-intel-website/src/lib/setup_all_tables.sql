-- COMPREHENSIVE DB SETUP SCRIPT
-- Run this in Supabase SQL Editor to support Dashboard & Pricing features

-- 1. Add missing columns to user_reports
ALTER TABLE user_reports ADD COLUMN IF NOT EXISTS channel_thumbnail TEXT;
ALTER TABLE user_reports ADD COLUMN IF NOT EXISTS folder_id UUID;

-- 2. Create report_folders table
CREATE TABLE IF NOT EXISTS report_folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    icon TEXT DEFAULT '📁',
    color TEXT DEFAULT '#6366f1',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Enable RLS on report_folders
ALTER TABLE report_folders ENABLE ROW LEVEL SECURITY;

-- 4. RLS Policies for report_folders

-- Allow users to view their own folders
DROP POLICY IF EXISTS "Users can view own folders" ON report_folders;
CREATE POLICY "Users can view own folders" 
ON report_folders FOR SELECT 
TO authenticated 
USING (auth.uid() = user_id);

-- Allow users to create their own folders
DROP POLICY IF EXISTS "Users can create own folders" ON report_folders;
CREATE POLICY "Users can create own folders" 
ON report_folders FOR INSERT 
TO authenticated 
WITH CHECK (auth.uid() = user_id);

-- Allow users to delete their own folders
DROP POLICY IF EXISTS "Users can delete own folders" ON report_folders;
CREATE POLICY "Users can delete own folders" 
ON report_folders FOR DELETE 
TO authenticated 
USING (auth.uid() = user_id);

-- Allow users to update their own folders
DROP POLICY IF EXISTS "Users can update own folders" ON report_folders;
CREATE POLICY "Users can update own folders" 
ON report_folders FOR UPDATE 
TO authenticated 
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- 5. Foreign key constraint for folder_id in user_reports (optional but verifying)
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'user_reports_folder_id_fkey'
    ) THEN 
        ALTER TABLE user_reports 
        ADD CONSTRAINT user_reports_folder_id_fkey 
        FOREIGN KEY (folder_id) 
        REFERENCES report_folders(id) 
        ON DELETE SET NULL;
    END IF; 
END $$;
