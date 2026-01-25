-- Add recovery metadata columns to user_reports
-- These columns store job parameters so stuck jobs can be recovered with correct values

-- User email for notification when job is recovered
ALTER TABLE user_reports ADD COLUMN IF NOT EXISTS user_email TEXT;

-- Tier determines video count and features
ALTER TABLE user_reports ADD COLUMN IF NOT EXISTS tier TEXT DEFAULT 'free';

-- Number of videos to analyze
ALTER TABLE user_reports ADD COLUMN IF NOT EXISTS video_count INTEGER DEFAULT 10;

-- Whether to include YouTube Shorts
ALTER TABLE user_reports ADD COLUMN IF NOT EXISTS include_shorts BOOLEAN DEFAULT TRUE;

-- Report language
ALTER TABLE user_reports ADD COLUMN IF NOT EXISTS language TEXT DEFAULT 'en';

-- Add comment explaining purpose
COMMENT ON COLUMN user_reports.user_email IS 'User email for recovery notifications';
COMMENT ON COLUMN user_reports.tier IS 'Subscription tier (free, starter, pro, enterprise)';
COMMENT ON COLUMN user_reports.video_count IS 'Number of videos to analyze';
COMMENT ON COLUMN user_reports.include_shorts IS 'Whether to include YouTube Shorts in analysis';
COMMENT ON COLUMN user_reports.language IS 'Report language code (en, de, fr, es, it)';

-- Backfill existing records with user_email from user_subscriptions
UPDATE user_reports ur
SET user_email = us.user_email,
    tier = us.tier
FROM user_subscriptions us
WHERE ur.user_id = us.user_id
  AND ur.user_email IS NULL;
