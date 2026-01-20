"""Product API routes."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app.models.schemas import (
    ProductResponse,
    ProductSearchParams,
    ProductCreate,
)
from app.services.ebay_service import EbayService

router = APIRouter()


@router.get("/search", response_model=List[ProductResponse])
async def search_products(
    keyword: Optional[str] = Query(None, min_length=1),
    platform: Optional[str] = Query(None, regex="^(amazon_au|ebay_au|ebay_nz|trademe)$"),
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    sort_by: str = Query("relevance", regex="^(relevance|price_asc|price_desc|rating|reviews)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    """
    Search products across platforms.

    - **keyword**: Search keyword (optional, if not provided returns all products)
    - **platform**: Filter by platform (optional)
    - **category**: Filter by category (optional)
    - **min_price/max_price**: Price range filter
    - **min_rating**: Minimum rating filter
    - **sort_by**: Sort order
    """
    # Build query
    query = db.table("products").select("*")

    if platform:
        query = query.eq("platform", platform)
    if category:
        query = query.ilike("category", f"%{category}%")
    if min_price:
        query = query.gte("price", min_price)
    if max_price:
        query = query.lte("price", max_price)
    if min_rating:
        query = query.gte("rating", min_rating)

    # Text search on title (only if keyword provided)
    if keyword:
        query = query.ilike("title", f"%{keyword}%")
    
    # Sorting
    if sort_by == "price_asc":
        query = query.order("price", desc=False)
    elif sort_by == "price_desc":
        query = query.order("price", desc=True)
    elif sort_by == "rating":
        query = query.order("rating", desc=True)
    elif sort_by == "reviews":
        query = query.order("review_count", desc=True)
    else:
        query = query.order("created_at", desc=True)
    
    # Pagination
    offset = (page - 1) * page_size
    query = query.range(offset, offset + page_size - 1)
    
    result = query.execute()
    return result.data


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db=Depends(get_db),
):
    """Get product by ID."""
    result = db.table("products").select("*").eq("id", str(product_id)).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return result.data[0]


@router.post("/fetch")
async def fetch_products_from_platform(
    keyword: str = Query(..., min_length=1),
    platform: str = Query(..., regex="^(ebay_au|ebay_nz)$"),
    limit: int = Query(50, ge=1, le=100),
    db=Depends(get_db),
):
    """
    Fetch products from external platform and save to database.
    Currently supports: eBay AU, eBay NZ
    """
    if platform in ["ebay_au", "ebay_nz"]:
        service = EbayService()
        region = "AU" if platform == "ebay_au" else "NZ"
        products = await service.search_products(keyword, region=region, limit=limit)
        
        # Save to database
        saved_count = 0
        for product in products:
            product["platform"] = platform
            try:
                db.table("products").upsert(
                    product,
                    on_conflict="platform,platform_id"
                ).execute()
                saved_count += 1
            except Exception as e:
                print(f"Error saving product: {e}")
        
        return {
            "message": f"Fetched and saved {saved_count} products",
            "platform": platform,
            "keyword": keyword,
        }
    
    raise HTTPException(status_code=400, detail=f"Platform {platform} not supported yet")


@router.get("/{product_id}/price-history")
async def get_price_history(
    product_id: UUID,
    days: int = Query(30, ge=1, le=365),
    db=Depends(get_db),
):
    """Get price history for a product."""
    result = db.table("price_history")\
        .select("*")\
        .eq("product_id", str(product_id))\
        .order("recorded_at", desc=True)\
        .limit(days)\
        .execute()
    
    return result.data
