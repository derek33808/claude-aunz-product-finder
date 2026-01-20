"""eBay API service for product data collection."""

import httpx
from typing import List, Optional
from datetime import datetime

from app.config import settings


class EbayService:
    """Service for interacting with eBay Browse API."""
    
    BASE_URL = "https://api.ebay.com"
    SANDBOX_URL = "https://api.sandbox.ebay.com"
    
    # eBay marketplace IDs
    MARKETPLACE_IDS = {
        "AU": "EBAY_AU",
        "NZ": "EBAY_AU",  # NZ uses AU marketplace
    }
    
    def __init__(self, sandbox: bool = False):
        self.base_url = self.SANDBOX_URL if sandbox else self.BASE_URL
        self.app_id = settings.ebay_app_id
        self.cert_id = settings.ebay_cert_id
        self._access_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
    
    async def _get_access_token(self) -> str:
        """Get OAuth access token from eBay."""
        if self._access_token and self._token_expires and datetime.utcnow() < self._token_expires:
            return self._access_token
        
        # Client credentials grant
        auth_url = f"{self.base_url}/identity/v1/oauth2/token"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                auth_url,
                data={
                    "grant_type": "client_credentials",
                    "scope": "https://api.ebay.com/oauth/api_scope",
                },
                auth=(self.app_id, self.cert_id),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to get eBay access token: {response.text}")
            
            data = response.json()
            self._access_token = data["access_token"]
            # Token expires in seconds, subtract 60 for safety margin
            expires_in = data.get("expires_in", 7200) - 60
            self._token_expires = datetime.utcnow()
            
            return self._access_token
    
    async def search_products(
        self,
        keyword: str,
        region: str = "AU",
        category_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort: str = "BEST_MATCH",
    ) -> List[dict]:
        """
        Search products using eBay Browse API.
        
        Args:
            keyword: Search keyword
            region: AU or NZ
            category_id: eBay category ID (optional)
            limit: Number of results (max 200)
            offset: Pagination offset
            sort: Sort order (BEST_MATCH, PRICE, -PRICE, NEWLY_LISTED)
        """
        token = await self._get_access_token()
        marketplace_id = self.MARKETPLACE_IDS.get(region, "EBAY_AU")
        
        search_url = f"{self.base_url}/buy/browse/v1/item_summary/search"
        
        params = {
            "q": keyword,
            "limit": min(limit, 200),
            "offset": offset,
            "sort": sort,
        }
        
        if category_id:
            params["category_ids"] = category_id
        
        headers = {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": marketplace_id,
            "X-EBAY-C-ENDUSERCTX": f"contextualLocation=country={region}",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(search_url, params=params, headers=headers)
            
            if response.status_code != 200:
                raise Exception(f"eBay search failed: {response.text}")
            
            data = response.json()
            items = data.get("itemSummaries", [])
            
            # Transform to our product format
            products = []
            for item in items:
                product = self._transform_item(item, region)
                products.append(product)
            
            return products
    
    def _transform_item(self, item: dict, region: str) -> dict:
        """Transform eBay item to our product format."""
        price_info = item.get("price", {})
        
        return {
            "platform_id": item.get("itemId", ""),
            "title": item.get("title", ""),
            "category": item.get("categories", [{}])[0].get("categoryName") if item.get("categories") else None,
            "price": float(price_info.get("value", 0)) if price_info.get("value") else None,
            "currency": price_info.get("currency", "AUD"),
            "rating": None,  # Not available in search results
            "review_count": 0,
            "seller_count": 1,
            "bsr_rank": None,
            "image_url": item.get("image", {}).get("imageUrl"),
            "product_url": item.get("itemWebUrl"),
            "raw_data": item,
        }
    
    async def get_product_details(self, item_id: str) -> dict:
        """Get detailed product information."""
        token = await self._get_access_token()
        
        url = f"{self.base_url}/buy/browse/v1/item/{item_id}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_AU",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code != 200:
                raise Exception(f"Failed to get item details: {response.text}")
            
            return response.json()
    
    async def get_trending_items(self, category_id: str, region: str = "AU") -> List[dict]:
        """Get trending items in a category."""
        # eBay doesn't have a direct trending API, so we use search with popularity sort
        return await self.search_products(
            keyword="*",
            region=region,
            category_id=category_id,
            sort="BEST_MATCH",
            limit=50,
        )
