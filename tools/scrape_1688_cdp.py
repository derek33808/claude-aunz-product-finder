#!/usr/bin/env python3
"""
1688 爬虫 - 连接已打开的 Chrome 浏览器

使用方法:
1. 先关闭所有 Chrome 窗口
2. 用调试模式启动 Chrome:
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
3. 在 Chrome 中登录 1688，然后打开搜索页面
4. 运行此脚本:
   python tools/scrape_1688_cdp.py

脚本会连接到你已打开的 Chrome，提取当前页面的产品数据。
"""

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("请安装 playwright: pip install playwright")
    sys.exit(1)

try:
    from supabase import create_client
except ImportError:
    create_client = None

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / "backend" / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


class ChromeCDPScraper:
    """连接已打开的 Chrome 浏览器进行爬取"""

    def __init__(self, cdp_url: str = "http://localhost:9222"):
        self.cdp_url = cdp_url
        self.supabase = None
        self._init_supabase()

    def _init_supabase(self):
        """初始化 Supabase"""
        if not create_client:
            return
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
        if url and key:
            try:
                self.supabase = create_client(url, key)
                print(f"✓ Supabase 已连接")
            except Exception as e:
                print(f"Supabase 连接失败: {e}")

    async def scrape_current_page(self, keyword: str = None) -> List[dict]:
        """从当前打开的 1688 页面提取数据"""
        print(f"\n🔗 连接到 Chrome: {self.cdp_url}")

        async with async_playwright() as p:
            try:
                browser = await p.chromium.connect_over_cdp(self.cdp_url)
                print("✓ 已连接到 Chrome")
            except Exception as e:
                print(f"\n❌ 无法连接到 Chrome: {e}")
                print("\n请按以下步骤操作:")
                print("1. 关闭所有 Chrome 窗口")
                print("2. 运行: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
                print("3. 在 Chrome 中打开 1688 搜索页面")
                print("4. 重新运行此脚本")
                return []

            contexts = browser.contexts
            if not contexts:
                print("❌ 没有找到浏览器上下文")
                return []

            # 获取第一个上下文中的页面
            pages = contexts[0].pages
            target_page = None

            for page in pages:
                url = page.url
                if "1688.com" in url:
                    target_page = page
                    print(f"✓ 找到 1688 页面: {url[:60]}...")
                    break

            if not target_page:
                print("❌ 没有找到打开的 1688 页面")
                print("   请在 Chrome 中打开 1688 搜索结果页面")
                return []

            # 获取页面标题
            title = await target_page.title()
            print(f"   页面标题: {title}")

            # 从 URL 提取关键词
            if not keyword:
                url = target_page.url
                match = re.search(r'keywords=([^&]+)', url)
                if match:
                    from urllib.parse import unquote
                    keyword = unquote(match.group(1))
                    print(f"   搜索关键词: {keyword}")

            # 提取产品
            products = await self._extract_products(target_page, keyword)
            print(f"\n✓ 提取到 {len(products)} 个产品")

            # 保存到数据库
            if products and self.supabase and keyword:
                await self._save_to_database(products, keyword)

            return products

    async def _extract_products(self, page, keyword: str) -> List[dict]:
        """提取产品数据"""
        products = []

        # 尝试不同选择器
        selectors = [
            ".search-offer-item",
            ".sm-offer-item",
            ".offer-list-row",
            "[data-offer-id]",
        ]

        items = []
        for selector in selectors:
            items = await page.query_selector_all(selector)
            if items:
                print(f"   使用选择器: {selector} (找到 {len(items)} 个)")
                break

        if not items:
            print("   ⚠️ 未找到产品元素")
            return []

        for i, item in enumerate(items[:50]):  # 最多 50 个
            try:
                product = await self._parse_item(item, keyword)
                if product:
                    products.append(product)
                    if i < 5:  # 只显示前 5 个
                        print(f"   [{i+1}] {product['title'][:30]}... ¥{product['price']}")
            except Exception as e:
                pass

        if len(products) > 5:
            print(f"   ... 还有 {len(products) - 5} 个产品")

        return products

    async def _parse_item(self, item, keyword: str) -> Optional[dict]:
        """解析单个产品"""
        # 标题
        title_elem = await item.query_selector(".title-text, .title, .offer-title, h2 a, [class*='title'] a")
        title = await title_elem.inner_text() if title_elem else ""
        title = title.strip()
        if not title:
            return None

        # 价格
        price_elem = await item.query_selector("[class*='price'], .price, .offer-price")
        price_text = await price_elem.inner_text() if price_elem else "0"
        price = self._parse_price(price_text)

        # 链接
        link_elem = await item.query_selector("a[href*='detail.1688.com'], a[href*='/offer/']")
        url = await link_elem.get_attribute("href") if link_elem else ""
        if url and not url.startswith("http"):
            url = f"https:{url}" if url.startswith("//") else f"https://detail.1688.com{url}"

        # 跳过非产品链接
        if "similar_search" in url:
            return None

        offer_id = self._extract_offer_id(url)
        if not offer_id:
            return None

        # 图片
        img_elem = await item.query_selector("img")
        image_url = await img_elem.get_attribute("src") if img_elem else None
        if image_url and not image_url.startswith("http"):
            image_url = f"https:{image_url}"

        # 销量
        sold_elem = await item.query_selector("[class*='sold'], [class*='deal'], .trade-quantity")
        sold_text = await sold_elem.inner_text() if sold_elem else "0"
        sold_count = self._parse_sold_count(sold_text)

        # 供应商
        supplier_elem = await item.query_selector(".company-name, .seller-name, [class*='company'] a")
        supplier_name = await supplier_elem.inner_text() if supplier_elem else "Unknown"

        # 位置
        location_elem = await item.query_selector(".location, .address, [class*='location']")
        location = await location_elem.inner_text() if location_elem else None

        return {
            "offer_id": offer_id,
            "title": title,
            "price": price,
            "product_url": url,
            "image_url": image_url,
            "sold_count": sold_count,
            "supplier_name": supplier_name.strip(),
            "location": location.strip() if location else None,
            "search_keyword": keyword,
            "scraped_at": datetime.now().isoformat(),
        }

    def _parse_price(self, text: str) -> float:
        text = re.sub(r"[^\d.]", "", text)
        try:
            return float(text) if text else 0
        except ValueError:
            return 0

    def _parse_sold_count(self, text: str) -> int:
        text = text.strip()
        if "万" in text:
            num = re.search(r"([\d.]+)", text)
            if num:
                return int(float(num.group(1)) * 10000)
        num = re.search(r"(\d+)", text)
        return int(num.group(1)) if num else 0

    def _extract_offer_id(self, url: str) -> str:
        match = re.search(r"/offer/(\d+)", url)
        if match:
            return match.group(1)
        match = re.search(r"(\d{10,})", url)
        if match:
            return match.group(1)
        return ""

    async def _save_to_database(self, products: List[dict], keyword: str):
        """保存到数据库"""
        if not self.supabase:
            return

        print(f"\n💾 保存到数据库...")
        saved = 0
        for product in products:
            try:
                self.supabase.table("suppliers_1688").upsert(
                    product,
                    on_conflict="offer_id"
                ).execute()
                saved += 1
            except Exception as e:
                print(f"   保存失败: {e}")

        print(f"✓ 已保存 {saved} 条记录")


async def main():
    parser = argparse.ArgumentParser(description="从已打开的 Chrome 提取 1688 数据")
    parser.add_argument("--keyword", help="搜索关键词（可选，会自动从 URL 提取）")
    parser.add_argument("--port", type=int, default=9222, help="Chrome 调试端口 (默认: 9222)")
    parser.add_argument("--output", help="输出 JSON 文件路径")

    args = parser.parse_args()

    scraper = ChromeCDPScraper(cdp_url=f"http://localhost:{args.port}")
    products = await scraper.scrape_current_page(keyword=args.keyword)

    if args.output and products:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        print(f"\n📁 已保存到: {args.output}")

    if products:
        print(f"\n{'='*50}")
        print(f"总计: {len(products)} 个产品")
        if products:
            prices = [p['price'] for p in products if p['price'] > 0]
            if prices:
                print(f"价格范围: ¥{min(prices):.2f} - ¥{max(prices):.2f}")
        print(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(main())
