"""
Tests unitaires pour VintedTaskHandler.

Couverture:
- handle_task_result: dispatch vers le bon handler selon task_type
- _handle_publish_result: succès et échec publication
- _handle_update_result: succès et échec mise à jour
- _handle_delete_result: succès et échec suppression

Author: Claude
Date: 2025-12-18
"""

import pytest
from datetime import date
from unittest.mock import Mock, patch, MagicMock

from services.vinted.vinted_task_handler import VintedTaskHandler


class TestHandleTaskResultDispatch:
    """Tests pour le dispatch de handle_task_result."""

    @patch.object(VintedTaskHandler, '_handle_publish_result')
    def test_dispatch_vinted_publish(self, mock_handler):
        """Test dispatch vers _handle_publish_result."""
        mock_db = Mock()
        mock_task = Mock()
        mock_task.task_type = "vinted_publish"

        VintedTaskHandler.handle_task_result(mock_db, mock_task)

        mock_handler.assert_called_once_with(mock_db, mock_task)

    @patch.object(VintedTaskHandler, '_handle_update_result')
    def test_dispatch_vinted_update(self, mock_handler):
        """Test dispatch vers _handle_update_result."""
        mock_db = Mock()
        mock_task = Mock()
        mock_task.task_type = "vinted_update"

        VintedTaskHandler.handle_task_result(mock_db, mock_task)

        mock_handler.assert_called_once_with(mock_db, mock_task)

    @patch.object(VintedTaskHandler, '_handle_delete_result')
    def test_dispatch_vinted_delete(self, mock_handler):
        """Test dispatch vers _handle_delete_result."""
        mock_db = Mock()
        mock_task = Mock()
        mock_task.task_type = "vinted_delete"

        VintedTaskHandler.handle_task_result(mock_db, mock_task)

        mock_handler.assert_called_once_with(mock_db, mock_task)

    def test_dispatch_unknown_type_logs_warning(self):
        """Test que les types inconnus sont logués."""
        mock_db = Mock()
        mock_task = Mock()
        mock_task.task_type = "unknown_type"

        with patch('services.vinted.vinted_task_handler.logger') as mock_logger:
            VintedTaskHandler.handle_task_result(mock_db, mock_task)
            mock_logger.warning.assert_called_once()
            assert "non géré" in str(mock_logger.warning.call_args)


class TestHandlePublishResult:
    """Tests pour _handle_publish_result."""

    @patch('services.vinted.vinted_task_handler.VintedProductRepository')
    def test_publish_success_updates_vinted_product(self, mock_repo):
        """Test que succès publication met à jour VintedProduct."""
        mock_db = Mock()
        mock_task = Mock()
        mock_task.id = 1
        mock_task.task_type = "vinted_publish"
        mock_task.product_id = 100
        mock_task.payload = {"vinted_product_id": 50}
        mock_task.status.value = "success"
        mock_task.result = {
            "vinted_id": 987654,
            "url": "https://vinted.fr/items/987654",
            "image_ids": "123,456,789"
        }

        mock_vinted_product = Mock()
        mock_repo.get_by_id.return_value = mock_vinted_product

        VintedTaskHandler._handle_publish_result(mock_db, mock_task)

        # Verify updates
        assert mock_vinted_product.vinted_id == 987654
        assert mock_vinted_product.url == "https://vinted.fr/items/987654"
        assert mock_vinted_product.image_ids == "123,456,789"
        assert mock_vinted_product.status == "published"
        mock_db.commit.assert_called_once()

    @patch('services.vinted.vinted_task_handler.VintedProductRepository')
    def test_publish_success_sets_date(self, mock_repo):
        """Test que succès publication définit la date."""
        mock_db = Mock()
        mock_task = Mock()
        mock_task.id = 1
        mock_task.payload = {"vinted_product_id": 50}
        mock_task.status.value = "success"
        mock_task.result = {"vinted_id": 123}
        mock_task.product_id = 100

        mock_vinted_product = Mock()
        mock_repo.get_by_id.return_value = mock_vinted_product

        VintedTaskHandler._handle_publish_result(mock_db, mock_task)

        assert mock_vinted_product.date == date.today()

    @patch('services.vinted.vinted_task_handler.VintedErrorLogRepository')
    @patch('services.vinted.vinted_task_handler.VintedProductRepository')
    def test_publish_failure_creates_error_log(self, mock_product_repo, mock_error_repo):
        """Test que échec publication crée un VintedErrorLog."""
        mock_db = Mock()
        mock_task = Mock()
        mock_task.id = 1
        mock_task.payload = {"vinted_product_id": 50}
        mock_task.status.value = "failed"
        mock_task.error_message = "API Error 500"
        mock_task.result = {
            "error_type": "api_error",
            "error_details": "Internal server error"
        }
        mock_task.product_id = 100

        mock_vinted_product = Mock()
        mock_product_repo.get_by_id.return_value = mock_vinted_product

        VintedTaskHandler._handle_publish_result(mock_db, mock_task)

        # Verify error log created
        mock_error_repo.create.assert_called_once()
        error_log = mock_error_repo.create.call_args[0][1]
        assert error_log.operation == "publish"
        assert error_log.error_type == "api_error"
        assert error_log.product_id == 100

        # Verify VintedProduct marked as error
        assert mock_vinted_product.status == "error"
        mock_db.commit.assert_called()

    @patch('services.vinted.vinted_task_handler.VintedProductRepository')
    def test_publish_missing_vinted_product_id_logs_error(self, mock_repo):
        """Test que payload sans vinted_product_id est logué."""
        mock_db = Mock()
        mock_task = Mock()
        mock_task.id = 1
        mock_task.payload = {}  # No vinted_product_id

        with patch('services.vinted.vinted_task_handler.logger') as mock_logger:
            VintedTaskHandler._handle_publish_result(mock_db, mock_task)
            mock_logger.error.assert_called()
            assert "vinted_product_id manquant" in str(mock_logger.error.call_args)

    @patch('services.vinted.vinted_task_handler.VintedProductRepository')
    def test_publish_vinted_product_not_found_logs_error(self, mock_repo):
        """Test que VintedProduct non trouvé est logué."""
        mock_db = Mock()
        mock_task = Mock()
        mock_task.id = 1
        mock_task.payload = {"vinted_product_id": 999}

        mock_repo.get_by_id.return_value = None  # Not found

        with patch('services.vinted.vinted_task_handler.logger') as mock_logger:
            VintedTaskHandler._handle_publish_result(mock_db, mock_task)
            mock_logger.error.assert_called()
            assert "non trouvé" in str(mock_logger.error.call_args)


class TestHandleUpdateResult:
    """Tests pour _handle_update_result."""

    @patch('services.vinted.vinted_task_handler.VintedProductRepository')
    def test_update_success_updates_fields(self, mock_repo):
        """Test que succès update met à jour les champs."""
        mock_db = Mock()
        mock_task = Mock()
        mock_task.id = 1
        mock_task.product_id = 100
        mock_task.status.value = "success"
        mock_task.result = {
            "title": "New Title",
            "price": 59.99
        }

        mock_vinted_product = Mock()
        mock_repo.get_by_product_id.return_value = mock_vinted_product

        VintedTaskHandler._handle_update_result(mock_db, mock_task)

        assert mock_vinted_product.title == "New Title"
        assert mock_vinted_product.price == 59.99
        mock_db.commit.assert_called_once()

    @patch('services.vinted.vinted_task_handler.VintedProductRepository')
    def test_update_success_partial_update(self, mock_repo):
        """Test update partiel (seulement titre)."""
        mock_db = Mock()
        mock_task = Mock()
        mock_task.id = 1
        mock_task.product_id = 100
        mock_task.status.value = "success"
        mock_task.result = {"title": "Only Title Updated"}

        mock_vinted_product = Mock()
        mock_vinted_product.price = 50.00  # Existing price
        mock_repo.get_by_product_id.return_value = mock_vinted_product

        VintedTaskHandler._handle_update_result(mock_db, mock_task)

        assert mock_vinted_product.title == "Only Title Updated"
        # Price should not be changed (not in result)
        mock_db.commit.assert_called_once()

    @patch('services.vinted.vinted_task_handler.VintedErrorLogRepository')
    @patch('services.vinted.vinted_task_handler.VintedProductRepository')
    def test_update_failure_creates_error_log(self, mock_product_repo, mock_error_repo):
        """Test que échec update crée un VintedErrorLog."""
        mock_db = Mock()
        mock_task = Mock()
        mock_task.id = 1
        mock_task.product_id = 100
        mock_task.status.value = "failed"
        mock_task.error_message = "Update failed"
        mock_task.result = {"error": "details"}

        mock_vinted_product = Mock()
        mock_product_repo.get_by_product_id.return_value = mock_vinted_product

        VintedTaskHandler._handle_update_result(mock_db, mock_task)

        mock_error_repo.create.assert_called_once()
        error_log = mock_error_repo.create.call_args[0][1]
        assert error_log.operation == "update"
        assert error_log.product_id == 100

    @patch('services.vinted.vinted_task_handler.VintedProductRepository')
    def test_update_no_product_id_returns_early(self, mock_repo):
        """Test que sans product_id, la fonction retourne tôt."""
        mock_db = Mock()
        mock_task = Mock()
        mock_task.product_id = None

        VintedTaskHandler._handle_update_result(mock_db, mock_task)

        mock_repo.get_by_product_id.assert_not_called()

    @patch('services.vinted.vinted_task_handler.VintedProductRepository')
    def test_update_vinted_product_not_found_logs_error(self, mock_repo):
        """Test que VintedProduct non trouvé est logué."""
        mock_db = Mock()
        mock_task = Mock()
        mock_task.id = 1
        mock_task.product_id = 100

        mock_repo.get_by_product_id.return_value = None

        with patch('services.vinted.vinted_task_handler.logger') as mock_logger:
            VintedTaskHandler._handle_update_result(mock_db, mock_task)
            mock_logger.error.assert_called()


class TestHandleDeleteResult:
    """Tests pour _handle_delete_result."""

    @patch('services.vinted.vinted_task_handler.VintedProductRepository')
    def test_delete_success_updates_status(self, mock_repo):
        """Test que succès delete met status à 'deleted'."""
        mock_db = Mock()
        mock_task = Mock()
        mock_task.id = 1
        mock_task.product_id = 100
        mock_task.status.value = "success"

        mock_vinted_product = Mock()
        mock_repo.get_by_product_id.return_value = mock_vinted_product

        VintedTaskHandler._handle_delete_result(mock_db, mock_task)

        assert mock_vinted_product.status == "deleted"
        mock_db.commit.assert_called_once()

    @patch('services.vinted.vinted_task_handler.VintedErrorLogRepository')
    @patch('services.vinted.vinted_task_handler.VintedProductRepository')
    def test_delete_failure_creates_error_log(self, mock_product_repo, mock_error_repo):
        """Test que échec delete crée un VintedErrorLog."""
        mock_db = Mock()
        mock_task = Mock()
        mock_task.id = 1
        mock_task.product_id = 100
        mock_task.status.value = "failed"
        mock_task.error_message = "Delete failed"
        mock_task.result = None

        mock_vinted_product = Mock()
        mock_product_repo.get_by_product_id.return_value = mock_vinted_product

        VintedTaskHandler._handle_delete_result(mock_db, mock_task)

        mock_error_repo.create.assert_called_once()
        error_log = mock_error_repo.create.call_args[0][1]
        assert error_log.operation == "delete"
        assert error_log.product_id == 100

    @patch('services.vinted.vinted_task_handler.VintedProductRepository')
    def test_delete_no_product_id_returns_early(self, mock_repo):
        """Test que sans product_id, la fonction retourne tôt."""
        mock_db = Mock()
        mock_task = Mock()
        mock_task.product_id = None

        VintedTaskHandler._handle_delete_result(mock_db, mock_task)

        mock_repo.get_by_product_id.assert_not_called()


class TestErrorHandling:
    """Tests pour la gestion des exceptions."""

    @patch('services.vinted.vinted_task_handler.VintedProductRepository')
    def test_publish_exception_is_caught(self, mock_repo):
        """Test que les exceptions dans publish sont catchées."""
        mock_db = Mock()
        mock_task = Mock()
        mock_task.id = 1
        mock_task.payload = {"vinted_product_id": 50}

        mock_repo.get_by_id.side_effect = Exception("DB error")

        with patch('services.vinted.vinted_task_handler.logger') as mock_logger:
            # Should not raise
            VintedTaskHandler._handle_publish_result(mock_db, mock_task)
            mock_logger.error.assert_called()

    @patch('services.vinted.vinted_task_handler.VintedProductRepository')
    def test_update_exception_is_caught(self, mock_repo):
        """Test que les exceptions dans update sont catchées."""
        mock_db = Mock()
        mock_task = Mock()
        mock_task.id = 1
        mock_task.product_id = 100

        mock_repo.get_by_product_id.side_effect = Exception("DB error")

        with patch('services.vinted.vinted_task_handler.logger') as mock_logger:
            VintedTaskHandler._handle_update_result(mock_db, mock_task)
            mock_logger.error.assert_called()

    @patch('services.vinted.vinted_task_handler.VintedProductRepository')
    def test_delete_exception_is_caught(self, mock_repo):
        """Test que les exceptions dans delete sont catchées."""
        mock_db = Mock()
        mock_task = Mock()
        mock_task.id = 1
        mock_task.product_id = 100

        mock_repo.get_by_product_id.side_effect = Exception("DB error")

        with patch('services.vinted.vinted_task_handler.logger') as mock_logger:
            VintedTaskHandler._handle_delete_result(mock_db, mock_task)
            mock_logger.error.assert_called()
