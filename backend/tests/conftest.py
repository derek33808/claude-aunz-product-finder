"""
Pytest configuration and fixtures for backend tests.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db


# Mock database client fixture
@pytest.fixture
def mock_db():
    """Create a mock database client."""
    mock = MagicMock()

    # Mock table method to return chainable mock
    mock_table = MagicMock()
    mock.table.return_value = mock_table

    # Make query methods chainable
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.ilike.return_value = mock_table
    mock_table.gte.return_value = mock_table
    mock_table.lte.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.range.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.upsert.return_value = mock_table

    # Default execute result
    mock_result = MagicMock()
    mock_result.data = []
    mock_table.execute.return_value = mock_result

    return mock


@pytest.fixture
def client(mock_db):
    """Create a test client with mocked database."""

    def override_get_db():
        return mock_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
def sample_products():
    """Sample product data for testing."""
    return [
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "platform": "ebay_au",
            "platform_id": "123456789",
            "title": "Wireless Bluetooth Earbuds",
            "category": "Electronics",
            "price": 59.99,
            "currency": "AUD",
            "rating": 4.5,
            "review_count": 150,
            "seller_count": 1,
            "bsr_rank": 100,
            "image_url": "https://example.com/image1.jpg",
            "product_url": "https://ebay.com.au/item/123456789",
            "created_at": "2026-01-20T00:00:00Z",
            "updated_at": "2026-01-20T00:00:00Z"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "platform": "ebay_nz",
            "platform_id": "987654321",
            "title": "Smart Watch Fitness Tracker",
            "category": "Electronics",
            "price": 129.00,
            "currency": "NZD",
            "rating": 4.2,
            "review_count": 85,
            "seller_count": 3,
            "bsr_rank": 50,
            "image_url": "https://example.com/image2.jpg",
            "product_url": "https://ebay.co.nz/item/987654321",
            "created_at": "2026-01-19T00:00:00Z",
            "updated_at": "2026-01-19T00:00:00Z"
        }
    ]


@pytest.fixture
def sample_trends_data():
    """Sample Google Trends data for testing."""
    return {
        "keyword": "wireless earbuds",
        "region": "AU",
        "timeline_data": [
            {"date": "2026-01-01", "value": 75},
            {"date": "2026-01-08", "value": 82},
            {"date": "2026-01-15", "value": 90},
        ],
        "related_queries": [
            {"query": "best wireless earbuds", "value": 100},
            {"query": "cheap earbuds", "value": 65},
        ]
    }
