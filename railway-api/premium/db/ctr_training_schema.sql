-- ============================================
-- CTR Training Data Schema
-- ============================================
-- Stores OAuth tokens and training data for ML-based CTR prediction

-- OAuth tokens storage (encrypted)
CREATE TABLE IF NOT EXISTS youtube_analytics_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    channel_id TEXT NOT NULL,
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    scopes TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, channel_id)
);

-- Row Level Security for tokens
ALTER TABLE youtube_analytics_tokens ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own tokens" ON youtube_analytics_tokens
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own tokens" ON youtube_analytics_tokens
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own tokens" ON youtube_analytics_tokens
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own tokens" ON youtube_analytics_tokens
    FOR DELETE USING (auth.uid() = user_id);

-- Service role can access all tokens (for backend API)
CREATE POLICY "Service role has full access" ON youtube_analytics_tokens
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- ============================================
-- Training data collection
-- ============================================

CREATE TABLE IF NOT EXISTS ctr_training_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    
    -- CTR metrics from YouTube Analytics
    impressions INTEGER NOT NULL,
    clicks INTEGER NOT NULL,
    ctr_actual DECIMAL(5,2) NOT NULL,  -- The actual CTR percentage (0-100)
    
    -- Thumbnail features (JSONB for flexibility)
    thumbnail_features JSONB DEFAULT '{}',
    thumbnail_url TEXT,
    
    -- Title features
    title TEXT,
    title_length INTEGER,
    title_has_numbers BOOLEAN DEFAULT FALSE,
    title_has_question BOOLEAN DEFAULT FALSE,
    title_has_power_words BOOLEAN DEFAULT FALSE,
    title_capitalization_ratio DECIMAL(3,2) DEFAULT 0,
    
    -- Video metadata
    published_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    category_id TEXT,
    
    -- Data collection metadata
    fetch_date TIMESTAMPTZ DEFAULT NOW(),
    data_source TEXT DEFAULT 'youtube_analytics',  -- 'youtube_analytics' or 'manual'
    
    -- Ensure we don't duplicate videos
    UNIQUE(video_id)
);

-- Indexes for efficient training queries
CREATE INDEX IF NOT EXISTS idx_ctr_training_channel ON ctr_training_data(channel_id);
CREATE INDEX IF NOT EXISTS idx_ctr_training_ctr ON ctr_training_data(ctr_actual);
CREATE INDEX IF NOT EXISTS idx_ctr_training_impressions ON ctr_training_data(impressions);
CREATE INDEX IF NOT EXISTS idx_ctr_training_fetch_date ON ctr_training_data(fetch_date);

-- RLS for training data (public read for model training, restricted write)
ALTER TABLE ctr_training_data ENABLE ROW LEVEL SECURITY;

-- Anyone can read training data (it's anonymized for ML)
CREATE POLICY "Training data is readable" ON ctr_training_data
    FOR SELECT USING (true);

-- Only service role can insert/update/delete
CREATE POLICY "Only service role can modify training data" ON ctr_training_data
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- ============================================
-- Model metadata storage
-- ============================================

CREATE TABLE IF NOT EXISTS ml_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name TEXT NOT NULL,  -- 'ctr_global', 'ctr_channel_UCxxx', etc.
    model_type TEXT NOT NULL,  -- 'xgboost', 'lightgbm', etc.
    
    -- Training info
    training_samples INTEGER NOT NULL,
    training_date TIMESTAMPTZ DEFAULT NOW(),
    feature_columns TEXT[] NOT NULL,
    
    -- Performance metrics
    metrics JSONB NOT NULL DEFAULT '{}',  -- {mae, rmse, r2, etc.}
    
    -- Model file location (relative to models directory)
    model_path TEXT NOT NULL,
    
    -- Versioning
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(model_name, version)
);

-- Index for quick model lookup
CREATE INDEX IF NOT EXISTS idx_ml_models_name ON ml_models(model_name);
CREATE INDEX IF NOT EXISTS idx_ml_models_active ON ml_models(is_active) WHERE is_active = TRUE;

-- ============================================
-- Data collection tracking
-- ============================================

CREATE TABLE IF NOT EXISTS ctr_collection_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id TEXT NOT NULL,
    user_id UUID NOT NULL,
    
    -- Collection results
    videos_processed INTEGER DEFAULT 0,
    videos_collected INTEGER DEFAULT 0,
    errors TEXT[],
    
    -- Timing
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    status TEXT DEFAULT 'pending'  -- 'pending', 'running', 'completed', 'failed'
);

CREATE INDEX IF NOT EXISTS idx_collection_log_channel ON ctr_collection_log(channel_id);
CREATE INDEX IF NOT EXISTS idx_collection_log_status ON ctr_collection_log(status);

-- ============================================
-- Helper functions
-- ============================================

-- Function to get training data count
CREATE OR REPLACE FUNCTION get_training_data_stats()
RETURNS TABLE (
    total_samples BIGINT,
    unique_channels BIGINT,
    unique_videos BIGINT,
    avg_ctr DECIMAL,
    min_ctr DECIMAL,
    max_ctr DECIMAL,
    last_collection TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_samples,
        COUNT(DISTINCT channel_id)::BIGINT as unique_channels,
        COUNT(DISTINCT video_id)::BIGINT as unique_videos,
        ROUND(AVG(ctr_actual), 2) as avg_ctr,
        MIN(ctr_actual) as min_ctr,
        MAX(ctr_actual) as max_ctr,
        MAX(fetch_date) as last_collection
    FROM ctr_training_data
    WHERE impressions >= 1000;  -- Only count statistically significant samples
END;
$$ LANGUAGE plpgsql;

-- Function to check if we have enough data to train
CREATE OR REPLACE FUNCTION can_train_model(min_samples INTEGER DEFAULT 1000)
RETURNS BOOLEAN AS $$
DECLARE
    sample_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO sample_count
    FROM ctr_training_data
    WHERE impressions >= 1000;
    
    RETURN sample_count >= min_samples;
END;
$$ LANGUAGE plpgsql;
