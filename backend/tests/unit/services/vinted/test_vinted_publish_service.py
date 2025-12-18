"""
Tests unitaires pour VintedPublishService.

Couverture:
- publish_product: validation, mapping, upload photos, création produit
- Gestion des erreurs et rollback
- Post-processing (création VintedProduct)

Author: Claude
Date: 2025-12-18
"""

import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from services.vinted.vinted_publish_service import VintedPublishService
from models.user.product import ProductStatus


class TestVintedPublishServiceInit:
    """Tests pour l'initialisation du service."""

    def test_init_creates_helper(self):
        """Test que l'init crée un PluginTaskHelper."""
        with patch('services.vinted.vinted_publish_service.PluginTaskHelper') as mock_helper:
            service = VintedPublishService()
            mock_helper.assert_called_once()
            assert service.helper is not None


class TestPublishProductValidation:
    """Tests pour la validation dans publish_product."""

    @pytest.mark.asyncio
    async def test_publish_product_not_found(self):
        """Test erreur si produit non trouvé."""
        service = VintedPublishService()
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="introuvable"):
            await service.publish_product(mock_db, product_id=999)

    @pytest.mark.asyncio
    async def test_publish_product_already_published(self):
        """Test erreur si produit déjà publié sur Vinted."""
        service = VintedPublishService()
        mock_db = Mock()

        # Product exists
        mock_product = Mock()
        mock_product.id = 1
        mock_product.title = "Test Product"

        # VintedProduct already exists
        mock_vinted_product = Mock()
        mock_vinted_product.vinted_id = 123456

        # Configure query to return product, then vinted_product
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            mock_vinted_product
        ]

        with pytest.raises(ValueError, match="déjà publié"):
            await service.publish_product(mock_db, product_id=1)

    @pytest.mark.asyncio
    async def test_publish_product_missing_title(self):
        """Test erreur si titre manquant."""
        service = VintedPublishService()
        mock_db = Mock()

        mock_product = Mock()
        mock_product.id = 1
        mock_product.title = ""  # Empty title

        # Product found, no VintedProduct
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None  # No existing VintedProduct
        ]

        with pytest.raises(ValueError, match="Titre manquant"):
            await service.publish_product(mock_db, product_id=1)

    @pytest.mark.asyncio
    async def test_publish_product_invalid_price_zero(self):
        """Test erreur si prix = 0."""
        service = VintedPublishService()
        mock_db = Mock()

        mock_product = Mock()
        mock_product.id = 1
        mock_product.title = "Test Product"
        mock_product.price = Decimal("0")

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None
        ]

        with pytest.raises(ValueError, match="Prix invalide"):
            await service.publish_product(mock_db, product_id=1)

    @pytest.mark.asyncio
    async def test_publish_product_invalid_price_negative(self):
        """Test erreur si prix négatif."""
        service = VintedPublishService()
        mock_db = Mock()

        mock_product = Mock()
        mock_product.id = 1
        mock_product.title = "Test Product"
        mock_product.price = Decimal("-10")

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None
        ]

        with pytest.raises(ValueError, match="Prix invalide"):
            await service.publish_product(mock_db, product_id=1)

    @pytest.mark.asyncio
    async def test_publish_product_price_none(self):
        """Test erreur si prix None."""
        service = VintedPublishService()
        mock_db = Mock()

        mock_product = Mock()
        mock_product.id = 1
        mock_product.title = "Test Product"
        mock_product.price = None

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None
        ]

        with pytest.raises(ValueError, match="Prix invalide"):
            await service.publish_product(mock_db, product_id=1)


class TestPublishProductSuccess:
    """Tests pour le flux de publication réussi."""

    @pytest.mark.asyncio
    @patch('services.vinted.vinted_publish_service.VintedProduct')
    @patch('services.vinted.vinted_publish_service.create_and_wait')
    async def test_publish_product_success_full_flow(self, mock_create_wait, mock_vinted_product_class):
        """Test publication complète réussie."""
        service = VintedPublishService()
        mock_db = Mock()

        # Mock product
        mock_product = Mock()
        mock_product.id = 1
        mock_product.title = "Test Product for Vinted"
        mock_product.description = "Great condition"
        mock_product.price = Decimal("49.99")

        # Mock queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,  # Product found
            None           # No existing VintedProduct
        ]

        # Mock VintedProduct instance
        mock_vinted_product = Mock()
        mock_vinted_product_class.return_value = mock_vinted_product

        # Mock create_and_wait responses
        # 3 photo uploads + 1 product creation
        mock_create_wait.side_effect = [
            {"id": 1001},  # Photo 1
            {"id": 1002},  # Photo 2
            {"id": 1003},  # Photo 3
            {"id": 987654, "url": "https://vinted.fr/items/987654"}  # Product
        ]

        result = await service.publish_product(mock_db, product_id=1)

        # Verify result
        assert result["success"] is True
        assert result["vinted_id"] == 987654
        assert result["url"] == "https://vinted.fr/items/987654"
        assert result["product_id"] == 1
        assert result["photos_count"] == 3

        # Verify db.add was called (VintedProduct created)
        assert mock_db.add.called
        assert mock_db.commit.called

        # Verify product status was updated
        assert mock_product.status == ProductStatus.PUBLISHED

    @pytest.mark.asyncio
    @patch('services.vinted.vinted_publish_service.VintedProduct')
    @patch('services.vinted.vinted_publish_service.create_and_wait')
    async def test_publish_product_price_calculation(self, mock_create_wait, mock_vinted_product_class):
        """Test que le prix Vinted est calculé correctement (prix - 10%)."""
        service = VintedPublishService()
        mock_db = Mock()

        mock_product = Mock()
        mock_product.id = 1
        mock_product.title = "Test Product"
        mock_product.description = "Description"
        mock_product.price = Decimal("100.00")  # Prix = 100€

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None
        ]

        mock_vinted_product_class.return_value = Mock()

        mock_create_wait.side_effect = [
            {"id": 1001},
            {"id": 1002},
            {"id": 1003},
            {"id": 123, "url": "https://vinted.fr/items/123"}
        ]

        result = await service.publish_product(mock_db, product_id=1)

        # Prix Vinted = 100 * 0.9 = 90€
        assert result["price"] == 90.0


class TestPublishProductErrors:
    """Tests pour la gestion des erreurs."""

    @pytest.mark.asyncio
    @patch('services.vinted.vinted_publish_service.create_and_wait')
    async def test_publish_product_photo_upload_fails(self, mock_create_wait):
        """Test erreur si upload photo échoue (pas d'ID)."""
        service = VintedPublishService()
        mock_db = Mock()

        mock_product = Mock()
        mock_product.id = 1
        mock_product.title = "Test Product"
        mock_product.price = Decimal("50.00")

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None
        ]

        # Photo upload returns no ID
        mock_create_wait.return_value = {"error": "upload failed"}

        with pytest.raises(Exception, match="ID manquant"):
            await service.publish_product(mock_db, product_id=1)

        # Verify rollback was called
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    @patch('services.vinted.vinted_publish_service.create_and_wait')
    async def test_publish_product_creation_fails(self, mock_create_wait):
        """Test erreur si création produit Vinted échoue."""
        service = VintedPublishService()
        mock_db = Mock()

        mock_product = Mock()
        mock_product.id = 1
        mock_product.title = "Test Product"
        mock_product.price = Decimal("50.00")

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None
        ]

        # Photo uploads succeed, product creation fails
        mock_create_wait.side_effect = [
            {"id": 1001},
            {"id": 1002},
            {"id": 1003},
            {"error": "creation failed"}  # No vinted_id
        ]

        with pytest.raises(Exception, match="vinted_id manquant"):
            await service.publish_product(mock_db, product_id=1)

        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    @patch('services.vinted.vinted_publish_service.create_and_wait')
    async def test_publish_product_exception_triggers_rollback(self, mock_create_wait):
        """Test que toute exception déclenche un rollback."""
        service = VintedPublishService()
        mock_db = Mock()

        mock_product = Mock()
        mock_product.id = 1
        mock_product.title = "Test Product"
        mock_product.price = Decimal("50.00")

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None
        ]

        # Simulate network error
        mock_create_wait.side_effect = Exception("Network error")

        with pytest.raises(Exception, match="Network error"):
            await service.publish_product(mock_db, product_id=1)

        mock_db.rollback.assert_called_once()


class TestPublishProductApiCalls:
    """Tests pour les appels API via create_and_wait."""

    @pytest.mark.asyncio
    @patch('services.vinted.vinted_publish_service.VintedProduct')
    @patch('services.vinted.vinted_publish_service.create_and_wait')
    async def test_photo_upload_api_call_format(self, mock_create_wait, mock_vinted_product_class):
        """Test format des appels API pour upload photo."""
        service = VintedPublishService()
        mock_db = Mock()

        mock_product = Mock()
        mock_product.id = 1
        mock_product.title = "Test"
        mock_product.description = "Desc"
        mock_product.price = Decimal("50.00")

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None
        ]

        mock_vinted_product_class.return_value = Mock()

        mock_create_wait.side_effect = [
            {"id": 1},
            {"id": 2},
            {"id": 3},
            {"id": 100, "url": "https://vinted.fr/items/100"}
        ]

        await service.publish_product(mock_db, product_id=1)

        # Verify first photo upload call
        first_call = mock_create_wait.call_args_list[0]
        assert first_call.kwargs["http_method"] == "POST"
        assert "photos" in first_call.kwargs["path"]
        assert first_call.kwargs["platform"] == "vinted"
        assert first_call.kwargs["product_id"] == 1

    @pytest.mark.asyncio
    @patch('services.vinted.vinted_publish_service.VintedProduct')
    @patch('services.vinted.vinted_publish_service.create_and_wait')
    async def test_product_creation_api_call_format(self, mock_create_wait, mock_vinted_product_class):
        """Test format de l'appel API création produit."""
        service = VintedPublishService()
        mock_db = Mock()

        mock_product = Mock()
        mock_product.id = 1
        mock_product.title = "My Product Title"
        mock_product.description = "Product description"
        mock_product.price = Decimal("75.00")

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None
        ]

        mock_vinted_product_class.return_value = Mock()

        mock_create_wait.side_effect = [
            {"id": 1},
            {"id": 2},
            {"id": 3},
            {"id": 555, "url": "https://vinted.fr/items/555"}
        ]

        await service.publish_product(mock_db, product_id=1)

        # Verify product creation call (4th call)
        creation_call = mock_create_wait.call_args_list[3]
        assert creation_call.kwargs["http_method"] == "POST"
        assert "items" in creation_call.kwargs["path"]
        assert creation_call.kwargs["platform"] == "vinted"

        # Check payload contains expected data
        payload = creation_call.kwargs["payload"]["body"]
        assert payload["title"] == "My Product Title"
        assert payload["description"] == "Product description"
        assert payload["photo_ids"] == [1, 2, 3]
        assert payload["currency"] == "EUR"
