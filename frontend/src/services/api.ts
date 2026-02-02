import axios from 'axios';
import type {
  Product,
  Report,
  ReportCreate,
  ReportProgress,
  ProductSearchParams,
  TrendData,
  RelatedQueries,
  Supplier1688,
  Supplier1688Detail,
  SupplierMatchRequest,
  SupplierMatchResult,
  ProfitEstimate1688,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Products API
export const productsApi = {
  search: async (params: ProductSearchParams): Promise<Product[]> => {
    const response = await api.get('/api/products/search', { params });
    return response.data;
  },

  getById: async (id: string): Promise<Product> => {
    const response = await api.get(`/api/products/${id}`);
    return response.data;
  },

  fetchFromPlatform: async (keyword: string, platform: string, limit = 50) => {
    const response = await api.post('/api/products/fetch', null, {
      params: { keyword, platform, limit },
    });
    return response.data;
  },

  getPriceHistory: async (productId: string, days = 30) => {
    const response = await api.get(`/api/products/${productId}/price-history`, {
      params: { days },
    });
    return response.data;
  },

  getHotProducts: async (limit = 10): Promise<(Product & { hot_score: number })[]> => {
    const response = await api.get('/api/products/hot', { params: { limit } });
    return response.data;
  },
};

// Trends API
export const trendsApi = {
  getInterest: async (keywords: string, region = 'AU', timeframe = 'today 12-m'): Promise<TrendData> => {
    const response = await api.get('/api/trends/interest', {
      params: { keywords, region, timeframe },
    });
    return response.data;
  },

  getRelatedQueries: async (keyword: string, region = 'AU'): Promise<RelatedQueries> => {
    const response = await api.get('/api/trends/related-queries', {
      params: { keyword, region },
    });
    return response.data;
  },

  compare: async (keywords: string, region = 'AU') => {
    const response = await api.get('/api/trends/compare', {
      params: { keywords, region },
    });
    return response.data;
  },

  getRegional: async (keyword: string) => {
    const response = await api.get('/api/trends/regional', {
      params: { keyword },
    });
    return response.data;
  },

  getSuggestions: async (keyword: string) => {
    const response = await api.get('/api/trends/suggestions', {
      params: { keyword },
    });
    return response.data;
  },
};

// Reports API
export const reportsApi = {
  generate: async (data: ReportCreate): Promise<ReportProgress> => {
    const response = await api.post('/api/reports/generate', data);
    return response.data;
  },

  getById: async (id: string): Promise<Report> => {
    const response = await api.get(`/api/reports/${id}`);
    return response.data;
  },

  getStatus: async (id: string): Promise<ReportProgress> => {
    const response = await api.get(`/api/reports/${id}/status`);
    return response.data;
  },

  list: async (params?: { report_type?: string; status?: string; page?: number; page_size?: number }): Promise<Report[]> => {
    const response = await api.get('/api/reports/', { params });
    return response.data;
  },

  download: async (id: string, format: 'pdf' | 'excel' = 'pdf') => {
    const response = await api.get(`/api/reports/${id}/download`, {
      params: { format },
    });
    return response.data;
  },

  createShareLink: async (id: string, expiresInDays = 7, password?: string) => {
    const response = await api.post(`/api/reports/${id}/share`, {
      expires_in_days: expiresInDays,
      password,
    });
    return response.data;
  },

  getShared: async (shareToken: string, password?: string): Promise<Report> => {
    const response = await api.get(`/api/reports/shared/${shareToken}`, {
      params: { password },
    });
    return response.data;
  },

  delete: async (id: string) => {
    const response = await api.delete(`/api/reports/${id}`);
    return response.data;
  },
};

// Suppliers API (1688)
export const suppliersApi = {
  match: async (request: SupplierMatchRequest): Promise<SupplierMatchResult[]> => {
    const response = await api.post('/api/suppliers/match', request);
    return response.data;
  },

  search: async (
    keyword: string,
    maxPrice = 500,
    limit = 20,
    sourcePrice = 0,
    sourceCurrency = 'AUD'
  ): Promise<Supplier1688[]> => {
    const response = await api.get('/api/suppliers/search', {
      params: {
        keyword,
        max_price: maxPrice,
        limit,
        source_price: sourcePrice,
        source_currency: sourceCurrency,
      },
    });
    return response.data;
  },

  getDetails: async (offerId: string): Promise<Supplier1688Detail> => {
    const response = await api.get(`/api/suppliers/${offerId}`);
    return response.data;
  },

  translateKeywords: async (title: string): Promise<{
    original_title: string;
    extracted_keywords: string[];
    chinese_keywords: string[];
  }> => {
    const response = await api.get('/api/suppliers/translate', {
      params: { title },
    });
    return response.data;
  },

  estimateProfit: async (
    sourceProductId: string,
    supplierOfferId: string,
    quantity = 100,
    shippingMethod = 'standard'
  ): Promise<ProfitEstimate1688> => {
    const response = await api.post('/api/suppliers/profit-estimate', {
      source_product_id: sourceProductId,
      supplier_offer_id: supplierOfferId,
      quantity,
      shipping_method: shippingMethod,
    });
    return response.data;
  },

  getExchangeRates: async (): Promise<{
    rates: Record<string, number>;
    note: string;
    updated: string;
  }> => {
    const response = await api.get('/api/suppliers/exchange-rates');
    return response.data;
  },

  batchMatch: async (
    productIds: string[],
    maxPrice = 500,
    limit = 10
  ): Promise<SupplierMatchResult[]> => {
    const response = await api.post('/api/suppliers/batch-match', productIds, {
      params: { max_price: maxPrice, limit },
    });
    return response.data;
  },
};

// Ranking API
export interface RankingResult {
  keyword: string;
  category_zh: string;
  category_en: string;
  total_score: number;
  rank: number;
  scores: {
    demand: number;
    trend: number;
    profit: number;
    competition: number;
  };
  platform_stats: Record<string, { listings: number; price_range?: { min: number; max: number; avg: number } }>;
  supplier_info: {
    cost_price_cny: number;
    product_count: number;
    top_product?: {
      title: string;
      price: number;
      product_url: string;
    };
  };
  profit_analysis: {
    cost_cny: number;
    market_price_local: number;
    profit_margin_percent: number;
  };
}

export interface RankingResponse {
  market: string;
  rankings: RankingResult[];
  generated_at: string;
  elapsed_seconds: number;
  version: string;
  data_sources: Record<string, boolean>;
  api_status: {
    trademe_configured: boolean;
    ebay_configured: boolean;
  };
}

export const rankingApi = {
  calculate: async (market: string = 'NZ'): Promise<RankingResponse> => {
    const response = await api.post(`/api/ranking/calculate?market=${market}`);
    return response.data.data;
  },

  getLatest: async (market: string = 'NZ'): Promise<RankingResponse | null> => {
    const response = await api.get(`/api/ranking/latest?market=${market}`);
    if (response.data.success) {
      return response.data.data;
    }
    return null;
  },

  getCategories: async () => {
    const response = await api.get('/api/ranking/categories');
    return response.data;
  },
};

export default api;
