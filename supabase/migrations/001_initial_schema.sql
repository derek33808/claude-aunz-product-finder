-- AU/NZ Product Finder Database Schema
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- Products Table
-- ============================================
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform VARCHAR(50) NOT NULL,
    platform_id VARCHAR(200) NOT NULL,
    title TEXT NOT NULL,
    category VARCHAR(500),
    price DECIMAL(12, 2),
    currency VARCHAR(3) DEFAULT 'AUD',
    rating DECIMAL(3, 2),
    review_count INTEGER DEFAULT 0,
    seller_count INTEGER DEFAULT 1,
    bsr_rank INTEGER,
    image_url TEXT,
    product_url TEXT,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(platform, platform_id)
);

-- Indexes for products
CREATE INDEX IF NOT EXISTS idx_products_platform ON products(platform);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
CREATE INDEX IF NOT EXISTS idx_products_created_at ON products(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_products_title_search ON products USING gin(to_tsvector('english', title));

-- ============================================
-- Price History Table
-- ============================================
CREATE TABLE IF NOT EXISTS price_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    price DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'AUD',
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_price_history_product ON price_history(product_id);
CREATE INDEX IF NOT EXISTS idx_price_history_recorded ON price_history(recorded_at DESC);

-- ============================================
-- Google Trends Table
-- ============================================
CREATE TABLE IF NOT EXISTS google_trends (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keyword VARCHAR(500) NOT NULL,
    region VARCHAR(10) NOT NULL DEFAULT 'AU',
    interest INTEGER CHECK (interest >= 0 AND interest <= 100),
    related_queries JSONB,
    interest_over_time JSONB,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_google_trends_keyword ON google_trends(keyword);
CREATE INDEX IF NOT EXISTS idx_google_trends_region ON google_trends(region);
CREATE INDEX IF NOT EXISTS idx_google_trends_recorded ON google_trends(recorded_at DESC);

-- ============================================
-- Keyword Metrics Table
-- ============================================
CREATE TABLE IF NOT EXISTS keyword_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keyword VARCHAR(500) NOT NULL,
    region VARCHAR(10) NOT NULL DEFAULT 'AU',
    monthly_searches INTEGER,
    competition DECIMAL(5, 4) CHECK (competition >= 0 AND competition <= 1),
    cpc DECIMAL(10, 2),
    trend VARCHAR(20) CHECK (trend IN ('rising', 'stable', 'declining')),
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_keyword_metrics_keyword ON keyword_metrics(keyword);
CREATE INDEX IF NOT EXISTS idx_keyword_metrics_region ON keyword_metrics(region);

-- ============================================
-- Reports Table
-- ============================================
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    title VARCHAR(500) NOT NULL,
    report_type VARCHAR(20) NOT NULL CHECK (report_type IN ('quick', 'full', 'comparison', 'monitor')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'generating', 'completed', 'failed')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    
    -- Target
    target_type VARCHAR(20) NOT NULL CHECK (target_type IN ('product', 'keyword', 'category')),
    target_value TEXT NOT NULL,
    
    -- Analysis Data (JSONB)
    summary JSONB,
    market_analysis JSONB,
    competition JSONB,
    google_trends JSONB,
    profit_estimate JSONB,
    risk_assessment JSONB,
    recommendation JSONB,
    
    -- Scores
    overall_score DECIMAL(5, 2) CHECK (overall_score >= 0 AND overall_score <= 100),
    market_score DECIMAL(5, 2),
    competition_score DECIMAL(5, 2),
    trend_score DECIMAL(5, 2),
    profit_score DECIMAL(5, 2),
    
    -- File Paths (Supabase Storage)
    pdf_path TEXT,
    excel_path TEXT,
    
    -- Sharing
    share_token VARCHAR(64) UNIQUE,
    share_password VARCHAR(255),
    share_expires_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reports_user ON reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(report_type);
CREATE INDEX IF NOT EXISTS idx_reports_created ON reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_share_token ON reports(share_token);

-- ============================================
-- Report Products Junction Table
-- ============================================
CREATE TABLE IF NOT EXISTS report_products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(report_id, product_id)
);

-- ============================================
-- Updated At Trigger Function
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to tables
DROP TRIGGER IF EXISTS update_products_updated_at ON products;
CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_reports_updated_at ON reports;
CREATE TRIGGER update_reports_updated_at
    BEFORE UPDATE ON reports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Row Level Security (RLS)
-- ============================================

-- Enable RLS on reports table
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own reports
CREATE POLICY "Users can view own reports" ON reports
    FOR SELECT USING (
        auth.uid() = user_id OR 
        user_id IS NULL OR
        (share_token IS NOT NULL AND share_expires_at > NOW())
    );

-- Policy: Users can insert their own reports
CREATE POLICY "Users can insert own reports" ON reports
    FOR INSERT WITH CHECK (
        auth.uid() = user_id OR user_id IS NULL
    );

-- Policy: Users can update their own reports
CREATE POLICY "Users can update own reports" ON reports
    FOR UPDATE USING (
        auth.uid() = user_id OR user_id IS NULL
    );

-- Policy: Users can delete their own reports
CREATE POLICY "Users can delete own reports" ON reports
    FOR DELETE USING (
        auth.uid() = user_id
    );

-- Products table is public read
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Products are viewable by everyone" ON products
    FOR SELECT USING (true);

-- ============================================
-- Storage Buckets (run in Supabase dashboard)
-- ============================================
-- INSERT INTO storage.buckets (id, name, public)
-- VALUES ('reports', 'reports', false);

COMMENT ON TABLE products IS 'Product listings from various AU/NZ platforms';
COMMENT ON TABLE reports IS 'Generated product selection reports';
COMMENT ON TABLE google_trends IS 'Cached Google Trends data';
