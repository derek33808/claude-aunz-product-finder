# AUNZ Product Finder - Frontend Design

## Project Overview

Frontend application for the AUNZ Product Finder project, built with modern React stack.

## Tech Stack

- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite 7
- **UI Library**: Ant Design 6 with @ant-design/icons
- **State Management**: Zustand
- **Routing**: React Router DOM 7
- **HTTP Client**: Axios
- **Backend Integration**: Supabase
- **Charts**: ECharts with echarts-for-react
- **Date Handling**: Day.js

## Directory Structure

```
frontend/src/
├── components/        # Reusable UI components
├── pages/            # Page components (routes)
├── services/         # API services and Supabase client
├── stores/           # Zustand state stores
├── hooks/            # Custom React hooks
├── types/            # TypeScript type definitions
└── utils/            # Utility functions
```

## Environment Variables

Required environment variables (see `.env.example`):
- `VITE_SUPABASE_URL` - Supabase project URL
- `VITE_SUPABASE_ANON_KEY` - Supabase anonymous key
- `VITE_API_BASE_URL` - Backend API base URL (default: http://localhost:8000)

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```
