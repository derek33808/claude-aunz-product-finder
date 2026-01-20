"""Pydantic models for API request/response schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


# ============ Product Schemas ============

class ProductBase(BaseModel):
    """Base product schema."""
    platform: str = Field(..., description="Platform: amazon_au, ebay_au, ebay_nz, trademe")
    platform_id: str = Field(..., description="Product ID on the platform")
    title: str
    category: Optional[str] = None
    price: Optional[Decimal] = None
    currency: str = "AUD"
    rating: Optional[float] = None
    review_count: int = 0
    seller_count: int = 1
    bsr_rank: Optional[int] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None


class ProductCreate(ProductBase):
    """Schema for creating a product."""
    raw_data: Optional[dict] = None


class ProductResponse(ProductBase):
    """Schema for product response."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductSearchParams(BaseModel):
    """Search parameters for products."""
    keyword: Optional[str] = None
    category: Optional[str] = None
    platform: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    min_rating: Optional[float] = None
    sort_by: str = "relevance"  # relevance, price_asc, price_desc, rating, reviews
    page: int = 1
    page_size: int = 20


# ============ Google Trends Schemas ============

class TrendQuery(BaseModel):
    """Query parameters for Google Trends."""
    keywords: List[str] = Field(..., max_length=5)
    region: str = "AU"  # AU or NZ
    timeframe: str = "today 12-m"


class TrendData(BaseModel):
    """Google Trends data response."""
    keyword: str
    region: str
    interest_over_time: List[dict]
    related_queries: List[dict]
    recorded_at: datetime


# ============ Report Schemas ============

class ReportCreate(BaseModel):
    """Schema for creating a report."""
    title: Optional[str] = None
    report_type: str = "full"  # quick, full, comparison, monitor
    target_type: str  # product, keyword, category
    target_value: str  # product_id, keyword, or category name
    options: Optional[dict] = Field(default_factory=dict)


class ReportProgress(BaseModel):
    """Report generation progress."""
    id: UUID
    status: str
    progress: int
    current_step: Optional[str] = None


class ReportSummary(BaseModel):
    """Report summary section."""
    conclusion: str
    overall_score: float
    recommendation: str  # recommended, wait, not_recommended
    key_points: List[str]


class MarketAnalysis(BaseModel):
    """Market analysis section."""
    market_size: Optional[Decimal] = None
    monthly_sales_estimate: Optional[int] = None
    price_range: dict
    seasonality: Optional[dict] = None


class CompetitionAnalysis(BaseModel):
    """Competition analysis section."""
    competition_level: str  # low, medium, high
    top_sellers: List[dict]
    review_distribution: dict
    new_seller_survival_rate: Optional[float] = None


class ProfitEstimate(BaseModel):
    """Profit estimation section."""
    suggested_price_range: dict
    estimated_cost: Optional[Decimal] = None
    gross_margin: Optional[float] = None
    roi_estimate: Optional[float] = None


class ReportResponse(BaseModel):
    """Full report response."""
    id: UUID
    title: str
    report_type: str
    status: str
    progress: int
    
    # Analysis sections
    summary: Optional[dict] = None
    market_analysis: Optional[dict] = None
    competition: Optional[dict] = None
    google_trends: Optional[dict] = None
    profit_estimate: Optional[dict] = None
    risk_assessment: Optional[dict] = None
    recommendation: Optional[dict] = None
    
    # Score
    overall_score: Optional[float] = None
    
    # Files
    pdf_path: Optional[str] = None
    excel_path: Optional[str] = None
    
    # Share
    share_token: Optional[str] = None
    share_expires_at: Optional[datetime] = None
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ShareLinkCreate(BaseModel):
    """Create share link request."""
    expires_in_days: int = 7
    password: Optional[str] = None


class ShareLinkResponse(BaseModel):
    """Share link response."""
    share_url: str
    expires_at: datetime
    has_password: bool
