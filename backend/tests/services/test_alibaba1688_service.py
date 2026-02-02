"""Unit tests for 1688 supplier service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.alibaba1688_service import (
    Supplier1688,
    extract_keywords,
    translate_to_chinese,
    parse_dimensions,
    filter_by_price,
    filter_by_size,
    calculate_supplier_score,
    calculate_profit_estimate,
    Alibaba1688Scraper,
    match_suppliers_for_products,
    EXCHANGE_RATES,
    SIZE_LIMITS,
)


class TestKeywordExtraction:
    """Tests for keyword extraction from product titles."""

    def test_extract_keywords_basic(self):
        """Test basic keyword extraction."""
        title = "Wireless Bluetooth Earbuds with Charging Case"
        keywords = extract_keywords(title)
        assert len(keywords) > 0
        assert isinstance(keywords, list)
        # Should contain meaningful words
        assert any(w in keywords for w in ['wireless', 'bluetooth', 'earbuds', 'charging', 'case'])

    def test_extract_keywords_removes_noise(self):
        """Test that noise words are removed."""
        title = "New Hot Sale Best Wireless Earbuds for iPhone"
        keywords = extract_keywords(title)
        # Should not contain noise words
        noise_words = ['new', 'hot', 'sale', 'best', 'for']
        for word in noise_words:
            assert word not in keywords

    def test_extract_keywords_limits_count(self):
        """Test that keywords are limited to top 3."""
        title = "Ultra Premium Professional High Quality Wireless Bluetooth Earbuds"
        keywords = extract_keywords(title)
        assert len(keywords) <= 3

    def test_extract_keywords_empty_title(self):
        """Test with empty title."""
        keywords = extract_keywords("")
        assert keywords == []

    def test_extract_keywords_short_words_filtered(self):
        """Test that very short words are filtered."""
        title = "A B C Earbuds"
        keywords = extract_keywords(title)
        assert 'a' not in keywords
        assert 'b' not in keywords
        assert 'c' not in keywords


class TestTranslation:
    """Tests for English to Chinese translation."""

    def test_translate_known_keywords(self):
        """Test translation of known keywords."""
        keywords = ["wireless earbuds", "headphones"]
        chinese = translate_to_chinese(keywords)
        assert len(chinese) > 0
        # Should contain Chinese characters
        assert any('\u4e00' <= c <= '\u9fff' for c in chinese[0])

    def test_translate_partial_match(self):
        """Test partial keyword matching."""
        keywords = ["wireless"]
        chinese = translate_to_chinese(keywords)
        # Should still find matches for partial words
        assert len(chinese) >= 0

    def test_translate_unknown_keyword(self):
        """Test translation of unknown keyword."""
        keywords = ["xyzunknown123"]
        chinese = translate_to_chinese(keywords)
        # Should return fallback
        assert chinese == ["产品"]

    def test_translate_removes_duplicates(self):
        """Test that duplicate translations are removed."""
        keywords = ["wireless earbuds", "bluetooth earbuds"]
        chinese = translate_to_chinese(keywords)
        # Check for no duplicates
        assert len(chinese) == len(set(chinese))


class TestDimensionParsing:
    """Tests for dimension string parsing."""

    def test_parse_standard_format(self):
        """Test parsing standard dimension format."""
        result = parse_dimensions("60x40x30cm")
        assert result == (60, 40, 30)

    def test_parse_asterisk_format(self):
        """Test parsing with asterisks."""
        result = parse_dimensions("60*40*30")
        assert result == (60, 40, 30)

    def test_parse_with_spaces(self):
        """Test parsing with spaces."""
        result = parse_dimensions("60 x 40 x 30 cm")
        assert result == (60, 40, 30)

    def test_parse_decimal_dimensions(self):
        """Test parsing decimal dimensions."""
        result = parse_dimensions("60.5x40.2x30.1cm")
        assert result == (60.5, 40.2, 30.1)

    def test_parse_invalid_format(self):
        """Test parsing invalid format."""
        result = parse_dimensions("invalid")
        assert result is None

    def test_parse_empty_string(self):
        """Test parsing empty string."""
        result = parse_dimensions("")
        assert result is None

    def test_parse_none(self):
        """Test parsing None."""
        result = parse_dimensions(None)
        assert result is None


class TestPriceFilter:
    """Tests for price filtering."""

    def test_filter_within_limit(self):
        """Test filtering supplier within price limit."""
        supplier = Supplier1688(
            offer_id="123",
            title="Test Product",
            price=300,
            product_url="http://test.com",
            supplier_name="Test Supplier"
        )
        assert filter_by_price(supplier, max_price=500) is True

    def test_filter_at_limit(self):
        """Test filtering supplier at price limit."""
        supplier = Supplier1688(
            offer_id="123",
            title="Test Product",
            price=500,
            product_url="http://test.com",
            supplier_name="Test Supplier"
        )
        assert filter_by_price(supplier, max_price=500) is True

    def test_filter_above_limit(self):
        """Test filtering supplier above price limit."""
        supplier = Supplier1688(
            offer_id="123",
            title="Test Product",
            price=600,
            product_url="http://test.com",
            supplier_name="Test Supplier"
        )
        assert filter_by_price(supplier, max_price=500) is False

    def test_filter_default_limit(self):
        """Test filtering with default limit."""
        supplier = Supplier1688(
            offer_id="123",
            title="Test Product",
            price=400,
            product_url="http://test.com",
            supplier_name="Test Supplier"
        )
        assert filter_by_price(supplier) is True


class TestSizeFilter:
    """Tests for size/weight filtering."""

    def test_filter_small_item(self):
        """Test filtering small item."""
        supplier = Supplier1688(
            offer_id="123",
            title="Test Product",
            price=100,
            product_url="http://test.com",
            supplier_name="Test Supplier",
            weight=2.0,
            is_small_medium=True
        )
        assert filter_by_size(supplier) is True

    def test_filter_heavy_item(self):
        """Test filtering heavy item."""
        supplier = Supplier1688(
            offer_id="123",
            title="Test Product",
            price=100,
            product_url="http://test.com",
            supplier_name="Test Supplier",
            weight=10.0,
            is_small_medium=True
        )
        assert filter_by_size(supplier) is False

    def test_filter_large_dimensions(self):
        """Test filtering item with large dimensions."""
        supplier = Supplier1688(
            offer_id="123",
            title="Test Product",
            price=100,
            product_url="http://test.com",
            supplier_name="Test Supplier",
            dimensions="100x80x60cm",
            is_small_medium=True
        )
        assert filter_by_size(supplier) is False

    def test_filter_medium_dimensions(self):
        """Test filtering item with medium dimensions."""
        supplier = Supplier1688(
            offer_id="123",
            title="Test Product",
            price=100,
            product_url="http://test.com",
            supplier_name="Test Supplier",
            dimensions="30x20x10cm",
            is_small_medium=True
        )
        assert filter_by_size(supplier) is True

    def test_filter_large_volume(self):
        """Test filtering item with large volume."""
        supplier = Supplier1688(
            offer_id="123",
            title="Test Product",
            price=100,
            product_url="http://test.com",
            supplier_name="Test Supplier",
            dimensions="50x50x25cm",  # 62500 cm3 > 50000
            is_small_medium=True
        )
        assert filter_by_size(supplier) is False

    def test_filter_no_size_info(self):
        """Test filtering item with no size info."""
        supplier = Supplier1688(
            offer_id="123",
            title="Test Product",
            price=100,
            product_url="http://test.com",
            supplier_name="Test Supplier",
            is_small_medium=True
        )
        assert filter_by_size(supplier) is True


class TestSupplierScore:
    """Tests for supplier score calculation."""

    def test_calculate_score_good_supplier(self):
        """Test score calculation for a good supplier."""
        supplier = Supplier1688(
            offer_id="123",
            title="Test Product",
            price=50,
            product_url="http://test.com",
            supplier_name="Test Supplier",
            supplier_rating=4.8,
            supplier_years=5,
            is_verified=True,
            sold_count=10000,
            is_small_medium=True
        )
        score = calculate_supplier_score(supplier, source_price=100, source_currency="AUD")
        assert 0 <= score <= 100
        assert score > 50  # Good supplier should score well

    def test_calculate_score_poor_supplier(self):
        """Test score calculation for a poor supplier."""
        supplier = Supplier1688(
            offer_id="123",
            title="Test Product",
            price=200,  # High price
            product_url="http://test.com",
            supplier_name="Test Supplier",
            supplier_rating=2.0,
            supplier_years=0,
            is_verified=False,
            sold_count=0,
            is_small_medium=False
        )
        score = calculate_supplier_score(supplier, source_price=50, source_currency="AUD")
        assert 0 <= score <= 100

    def test_calculate_score_nzd_currency(self):
        """Test score calculation with NZD currency."""
        supplier = Supplier1688(
            offer_id="123",
            title="Test Product",
            price=50,
            product_url="http://test.com",
            supplier_name="Test Supplier",
            is_small_medium=True
        )
        score = calculate_supplier_score(supplier, source_price=100, source_currency="NZD")
        assert 0 <= score <= 100

    def test_calculate_score_range(self):
        """Test that score is always within valid range."""
        supplier = Supplier1688(
            offer_id="123",
            title="Test Product",
            price=1,
            product_url="http://test.com",
            supplier_name="Test Supplier",
            supplier_rating=5.0,
            supplier_years=20,
            is_verified=True,
            sold_count=1000000,
            is_small_medium=True
        )
        score = calculate_supplier_score(supplier, source_price=1000, source_currency="AUD")
        assert 0 <= score <= 100


class TestProfitEstimate:
    """Tests for profit estimation."""

    def test_profit_estimate_basic(self):
        """Test basic profit estimation."""
        result = calculate_profit_estimate(
            source_price=100,
            source_currency="AUD",
            supplier_price=50,
            quantity=100,
            shipping_per_unit=15
        )
        assert "source_price" in result
        assert "profit_margin" in result
        assert "roi" in result
        assert result["source_price"] == 100

    def test_profit_estimate_quantity_effect(self):
        """Test that quantity affects total costs."""
        result_100 = calculate_profit_estimate(
            source_price=100,
            source_currency="AUD",
            supplier_price=50,
            quantity=100
        )
        result_200 = calculate_profit_estimate(
            source_price=100,
            source_currency="AUD",
            supplier_price=50,
            quantity=200
        )
        assert result_200["purchase_cost_cny"] == 2 * result_100["purchase_cost_cny"]

    def test_profit_estimate_nzd(self):
        """Test profit estimation with NZD."""
        result = calculate_profit_estimate(
            source_price=100,
            source_currency="NZD",
            supplier_price=50,
            quantity=100
        )
        assert result["exchange_rate"] == EXCHANGE_RATES["NZD_CNY"]

    def test_profit_estimate_notes(self):
        """Test that notes are included."""
        result = calculate_profit_estimate(
            source_price=100,
            source_currency="AUD",
            supplier_price=50,
            quantity=100
        )
        assert "notes" in result
        assert len(result["notes"]) > 0


class TestSupplier1688Model:
    """Tests for Supplier1688 Pydantic model."""

    def test_create_minimal_supplier(self):
        """Test creating supplier with minimal fields."""
        supplier = Supplier1688(
            offer_id="123",
            title="Test Product",
            price=100,
            product_url="http://test.com",
            supplier_name="Test Supplier"
        )
        assert supplier.offer_id == "123"
        assert supplier.moq == 1  # Default value
        assert supplier.is_small_medium is True  # Default value

    def test_create_full_supplier(self):
        """Test creating supplier with all fields."""
        supplier = Supplier1688(
            offer_id="123",
            title="Test Product",
            price=100,
            price_range="80-120",
            moq=50,
            sold_count=1000,
            image_url="http://image.com/img.jpg",
            product_url="http://test.com",
            supplier_name="Test Supplier",
            supplier_url="http://supplier.com",
            supplier_years=5,
            supplier_rating=4.5,
            is_verified=True,
            location="Shenzhen",
            shipping_estimate="3-5 days",
            weight=0.5,
            dimensions="10x10x5cm",
            is_small_medium=True,
            match_score=85.5
        )
        assert supplier.price_range == "80-120"
        assert supplier.moq == 50
        assert supplier.is_verified is True
        assert supplier.match_score == 85.5


class TestConstants:
    """Tests for module constants."""

    def test_exchange_rates_defined(self):
        """Test that exchange rates are defined."""
        assert "AUD_CNY" in EXCHANGE_RATES
        assert "NZD_CNY" in EXCHANGE_RATES
        assert EXCHANGE_RATES["AUD_CNY"] > 0
        assert EXCHANGE_RATES["NZD_CNY"] > 0

    def test_size_limits_defined(self):
        """Test that size limits are defined."""
        assert "max_weight_kg" in SIZE_LIMITS
        assert "max_length_cm" in SIZE_LIMITS
        assert "max_volume_cm3" in SIZE_LIMITS
        assert SIZE_LIMITS["max_weight_kg"] == 5
        assert SIZE_LIMITS["max_length_cm"] == 60


# Integration tests (require mocking)
class TestAlibaba1688Scraper:
    """Integration tests for the scraper class."""

    @pytest.mark.asyncio
    async def test_scraper_initialization(self):
        """Test scraper initialization."""
        scraper = Alibaba1688Scraper()
        assert scraper._browser is None
        assert scraper._request_count == 0
        await scraper.close()

    @pytest.mark.asyncio
    async def test_scraper_close(self):
        """Test scraper close."""
        scraper = Alibaba1688Scraper()
        await scraper.close()
        assert scraper._browser is None


class TestMatchSuppliersForProducts:
    """Tests for the main matching function."""

    @pytest.mark.asyncio
    async def test_match_empty_products(self):
        """Test matching with empty product list."""
        results = await match_suppliers_for_products(
            products=[],
            max_price=500,
            limit_per_product=10
        )
        assert results == []
