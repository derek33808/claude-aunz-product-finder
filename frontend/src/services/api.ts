import axios from 'axios';
import type {
  Product,
  Report,
  ReportCreate,
  ReportProgress,
  ProductSearchParams,
  TrendData,
  RelatedQueries,
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

export default api;
