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


# ============ 1688 Supplier Schemas ============

class Supplier1688Base(BaseModel):
    """Base 1688 supplier schema."""
    offer_id: str = Field(..., description="1688 product offer ID")
    title: str
    price: float = Field(..., description="Price in CNY")
    price_range: Optional[str] = Field(None, description="Price range (e.g., '9.9-15.8')")
    moq: int = Field(1, description="Minimum Order Quantity")
    sold_count: int = Field(0, description="Total sold count")
    image_url: Optional[str] = None
    product_url: str

    # Supplier info
    supplier_name: str
    supplier_url: Optional[str] = None
    supplier_years: Optional[int] = Field(None, description="Years in business")
    supplier_rating: Optional[float] = Field(None, description="Supplier rating (0-5)")
    is_verified: bool = Field(False, description="Is verified supplier (诚信通)")

    # Logistics info
    location: Optional[str] = Field(None, description="Shipping location")
    shipping_estimate: Optional[str] = None

    # Product attributes
    weight: Optional[float] = Field(None, description="Weight in kg")
    dimensions: Optional[str] = Field(None, description="Dimensions (e.g., '15x10x5cm')")
    is_small_medium: bool = Field(True, description="Is small/medium sized item")


class Supplier1688Response(Supplier1688Base):
    """1688 supplier response schema."""
    id: Optional[str] = None
    match_score: Optional[float] = Field(None, description="Matching score (0-100)")
    profit_margin: Optional[float] = Field(None, description="Estimated profit margin")
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Supplier1688Detail(Supplier1688Base):
    """Detailed 1688 supplier information."""
    description: Optional[str] = None
    specifications: Optional[dict] = Field(default_factory=dict)
    price_tiers: Optional[List[dict]] = Field(default_factory=list)
    images: Optional[List[str]] = Field(default_factory=list)
    shipping_methods: Optional[List[dict]] = Field(default_factory=list)


class SupplierMatchRequest(BaseModel):
    """Request for matching suppliers."""
    product_ids: List[str] = Field(..., description="List of AU/NZ product IDs to match")
    max_price: float = Field(500, le=1000, description="Max price in CNY")
    limit: int = Field(10, ge=1, le=20, description="Number of suppliers per product")
    include_large: bool = Field(False, description="Include large items")


class SupplierMatchResult(BaseModel):
    """Result of supplier matching for a single product."""
    source_product_id: str
    source_product_title: str
    search_keywords: List[str]
    matched_suppliers: List[Supplier1688Response]
    match_count: int


class ProfitEstimateRequest(BaseModel):
    """Request for profit estimation."""
    source_product_id: str
    supplier_offer_id: str
    quantity: int = Field(100, ge=1, description="Purchase quantity")
    shipping_method: str = Field("standard", description="Shipping method")


class ProfitEstimateResponse(BaseModel):
    """Profit estimation response."""
    source_price: float
    source_currency: str
    supplier_price_cny: float
    purchase_cost_cny: float
    shipping_cost_cny: float
    total_cost_cny: float
    total_cost_target_currency: float
    exchange_rate: float
    gross_profit: float
    profit_margin: float
    roi: float
    break_even_quantity: int
    notes: List[str] = Field(default_factory=list)
