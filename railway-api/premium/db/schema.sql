-- ================================================
-- Premium Analysis Database Schema
-- For ML training data and analysis results
-- ================================================

-- Video performance data for ML training
CREATE TABLE IF NOT EXISTS video_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id TEXT NOT NULL,
    video_id TEXT UNIQUE NOT NULL,
    title TEXT,
    description TEXT,
    published_at TIMESTAMP,
    thumbnail_url TEXT,
    
    -- Core metrics
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    
    -- Velocity metrics (for trajectory prediction)
    views_1h INTEGER,
    views_6h INTEGER,
    views_24h INTEGER,
    views_7d INTEGER,
    views_30d INTEGER,
    
    -- Engagement metrics
    engagement_rate FLOAT,
    ctr_proxy FLOAT,
    avg_view_duration FLOAT,
    
    -- Metadata
    duration_seconds INTEGER,
    category_id TEXT,
    tags JSONB,
    
    -- Computed scores
    viral_score FLOAT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_video_performance_channel ON video_performance(channel_id);
CREATE INDEX IF NOT EXISTS idx_video_performance_published ON video_performance(published_at DESC);


-- Thumbnail features for ML training
CREATE TABLE IF NOT EXISTS thumbnail_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id TEXT REFERENCES video_performance(video_id) ON DELETE CASCADE,
    
    -- Color features
    dominant_colors JSONB,
    avg_saturation FLOAT,
    avg_brightness FLOAT,
    contrast_score FLOAT,
    color_diversity FLOAT,
    warm_color_ratio FLOAT,
    has_red_accent BOOLEAN,
    
    -- Face features
    face_count INTEGER DEFAULT 0,
    face_area_ratio FLOAT,
    has_eye_contact BOOLEAN,
    faces_are_large BOOLEAN,
    
    -- Text features
    has_text BOOLEAN DEFAULT FALSE,
    word_count INTEGER DEFAULT 0,
    text_area_ratio FLOAT,
    extracted_text TEXT,
    uses_numbers BOOLEAN,
    uses_all_caps BOOLEAN,
    
    -- Composition features
    edge_density FLOAT,
    rule_of_thirds_score FLOAT,
    visual_complexity FLOAT,
    mobile_readability_score FLOAT,
    
    -- Full feature vector (for ML models)
    feature_vector FLOAT[],
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_thumbnail_video ON thumbnail_features(video_id);


-- Competitor tracking
CREATE TABLE IF NOT EXISTS competitor_channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_channel_id TEXT NOT NULL,
    competitor_channel_id TEXT NOT NULL,
    competitor_name TEXT,
    
    -- Discovery metadata
    discovery_method TEXT,  -- 'manual', 'auto_search', 'similar_channels'
    relevance_score FLOAT DEFAULT 0.5,
    
    -- Relationship
    size_ratio FLOAT,  -- competitor subs / target subs
    
    -- Active tracking
    is_active BOOLEAN DEFAULT TRUE,
    
    added_at TIMESTAMP DEFAULT NOW(),
    last_analyzed TIMESTAMP,
    
    UNIQUE(target_channel_id, competitor_channel_id)
);

CREATE INDEX IF NOT EXISTS idx_competitor_target ON competitor_channels(target_channel_id);


-- ML prediction history
CREATE TABLE IF NOT EXISTS ml_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id TEXT,
    video_id TEXT,
    
    -- Prediction details
    prediction_type TEXT,  -- 'ctr', 'views_7d', 'views_30d', 'viral'
    input_features JSONB,
    predicted_value FLOAT,
    confidence FLOAT,
    
    -- Actual outcome (updated after video publishes)
    actual_value FLOAT,
    prediction_error FLOAT,
    
    -- Metadata
    model_version TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- For tracking accuracy over time
    evaluated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_prediction_type ON ml_predictions(prediction_type);
CREATE INDEX IF NOT EXISTS idx_prediction_channel ON ml_predictions(channel_id);


-- Premium analysis results (cached for faster access)
CREATE TABLE IF NOT EXISTS premium_analysis_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    access_key TEXT UNIQUE NOT NULL,
    channel_id TEXT NOT NULL,
    channel_name TEXT,
    
    -- Analysis type
    analysis_type TEXT DEFAULT 'full',  -- 'full', 'quick', 'thumbnail_only'
    
    -- Results (stored as JSONB for flexibility)
    thumbnail_analysis JSONB,
    competitor_analysis JSONB,
    ctr_predictions JSONB,
    gap_analysis JSONB,
    recommendations JSONB,
    
    -- Report generation
    report_html TEXT,
    report_generated_at TIMESTAMP,
    
    -- Metadata
    status TEXT DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    error_message TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cache_access_key ON premium_analysis_cache(access_key);
CREATE INDEX IF NOT EXISTS idx_cache_channel ON premium_analysis_cache(channel_id);


-- ================================================
-- Row Level Security (RLS) Policies
-- ================================================

-- Enable RLS
ALTER TABLE video_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE thumbnail_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE competitor_channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE ml_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE premium_analysis_cache ENABLE ROW LEVEL SECURITY;

-- Service role full access for all tables
CREATE POLICY "Service role full access on video_performance" 
ON video_performance FOR ALL TO service_role
USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access on thumbnail_features" 
ON thumbnail_features FOR ALL TO service_role
USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access on competitor_channels" 
ON competitor_channels FOR ALL TO service_role
USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access on ml_predictions" 
ON ml_predictions FOR ALL TO service_role
USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access on premium_analysis_cache" 
ON premium_analysis_cache FOR ALL TO service_role
USING (true) WITH CHECK (true);

-- Anon can read cached results by access_key
CREATE POLICY "Anon read premium cache by access key" 
ON premium_analysis_cache FOR SELECT TO anon
USING (true);
