"""API routes for product ranking calculations."""

from fastapi import APIRouter, Query, BackgroundTasks
from typing import Optional, List
from datetime import datetime

from app.services.ranking_service import RankingService

router = APIRouter(prefix="/ranking", tags=["ranking"])

# Store latest ranking results in memory (for quick access)
_ranking_cache = {
    "NZ": None,
    "AU": None,
}


@router.post("/calculate")
async def calculate_rankings(
    market: str = Query("NZ", pattern="^(NZ|AU)$"),
    categories: Optional[str] = Query(None, description="Comma-separated category keywords"),
):
    """
    Calculate product rankings for specified market.

    This endpoint triggers data collection from all platforms and calculates
    comprehensive rankings based on demand, trends, profit margin, and competition.

    Args:
        market: Target market (NZ or AU)
        categories: Optional comma-separated list of category keywords to analyze

    Returns:
        Complete ranking results with detailed scores
    """
    ranking_service = RankingService()

    try:
        # Parse categories if provided
        cat_list = None
        if categories:
            cat_list = [c.strip() for c in categories.split(",")]

        # Calculate rankings
        results = await ranking_service.calculate_rankings(
            market=market,
            categories=cat_list,
        )

        # Cache results
        _ranking_cache[market] = results

        return {
            "success": True,
            "data": results,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
    finally:
        await ranking_service.close()


@router.get("/latest")
async def get_latest_rankings(
    market: str = Query("NZ", pattern="^(NZ|AU)$"),
):
    """
    Get the latest cached ranking results.

    Returns cached results from the most recent calculation.
    Use POST /calculate to refresh the rankings.
    """
    cached = _ranking_cache.get(market)

    if cached:
        return {
            "success": True,
            "data": cached,
            "is_cached": True,
        }
    else:
        return {
            "success": False,
            "error": f"No cached rankings for {market}. Please call POST /ranking/calculate first.",
            "is_cached": False,
        }


@router.get("/categories")
async def get_available_categories():
    """
    Get list of available product categories for ranking.
    """
    from app.services.ranking_service import RankingService

    return {
        "categories": RankingService.CATEGORIES,
        "weights": RankingService.WEIGHTS,
    }


@router.get("/status")
async def get_ranking_status():
    """
    Get status of ranking data for both markets.
    """
    return {
        "NZ": {
            "has_data": _ranking_cache.get("NZ") is not None,
            "generated_at": _ranking_cache["NZ"]["generated_at"] if _ranking_cache.get("NZ") else None,
        },
        "AU": {
            "has_data": _ranking_cache.get("AU") is not None,
            "generated_at": _ranking_cache["AU"]["generated_at"] if _ranking_cache.get("AU") else None,
        },
    }


@router.get("/debug/suppliers")
async def debug_supplier_query(
    keyword: str = Query("蓝牙耳机", description="Chinese keyword to search"),
):
    """
    Debug endpoint to test 1688 supplier query.
    """
    from app.database import get_db

    db = get_db()
    results = {
        "keyword": keyword,
        "queries": {},
    }

    # Test 1: Simple select all
    try:
        all_result = db.table("suppliers_1688").select("search_keyword").limit(5).execute()
        results["queries"]["select_all"] = {
            "count": len(all_result.data),
            "sample": all_result.data[:3] if all_result.data else [],
        }
    except Exception as e:
        results["queries"]["select_all"] = {"error": str(e)}

    # Test 2: eq query
    try:
        eq_result = db.table("suppliers_1688").select("*").eq("search_keyword", keyword).limit(5).execute()
        results["queries"]["eq_query"] = {
            "count": len(eq_result.data),
            "sample": [{"title": d.get("title", "")[:30], "price": d.get("price")} for d in eq_result.data[:3]] if eq_result.data else [],
        }
    except Exception as e:
        results["queries"]["eq_query"] = {"error": str(e)}

    # Test 3: ilike query
    try:
        like_result = db.table("suppliers_1688").select("*").ilike("title", f"%{keyword[:2]}%").limit(5).execute()
        results["queries"]["ilike_query"] = {
            "count": len(like_result.data),
            "sample": [{"title": d.get("title", "")[:30], "price": d.get("price")} for d in like_result.data[:3]] if like_result.data else [],
        }
    except Exception as e:
        results["queries"]["ilike_query"] = {"error": str(e)}

    return results
