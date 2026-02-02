/**
 * Tests for the main App component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from '../App'

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'app.title': 'AU/NZ Finder',
        'app.subtitle': 'Product Research Tool',
        'nav.dashboard': 'Dashboard',
        'nav.products': 'Products',
        'nav.trends': 'Trends',
        'nav.reports': 'Reports',
        'header.dashboard': 'Dashboard',
      }
      return translations[key] || key
    },
    i18n: {
      language: 'en',
      changeLanguage: vi.fn(),
    },
  }),
  I18nextProvider: ({ children }: { children: React.ReactNode }) => children,
  initReactI18next: {
    type: '3rdParty',
    init: vi.fn(),
  },
}))

// Mock antd components that might cause issues
vi.mock('antd', async () => {
  const actual = await vi.importActual('antd')
  return {
    ...actual,
    ConfigProvider: ({ children }: { children: React.ReactNode }) => children,
  }
})

describe('App Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the app title', () => {
    render(<App />)

    expect(screen.getByText('AU/NZ Finder')).toBeInTheDocument()
  })

  it('renders navigation menu items', () => {
    render(<App />)

    // Use getAllByText since Dashboard appears in both nav and header
    expect(screen.getAllByText('Dashboard').length).toBeGreaterThan(0)
    expect(screen.getByText('Products')).toBeInTheDocument()
    expect(screen.getByText('Trends')).toBeInTheDocument()
    expect(screen.getByText('Reports')).toBeInTheDocument()
  })

  it('renders language switcher button', () => {
    render(<App />)

    // Language button should be present
    const langButton = screen.getByRole('button', { name: /en/i })
    expect(langButton).toBeInTheDocument()
  })

  it('renders the app subtitle', () => {
    render(<App />)

    expect(screen.getByText('Product Research Tool')).toBeInTheDocument()
  })
})

describe('App Navigation', () => {
  it('shows Dashboard as default route', () => {
    render(<App />)

    // Dashboard should appear (nav and header)
    const dashboardElements = screen.getAllByText('Dashboard')
    expect(dashboardElements.length).toBeGreaterThan(0)
  })
})
