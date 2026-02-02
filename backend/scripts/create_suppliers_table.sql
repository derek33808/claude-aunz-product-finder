-- Create suppliers_1688 table for caching scraped 1688 data
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS suppliers_1688 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 1688 product info
    offer_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    price_range TEXT,
    moq INTEGER DEFAULT 1,
    sold_count INTEGER DEFAULT 0,
    image_url TEXT,
    product_url TEXT NOT NULL,

    -- Supplier info
    supplier_name TEXT NOT NULL,
    supplier_url TEXT,
    supplier_years INTEGER,
    supplier_rating DECIMAL(3, 2),
    is_verified BOOLEAN DEFAULT FALSE,

    -- Logistics info
    location TEXT,
    shipping_estimate TEXT,

    -- Product attributes
    weight DECIMAL(10, 3),
    dimensions TEXT,
    is_small_medium BOOLEAN DEFAULT TRUE,

    -- Search/categorization
    search_keyword TEXT NOT NULL,  -- The keyword used to find this product
    category TEXT,

    -- Timestamps
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_suppliers_1688_keyword ON suppliers_1688(search_keyword);
CREATE INDEX IF NOT EXISTS idx_suppliers_1688_price ON suppliers_1688(price);
CREATE INDEX IF NOT EXISTS idx_suppliers_1688_scraped_at ON suppliers_1688(scraped_at);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_suppliers_1688_updated_at ON suppliers_1688;
CREATE TRIGGER update_suppliers_1688_updated_at
    BEFORE UPDATE ON suppliers_1688
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable RLS (Row Level Security)
ALTER TABLE suppliers_1688 ENABLE ROW LEVEL SECURITY;

-- Create policy for public read access
CREATE POLICY "Allow public read access" ON suppliers_1688
    FOR SELECT USING (true);

-- Create policy for authenticated insert/update (for scraper)
CREATE POLICY "Allow service role full access" ON suppliers_1688
    FOR ALL USING (true) WITH CHECK (true);
