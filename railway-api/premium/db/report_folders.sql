-- Report Folders Table
-- Organize reports into folders

CREATE TABLE IF NOT EXISTS report_folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    color TEXT DEFAULT '#6366f1',
    icon TEXT DEFAULT '📁',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, name)
);

-- Add folder_id to user_reports
ALTER TABLE user_reports ADD COLUMN IF NOT EXISTS folder_id UUID REFERENCES report_folders(id) ON DELETE SET NULL;
ALTER TABLE user_reports ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT false;
ALTER TABLE user_reports ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_user_reports_folder ON user_reports(folder_id);
CREATE INDEX IF NOT EXISTS idx_user_reports_deleted ON user_reports(is_deleted);
CREATE INDEX IF NOT EXISTS idx_report_folders_user ON report_folders(user_id);

-- RLS Policies for report_folders
ALTER TABLE report_folders ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own folders" ON report_folders
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can create their own folders" ON report_folders
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own folders" ON report_folders
    FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY "Users can delete their own folders" ON report_folders
    FOR DELETE USING (user_id = auth.uid());

-- Service role access
CREATE POLICY "Service role full access to report_folders" ON report_folders 
    FOR ALL TO service_role USING (true) WITH CHECK (true);
