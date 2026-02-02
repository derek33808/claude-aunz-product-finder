"""TradeMe Official API service for product data collection.

TradeMe API Documentation: https://developer.trademe.co.nz/
"""

import httpx
import hashlib
import hmac
import base64
import time
import urllib.parse
from typing import List, Optional, Dict
from datetime import datetime

from app.config import settings


class TradeMeAPIService:
    """Service for interacting with TradeMe Official API."""

    PRODUCTION_URL = "https://api.trademe.co.nz/v1"
    SANDBOX_URL = "https://api.tmsandbox.co.nz/v1"

    def __init__(self, sandbox: bool = None):
        if sandbox is None:
            sandbox = settings.trademe_sandbox
        self.base_url = self.SANDBOX_URL if sandbox else self.PRODUCTION_URL
        self.consumer_key = settings.trademe_consumer_key
        self.consumer_secret = settings.trademe_consumer_secret
        self.oauth_token = settings.trademe_oauth_token
        self.oauth_token_secret = settings.trademe_oauth_token_secret

    def _generate_oauth_signature(
        self,
        method: str,
        url: str,
        params: Dict[str, str],
        oauth_params: Dict[str, str],
    ) -> str:
        """Generate OAuth 1.0a signature."""
        # Combine all parameters
        all_params = {**params, **oauth_params}

        # Sort and encode parameters
        sorted_params = sorted(all_params.items())
        param_string = "&".join(
            f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(str(v), safe='')}"
            for k, v in sorted_params
        )

        # Create signature base string
        base_string = "&".join([
            method.upper(),
            urllib.parse.quote(url, safe=''),
            urllib.parse.quote(param_string, safe=''),
        ])

        # Create signing key
        signing_key = "&".join([
            urllib.parse.quote(self.consumer_secret, safe=''),
            urllib.parse.quote(self.oauth_token_secret or '', safe=''),
        ])

        # Generate signature
        signature = hmac.new(
            signing_key.encode('utf-8'),
            base_string.encode('utf-8'),
            hashlib.sha1
        ).digest()

        return base64.b64encode(signature).decode('utf-8')

    def _get_oauth_header(self, method: str, url: str, params: Dict[str, str] = None) -> str:
        """Generate OAuth Authorization header."""
        params = params or {}

        oauth_params = {
            "oauth_consumer_key": self.consumer_key,
            "oauth_nonce": str(int(time.time() * 1000)),
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_version": "1.0",
        }

        if self.oauth_token:
            oauth_params["oauth_token"] = self.oauth_token

        # Generate signature
        signature = self._generate_oauth_signature(method, url, params, oauth_params)
        oauth_params["oauth_signature"] = signature

        # Build header
        header_params = ", ".join(
            f'{k}="{urllib.parse.quote(str(v), safe="")}"'
            for k, v in sorted(oauth_params.items())
        )

        return f"OAuth {header_params}"

    async def search_general(
        self,
        keyword: str,
        category: str = "",
        rows: int = 50,
        page: int = 1,
        sort_order: str = "Default",
    ) -> Dict:
        """
        Search TradeMe General listings.

        Args:
            keyword: Search string
            category: Category number (e.g., "0001-" for Electronics)
            rows: Number of results per page (max 500)
            page: Page number (1-indexed)
            sort_order: BuyNowPrice, ExpiryAsc, ExpiryDesc, etc.

        Returns:
            Dict with TotalCount, Page, PageSize, List of items
        """
        url = f"{self.base_url}/Search/General.json"

        params = {
            "search_string": keyword,
            "rows": min(rows, 500),
            "page": page,
            "sort_order": sort_order,
        }

        if category:
            params["category"] = category

        auth_header = self._get_oauth_header("GET", url, params)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                headers={"Authorization": auth_header},
                timeout=30.0,
            )

            if response.status_code != 200:
                raise Exception(f"TradeMe search failed: {response.status_code} - {response.text}")

            return response.json()

    async def search_products(
        self,
        keyword: str,
        limit: int = 50,
        page: int = 1,
    ) -> Dict:
        """
        Search TradeMe and return formatted results.

        Args:
            keyword: Search keyword
            limit: Number of results
            page: Page number

        Returns:
            Dict with total_results, products list, price_stats
        """
        try:
            data = await self.search_general(keyword, rows=limit, page=page)

            items = data.get("List", [])
            total_count = data.get("TotalCount", 0)

            products = []
            prices = []

            for item in items:
                price = None
                if item.get("BuyNowPrice"):
                    price = float(item["BuyNowPrice"])
                elif item.get("StartPrice"):
                    price = float(item["StartPrice"])

                if price:
                    prices.append(price)

                products.append({
                    "platform_id": str(item.get("ListingId", "")),
                    "title": item.get("Title", ""),
                    "price": price,
                    "currency": "NZD",
                    "image_url": item.get("PictureHref"),
                    "product_url": f"https://www.trademe.co.nz/a/{item.get('ListingId')}",
                    "category": item.get("Category"),
                    "region": item.get("Region"),
                    "is_buy_now": item.get("HasBuyNow", False),
                    "closing_date": item.get("EndDate"),
                })

            return {
                "total_results": total_count,
                "products": products,
                "price_stats": {
                    "min": min(prices) if prices else 0,
                    "max": max(prices) if prices else 0,
                    "avg": sum(prices) / len(prices) if prices else 0,
                },
            }

        except Exception as e:
            print(f"[TradeMe API] Error: {e}")
            return {
                "total_results": 0,
                "products": [],
                "price_stats": {"min": 0, "max": 0, "avg": 0},
                "error": str(e),
            }

    async def get_categories(self) -> List[Dict]:
        """Get TradeMe category tree."""
        url = f"{self.base_url}/Categories.json"

        auth_header = self._get_oauth_header("GET", url)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": auth_header},
                timeout=30.0,
            )

            if response.status_code != 200:
                raise Exception(f"Failed to get categories: {response.text}")

            return response.json().get("Subcategories", [])

    async def get_listing_details(self, listing_id: int) -> Dict:
        """Get detailed information about a listing."""
        url = f"{self.base_url}/Listings/{listing_id}.json"

        auth_header = self._get_oauth_header("GET", url)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": auth_header},
                timeout=30.0,
            )

            if response.status_code != 200:
                raise Exception(f"Failed to get listing: {response.text}")

            return response.json()


# Convenience function to check if API is configured
def is_trademe_api_configured() -> bool:
    """Check if TradeMe API credentials are configured."""
    return bool(settings.trademe_consumer_key and settings.trademe_consumer_secret)
