"""Temu scraper for product data collection."""

import asyncio
import re
from typing import List, Optional
from playwright.async_api import async_playwright, Browser, Page


class TemuScraper:
    """Scraper for Temu (supports AU and NZ markets)."""

    BASE_URLS = {
        "AU": "https://www.temu.com/au",
        "NZ": "https://www.temu.com/nz",
    }

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
        Search products on Temu.

        Args:
            keyword: Search keyword
            region: AU or NZ
            limit: Number of results to fetch

        Returns:
            Dictionary with products and stats
        """
        browser = await self._get_browser()
        page = await browser.new_page()

        base_url = self.BASE_URLS.get(region, self.BASE_URLS["AU"])
        currency = "AUD" if region == "AU" else "NZD"

        try:
            # Set user agent
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })

            # Build search URL
            search_url = f"{base_url}/search_result.html?search_key={keyword}"

            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)  # Wait for dynamic content

            # Get total results count
            total_results = await self._get_results_count(page)

            # Extract products
            products = await self._extract_products(page, limit, region)

            # Calculate price stats
            prices = [p["price"] for p in products if p["price"]]
            price_stats = {
                "min": min(prices) if prices else 0,
                "max": max(prices) if prices else 0,
                "avg": sum(prices) / len(prices) if prices else 0,
            }

            return {
                "platform": f"temu_{region.lower()}",
                "region": region,
                "keyword": keyword,
                "total_results": total_results,
                "products": products,
                "price_stats": price_stats,
                "currency": currency,
            }

        except Exception as e:
            print(f"Temu scraping error: {e}")
            return {
                "platform": f"temu_{region.lower()}",
                "region": region,
                "keyword": keyword,
                "total_results": 0,
                "products": [],
                "price_stats": {"min": 0, "max": 0, "avg": 0},
                "currency": currency,
                "error": str(e),
            }
        finally:
            await page.close()

    async def _get_results_count(self, page: Page) -> int:
        """Extract total results count from page."""
        try:
            # Try to find results count
            count_elem = await page.query_selector("[class*='SearchResultHeader'] span")
            if count_elem:
                text = await count_elem.inner_text()
                match = re.search(r"([\d,]+)", text)
                if match:
                    return int(match.group(1).replace(",", ""))
            return 0
        except Exception:
            return 0

    async def _extract_products(self, page: Page, limit: int, region: str) -> List[dict]:
        """Extract product data from search results page."""
        products = []
        currency = "AUD" if region == "AU" else "NZD"

        # Find product cards - Temu uses various class patterns
        cards = await page.query_selector_all("[class*='ProductCard'], [class*='product-card'], [data-testid='product-card']")

        # If no cards found, try alternative selectors
        if not cards:
            cards = await page.query_selector_all("a[href*='/goods.html']")

        for card in cards[:limit]:
            try:
                # Extract product URL
                href = await card.get_attribute("href")
                if href and "/goods.html" in href:
                    product_url = href if href.startswith("http") else f"https://www.temu.com{href}"
                else:
                    link_elem = await card.query_selector("a[href*='/goods.html']")
                    href = await link_elem.get_attribute("href") if link_elem else ""
                    product_url = href if href.startswith("http") else f"https://www.temu.com{href}"

                # Extract product ID from URL
                product_id_match = re.search(r"goods\.html\?.*goods_id=(\d+)", product_url)
                product_id = product_id_match.group(1) if product_id_match else ""

                # Extract title
                title_elem = await card.query_selector("[class*='title'], [class*='ProductTitle'], h3")
                title = await title_elem.inner_text() if title_elem else ""

                # Extract price
                price_elem = await card.query_selector("[class*='price'], [class*='Price']")
                price_text = await price_elem.inner_text() if price_elem else "0"
                price = self._parse_price(price_text)

                # Extract sold count (if available)
                sold_elem = await card.query_selector("[class*='sold'], [class*='Sold']")
                sold_text = await sold_elem.inner_text() if sold_elem else ""
                sold_count = self._parse_sold_count(sold_text)

                # Extract image
                img_elem = await card.query_selector("img")
                image_url = await img_elem.get_attribute("src") if img_elem else None

                if title:  # Only add if we got a title
                    products.append({
                        "platform_id": product_id,
                        "title": title.strip(),
                        "price": price,
                        "currency": currency,
                        "sold_count": sold_count,
                        "image_url": image_url,
                        "product_url": product_url,
                    })

            except Exception as e:
                print(f"Error extracting Temu product: {e}")
                continue

        return products

    def _parse_price(self, price_text: str) -> Optional[float]:
        """Parse price from text like '$12.99' or 'A$12.99'."""
        price_text = re.sub(r"[^\d.]", "", price_text)
        try:
            return float(price_text) if price_text else None
        except ValueError:
            return None

    def _parse_sold_count(self, sold_text: str) -> int:
        """Parse sold count from text like '1.2k+ sold' or '500+ sold'."""
        if not sold_text:
            return 0

        # Handle "1.2k+" format
        match = re.search(r"([\d.]+)k", sold_text, re.IGNORECASE)
        if match:
            return int(float(match.group(1)) * 1000)

        # Handle regular numbers
        match = re.search(r"([\d,]+)", sold_text)
        if match:
            return int(match.group(1).replace(",", ""))

        return 0
