"""
Tests for EbayProductConversionService

Tests the product conversion and category auto-resolution.

Author: Claude
Date: 2025-12-22
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from shared.exceptions import ProductValidationError


class TestEbayProductConversionServiceCategoryResolution:
    """Tests for category auto-resolution in create_offer_data."""

    @pytest.fixture
    def mock_product(self):
        """Create a mock product with all required attributes."""
        product = MagicMock()
        product.id = 1
        product.title = "Test Product"
        product.description = "Test description"
        product.price = Decimal("50.00")
        product.condition = 8  # 8 = Excellent
        product.stock_quantity = 1
        product.brand = "TestBrand"
        product.color = "Blue"
        product.size_original = "M"
        product.material = "Cotton"
        product.gender = "men"
        product.fit = None
        product.condition_sup = None
        product.category = "jeans"
        product.images = '["https://example.com/img1.jpg"]'
        return product

    @pytest.fixture
    def mock_service(self):
        """Create a mock service with all dependencies mocked."""
        with patch(
            "services.ebay.ebay_product_conversion_service.EbayProductConversionService.__init__",
            return_value=None
        ):
            from services.ebay.ebay_product_conversion_service import (
                EbayProductConversionService,
            )
            service = EbayProductConversionService.__new__(EbayProductConversionService)
            service.db = MagicMock()
            service.user_id = 1
            service.platform_mapping = MagicMock()
            service.platform_mapping.ebay_price_coefficient_fr = Decimal("1.2")
            service.platform_mapping.ebay_price_fee_fr = Decimal("2.00")
            service._condition_map = {"excellent": "PRE_OWNED_EXCELLENT"}
            return service

    @pytest.fixture
    def mock_marketplace_config(self):
        """Create a mock marketplace config."""
        config = MagicMock()
        config.marketplace_id = "EBAY_FR"
        config.currency = "EUR"
        return config

    def test_create_offer_data_auto_resolves_category(
        self, mock_service, mock_product, mock_marketplace_config
    ):
        """Test that category_id is auto-resolved when not provided."""
        # Setup mock queries
        mock_service.db.query.return_value.filter.return_value.first.return_value = (
            mock_marketplace_config
        )

        with patch(
            "services.ebay.ebay_product_conversion_service.EbayMapper.resolve_ebay_category_id",
            return_value=11483
        ) as mock_resolve:
            result = mock_service.create_offer_data(
                product=mock_product,
                sku_derived="1-FR",
                marketplace_id="EBAY_FR",
                payment_policy_id="pay123",
                fulfillment_policy_id="ful123",
                return_policy_id="ret123",
                inventory_location="warehouse_fr",
                category_id=None,  # Not provided - should auto-resolve
            )

            # Verify category was auto-resolved
            mock_resolve.assert_called_once_with(
                mock_service.db, "jeans", "men"
            )
            assert result["categoryId"] == "11483"

    def test_create_offer_data_uses_provided_category(
        self, mock_service, mock_product, mock_marketplace_config
    ):
        """Test that provided category_id is used when given."""
        mock_service.db.query.return_value.filter.return_value.first.return_value = (
            mock_marketplace_config
        )

        with patch(
            "services.ebay.ebay_product_conversion_service.EbayMapper.resolve_ebay_category_id"
        ) as mock_resolve:
            result = mock_service.create_offer_data(
                product=mock_product,
                sku_derived="1-FR",
                marketplace_id="EBAY_FR",
                payment_policy_id="pay123",
                fulfillment_policy_id="ful123",
                return_policy_id="ret123",
                inventory_location="warehouse_fr",
                category_id="99999",  # Explicitly provided
            )

            # Verify auto-resolve was NOT called
            mock_resolve.assert_not_called()
            assert result["categoryId"] == "99999"

    def test_create_offer_data_raises_error_when_cannot_resolve(
        self, mock_service, mock_product, mock_marketplace_config
    ):
        """Test that error is raised when category cannot be resolved."""
        mock_product.category = "unknown_category"

        mock_service.db.query.return_value.filter.return_value.first.return_value = (
            mock_marketplace_config
        )

        with patch(
            "services.ebay.ebay_product_conversion_service.EbayMapper.resolve_ebay_category_id",
            return_value=None  # Cannot resolve
        ):
            with pytest.raises(ProductValidationError) as exc_info:
                mock_service.create_offer_data(
                    product=mock_product,
                    sku_derived="1-FR",
                    marketplace_id="EBAY_FR",
                    payment_policy_id="pay123",
                    fulfillment_policy_id="ful123",
                    return_policy_id="ret123",
                    inventory_location="warehouse_fr",
                    category_id=None,
                )

            assert "category_id est requis" in str(exc_info.value)
            assert "unknown_category" in str(exc_info.value)

    def test_create_offer_data_raises_error_when_no_category_no_gender(
        self, mock_service, mock_product, mock_marketplace_config
    ):
        """Test error when product has no category or gender for resolution."""
        mock_product.category = None
        mock_product.gender = None

        mock_service.db.query.return_value.filter.return_value.first.return_value = (
            mock_marketplace_config
        )

        with pytest.raises(ProductValidationError) as exc_info:
            mock_service.create_offer_data(
                product=mock_product,
                sku_derived="1-FR",
                marketplace_id="EBAY_FR",
                payment_policy_id="pay123",
                fulfillment_policy_id="ful123",
                return_policy_id="ret123",
                inventory_location="warehouse_fr",
                category_id=None,
            )

        assert "category_id est requis" in str(exc_info.value)

    def test_create_offer_data_logs_auto_resolution(
        self, mock_service, mock_product, mock_marketplace_config
    ):
        """Test that auto-resolution is logged."""
        mock_service.db.query.return_value.filter.return_value.first.return_value = (
            mock_marketplace_config
        )

        with patch(
            "services.ebay.ebay_product_conversion_service.EbayMapper.resolve_ebay_category_id",
            return_value=11483
        ):
            with patch(
                "services.ebay.ebay_product_conversion_service.logger"
            ) as mock_logger:
                mock_service.create_offer_data(
                    product=mock_product,
                    sku_derived="1-FR",
                    marketplace_id="EBAY_FR",
                    payment_policy_id="pay123",
                    fulfillment_policy_id="ful123",
                    return_policy_id="ret123",
                    inventory_location="warehouse_fr",
                    category_id=None,
                )

                # Verify info log was called
                mock_logger.info.assert_called()
                log_message = str(mock_logger.info.call_args)
                assert "Auto-resolved" in log_message or "11483" in log_message
