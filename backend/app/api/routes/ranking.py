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
