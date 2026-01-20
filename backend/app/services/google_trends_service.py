"""Google Trends service for search trend analysis."""

import asyncio
import time
import random
from typing import List, Optional
from datetime import datetime, timedelta
from pytrends.request import TrendReq
import pandas as pd

# Flag to enable mock data when Google Trends is unavailable
USE_MOCK_DATA_ON_FAILURE = True
# Flag to skip real API calls entirely and use mock data directly
ALWAYS_USE_MOCK_DATA = False  # Set to True for testing without Google access


class GoogleTrendsService:
    """Service for fetching Google Trends data."""

    REGION_CONFIG = {
        "AU": {"geo": "AU", "hl": "en-AU", "tz": 600},
        "NZ": {"geo": "NZ", "hl": "en-NZ", "tz": 720},
    }

    def __init__(self):
        self._pytrends: Optional[TrendReq] = None

    def _get_client(self, region: str = "AU") -> TrendReq:
        """Get pytrends client for region with short timeout for faster fallback."""
        config = self.REGION_CONFIG.get(region, self.REGION_CONFIG["AU"])
        return TrendReq(
            hl=config["hl"],
            tz=config["tz"],
            timeout=(3, 5),  # (connect timeout, read timeout) - short for faster mock fallback
        )

    def _fetch_with_retry(self, func, max_retries=3):
        """Execute function with retry logic for rate limiting."""
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "Too Many Requests" in error_str:
                    if attempt < max_retries - 1:
                        sleep_time = (attempt + 1) * 2 + random.uniform(0, 1)
                        time.sleep(sleep_time)
                        continue
                raise e
        return None

    def _generate_mock_data(self, keywords: List[str], region: str, timeframe: str) -> dict:
        """Generate mock trend data for testing when API is unavailable."""
        # Generate 52 weeks of data
        data = []
        base_date = datetime.now() - timedelta(days=365)

        for i in range(52):
            date = base_date + timedelta(weeks=i)
            record = {"date": date.strftime("%Y-%m-%d")}
            for kw in keywords:
                # Generate realistic-looking trend data
                base_value = 50 + random.randint(-20, 20)
                seasonal = 10 * (1 + 0.5 * (i % 12) / 12)  # Seasonal variation
                noise = random.randint(-5, 5)
                record[kw] = max(0, min(100, int(base_value + seasonal + noise)))
            data.append(record)

        return {
            "data": data,
            "keywords": keywords,
            "region": region,
            "timeframe": timeframe,
            "is_mock": True,  # Flag to indicate mock data
        }

    def _generate_mock_related_queries(self, keyword: str, region: str) -> dict:
        """Generate mock related queries for testing."""
        # Sample related queries based on common e-commerce patterns
        top_queries = [
            {"query": f"{keyword} wireless", "value": 100},
            {"query": f"best {keyword}", "value": 85},
            {"query": f"{keyword} bluetooth", "value": 72},
            {"query": f"cheap {keyword}", "value": 65},
            {"query": f"{keyword} price", "value": 58},
        ]
        rising_queries = [
            {"query": f"{keyword} 2024", "value": "Breakout"},
            {"query": f"{keyword} noise cancelling", "value": "+250%"},
            {"query": f"{keyword} for running", "value": "+180%"},
            {"query": f"{keyword} waterproof", "value": "+120%"},
        ]
        return {
            "keyword": keyword,
            "region": region,
            "top": top_queries,
            "rising": rising_queries,
            "is_mock": True,
        }
    
    async def get_interest_over_time(
        self,
        keywords: List[str],
        region: str = "AU",
        timeframe: str = "today 12-m",
    ) -> dict:
        """
        Get interest over time for keywords.

        Args:
            keywords: List of keywords (max 5)
            region: AU or NZ
            timeframe: Time range (e.g., 'today 12-m', 'today 3-m')

        Returns:
            Dictionary with interest data
        """
        def _fetch():
            def _do_fetch():
                pytrends = self._get_client(region)
                geo = self.REGION_CONFIG[region]["geo"]

                pytrends.build_payload(
                    kw_list=keywords[:5],
                    timeframe=timeframe,
                    geo=geo,
                )

                return pytrends.interest_over_time()

            df = self._fetch_with_retry(_do_fetch)

            if df is None or df.empty:
                return {"data": [], "keywords": keywords}

            # Convert to list of dicts
            df = df.reset_index()
            df["date"] = df["date"].dt.strftime("%Y-%m-%d")

            # Remove isPartial column if exists
            if "isPartial" in df.columns:
                df = df.drop(columns=["isPartial"])

            return {
                "data": df.to_dict(orient="records"),
                "keywords": keywords,
                "region": region,
                "timeframe": timeframe,
            }

        # Return mock data directly if configured
        if ALWAYS_USE_MOCK_DATA:
            return self._generate_mock_data(keywords, region, timeframe)

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, _fetch)
        except Exception as e:
            if USE_MOCK_DATA_ON_FAILURE:
                # Return mock data when API fails
                return self._generate_mock_data(keywords, region, timeframe)
            raise e
    
    async def get_related_queries(
        self,
        keyword: str,
        region: str = "AU",
    ) -> dict:
        """
        Get related queries for a keyword.
        
        Returns both 'top' and 'rising' related queries.
        """
        def _fetch():
            pytrends = self._get_client(region)
            geo = self.REGION_CONFIG[region]["geo"]
            
            pytrends.build_payload(
                kw_list=[keyword],
                timeframe="today 12-m",
                geo=geo,
            )
            
            related = pytrends.related_queries()
            
            result = {
                "keyword": keyword,
                "region": region,
                "top": [],
                "rising": [],
            }
            
            if keyword in related:
                top_df = related[keyword].get("top")
                rising_df = related[keyword].get("rising")
                
                if top_df is not None and not top_df.empty:
                    result["top"] = top_df.to_dict(orient="records")
                
                if rising_df is not None and not rising_df.empty:
                    result["rising"] = rising_df.to_dict(orient="records")
            
            return result
        
        # Return mock data directly if configured
        if ALWAYS_USE_MOCK_DATA:
            return self._generate_mock_related_queries(keyword, region)

        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, _fetch)
        except Exception as e:
            if USE_MOCK_DATA_ON_FAILURE:
                return self._generate_mock_related_queries(keyword, region)
            raise e

    async def compare_keywords(
        self,
        keywords: List[str],
        region: str = "AU",
    ) -> dict:
        """Compare interest between multiple keywords."""
        def _fetch():
            pytrends = self._get_client(region)
            geo = self.REGION_CONFIG[region]["geo"]
            
            pytrends.build_payload(
                kw_list=keywords[:5],
                timeframe="today 12-m",
                geo=geo,
            )
            
            df = pytrends.interest_over_time()
            
            if df.empty:
                return {"comparison": [], "keywords": keywords}
            
            # Calculate average interest for each keyword
            comparison = []
            for kw in keywords:
                if kw in df.columns:
                    comparison.append({
                        "keyword": kw,
                        "average_interest": float(df[kw].mean()),
                        "max_interest": int(df[kw].max()),
                        "min_interest": int(df[kw].min()),
                        "current_interest": int(df[kw].iloc[-1]) if len(df) > 0 else 0,
                    })
            
            # Sort by average interest
            comparison.sort(key=lambda x: x["average_interest"], reverse=True)
            
            return {
                "comparison": comparison,
                "keywords": keywords,
                "region": region,
            }
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _fetch)
    
    async def get_suggestions(self, keyword: str) -> List[dict]:
        """Get keyword suggestions from Google Trends."""
        def _fetch():
            pytrends = self._get_client("AU")
            suggestions = pytrends.suggestions(keyword)
            return suggestions
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _fetch)
    
    async def get_interest_by_region(
        self,
        keyword: str,
        resolution: str = "COUNTRY",
    ) -> dict:
        """
        Get interest by region/country.
        
        Args:
            keyword: Search keyword
            resolution: COUNTRY, REGION, CITY, DMA
        """
        def _fetch():
            pytrends = self._get_client("AU")
            
            pytrends.build_payload(
                kw_list=[keyword],
                timeframe="today 12-m",
            )
            
            df = pytrends.interest_by_region(resolution=resolution)
            
            if df.empty:
                return {"data": [], "keyword": keyword}
            
            df = df.reset_index()
            df = df.rename(columns={"geoName": "region", keyword: "interest"})
            df = df[df["interest"] > 0]
            df = df.sort_values("interest", ascending=False)
            
            return {
                "data": df.to_dict(orient="records"),
                "keyword": keyword,
                "resolution": resolution,
            }
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _fetch)
