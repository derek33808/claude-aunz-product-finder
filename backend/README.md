# AU/NZ Product Finder - Backend

FastAPI backend for the AU/NZ Product Finder tool.

## Features

- **Product Search**: Multi-platform product search (eBay AU/NZ, TradeMe)
- **Google Trends**: Search trend analysis for AU/NZ markets
- **Report Generation**: Automated product selection reports
- **Supabase Integration**: PostgreSQL database + file storage

## Quick Start

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for TradeMe scraping)
playwright install chromium

# Copy environment file
cp .env.example .env
# Edit .env with your credentials

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Products
- `GET /api/products/search` - Search products
- `GET /api/products/{id}` - Get product details
- `POST /api/products/fetch` - Fetch from external platform
- `GET /api/products/{id}/price-history` - Get price history

### Trends
- `GET /api/trends/interest` - Get Google Trends interest
- `GET /api/trends/related-queries` - Get related queries
- `GET /api/trends/compare` - Compare keywords
- `GET /api/trends/regional` - Get regional interest

### Reports
- `POST /api/reports/generate` - Generate new report
- `GET /api/reports/{id}` - Get report
- `GET /api/reports/{id}/status` - Get generation status
- `GET /api/reports` - List all reports
- `GET /api/reports/{id}/download` - Download report file
- `POST /api/reports/{id}/share` - Create share link

## Environment Variables

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

EBAY_APP_ID=your-ebay-app-id
EBAY_CERT_ID=your-ebay-cert-id
EBAY_DEV_ID=your-ebay-dev-id

HOST=0.0.0.0
PORT=8000
DEBUG=true
```

## Project Structure

```
backend/
├── app/
│   ├── main.py           # FastAPI app
│   ├── config.py         # Settings
│   ├── database.py       # Supabase client
│   ├── api/
│   │   └── routes/
│   │       ├── products.py
│   │       ├── reports.py
│   │       └── trends.py
│   ├── services/
│   │   ├── ebay_service.py
│   │   ├── google_trends_service.py
│   │   ├── trademe_scraper.py
│   │   └── report_generator.py
│   └── models/
│       └── schemas.py
├── requirements.txt
└── .env.example
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
