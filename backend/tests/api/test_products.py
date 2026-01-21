"""
Tests for the Products API endpoints.
"""

import pytest
from unittest.mock import MagicMock


class TestProductSearch:
    """Test product search endpoint."""

    def test_search_products_empty(self, client, mock_db):
        """Test search with no results."""
        mock_result = MagicMock()
        mock_result.data = []
        mock_db.table.return_value.select.return_value.order.return_value.range.return_value.execute.return_value = mock_result

        response = client.get("/api/products/search")

        assert response.status_code == 200
        assert response.json() == []

    def test_search_products_with_results(self, client, mock_db, sample_products):
        """Test search returns products."""
        mock_result = MagicMock()
        mock_result.data = sample_products
        mock_db.table.return_value.select.return_value.order.return_value.range.return_value.execute.return_value = mock_result

        response = client.get("/api/products/search")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "Wireless Bluetooth Earbuds"

    def test_search_with_keyword(self, client, mock_db, sample_products):
        """Test search with keyword filter."""
        mock_result = MagicMock()
        mock_result.data = [sample_products[0]]  # Only earbuds
        mock_db.table.return_value.select.return_value.ilike.return_value.order.return_value.range.return_value.execute.return_value = mock_result

        response = client.get("/api/products/search?keyword=earbuds")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_search_with_platform_filter(self, client, mock_db, sample_products):
        """Test search with platform filter."""
        mock_result = MagicMock()
        mock_result.data = [sample_products[0]]  # Only eBay AU
        mock_db.table.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_result

        response = client.get("/api/products/search?platform=ebay_au")

        assert response.status_code == 200

    def test_search_invalid_platform(self, client, mock_db):
        """Test search with invalid platform returns 422."""
        response = client.get("/api/products/search?platform=invalid")

        assert response.status_code == 422

    def test_search_with_price_range(self, client, mock_db, sample_products):
        """Test search with price range filter."""
        mock_result = MagicMock()
        mock_result.data = [sample_products[0]]  # Product under $100
        mock_db.table.return_value.select.return_value.gte.return_value.lte.return_value.order.return_value.range.return_value.execute.return_value = mock_result

        response = client.get("/api/products/search?min_price=50&max_price=100")

        assert response.status_code == 200

    def test_search_pagination(self, client, mock_db):
        """Test search pagination parameters."""
        mock_result = MagicMock()
        mock_result.data = []
        mock_db.table.return_value.select.return_value.order.return_value.range.return_value.execute.return_value = mock_result

        response = client.get("/api/products/search?page=2&page_size=10")

        assert response.status_code == 200

    def test_search_invalid_page(self, client, mock_db):
        """Test search with invalid page number."""
        response = client.get("/api/products/search?page=0")

        assert response.status_code == 422


class TestHotProducts:
    """Test hot products endpoint."""

    def test_get_hot_products_empty(self, client, mock_db):
        """Test hot products with no data."""
        mock_result = MagicMock()
        mock_result.data = []
        mock_db.table.return_value.select.return_value.execute.return_value = mock_result

        response = client.get("/api/products/hot")

        assert response.status_code == 200
        assert response.json() == []

    def test_get_hot_products_with_data(self, client, mock_db, sample_products):
        """Test hot products returns sorted results."""
        mock_result = MagicMock()
        mock_result.data = sample_products.copy()
        mock_db.table.return_value.select.return_value.execute.return_value = mock_result

        response = client.get("/api/products/hot")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Should have hot_score field
        assert "hot_score" in data[0]
        # First product should have higher or equal score (sorted)
        assert data[0]["hot_score"] >= data[1]["hot_score"]

    def test_get_hot_products_limit(self, client, mock_db, sample_products):
        """Test hot products respects limit parameter."""
        mock_result = MagicMock()
        mock_result.data = sample_products.copy()
        mock_db.table.return_value.select.return_value.execute.return_value = mock_result

        response = client.get("/api/products/hot?limit=1")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_get_hot_products_invalid_limit(self, client, mock_db):
        """Test hot products with invalid limit."""
        response = client.get("/api/products/hot?limit=0")

        assert response.status_code == 422


class TestProductById:
    """Test get product by ID endpoint."""

    def test_get_product_found(self, client, mock_db, sample_products):
        """Test getting existing product by ID."""
        mock_result = MagicMock()
        mock_result.data = [sample_products[0]]
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        product_id = "550e8400-e29b-41d4-a716-446655440001"
        response = client.get(f"/api/products/{product_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Wireless Bluetooth Earbuds"

    def test_get_product_not_found(self, client, mock_db):
        """Test getting non-existent product returns 404."""
        mock_result = MagicMock()
        mock_result.data = []
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        product_id = "550e8400-e29b-41d4-a716-000000000000"
        response = client.get(f"/api/products/{product_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_product_invalid_uuid(self, client, mock_db):
        """Test getting product with invalid UUID returns 422."""
        response = client.get("/api/products/invalid-uuid")

        assert response.status_code == 422
