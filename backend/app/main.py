"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes import products, reports, trends, suppliers, ranking

# Create FastAPI app
app = FastAPI(
    title="AU/NZ Product Finder API",
    description="API for finding trending products in Australia and New Zealand markets",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(trends.router, prefix="/api/trends", tags=["Trends"])
app.include_router(suppliers.router, prefix="/api/suppliers", tags=["Suppliers"])
app.include_router(ranking.router, prefix="/api", tags=["Ranking"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AU/NZ Product Finder API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
