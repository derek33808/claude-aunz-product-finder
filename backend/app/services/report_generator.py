"""Report generation service."""

import asyncio
from typing import Optional
from datetime import datetime
from uuid import UUID
import json
from decimal import Decimal

from supabase import Client

from app.services.ebay_service import EbayService
from app.services.google_trends_service import GoogleTrendsService


class ReportGenerator:
    """Service for generating product selection reports."""
    
    def __init__(self, db: Client):
        self.db = db
        self.ebay_service = EbayService()
        self.trends_service = GoogleTrendsService()
    
    async def generate_report(
        self,
        report_id: str,
        report_type: str,
        target_type: str,
        target_value: str,
        options: dict,
    ):
        """
        Generate a complete product selection report.
        
        This method runs in the background and updates the report
        record as it progresses.
        """
        try:
            # Update status to generating
            self._update_progress(report_id, 5, "generating")
            
            # Step 1: Fetch product data (10-30%)
            product_data = await self._fetch_product_data(
                report_id, target_type, target_value
            )
            self._update_progress(report_id, 30, "generating")
            
            # Step 2: Fetch Google Trends data (30-50%)
            trends_data = await self._fetch_trends_data(
                report_id, target_type, target_value
            )
            self._update_progress(report_id, 50, "generating")
            
            # Step 3: Analyze competition (50-70%)
            competition_data = await self._analyze_competition(
                report_id, product_data
            )
            self._update_progress(report_id, 70, "generating")
            
            # Step 4: Calculate profit estimates (70-85%)
            profit_data = self._calculate_profit_estimates(product_data)
            self._update_progress(report_id, 85, "generating")
            
            # Step 5: Generate summary and recommendations
            summary = self._generate_summary(
                product_data, trends_data, competition_data, profit_data
            )
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(
                product_data, trends_data, competition_data, profit_data
            )
            
            # Step 6: Generate report files (85-95%)
            pdf_path = await self._generate_pdf(report_id, {
                "summary": summary,
                "market_analysis": product_data,
                "google_trends": trends_data,
                "competition": competition_data,
                "profit_estimate": profit_data,
            })
            
            excel_path = await self._generate_excel(report_id, product_data)
            self._update_progress(report_id, 95, "generating")
            
            # Final update
            self.db.table("reports").update({
                "status": "completed",
                "progress": 100,
                "summary": summary,
                "market_analysis": product_data,
                "google_trends": trends_data,
                "competition": competition_data,
                "profit_estimate": profit_data,
                "overall_score": overall_score,
                "pdf_path": pdf_path,
                "excel_path": excel_path,
                "updated_at": datetime.utcnow().isoformat(),
            }).eq("id", report_id).execute()
            
        except Exception as e:
            print(f"Report generation failed: {e}")
            self.db.table("reports").update({
                "status": "failed",
                "summary": {"error": str(e)},
                "updated_at": datetime.utcnow().isoformat(),
            }).eq("id", report_id).execute()
    
    def _update_progress(self, report_id: str, progress: int, status: str):
        """Update report progress in database."""
        self.db.table("reports").update({
            "progress": progress,
            "status": status,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", report_id).execute()
    
    async def _fetch_product_data(
        self,
        report_id: str,
        target_type: str,
        target_value: str,
    ) -> dict:
        """Fetch product data from platforms."""
        products = []
        
        if target_type == "keyword":
            # Search eBay AU
            try:
                ebay_au = await self.ebay_service.search_products(
                    target_value, region="AU", limit=50
                )
                products.extend(ebay_au)
            except Exception as e:
                print(f"eBay AU fetch error: {e}")
            
            # Search eBay NZ
            try:
                ebay_nz = await self.ebay_service.search_products(
                    target_value, region="NZ", limit=50
                )
                products.extend(ebay_nz)
            except Exception as e:
                print(f"eBay NZ fetch error: {e}")
        
        elif target_type == "product":
            # Get specific product
            result = self.db.table("products")\
                .select("*")\
                .eq("id", target_value)\
                .execute()
            if result.data:
                products = result.data
        
        # Calculate market statistics
        prices = [p["price"] for p in products if p.get("price")]
        
        return {
            "product_count": len(products),
            "platforms": list(set(p.get("platform", "unknown") for p in products)),
            "price_range": {
                "min": min(prices) if prices else 0,
                "max": max(prices) if prices else 0,
                "avg": sum(prices) / len(prices) if prices else 0,
            },
            "sample_products": products[:10],
        }
    
    async def _fetch_trends_data(
        self,
        report_id: str,
        target_type: str,
        target_value: str,
    ) -> dict:
        """Fetch Google Trends data."""
        keyword = target_value if target_type == "keyword" else ""
        
        if not keyword:
            return {"available": False}
        
        try:
            # Get interest over time
            interest = await self.trends_service.get_interest_over_time(
                [keyword], region="AU"
            )
            
            # Get related queries
            related = await self.trends_service.get_related_queries(keyword, region="AU")
            
            # Get NZ comparison
            nz_interest = await self.trends_service.get_interest_over_time(
                [keyword], region="NZ"
            )
            
            return {
                "available": True,
                "keyword": keyword,
                "au_interest": interest,
                "nz_interest": nz_interest,
                "related_queries": related,
            }
        except Exception as e:
            print(f"Trends fetch error: {e}")
            return {"available": False, "error": str(e)}
    
    async def _analyze_competition(
        self,
        report_id: str,
        product_data: dict,
    ) -> dict:
        """Analyze market competition."""
        products = product_data.get("sample_products", [])
        
        if not products:
            return {"level": "unknown", "analysis": "Insufficient data"}
        
        # Count sellers
        seller_count = len(set(p.get("platform_id") for p in products))
        
        # Review distribution
        reviews = [p.get("review_count", 0) for p in products]
        avg_reviews = sum(reviews) / len(reviews) if reviews else 0
        
        # Determine competition level
        if seller_count > 100:
            level = "high"
        elif seller_count > 30:
            level = "medium"
        else:
            level = "low"
        
        return {
            "level": level,
            "seller_count": seller_count,
            "avg_reviews": avg_reviews,
            "top_products": products[:5],
            "analysis": f"Found {seller_count} competing products. Competition level: {level}.",
        }
    
    def _calculate_profit_estimates(self, product_data: dict) -> dict:
        """Calculate profit estimates."""
        price_range = product_data.get("price_range", {})
        avg_price = price_range.get("avg", 0)
        
        # Rough estimates (would need cost data for accuracy)
        estimated_cost = avg_price * 0.4  # Assume 40% cost
        gross_margin = 0.3  # Assume 30% margin
        estimated_profit = avg_price * gross_margin
        
        return {
            "suggested_price": {
                "min": round(avg_price * 0.9, 2),
                "max": round(avg_price * 1.1, 2),
                "optimal": round(avg_price, 2),
            },
            "estimated_cost": round(estimated_cost, 2),
            "gross_margin": gross_margin,
            "estimated_profit_per_unit": round(estimated_profit, 2),
            "note": "Estimates based on market averages. Actual costs may vary.",
        }
    
    def _generate_summary(
        self,
        product_data: dict,
        trends_data: dict,
        competition_data: dict,
        profit_data: dict,
    ) -> dict:
        """Generate report summary and recommendations."""
        competition_level = competition_data.get("level", "unknown")
        trends_available = trends_data.get("available", False)
        
        # Determine recommendation
        if competition_level == "low":
            recommendation = "recommended"
            conclusion = "This appears to be a good opportunity with low competition."
        elif competition_level == "medium":
            recommendation = "wait"
            conclusion = "Moderate competition. Consider differentiation strategy."
        else:
            recommendation = "not_recommended"
            conclusion = "High competition market. Entry may be challenging."
        
        key_points = [
            f"Found {product_data.get('product_count', 0)} products across platforms",
            f"Competition level: {competition_level}",
            f"Average price: ${product_data.get('price_range', {}).get('avg', 0):.2f}",
        ]
        
        if trends_available:
            key_points.append("Google Trends data available for analysis")
        
        return {
            "conclusion": conclusion,
            "recommendation": recommendation,
            "key_points": key_points,
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    def _calculate_overall_score(
        self,
        product_data: dict,
        trends_data: dict,
        competition_data: dict,
        profit_data: dict,
    ) -> float:
        """Calculate overall product score (0-100)."""
        score = 50  # Base score
        
        # Competition adjustment
        level = competition_data.get("level", "medium")
        if level == "low":
            score += 20
        elif level == "high":
            score -= 20
        
        # Profit margin adjustment
        margin = profit_data.get("gross_margin", 0)
        if margin > 0.4:
            score += 15
        elif margin > 0.2:
            score += 5
        
        # Trends adjustment
        if trends_data.get("available"):
            score += 10
        
        return min(max(score, 0), 100)
    
    async def _generate_pdf(self, report_id: str, data: dict) -> Optional[str]:
        """Generate PDF report file."""
        # TODO: Implement PDF generation with WeasyPrint
        # For now, return placeholder
        return f"reports/pdf/{report_id}.pdf"
    
    async def _generate_excel(self, report_id: str, data: dict) -> Optional[str]:
        """Generate Excel report file."""
        # TODO: Implement Excel generation with openpyxl
        # For now, return placeholder
        return f"reports/excel/{report_id}.xlsx"
