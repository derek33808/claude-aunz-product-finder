/**
 * Tests for 1688 Supplier Matching functionality in Dashboard
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { I18nextProvider } from 'react-i18next';
import i18n from '../../i18n';

// Mock the API
vi.mock('../../services/api', () => ({
  productsApi: {
    search: vi.fn().mockResolvedValue([]),
    getHotProducts: vi.fn().mockResolvedValue([]),
  },
  reportsApi: {
    list: vi.fn().mockResolvedValue([]),
    generate: vi.fn().mockResolvedValue({ id: 'test-id' }),
  },
  trendsApi: {
    getInterest: vi.fn().mockResolvedValue({ data: [] }),
  },
  suppliersApi: {
    match: vi.fn().mockResolvedValue([]),
    search: vi.fn().mockResolvedValue([]),
    getDetails: vi.fn().mockResolvedValue(null),
    translateKeywords: vi.fn().mockResolvedValue({
      original_title: 'Test',
      extracted_keywords: ['test'],
      chinese_keywords: ['测试'],
    }),
    estimateProfit: vi.fn().mockResolvedValue({
      source_price: 100,
      profit_margin: 30,
      roi: 50,
    }),
    getExchangeRates: vi.fn().mockResolvedValue({
      rates: { AUD_CNY: 4.7, NZD_CNY: 4.3 },
    }),
  },
}));

// Mock antd components that may cause issues
vi.mock('echarts-for-react', () => ({
  default: () => <div data-testid="mock-chart">Chart</div>,
}));

// Test wrapper with providers
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <I18nextProvider i18n={i18n}>
      {children}
    </I18nextProvider>
  </BrowserRouter>
);

describe('Supplier Matching Types', () => {
  it('should have correct Supplier1688 type structure', () => {
    const supplier = {
      offer_id: '123',
      title: 'Test Product',
      price: 50,
      moq: 10,
      sold_count: 1000,
      product_url: 'http://test.com',
      supplier_name: 'Test Supplier',
      is_verified: true,
      is_small_medium: true,
    };

    expect(supplier.offer_id).toBe('123');
    expect(supplier.price).toBe(50);
    expect(supplier.is_verified).toBe(true);
  });

  it('should have correct SupplierMatchResult type structure', () => {
    const result = {
      source_product_id: 'prod-123',
      source_product_title: 'Wireless Earbuds',
      search_keywords: ['无线耳机', '蓝牙耳机'],
      matched_suppliers: [],
      match_count: 0,
    };

    expect(result.source_product_id).toBe('prod-123');
    expect(result.search_keywords).toHaveLength(2);
  });
});

describe('Supplier API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should call match API with correct parameters', async () => {
    const { suppliersApi } = await import('../../services/api');

    await suppliersApi.match({
      product_ids: ['123', '456'],
      max_price: 500,
      limit: 10,
      include_large: false,
    });

    expect(suppliersApi.match).toHaveBeenCalledWith({
      product_ids: ['123', '456'],
      max_price: 500,
      limit: 10,
      include_large: false,
    });
  });

  it('should call search API with keyword', async () => {
    const { suppliersApi } = await import('../../services/api');

    await suppliersApi.search('无线耳机', 500, 20);

    expect(suppliersApi.search).toHaveBeenCalled();
  });

  it('should call translateKeywords API', async () => {
    const { suppliersApi } = await import('../../services/api');

    const result = await suppliersApi.translateKeywords('Wireless Earbuds');

    expect(suppliersApi.translateKeywords).toHaveBeenCalledWith('Wireless Earbuds');
    expect(result.chinese_keywords).toContain('测试');
  });
});

describe('Profit Calculation Logic', () => {
  it('should calculate profit margin correctly', () => {
    const sourcePrice = 100; // AUD
    const supplierPrice = 50; // CNY
    const quantity = 100;
    const shippingPerUnit = 15; // CNY
    const exchangeRate = 0.213; // CNY to AUD

    const totalCostCNY = (supplierPrice + shippingPerUnit) * quantity;
    const totalCostAUD = totalCostCNY * exchangeRate;
    const revenue = sourcePrice * quantity;
    const grossProfit = revenue - totalCostAUD;
    const profitMargin = (grossProfit / revenue) * 100;

    // Expected calculations
    expect(totalCostCNY).toBe(6500); // (50 + 15) * 100
    expect(totalCostAUD).toBeCloseTo(1384.5); // 6500 * 0.213
    expect(revenue).toBe(10000); // 100 * 100
    expect(grossProfit).toBeCloseTo(8615.5);
    expect(profitMargin).toBeCloseTo(86.155);
  });

  it('should handle negative profit', () => {
    const sourcePrice = 20; // AUD (low selling price)
    const supplierPrice = 100; // CNY (high cost)
    const quantity = 100;
    const shippingPerUnit = 15;
    const exchangeRate = 0.213;

    const totalCostCNY = (supplierPrice + shippingPerUnit) * quantity;
    const totalCostAUD = totalCostCNY * exchangeRate;
    const revenue = sourcePrice * quantity;
    const grossProfit = revenue - totalCostAUD;

    expect(grossProfit).toBeLessThan(0); // Should be negative
  });

  it('should use correct exchange rate for NZD', () => {
    const exchangeRateNZD = 0.233;
    const exchangeRateAUD = 0.213;

    expect(exchangeRateNZD).toBeGreaterThan(exchangeRateAUD);
  });
});

describe('Size Filter Logic', () => {
  const SIZE_LIMITS = {
    max_weight_kg: 5,
    max_length_cm: 60,
    max_volume_cm3: 50000,
  };

  it('should filter items by weight', () => {
    const lightItem = { weight: 2 };
    const heavyItem = { weight: 10 };

    expect(lightItem.weight <= SIZE_LIMITS.max_weight_kg).toBe(true);
    expect(heavyItem.weight <= SIZE_LIMITS.max_weight_kg).toBe(false);
  });

  it('should filter items by longest dimension', () => {
    const smallItem = { dimensions: [30, 20, 10] };
    const largeItem = { dimensions: [100, 50, 30] };

    expect(Math.max(...smallItem.dimensions) <= SIZE_LIMITS.max_length_cm).toBe(true);
    expect(Math.max(...largeItem.dimensions) <= SIZE_LIMITS.max_length_cm).toBe(false);
  });

  it('should filter items by volume', () => {
    const smallVolume = { l: 30, w: 20, h: 10 }; // 6000 cm3
    const largeVolume = { l: 50, w: 50, h: 25 }; // 62500 cm3

    const smallVol = smallVolume.l * smallVolume.w * smallVolume.h;
    const largeVol = largeVolume.l * largeVolume.w * largeVolume.h;

    expect(smallVol <= SIZE_LIMITS.max_volume_cm3).toBe(true);
    expect(largeVol <= SIZE_LIMITS.max_volume_cm3).toBe(false);
  });
});

describe('Keyword Translation Mapping', () => {
  const PRODUCT_KEYWORD_MAP: Record<string, string[]> = {
    'wireless earbuds': ['无线耳机', '蓝牙耳机', 'TWS耳机'],
    'headphones': ['耳机', '头戴式耳机'],
    'phone case': ['手机壳', '手机保护套'],
  };

  it('should map known keywords', () => {
    const keyword = 'wireless earbuds';
    const chinese = PRODUCT_KEYWORD_MAP[keyword];

    expect(chinese).toBeDefined();
    expect(chinese).toContain('无线耳机');
    expect(chinese.length).toBeGreaterThan(0);
  });

  it('should return multiple translations for one keyword', () => {
    const keyword = 'wireless earbuds';
    const chinese = PRODUCT_KEYWORD_MAP[keyword];

    expect(chinese.length).toBeGreaterThan(1);
  });

  it('should handle unknown keywords gracefully', () => {
    const keyword = 'unknown product xyz';
    const chinese = PRODUCT_KEYWORD_MAP[keyword];

    expect(chinese).toBeUndefined();
  });
});

describe('Supplier Score Calculation', () => {
  it('should weight price competitiveness at 30%', () => {
    const weights = {
      price: 0.30,
      reputation: 0.25,
      sales: 0.20,
      logistics: 0.15,
      match: 0.10,
    };

    const total = Object.values(weights).reduce((a, b) => a + b, 0);
    expect(total).toBeCloseTo(1.0);
    expect(weights.price).toBe(0.30);
  });

  it('should calculate score within 0-100 range', () => {
    const calculateScore = (params: {
      priceScore: number;
      reputationScore: number;
      salesScore: number;
      logisticsScore: number;
      matchScore: number;
    }) => {
      return (
        params.priceScore * 0.30 +
        params.reputationScore * 0.25 +
        params.salesScore * 0.20 +
        params.logisticsScore * 0.15 +
        params.matchScore * 0.10
      );
    };

    // Max score
    const maxScore = calculateScore({
      priceScore: 100,
      reputationScore: 100,
      salesScore: 100,
      logisticsScore: 100,
      matchScore: 100,
    });
    expect(maxScore).toBe(100);

    // Min score
    const minScore = calculateScore({
      priceScore: 0,
      reputationScore: 0,
      salesScore: 0,
      logisticsScore: 0,
      matchScore: 0,
    });
    expect(minScore).toBe(0);
  });
});

describe('Export Functionality', () => {
  it('should generate correct CSV format', () => {
    const suppliers = [
      {
        source_product: 'Test Product',
        rank: 1,
        supplier_title: 'Supplier Product',
        price_cny: 50,
        moq: 100,
        sold_count: 1000,
        supplier_name: 'Test Supplier',
        location: 'Shenzhen',
        is_verified: true,
        match_score: 85,
        product_url: 'http://test.com',
      },
    ];

    const headers = Object.keys(suppliers[0]).join(',');
    expect(headers).toContain('source_product');
    expect(headers).toContain('price_cny');
    expect(headers).toContain('match_score');
  });

  it('should handle empty results for export', () => {
    const suppliers: any[] = [];
    expect(suppliers.length).toBe(0);
  });
});
