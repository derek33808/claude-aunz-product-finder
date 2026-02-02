#!/usr/bin/env python3
"""
本地 1688 爬虫脚本

使用方法:
1. 确保已安装依赖: pip install playwright supabase python-dotenv
2. 确保已安装浏览器: playwright install chromium
3. 运行: python tools/scrape_1688.py "蓝牙耳机" --limit 20

脚本会打开浏览器窗口，使用你已登录的 Chrome profile 爬取 1688 搜索结果，
然后将数据存入 Supabase 数据库供云端 API 使用。
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

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("请安装 playwright: pip install playwright && playwright install chromium")
    sys.exit(1)

try:
    from supabase import create_client
except ImportError:
    print("请安装 supabase: pip install supabase")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("请安装 python-dotenv: pip install python-dotenv")
    sys.exit(1)


# 加载环境变量
env_path = Path(__file__).parent.parent / "backend" / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # 尝试项目根目录
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)


class Local1688Scraper:
    """本地 1688 爬虫，使用用户已登录的浏览器"""

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.supabase = None
        self._init_supabase()

    def _init_supabase(self):
        """初始化 Supabase 客户端"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")

        if not url or not key:
            print("警告: 未配置 Supabase，数据将只输出到控制台")
            print("请在 .env 文件中配置 SUPABASE_URL 和 SUPABASE_KEY")
            return

        try:
            self.supabase = create_client(url, key)
            print(f"✓ Supabase 已连接: {url[:30]}...")
        except Exception as e:
            print(f"Supabase 连接失败: {e}")

    async def scrape(
        self,
        keyword: str,
        max_price: float = 500,
        limit: int = 20,
    ) -> List[dict]:
        """
        爬取 1688 搜索结果

        Args:
            keyword: 中文搜索关键词
            max_price: 最高价格（人民币）
            limit: 获取数量

        Returns:
            供应商产品列表
        """
        print(f"\n🔍 搜索关键词: {keyword}")
        print(f"📦 最高价格: ¥{max_price}")
        print(f"📊 获取数量: {limit}")

        async with async_playwright() as p:
            # 使用持久化上下文（用户已登录的浏览器 profile）
            # 这样可以使用用户的登录状态
            user_data_dir = self._get_chrome_profile_path()

            print(f"\n🌐 启动浏览器...")
            if user_data_dir and Path(user_data_dir).exists():
                print(f"   使用 Chrome Profile: {user_data_dir}")
                context = await p.chromium.launch_persistent_context(
                    user_data_dir,
                    headless=self.headless,
                    viewport={"width": 1920, "height": 1080},
                    locale="zh-CN",
                )
            else:
                print("   使用新的浏览器实例（需要手动登录）")
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    locale="zh-CN",
                )

            page = await context.new_page()

            try:
                # 构建搜索 URL
                search_url = f"https://s.1688.com/selloffer/offer_search.htm?keywords={keyword}"
                if max_price > 0:
                    search_url += f"&e_price={int(max_price)}"

                print(f"\n📄 访问: {search_url}")
                await page.goto(search_url, wait_until="networkidle", timeout=60000)

                # 等待页面加载
                await asyncio.sleep(3)

                # 检查是否需要登录或验证
                page_title = await page.title()
                print(f"   页面标题: {page_title}")

                if "验证" in page_title or "登录" in page_title:
                    print("\n⚠️  检测到验证码或登录页面")
                    print("   请在浏览器中完成验证/登录，然后按 Enter 继续...")
                    input()
                    await asyncio.sleep(2)

                # 提取产品数据
                suppliers = await self._extract_products(page, limit)

                print(f"\n✓ 提取到 {len(suppliers)} 个产品")

                # 保存到数据库
                if suppliers and self.supabase:
                    await self._save_to_database(suppliers, keyword)

                return suppliers

            except Exception as e:
                print(f"\n❌ 爬取错误: {e}")
                import traceback
                traceback.print_exc()
                return []

            finally:
                await context.close()

    async def _extract_products(self, page, limit: int) -> List[dict]:
        """从页面提取产品数据"""
        products = []

        # 尝试不同的选择器
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
            print("   ⚠️ 未找到产品元素，尝试从页面 JSON 提取...")
            return await self._extract_from_json(page, limit)

        for i, item in enumerate(items[:limit]):
            try:
                product = await self._parse_item(item)
                if product:
                    products.append(product)
                    print(f"   [{i+1}] {product['title'][:30]}... ¥{product['price']}")
            except Exception as e:
                print(f"   [{i+1}] 解析失败: {e}")

        return products

    async def _parse_item(self, item) -> Optional[dict]:
        """解析单个产品元素"""
        # 提取标题
        title_elem = await item.query_selector(
            ".title-text, .title, .offer-title, h2 a, [class*='title'] a"
        )
        title = await title_elem.inner_text() if title_elem else ""
        title = title.strip()

        if not title:
            return None

        # 提取价格
        price_elem = await item.query_selector("[class*='price'], .price, .offer-price")
        price_text = await price_elem.inner_text() if price_elem else "0"
        price = self._parse_price(price_text)

        # 提取链接和 offer_id
        link_elem = await item.query_selector(
            "a[href*='detail.1688.com'], a[href*='/offer/']"
        )
        url = await link_elem.get_attribute("href") if link_elem else ""
        if url and not url.startswith("http"):
            url = f"https:{url}" if url.startswith("//") else f"https://detail.1688.com{url}"

        offer_id = self._extract_offer_id(url)

        # 跳过非产品链接
        if "similar_search" in url or not offer_id:
            return None

        # 提取图片
        img_elem = await item.query_selector("img")
        image_url = await img_elem.get_attribute("src") if img_elem else None
        if image_url and not image_url.startswith("http"):
            image_url = f"https:{image_url}"

        # 提取销量
        sold_elem = await item.query_selector("[class*='sold'], [class*='deal'], .trade-quantity")
        sold_text = await sold_elem.inner_text() if sold_elem else "0"
        sold_count = self._parse_sold_count(sold_text)

        # 提取供应商
        supplier_elem = await item.query_selector(".company-name, .seller-name, [class*='company'] a")
        supplier_name = await supplier_elem.inner_text() if supplier_elem else "Unknown"

        # 提取位置
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
            "scraped_at": datetime.now().isoformat(),
        }

    async def _extract_from_json(self, page, limit: int) -> List[dict]:
        """从页面 JSON 数据提取"""
        try:
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

            if not script_content:
                return []

            # 解析 JSON
            match = re.search(r'"offerList"\s*:\s*(\[.*?\])', script_content, re.DOTALL)
            if not match:
                return []

            offers = json.loads(match.group(1))
            products = []

            for offer in offers[:limit]:
                products.append({
                    "offer_id": str(offer.get("offerId", offer.get("id", ""))),
                    "title": offer.get("subject", offer.get("title", "")),
                    "price": float(offer.get("price", 0)),
                    "product_url": f"https://detail.1688.com/offer/{offer.get('offerId', '')}.html",
                    "image_url": offer.get("imageUrl"),
                    "sold_count": int(offer.get("gmvReTrade30Day", 0)),
                    "supplier_name": offer.get("companyName", "Unknown"),
                    "location": offer.get("location"),
                    "scraped_at": datetime.now().isoformat(),
                })

            return products

        except Exception as e:
            print(f"   JSON 提取失败: {e}")
            return []

    def _parse_price(self, price_text: str) -> float:
        """解析价格文本"""
        price_text = re.sub(r"[^\d.]", "", price_text)
        try:
            return float(price_text) if price_text else 0
        except ValueError:
            return 0

    def _parse_sold_count(self, sold_text: str) -> int:
        """解析销量文本"""
        sold_text = sold_text.strip()
        if "万" in sold_text:
            num = re.search(r"([\d.]+)", sold_text)
            if num:
                return int(float(num.group(1)) * 10000)
        num = re.search(r"(\d+)", sold_text)
        return int(num.group(1)) if num else 0

    def _extract_offer_id(self, url: str) -> str:
        """从 URL 提取 offer ID"""
        match = re.search(r"/offer/(\d+)", url)
        if match:
            return match.group(1)
        match = re.search(r"offerId[=:](\d+)", url)
        if match:
            return match.group(1)
        # 尝试提取任何长数字
        match = re.search(r"(\d{10,})", url)
        if match:
            return match.group(1)
        return ""

    def _get_chrome_profile_path(self) -> Optional[str]:
        """获取 Chrome 用户数据目录"""
        import platform

        system = platform.system()
        home = Path.home()

        if system == "Darwin":  # macOS
            return str(home / "Library/Application Support/Google/Chrome")
        elif system == "Windows":
            return str(home / "AppData/Local/Google/Chrome/User Data")
        elif system == "Linux":
            return str(home / ".config/google-chrome")

        return None

    async def _save_to_database(self, products: List[dict], keyword: str):
        """保存到 Supabase 数据库"""
        if not self.supabase:
            return

        print(f"\n💾 保存到数据库...")

        for product in products:
            try:
                # 添加搜索关键词
                product["search_keyword"] = keyword

                # Upsert（插入或更新）
                self.supabase.table("suppliers_1688").upsert(
                    product,
                    on_conflict="offer_id"
                ).execute()

            except Exception as e:
                print(f"   保存失败 [{product['offer_id']}]: {e}")

        print(f"✓ 已保存 {len(products)} 条记录")


async def main():
    parser = argparse.ArgumentParser(description="本地 1688 爬虫")
    parser.add_argument("keyword", help="搜索关键词（中文）")
    parser.add_argument("--limit", type=int, default=20, help="获取数量 (默认: 20)")
    parser.add_argument("--max-price", type=float, default=500, help="最高价格 (默认: 500)")
    parser.add_argument("--headless", action="store_true", help="无头模式运行")
    parser.add_argument("--output", help="输出 JSON 文件路径")

    args = parser.parse_args()

    scraper = Local1688Scraper(headless=args.headless)
    products = await scraper.scrape(
        keyword=args.keyword,
        max_price=args.max_price,
        limit=args.limit,
    )

    # 输出到文件
    if args.output and products:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        print(f"\n📁 已保存到: {args.output}")

    # 打印摘要
    if products:
        print(f"\n{'='*50}")
        print(f"搜索关键词: {args.keyword}")
        print(f"获取产品数: {len(products)}")
        print(f"价格范围: ¥{min(p['price'] for p in products):.2f} - ¥{max(p['price'] for p in products):.2f}")
        print(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(main())
