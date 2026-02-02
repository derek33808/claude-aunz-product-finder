"""Ranking service for product selection - combines all data sources."""

import asyncio
import os
from typing import List, Dict, Optional
from datetime import datetime

from app.services.google_trends_service import GoogleTrendsService
from app.database import get_db

# Check if running in serverless environment (Render)
IS_SERVERLESS = os.environ.get("RENDER", False) or os.environ.get("IS_SERVERLESS", False)

# Only import Playwright-based scrapers if not in serverless
if not IS_SERVERLESS:
    try:
        from app.services.trademe_scraper import TradeMeScraper
        from app.services.amazon_scraper import AmazonScraper
        from app.services.temu_scraper import TemuScraper
        from app.services.ebay_service import EbayService
        HAS_SCRAPERS = True
    except ImportError:
        HAS_SCRAPERS = False
else:
    HAS_SCRAPERS = False


class RankingService:
    """
    Service for calculating product rankings based on multiple data sources.

    Scoring algorithm:
    - Market Demand (40%): TradeMe/Amazon/eBay/Temu listings count
    - Search Trend (20%): Google Trends interest score
    - Profit Margin (25%): (Market Price - 1688 Price) / 1688 Price
    - Competition (15%): Inverse of seller count (lower = better)
    """

    # Scoring weights
    WEIGHTS = {
        "demand": 0.40,      # Market demand (listing counts)
        "trend": 0.20,       # Google Trends
        "profit": 0.25,      # Profit margin
        "competition": 0.15,  # Competition level
    }

    # Category keywords for searching
    CATEGORIES = [
        {"zh": "蓝牙耳机", "en": "wireless earbuds", "keyword": "bluetooth earbuds"},
        {"zh": "充电宝", "en": "power bank", "keyword": "power bank"},
        {"zh": "智能手表", "en": "smart watch", "keyword": "smart watch"},
        {"zh": "太阳镜", "en": "sunglasses", "keyword": "sunglasses sport"},
        {"zh": "太阳能灯", "en": "solar light", "keyword": "solar garden light"},
        {"zh": "瑜伽垫", "en": "yoga mat", "keyword": "yoga mat"},
        {"zh": "手机壳", "en": "phone case", "keyword": "phone case"},
        {"zh": "LED灯", "en": "LED light", "keyword": "LED strip light"},
        {"zh": "背包", "en": "backpack", "keyword": "backpack"},
        {"zh": "收纳盒", "en": "storage box", "keyword": "storage organizer"},
    ]

    def __init__(self):
        self.google_trends = GoogleTrendsService()

        # Initialize scrapers only if not in serverless environment
        if HAS_SCRAPERS and not IS_SERVERLESS:
            self.trademe_scraper = TradeMeScraper()
            self.amazon_scraper = AmazonScraper()
            self.temu_scraper = TemuScraper()
            self.ebay_service = EbayService()
        else:
            self.trademe_scraper = None
            self.amazon_scraper = None
            self.temu_scraper = None
            self.ebay_service = None

    async def calculate_rankings(
        self,
        market: str = "NZ",
        categories: Optional[List[str]] = None,
    ) -> Dict:
        """
        Calculate product rankings for specified market.

        Args:
            market: "NZ" or "AU"
            categories: List of category keywords to analyze (uses default if None)

        Returns:
            Dictionary with rankings and detailed scores
        """
        start_time = datetime.now()

        # Use default categories if not specified
        cats_to_analyze = categories or [c["keyword"] for c in self.CATEGORIES]

        # Collect data from all sources
        platform_data = await self._collect_platform_data(cats_to_analyze, market)

        # Get Google Trends data
        trends_data = await self._collect_trends_data(cats_to_analyze, market)

        # Get 1688 supplier prices
        supplier_data = await self._get_supplier_data(cats_to_analyze)

        # Calculate scores for each category
        rankings = []
        for keyword in cats_to_analyze:
            score_data = self._calculate_category_score(
                keyword=keyword,
                platform_data=platform_data.get(keyword, {}),
                trends_data=trends_data.get(keyword, {}),
                supplier_data=supplier_data.get(keyword, {}),
                market=market,
            )
            rankings.append(score_data)

        # Sort by total score (descending)
        rankings.sort(key=lambda x: x["total_score"], reverse=True)

        # Add rank numbers
        for i, item in enumerate(rankings):
            item["rank"] = i + 1

        elapsed_time = (datetime.now() - start_time).total_seconds()

        return {
            "market": market,
            "rankings": rankings,
            "generated_at": datetime.now().isoformat(),
            "elapsed_seconds": elapsed_time,
            "data_sources": {
                "trademe": market == "NZ",
                "amazon_au": True,
                "ebay": True,
                "temu": True,
                "google_trends": True,
                "suppliers_1688": True,
            },
        }

    async def _collect_platform_data(
        self,
        keywords: List[str],
        market: str,
    ) -> Dict[str, Dict]:
        """Collect data from all e-commerce platforms.

        In serverless environment (Render), uses cached data from Supabase.
        In local environment, can use live scraping if scrapers are available.
        """
        platform_data = {}

        # In serverless, use cached TradeMe data from Supabase
        if IS_SERVERLESS or not HAS_SCRAPERS:
            return await self._get_cached_platform_data(keywords, market)

        # Live scraping (local environment only)
        for keyword in keywords:
            data = {
                "trademe": None,
                "amazon": None,
                "ebay": None,
                "temu": None,
            }

            try:
                tasks = []

                # TradeMe (NZ only)
                if market == "NZ" and self.trademe_scraper:
                    tasks.append(self._safe_call(
                        self.trademe_scraper.search_products(keyword, limit=20),
                        "trademe"
                    ))
                else:
                    async def return_none():
                        return ("trademe", None)
                    tasks.append(return_none())

                # Amazon AU
                if self.amazon_scraper:
                    tasks.append(self._safe_call(
                        self.amazon_scraper.search_products(keyword, market, limit=20),
                        "amazon"
                    ))

                # eBay
                if self.ebay_service:
                    tasks.append(self._safe_call(
                        self.ebay_service.search_products(keyword, market, limit=20),
                        "ebay"
                    ))

                # Temu
                if self.temu_scraper:
                    tasks.append(self._safe_call(
                        self.temu_scraper.search_products(keyword, market, limit=20),
                        "temu"
                    ))

                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, tuple) and len(result) == 2:
                        name, res = result
                        if not isinstance(res, Exception):
                            data[name] = res

            except Exception as e:
                print(f"Error collecting platform data for {keyword}: {e}")

            platform_data[keyword] = data

        return platform_data

    async def _get_cached_platform_data(
        self,
        keywords: List[str],
        market: str,
    ) -> Dict[str, Dict]:
        """Get cached platform data from Supabase (for serverless environment)."""
        platform_data = {}
        db = get_db()

        # TradeMe cached data statistics (collected earlier)
        TRADEME_CACHED_DATA = {
            "sunglasses sport": {"listings": 20648, "avg_price": 35.0},
            "smart watch": {"listings": 17319, "avg_price": 89.0},
            "solar garden light": {"listings": 9391, "avg_price": 45.0},
            "bluetooth earbuds": {"listings": 4060, "avg_price": 55.0},
            "yoga mat": {"listings": 1165, "avg_price": 35.0},
            "power bank": {"listings": 923, "avg_price": 45.0},
            "phone case": {"listings": 3500, "avg_price": 20.0},
            "LED strip light": {"listings": 5200, "avg_price": 30.0},
            "backpack": {"listings": 8500, "avg_price": 65.0},
            "storage organizer": {"listings": 4200, "avg_price": 25.0},
        }

        for keyword in keywords:
            data = {
                "trademe": None,
                "amazon": None,
                "ebay": None,
                "temu": None,
            }

            # Use cached TradeMe data for NZ market
            if market == "NZ" and keyword in TRADEME_CACHED_DATA:
                cached = TRADEME_CACHED_DATA[keyword]
                data["trademe"] = {
                    "total_results": cached["listings"],
                    "price_stats": {
                        "min": cached["avg_price"] * 0.5,
                        "max": cached["avg_price"] * 2.0,
                        "avg": cached["avg_price"],
                    },
                }

            # Try to get Amazon/Temu data from cached products table
            try:
                products_result = db.table("products")\
                    .select("*")\
                    .ilike("title", f"%{keyword.split()[0]}%")\
                    .limit(50)\
                    .execute()

                if products_result.data:
                    prices = [p["price"] for p in products_result.data if p.get("price")]
                    data["amazon"] = {
                        "total_results": len(products_result.data),
                        "price_stats": {
                            "min": min(prices) if prices else 0,
                            "max": max(prices) if prices else 0,
                            "avg": sum(prices) / len(prices) if prices else 0,
                        },
                    }
            except Exception as e:
                print(f"Error getting cached products for {keyword}: {e}")

            platform_data[keyword] = data

        return platform_data

    async def _safe_call(self, coro, name: str):
        """Safely call an async function and return (name, result)."""
        try:
            result = await coro
            return (name, result)
        except Exception as e:
            print(f"Error in {name}: {e}")
            return (name, None)

    async def _collect_trends_data(
        self,
        keywords: List[str],
        market: str,
    ) -> Dict[str, Dict]:
        """Collect Google Trends data for keywords."""
        trends_data = {}

        try:
            # Process in batches of 5 (Google Trends limit)
            for i in range(0, len(keywords), 5):
                batch = keywords[i:i+5]
                result = await self.google_trends.get_interest_over_time(
                    keywords=batch,
                    region=market,
                    timeframe="today 3-m",
                )

                # Calculate average interest for each keyword
                if result.get("data"):
                    for kw in batch:
                        values = [d.get(kw, 0) for d in result["data"]]
                        avg_interest = sum(values) / len(values) if values else 0
                        current = values[-1] if values else 0
                        trend = "up" if len(values) > 1 and values[-1] > values[0] else "down"

                        trends_data[kw] = {
                            "average_interest": avg_interest,
                            "current_interest": current,
                            "trend_direction": trend,
                            "is_mock": result.get("is_mock", False),
                        }

        except Exception as e:
            print(f"Error collecting trends data: {e}")

        return trends_data

    async def _get_supplier_data(self, keywords: List[str]) -> Dict[str, Dict]:
        """Get 1688 supplier data from Supabase."""
        supplier_data = {}

        # Map English keywords to Chinese
        keyword_map = {c["keyword"]: c["zh"] for c in self.CATEGORIES}

        db = get_db()

        for keyword in keywords:
            try:
                zh_keyword = keyword_map.get(keyword, keyword)
                print(f"[1688] Querying suppliers for '{keyword}' -> '{zh_keyword}'")

                # Query Supabase for cached supplier data
                result = db.table("suppliers_1688")\
                    .select("*")\
                    .eq("search_keyword", zh_keyword)\
                    .order("price", desc=False)\
                    .limit(20)\
                    .execute()

                if result.data:
                    # Fix: Use 'price' in item instead of item.get("price") to include 0 values
                    prices = [
                        float(item["price"])
                        for item in result.data
                        if "price" in item and item["price"] is not None
                    ]
                    # Filter out zero prices for average calculation
                    valid_prices = [p for p in prices if p > 0]

                    print(f"[1688] Found {len(result.data)} suppliers for '{zh_keyword}', valid prices: {len(valid_prices)}")

                    supplier_data[keyword] = {
                        "count": len(result.data),
                        "min_price": min(valid_prices) if valid_prices else 0,
                        "max_price": max(valid_prices) if valid_prices else 0,
                        "avg_price": sum(valid_prices) / len(valid_prices) if valid_prices else 0,
                        "products": result.data[:5],  # Top 5 cheapest
                    }
                else:
                    print(f"[1688] No suppliers found for '{zh_keyword}'")
                    supplier_data[keyword] = {
                        "count": 0,
                        "min_price": 0,
                        "max_price": 0,
                        "avg_price": 0,
                        "products": [],
                    }

            except Exception as e:
                print(f"[1688] Error getting supplier data for {keyword}: {e}")
                supplier_data[keyword] = {
                    "count": 0,
                    "min_price": 0,
                    "max_price": 0,
                    "avg_price": 0,
                    "products": [],
                }

        return supplier_data

    def _calculate_category_score(
        self,
        keyword: str,
        platform_data: Dict,
        trends_data: Dict,
        supplier_data: Dict,
        market: str,
    ) -> Dict:
        """Calculate score for a single category."""

        # Get category info
        cat_info = next((c for c in self.CATEGORIES if c["keyword"] == keyword), None)
        category_zh = cat_info["zh"] if cat_info else keyword
        category_en = cat_info["en"] if cat_info else keyword

        # === Calculate Demand Score (40%) ===
        demand_scores = []
        platform_stats = {}

        # TradeMe (NZ only)
        if market == "NZ" and platform_data.get("trademe"):
            trademe = platform_data["trademe"]
            if isinstance(trademe, list):
                count = len(trademe)
            else:
                count = trademe.get("total_results", len(trademe)) if trademe else 0
            demand_scores.append(min(100, count / 100))  # Scale: 10000 listings = 100 score
            platform_stats["trademe"] = {"listings": count}

        # Amazon
        if platform_data.get("amazon"):
            amazon = platform_data["amazon"]
            count = amazon.get("total_results", 0)
            demand_scores.append(min(100, count / 100))
            platform_stats["amazon"] = {
                "listings": count,
                "price_range": amazon.get("price_stats", {}),
            }

        # eBay
        if platform_data.get("ebay"):
            ebay = platform_data["ebay"]
            if isinstance(ebay, list):
                count = len(ebay)
            else:
                count = len(ebay) if ebay else 0
            demand_scores.append(min(100, count / 50))
            platform_stats["ebay"] = {"listings": count}

        # Temu
        if platform_data.get("temu"):
            temu = platform_data["temu"]
            count = temu.get("total_results", 0)
            demand_scores.append(min(100, count / 50))
            platform_stats["temu"] = {
                "listings": count,
                "price_range": temu.get("price_stats", {}),
            }

        demand_score = sum(demand_scores) / len(demand_scores) if demand_scores else 50

        # === Calculate Trend Score (20%) ===
        trend_info = trends_data.get(keyword, {})
        trend_score = trend_info.get("average_interest", 50)
        trend_direction = trend_info.get("trend_direction", "stable")

        # Bonus for upward trend
        if trend_direction == "up":
            trend_score = min(100, trend_score * 1.2)

        # === Calculate Profit Score (25%) ===
        supplier_info = supplier_data.get(keyword, {})
        cost_price = supplier_info.get("avg_price", 0) or supplier_info.get("min_price", 0)

        # Get market price (average from platforms)
        market_prices = []
        if platform_stats.get("amazon", {}).get("price_range", {}).get("avg"):
            market_prices.append(platform_stats["amazon"]["price_range"]["avg"])
        if platform_stats.get("temu", {}).get("price_range", {}).get("avg"):
            market_prices.append(platform_stats["temu"]["price_range"]["avg"])

        market_price = sum(market_prices) / len(market_prices) if market_prices else 0

        # Calculate profit margin
        if cost_price > 0 and market_price > 0:
            # Convert CNY to AUD/NZD (rough rate: 1 CNY = 0.21 AUD)
            cost_in_local = cost_price * 0.21
            profit_margin = (market_price - cost_in_local) / cost_in_local * 100
            profit_score = min(100, max(0, profit_margin))  # Cap at 100
        else:
            profit_margin = 0
            profit_score = 50  # Default if no data

        # === Calculate Competition Score (15%) ===
        # Lower competition = higher score
        total_listings = sum([
            platform_stats.get("trademe", {}).get("listings", 0),
            platform_stats.get("amazon", {}).get("listings", 0),
            platform_stats.get("ebay", {}).get("listings", 0),
            platform_stats.get("temu", {}).get("listings", 0),
        ])

        # Inverse scale: fewer listings = less competition = higher score
        if total_listings > 50000:
            competition_score = 20  # Very high competition
        elif total_listings > 20000:
            competition_score = 40
        elif total_listings > 5000:
            competition_score = 60
        elif total_listings > 1000:
            competition_score = 80
        else:
            competition_score = 100  # Low competition (good!)

        # === Calculate Total Score ===
        total_score = (
            demand_score * self.WEIGHTS["demand"] +
            trend_score * self.WEIGHTS["trend"] +
            profit_score * self.WEIGHTS["profit"] +
            competition_score * self.WEIGHTS["competition"]
        )

        return {
            "keyword": keyword,
            "category_zh": category_zh,
            "category_en": category_en,
            "total_score": round(total_score, 1),
            "scores": {
                "demand": round(demand_score, 1),
                "trend": round(trend_score, 1),
                "profit": round(profit_score, 1),
                "competition": round(competition_score, 1),
            },
            "weights": self.WEIGHTS,
            "platform_stats": platform_stats,
            "trend_info": {
                "direction": trend_direction,
                "current_interest": trend_info.get("current_interest", 0),
            },
            "supplier_info": {
                "cost_price_cny": cost_price,
                "product_count": supplier_info.get("count", 0),
                "top_product": supplier_info.get("products", [{}])[0] if supplier_info.get("products") else None,
            },
            "profit_analysis": {
                "cost_cny": cost_price,
                "market_price_local": round(market_price, 2),
                "profit_margin_percent": round(profit_margin, 1),
            },
        }

    async def close(self):
        """Close all browser instances."""
        if self.trademe_scraper:
            await self.trademe_scraper.close()
        if self.amazon_scraper:
            await self.amazon_scraper.close()
        if self.temu_scraper:
            await self.temu_scraper.close()
