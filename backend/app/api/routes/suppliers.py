"""1688 Supplier API routes."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app.models.schemas import (
    Supplier1688Response,
    Supplier1688Detail,
    SupplierMatchRequest,
    SupplierMatchResult,
    ProfitEstimateRequest,
    ProfitEstimateResponse,
)
from app.services.alibaba1688_service import (
    Alibaba1688Scraper,
    match_suppliers_for_products,
    extract_keywords,
    translate_to_chinese,
    calculate_profit_estimate,
    EXCHANGE_RATES,
)

router = APIRouter()


@router.post("/match", response_model=List[SupplierMatchResult])
async def match_suppliers(
    request: SupplierMatchRequest,
    db=Depends(get_db),
):
    """
    Match 1688 suppliers for selected AU/NZ products.

    Takes a list of product IDs and returns matched suppliers for each product.

    - **product_ids**: List of product UUIDs to match
    - **max_price**: Maximum price in CNY (default: 500)
    - **limit**: Number of suppliers per product (default: 10, max: 20)
    - **include_large**: Include large items (default: false)
    """
    # Fetch products from database
    products = []
    for product_id in request.product_ids:
        result = db.table("products").select("*").eq("id", product_id).execute()
        if result.data:
            products.append(result.data[0])

    if not products:
        raise HTTPException(status_code=404, detail="No products found")

    # Match suppliers
    results = await match_suppliers_for_products(
        products=products,
        max_price=request.max_price,
        limit_per_product=request.limit,
        include_large=request.include_large,
    )

    return results


@router.get("/search", response_model=List[Supplier1688Response])
async def search_1688_suppliers(
    keyword: str = Query(..., min_length=1, description="Chinese keyword to search"),
    max_price: float = Query(500, le=1000, description="Max price in CNY"),
    limit: int = Query(20, ge=1, le=50, description="Number of results"),
    source_price: float = Query(0, description="Source product price for scoring"),
    source_currency: str = Query("AUD", regex="^(AUD|NZD)$"),
    use_cache: bool = Query(True, description="Use cached data from database"),
    db=Depends(get_db),
):
    """
    Search 1688 suppliers by keyword.

    优先从数据库缓存查询，如果没有缓存数据则尝试实时爬取。
    建议使用本地爬虫脚本 (tools/scrape_1688.py) 预先填充缓存数据。

    - **keyword**: Chinese search keyword (e.g., "无线耳机")
    - **max_price**: Maximum price in CNY
    - **limit**: Number of results to return
    - **source_price**: Original product price for profit calculation
    - **source_currency**: AUD or NZD
    - **use_cache**: Whether to use cached database data (default: true)
    """
    # 首先尝试从数据库缓存查询
    if use_cache:
        try:
            query = db.table("suppliers_1688").select("*")

            # 关键词匹配（精确匹配或模糊匹配）
            query = query.or_(
                f"search_keyword.eq.{keyword},title.ilike.%{keyword}%"
            )

            # 价格过滤
            if max_price > 0:
                query = query.lte("price", max_price)

            # 排序和限制
            query = query.order("sold_count", desc=True).limit(limit)

            result = query.execute()

            if result.data:
                print(f"[1688] Found {len(result.data)} cached suppliers for '{keyword}'")
                suppliers = []
                for s in result.data:
                    # Extract offer_id from product_url
                    product_url = s.get("product_url", "")
                    offer_id = ""
                    if product_url:
                        import re
                        match = re.search(r"/offer/(\d+)", product_url)
                        if match:
                            offer_id = match.group(1)

                    suppliers.append(Supplier1688Response(
                        offer_id=offer_id or str(s.get("id", "")),
                        title=s["title"],
                        price=float(s["price"]),
                        moq=s.get("moq", 1),
                        sold_count=s.get("sold_count", 0),
                        image_url=s.get("image_url"),
                        product_url=product_url,
                        supplier_name=s.get("supplier_name") or "Unknown",
                        location=s.get("location"),
                        is_small_medium=s.get("is_small_medium", True),
                        id=offer_id or str(s.get("id", "")),
                    ))
                return suppliers
        except Exception as e:
            print(f"[1688] Cache query error: {e}")
            # 继续尝试实时爬取

    # 如果缓存没有数据，尝试实时爬取（可能被验证码拦截）
    print(f"[1688] No cache found, attempting live scrape for '{keyword}'")
    scraper = Alibaba1688Scraper()

    try:
        suppliers = await scraper.search_suppliers(
            keyword=keyword,
            max_price=max_price,
            limit=limit,
            source_price=source_price,
            source_currency=source_currency,
        )

        if not suppliers:
            # 返回提示信息
            print(f"[1688] No suppliers found. Run: python tools/scrape_1688.py \"{keyword}\"")

        return [
            Supplier1688Response(
                **s.model_dump(),
                id=s.offer_id,
            )
            for s in suppliers
        ]
    finally:
        await scraper.close()


@router.get("/translate")
async def translate_keywords(
    title: str = Query(..., description="Product title in English"),
):
    """
    Extract and translate keywords from product title.

    Useful for debugging the keyword extraction and translation process.

    - **title**: Product title in English
    """
    keywords = extract_keywords(title)
    chinese_keywords = translate_to_chinese(keywords)

    return {
        "original_title": title,
        "extracted_keywords": keywords,
        "chinese_keywords": chinese_keywords,
    }


@router.get("/cache-stats")
async def get_cache_stats(db=Depends(get_db)):
    """
    获取 1688 供应商缓存统计信息。

    返回缓存的关键词列表、总数量和最后更新时间。
    """
    try:
        # 获取总数
        count_result = db.table("suppliers_1688").select("id", count="exact").execute()
        total_count = count_result.count if hasattr(count_result, 'count') else len(count_result.data)

        # 获取关键词统计
        keywords_result = db.table("suppliers_1688").select("search_keyword").execute()
        keyword_counts = {}
        for row in keywords_result.data:
            kw = row.get("search_keyword", "unknown")
            keyword_counts[kw] = keyword_counts.get(kw, 0) + 1

        # 获取最后更新时间
        latest_result = db.table("suppliers_1688").select("scraped_at").order("scraped_at", desc=True).limit(1).execute()
        last_updated = latest_result.data[0]["scraped_at"] if latest_result.data else None

        return {
            "total_cached": total_count,
            "keywords": keyword_counts,
            "last_updated": last_updated,
            "note": "使用 tools/scrape_1688.py 脚本更新缓存数据",
        }
    except Exception as e:
        return {
            "total_cached": 0,
            "keywords": {},
            "last_updated": None,
            "error": str(e),
            "note": "请先运行数据库迁移: supabase/migrations/002_suppliers_1688.sql",
        }


@router.get("/exchange-rates")
async def get_exchange_rates():
    """
    Get current exchange rates used for calculations.

    Returns exchange rates between AUD, NZD, and CNY.
    """
    return {
        "rates": EXCHANGE_RATES,
        "note": "Exchange rates are approximate and may not reflect real-time market rates",
        "updated": "2026-02-02",
    }


@router.get("/details/{offer_id}", response_model=Supplier1688Detail)
async def get_supplier_details(
    offer_id: str,
):
    """
    Get detailed information for a 1688 product.

    - **offer_id**: 1688 product/offer ID
    """
    scraper = Alibaba1688Scraper()

    try:
        details = await scraper.get_product_details(offer_id)

        if not details:
            raise HTTPException(status_code=404, detail="Supplier product not found")

        return Supplier1688Detail(
            offer_id=details.get("offer_id", offer_id),
            title=details.get("title", ""),
            price=0,  # Would need to parse from details
            product_url=details.get("url", ""),
            supplier_name="",
            moq=details.get("moq", 1),
            specifications=details.get("specifications", {}),
            images=details.get("images", []),
            weight=details.get("weight"),
            dimensions=details.get("dimensions"),
        )
    finally:
        await scraper.close()


@router.post("/profit-estimate", response_model=ProfitEstimateResponse)
async def estimate_profit(
    request: ProfitEstimateRequest,
    db=Depends(get_db),
):
    """
    Calculate profit estimation for a product-supplier combination.

    - **source_product_id**: UUID of the AU/NZ product
    - **supplier_offer_id**: 1688 offer ID
    - **quantity**: Purchase quantity (default: 100)
    - **shipping_method**: standard/express
    """
    # Get source product
    result = db.table("products").select("*").eq("id", request.source_product_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Source product not found")

    product = result.data[0]

    # Get supplier details (from cache or fresh scrape)
    # For MVP, we'll use the offer_id to get basic info
    scraper = Alibaba1688Scraper()

    try:
        # Try to get supplier details
        details = await scraper.get_product_details(request.supplier_offer_id)

        if not details:
            # Use a default supplier price if we can't fetch
            supplier_price = 50  # Default fallback
        else:
            # Extract price from details (would need parsing)
            supplier_price = 50  # Placeholder

        # Calculate shipping cost based on method
        shipping_per_unit = 15 if request.shipping_method == "standard" else 25

        # Calculate profit
        estimate = calculate_profit_estimate(
            source_price=float(product.get("price", 0)),
            source_currency=product.get("currency", "AUD"),
            supplier_price=supplier_price,
            quantity=request.quantity,
            shipping_per_unit=shipping_per_unit,
        )

        return ProfitEstimateResponse(**estimate)

    finally:
        await scraper.close()


@router.post("/batch-match")
async def batch_match_suppliers(
    product_ids: List[str],
    max_price: float = Query(500, le=1000),
    limit: int = Query(10, ge=1, le=20),
    db=Depends(get_db),
):
    """
    Batch match suppliers for multiple products.

    This is an optimized endpoint for matching many products at once.

    - **product_ids**: List of product IDs
    - **max_price**: Max price in CNY
    - **limit**: Suppliers per product
    """
    # Validate product IDs
    if len(product_ids) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 products allowed per batch request"
        )

    # Fetch products
    products = []
    for product_id in product_ids:
        result = db.table("products").select("*").eq("id", product_id).execute()
        if result.data:
            products.append(result.data[0])

    if not products:
        return []

    # Match suppliers
    results = await match_suppliers_for_products(
        products=products,
        max_price=max_price,
        limit_per_product=limit,
        include_large=False,
    )

    return results
