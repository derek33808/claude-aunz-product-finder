-- Seed data for testing

-- Sample products
INSERT INTO products (platform, platform_id, title, category, price, currency, rating, review_count, image_url, product_url) VALUES
('ebay_au', 'test_001', 'Wireless Bluetooth Earbuds TWS Headphones', 'Electronics > Audio', 29.99, 'AUD', 4.5, 1250, 'https://example.com/img1.jpg', 'https://ebay.com.au/itm/test_001'),
('ebay_au', 'test_002', 'Smart Watch Fitness Tracker Heart Rate Monitor', 'Electronics > Wearables', 45.00, 'AUD', 4.2, 890, 'https://example.com/img2.jpg', 'https://ebay.com.au/itm/test_002'),
('ebay_au', 'test_003', 'Portable Phone Charger Power Bank 20000mAh', 'Electronics > Accessories', 35.50, 'AUD', 4.7, 2100, 'https://example.com/img3.jpg', 'https://ebay.com.au/itm/test_003'),
('ebay_nz', 'test_004', 'LED Desk Lamp USB Rechargeable', 'Home & Garden > Lighting', 25.00, 'NZD', 4.3, 560, 'https://example.com/img4.jpg', 'https://ebay.com.au/itm/test_004'),
('trademe', 'test_005', 'Organic Cotton T-Shirt Unisex', 'Clothing > Tops', 32.00, 'NZD', 4.6, 340, 'https://example.com/img5.jpg', 'https://trademe.co.nz/listing/test_005')
ON CONFLICT (platform, platform_id) DO NOTHING;

-- Sample price history
INSERT INTO price_history (product_id, price, recorded_at)
SELECT id, price * 1.1, NOW() - INTERVAL '30 days' FROM products WHERE platform_id = 'test_001'
UNION ALL
SELECT id, price * 1.05, NOW() - INTERVAL '15 days' FROM products WHERE platform_id = 'test_001'
UNION ALL
SELECT id, price, NOW() FROM products WHERE platform_id = 'test_001';

-- Sample Google Trends data
INSERT INTO google_trends (keyword, region, interest, related_queries) VALUES
('wireless earbuds', 'AU', 75, '{"top": ["airpods", "samsung buds", "jbl earbuds"], "rising": ["bone conduction"]}'),
('wireless earbuds', 'NZ', 68, '{"top": ["airpods", "sony wf"], "rising": ["workout earbuds"]}'),
('fitness tracker', 'AU', 62, '{"top": ["fitbit", "garmin", "apple watch"], "rising": ["sleep tracker"]}');

-- Sample keyword metrics
INSERT INTO keyword_metrics (keyword, region, monthly_searches, competition, cpc, trend) VALUES
('wireless earbuds australia', 'AU', 12000, 0.72, 1.25, 'rising'),
('bluetooth headphones', 'AU', 8500, 0.65, 0.98, 'stable'),
('fitness watch nz', 'NZ', 3200, 0.58, 0.85, 'rising');

SELECT 'Seed data inserted successfully' AS status;
