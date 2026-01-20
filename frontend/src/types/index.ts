// Product types
export interface Product {
  id: string;
  platform: 'amazon_au' | 'ebay_au' | 'ebay_nz' | 'trademe';
  platform_id: string;
  title: string;
  category?: string;
  price?: number;
  currency: string;
  rating?: number;
  review_count: number;
  seller_count: number;
  bsr_rank?: number;
  image_url?: string;
  product_url?: string;
  created_at: string;
  updated_at: string;
}

export interface PriceHistory {
  id: string;
  product_id: string;
  price: number;
  recorded_at: string;
}

// Google Trends types
export interface TrendData {
  keyword: string;
  region: string;
  data: Array<{
    date: string;
    [keyword: string]: string | number;
  }>;
}

export interface RelatedQueries {
  keyword: string;
  region: string;
  top: Array<{ query: string; value: number }>;
  rising: Array<{ query: string; value: string }>;
}

// Report types
export type ReportType = 'quick' | 'full' | 'comparison' | 'monitor';
export type ReportStatus = 'pending' | 'generating' | 'completed' | 'failed';
export type TargetType = 'product' | 'keyword' | 'category';

export interface ReportCreate {
  title?: string;
  report_type: ReportType;
  target_type: TargetType;
  target_value: string;
  options?: {
    include_competitors?: boolean;
    forecast_days?: number;
    export_formats?: string[];
  };
}

export interface ReportProgress {
  id: string;
  status: ReportStatus;
  progress: number;
  current_step?: string;
}

export interface Report {
  id: string;
  title: string;
  report_type: ReportType;
  status: ReportStatus;
  progress: number;
  target_type: TargetType;
  target_value: string;
  
  // Analysis sections
  summary?: ReportSummary;
  market_analysis?: MarketAnalysis;
  competition?: CompetitionAnalysis;
  google_trends?: Record<string, unknown>;
  profit_estimate?: ProfitEstimate;
  risk_assessment?: Record<string, unknown>;
  recommendation?: Record<string, unknown>;
  
  overall_score?: number;
  pdf_path?: string;
  excel_path?: string;
  share_token?: string;
  share_expires_at?: string;
  
  created_at: string;
  updated_at: string;
}

export interface ReportSummary {
  conclusion: string;
  recommendation: 'recommended' | 'wait' | 'not_recommended';
  key_points: string[];
  generated_at: string;
}

export interface MarketAnalysis {
  product_count: number;
  platforms: string[];
  price_range: {
    min: number;
    max: number;
    avg: number;
  };
  sample_products: Product[];
}

export interface CompetitionAnalysis {
  level: 'low' | 'medium' | 'high' | 'unknown';
  seller_count: number;
  avg_reviews: number;
  top_products: Product[];
  analysis: string;
}

export interface ProfitEstimate {
  suggested_price: {
    min: number;
    max: number;
    optimal: number;
  };
  estimated_cost: number;
  gross_margin: number;
  estimated_profit_per_unit: number;
  note: string;
}

// Search params
export interface ProductSearchParams {
  keyword?: string;
  platform?: string;
  category?: string;
  min_price?: number;
  max_price?: number;
  min_rating?: number;
  sort_by?: 'relevance' | 'price_asc' | 'price_desc' | 'rating' | 'reviews';
  page?: number;
  page_size?: number;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
