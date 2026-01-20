"""TradeMe scraper using Playwright."""

import asyncio
from typing import List, Optional
from playwright.async_api import async_playwright, Browser, Page
import re


class TradeMeScraper:
    """Scraper for TradeMe (New Zealand marketplace)."""
    
    BASE_URL = "https://www.trademe.co.nz"
    
    def __init__(self):
        self._browser: Optional[Browser] = None
    
    async def _get_browser(self) -> Browser:
        """Get or create browser instance."""
        if self._browser is None:
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
        return self._browser
    
    async def close(self):
        """Close browser."""
        if self._browser:
            await self._browser.close()
            self._browser = None
    
    async def search_products(
        self,
        keyword: str,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 50,
    ) -> List[dict]:
        """
        Search products on TradeMe.
        
        Args:
            keyword: Search keyword
            category: Category filter
            min_price: Minimum price
            max_price: Maximum price
            limit: Number of results to fetch
        """
        browser = await self._get_browser()
        page = await browser.new_page()
        
        try:
            # Build search URL
            search_url = f"{self.BASE_URL}/Browse/SearchResults.aspx?searchString={keyword}&type=Search&searchType=all"
            
            if min_price:
                search_url += f"&price_min={min_price}"
            if max_price:
                search_url += f"&price_max={max_price}"
            
            await page.goto(search_url, wait_until="networkidle")
            
            # Wait for listings to load
            await page.wait_for_selector(".tm-marketplace-search-card", timeout=10000)
            
            # Extract product data
            products = await self._extract_products(page, limit)
            
            return products
            
        except Exception as e:
            print(f"TradeMe scraping error: {e}")
            return []
        finally:
            await page.close()
    
    async def _extract_products(self, page: Page, limit: int) -> List[dict]:
        """Extract product data from search results page."""
        products = []
        
        cards = await page.query_selector_all(".tm-marketplace-search-card")
        
        for card in cards[:limit]:
            try:
                # Extract title
                title_elem = await card.query_selector(".tm-marketplace-search-card__title")
                title = await title_elem.inner_text() if title_elem else ""
                
                # Extract price
                price_elem = await card.query_selector(".tm-marketplace-search-card__price")
                price_text = await price_elem.inner_text() if price_elem else "0"
                price = self._parse_price(price_text)
                
                # Extract URL
                link_elem = await card.query_selector("a")
                url = await link_elem.get_attribute("href") if link_elem else ""
                if url and not url.startswith("http"):
                    url = f"{self.BASE_URL}{url}"
                
                # Extract listing ID from URL
                listing_id = self._extract_listing_id(url)
                
                # Extract image
                img_elem = await card.query_selector("img")
                image_url = await img_elem.get_attribute("src") if img_elem else None
                
                products.append({
                    "platform_id": listing_id,
                    "title": title.strip(),
                    "category": None,
                    "price": price,
                    "currency": "NZD",
                    "rating": None,
                    "review_count": 0,
                    "seller_count": 1,
                    "bsr_rank": None,
                    "image_url": image_url,
                    "product_url": url,
                    "raw_data": {},
                })
                
            except Exception as e:
                print(f"Error extracting product: {e}")
                continue
        
        return products
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """Parse price from text."""
        # Remove currency symbols and commas
        price_text = re.sub(r"[^\d.]", "", price_text)
        try:
            return float(price_text) if price_text else None
        except ValueError:
            return None
    
    def _extract_listing_id(self, url: str) -> str:
        """Extract listing ID from URL."""
        match = re.search(r"/listing/(\d+)", url)
        if match:
            return match.group(1)
        return url.split("/")[-1]
    
    async def get_product_details(self, listing_id: str) -> Optional[dict]:
        """Get detailed product information."""
        browser = await self._get_browser()
        page = await browser.new_page()
        
        try:
            url = f"{self.BASE_URL}/listing/{listing_id}"
            await page.goto(url, wait_until="networkidle")
            
            # Extract detailed info
            title_elem = await page.query_selector("h1")
            title = await title_elem.inner_text() if title_elem else ""
            
            price_elem = await page.query_selector(".tm-buy-box__price")
            price_text = await price_elem.inner_text() if price_elem else "0"
            
            description_elem = await page.query_selector(".tm-markdown")
            description = await description_elem.inner_text() if description_elem else ""
            
            return {
                "platform_id": listing_id,
                "title": title.strip(),
                "price": self._parse_price(price_text),
                "currency": "NZD",
                "description": description,
                "product_url": url,
            }
            
        except Exception as e:
            print(f"Error getting product details: {e}")
            return None
        finally:
            await page.close()
    
    async def get_trending_categories(self) -> List[dict]:
        """Get trending categories from TradeMe."""
        browser = await self._get_browser()
        page = await browser.new_page()
        
        try:
            await page.goto(self.BASE_URL, wait_until="networkidle")
            
            categories = []
            cat_elements = await page.query_selector_all(".tm-root-category-tile")
            
            for elem in cat_elements:
                name_elem = await elem.query_selector(".tm-root-category-tile__name")
                name = await name_elem.inner_text() if name_elem else ""
                
                link_elem = await elem.query_selector("a")
                url = await link_elem.get_attribute("href") if link_elem else ""
                
                if name:
                    categories.append({
                        "name": name.strip(),
                        "url": url,
                    })
            
            return categories
            
        except Exception as e:
            print(f"Error getting categories: {e}")
            return []
        finally:
            await page.close()
