import { create } from 'zustand';
import type { Product, Report, ReportProgress } from '../types';

interface AppState {
  // Products
  products: Product[];
  selectedProduct: Product | null;
  isLoadingProducts: boolean;
  
  // Reports
  reports: Report[];
  currentReport: Report | null;
  reportProgress: ReportProgress | null;
  isGeneratingReport: boolean;
  
  // UI State
  searchKeyword: string;
  selectedPlatform: string | null;
  
  // Actions
  setProducts: (products: Product[]) => void;
  setSelectedProduct: (product: Product | null) => void;
  setIsLoadingProducts: (loading: boolean) => void;
  
  setReports: (reports: Report[]) => void;
  setCurrentReport: (report: Report | null) => void;
  setReportProgress: (progress: ReportProgress | null) => void;
  setIsGeneratingReport: (generating: boolean) => void;
  
  setSearchKeyword: (keyword: string) => void;
  setSelectedPlatform: (platform: string | null) => void;
  
  reset: () => void;
}

const initialState = {
  products: [],
  selectedProduct: null,
  isLoadingProducts: false,
  reports: [],
  currentReport: null,
  reportProgress: null,
  isGeneratingReport: false,
  searchKeyword: '',
  selectedPlatform: null,
};

export const useAppStore = create<AppState>((set) => ({
  ...initialState,
  
  // Products actions
  setProducts: (products) => set({ products }),
  setSelectedProduct: (product) => set({ selectedProduct: product }),
  setIsLoadingProducts: (loading) => set({ isLoadingProducts: loading }),
  
  // Reports actions
  setReports: (reports) => set({ reports }),
  setCurrentReport: (report) => set({ currentReport: report }),
  setReportProgress: (progress) => set({ reportProgress: progress }),
  setIsGeneratingReport: (generating) => set({ isGeneratingReport: generating }),
  
  // UI actions
  setSearchKeyword: (keyword) => set({ searchKeyword: keyword }),
  setSelectedPlatform: (platform) => set({ selectedPlatform: platform }),
  
  reset: () => set(initialState),
}));
