"""Trends API routes - Google Trends integration."""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException

from app.models.schemas import TrendQuery, TrendData
from app.services.google_trends_service import GoogleTrendsService

router = APIRouter()


@router.get("/interest")
async def get_interest_over_time(
    keywords: str = Query(..., description="Comma-separated keywords (max 5)"),
    region: str = Query("AU", regex="^(AU|NZ)$"),
    timeframe: str = Query("today 12-m", description="Timeframe for trends"),
):
    """
    Get Google Trends interest over time for keywords.
    
    - **keywords**: Comma-separated list of keywords (max 5)
    - **region**: AU or NZ
    - **timeframe**: Time range (e.g., 'today 12-m', 'today 3-m', '2024-01-01 2024-12-31')
    """
    keyword_list = [k.strip() for k in keywords.split(",")][:5]
    
    if not keyword_list:
        raise HTTPException(status_code=400, detail="At least one keyword required")
    
    service = GoogleTrendsService()
    try:
        data = await service.get_interest_over_time(
            keywords=keyword_list,
            region=region,
            timeframe=timeframe,
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch trends: {str(e)}")


@router.get("/related-queries")
async def get_related_queries(
    keyword: str = Query(..., min_length=1),
    region: str = Query("AU", regex="^(AU|NZ)$"),
):
    """
    Get related queries for a keyword.
    
    Returns both 'top' and 'rising' related queries.
    """
    service = GoogleTrendsService()
    try:
        data = await service.get_related_queries(keyword=keyword, region=region)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch related queries: {str(e)}")


@router.get("/compare")
async def compare_keywords(
    keywords: str = Query(..., description="Comma-separated keywords to compare (max 5)"),
    region: str = Query("AU", regex="^(AU|NZ)$"),
):
    """
    Compare interest between multiple keywords.
    """
    keyword_list = [k.strip() for k in keywords.split(",")][:5]
    
    if len(keyword_list) < 2:
        raise HTTPException(status_code=400, detail="At least 2 keywords required for comparison")
    
    service = GoogleTrendsService()
    try:
        data = await service.compare_keywords(keywords=keyword_list, region=region)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare keywords: {str(e)}")


@router.get("/regional")
async def get_regional_interest(
    keyword: str = Query(..., min_length=1),
):
    """
    Get interest by region (compare AU vs NZ).
    """
    service = GoogleTrendsService()
    try:
        au_data = await service.get_interest_over_time([keyword], region="AU")
        nz_data = await service.get_interest_over_time([keyword], region="NZ")
        
        return {
            "keyword": keyword,
            "AU": au_data,
            "NZ": nz_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch regional data: {str(e)}")


@router.get("/suggestions")
async def get_keyword_suggestions(
    keyword: str = Query(..., min_length=1),
):
    """
    Get keyword suggestions based on Google Trends.
    """
    service = GoogleTrendsService()
    try:
        suggestions = await service.get_suggestions(keyword)
        return {"keyword": keyword, "suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")
