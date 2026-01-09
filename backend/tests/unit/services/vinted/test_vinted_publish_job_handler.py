"""
Unit Tests for PublishJobHandler

Tests for the Vinted publish job handler that manages the complete workflow
of publishing products to Vinted marketplace.

Author: Claude
Date: 2026-01-08
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from models.user.product import Product, ProductStatus
from models.user.vinted_product import VintedProduct
from models.user.marketplace_job import JobStatus, MarketplaceJob
from services.vinted.jobs.publish_job_handler import PublishJobHandler


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_db():
    """Mock SQLAlchemy session."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    return db


@pytest.fixture
def mock_job():
    """Mock MarketplaceJob for publish action."""
    job = MagicMock(spec=MarketplaceJob)
    job.id = 1
    job.product_id = 100
    job.action_type_id = 1
    job.status = JobStatus.PENDING
    job.priority = 3
    job.retry_count = 0
    job.batch_id = None
    job.result_data = None
    job.created_at = datetime.now(timezone.utc)
    return job


@pytest.fixture
def mock_product():
    """Mock Product instance."""
    product = MagicMock(spec=Product)
    product.id = 100
    product.title = "Vintage Nike Sweatshirt XL"
    product.description = "Beautiful vintage Nike sweatshirt in great condition"
    product.price = Decimal("45.00")
    product.category = "Sweatshirts"
    product.brand = "Nike"
    product.condition = 8
    product.size_normalized = "XL"
    product.gender = "Men"
    product.status = ProductStatus.DRAFT
    product.images = [
        {"url": "https://example.com/image1.jpg", "order": 0},
        {"url": "https://example.com/image2.jpg", "order": 1},
    ]
    product.colors = ["Blue", "White"]
    product.materials = ["Cotton"]
    return product


@pytest.fixture
def handler(mock_db):
    """Create PublishJobHandler instance with mocked dependencies."""
    return PublishJobHandler(db=mock_db, shop_id=123, job_id=1)


# =============================================================================
# TESTS - HANDLER INITIALIZATION
# =============================================================================


class TestPublishJobHandlerInit:
    """Tests for PublishJobHandler initialization."""

    def test_init_with_all_params(self, mock_db):
        """Test initialization with all parameters."""
        handler = PublishJobHandler(db=mock_db, shop_id=123, job_id=1)

        assert handler.db == mock_db
        assert handler.shop_id == 123
        assert handler.job_id == 1
        assert handler.ACTION_CODE == "publish"

    def test_init_with_minimal_params(self, mock_db):
        """Test initialization with minimal parameters."""
        handler = PublishJobHandler(db=mock_db)

        assert handler.db == mock_db
        assert handler.shop_id is None
        assert handler.job_id is None

    def test_init_creates_services(self, mock_db):
        """Test that initialization creates required services."""
        handler = PublishJobHandler(db=mock_db, shop_id=123)

        assert handler.mapping_service is not None
        assert handler.pricing_service is not None
        assert handler.validator is not None
        assert handler.title_service is not None
        assert handler.description_service is not None


# =============================================================================
# TESTS - EXECUTE METHOD
# =============================================================================


class TestPublishJobHandlerExecute:
    """Tests for execute method."""

    @pytest.mark.asyncio
    async def test_execute_missing_product_id(self, handler):
        """Test execute fails when product_id is missing."""
        job = MagicMock(spec=MarketplaceJob)
        job.product_id = None

        result = await handler.execute(job)

        assert result["success"] is False
        assert "product_id required" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_product_not_found(self, handler, mock_job):
        """Test execute fails when product not found in database."""
        handler.db.query.return_value.filter.return_value.first.return_value = None

        result = await handler.execute(mock_job)

        assert result["success"] is False
        assert result["product_id"] == 100
        assert "introuvable" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_already_published(self, handler, mock_job, mock_product):
        """Test execute fails when product is already published on Vinted."""
        # Mock for Product and VintedProduct queries
        existing_vinted = MagicMock(spec=VintedProduct)
        existing_vinted.vinted_id = 999

        # Create separate mock chains for Product and VintedProduct queries
        product_query = MagicMock()
        product_query.filter.return_value.first.return_value = mock_product

        vinted_query = MagicMock()
        vinted_query.filter.return_value.first.return_value = existing_vinted

        def query_side_effect(model):
            if model == Product:
                return product_query
            elif model == VintedProduct:
                return vinted_query
            return MagicMock()

        handler.db.query.side_effect = query_side_effect

        # check_not_already_published is called after get_product, before validation
        result = await handler.execute(mock_job)

        assert result["success"] is False
        # Message contains "déjà publié" with French accents
        assert "publi" in result["error"].lower() or "already" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_validation_failure(self, handler, mock_job, mock_product):
        """Test execute fails when product validation fails."""
        # Create separate mock chains for Product and VintedProduct queries
        product_query = MagicMock()
        product_query.filter.return_value.first.return_value = mock_product

        vinted_query = MagicMock()
        vinted_query.filter.return_value.first.return_value = None  # Not already published

        def query_side_effect(model):
            if model == Product:
                return product_query
            elif model == VintedProduct:
                return vinted_query
            return MagicMock()

        handler.db.query.side_effect = query_side_effect

        with patch.object(
            handler.validator, 'validate_for_creation',
            return_value=(False, "Missing required field: category")
        ):
            result = await handler.execute(mock_job)

        assert result["success"] is False
        assert "Validation" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_mapping_failure(self, handler, mock_job, mock_product):
        """Test execute fails when attribute mapping fails."""
        product_query = MagicMock()
        product_query.filter.return_value.first.return_value = mock_product

        vinted_query = MagicMock()
        vinted_query.filter.return_value.first.return_value = None

        def query_side_effect(model):
            if model == Product:
                return product_query
            elif model == VintedProduct:
                return vinted_query
            return MagicMock()

        handler.db.query.side_effect = query_side_effect

        with patch.object(handler.validator, 'validate_for_creation', return_value=(True, None)):
            with patch.object(
                handler.mapping_service, 'map_all_attributes',
                return_value={"catalog_id": None}  # Invalid mapping
            ):
                with patch.object(
                    handler.validator, 'validate_mapped_attributes',
                    return_value=(False, "catalog_id is required")
                ):
                    result = await handler.execute(mock_job)

        assert result["success"] is False
        assert "Attributs invalides" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_image_upload_failure(self, handler, mock_job, mock_product):
        """Test execute fails when image upload fails."""
        product_query = MagicMock()
        product_query.filter.return_value.first.return_value = mock_product

        vinted_query = MagicMock()
        vinted_query.filter.return_value.first.return_value = None

        def query_side_effect(model):
            if model == Product:
                return product_query
            elif model == VintedProduct:
                return vinted_query
            return MagicMock()

        handler.db.query.side_effect = query_side_effect

        with patch.object(handler.validator, 'validate_for_creation', return_value=(True, None)):
            with patch.object(
                handler.mapping_service, 'map_all_attributes',
                return_value={"catalog_id": 123, "brand_id": 456}
            ):
                with patch.object(
                    handler.validator, 'validate_mapped_attributes',
                    return_value=(True, None)
                ):
                    with patch.object(handler.pricing_service, 'calculate_vinted_price', return_value=50.0):
                        with patch.object(handler.title_service, 'generate_title', return_value="Test Title"):
                            with patch.object(
                                handler.description_service, 'generate_description',
                                return_value="Test Description"
                            ):
                                with patch(
                                    'services.vinted.jobs.publish_job_handler.upload_product_images',
                                    new_callable=AsyncMock,
                                    return_value=[]  # Empty = failure
                                ):
                                    with patch.object(
                                        handler.validator, 'validate_images',
                                        return_value=(False, "At least 1 image required")
                                    ):
                                        result = await handler.execute(mock_job)

        assert result["success"] is False
        assert "Images invalides" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_plugin_call_failure(self, handler, mock_job, mock_product):
        """Test execute handles plugin call failure."""
        product_query = MagicMock()
        product_query.filter.return_value.first.return_value = mock_product

        vinted_query = MagicMock()
        vinted_query.filter.return_value.first.return_value = None

        def query_side_effect(model):
            if model == Product:
                return product_query
            elif model == VintedProduct:
                return vinted_query
            return MagicMock()

        handler.db.query.side_effect = query_side_effect

        with patch.object(handler.validator, 'validate_for_creation', return_value=(True, None)):
            with patch.object(
                handler.mapping_service, 'map_all_attributes',
                return_value={"catalog_id": 123}
            ):
                with patch.object(handler.validator, 'validate_mapped_attributes', return_value=(True, None)):
                    with patch.object(handler.pricing_service, 'calculate_vinted_price', return_value=50.0):
                        with patch.object(handler.title_service, 'generate_title', return_value="Test"):
                            with patch.object(handler.description_service, 'generate_description', return_value="Desc"):
                                with patch(
                                    'services.vinted.jobs.publish_job_handler.upload_product_images',
                                    new_callable=AsyncMock,
                                    return_value=[1, 2, 3]
                                ):
                                    with patch.object(handler.validator, 'validate_images', return_value=(True, None)):
                                        with patch(
                                            'services.vinted.jobs.publish_job_handler.VintedProductConverter.build_create_payload',
                                            return_value={"title": "Test", "price": 50.0}
                                        ):
                                            with patch.object(
                                                handler, 'call_plugin',
                                                new_callable=AsyncMock,
                                                side_effect=Exception("Plugin timeout")
                                            ):
                                                result = await handler.execute(mock_job)

        assert result["success"] is False
        assert "Plugin timeout" in result["error"]
        handler.db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_success_full_workflow(self, handler, mock_job, mock_product):
        """Test successful execution of complete publish workflow."""
        product_query = MagicMock()
        product_query.filter.return_value.first.return_value = mock_product

        vinted_query = MagicMock()
        vinted_query.filter.return_value.first.return_value = None  # Not already published

        def query_side_effect(model):
            if model == Product:
                return product_query
            elif model == VintedProduct:
                return vinted_query
            return MagicMock()

        handler.db.query.side_effect = query_side_effect

        plugin_response = {
            "item": {
                "id": 12345678,
                "url": "https://www.vinted.fr/items/12345678",
                "title": "Test Product"
            }
        }

        with patch.object(handler.validator, 'validate_for_creation', return_value=(True, None)):
            with patch.object(
                handler.mapping_service, 'map_all_attributes',
                return_value={"catalog_id": 123, "brand_id": 456, "size_id": 789}
            ):
                with patch.object(handler.validator, 'validate_mapped_attributes', return_value=(True, None)):
                    with patch.object(handler.pricing_service, 'calculate_vinted_price', return_value=50.0):
                        with patch.object(handler.title_service, 'generate_title', return_value="Test Title"):
                            with patch.object(handler.description_service, 'generate_description', return_value="Desc"):
                                with patch(
                                    'services.vinted.jobs.publish_job_handler.upload_product_images',
                                    new_callable=AsyncMock,
                                    return_value=[1, 2, 3]
                                ):
                                    with patch.object(handler.validator, 'validate_images', return_value=(True, None)):
                                        with patch(
                                            'services.vinted.jobs.publish_job_handler.VintedProductConverter.build_create_payload',
                                            return_value={"title": "Test Title", "price": 50.0}
                                        ):
                                            with patch.object(
                                                handler, 'call_plugin',
                                                new_callable=AsyncMock,
                                                return_value=plugin_response
                                            ):
                                                with patch(
                                                    'services.vinted.jobs.publish_job_handler.save_new_vinted_product'
                                                ) as mock_save:
                                                    result = await handler.execute(mock_job)

        assert result["success"] is True
        assert result["vinted_id"] == 12345678
        assert result["url"] == "https://www.vinted.fr/items/12345678"
        assert result["product_id"] == 100
        assert result["price"] == 50.0
        mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_missing_vinted_id_in_response(self, handler, mock_job, mock_product):
        """Test execute fails when vinted_id is missing from response."""
        product_query = MagicMock()
        product_query.filter.return_value.first.return_value = mock_product

        vinted_query = MagicMock()
        vinted_query.filter.return_value.first.return_value = None

        def query_side_effect(model):
            if model == Product:
                return product_query
            elif model == VintedProduct:
                return vinted_query
            return MagicMock()

        handler.db.query.side_effect = query_side_effect

        # Response without vinted_id
        plugin_response = {"item": {"url": "https://vinted.fr/items/123"}}

        with patch.object(handler.validator, 'validate_for_creation', return_value=(True, None)):
            with patch.object(handler.mapping_service, 'map_all_attributes', return_value={"catalog_id": 123}):
                with patch.object(handler.validator, 'validate_mapped_attributes', return_value=(True, None)):
                    with patch.object(handler.pricing_service, 'calculate_vinted_price', return_value=50.0):
                        with patch.object(handler.title_service, 'generate_title', return_value="Test"):
                            with patch.object(handler.description_service, 'generate_description', return_value="Desc"):
                                with patch(
                                    'services.vinted.jobs.publish_job_handler.upload_product_images',
                                    new_callable=AsyncMock,
                                    return_value=[1, 2]
                                ):
                                    with patch.object(handler.validator, 'validate_images', return_value=(True, None)):
                                        with patch(
                                            'services.vinted.jobs.publish_job_handler.VintedProductConverter.build_create_payload',
                                            return_value={"title": "Test", "price": 50.0}
                                        ):
                                            with patch.object(
                                                handler, 'call_plugin',
                                                new_callable=AsyncMock,
                                                return_value=plugin_response
                                            ):
                                                result = await handler.execute(mock_job)

        assert result["success"] is False
        assert "vinted_id manquant" in result["error"]


# =============================================================================
# TESTS - PRIVATE METHODS
# =============================================================================


class TestPublishJobHandlerPrivateMethods:
    """Tests for private helper methods."""

    def test_get_product_success(self, handler, mock_product):
        """Test _get_product returns product when found."""
        handler.db.query.return_value.filter.return_value.first.return_value = mock_product

        result = handler._get_product(100)

        assert result == mock_product

    def test_get_product_not_found(self, handler):
        """Test _get_product raises ValueError when not found."""
        handler.db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError) as exc_info:
            handler._get_product(999)

        assert "introuvable" in str(exc_info.value)

    def test_check_not_already_published_success(self, handler):
        """Test _check_not_already_published passes when not published."""
        handler.db.query.return_value.filter.return_value.first.return_value = None

        # Should not raise
        handler._check_not_already_published(100)

    def test_check_not_already_published_raises(self, handler):
        """Test _check_not_already_published raises when already published."""
        existing = MagicMock(spec=VintedProduct)
        existing.vinted_id = 12345
        handler.db.query.return_value.filter.return_value.first.return_value = existing

        with pytest.raises(ValueError) as exc_info:
            handler._check_not_already_published(100)

        assert "deja publie" in str(exc_info.value).lower() or "12345" in str(exc_info.value)

    def test_validate_product_success(self, handler, mock_product):
        """Test _validate_product passes validation."""
        with patch.object(handler.validator, 'validate_for_creation', return_value=(True, None)):
            # Should not raise
            handler._validate_product(mock_product)

    def test_validate_product_failure(self, handler, mock_product):
        """Test _validate_product raises on validation failure."""
        with patch.object(
            handler.validator, 'validate_for_creation',
            return_value=(False, "Missing category")
        ):
            with pytest.raises(ValueError) as exc_info:
                handler._validate_product(mock_product)

            assert "Validation" in str(exc_info.value)

    def test_map_attributes_success(self, handler, mock_product):
        """Test _map_attributes returns mapped attributes."""
        mapped = {"catalog_id": 123, "brand_id": 456}

        with patch.object(handler.mapping_service, 'map_all_attributes', return_value=mapped):
            with patch.object(handler.validator, 'validate_mapped_attributes', return_value=(True, None)):
                result = handler._map_attributes(mock_product)

        assert result == mapped

    def test_map_attributes_invalid(self, handler, mock_product):
        """Test _map_attributes raises on invalid mapping."""
        with patch.object(handler.mapping_service, 'map_all_attributes', return_value={}):
            with patch.object(
                handler.validator, 'validate_mapped_attributes',
                return_value=(False, "catalog_id required")
            ):
                with pytest.raises(ValueError) as exc_info:
                    handler._map_attributes(mock_product)

                assert "Attributs invalides" in str(exc_info.value)

    def test_calculate_price(self, handler, mock_product):
        """Test _calculate_price returns calculated price."""
        with patch.object(handler.pricing_service, 'calculate_vinted_price', return_value=55.0):
            result = handler._calculate_price(mock_product)

        assert result == 55.0

    @pytest.mark.asyncio
    async def test_upload_images_success(self, handler, mock_product):
        """Test _upload_images uploads images successfully."""
        with patch(
            'services.vinted.jobs.publish_job_handler.upload_product_images',
            new_callable=AsyncMock,
            return_value=[1, 2, 3]
        ):
            with patch.object(handler.validator, 'validate_images', return_value=(True, None)):
                result = await handler._upload_images(mock_product)

        assert result == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_upload_images_validation_failure(self, handler, mock_product):
        """Test _upload_images raises on validation failure."""
        with patch(
            'services.vinted.jobs.publish_job_handler.upload_product_images',
            new_callable=AsyncMock,
            return_value=[]
        ):
            with patch.object(
                handler.validator, 'validate_images',
                return_value=(False, "No images uploaded")
            ):
                with pytest.raises(ValueError) as exc_info:
                    await handler._upload_images(mock_product)

                assert "Images invalides" in str(exc_info.value)

    def test_update_product_status(self, handler, mock_product):
        """Test _update_product_status updates product to PUBLISHED."""
        handler._update_product_status(mock_product)

        assert mock_product.status == ProductStatus.PUBLISHED
        handler.db.commit.assert_called_once()


# =============================================================================
# TESTS - EDGE CASES
# =============================================================================


class TestPublishJobHandlerEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_execute_with_empty_title_product(self, handler, mock_job):
        """Test execute handles product with None/empty title."""
        product = MagicMock(spec=Product)
        product.id = 100
        product.title = None  # Empty title

        handler.db.query.return_value.filter.return_value.first.side_effect = [
            product,
            None
        ]

        # Should handle None title gracefully in logging
        with patch.object(handler.validator, 'validate_for_creation', return_value=(False, "Title required")):
            result = await handler.execute(mock_job)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_execute_database_error(self, handler, mock_job):
        """Test execute handles database errors gracefully."""
        handler.db.query.side_effect = Exception("Database connection lost")

        result = await handler.execute(mock_job)

        assert result["success"] is False
        assert "Database connection lost" in result["error"]
        handler.db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_flat_response(self, handler, mock_job, mock_product):
        """Test execute handles flat response (without 'item' wrapper)."""
        product_query = MagicMock()
        product_query.filter.return_value.first.return_value = mock_product

        vinted_query = MagicMock()
        vinted_query.filter.return_value.first.return_value = None

        def query_side_effect(model):
            if model == Product:
                return product_query
            elif model == VintedProduct:
                return vinted_query
            return MagicMock()

        handler.db.query.side_effect = query_side_effect

        # Flat response without 'item' wrapper
        flat_response = {
            "id": 12345678,
            "url": "https://www.vinted.fr/items/12345678"
        }

        with patch.object(handler.validator, 'validate_for_creation', return_value=(True, None)):
            with patch.object(handler.mapping_service, 'map_all_attributes', return_value={"catalog_id": 123}):
                with patch.object(handler.validator, 'validate_mapped_attributes', return_value=(True, None)):
                    with patch.object(handler.pricing_service, 'calculate_vinted_price', return_value=50.0):
                        with patch.object(handler.title_service, 'generate_title', return_value="Test"):
                            with patch.object(handler.description_service, 'generate_description', return_value="Desc"):
                                with patch(
                                    'services.vinted.jobs.publish_job_handler.upload_product_images',
                                    new_callable=AsyncMock,
                                    return_value=[1]
                                ):
                                    with patch.object(handler.validator, 'validate_images', return_value=(True, None)):
                                        with patch(
                                            'services.vinted.jobs.publish_job_handler.VintedProductConverter.build_create_payload',
                                            return_value={"title": "Test", "price": 50.0}
                                        ):
                                            with patch.object(
                                                handler, 'call_plugin',
                                                new_callable=AsyncMock,
                                                return_value=flat_response
                                            ):
                                                with patch(
                                                    'services.vinted.jobs.publish_job_handler.save_new_vinted_product'
                                                ):
                                                    result = await handler.execute(mock_job)

        assert result["success"] is True
        assert result["vinted_id"] == 12345678

    @pytest.mark.asyncio
    async def test_execute_rollback_on_exception(self, handler, mock_job, mock_product):
        """Test that database is rolled back on exception."""
        handler.db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None
        ]

        with patch.object(handler.validator, 'validate_for_creation', side_effect=RuntimeError("Unexpected error")):
            result = await handler.execute(mock_job)

        assert result["success"] is False
        handler.db.rollback.assert_called_once()
