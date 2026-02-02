#!/usr/bin/env python3
"""
1688 本地爬虫脚本

使用方法:
1. 确保已安装依赖: pip install playwright supabase python-dotenv
2. 安装浏览器: playwright install chromium
3. 在 .env 文件中配置 SUPABASE_URL 和 SUPABASE_SERVICE_KEY
4. 运行: python scripts/scrape_1688.py

这个脚本会:
1. 打开浏览器让你手动登录 1688
2. 登录后按回车继续
3. 爬取预定义的关键词列表
4. 将结果保存到 Supabase 数据库
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, Browser

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("错误: 请在 .env 文件中配置 SUPABASE_URL 和 SUPABASE_SERVICE_KEY")
    sys.exit(1)

# 要爬取的关键词列表 (中文)
KEYWORDS_TO_SCRAPE = [
    # 电子产品
    "无线耳机",
    "蓝牙耳机",
    "手机壳",
    "手机支架",
    "充电宝",
    "数据线",
    "智能手表",

    # 家居用品
    "收纳盒",
    "LED灯",
    "保温杯",

    # 时尚配饰
    "太阳镜",
    "背包",
    "钱包",

    # 运动健身
    "瑜伽垫",
    "运动手环",

    # 宠物用品
    "宠物玩具",
    "宠物碗",
]

# 每个关键词爬取的产品数量
PRODUCTS_PER_KEYWORD = 30


class Alibaba1688Scraper:
    """1688 爬虫类"""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def start(self, headless: bool = False):
        """启动浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )

        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
        )

        self.page = await context.new_page()
        return self

    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()

    async def manual_login(self):
        """让用户手动登录"""
        print("\n" + "=" * 50)
        print("请在浏览器中登录 1688 账号")
        print("=" * 50)

        # 导航到登录页面
        await self.page.goto("https://www.1688.com")
        await asyncio.sleep(2)

        # 等待用户登录
        input("\n登录完成后，按回车键继续...")

        # 验证登录状态
        await self.page.goto("https://www.1688.com")
        await asyncio.sleep(2)

        # 检查是否登录成功
        content = await self.page.content()
        if "登录" in content and "我的阿里" not in content:
            print("警告: 可能未成功登录，继续尝试...")

        print("继续爬取...")

    async def search_products(self, keyword: str, limit: int = 30) -> List[Dict[str, Any]]:
        """搜索产品"""
        print(f"\n正在搜索: {keyword}")

        url = f"https://s.1688.com/selloffer/offer_search.htm?keywords={keyword}"
        await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(3)

        # 检查是否被重定向到登录页
        current_url = self.page.url
        if "login" in current_url.lower():
            print(f"警告: 被重定向到登录页面，跳过关键词: {keyword}")
            return []

        products = []

        # 滚动加载更多产品
        for scroll in range(3):
            await self.page.evaluate("window.scrollBy(0, 1000)")
            await asyncio.sleep(1)

        # 尝试不同的选择器
        selectors = [
            "div[class*='offer-item']",
            "div[class*='offeritem']",
            ".space-offer-card-box",
            "[data-tracklog]",
            "a[href*='detail.1688.com']",
        ]

        items = []
        for selector in selectors:
            try:
                items = await self.page.query_selector_all(selector)
                if items and len(items) > 0:
                    print(f"  使用选择器: {selector}, 找到 {len(items)} 个项目")
                    break
            except:
                continue

        if not items:
            print(f"  未找到任何产品")
            return []

        for item in items[:limit]:
            try:
                product = await self._parse_item(item, keyword)
                if product:
                    products.append(product)
            except Exception as e:
                print(f"  解析产品时出错: {e}")
                continue

        print(f"  成功解析 {len(products)} 个产品")
        return products

    async def _parse_item(self, item, keyword: str) -> Optional[Dict[str, Any]]:
        """解析单个产品"""
        try:
            # 标题
            title_elem = await item.query_selector("a[title], .title a, h2 a")
            title = ""
            if title_elem:
                title = await title_elem.get_attribute("title") or await title_elem.inner_text()
            title = title.strip() if title else ""

            if not title:
                return None

            # 链接和 offer_id
            link_elem = await item.query_selector("a[href*='detail.1688.com'], a[href*='offer']")
            url = ""
            if link_elem:
                url = await link_elem.get_attribute("href") or ""
                if url and not url.startswith("http"):
                    url = f"https:{url}" if url.startswith("//") else f"https://detail.1688.com{url}"

            offer_id = self._extract_offer_id(url)
            if not offer_id:
                return None

            # 价格
            price_elem = await item.query_selector("[class*='price'] em, .price em, .sm-offer-price")
            price_text = await price_elem.inner_text() if price_elem else "0"
            price = self._parse_price(price_text)

            # 图片
            img_elem = await item.query_selector("img")
            image_url = await img_elem.get_attribute("src") if img_elem else None
            if image_url and not image_url.startswith("http"):
                image_url = f"https:{image_url}"

            # 销量
            sold_elem = await item.query_selector("[class*='sold'], [class*='deal']")
            sold_text = await sold_elem.inner_text() if sold_elem else "0"
            sold_count = self._parse_sold_count(sold_text)

            # 供应商名称
            supplier_elem = await item.query_selector("[class*='company'] a, .seller-name")
            supplier_name = await supplier_elem.inner_text() if supplier_elem else "未知供应商"

            # 地区
            location_elem = await item.query_selector("[class*='location'], .address")
            location = await location_elem.inner_text() if location_elem else None

            return {
                "offer_id": offer_id,
                "title": title,
                "price": price,
                "product_url": url,
                "image_url": image_url,
                "sold_count": sold_count,
                "supplier_name": supplier_name.strip() if supplier_name else "未知供应商",
                "location": location.strip() if location else None,
                "search_keyword": keyword,
                "moq": 1,
                "is_verified": False,
                "is_small_medium": True,
                "scraped_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return None

    def _extract_offer_id(self, url: str) -> str:
        """从 URL 提取 offer_id"""
        import re
        match = re.search(r"/offer/(\d+)", url)
        if match:
            return match.group(1)
        match = re.search(r"offerId[=:](\d+)", url)
        if match:
            return match.group(1)
        return ""

    def _parse_price(self, price_text: str) -> float:
        """解析价格"""
        import re
        price_text = re.sub(r"[^\d.]", "", price_text)
        try:
            return float(price_text) if price_text else 0
        except:
            return 0

    def _parse_sold_count(self, sold_text: str) -> int:
        """解析销量"""
        import re
        if "万" in sold_text:
            num = re.search(r"([\d.]+)", sold_text)
            if num:
                return int(float(num.group(1)) * 10000)
        num = re.search(r"(\d+)", sold_text)
        return int(num.group(1)) if num else 0


async def save_to_supabase(products: List[Dict[str, Any]]):
    """保存产品到 Supabase"""
    from supabase import create_client

    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    saved_count = 0
    updated_count = 0

    for product in products:
        try:
            # 使用 upsert (如果存在则更新，不存在则插入)
            result = supabase.table("suppliers_1688").upsert(
                product,
                on_conflict="offer_id"
            ).execute()

            if result.data:
                saved_count += 1

        except Exception as e:
            print(f"保存产品 {product.get('offer_id')} 时出错: {e}")

    print(f"保存完成: {saved_count} 条记录")
    return saved_count


async def main():
    """主函数"""
    print("=" * 50)
    print("1688 爬虫脚本")
    print("=" * 50)

    scraper = Alibaba1688Scraper()

    try:
        # 启动浏览器 (非无头模式，方便登录)
        await scraper.start(headless=False)

        # 手动登录
        await scraper.manual_login()

        # 爬取所有关键词
        all_products = []

        for keyword in KEYWORDS_TO_SCRAPE:
            try:
                products = await scraper.search_products(keyword, PRODUCTS_PER_KEYWORD)
                all_products.extend(products)

                # 请求间隔，避免被封
                await asyncio.sleep(3)

            except Exception as e:
                print(f"爬取关键词 '{keyword}' 时出错: {e}")
                continue

        print(f"\n共爬取 {len(all_products)} 个产品")

        # 保存到 Supabase
        if all_products:
            print("\n正在保存到数据库...")
            await save_to_supabase(all_products)

        print("\n爬取完成!")

    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
