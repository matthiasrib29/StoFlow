"""
Tests Unitaires pour VintedSyncService

Tests de la logique d'orchestration de synchronisation Vinted.
Utilise des mocks pour la base de donnees et les services externes.

Author: Claude
Date: 2026-01-08
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch, AsyncMock, PropertyMock
import pytest

from models.user.product import ProductStatus


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_db():
    """Mock de la session SQLAlchemy."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    return db


@pytest.fixture
def mock_product():
    """Mock d'un produit Stoflow."""
    from models.user.product import Product, ProductStatus

    product = MagicMock(spec=Product)
    product.id = 123
    product.title = "Jean Levi's 501 Vintage"
    product.description = "Jean vintage en excellent etat"
    product.price = Decimal("45.99")
    product.brand = "Levi's"
    product.category = "Jeans"
    product.condition = 8  # Tres bon etat
    product.size_original = "W32L34"
    product.size_normalized = "M"
    product.gender = "Men"
    product.fit = "Slim"
    product.status = ProductStatus.DRAFT
    product.stock_quantity = 1
    product.images = [
        {"url": "https://cdn.stoflow.com/img1.jpg", "order": 0},
        {"url": "https://cdn.stoflow.com/img2.jpg", "order": 1},
    ]
    product.colors = ["Blue"]
    product.materials = ["Denim"]
    # Legacy color attribute for backward compatibility
    product.color = "Blue"
    product.primary_color = "Blue"
    return product


@pytest.fixture
def mock_vinted_product():
    """Mock d'un VintedProduct existant."""
    from models.user.vinted_product import VintedProduct

    vp = MagicMock(spec=VintedProduct)
    vp.vinted_id = 99999
    vp.product_id = 123
    vp.title = "Jean Levi's 501"
    vp.price = Decimal("45.99")
    vp.status = "published"
    vp.url = "https://www.vinted.fr/items/99999"
    return vp


@pytest.fixture
def mock_mapping_service():
    """Mock du VintedMappingService."""
    service = MagicMock()
    service.map_all_attributes.return_value = {
        "catalog_id": 1193,
        "brand_id": 100,
        "size_id": 50,
        "color_ids": [10],
        "status_id": 2,
    }
    return service


@pytest.fixture
def mock_pricing_service():
    """Mock du VintedPricingService."""
    service = MagicMock()
    service.calculate_vinted_price.return_value = 45.99
    return service


@pytest.fixture
def mock_validator():
    """Mock du VintedProductValidator."""
    validator = MagicMock()
    validator.validate_for_creation.return_value = (True, None)
    validator.validate_for_update.return_value = (True, None)
    validator.validate_mapped_attributes.return_value = (True, None)
    validator.validate_images.return_value = (True, None)
    return validator


@pytest.fixture
def mock_title_service():
    """Mock du VintedTitleService."""
    service = MagicMock()
    service.generate_title.return_value = "Jean Levi's 501 Vintage - W32L34"
    return service


@pytest.fixture
def mock_description_service():
    """Mock du VintedDescriptionService."""
    service = MagicMock()
    service.generate_description.return_value = "Jean vintage en excellent etat. Taille W32L34."
    return service


# =============================================================================
# TESTS - INITIALIZATION
# =============================================================================


class TestVintedSyncServiceInit:
    """Tests pour l'initialisation du service."""

    def test_init_with_shop_id(self):
        """Test initialisation avec shop_id."""
        from services.vinted.vinted_sync_service import VintedSyncService

        service = VintedSyncService(shop_id=123)

        assert service.shop_id == 123
        assert service._api_sync is None
        assert service._order_sync is None

    def test_init_without_shop_id(self):
        """Test initialisation sans shop_id."""
        from services.vinted.vinted_sync_service import VintedSyncService

        service = VintedSyncService()

        assert service.shop_id is None

    def test_api_sync_lazy_load_requires_shop_id(self):
        """Test que api_sync necessite shop_id."""
        from services.vinted.vinted_sync_service import VintedSyncService

        service = VintedSyncService()  # Pas de shop_id

        with pytest.raises(ValueError, match="shop_id requis"):
            _ = service.api_sync

    def test_api_sync_lazy_load_success(self):
        """Test lazy loading de api_sync avec shop_id."""
        from services.vinted.vinted_sync_service import VintedSyncService

        with patch('services.vinted.vinted_sync_service.VintedApiSyncService') as mock_api:
            service = VintedSyncService(shop_id=123)
            _ = service.api_sync

            mock_api.assert_called_once_with(shop_id=123)

    def test_order_sync_lazy_load_success(self):
        """Test lazy loading de order_sync."""
        from services.vinted.vinted_sync_service import VintedSyncService

        with patch('services.vinted.vinted_sync_service.VintedOrderSyncService') as mock_order:
            service = VintedSyncService(shop_id=123)
            _ = service.order_sync

            mock_order.assert_called_once()


# =============================================================================
# TESTS - PUBLISH PRODUCT
# =============================================================================


class TestPublishProduct:
    """Tests pour la publication de produits."""

    @pytest.mark.asyncio
    async def test_publish_product_success(
        self, mock_db, mock_product, mock_mapping_service, mock_pricing_service,
        mock_validator, mock_title_service, mock_description_service
    ):
        """Test publication produit avec succes."""
        from services.vinted.vinted_sync_service import VintedSyncService

        # Setup mock DB
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,  # Product query
            None,  # VintedProduct query (pas encore publie)
        ]

        with patch.multiple(
            'services.vinted.vinted_sync_service',
            VintedMappingService=lambda: mock_mapping_service,
            VintedPricingService=lambda: mock_pricing_service,
            VintedProductValidator=lambda: mock_validator,
            VintedTitleService=lambda: mock_title_service,
            VintedDescriptionService=lambda: mock_description_service,
        ):
            with patch('services.vinted.vinted_sync_service.upload_product_images') as mock_upload:
                mock_upload.return_value = [1001, 1002]

                with patch('services.vinted.vinted_sync_service.VintedProductConverter') as mock_converter:
                    mock_converter.build_create_payload.return_value = {"title": "Test", "price": 45.99}

                    with patch('services.vinted.vinted_sync_service.create_and_wait') as mock_create:
                        mock_create.return_value = {
                            "item": {"id": 99999, "url": "https://vinted.fr/items/99999"}
                        }

                        with patch('services.vinted.vinted_sync_service.save_new_vinted_product') as mock_save:
                            service = VintedSyncService(shop_id=123)
                            service.mapping_service = mock_mapping_service
                            service.pricing_service = mock_pricing_service
                            service.validator = mock_validator
                            service.title_service = mock_title_service
                            service.description_service = mock_description_service

                            result = await service.publish_product(mock_db, product_id=123)

                            assert result["success"] is True
                            assert result["vinted_id"] == 99999
                            assert result["product_id"] == 123
                            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_product_not_found(self, mock_db):
        """Test erreur si produit introuvable."""
        from services.vinted.vinted_sync_service import VintedSyncService

        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = VintedSyncService(shop_id=123)
        result = await service.publish_product(mock_db, product_id=999)

        assert result["success"] is False
        assert "introuvable" in result["error"]

    @pytest.mark.asyncio
    async def test_publish_product_already_published(self, mock_db, mock_product, mock_vinted_product):
        """Test erreur si produit deja publie."""
        from services.vinted.vinted_sync_service import VintedSyncService

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,  # Product query
            mock_vinted_product,  # VintedProduct query (deja publie)
        ]

        service = VintedSyncService(shop_id=123)
        result = await service.publish_product(mock_db, product_id=123)

        assert result["success"] is False
        assert "deja publie" in result["error"]

    @pytest.mark.asyncio
    async def test_publish_product_validation_failed(
        self, mock_db, mock_product, mock_validator
    ):
        """Test erreur si validation echoue."""
        from services.vinted.vinted_sync_service import VintedSyncService

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None,
        ]

        mock_validator.validate_for_creation.return_value = (False, "Missing required field")

        with patch('services.vinted.vinted_sync_service.VintedProductValidator', return_value=mock_validator):
            service = VintedSyncService(shop_id=123)
            service.validator = mock_validator

            result = await service.publish_product(mock_db, product_id=123)

            assert result["success"] is False
            assert "Validation echouee" in result["error"]

    @pytest.mark.asyncio
    async def test_publish_product_mapping_failed(
        self, mock_db, mock_product, mock_validator, mock_mapping_service
    ):
        """Test erreur si mapping attributs echoue."""
        from services.vinted.vinted_sync_service import VintedSyncService

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None,
        ]

        mock_validator.validate_for_creation.return_value = (True, None)
        mock_validator.validate_mapped_attributes.return_value = (False, "Invalid catalog_id")

        with patch('services.vinted.vinted_sync_service.VintedProductValidator', return_value=mock_validator):
            with patch('services.vinted.vinted_sync_service.VintedMappingService', return_value=mock_mapping_service):
                service = VintedSyncService(shop_id=123)
                service.validator = mock_validator
                service.mapping_service = mock_mapping_service

                result = await service.publish_product(mock_db, product_id=123)

                assert result["success"] is False
                assert "Attributs invalides" in result["error"]

    @pytest.mark.asyncio
    async def test_publish_product_image_upload_failed(
        self, mock_db, mock_product, mock_validator, mock_mapping_service, mock_pricing_service
    ):
        """Test erreur si upload images echoue."""
        from services.vinted.vinted_sync_service import VintedSyncService

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None,
        ]

        mock_validator.validate_images.return_value = (False, "No images uploaded")

        with patch('services.vinted.vinted_sync_service.upload_product_images') as mock_upload:
            mock_upload.return_value = []  # Aucune image uploadee

            service = VintedSyncService(shop_id=123)
            service.validator = mock_validator
            service.mapping_service = mock_mapping_service
            service.pricing_service = mock_pricing_service

            result = await service.publish_product(mock_db, product_id=123)

            assert result["success"] is False
            assert "Images invalides" in result["error"]

    @pytest.mark.asyncio
    async def test_publish_product_api_error(
        self, mock_db, mock_product, mock_validator, mock_mapping_service,
        mock_pricing_service, mock_title_service, mock_description_service
    ):
        """Test erreur si API Vinted echoue."""
        from services.vinted.vinted_sync_service import VintedSyncService

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None,
        ]

        with patch('services.vinted.vinted_sync_service.upload_product_images') as mock_upload:
            mock_upload.return_value = [1001, 1002]

            with patch('services.vinted.vinted_sync_service.VintedProductConverter') as mock_converter:
                mock_converter.build_create_payload.return_value = {"title": "Test"}

                with patch('services.vinted.vinted_sync_service.create_and_wait') as mock_create:
                    mock_create.side_effect = Exception("Plugin timeout")

                    service = VintedSyncService(shop_id=123)
                    service.validator = mock_validator
                    service.mapping_service = mock_mapping_service
                    service.pricing_service = mock_pricing_service
                    service.title_service = mock_title_service
                    service.description_service = mock_description_service

                    result = await service.publish_product(mock_db, product_id=123)

                    assert result["success"] is False
                    assert "Plugin timeout" in result["error"]
                    mock_db.rollback.assert_called_once()


# =============================================================================
# TESTS - UPDATE PRODUCT
# =============================================================================


class TestUpdateProduct:
    """Tests pour la mise a jour de produits."""

    @pytest.mark.asyncio
    async def test_update_product_success(
        self, mock_db, mock_product, mock_vinted_product, mock_validator,
        mock_mapping_service, mock_pricing_service, mock_title_service, mock_description_service
    ):
        """Test mise a jour produit avec succes."""
        from services.vinted.vinted_sync_service import VintedSyncService

        # Prix different pour declencher l'update
        mock_pricing_service.calculate_vinted_price.return_value = 39.99

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            mock_vinted_product,
        ]

        with patch('services.vinted.vinted_sync_service.VintedProductConverter') as mock_converter:
            mock_converter.build_update_payload.return_value = {"title": "Updated", "price": 39.99}

            with patch('services.vinted.vinted_sync_service.create_and_wait') as mock_create:
                mock_create.return_value = {"item": {"id": 99999}}

                service = VintedSyncService(shop_id=123)
                service.validator = mock_validator
                service.mapping_service = mock_mapping_service
                service.pricing_service = mock_pricing_service
                service.title_service = mock_title_service
                service.description_service = mock_description_service

                result = await service.update_product(mock_db, product_id=123)

                assert result["success"] is True
                mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_update_product_not_found(self, mock_db):
        """Test erreur si produit introuvable."""
        from services.vinted.vinted_sync_service import VintedSyncService

        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = VintedSyncService(shop_id=123)
        result = await service.update_product(mock_db, product_id=999)

        assert result["success"] is False
        assert "introuvable" in result["error"]

    @pytest.mark.asyncio
    async def test_update_product_not_published(self, mock_db, mock_product):
        """Test erreur si produit non publie sur Vinted."""
        from services.vinted.vinted_sync_service import VintedSyncService

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None,  # Pas de VintedProduct
        ]

        service = VintedSyncService(shop_id=123)
        result = await service.update_product(mock_db, product_id=123)

        assert result["success"] is False
        assert "non publie" in result["error"]

    @pytest.mark.asyncio
    async def test_update_product_wrong_status(self, mock_db, mock_product, mock_vinted_product):
        """Test erreur si statut VintedProduct incorrect."""
        from services.vinted.vinted_sync_service import VintedSyncService

        mock_vinted_product.status = "sold"  # Vendu, pas modifiable

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            mock_vinted_product,
        ]

        service = VintedSyncService(shop_id=123)
        result = await service.update_product(mock_db, product_id=123)

        assert result["success"] is False
        assert "Statut incorrect" in result["error"]

    @pytest.mark.asyncio
    async def test_update_product_same_price_skip(
        self, mock_db, mock_product, mock_vinted_product, mock_validator,
        mock_mapping_service, mock_pricing_service
    ):
        """Test skip update si prix identique."""
        from services.vinted.vinted_sync_service import VintedSyncService

        # Prix identique
        mock_pricing_service.calculate_vinted_price.return_value = 45.99
        mock_vinted_product.price = Decimal("45.99")

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            mock_vinted_product,
        ]

        service = VintedSyncService(shop_id=123)
        service.validator = mock_validator
        service.mapping_service = mock_mapping_service
        service.pricing_service = mock_pricing_service

        result = await service.update_product(mock_db, product_id=123)

        assert result["success"] is False
        assert "Prix identique" in result["error"]


# =============================================================================
# TESTS - DELETE PRODUCT
# =============================================================================


class TestDeleteProduct:
    """Tests pour la suppression de produits."""

    @pytest.mark.asyncio
    async def test_delete_product_success(self, mock_db, mock_vinted_product):
        """Test suppression produit avec succes."""
        from services.vinted.vinted_sync_service import VintedSyncService

        mock_db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        with patch('services.vinted.vinted_sync_service.should_delete_product') as mock_should_delete:
            mock_should_delete.return_value = True

            with patch('services.vinted.vinted_sync_service.create_and_wait') as mock_create:
                mock_create.return_value = {"success": True}

                with patch('services.vinted.vinted_sync_service.VintedDeletion') as mock_deletion:
                    mock_deletion.from_vinted_product.return_value = MagicMock()

                    service = VintedSyncService(shop_id=123)
                    result = await service.delete_product(mock_db, product_id=123)

                    assert result["success"] is True
                    mock_db.delete.assert_called_once_with(mock_vinted_product)
                    mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_delete_product_not_found(self, mock_db):
        """Test erreur si produit Vinted introuvable."""
        from services.vinted.vinted_sync_service import VintedSyncService

        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = VintedSyncService(shop_id=123)
        result = await service.delete_product(mock_db, product_id=999)

        assert result["success"] is False
        assert "non trouve" in result["error"]

    @pytest.mark.asyncio
    async def test_delete_product_conditions_not_met(self, mock_db, mock_vinted_product):
        """Test skip si conditions de suppression non remplies."""
        from services.vinted.vinted_sync_service import VintedSyncService

        mock_db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        with patch('services.vinted.vinted_sync_service.should_delete_product') as mock_should_delete:
            mock_should_delete.return_value = False

            service = VintedSyncService(shop_id=123)
            result = await service.delete_product(mock_db, product_id=123, check_conditions=True)

            assert result["success"] is False
            assert "Conditions non remplies" in result["error"]

    @pytest.mark.asyncio
    async def test_delete_product_skip_conditions_check(self, mock_db, mock_vinted_product):
        """Test suppression forcee sans verification conditions."""
        from services.vinted.vinted_sync_service import VintedSyncService

        mock_db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        with patch('services.vinted.vinted_sync_service.create_and_wait') as mock_create:
            mock_create.return_value = {"success": True}

            with patch('services.vinted.vinted_sync_service.VintedDeletion') as mock_deletion:
                mock_deletion.from_vinted_product.return_value = MagicMock()

                service = VintedSyncService(shop_id=123)
                result = await service.delete_product(
                    mock_db, product_id=123, check_conditions=False
                )

                assert result["success"] is True

    @pytest.mark.asyncio
    async def test_delete_product_api_error(self, mock_db, mock_vinted_product):
        """Test erreur si API Vinted echoue."""
        from services.vinted.vinted_sync_service import VintedSyncService

        mock_db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        with patch('services.vinted.vinted_sync_service.should_delete_product') as mock_should_delete:
            mock_should_delete.return_value = True

            with patch('services.vinted.vinted_sync_service.VintedDeletion') as mock_deletion:
                mock_deletion.from_vinted_product.return_value = MagicMock()

                with patch('services.vinted.vinted_sync_service.create_and_wait') as mock_create:
                    mock_create.side_effect = Exception("API Error")

                    service = VintedSyncService(shop_id=123)
                    result = await service.delete_product(mock_db, product_id=123)

                    assert result["success"] is False
                    assert "API Error" in result["error"]
                    mock_db.rollback.assert_called_once()


# =============================================================================
# TESTS - DELEGATION METHODS
# =============================================================================


class TestDelegationMethods:
    """Tests pour les methodes de delegation."""

    @pytest.mark.asyncio
    async def test_sync_products_from_api_delegates(self, mock_db):
        """Test delegation sync_products_from_api."""
        from services.vinted.vinted_sync_service import VintedSyncService

        with patch('services.vinted.vinted_sync_service.VintedApiSyncService') as mock_api_class:
            mock_api_instance = AsyncMock()
            mock_api_instance.sync_products_from_api.return_value = {"synced": 10}
            mock_api_class.return_value = mock_api_instance

            service = VintedSyncService(shop_id=123)
            result = await service.sync_products_from_api(mock_db)

            assert result == {"synced": 10}
            mock_api_instance.sync_products_from_api.assert_called_once_with(mock_db)

    @pytest.mark.asyncio
    async def test_sync_orders_delegates(self, mock_db):
        """Test delegation sync_orders."""
        from services.vinted.vinted_sync_service import VintedSyncService

        with patch('services.vinted.vinted_sync_service.VintedOrderSyncService') as mock_order_class:
            mock_order_instance = AsyncMock()
            mock_order_instance.sync_orders.return_value = {"orders_synced": 5}
            mock_order_class.return_value = mock_order_instance

            service = VintedSyncService(shop_id=123)
            result = await service.sync_orders(mock_db, duplicate_threshold=0.8, per_page=20)

            assert result == {"orders_synced": 5}
            mock_order_instance.sync_orders.assert_called_once_with(mock_db, 0.8, 20)

    @pytest.mark.asyncio
    async def test_sync_orders_by_month_delegates(self, mock_db):
        """Test delegation sync_orders_by_month."""
        from services.vinted.vinted_sync_service import VintedSyncService

        with patch('services.vinted.vinted_sync_service.VintedOrderSyncService') as mock_order_class:
            mock_order_instance = AsyncMock()
            mock_order_instance.sync_orders_by_month.return_value = {"orders_synced": 3}
            mock_order_class.return_value = mock_order_instance

            service = VintedSyncService(shop_id=123)
            result = await service.sync_orders_by_month(mock_db, year=2025, month=12)

            assert result == {"orders_synced": 3}
            mock_order_instance.sync_orders_by_month.assert_called_once_with(mock_db, 2025, 12)


# =============================================================================
# TESTS - ERROR HANDLING & ROLLBACK
# =============================================================================


class TestErrorHandlingAndRollback:
    """Tests pour la gestion des erreurs et rollback."""

    @pytest.mark.asyncio
    async def test_publish_product_rollback_on_exception(self, mock_db, mock_product):
        """Test rollback si exception pendant publication."""
        from services.vinted.vinted_sync_service import VintedSyncService

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None,
        ]

        mock_validator = MagicMock()
        mock_validator.validate_for_creation.side_effect = Exception("Unexpected error")

        with patch('services.vinted.vinted_sync_service.VintedProductValidator', return_value=mock_validator):
            service = VintedSyncService(shop_id=123)
            service.validator = mock_validator

            result = await service.publish_product(mock_db, product_id=123)

            assert result["success"] is False
            mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_product_rollback_on_exception(self, mock_db, mock_product, mock_vinted_product):
        """Test rollback si exception pendant update."""
        from services.vinted.vinted_sync_service import VintedSyncService

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            mock_vinted_product,
        ]

        mock_validator = MagicMock()
        mock_validator.validate_for_update.side_effect = Exception("Update error")

        service = VintedSyncService(shop_id=123)
        service.validator = mock_validator

        result = await service.update_product(mock_db, product_id=123)

        assert result["success"] is False
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_product_rollback_on_exception(self, mock_db, mock_vinted_product):
        """Test rollback si exception pendant suppression."""
        from services.vinted.vinted_sync_service import VintedSyncService

        mock_db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        with patch('services.vinted.vinted_sync_service.should_delete_product') as mock_should_delete:
            mock_should_delete.return_value = True

            with patch('services.vinted.vinted_sync_service.VintedDeletion') as mock_deletion:
                mock_deletion.from_vinted_product.side_effect = Exception("Deletion error")

                service = VintedSyncService(shop_id=123)
                result = await service.delete_product(mock_db, product_id=123)

                assert result["success"] is False
                mock_db.rollback.assert_called_once()


# =============================================================================
# TESTS - PRODUCT STATUS UPDATE
# =============================================================================


class TestProductStatusUpdate:
    """Tests pour la mise a jour du statut produit."""

    @pytest.mark.asyncio
    async def test_publish_product_updates_status_to_published(
        self, mock_db, mock_product, mock_validator, mock_mapping_service,
        mock_pricing_service, mock_title_service, mock_description_service
    ):
        """Test que publish_product met a jour le status a PUBLISHED."""
        from services.vinted.vinted_sync_service import VintedSyncService

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None,
        ]

        with patch('services.vinted.vinted_sync_service.upload_product_images') as mock_upload:
            mock_upload.return_value = [1001]

            with patch('services.vinted.vinted_sync_service.VintedProductConverter') as mock_converter:
                mock_converter.build_create_payload.return_value = {"title": "Test"}

                with patch('services.vinted.vinted_sync_service.create_and_wait') as mock_create:
                    mock_create.return_value = {"item": {"id": 99999, "url": "https://vinted.fr/items/99999"}}

                    with patch('services.vinted.vinted_sync_service.save_new_vinted_product'):
                        service = VintedSyncService(shop_id=123)
                        service.validator = mock_validator
                        service.mapping_service = mock_mapping_service
                        service.pricing_service = mock_pricing_service
                        service.title_service = mock_title_service
                        service.description_service = mock_description_service

                        await service.publish_product(mock_db, product_id=123)

                        # Verifier que le status a ete mis a jour
                        assert mock_product.status == ProductStatus.PUBLISHED
