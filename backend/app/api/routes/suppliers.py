"""1688 Supplier API routes."""

import math
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
    db=Depends(get_db),
):
    """
    Search 1688 suppliers by keyword from cached database.

    - **keyword**: Chinese search keyword (e.g., "无线耳机")
    - **max_price**: Maximum price in CNY
    - **limit**: Number of results to return
    - **source_price**: Original product price for profit calculation
    - **source_currency**: AUD or NZD

    Note: Data comes from periodic scraping, not real-time.
    """
    try:
        # Query from database
        query = db.table("suppliers_1688").select("*")

        # Filter by keyword (exact match or contains)
        query = query.or_(f"search_keyword.eq.{keyword},title.ilike.%{keyword}%")

        # Filter by price
        if max_price > 0:
            query = query.lte("price", max_price)

        # Order by sold_count (popularity) and limit
        query = query.order("sold_count", desc=True).limit(limit)

        result = query.execute()

        suppliers = []
        for row in result.data:
            # Calculate match score if source price provided
            match_score = None
            if source_price > 0:
                match_score = calculate_supplier_score_from_row(
                    row, source_price, source_currency
                )

            suppliers.append(Supplier1688Response(
                id=row.get("offer_id"),
                offer_id=row.get("offer_id"),
                title=row.get("title", ""),
                price=float(row.get("price", 0)),
                price_range=row.get("price_range"),
                moq=row.get("moq", 1),
                sold_count=row.get("sold_count", 0),
                image_url=row.get("image_url"),
                product_url=row.get("product_url", ""),
                supplier_name=row.get("supplier_name", ""),
                supplier_url=row.get("supplier_url"),
                supplier_years=row.get("supplier_years"),
                supplier_rating=row.get("supplier_rating"),
                is_verified=row.get("is_verified", False),
                location=row.get("location"),
                shipping_estimate=row.get("shipping_estimate"),
                weight=row.get("weight"),
                dimensions=row.get("dimensions"),
                is_small_medium=row.get("is_small_medium", True),
                match_score=match_score,
                created_at=row.get("created_at"),
            ))

        return suppliers

    except Exception as e:
        print(f"Database query error: {e}")
        return []


def calculate_supplier_score_from_row(
    row: dict,
    source_price: float,
    source_currency: str = "AUD",
) -> float:
    """Calculate supplier score from database row."""
    exchange_rate = EXCHANGE_RATES.get(f"{source_currency}_CNY", 4.5)
    price = float(row.get("price", 0))

    # Price competitiveness score
    target_cost_cny = source_price * exchange_rate * 0.3
    if price <= target_cost_cny * 0.5:
        price_score = 100
    elif price <= target_cost_cny:
        price_score = 70 + 30 * (1 - price / target_cost_cny)
    elif price <= target_cost_cny * 1.5:
        price_score = 40
    else:
        price_score = 20

    # Sales score
    sold_count = row.get("sold_count", 0)
    if sold_count > 0:
        sales_score = min(math.log10(sold_count + 1) * 25, 100)
    else:
        sales_score = 0

    # Reputation score
    reputation_score = 50  # Base score
    if row.get("is_verified"):
        reputation_score += 25
    if row.get("supplier_rating"):
        reputation_score += float(row.get("supplier_rating", 0)) * 5

    # Weighted score
    final_score = (
        price_score * 0.35 +
        sales_score * 0.30 +
        reputation_score * 0.35
    )

    return round(final_score, 2)


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


@router.get("/stats")
async def get_supplier_stats(db=Depends(get_db)):
    """
    Get statistics about cached 1688 supplier data.

    Returns counts, keywords, and last update time.
    """
    try:
        # Get total count
        count_result = db.table("suppliers_1688").select("id", count="exact").execute()
        total_count = count_result.count if count_result.count else 0

        # Get unique keywords
        keywords_result = db.table("suppliers_1688").select("search_keyword").execute()
        keywords = list(set(row.get("search_keyword") for row in keywords_result.data if row.get("search_keyword")))

        # Get latest scraped_at
        latest_result = db.table("suppliers_1688").select("scraped_at").order("scraped_at", desc=True).limit(1).execute()
        last_scraped = latest_result.data[0].get("scraped_at") if latest_result.data else None

        return {
            "total_suppliers": total_count,
            "unique_keywords": len(keywords),
            "keywords": sorted(keywords),
            "last_scraped_at": last_scraped,
            "data_source": "local_scraper",
            "note": "Run scripts/scrape_1688.py to update data"
        }

    except Exception as e:
        return {
            "total_suppliers": 0,
            "error": str(e),
            "note": "Table may not exist. Run scripts/create_suppliers_table.sql in Supabase first."
        }


@router.get("/debug")
async def debug_1688_scraper(
    keyword: str = Query("手机壳", description="Test keyword"),
):
    """
    Debug endpoint for 1688 scraper.
    Returns detailed information about the scraping process.
    """
    from app.services.alibaba1688_service import PLAYWRIGHT_AVAILABLE
    from app.config import settings
    import json

    debug_info = {
        "playwright_available": PLAYWRIGHT_AVAILABLE,
        "cookies_configured": bool(settings.alibaba_1688_cookies),
        "cookies_count": 0,
        "browser_launched": False,
        "page_loaded": False,
        "page_title": None,
        "page_url": None,
        "html_snippet": None,
        "captcha_detected": False,
        "login_detected": False,
        "selectors_tested": [],
        "items_found": 0,
        "error": None,
    }

    # Check cookies count
    if settings.alibaba_1688_cookies:
        try:
            cookies = json.loads(settings.alibaba_1688_cookies)
            debug_info["cookies_count"] = len(cookies)
        except:
            debug_info["cookies_count"] = -1  # Invalid JSON

    if not PLAYWRIGHT_AVAILABLE:
        debug_info["error"] = "Playwright not available"
        return debug_info

    try:
        from playwright.async_api import async_playwright
        import asyncio

        async def run_debug():
            playwright = await async_playwright().start()
            try:
                browser = await playwright.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox"],
                )
                debug_info["browser_launched"] = True

                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    locale="zh-CN",
                )

                # Add cookies from config if available
                if settings.alibaba_1688_cookies:
                    try:
                        cookies = json.loads(settings.alibaba_1688_cookies)
                        formatted_cookies = []
                        for cookie in cookies:
                            formatted_cookie = {
                                "name": cookie.get("name", ""),
                                "value": cookie.get("value", ""),
                                "domain": cookie.get("domain", ".1688.com"),
                                "path": cookie.get("path", "/"),
                            }
                            if cookie.get("expires"):
                                formatted_cookie["expires"] = cookie["expires"]
                            if cookie.get("httpOnly") is not None:
                                formatted_cookie["httpOnly"] = cookie["httpOnly"]
                            if cookie.get("secure") is not None:
                                formatted_cookie["secure"] = cookie["secure"]
                            if cookie.get("sameSite"):
                                formatted_cookie["sameSite"] = cookie["sameSite"]
                            formatted_cookies.append(formatted_cookie)
                        await context.add_cookies(formatted_cookies)
                    except Exception as e:
                        debug_info["error"] = f"Cookie error: {e}"

                page = await context.new_page()

                # Add stealth script
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    window.chrome = { runtime: {} };
                """)

                url = f"https://s.1688.com/selloffer/offer_search.htm?keywords={keyword}"
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                debug_info["page_loaded"] = True

                await asyncio.sleep(3)

                debug_info["page_title"] = await page.title()
                debug_info["page_url"] = page.url

                # Get HTML snippet
                content = await page.content()
                debug_info["html_snippet"] = content[:2000]

                # Check for captcha/login
                if "验证" in content:
                    debug_info["captcha_detected"] = True
                if "登录" in content or "login" in content.lower():
                    debug_info["login_detected"] = True

                # Test selectors
                selectors = [
                    "div[class*='offer-item']",
                    "div[class*='offeritem']",
                    "div[class*='card-container']",
                    ".J_ShopCard",
                    ".offer-list-row",
                    ".sm-offer-item",
                    "[data-tracklog]",
                    ".space-offer-card-box",
                    "div[class*='product']",
                    "div[class*='item-content']",
                    "a[href*='detail.1688.com']",
                ]

                for selector in selectors:
                    try:
                        items = await page.query_selector_all(selector)
                        count = len(items) if items else 0
                        debug_info["selectors_tested"].append({
                            "selector": selector,
                            "count": count
                        })
                        if count > 0:
                            debug_info["items_found"] = max(debug_info["items_found"], count)
                    except Exception as e:
                        debug_info["selectors_tested"].append({
                            "selector": selector,
                            "error": str(e)
                        })

                await page.close()
                await context.close()
                await browser.close()

            finally:
                await playwright.stop()

        await run_debug()

    except Exception as e:
        debug_info["error"] = str(e)

    return debug_info


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
