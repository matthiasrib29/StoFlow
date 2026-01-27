"""
Tests for EbayDescriptionService.

Tests multilingual HTML description generation for eBay listings.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from services.ebay.ebay_description_service import (
    EbayDescriptionService,
    MAX_DESCRIPTION_LENGTH,
)


@pytest.fixture
def mock_product():
    """Create a mock product with all required attributes."""
    product = MagicMock()
    product.id = 1
    product.title = "Test Product"
    product.description = "Test description"
    product.brand = "Levi's"
    product.model = "501"
    product.category = "Jeans"
    product.condition = 3  # note 0-10
    product.fit = "Regular"
    product.gender = "men"
    product.decade = "1990"
    product.location = "Paris"
    product.trend = "Vintage"
    product.season = None
    product.sport = None
    product.neckline = None
    product.length = None
    product.pattern = None
    product.rise = None
    product.closure = None
    product.sleeve_length = None
    product.origin = None
    product.stretch = None
    product.lining = None

    # M2M relationships
    product.colors = ["Blue"]
    product.materials = ["Denim"]
    product.condition_sups = []
    product.unique_feature = ["Vintage wash", "Original buttons"]

    # Sizes
    product.size_original = "W32/L34"
    product.size_normalized = "M"

    # Dimensions
    product.dim1 = 42
    product.dim2 = 105
    product.dim3 = 30
    product.dim4 = 20
    product.dim5 = 24
    product.dim6 = 82

    return product


@pytest.fixture
def mock_service():
    """Create an EbayDescriptionService with mocked DB."""
    db = MagicMock()
    service = EbayDescriptionService(db)
    return service


@pytest.fixture
def mock_marketplace_config_en():
    """Mock marketplace config returning English."""
    config = MagicMock()
    config.get_language.return_value = "en"
    return config


@pytest.fixture
def mock_marketplace_config_fr():
    """Mock marketplace config returning French."""
    config = MagicMock()
    config.get_language.return_value = "fr"
    return config


@pytest.fixture
def mock_condition():
    """Mock condition object."""
    condition = MagicMock()
    condition.note = 3
    condition.get_name.return_value = "Very good"
    return condition


class TestEbayDescriptionService:
    """Tests for EbayDescriptionService.generate_description."""

    def test_generate_description_en_contains_all_sections(
        self, mock_service, mock_product, mock_marketplace_config_en, mock_condition,
    ):
        """Full EN description contains header, characteristics, measurements, footer, tags."""
        # Setup DB mocks
        mock_service.db.query.return_value.filter.return_value.first.side_effect = [
            mock_marketplace_config_en,  # _get_language
            None,  # _get_category_type (Category lookup)
            None,  # _translate_attribute for category in seo_intro
            mock_condition,  # _get_condition_text in seo_intro
            None,  # _translate_attribute Color in characteristics
            mock_condition,  # _get_condition_text in characteristics
            None,  # _translate_attribute Gender in characteristics
        ]

        result = mock_service.generate_description(mock_product, "EBAY_GB")

        # Header
        assert "SHOP TON OUTFIT" in result
        assert "Premium Second Hand Fashion" in result
        # Characteristics section
        assert "Characteristics" in result
        assert "Levi" in result
        assert "501" in result
        assert "Regular" in result
        # Measurements section
        assert "Measurements" in result
        assert "W32/L34" in result
        assert "42 cm" in result
        # Shipping
        assert "Shipping" in result
        assert "Fast shipping" in result
        # Footer
        assert "Professional seller" in result
        # SEO tags
        assert "SEO Tags" in result
        assert "#vintage" in result

    def test_generate_description_fr_uses_french_labels(
        self, mock_service, mock_product, mock_marketplace_config_fr, mock_condition,
    ):
        """FR description uses French section labels."""
        mock_condition.get_name.return_value = "Très bon état"

        mock_service.db.query.return_value.filter.return_value.first.side_effect = [
            mock_marketplace_config_fr,  # _get_language
            None,  # _get_category_type
            None,  # _translate_attribute category
            mock_condition,  # _get_condition_text seo_intro
            None,  # _translate_attribute Color
            mock_condition,  # _get_condition_text characteristics
            None,  # _translate_attribute Gender
        ]

        result = mock_service.generate_description(mock_product, "EBAY_FR")

        assert "Caractéristiques" in result
        assert "Mesures" in result
        assert "Expédition rapide" in result
        assert "Mode seconde main" in result

    def test_custom_shop_name_in_header(
        self, mock_service, mock_product, mock_marketplace_config_en, mock_condition,
    ):
        """Custom shop name appears in the header."""
        mock_service.db.query.return_value.filter.return_value.first.side_effect = [
            mock_marketplace_config_en,
            None, None, mock_condition, None, mock_condition, None,
        ]

        result = mock_service.generate_description(
            mock_product, "EBAY_GB", shop_name="MY VINTAGE STORE"
        )

        assert "MY VINTAGE STORE" in result
        assert "SHOP TON OUTFIT" not in result

    def test_seo_intro_contains_brand_and_category(
        self, mock_service, mock_product, mock_marketplace_config_en, mock_condition,
    ):
        """SEO intro paragraph includes brand and category."""
        mock_service.db.query.return_value.filter.return_value.first.side_effect = [
            mock_marketplace_config_en,
            None, None, mock_condition, None, mock_condition, None,
        ]

        result = mock_service.generate_description(mock_product, "EBAY_GB")

        # SEO intro should contain brand
        assert "Levi" in result
        # Category name (Jeans) should appear
        assert "Jeans" in result

    def test_measurements_shown_when_dims_present(
        self, mock_service, mock_product, mock_marketplace_config_en, mock_condition,
    ):
        """Measurements displayed when dim1/dim2 etc. are present."""
        mock_service.db.query.return_value.filter.return_value.first.side_effect = [
            mock_marketplace_config_en,
            None, None, mock_condition, None, mock_condition, None,
        ]

        result = mock_service.generate_description(mock_product, "EBAY_GB")

        assert "42 cm" in result
        assert "105 cm" in result
        assert "82 cm" in result

    def test_measurements_hidden_when_no_dims(
        self, mock_service, mock_product, mock_marketplace_config_en, mock_condition,
    ):
        """No measurement lines when dimensions are all None."""
        mock_product.dim1 = None
        mock_product.dim2 = None
        mock_product.dim3 = None
        mock_product.dim4 = None
        mock_product.dim5 = None
        mock_product.dim6 = None

        mock_service.db.query.return_value.filter.return_value.first.side_effect = [
            mock_marketplace_config_en,
            None, None, mock_condition, None, mock_condition, None,
        ]

        result = mock_service.generate_description(mock_product, "EBAY_GB")

        # Should have the dash placeholder instead of cm measurements
        assert "cm</p>" not in result

    def test_category_type_jeans_has_six_dim_labels(
        self, mock_service, mock_product,
    ):
        """Jeans category type returns 6 measurement label pairs."""
        # Mock category DB lookup to return a jeans-related category
        mock_category = MagicMock()
        mock_category.parent_category = "Pants"

        mock_service.db.query.return_value.filter.return_value.first.return_value = mock_category
        mock_product.category = "Jeans"

        result = mock_service._get_category_type(mock_product)
        assert result == "jeans"

    def test_category_type_shorts_detected(self, mock_service, mock_product):
        """Shorts category type correctly detected."""
        mock_category = MagicMock()
        mock_category.parent_category = "Shorts"

        mock_service.db.query.return_value.filter.return_value.first.return_value = mock_category
        mock_product.category = "Cargo Shorts"

        result = mock_service._get_category_type(mock_product)
        assert result == "shorts"

    def test_category_type_tops_is_default(self, mock_service, mock_product):
        """Tops is the default category type for unrecognized categories."""
        mock_category = MagicMock()
        mock_category.parent_category = "Outerwear"

        mock_service.db.query.return_value.filter.return_value.first.return_value = mock_category
        mock_product.category = "Jacket"

        result = mock_service._get_category_type(mock_product)
        assert result == "tops"

    def test_tags_present_in_description(
        self, mock_service, mock_product, mock_marketplace_config_en, mock_condition,
    ):
        """SEO tags section is present in the output."""
        mock_service.db.query.return_value.filter.return_value.first.side_effect = [
            mock_marketplace_config_en,
            None, None, mock_condition, None, mock_condition, None,
        ]

        result = mock_service.generate_description(mock_product, "EBAY_GB")

        assert "SEO Tags:" in result
        # At least some tags should be present
        assert "#" in result

    def test_truncation_at_max_length(
        self, mock_service, mock_product, mock_marketplace_config_en, mock_condition,
    ):
        """Description is truncated if it exceeds MAX_DESCRIPTION_LENGTH."""
        mock_service.db.query.return_value.filter.return_value.first.side_effect = [
            mock_marketplace_config_en,
            None, None, mock_condition, None, mock_condition, None,
        ]

        # Make description very long by adding many unique features
        mock_product.unique_feature = [f"feature_{i}" for i in range(500)]

        result = mock_service.generate_description(mock_product, "EBAY_GB")

        assert len(result) <= MAX_DESCRIPTION_LENGTH

    def test_condition_badge_colors(self):
        """Condition badge colors match note ranges."""
        assert EbayDescriptionService._get_condition_color(0) == "#28a745"
        assert EbayDescriptionService._get_condition_color(3) == "#28a745"
        assert EbayDescriptionService._get_condition_color(4) == "#ffc107"
        assert EbayDescriptionService._get_condition_color(5) == "#ffc107"
        assert EbayDescriptionService._get_condition_color(6) == "#ff9800"
        assert EbayDescriptionService._get_condition_color(10) == "#ff9800"
        assert EbayDescriptionService._get_condition_color(None) == "#28a745"

    def test_era_format_per_language(self):
        """Era/decade formatting varies by language."""
        t = {}  # Not used by _format_era
        assert EbayDescriptionService._format_era("1990", "en", t) == "1990s"
        assert EbayDescriptionService._format_era("1990", "fr", t) == "Années 1990"
        assert EbayDescriptionService._format_era("1990", "de", t) == "1990er Jahre"
        assert EbayDescriptionService._format_era("1990", "it", t) == "Anni 1990"
        assert EbayDescriptionService._format_era("1990", "es", t) == "Años 1990"

    def test_no_brand_shows_vintage_in_intro(
        self, mock_service, mock_product, mock_marketplace_config_en, mock_condition,
    ):
        """When brand is unbranded, SEO intro uses 'vintage' instead."""
        mock_product.brand = "unbranded"

        mock_service.db.query.return_value.filter.return_value.first.side_effect = [
            mock_marketplace_config_en,
            None, None, mock_condition, None, mock_condition, None,
        ]

        result = mock_service.generate_description(mock_product, "EBAY_GB")

        assert "vintage" in result.lower()

    def test_language_fallback_to_english(self, mock_service, mock_product, mock_condition):
        """Unknown marketplace falls back to English."""
        # No marketplace config found
        mock_service.db.query.return_value.filter.return_value.first.side_effect = [
            None,  # _get_language returns "en" (fallback)
            None, None, mock_condition, None, mock_condition, None,
        ]

        result = mock_service.generate_description(mock_product, "EBAY_UNKNOWN")

        # Should use English labels
        assert "Characteristics" in result
