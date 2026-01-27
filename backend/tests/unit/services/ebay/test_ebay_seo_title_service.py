"""
Tests for EbaySeoTitleService.

Tests SEO title generation with multilingual translations and priority truncation.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestEbaySeoTitleService:
    """Tests for SEO title generation."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock DB session."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mocked __init__ dependencies."""
        with patch(
            "services.ebay.ebay_seo_title_service.MarketplaceConfig"
        ) as MockConfig:
            from services.ebay.ebay_seo_title_service import EbaySeoTitleService

            svc = EbaySeoTitleService(mock_db)
            return svc

    @pytest.fixture
    def mock_product(self):
        """Create a fully-populated mock product."""
        product = MagicMock()
        product.brand = "Levi's"
        product.model = "501"
        product.category = "jeans"
        product.size_original = "W32/L34"
        product.colors = ["Blue"]
        product.condition = 3
        product.gender = "men"
        product.decade = "1990s"
        product.location = "Paris"
        return product

    @pytest.fixture
    def mock_marketplace_config_fr(self):
        """Mock MarketplaceConfig for EBAY_FR."""
        config = MagicMock()
        config.marketplace_id = "EBAY_FR"
        config.country_code = "FR"
        config.get_language.return_value = "fr"
        return config

    @pytest.fixture
    def mock_marketplace_config_gb(self):
        """Mock MarketplaceConfig for EBAY_GB."""
        config = MagicMock()
        config.marketplace_id = "EBAY_GB"
        config.country_code = "UK"
        config.get_language.return_value = "en"
        return config

    def _setup_db_mocks(self, mock_db, marketplace_config, translations=None):
        """
        Configure mock_db to return appropriate objects for queries.

        Args:
            translations: dict mapping (model_class_name, name_en) -> mock object
        """
        if translations is None:
            translations = {}

        def query_side_effect(model_class):
            mock_query = MagicMock()
            class_name = model_class.__name__

            def filter_side_effect(*args, **kwargs):
                mock_filter = MagicMock()

                def first_side_effect():
                    # MarketplaceConfig
                    if class_name == "MarketplaceConfig":
                        return marketplace_config

                    # Condition (PK = note int)
                    if class_name == "Condition":
                        for key, obj in translations.items():
                            if key[0] == "Condition":
                                return obj
                        return None

                    # Other attribute models (PK = name_en)
                    for key, obj in translations.items():
                        if key[0] == class_name:
                            return obj
                    return None

                mock_filter.first = first_side_effect
                return mock_filter

            mock_query.filter = filter_side_effect
            return mock_query

        mock_db.query = MagicMock(side_effect=query_side_effect)

    def test_full_title_with_all_components_en(
        self, service, mock_db, mock_product, mock_marketplace_config_gb
    ):
        """Test title with all components in English (no translation needed)."""
        self._setup_db_mocks(mock_db, mock_marketplace_config_gb, {
            ("Condition", 3): self._mock_condition("Very good", "en"),
        })

        title = service.generate_seo_title(mock_product, "EBAY_GB")

        assert "Levi's" in title
        assert "501" in title
        assert "jeans" in title
        assert "W32/L34" in title
        assert "Blue" in title
        assert "Very good" in title
        assert "men" in title
        assert "1990s" in title
        assert len(title) <= 80

    def test_full_title_translated_fr(
        self, service, mock_db, mock_product, mock_marketplace_config_fr
    ):
        """Test title with French translations."""
        self._setup_db_mocks(mock_db, mock_marketplace_config_fr, {
            ("Category", "jeans"): self._mock_attr(name_en="jeans", name_fr="Jean"),
            ("Color", "Blue"): self._mock_attr(name_en="Blue", name_fr="Bleu"),
            ("Condition", 3): self._mock_condition("Tres bon etat", "fr"),
            ("Gender", "men"): self._mock_attr(name_en="men", name_fr="Homme"),
        })

        title = service.generate_seo_title(mock_product, "EBAY_FR")

        assert "Levi's" in title
        assert "501" in title
        assert "Jean" in title
        assert "Bleu" in title
        assert "Tres bon etat" in title
        assert "Homme" in title
        assert "1990s" in title
        assert len(title) <= 80

    def test_truncation_drops_lowest_priority(
        self, service, mock_db, mock_marketplace_config_gb
    ):
        """Test that lowest priority components are dropped when title > 80 chars."""
        product = MagicMock()
        product.brand = "A Very Long Brand Name That Takes Space"
        product.model = "Super Exclusive Model XYZ-2000"
        product.category = "very-long-category-name"
        product.size_original = "XXL"
        product.colors = ["Multicolored"]
        product.condition = 3
        product.gender = "men"
        product.decade = "1990s"
        product.location = None

        self._setup_db_mocks(mock_db, mock_marketplace_config_gb, {
            ("Condition", 3): self._mock_condition("Very good", "en"),
        })

        title = service.generate_seo_title(product, "EBAY_GB")

        assert len(title) <= 80
        # Brand should always be present (highest priority)
        assert "A Very Long Brand Name That Takes Space" in title

    def test_fallback_to_english_when_translation_missing(
        self, service, mock_db, mock_product, mock_marketplace_config_fr
    ):
        """Test fallback to English when translation column is empty."""
        # Category with no name_fr (e.g., NL/PL not available for Category)
        mock_cat = MagicMock()
        mock_cat.name_en = "jeans"
        mock_cat.name_fr = None  # No French translation

        self._setup_db_mocks(mock_db, mock_marketplace_config_fr, {
            ("Category", "jeans"): mock_cat,
            ("Color", "Blue"): self._mock_attr(name_en="Blue", name_fr="Bleu"),
            ("Condition", 3): self._mock_condition("Tres bon etat", "fr"),
            ("Gender", "men"): self._mock_attr(name_en="men", name_fr="Homme"),
        })

        title = service.generate_seo_title(mock_product, "EBAY_FR")

        # Category falls back to English "jeans"
        assert "jeans" in title

    def test_condition_zero_not_skipped(
        self, service, mock_db, mock_marketplace_config_gb
    ):
        """Test that condition=0 (new with tags) is not skipped."""
        product = MagicMock()
        product.brand = "Nike"
        product.model = None
        product.category = "t-shirts"
        product.size_original = "M"
        product.colors = []
        product.condition = 0  # Falsy but valid!
        product.gender = None
        product.decade = None
        product.location = None

        self._setup_db_mocks(mock_db, mock_marketplace_config_gb, {
            ("Condition", 0): self._mock_condition("New with tags", "en"),
        })

        title = service.generate_seo_title(product, "EBAY_GB")

        assert "New with tags" in title

    def test_product_without_optional_attributes(
        self, service, mock_db, mock_marketplace_config_gb
    ):
        """Test product with only required attributes (brand + category)."""
        product = MagicMock()
        product.brand = "Nike"
        product.model = None
        product.category = "t-shirts"
        product.size_original = None
        product.colors = []
        product.condition = None
        product.gender = None
        product.decade = None
        product.location = None

        self._setup_db_mocks(mock_db, mock_marketplace_config_gb)

        title = service.generate_seo_title(product, "EBAY_GB")

        assert title == "Nike t-shirts"

    def test_location_added_if_space_permits(
        self, service, mock_db, mock_marketplace_config_gb
    ):
        """Test that location is appended in parentheses if space allows."""
        product = MagicMock()
        product.brand = "Nike"
        product.model = None
        product.category = "t-shirts"
        product.size_original = "M"
        product.colors = []
        product.condition = None
        product.gender = None
        product.decade = None
        product.location = "Paris"

        self._setup_db_mocks(mock_db, mock_marketplace_config_gb)

        title = service.generate_seo_title(product, "EBAY_GB")

        assert title == "Nike t-shirts M (Paris)"

    def test_location_not_added_if_too_long(
        self, service, mock_db, mock_marketplace_config_gb
    ):
        """Test that location is NOT appended if it would exceed 80 chars."""
        product = MagicMock()
        product.brand = "A" * 40
        product.model = "B" * 30
        product.category = None
        product.size_original = None
        product.colors = []
        product.condition = None
        product.gender = None
        product.decade = None
        product.location = "Very Long Location Name"

        self._setup_db_mocks(mock_db, mock_marketplace_config_gb)

        title = service.generate_seo_title(product, "EBAY_GB")

        assert "(Very Long Location Name)" not in title
        assert len(title) <= 80

    def test_unbranded_is_skipped(
        self, service, mock_db, mock_marketplace_config_gb
    ):
        """Test that 'unbranded' brand is not included."""
        product = MagicMock()
        product.brand = "Unbranded"
        product.model = None
        product.category = "t-shirts"
        product.size_original = None
        product.colors = []
        product.condition = None
        product.gender = None
        product.decade = None
        product.location = None

        self._setup_db_mocks(mock_db, mock_marketplace_config_gb)

        title = service.generate_seo_title(product, "EBAY_GB")

        assert "Unbranded" not in title
        assert title == "t-shirts"

    def test_empty_product_returns_empty_string(
        self, service, mock_db, mock_marketplace_config_gb
    ):
        """Test product with no attributes returns empty string."""
        product = MagicMock()
        product.brand = None
        product.model = None
        product.category = None
        product.size_original = None
        product.colors = []
        product.condition = None
        product.gender = None
        product.decade = None
        product.location = None

        self._setup_db_mocks(mock_db, mock_marketplace_config_gb)

        title = service.generate_seo_title(product, "EBAY_GB")

        assert title == ""

    def test_assemble_title_static_method(self):
        """Test the static _assemble_title method directly."""
        from services.ebay.ebay_seo_title_service import EbaySeoTitleService

        # Normal case
        result = EbaySeoTitleService._assemble_title(["Nike", "Air Max", "Sneakers"])
        assert result == "Nike Air Max Sneakers"

        # Truncation
        components = ["A" * 40, "B" * 30, "C" * 20]
        result = EbaySeoTitleService._assemble_title(components)
        assert len(result) <= 80

        # Empty
        result = EbaySeoTitleService._assemble_title([])
        assert result == ""

    def test_marketplace_not_found_falls_back_to_english(
        self, service, mock_db, mock_product
    ):
        """Test fallback to English when marketplace config not found."""
        self._setup_db_mocks(mock_db, None)  # No marketplace config

        title = service.generate_seo_title(mock_product, "EBAY_UNKNOWN")

        # Should still produce a title (in English)
        assert "Levi's" in title
        assert len(title) <= 80

    # ========== HELPER METHODS ==========

    @staticmethod
    def _mock_attr(**kwargs):
        """Create a mock attribute model (Color, Category, Gender)."""
        obj = MagicMock()
        for key, value in kwargs.items():
            setattr(obj, key, value)
        return obj

    @staticmethod
    def _mock_condition(name_value: str, lang: str):
        """Create a mock Condition with get_name support."""
        obj = MagicMock()
        obj.get_name.return_value = name_value
        return obj
