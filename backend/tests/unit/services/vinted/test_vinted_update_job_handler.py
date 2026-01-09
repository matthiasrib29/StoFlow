"""
Unit Tests for UpdateJobHandler

Tests for the Vinted update job handler that manages the workflow
of updating existing products on Vinted marketplace.

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
from services.vinted.jobs.update_job_handler import UpdateJobHandler


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_db():
    """Mock SQLAlchemy session."""
    db = MagicMock()
    return db


@pytest.fixture
def mock_job():
    """Mock MarketplaceJob for update action."""
    job = MagicMock(spec=MarketplaceJob)
    job.id = 1
    job.product_id = 100
    job.action_type_id = 2  # update action type
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
    product.title = "Vintage Nike Sweatshirt XL - Updated"
    product.description = "Updated description for the product"
    product.price = Decimal("55.00")  # Updated price
    product.category = "Sweatshirts"
    product.brand = "Nike"
    product.condition = 8
    product.size_normalized = "XL"
    product.gender = "Men"
    product.status = ProductStatus.PUBLISHED
    product.images = [
        {"url": "https://example.com/image1.jpg", "order": 0},
        {"url": "https://example.com/image2.jpg", "order": 1},
    ]
    product.colors = ["Blue", "White"]
    product.materials = ["Cotton"]
    return product


@pytest.fixture
def mock_vinted_product():
    """Mock VintedProduct instance."""
    vp = MagicMock(spec=VintedProduct)
    vp.vinted_id = 12345678
    vp.product_id = 100
    vp.price = Decimal("50.00")  # Original price
    vp.title = "Vintage Nike Sweatshirt XL"
    vp.status = "published"
    vp.url = "https://www.vinted.fr/items/12345678"
    vp.view_count = 150
    vp.favourite_count = 10
    vp.image_ids_list = [1, 2, 3]  # Required for VintedProductConverter
    return vp


@pytest.fixture
def handler(mock_db):
    """Create UpdateJobHandler instance with mocked dependencies."""
    return UpdateJobHandler(db=mock_db, shop_id=123, job_id=1)


# =============================================================================
# TESTS - HANDLER INITIALIZATION
# =============================================================================


class TestUpdateJobHandlerInit:
    """Tests for UpdateJobHandler initialization."""

    def test_init_with_all_params(self, mock_db):
        """Test initialization with all parameters."""
        handler = UpdateJobHandler(db=mock_db, shop_id=123, job_id=1)

        assert handler.db == mock_db
        assert handler.shop_id == 123
        assert handler.job_id == 1
        assert handler.ACTION_CODE == "update"

    def test_init_with_minimal_params(self, mock_db):
        """Test initialization with minimal parameters."""
        handler = UpdateJobHandler(db=mock_db)

        assert handler.db == mock_db
        assert handler.shop_id is None
        assert handler.job_id is None

    def test_init_creates_services(self, mock_db):
        """Test that initialization creates required services."""
        handler = UpdateJobHandler(db=mock_db, shop_id=123)

        assert handler.mapping_service is not None
        assert handler.pricing_service is not None
        assert handler.validator is not None
        assert handler.title_service is not None
        assert handler.description_service is not None


# =============================================================================
# TESTS - EXECUTE METHOD
# =============================================================================


class TestUpdateJobHandlerExecute:
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
    async def test_execute_vinted_product_not_found(self, handler, mock_job, mock_product):
        """Test execute fails when VintedProduct not found."""
        product_query = MagicMock()
        product_query.filter.return_value.first.return_value = mock_product

        vinted_query = MagicMock()
        vinted_query.filter.return_value.first.return_value = None  # VintedProduct not found

        def query_side_effect(model):
            if model == Product:
                return product_query
            elif model == VintedProduct:
                return vinted_query
            return MagicMock()

        handler.db.query.side_effect = query_side_effect

        result = await handler.execute(mock_job)

        assert result["success"] is False
        assert "non publi" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_wrong_vinted_status(self, handler, mock_job, mock_product, mock_vinted_product):
        """Test execute fails when VintedProduct status is not 'published'."""
        mock_vinted_product.status = "sold"  # Wrong status

        product_query = MagicMock()
        product_query.filter.return_value.first.return_value = mock_product

        vinted_query = MagicMock()
        vinted_query.filter.return_value.first.return_value = mock_vinted_product

        def query_side_effect(model):
            if model == Product:
                return product_query
            elif model == VintedProduct:
                return vinted_query
            return MagicMock()

        handler.db.query.side_effect = query_side_effect

        result = await handler.execute(mock_job)

        assert result["success"] is False
        assert "Statut incorrect" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_validation_failure(self, handler, mock_job, mock_product, mock_vinted_product):
        """Test execute fails when product validation fails."""
        product_query = MagicMock()
        product_query.filter.return_value.first.return_value = mock_product

        vinted_query = MagicMock()
        vinted_query.filter.return_value.first.return_value = mock_vinted_product

        def query_side_effect(model):
            if model == Product:
                return product_query
            elif model == VintedProduct:
                return vinted_query
            return MagicMock()

        handler.db.query.side_effect = query_side_effect

        with patch.object(
            handler.validator, 'validate_for_update',
            return_value=(False, "Product in invalid state for update")
        ):
            result = await handler.execute(mock_job)

        assert result["success"] is False
        assert "Validation" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_mapping_failure(self, handler, mock_job, mock_product, mock_vinted_product):
        """Test execute fails when attribute mapping fails."""
        product_query = MagicMock()
        product_query.filter.return_value.first.return_value = mock_product

        vinted_query = MagicMock()
        vinted_query.filter.return_value.first.return_value = mock_vinted_product

        def query_side_effect(model):
            if model == Product:
                return product_query
            elif model == VintedProduct:
                return vinted_query
            return MagicMock()

        handler.db.query.side_effect = query_side_effect

        with patch.object(handler.validator, 'validate_for_update', return_value=(True, None)):
            with patch.object(handler.mapping_service, 'map_all_attributes', return_value={}):
                with patch.object(
                    handler.validator, 'validate_mapped_attributes',
                    return_value=(False, "Invalid category mapping")
                ):
                    result = await handler.execute(mock_job)

        assert result["success"] is False
        assert "Attributs invalides" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_plugin_call_failure(self, handler, mock_job, mock_product, mock_vinted_product):
        """Test execute handles plugin call failure."""
        product_query = MagicMock()
        product_query.filter.return_value.first.return_value = mock_product

        vinted_query = MagicMock()
        vinted_query.filter.return_value.first.return_value = mock_vinted_product

        def query_side_effect(model):
            if model == Product:
                return product_query
            elif model == VintedProduct:
                return vinted_query
            return MagicMock()

        handler.db.query.side_effect = query_side_effect

        with patch.object(handler.validator, 'validate_for_update', return_value=(True, None)):
            with patch.object(
                handler.mapping_service, 'map_all_attributes',
                return_value={"catalog_id": 123}
            ):
                with patch.object(handler.validator, 'validate_mapped_attributes', return_value=(True, None)):
                    with patch.object(handler.pricing_service, 'calculate_vinted_price', return_value=55.0):
                        with patch.object(handler.title_service, 'generate_title', return_value="Test"):
                            with patch.object(handler.description_service, 'generate_description', return_value="Desc"):
                                with patch.object(
                                    handler, 'call_plugin',
                                    new_callable=AsyncMock,
                                    side_effect=Exception("Network timeout")
                                ):
                                    result = await handler.execute(mock_job)

        assert result["success"] is False
        assert "Network timeout" in result["error"]
        handler.db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_success_with_price_change(self, handler, mock_job, mock_product, mock_vinted_product):
        """Test successful execution with price change."""
        product_query = MagicMock()
        product_query.filter.return_value.first.return_value = mock_product

        vinted_query = MagicMock()
        vinted_query.filter.return_value.first.return_value = mock_vinted_product

        def query_side_effect(model):
            if model == Product:
                return product_query
            elif model == VintedProduct:
                return vinted_query
            return MagicMock()

        handler.db.query.side_effect = query_side_effect

        with patch.object(handler.validator, 'validate_for_update', return_value=(True, None)):
            with patch.object(
                handler.mapping_service, 'map_all_attributes',
                return_value={"catalog_id": 123, "brand_id": 456}
            ):
                with patch.object(handler.validator, 'validate_mapped_attributes', return_value=(True, None)):
                    with patch.object(handler.pricing_service, 'calculate_vinted_price', return_value=55.0):
                        with patch.object(handler.title_service, 'generate_title', return_value="Updated Title"):
                            with patch.object(handler.description_service, 'generate_description', return_value="New Desc"):
                                with patch.object(
                                    handler, 'call_plugin',
                                    new_callable=AsyncMock,
                                    return_value={"success": True}
                                ):
                                    result = await handler.execute(mock_job)

        assert result["success"] is True
        assert result["product_id"] == 100
        assert result["old_price"] == 50.0  # Original price from mock_vinted_product
        assert result["new_price"] == 55.0

    @pytest.mark.asyncio
    async def test_execute_success_same_price(self, handler, mock_job, mock_product, mock_vinted_product):
        """Test successful execution when price is the same."""
        mock_vinted_product.price = Decimal("50.00")

        product_query = MagicMock()
        product_query.filter.return_value.first.return_value = mock_product

        vinted_query = MagicMock()
        vinted_query.filter.return_value.first.return_value = mock_vinted_product

        def query_side_effect(model):
            if model == Product:
                return product_query
            elif model == VintedProduct:
                return vinted_query
            return MagicMock()

        handler.db.query.side_effect = query_side_effect

        with patch.object(handler.validator, 'validate_for_update', return_value=(True, None)):
            with patch.object(handler.mapping_service, 'map_all_attributes', return_value={"catalog_id": 123}):
                with patch.object(handler.validator, 'validate_mapped_attributes', return_value=(True, None)):
                    with patch.object(handler.pricing_service, 'calculate_vinted_price', return_value=50.0):
                        with patch.object(handler.title_service, 'generate_title', return_value="Title"):
                            with patch.object(handler.description_service, 'generate_description', return_value="Desc"):
                                with patch.object(
                                    handler, 'call_plugin',
                                    new_callable=AsyncMock,
                                    return_value={"success": True}
                                ):
                                    result = await handler.execute(mock_job)

        # Should still succeed even with identical price
        assert result["success"] is True
        assert result["old_price"] == 50.0
        assert result["new_price"] == 50.0


# =============================================================================
# TESTS - PRIVATE METHODS
# =============================================================================


class TestUpdateJobHandlerPrivateMethods:
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

    def test_get_vinted_product_success(self, handler, mock_vinted_product):
        """Test _get_vinted_product returns vinted product when found."""
        handler.db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        result = handler._get_vinted_product(100)

        assert result == mock_vinted_product

    def test_get_vinted_product_not_found(self, handler):
        """Test _get_vinted_product raises ValueError when not found."""
        handler.db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError) as exc_info:
            handler._get_vinted_product(100)

        assert "non publi" in str(exc_info.value).lower()

    def test_get_vinted_product_wrong_status(self, handler, mock_vinted_product):
        """Test _get_vinted_product raises ValueError for non-published status."""
        mock_vinted_product.status = "sold"
        handler.db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        with pytest.raises(ValueError) as exc_info:
            handler._get_vinted_product(100)

        assert "Statut incorrect" in str(exc_info.value)

    def test_get_vinted_product_draft_status(self, handler, mock_vinted_product):
        """Test _get_vinted_product raises ValueError for draft status."""
        mock_vinted_product.status = "draft"
        handler.db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        with pytest.raises(ValueError) as exc_info:
            handler._get_vinted_product(100)

        assert "Statut incorrect" in str(exc_info.value)

    def test_validate_product_success(self, handler, mock_product):
        """Test _validate_product passes validation."""
        with patch.object(handler.validator, 'validate_for_update', return_value=(True, None)):
            # Should not raise
            handler._validate_product(mock_product)

    def test_validate_product_failure(self, handler, mock_product):
        """Test _validate_product raises on validation failure."""
        with patch.object(
            handler.validator, 'validate_for_update',
            return_value=(False, "Product validation failed")
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
                return_value=(False, "Invalid mapping")
            ):
                with pytest.raises(ValueError) as exc_info:
                    handler._map_attributes(mock_product)

                assert "Attributs invalides" in str(exc_info.value)

    def test_update_vinted_product(self, handler, mock_vinted_product):
        """Test _update_vinted_product updates price and title."""
        handler._update_vinted_product(mock_vinted_product, 65.0, "New Title")

        assert mock_vinted_product.price == Decimal("65.0")
        assert mock_vinted_product.title == "New Title"
        handler.db.commit.assert_called_once()


# =============================================================================
# TESTS - EDGE CASES
# =============================================================================


class TestUpdateJobHandlerEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_execute_with_none_price_in_vinted_product(self, handler, mock_job, mock_product, mock_vinted_product):
        """Test execute handles None price in existing VintedProduct."""
        mock_vinted_product.price = None  # None price

        product_query = MagicMock()
        product_query.filter.return_value.first.return_value = mock_product

        vinted_query = MagicMock()
        vinted_query.filter.return_value.first.return_value = mock_vinted_product

        def query_side_effect(model):
            if model == Product:
                return product_query
            elif model == VintedProduct:
                return vinted_query
            return MagicMock()

        handler.db.query.side_effect = query_side_effect

        with patch.object(handler.validator, 'validate_for_update', return_value=(True, None)):
            with patch.object(handler.mapping_service, 'map_all_attributes', return_value={"catalog_id": 123}):
                with patch.object(handler.validator, 'validate_mapped_attributes', return_value=(True, None)):
                    with patch.object(handler.pricing_service, 'calculate_vinted_price', return_value=55.0):
                        with patch.object(handler.title_service, 'generate_title', return_value="Title"):
                            with patch.object(handler.description_service, 'generate_description', return_value="Desc"):
                                with patch.object(
                                    handler, 'call_plugin',
                                    new_callable=AsyncMock,
                                    return_value={"success": True}
                                ):
                                    result = await handler.execute(mock_job)

        assert result["success"] is True
        assert result["old_price"] == 0.0  # Should default to 0.0

    @pytest.mark.asyncio
    async def test_execute_price_difference_below_threshold(self, handler, mock_job, mock_product, mock_vinted_product):
        """Test execute proceeds when price difference is below 0.01 threshold."""
        mock_vinted_product.price = Decimal("50.005")  # Very close to 50.00

        product_query = MagicMock()
        product_query.filter.return_value.first.return_value = mock_product

        vinted_query = MagicMock()
        vinted_query.filter.return_value.first.return_value = mock_vinted_product

        def query_side_effect(model):
            if model == Product:
                return product_query
            elif model == VintedProduct:
                return vinted_query
            return MagicMock()

        handler.db.query.side_effect = query_side_effect

        with patch.object(handler.validator, 'validate_for_update', return_value=(True, None)):
            with patch.object(handler.mapping_service, 'map_all_attributes', return_value={"catalog_id": 123}):
                with patch.object(handler.validator, 'validate_mapped_attributes', return_value=(True, None)):
                    with patch.object(handler.pricing_service, 'calculate_vinted_price', return_value=50.00):
                        with patch.object(handler.title_service, 'generate_title', return_value="Title"):
                            with patch.object(handler.description_service, 'generate_description', return_value="Desc"):
                                with patch.object(
                                    handler, 'call_plugin',
                                    new_callable=AsyncMock,
                                    return_value={"success": True}
                                ):
                                    result = await handler.execute(mock_job)

        # Should still update even if price is almost identical
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_database_error(self, handler, mock_job):
        """Test execute handles database errors gracefully."""
        handler.db.query.side_effect = Exception("Database connection lost")

        result = await handler.execute(mock_job)

        assert result["success"] is False
        assert "Database connection lost" in result["error"]
        handler.db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_rollback_on_commit_failure(self, handler, mock_job, mock_product, mock_vinted_product):
        """Test that database rollback occurs on commit failure."""
        product_query = MagicMock()
        product_query.filter.return_value.first.return_value = mock_product

        vinted_query = MagicMock()
        vinted_query.filter.return_value.first.return_value = mock_vinted_product

        def query_side_effect(model):
            if model == Product:
                return product_query
            elif model == VintedProduct:
                return vinted_query
            return MagicMock()

        handler.db.query.side_effect = query_side_effect

        with patch.object(handler.validator, 'validate_for_update', return_value=(True, None)):
            with patch.object(handler.mapping_service, 'map_all_attributes', return_value={"catalog_id": 123}):
                with patch.object(handler.validator, 'validate_mapped_attributes', return_value=(True, None)):
                    with patch.object(handler.pricing_service, 'calculate_vinted_price', return_value=55.0):
                        with patch.object(handler.title_service, 'generate_title', return_value="Title"):
                            with patch.object(handler.description_service, 'generate_description', return_value="Desc"):
                                with patch.object(
                                    handler, 'call_plugin',
                                    new_callable=AsyncMock,
                                    return_value={"success": True}
                                ):
                                    # Make commit fail during _update_vinted_product
                                    handler.db.commit.side_effect = Exception("Commit failed")

                                    result = await handler.execute(mock_job)

        assert result["success"] is False
        assert "Commit failed" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_uses_correct_api_path(self, handler, mock_job, mock_product, mock_vinted_product):
        """Test that correct API path is used for update."""
        product_query = MagicMock()
        product_query.filter.return_value.first.return_value = mock_product

        vinted_query = MagicMock()
        vinted_query.filter.return_value.first.return_value = mock_vinted_product

        def query_side_effect(model):
            if model == Product:
                return product_query
            elif model == VintedProduct:
                return vinted_query
            return MagicMock()

        handler.db.query.side_effect = query_side_effect

        call_plugin_mock = AsyncMock(return_value={"success": True})

        with patch.object(handler.validator, 'validate_for_update', return_value=(True, None)):
            with patch.object(handler.mapping_service, 'map_all_attributes', return_value={"catalog_id": 123}):
                with patch.object(handler.validator, 'validate_mapped_attributes', return_value=(True, None)):
                    with patch.object(handler.pricing_service, 'calculate_vinted_price', return_value=55.0):
                        with patch.object(handler.title_service, 'generate_title', return_value="Title"):
                            with patch.object(handler.description_service, 'generate_description', return_value="Desc"):
                                with patch.object(handler, 'call_plugin', call_plugin_mock):
                                    await handler.execute(mock_job)

        # Verify call_plugin was called with PUT method
        call_plugin_mock.assert_called_once()
        call_args = call_plugin_mock.call_args
        assert call_args.kwargs["http_method"] == "PUT"
        assert str(mock_vinted_product.vinted_id) in call_args.kwargs["path"]

    @pytest.mark.asyncio
    async def test_execute_with_deleted_status(self, handler, mock_job, mock_product, mock_vinted_product):
        """Test execute fails when VintedProduct has 'deleted' status."""
        mock_vinted_product.status = "deleted"

        product_query = MagicMock()
        product_query.filter.return_value.first.return_value = mock_product

        vinted_query = MagicMock()
        vinted_query.filter.return_value.first.return_value = mock_vinted_product

        def query_side_effect(model):
            if model == Product:
                return product_query
            elif model == VintedProduct:
                return vinted_query
            return MagicMock()

        handler.db.query.side_effect = query_side_effect

        result = await handler.execute(mock_job)

        assert result["success"] is False
        assert "Statut incorrect" in result["error"]
