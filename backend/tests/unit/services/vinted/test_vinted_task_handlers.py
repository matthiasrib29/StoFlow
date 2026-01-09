"""
Tests Unitaires pour VintedTaskHandler

Tests de la logique de post-processing des taches Vinted.
Utilise des mocks pour la base de donnees.

Note: Ce module est marque DEPRECATED mais est conserve pour retrocompatibilite.

Author: Claude
Date: 2026-01-08
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest

from models.user.product import ProductStatus
from models.user.plugin_task import TaskStatus


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_db():
    """Mock de la session SQLAlchemy."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
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
    product.status = ProductStatus.DRAFT
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
    vp.set_image_ids = MagicMock()
    return vp


@pytest.fixture
def mock_plugin_task():
    """Mock d'une PluginTask."""
    from models.user.plugin_task import PluginTask, TaskStatus

    task = MagicMock(spec=PluginTask)
    task.id = 1
    task.task_type = "vinted_publish"
    task.status = TaskStatus.SUCCESS
    task.payload = {"product_id": 123}
    task.result = None
    return task


@pytest.fixture
def mock_publish_result():
    """Mock du resultat de publication."""
    return {
        "status": "success",
        "data": {
            "id": 99999,
            "url": "https://www.vinted.fr/items/99999",
            "photos": [
                {"id": 1001, "url": "https://cdn.vinted.fr/1001.jpg"},
                {"id": 1002, "url": "https://cdn.vinted.fr/1002.jpg"},
            ],
            "price_numeric": 45.99,
        }
    }


# =============================================================================
# TESTS - HANDLE VINTED PUBLISH
# =============================================================================


class TestHandleVintedPublish:
    """Tests pour le handler VINTED_PUBLISH."""

    def test_publish_creates_new_vinted_product(
        self, mock_db, mock_plugin_task, mock_product, mock_publish_result
    ):
        """Test creation d'un nouveau VintedProduct apres publication."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.payload = {"product_id": 123}

        # Pas de VintedProduct existant
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,  # Product query
            None,  # VintedProduct query
        ]

        # Mock VintedProduct class to avoid SQLAlchemy validation
        with patch('services.vinted.vinted_task_handlers.VintedProduct') as MockVP:
            mock_new_vp = MagicMock()
            mock_new_vp.set_image_ids = MagicMock()
            MockVP.return_value = mock_new_vp

            result = VintedTaskHandler.handle_vinted_publish(
                mock_db, mock_plugin_task, mock_publish_result
            )

            assert result["product_id"] == 123
            assert result["vinted_id"] == 99999
            assert result["status"] == "published"
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    def test_publish_updates_existing_vinted_product(
        self, mock_db, mock_plugin_task, mock_product, mock_vinted_product, mock_publish_result
    ):
        """Test mise a jour d'un VintedProduct existant."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.payload = {"product_id": 123}

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            mock_vinted_product,  # VintedProduct existe deja
        ]

        result = VintedTaskHandler.handle_vinted_publish(
            mock_db, mock_plugin_task, mock_publish_result
        )

        assert result["vinted_id"] == 99999
        assert mock_vinted_product.vinted_id == 99999
        assert mock_vinted_product.status == "published"
        mock_vinted_product.set_image_ids.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_publish_updates_product_status(
        self, mock_db, mock_plugin_task, mock_product, mock_publish_result
    ):
        """Test mise a jour du status Product a PUBLISHED."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None,
        ]

        # Mock VintedProduct class to avoid SQLAlchemy validation
        with patch('services.vinted.vinted_task_handlers.VintedProduct') as MockVP:
            mock_new_vp = MagicMock()
            mock_new_vp.set_image_ids = MagicMock()
            MockVP.return_value = mock_new_vp

            VintedTaskHandler.handle_vinted_publish(
                mock_db, mock_plugin_task, mock_publish_result
            )

            assert mock_product.status == ProductStatus.PUBLISHED

    def test_publish_missing_product_id_raises_error(
        self, mock_db, mock_plugin_task, mock_publish_result
    ):
        """Test erreur si product_id manquant dans payload."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.payload = {}  # Pas de product_id

        with pytest.raises(ValueError, match="product_id manquant"):
            VintedTaskHandler.handle_vinted_publish(
                mock_db, mock_plugin_task, mock_publish_result
            )

    def test_publish_product_not_found_raises_error(
        self, mock_db, mock_plugin_task, mock_publish_result
    ):
        """Test erreur si produit introuvable."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.payload = {"product_id": 999}
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="introuvable"):
            VintedTaskHandler.handle_vinted_publish(
                mock_db, mock_plugin_task, mock_publish_result
            )

    def test_publish_missing_vinted_id_raises_error(
        self, mock_db, mock_plugin_task, mock_product
    ):
        """Test erreur si vinted_id manquant dans resultat."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.payload = {"product_id": 123}
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None,
        ]

        result_without_id = {"status": "success", "data": {"url": "https://vinted.fr"}}

        with pytest.raises(ValueError, match="vinted_id manquant"):
            VintedTaskHandler.handle_vinted_publish(
                mock_db, mock_plugin_task, result_without_id
            )


# =============================================================================
# TESTS - HANDLE VINTED UPDATE PRICE
# =============================================================================


class TestHandleVintedUpdatePrice:
    """Tests pour le handler VINTED_UPDATE_PRICE."""

    def test_update_price_success(self, mock_db, mock_plugin_task, mock_vinted_product):
        """Test mise a jour prix avec succes."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.task_type = "vinted_update_price"
        mock_plugin_task.payload = {"product_id": 123, "new_price": 39.99}

        mock_db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        result = VintedTaskHandler.handle_vinted_update_price(
            mock_db, mock_plugin_task, {"status": "success"}
        )

        assert result["product_id"] == 123
        assert result["old_price"] == 45.99
        assert result["new_price"] == 39.99
        assert mock_vinted_product.price == 39.99
        mock_db.commit.assert_called_once()

    def test_update_price_missing_product_id_raises_error(self, mock_db, mock_plugin_task):
        """Test erreur si product_id manquant."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.payload = {"new_price": 39.99}  # Pas de product_id

        with pytest.raises(ValueError, match="product_id ou new_price manquant"):
            VintedTaskHandler.handle_vinted_update_price(
                mock_db, mock_plugin_task, {}
            )

    def test_update_price_missing_new_price_raises_error(self, mock_db, mock_plugin_task):
        """Test erreur si new_price manquant."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.payload = {"product_id": 123}  # Pas de new_price

        with pytest.raises(ValueError, match="product_id ou new_price manquant"):
            VintedTaskHandler.handle_vinted_update_price(
                mock_db, mock_plugin_task, {}
            )

    def test_update_price_vinted_product_not_found_raises_error(
        self, mock_db, mock_plugin_task
    ):
        """Test erreur si VintedProduct introuvable."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.payload = {"product_id": 999, "new_price": 39.99}
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="VintedProduct introuvable"):
            VintedTaskHandler.handle_vinted_update_price(
                mock_db, mock_plugin_task, {}
            )


# =============================================================================
# TESTS - HANDLE VINTED UPDATE STOCK
# =============================================================================


class TestHandleVintedUpdateStock:
    """Tests pour le handler VINTED_UPDATE_STOCK."""

    def test_update_stock_available_true(self, mock_db, mock_plugin_task, mock_vinted_product):
        """Test mise a jour stock avec available=True."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.task_type = "vinted_update_stock"
        mock_plugin_task.payload = {"product_id": 123, "available": True}

        mock_db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        result = VintedTaskHandler.handle_vinted_update_stock(
            mock_db, mock_plugin_task, {"status": "success"}
        )

        assert result["available"] is True
        assert mock_vinted_product.status == "published"
        mock_db.commit.assert_called_once()

    def test_update_stock_available_false(self, mock_db, mock_plugin_task, mock_vinted_product):
        """Test mise a jour stock avec available=False (archive)."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.task_type = "vinted_update_stock"
        mock_plugin_task.payload = {"product_id": 123, "available": False}

        mock_db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        result = VintedTaskHandler.handle_vinted_update_stock(
            mock_db, mock_plugin_task, {"status": "success"}
        )

        assert result["available"] is False
        assert mock_vinted_product.status == "archived"

    def test_update_stock_missing_available_raises_error(self, mock_db, mock_plugin_task):
        """Test erreur si available manquant."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.payload = {"product_id": 123}  # Pas de available

        with pytest.raises(ValueError, match="available manquant"):
            VintedTaskHandler.handle_vinted_update_stock(
                mock_db, mock_plugin_task, {}
            )


# =============================================================================
# TESTS - HANDLE VINTED DELETE
# =============================================================================


class TestHandleVintedDelete:
    """Tests pour le handler VINTED_DELETE."""

    def test_delete_success(self, mock_db, mock_plugin_task, mock_product, mock_vinted_product):
        """Test suppression avec succes."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.task_type = "vinted_delete"
        mock_plugin_task.payload = {"product_id": 123}

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_vinted_product,  # VintedProduct query
            mock_product,  # Product query
        ]

        result = VintedTaskHandler.handle_vinted_delete(
            mock_db, mock_plugin_task, {"status": "success"}
        )

        assert result["vinted_id"] == 99999
        assert result["status"] == "deleted"
        assert mock_vinted_product.status == "deleted"
        assert mock_product.status == ProductStatus.ARCHIVED
        mock_db.commit.assert_called_once()

    def test_delete_missing_product_id_raises_error(self, mock_db, mock_plugin_task):
        """Test erreur si product_id manquant."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.payload = {}

        with pytest.raises(ValueError, match="product_id manquant"):
            VintedTaskHandler.handle_vinted_delete(
                mock_db, mock_plugin_task, {}
            )

    def test_delete_vinted_product_not_found_raises_error(self, mock_db, mock_plugin_task):
        """Test erreur si VintedProduct introuvable."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.payload = {"product_id": 999}
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="VintedProduct introuvable"):
            VintedTaskHandler.handle_vinted_delete(
                mock_db, mock_plugin_task, {}
            )

    def test_delete_without_product_succeeds(self, mock_db, mock_plugin_task, mock_vinted_product):
        """Test suppression quand Product n'existe pas (orphelin)."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.payload = {"product_id": 123}

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_vinted_product,  # VintedProduct existe
            None,  # Product n'existe pas
        ]

        result = VintedTaskHandler.handle_vinted_delete(
            mock_db, mock_plugin_task, {"status": "success"}
        )

        # La suppression doit reussir meme sans Product
        assert result["status"] == "deleted"
        mock_db.commit.assert_called_once()


# =============================================================================
# TESTS - HANDLE VINTED UPDATE DETAILS
# =============================================================================


class TestHandleVintedUpdateDetails:
    """Tests pour le handler VINTED_UPDATE_DETAILS."""

    def test_update_details_title_success(self, mock_db, mock_plugin_task, mock_vinted_product):
        """Test mise a jour du titre."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.task_type = "vinted_update_details"
        mock_plugin_task.payload = {
            "product_id": 123,
            "update_data": {"title": "New Title"}
        }

        mock_db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        result = VintedTaskHandler.handle_vinted_update_details(
            mock_db, mock_plugin_task, {"status": "success", "data": {}}
        )

        assert "title" in result["updated_fields"]
        assert mock_vinted_product.title == "New Title"
        mock_db.commit.assert_called_once()

    def test_update_details_photos_success(self, mock_db, mock_plugin_task, mock_vinted_product):
        """Test mise a jour des photos."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.task_type = "vinted_update_details"
        mock_plugin_task.payload = {"product_id": 123, "update_data": {}}

        mock_db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        result_with_photos = {
            "status": "success",
            "data": {
                "photos": [
                    {"id": 2001, "url": "https://cdn.vinted.fr/2001.jpg"},
                    {"id": 2002, "url": "https://cdn.vinted.fr/2002.jpg"},
                ]
            }
        }

        result = VintedTaskHandler.handle_vinted_update_details(
            mock_db, mock_plugin_task, result_with_photos
        )

        assert "photos" in result["updated_fields"]
        mock_vinted_product.set_image_ids.assert_called_once_with([2001, 2002])

    def test_update_details_missing_product_id_raises_error(self, mock_db, mock_plugin_task):
        """Test erreur si product_id manquant."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.payload = {"update_data": {}}

        with pytest.raises(ValueError, match="product_id manquant"):
            VintedTaskHandler.handle_vinted_update_details(
                mock_db, mock_plugin_task, {}
            )


# =============================================================================
# TESTS - ROUTE TASK HANDLER
# =============================================================================


class TestRouteTaskHandler:
    """Tests pour le routeur de handlers."""

    def test_route_to_publish_handler(self, mock_db, mock_plugin_task, mock_product, mock_publish_result):
        """Test routage vers handler publish."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.task_type = "vinted_publish"
        mock_plugin_task.payload = {"product_id": 123}

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None,
        ]

        # Mock VintedProduct class to avoid SQLAlchemy validation
        with patch('services.vinted.vinted_task_handlers.VintedProduct') as MockVP:
            mock_new_vp = MagicMock()
            mock_new_vp.set_image_ids = MagicMock()
            MockVP.return_value = mock_new_vp

            result = VintedTaskHandler.route_task_handler(
                mock_db, mock_plugin_task, mock_publish_result
            )

            assert result["vinted_id"] == 99999
            assert result["status"] == "published"

    def test_route_to_update_price_handler(self, mock_db, mock_plugin_task, mock_vinted_product):
        """Test routage vers handler update_price."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.task_type = "vinted_update_price"
        mock_plugin_task.payload = {"product_id": 123, "new_price": 39.99}

        mock_db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        result = VintedTaskHandler.route_task_handler(
            mock_db, mock_plugin_task, {"status": "success"}
        )

        assert result["new_price"] == 39.99

    def test_route_to_update_stock_handler(self, mock_db, mock_plugin_task, mock_vinted_product):
        """Test routage vers handler update_stock."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.task_type = "vinted_update_stock"
        mock_plugin_task.payload = {"product_id": 123, "available": True}

        mock_db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        result = VintedTaskHandler.route_task_handler(
            mock_db, mock_plugin_task, {"status": "success"}
        )

        assert result["available"] is True

    def test_route_to_update_details_handler(self, mock_db, mock_plugin_task, mock_vinted_product):
        """Test routage vers handler update_details."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.task_type = "vinted_update_details"
        mock_plugin_task.payload = {"product_id": 123, "update_data": {"title": "New"}}

        mock_db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        result = VintedTaskHandler.route_task_handler(
            mock_db, mock_plugin_task, {"status": "success", "data": {}}
        )

        assert "updated_fields" in result

    def test_route_to_delete_handler(
        self, mock_db, mock_plugin_task, mock_product, mock_vinted_product
    ):
        """Test routage vers handler delete."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.task_type = "vinted_delete"
        mock_plugin_task.payload = {"product_id": 123}

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_vinted_product,
            mock_product,
        ]

        result = VintedTaskHandler.route_task_handler(
            mock_db, mock_plugin_task, {"status": "success"}
        )

        assert result["status"] == "deleted"

    def test_route_unknown_task_type_returns_default(self, mock_db, mock_plugin_task):
        """Test routage type inconnu retourne message par defaut."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.task_type = "unknown_task"
        mock_plugin_task.id = 42

        result = VintedTaskHandler.route_task_handler(
            mock_db, mock_plugin_task, {"status": "success"}
        )

        assert result["task_id"] == 42
        assert "pas de post-processing" in result["message"]

    def test_route_handler_exception_rollback(
        self, mock_db, mock_plugin_task, mock_publish_result
    ):
        """Test rollback si handler leve une exception."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.task_type = "vinted_publish"
        mock_plugin_task.payload = {"product_id": 123}

        # Simuler erreur dans le handler
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError):
            VintedTaskHandler.route_task_handler(
                mock_db, mock_plugin_task, mock_publish_result
            )

        mock_db.rollback.assert_called_once()


# =============================================================================
# TESTS - EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Tests pour les cas limites."""

    def test_publish_with_empty_photos(self, mock_db, mock_plugin_task, mock_product):
        """Test publication avec liste photos vide."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.payload = {"product_id": 123}

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None,
        ]

        result_empty_photos = {
            "status": "success",
            "data": {
                "id": 99999,
                "url": "https://vinted.fr/items/99999",
                "photos": [],  # Liste vide
            }
        }

        # Mock VintedProduct class to avoid SQLAlchemy validation
        with patch('services.vinted.vinted_task_handlers.VintedProduct') as MockVP:
            mock_new_vp = MagicMock()
            mock_new_vp.set_image_ids = MagicMock()
            MockVP.return_value = mock_new_vp

            result = VintedTaskHandler.handle_vinted_publish(
                mock_db, mock_plugin_task, result_empty_photos
            )

            assert result["vinted_id"] == 99999

    def test_publish_photos_missing_id_field(self, mock_db, mock_plugin_task, mock_product):
        """Test publication avec photos sans champ id."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.payload = {"product_id": 123}

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None,
        ]

        result_photos_no_id = {
            "status": "success",
            "data": {
                "id": 99999,
                "url": "https://vinted.fr/items/99999",
                "photos": [
                    {"url": "https://cdn.vinted.fr/1.jpg"},  # Pas de champ 'id'
                    {"id": 1002, "url": "https://cdn.vinted.fr/2.jpg"},  # Avec id
                ],
            }
        }

        # Mock VintedProduct class to avoid SQLAlchemy validation
        with patch('services.vinted.vinted_task_handlers.VintedProduct') as MockVP:
            mock_new_vp = MagicMock()
            mock_new_vp.set_image_ids = MagicMock()
            MockVP.return_value = mock_new_vp

            result = VintedTaskHandler.handle_vinted_publish(
                mock_db, mock_plugin_task, result_photos_no_id
            )

            # Doit filtrer les photos sans id
            assert result["vinted_id"] == 99999

    def test_update_price_with_zero_price(self, mock_db, mock_plugin_task, mock_vinted_product):
        """Test mise a jour prix a zero (cas limite)."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.payload = {"product_id": 123, "new_price": 0}

        mock_db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        result = VintedTaskHandler.handle_vinted_update_price(
            mock_db, mock_plugin_task, {"status": "success"}
        )

        assert result["new_price"] == 0
        assert mock_vinted_product.price == 0

    def test_update_stock_with_none_available(self, mock_db, mock_plugin_task):
        """Test update stock avec available=None leve erreur."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.payload = {"product_id": 123, "available": None}

        with pytest.raises(ValueError, match="available manquant"):
            VintedTaskHandler.handle_vinted_update_stock(
                mock_db, mock_plugin_task, {}
            )

    def test_update_details_empty_update_data(self, mock_db, mock_plugin_task, mock_vinted_product):
        """Test update details avec update_data vide."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.payload = {"product_id": 123, "update_data": {}}

        mock_db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        result = VintedTaskHandler.handle_vinted_update_details(
            mock_db, mock_plugin_task, {"status": "success", "data": {}}
        )

        # Doit reussir sans mettre a jour de champs
        assert result["updated_fields"] == []


# =============================================================================
# TESTS - LOGGING
# =============================================================================


class TestLogging:
    """Tests pour le logging."""

    def test_publish_logs_success(self, mock_db, mock_plugin_task, mock_product, mock_publish_result):
        """Test que publish log le succes."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.payload = {"product_id": 123}

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None,
        ]

        with patch('services.vinted.vinted_task_handlers.logger') as mock_logger:
            # Mock VintedProduct class to avoid SQLAlchemy validation
            with patch('services.vinted.vinted_task_handlers.VintedProduct') as MockVP:
                mock_new_vp = MagicMock()
                mock_new_vp.set_image_ids = MagicMock()
                MockVP.return_value = mock_new_vp

                VintedTaskHandler.handle_vinted_publish(
                    mock_db, mock_plugin_task, mock_publish_result
                )

                # Verifier qu'au moins un log info a ete appele
                assert mock_logger.info.called

    def test_route_handler_logs_task_type(self, mock_db, mock_plugin_task, mock_vinted_product):
        """Test que route_task_handler log le task_type."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.task_type = "vinted_update_price"
        mock_plugin_task.payload = {"product_id": 123, "new_price": 39.99}
        mock_plugin_task.id = 42

        mock_db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        with patch('services.vinted.vinted_task_handlers.logger') as mock_logger:
            VintedTaskHandler.route_task_handler(
                mock_db, mock_plugin_task, {"status": "success"}
            )

            # Verifier que le task_type est mentionne dans les logs
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            assert any("vinted_update_price" in call for call in log_calls)


# =============================================================================
# TESTS - DATE HANDLING
# =============================================================================


class TestDateHandling:
    """Tests pour la gestion des dates."""

    def test_publish_sets_date_to_today(self, mock_db, mock_plugin_task, mock_product, mock_publish_result):
        """Test que publish appelle VintedProduct avec date = today."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.payload = {"product_id": 123}

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            None,
        ]

        # Mock VintedProduct class to capture the call arguments
        with patch('services.vinted.vinted_task_handlers.VintedProduct') as MockVP:
            mock_new_vp = MagicMock()
            mock_new_vp.set_image_ids = MagicMock()
            MockVP.return_value = mock_new_vp

            VintedTaskHandler.handle_vinted_publish(
                mock_db, mock_plugin_task, mock_publish_result
            )

            # Verifier que VintedProduct a ete appele avec date = today
            call_kwargs = MockVP.call_args[1]
            assert call_kwargs.get("date") == date.today()

    def test_publish_existing_updates_date(
        self, mock_db, mock_plugin_task, mock_product, mock_vinted_product, mock_publish_result
    ):
        """Test que publish met a jour date sur VintedProduct existant."""
        from services.vinted.vinted_task_handlers import VintedTaskHandler

        mock_plugin_task.payload = {"product_id": 123}

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_product,
            mock_vinted_product,
        ]

        VintedTaskHandler.handle_vinted_publish(
            mock_db, mock_plugin_task, mock_publish_result
        )

        assert mock_vinted_product.date == date.today()
