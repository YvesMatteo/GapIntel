-- Add retry_count column to user_reports for stuck job recovery
-- This tracks how many times a job has been re-queued after getting stuck

ALTER TABLE user_reports ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;

-- Add index for faster stuck job queries
CREATE INDEX IF NOT EXISTS idx_user_reports_status_updated ON user_reports(status, updated_at);
