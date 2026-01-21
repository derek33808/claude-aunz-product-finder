/**
 * Tests for the Dashboard page component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Dashboard from '../../pages/Dashboard'

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'dashboard.title': 'Data Overview',
        'dashboard.findHotProducts': 'Find Hot Products',
        'dashboard.finding': 'Finding...',
        'dashboard.refresh': 'Refresh',
        'dashboard.totalProducts': 'Total Products',
        'dashboard.reportsGenerated': 'Reports Generated',
        'dashboard.platforms': 'Platforms',
        'dashboard.trending': 'Trending',
        'dashboard.active': 'Active',
        'dashboard.topHotProducts': 'Top Hot Products',
        'dashboard.googleTrends': 'Google Trends',
        'dashboard.sample': 'Sample',
        'dashboard.noTrendData': 'No trend data available',
        'dashboard.recentReports': 'Recent Reports',
        'dashboard.viewAll': 'View All',
        'dashboard.noReports': 'No reports yet',
        'dashboard.recentProducts': 'Recent Products',
        'dashboard.hotScore': 'Hot Score',
        'products.product': 'Product',
        'products.platform': 'Platform',
        'products.price': 'Price',
        'products.rating': 'Rating',
        'reports.title': 'Title',
        'reports.status': 'Status',
        'reports.score': 'Score',
      }
      return translations[key] || key
    },
    i18n: {
      language: 'en',
      changeLanguage: vi.fn(),
    },
  }),
}))

// Mock the API services
vi.mock('../../services/api', () => ({
  productsApi: {
    search: vi.fn().mockResolvedValue([
      {
        id: '1',
        title: 'Test Product 1',
        platform: 'ebay_au',
        price: 99.99,
        currency: 'AUD',
        rating: 4.5,
      },
      {
        id: '2',
        title: 'Test Product 2',
        platform: 'ebay_nz',
        price: 149.99,
        currency: 'NZD',
        rating: 4.0,
      },
    ]),
    getHotProducts: vi.fn().mockResolvedValue([
      {
        id: '1',
        title: 'Hot Product 1',
        platform: 'ebay_au',
        price: 59.99,
        currency: 'AUD',
        rating: 4.8,
        hot_score: 85.5,
      },
    ]),
  },
  reportsApi: {
    list: vi.fn().mockResolvedValue([]),
  },
  trendsApi: {
    getInterest: vi.fn().mockResolvedValue({
      keywords: ['wireless earbuds'],
      data: [
        { date: '2026-01-01', 'wireless earbuds': 75 },
        { date: '2026-01-08', 'wireless earbuds': 82 },
      ],
    }),
  },
}))

// Mock echarts
vi.mock('echarts-for-react', () => ({
  default: () => <div data-testid="echarts-mock">ECharts Mock</div>,
}))

const renderWithRouter = (component: React.ReactNode) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('Dashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders dashboard title', async () => {
    renderWithRouter(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('Data Overview')).toBeInTheDocument()
    })
  })

  it('renders statistic cards', async () => {
    renderWithRouter(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('Total Products')).toBeInTheDocument()
      expect(screen.getByText('Reports Generated')).toBeInTheDocument()
      expect(screen.getByText('Platforms')).toBeInTheDocument()
      expect(screen.getByText('Trending')).toBeInTheDocument()
    })
  })

  it('renders Find Hot Products button', async () => {
    renderWithRouter(<Dashboard />)

    await waitFor(() => {
      const hotButton = screen.getByRole('button', { name: /find hot products/i })
      expect(hotButton).toBeInTheDocument()
    })
  })

  it('renders Refresh button', async () => {
    renderWithRouter(<Dashboard />)

    await waitFor(() => {
      const refreshButton = screen.getByRole('button', { name: /refresh/i })
      expect(refreshButton).toBeInTheDocument()
    })
  })

  it('renders Recent Products section', async () => {
    renderWithRouter(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('Recent Products')).toBeInTheDocument()
    })
  })

  it('renders Google Trends section', async () => {
    renderWithRouter(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('Google Trends')).toBeInTheDocument()
    })
  })

  it('renders Recent Reports section', async () => {
    renderWithRouter(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('Recent Reports')).toBeInTheDocument()
    })
  })
})

describe('Dashboard Interactions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls getHotProducts when Find Hot Products button is clicked', async () => {
    const { productsApi } = await import('../../services/api')
    renderWithRouter(<Dashboard />)

    await waitFor(() => {
      const hotButton = screen.getByRole('button', { name: /find hot products/i })
      fireEvent.click(hotButton)
    })

    await waitFor(() => {
      expect(productsApi.getHotProducts).toHaveBeenCalledWith(10)
    })
  })
})
