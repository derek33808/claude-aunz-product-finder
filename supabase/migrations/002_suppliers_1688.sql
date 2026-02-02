-- 1688 供应商缓存表
-- 用于存储本地爬虫抓取的 1688 产品数据

CREATE TABLE IF NOT EXISTS suppliers_1688 (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    offer_id VARCHAR(50) UNIQUE NOT NULL,  -- 1688 产品 ID
    title TEXT NOT NULL,                    -- 产品标题
    price DECIMAL(10, 2) NOT NULL,          -- 价格（人民币）
    product_url TEXT,                       -- 产品链接
    image_url TEXT,                         -- 图片链接
    sold_count INTEGER DEFAULT 0,           -- 销量
    supplier_name VARCHAR(255),             -- 供应商名称
    location VARCHAR(100),                  -- 供应商位置
    search_keyword VARCHAR(100),            -- 搜索关键词（用于分类查询）
    scraped_at TIMESTAMP WITH TIME ZONE,    -- 爬取时间
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_suppliers_1688_keyword ON suppliers_1688(search_keyword);
CREATE INDEX IF NOT EXISTS idx_suppliers_1688_price ON suppliers_1688(price);
CREATE INDEX IF NOT EXISTS idx_suppliers_1688_sold ON suppliers_1688(sold_count DESC);
CREATE INDEX IF NOT EXISTS idx_suppliers_1688_scraped ON suppliers_1688(scraped_at DESC);

-- 更新时间触发器
CREATE OR REPLACE FUNCTION update_suppliers_1688_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_suppliers_1688_updated_at ON suppliers_1688;
CREATE TRIGGER trigger_suppliers_1688_updated_at
    BEFORE UPDATE ON suppliers_1688
    FOR EACH ROW
    EXECUTE FUNCTION update_suppliers_1688_updated_at();

-- 添加 RLS 策略（可选，如果需要公开访问可以跳过）
ALTER TABLE suppliers_1688 ENABLE ROW LEVEL SECURITY;

-- 允许匿名读取
CREATE POLICY "Allow anonymous read" ON suppliers_1688
    FOR SELECT
    TO anon
    USING (true);

-- 允许 service role 完全访问
CREATE POLICY "Allow service role full access" ON suppliers_1688
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

COMMENT ON TABLE suppliers_1688 IS '1688 供应商产品缓存表，由本地爬虫定期更新';
