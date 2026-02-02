"""1688.com supplier scraper using Playwright."""

import asyncio
import re
import math
import json
from typing import List, Optional, Tuple, Dict, Any, TYPE_CHECKING
from pydantic import BaseModel

from app.config import settings

# Playwright is optional - only required for actual scraping
# In production without Playwright, the service returns mock/empty results
PLAYWRIGHT_AVAILABLE = False
STEALTH_AVAILABLE = False
try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    # Playwright not installed - scraping will be disabled
    async_playwright = None
    Browser = None
    Page = None

# Stealth plugin to bypass bot detection
try:
    from playwright_stealth import stealth_async
    STEALTH_AVAILABLE = True
except ImportError:
    stealth_async = None
    print("[1688] Warning: playwright-stealth not installed, bot detection bypass disabled")


# ============ Data Models ============

class Supplier1688(BaseModel):
    """1688 supplier data model."""
    offer_id: str
    title: str
    price: float
    price_range: Optional[str] = None
    moq: int = 1
    sold_count: int = 0
    image_url: Optional[str] = None
    product_url: str

    # Supplier info
    supplier_name: str
    supplier_url: Optional[str] = None
    supplier_years: Optional[int] = None
    supplier_rating: Optional[float] = None
    is_verified: bool = False

    # Logistics info
    location: Optional[str] = None
    shipping_estimate: Optional[str] = None

    # Product attributes
    weight: Optional[float] = None
    dimensions: Optional[str] = None
    is_small_medium: bool = True

    # Matching score
    match_score: Optional[float] = None


# ============ Constants ============

# Exchange rates (can be updated dynamically)
EXCHANGE_RATES = {
    "AUD_CNY": 4.70,
    "NZD_CNY": 4.30,
    "CNY_AUD": 0.213,
    "CNY_NZD": 0.233,
}

# Size limits for small/medium items
SIZE_LIMITS = {
    "max_weight_kg": 5,
    "max_length_cm": 60,
    "max_volume_cm3": 50000,
}

# Common product keywords mapping (English -> Chinese)
PRODUCT_KEYWORD_MAP = {
    # Electronics
    "wireless earbuds": ["无线耳机", "蓝牙耳机", "TWS耳机"],
    "bluetooth earbuds": ["蓝牙耳机", "无线蓝牙耳机"],
    "headphones": ["耳机", "头戴式耳机"],
    "speaker": ["音箱", "蓝牙音箱", "音响"],
    "charger": ["充电器", "快充充电器"],
    "power bank": ["充电宝", "移动电源"],
    "phone case": ["手机壳", "手机保护套"],
    "screen protector": ["钢化膜", "屏幕保护膜"],
    "cable": ["数据线", "充电线"],
    "usb cable": ["USB数据线", "充电线"],
    "smart watch": ["智能手表", "运动手表"],
    "fitness tracker": ["运动手环", "智能手环"],

    # Home & Garden
    "led light": ["LED灯", "灯带", "LED灯条"],
    "lamp": ["台灯", "灯具"],
    "storage box": ["收纳箱", "收纳盒"],
    "organizer": ["收纳架", "收纳盒"],
    "kitchen tool": ["厨房用品", "厨具"],
    "water bottle": ["水杯", "保温杯", "水壶"],
    "pillow": ["枕头", "靠枕"],
    "blanket": ["毛毯", "毯子"],
    "curtain": ["窗帘"],
    "rug": ["地毯", "地垫"],

    # Fashion
    "watch": ["手表", "石英表"],
    "sunglasses": ["太阳镜", "墨镜"],
    "bag": ["包", "背包", "手提包"],
    "backpack": ["背包", "双肩包"],
    "wallet": ["钱包", "皮夹"],
    "belt": ["皮带", "腰带"],
    "hat": ["帽子", "鸭舌帽"],
    "scarf": ["围巾", "丝巾"],
    "jewelry": ["首饰", "饰品"],
    "necklace": ["项链"],
    "bracelet": ["手链", "手镯"],
    "ring": ["戒指"],
    "earrings": ["耳环", "耳饰"],

    # Toys & Games
    "toy": ["玩具"],
    "puzzle": ["拼图", "益智玩具"],
    "board game": ["桌游", "棋牌游戏"],
    "drone": ["无人机", "遥控飞机"],
    "rc car": ["遥控车", "RC汽车"],
    "plush toy": ["毛绒玩具", "公仔"],

    # Sports
    "yoga mat": ["瑜伽垫"],
    "resistance band": ["弹力带", "拉力带"],
    "dumbbell": ["哑铃"],
    "sports bottle": ["运动水壶"],
    "gym bag": ["健身包", "运动包"],

    # Beauty
    "makeup brush": ["化妆刷", "刷子套装"],
    "makeup": ["化妆品", "彩妆"],
    "skincare": ["护肤品"],
    "hair tool": ["美发工具"],
    "nail art": ["美甲", "指甲油"],

    # Pet
    "pet toy": ["宠物玩具", "狗玩具", "猫玩具"],
    "pet bed": ["宠物窝", "狗窝", "猫窝"],
    "pet collar": ["宠物项圈", "狗项圈"],
    "pet bowl": ["宠物碗", "狗碗", "猫碗"],
}


# ============ Utility Functions ============

def extract_keywords(product_title: str) -> List[str]:
    """
    Extract core keywords from product title.

    Args:
        product_title: Product title in English

    Returns:
        List of extracted keywords
    """
    # Normalize
    title = product_title.lower()

    # Remove common noise words
    noise_words = [
        'for', 'with', 'and', 'the', 'a', 'an', 'of', 'in', 'on', 'at',
        'new', 'hot', 'best', 'sale', 'free', 'shipping', 'pack', 'pcs',
        'set', 'kit', 'piece', 'pieces', 'lot', '2024', '2025', '2026'
    ]

    # Remove brand names (common patterns)
    brand_patterns = [
        r'\b[A-Z][a-z]+\s+(?:brand|official)\b',
        r'\b(?:genuine|original|authentic)\b',
    ]
    for pattern in brand_patterns:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)

    # Split into words
    words = re.findall(r'\b[a-z]+\b', title)

    # Filter noise words
    words = [w for w in words if w not in noise_words and len(w) > 2]

    # Generate keyword combinations
    keywords = []

    # Single important words
    important_words = words[:5]  # First 5 significant words

    # Two-word combinations
    for i in range(len(words) - 1):
        two_word = f"{words[i]} {words[i+1]}"
        if two_word in PRODUCT_KEYWORD_MAP:
            keywords.append(two_word)

    # Add single words as fallback
    for word in important_words:
        if word not in [k.split()[0] for k in keywords]:
            keywords.append(word)

    # Limit to top 3 keywords
    return keywords[:3] if keywords else words[:3]


def translate_to_chinese(keywords: List[str]) -> List[str]:
    """
    Translate English keywords to Chinese.

    Uses local keyword mapping for common product terms.
    Falls back to simple word combinations if no match found.

    Args:
        keywords: List of English keywords

    Returns:
        List of Chinese keywords
    """
    chinese_keywords = []

    for keyword in keywords:
        keyword_lower = keyword.lower().strip()

        # Check exact match in mapping
        if keyword_lower in PRODUCT_KEYWORD_MAP:
            chinese_keywords.extend(PRODUCT_KEYWORD_MAP[keyword_lower])
        else:
            # Try partial match
            for eng, chi_list in PRODUCT_KEYWORD_MAP.items():
                if keyword_lower in eng or eng in keyword_lower:
                    chinese_keywords.extend(chi_list[:1])  # Add first match only
                    break

    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for k in chinese_keywords:
        if k not in seen:
            seen.add(k)
            unique_keywords.append(k)

    return unique_keywords[:5] if unique_keywords else ["产品"]  # Fallback


def parse_dimensions(dim_str: str) -> Optional[Tuple[float, float, float]]:
    """
    Parse dimensions string to tuple.

    Args:
        dim_str: Dimension string like "60x40x30cm" or "60*40*30"

    Returns:
        Tuple of (length, width, height) or None
    """
    if not dim_str:
        return None

    match = re.search(
        r"(\d+\.?\d*)\s*[xX*]\s*(\d+\.?\d*)\s*[xX*]\s*(\d+\.?\d*)",
        dim_str
    )
    if match:
        return (
            float(match.group(1)),
            float(match.group(2)),
            float(match.group(3))
        )
    return None


def filter_by_price(supplier: Supplier1688, max_price: float = 500) -> bool:
    """Filter supplier by price."""
    return supplier.price <= max_price


def filter_by_size(supplier: Supplier1688) -> bool:
    """
    Filter supplier by size/weight.

    Returns True if item is small/medium sized.
    """
    # Weight check
    if supplier.weight and supplier.weight > SIZE_LIMITS["max_weight_kg"]:
        return False

    # Dimensions check
    if supplier.dimensions:
        dimensions = parse_dimensions(supplier.dimensions)
        if dimensions:
            length, width, height = dimensions
            # Check longest side
            if max(length, width, height) > SIZE_LIMITS["max_length_cm"]:
                return False
            # Check volume
            if length * width * height > SIZE_LIMITS["max_volume_cm3"]:
                return False

    return supplier.is_small_medium


def calculate_supplier_score(
    supplier: Supplier1688,
    source_price: float,
    source_currency: str = "AUD",
) -> float:
    """
    Calculate comprehensive supplier score.

    Score dimensions:
    - Price competitiveness: 30%
    - Supplier reputation: 25%
    - Sales performance: 20%
    - Logistics friendliness: 15%
    - Matching relevance: 10%

    Args:
        supplier: Supplier data
        source_price: Source product price
        source_currency: Source currency (AUD/NZD)

    Returns:
        Score from 0-100
    """
    exchange_rate = EXCHANGE_RATES.get(f"{source_currency}_CNY", 4.5)

    # 1. Price competitiveness score (0-100)
    # Target: supplier cost should be ~30% of selling price
    target_cost_cny = source_price * exchange_rate * 0.3

    if supplier.price <= target_cost_cny * 0.5:
        price_score = 100
    elif supplier.price <= target_cost_cny:
        price_score = 70 + 30 * (1 - supplier.price / target_cost_cny)
    elif supplier.price <= target_cost_cny * 1.5:
        price_score = 40
    else:
        price_score = 20

    # 2. Supplier reputation score (0-100)
    reputation_score = 0
    if supplier.supplier_rating:
        reputation_score += supplier.supplier_rating * 15  # Max 75
    if supplier.is_verified:
        reputation_score += 15
    if supplier.supplier_years:
        reputation_score += min(supplier.supplier_years * 2, 10)  # Max 10

    # 3. Sales score (0-100)
    if supplier.sold_count > 0:
        sales_score = min(math.log10(supplier.sold_count + 1) * 25, 100)
    else:
        sales_score = 0

    # 4. Logistics score (0-100)
    logistics_score = 70  # Base score
    if supplier.is_small_medium:
        logistics_score += 30

    # 5. Match relevance (assumed good from search ranking)
    match_score = 80

    # Calculate weighted final score
    final_score = (
        price_score * 0.30 +
        reputation_score * 0.25 +
        sales_score * 0.20 +
        logistics_score * 0.15 +
        match_score * 0.10
    )

    return round(final_score, 2)


def calculate_profit_estimate(
    source_price: float,
    source_currency: str,
    supplier_price: float,
    quantity: int = 100,
    shipping_per_unit: float = 15,  # Estimated shipping cost per unit in CNY
) -> Dict[str, Any]:
    """
    Calculate profit estimation.

    Args:
        source_price: Selling price in source currency
        source_currency: AUD or NZD
        supplier_price: Purchase price in CNY
        quantity: Purchase quantity
        shipping_per_unit: Estimated shipping cost per unit in CNY

    Returns:
        Profit estimation details
    """
    exchange_rate = EXCHANGE_RATES.get(f"{source_currency}_CNY", 4.5)
    exchange_rate_reverse = EXCHANGE_RATES.get(f"CNY_{source_currency}", 0.22)

    # Costs in CNY
    purchase_cost_cny = supplier_price * quantity
    shipping_cost_cny = shipping_per_unit * quantity
    total_cost_cny = purchase_cost_cny + shipping_cost_cny

    # Convert to target currency
    total_cost_target = total_cost_cny * exchange_rate_reverse

    # Revenue
    revenue = source_price * quantity

    # Profit
    gross_profit = revenue - total_cost_target

    # Margin
    profit_margin = (gross_profit / revenue * 100) if revenue > 0 else 0

    # ROI
    roi = (gross_profit / total_cost_target * 100) if total_cost_target > 0 else 0

    # Break-even quantity
    unit_cost_target = (supplier_price + shipping_per_unit) * exchange_rate_reverse
    break_even = int(total_cost_target / source_price) + 1 if source_price > unit_cost_target else 0

    return {
        "source_price": source_price,
        "source_currency": source_currency,
        "supplier_price_cny": supplier_price,
        "purchase_cost_cny": purchase_cost_cny,
        "shipping_cost_cny": shipping_cost_cny,
        "total_cost_cny": total_cost_cny,
        "total_cost_target_currency": round(total_cost_target, 2),
        "exchange_rate": exchange_rate,
        "gross_profit": round(gross_profit, 2),
        "profit_margin": round(profit_margin, 2),
        "roi": round(roi, 2),
        "break_even_quantity": break_even,
        "notes": [
            f"Exchange rate: 1 {source_currency} = {exchange_rate} CNY",
            f"Shipping cost estimate: {shipping_per_unit} CNY/unit",
            "Platform fees not included (~15%)",
            "Actual costs may vary",
        ]
    }


# ============ Scraper Class ============

class Alibaba1688Scraper:
    """Scraper for 1688.com (Alibaba China)."""

    BASE_URL = "https://s.1688.com"
    DETAIL_URL = "https://detail.1688.com"

    def __init__(self):
        self._browser = None
        self._playwright = None
        self._request_count = 0
        self._max_requests_per_session = 50

    async def _get_browser(self):
        """Get or create browser instance."""
        if not PLAYWRIGHT_AVAILABLE:
            return None

        if self._browser is None or self._request_count >= self._max_requests_per_session:
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
            try:
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-blink-features=AutomationControlled",
                    ],
                )
                self._request_count = 0
            except Exception as e:
                # Browser binary not found or launch failed
                print(f"Failed to launch browser: {e}")
                print("Playwright browsers may not be installed. Run: playwright install chromium")
                self._playwright = None
                self._browser = None
                return None
        return self._browser

    async def close(self):
        """Close browser."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def search_suppliers(
        self,
        keyword: str,
        max_price: float = 500,
        limit: int = 20,
        source_price: float = 0,
        source_currency: str = "AUD",
    ) -> List[Supplier1688]:
        """
        Search suppliers on 1688.

        Args:
            keyword: Chinese search keyword
            max_price: Maximum price in CNY
            limit: Number of results to return
            source_price: Source product price for scoring
            source_currency: Source currency

        Returns:
            List of supplier data
        """
        # Check if Playwright is available
        if not PLAYWRIGHT_AVAILABLE:
            print("Playwright not available - scraping disabled. Returning empty results.")
            return []

        browser = await self._get_browser()
        if browser is None:
            return []

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
        )

        # Add cookies from config if available
        if settings.alibaba_1688_cookies:
            try:
                cookies = json.loads(settings.alibaba_1688_cookies)
                formatted_cookies = []
                for cookie in cookies:
                    formatted_cookie = {
                        "name": cookie.get("name", ""),
                        "value": cookie.get("value", ""),
                        "domain": cookie.get("domain", ".1688.com"),
                        "path": cookie.get("path", "/"),
                    }
                    if cookie.get("expires"):
                        formatted_cookie["expires"] = cookie["expires"]
                    if cookie.get("httpOnly") is not None:
                        formatted_cookie["httpOnly"] = cookie["httpOnly"]
                    if cookie.get("secure") is not None:
                        formatted_cookie["secure"] = cookie["secure"]
                    formatted_cookies.append(formatted_cookie)
                await context.add_cookies(formatted_cookies)
                print(f"[1688] Added {len(formatted_cookies)} cookies from config")
            except json.JSONDecodeError as e:
                print(f"[1688] Warning: Failed to parse cookies JSON: {e}")
            except Exception as e:
                print(f"[1688] Warning: Failed to add cookies: {e}")

        page = await context.new_page()

        # Apply stealth to bypass bot detection
        if STEALTH_AVAILABLE and stealth_async:
            await stealth_async(page)
            print("[1688] Stealth mode applied")

        try:
            # Build search URL with price filter
            search_url = f"{self.BASE_URL}/selloffer/offer_search.htm"
            params = {
                "keywords": keyword,
                "n": "y",
                "spm": "a26352.13672862.searchbox.input",
            }

            # Add price filter
            if max_price > 0:
                params["e_price"] = str(int(max_price))

            url = f"{search_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

            # Navigate with retry
            for attempt in range(3):
                try:
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    break
                except Exception as e:
                    if attempt == 2:
                        raise
                    await asyncio.sleep(2)

            self._request_count += 1

            # Wait for content
            await asyncio.sleep(2)

            # Debug: Log current URL and page title
            current_url = page.url
            page_title = await page.title()
            print(f"[1688] Current URL: {current_url}")
            print(f"[1688] Page title: {page_title}")

            # Check if redirected to login
            if "login" in current_url.lower() or "passport" in current_url.lower():
                print("[1688] Warning: Redirected to login page - cookies may have expired")
                return []

            # Extract suppliers
            suppliers = await self._extract_suppliers(page, limit, source_price, source_currency)
            print(f"[1688] Extracted {len(suppliers)} suppliers")

            # Filter by price
            suppliers = [s for s in suppliers if filter_by_price(s, max_price)]

            # Filter by size
            suppliers = [s for s in suppliers if filter_by_size(s)]

            # Sort by score
            suppliers.sort(key=lambda x: x.match_score or 0, reverse=True)

            return suppliers[:limit]

        except Exception as e:
            print(f"1688 scraping error: {e}")
            return []
        finally:
            await page.close()
            await context.close()

    async def _extract_suppliers(
        self,
        page: Page,
        limit: int,
        source_price: float,
        source_currency: str,
    ) -> List[Supplier1688]:
        """Extract supplier data from search results page."""
        suppliers = []

        # Try different selectors for 1688 search results (updated 2026)
        # Focus on main search results area, exclude similar/recommended sections
        selectors = [
            # Main search result containers - more specific selectors first
            ".sm-offer-list .sm-offer-item",  # Standard offer list
            ".offer-list .offer-list-row",  # Offer list rows
            "#sm-offer-list .search-offer-item",  # ID-based selector
            ".app-offer-list .space-offer-card-box",  # App offer list
            # Fallback to broader selectors
            ".sm-offer-item",
            ".offer-list-row",
            ".search-offer-item:not([class*='similar']):not([class*='recommend'])",
            "[data-offer-id]",  # Elements with offer ID attribute
        ]

        items = []
        used_selector = None
        for selector in selectors:
            try:
                found_items = await page.query_selector_all(selector)
                print(f"[1688] Selector '{selector}': found {len(found_items)} items")
                if found_items and len(found_items) >= 1:
                    # Check if any item has a valid product link
                    for test_item in found_items[:3]:
                        # Look for any link with numeric offer ID
                        all_links = await test_item.query_selector_all("a[href*='1688.com']")
                        for link in all_links:
                            href = await link.get_attribute("href") or ""
                            if "detail.1688.com/offer" in href and "similar_search" not in href:
                                items = found_items
                                used_selector = selector
                                print(f"[1688] Using selector '{selector}' with valid product links")
                                break
                        if items:
                            break
                    if items:
                        break
            except Exception as e:
                print(f"[1688] Selector '{selector}' error: {e}")
                continue

        # If no valid selector found, try fallback with first available items
        if not items:
            print("[1688] No valid selector found, trying fallback extraction")
            for selector in selectors:
                try:
                    items = await page.query_selector_all(selector)
                    if items:
                        used_selector = selector
                        print(f"[1688] Fallback: using '{selector}' with {len(items)} items")
                        break
                except:
                    continue

        if not items:
            # Log page content sample for debugging
            body_text = await page.evaluate("() => document.body ? document.body.innerText.slice(0, 500) : 'No body'")
            print(f"[1688] No items found. Page content sample: {body_text[:200]}...")
            # Try to extract from page content directly
            return await self._extract_from_json(page, limit, source_price, source_currency)

        for item in items[:limit * 2]:  # Get extra for filtering
            try:
                supplier = await self._parse_supplier_item(item, source_price, source_currency)
                if supplier:
                    suppliers.append(supplier)
            except Exception as e:
                print(f"Error parsing supplier item: {e}")
                continue

        return suppliers

    async def _extract_from_json(
        self,
        page: Page,
        limit: int,
        source_price: float,
        source_currency: str,
    ) -> List[Supplier1688]:
        """Try to extract data from page's JSON data."""
        suppliers = []

        try:
            # Try to get data from page scripts
            script_content = await page.evaluate("""
                () => {
                    const scripts = document.querySelectorAll('script');
                    for (const script of scripts) {
                        if (script.textContent && script.textContent.includes('offerList')) {
                            return script.textContent;
                        }
                    }
                    return null;
                }
            """)

            if script_content:
                # Parse JSON from script
                match = re.search(r'"offerList"\s*:\s*(\[.*?\])', script_content, re.DOTALL)
                if match:
                    import json
                    offers = json.loads(match.group(1))
                    for offer in offers[:limit]:
                        supplier = self._parse_json_offer(offer, source_price, source_currency)
                        if supplier:
                            suppliers.append(supplier)

        except Exception as e:
            print(f"Error extracting JSON data: {e}")

        return suppliers

    async def _parse_supplier_item(
        self,
        item,
        source_price: float,
        source_currency: str,
    ) -> Optional[Supplier1688]:
        """Parse a single supplier item from DOM."""
        try:
            # Extract title (updated selectors for 2026)
            title_elem = await item.query_selector(".title-text, .title, .offer-title, h2 a, [class*='title'] a")
            title = await title_elem.inner_text() if title_elem else ""
            title = title.strip()

            if not title:
                return None

            # Extract price (updated selectors for 2026)
            price_elem = await item.query_selector("[class*='price'], .price, .offer-price")
            price_text = await price_elem.inner_text() if price_elem else "0"
            price = self._parse_price(price_text)

            # Extract URL and offer_id (updated selectors for 2026)
            # Prioritize links to actual product detail pages
            link_elem = await item.query_selector("a[href*='detail.1688.com/offer']")
            if not link_elem:
                link_elem = await item.query_selector("a[href*='/offer/'][href*='.html']")
            if not link_elem:
                link_elem = await item.query_selector("a[href*='1688.com']")

            url = await link_elem.get_attribute("href") if link_elem else ""

            # Skip items with similar_search or recommend URLs (not real products)
            if "similar_search" in url or "recommend" in url:
                print(f"[1688] Skipping non-product URL: {url[:80]}...")
                return None

            if url and not url.startswith("http"):
                url = f"https:{url}" if url.startswith("//") else f"https://detail.1688.com{url}"

            offer_id = self._extract_offer_id(url)

            # Validate offer_id - should be numeric or a valid product identifier
            if not offer_id:
                print(f"[1688] No offer_id found in URL: {url[:80]}")
                return None

            # If offer_id looks like a path/query, try to extract numeric ID
            if not offer_id.isdigit():
                numeric_match = re.search(r'(\d{10,})', url)
                if numeric_match:
                    offer_id = numeric_match.group(1)
                else:
                    print(f"[1688] Non-numeric offer_id, URL: {url[:80]}")
                    return None

            # Extract image
            img_elem = await item.query_selector("img")
            image_url = await img_elem.get_attribute("src") if img_elem else None
            if image_url and not image_url.startswith("http"):
                image_url = f"https:{image_url}"

            # Extract sold count
            sold_elem = await item.query_selector("[class*='sold'], [class*='deal'], .trade-quantity")
            sold_text = await sold_elem.inner_text() if sold_elem else "0"
            sold_count = self._parse_sold_count(sold_text)

            # Extract supplier name
            supplier_elem = await item.query_selector(".company-name, .seller-name, [class*='company'] a")
            supplier_name = await supplier_elem.inner_text() if supplier_elem else "Unknown"

            # Extract location
            location_elem = await item.query_selector(".location, .address, [class*='location']")
            location = await location_elem.inner_text() if location_elem else None

            # Check if verified
            verified_elem = await item.query_selector(".tp-icon, [class*='verified'], [class*='trust']")
            is_verified = verified_elem is not None

            # Create supplier object
            supplier = Supplier1688(
                offer_id=offer_id,
                title=title,
                price=price,
                moq=1,  # Default, would need detail page for actual value
                sold_count=sold_count,
                image_url=image_url,
                product_url=url,
                supplier_name=supplier_name.strip(),
                is_verified=is_verified,
                location=location.strip() if location else None,
                is_small_medium=True,  # Assume true, filter later if needed
            )

            # Calculate score
            if source_price > 0:
                supplier.match_score = calculate_supplier_score(
                    supplier, source_price, source_currency
                )

            return supplier

        except Exception as e:
            print(f"Error parsing supplier: {e}")
            return None

    def _parse_json_offer(
        self,
        offer: dict,
        source_price: float,
        source_currency: str,
    ) -> Optional[Supplier1688]:
        """Parse supplier from JSON offer data."""
        try:
            supplier = Supplier1688(
                offer_id=str(offer.get("offerId", offer.get("id", ""))),
                title=offer.get("subject", offer.get("title", "")),
                price=float(offer.get("price", offer.get("priceInfo", {}).get("price", 0))),
                moq=int(offer.get("quantityBegin", 1)),
                sold_count=int(offer.get("gmvReTrade30Day", offer.get("soldCount", 0))),
                image_url=offer.get("imageUrl", offer.get("image", {}).get("url")),
                product_url=f"https://detail.1688.com/offer/{offer.get('offerId', offer.get('id', ''))}.html",
                supplier_name=offer.get("companyName", offer.get("company", {}).get("name", "Unknown")),
                supplier_years=offer.get("tpYear"),
                is_verified=offer.get("isTp", False),
                location=offer.get("location"),
                is_small_medium=True,
            )

            if source_price > 0:
                supplier.match_score = calculate_supplier_score(
                    supplier, source_price, source_currency
                )

            return supplier

        except Exception as e:
            print(f"Error parsing JSON offer: {e}")
            return None

    def _parse_price(self, price_text: str) -> float:
        """Parse price from text."""
        # Remove currency symbols and extract numbers
        price_text = re.sub(r"[^\d.]", "", price_text)
        try:
            return float(price_text) if price_text else 0
        except ValueError:
            return 0

    def _parse_sold_count(self, sold_text: str) -> int:
        """Parse sold count from text."""
        # Handle formats like "1000+", "5万+", "1.2万"
        sold_text = sold_text.strip()

        if "万" in sold_text:
            # Chinese "wan" = 10000
            num = re.search(r"([\d.]+)", sold_text)
            if num:
                return int(float(num.group(1)) * 10000)

        num = re.search(r"(\d+)", sold_text)
        return int(num.group(1)) if num else 0

    def _extract_offer_id(self, url: str) -> str:
        """Extract offer ID from URL."""
        match = re.search(r"/offer/(\d+)", url)
        if match:
            return match.group(1)
        match = re.search(r"offerId[=:](\d+)", url)
        if match:
            return match.group(1)
        return url.split("/")[-1].replace(".html", "")

    async def get_product_details(self, offer_id: str) -> Optional[dict]:
        """
        Get detailed product information.

        Args:
            offer_id: 1688 offer ID

        Returns:
            Product details dict
        """
        # Check if Playwright is available
        if not PLAYWRIGHT_AVAILABLE:
            print("Playwright not available - returning None for product details.")
            return None

        browser = await self._get_browser()
        if browser is None:
            return None

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
        )
        page = await context.new_page()

        # Apply stealth to bypass bot detection
        if STEALTH_AVAILABLE and stealth_async:
            await stealth_async(page)

        try:
            url = f"{self.DETAIL_URL}/offer/{offer_id}.html"
            await page.goto(url, wait_until="networkidle", timeout=30000)
            self._request_count += 1

            await asyncio.sleep(2)

            # Extract detailed information
            details = {
                "offer_id": offer_id,
                "url": url,
            }

            # Title
            title_elem = await page.query_selector("h1, .mod-detail-title")
            if title_elem:
                details["title"] = await title_elem.inner_text()

            # Price tiers
            price_tiers = []
            tier_elems = await page.query_selector_all(".price-tier, .ladder-price-item")
            for tier in tier_elems:
                tier_text = await tier.inner_text()
                price_tiers.append(tier_text)
            details["price_tiers"] = price_tiers

            # MOQ
            moq_elem = await page.query_selector("[class*='min-order'], .unit-price")
            if moq_elem:
                moq_text = await moq_elem.inner_text()
                moq_match = re.search(r"(\d+)", moq_text)
                details["moq"] = int(moq_match.group(1)) if moq_match else 1

            # Specifications
            specs = {}
            spec_rows = await page.query_selector_all(".obj-content tr, .attribute-item")
            for row in spec_rows:
                try:
                    cells = await row.query_selector_all("td, span")
                    if len(cells) >= 2:
                        key = await cells[0].inner_text()
                        value = await cells[1].inner_text()
                        specs[key.strip()] = value.strip()
                except:
                    pass
            details["specifications"] = specs

            # Images
            images = []
            img_elems = await page.query_selector_all(".detail-gallery img, .detail-pictures img")
            for img in img_elems[:10]:
                src = await img.get_attribute("src")
                if src:
                    images.append(src if src.startswith("http") else f"https:{src}")
            details["images"] = images

            # Weight (try to extract from specs)
            weight_patterns = ["重量", "weight", "净重"]
            for key, value in specs.items():
                if any(p in key.lower() for p in weight_patterns):
                    weight_match = re.search(r"([\d.]+)\s*(?:kg|g|千克|克)", value.lower())
                    if weight_match:
                        weight = float(weight_match.group(1))
                        if "g" in value.lower() or "克" in value:
                            weight /= 1000
                        details["weight"] = weight
                        break

            # Dimensions
            dim_patterns = ["尺寸", "size", "dimension", "规格"]
            for key, value in specs.items():
                if any(p in key.lower() for p in dim_patterns):
                    details["dimensions"] = value
                    break

            return details

        except Exception as e:
            print(f"Error getting product details: {e}")
            return None
        finally:
            await page.close()
            await context.close()


# ============ Service Functions ============

async def match_suppliers_for_products(
    products: List[dict],
    max_price: float = 500,
    limit_per_product: int = 10,
    include_large: bool = False,
) -> List[dict]:
    """
    Match 1688 suppliers for multiple AU/NZ products.

    Args:
        products: List of source products with title, price, currency
        max_price: Max supplier price in CNY
        limit_per_product: Number of suppliers per product
        include_large: Include large items

    Returns:
        List of match results
    """
    scraper = Alibaba1688Scraper()
    results = []

    try:
        for product in products:
            # Extract keywords
            keywords = extract_keywords(product.get("title", ""))
            chinese_keywords = translate_to_chinese(keywords)

            all_suppliers = []

            # Search with each keyword
            for keyword in chinese_keywords[:2]:  # Try top 2 keywords
                suppliers = await scraper.search_suppliers(
                    keyword=keyword,
                    max_price=max_price,
                    limit=limit_per_product * 2,
                    source_price=float(product.get("price", 0)),
                    source_currency=product.get("currency", "AUD"),
                )
                all_suppliers.extend(suppliers)

                # Small delay between requests
                await asyncio.sleep(1)

            # Deduplicate by offer_id
            seen_ids = set()
            unique_suppliers = []
            for s in all_suppliers:
                if s.offer_id not in seen_ids:
                    seen_ids.add(s.offer_id)
                    unique_suppliers.append(s)

            # Filter by size if needed
            if not include_large:
                unique_suppliers = [s for s in unique_suppliers if filter_by_size(s)]

            # Sort by score and take top N
            unique_suppliers.sort(key=lambda x: x.match_score or 0, reverse=True)
            top_suppliers = unique_suppliers[:limit_per_product]

            results.append({
                "source_product_id": product.get("id"),
                "source_product_title": product.get("title"),
                "search_keywords": chinese_keywords,
                "matched_suppliers": [s.model_dump() for s in top_suppliers],
                "match_count": len(top_suppliers),
            })

    finally:
        await scraper.close()

    return results
