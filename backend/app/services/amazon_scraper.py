"""Amazon AU scraper for product data collection."""

import asyncio
import re
from typing import List, Optional
from playwright.async_api import async_playwright, Browser, Page


class AmazonScraper:
    """Scraper for Amazon Australia (serves both AU and NZ markets)."""

    BASE_URL = "https://www.amazon.com.au"

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
        region: str = "AU",
        limit: int = 20,
    ) -> dict:
        """
        Search products on Amazon AU.

        Args:
            keyword: Search keyword
            region: AU or NZ (both use Amazon AU)
            limit: Number of results to fetch

        Returns:
            Dictionary with products and stats
        """
        browser = await self._get_browser()
        page = await browser.new_page()

        try:
            # Set user agent to avoid bot detection
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })

            # Build search URL
            search_url = f"{self.BASE_URL}/s?k={keyword}"

            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)  # Wait for dynamic content

            # Get total results count
            total_results = await self._get_results_count(page)

            # Extract products
            products = await self._extract_products(page, limit)

            # Calculate price stats
            prices = [p["price"] for p in products if p["price"]]
            price_stats = {
                "min": min(prices) if prices else 0,
                "max": max(prices) if prices else 0,
                "avg": sum(prices) / len(prices) if prices else 0,
            }

            return {
                "platform": "amazon_au",
                "region": region,
                "keyword": keyword,
                "total_results": total_results,
                "products": products,
                "price_stats": price_stats,
                "currency": "AUD",
            }

        except Exception as e:
            print(f"Amazon scraping error: {e}")
            return {
                "platform": "amazon_au",
                "region": region,
                "keyword": keyword,
                "total_results": 0,
                "products": [],
                "price_stats": {"min": 0, "max": 0, "avg": 0},
                "currency": "AUD",
                "error": str(e),
            }
        finally:
            await page.close()

    async def _get_results_count(self, page: Page) -> int:
        """Extract total results count from page."""
        try:
            # Try to find results count text
            count_elem = await page.query_selector(".s-breadcrumb .a-text-bold")
            if count_elem:
                text = await count_elem.inner_text()
                # Extract number from text like "1-48 of over 10,000 results"
                match = re.search(r"of\s+(?:over\s+)?([\d,]+)", text)
                if match:
                    return int(match.group(1).replace(",", ""))

            # Alternative: count from results text
            results_elem = await page.query_selector("[data-component-type='s-result-info-bar']")
            if results_elem:
                text = await results_elem.inner_text()
                match = re.search(r"([\d,]+)\s+results", text)
                if match:
                    return int(match.group(1).replace(",", ""))

            return 0
        except Exception:
            return 0

    async def _extract_products(self, page: Page, limit: int) -> List[dict]:
        """Extract product data from search results page."""
        products = []

        # Find all product cards
        cards = await page.query_selector_all("[data-component-type='s-search-result']")

        for card in cards[:limit]:
            try:
                # Extract ASIN (Amazon product ID)
                asin = await card.get_attribute("data-asin")
                if not asin:
                    continue

                # Extract title
                title_elem = await card.query_selector("h2 a span")
                title = await title_elem.inner_text() if title_elem else ""

                # Extract price
                price_elem = await card.query_selector(".a-price .a-offscreen")
                price_text = await price_elem.inner_text() if price_elem else "0"
                price = self._parse_price(price_text)

                # Extract rating
                rating_elem = await card.query_selector("[data-cy='reviews-ratings-slot'] .a-icon-alt")
                rating_text = await rating_elem.inner_text() if rating_elem else ""
                rating = self._parse_rating(rating_text)

                # Extract review count
                review_elem = await card.query_selector("[data-cy='reviews-ratings-slot'] .a-size-base")
                review_text = await review_elem.inner_text() if review_elem else "0"
                review_count = self._parse_review_count(review_text)

                # Extract image
                img_elem = await card.query_selector(".s-image")
                image_url = await img_elem.get_attribute("src") if img_elem else None

                # Build product URL
                product_url = f"{self.BASE_URL}/dp/{asin}"

                products.append({
                    "platform_id": asin,
                    "title": title.strip(),
                    "price": price,
                    "currency": "AUD",
                    "rating": rating,
                    "review_count": review_count,
                    "image_url": image_url,
                    "product_url": product_url,
                })

            except Exception as e:
                print(f"Error extracting Amazon product: {e}")
                continue

        return products

    def _parse_price(self, price_text: str) -> Optional[float]:
        """Parse price from text like '$29.99'."""
        price_text = re.sub(r"[^\d.]", "", price_text)
        try:
            return float(price_text) if price_text else None
        except ValueError:
            return None

    def _parse_rating(self, rating_text: str) -> Optional[float]:
        """Parse rating from text like '4.5 out of 5 stars'."""
        match = re.search(r"([\d.]+)\s+out", rating_text)
        if match:
            return float(match.group(1))
        return None

    def _parse_review_count(self, review_text: str) -> int:
        """Parse review count from text like '1,234'."""
        review_text = re.sub(r"[^\d]", "", review_text)
        try:
            return int(review_text) if review_text else 0
        except ValueError:
            return 0
