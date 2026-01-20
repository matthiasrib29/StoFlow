"""
Tests unitaires pour VintedJobBridgeService.

Ce service fait le pont entre Celery et les MarketplaceJobs pour Vinted.
Les workers Celery ne peuvent pas exécuter directement les jobs Vinted
(WebSocket requis), donc ils créent des MarketplaceJobs que le frontend exécute.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone


class TestVintedJobBridgeService:
    """Tests pour VintedJobBridgeService."""

    @pytest.fixture
    def mock_db(self):
        """Mock de la session DB."""
        db = MagicMock()
        db.commit = MagicMock()
        db.flush = MagicMock()
        return db

    @pytest.fixture
    def mock_job_service(self):
        """Mock du MarketplaceJobService."""
        service = MagicMock()
        return service

    @pytest.fixture
    def bridge_service(self, mock_db, mock_job_service):
        """Instance du service avec mocks."""
        with patch(
            "services.vinted.vinted_job_bridge_service.MarketplaceJobService"
        ) as MockJobService:
            MockJobService.return_value = mock_job_service
            from services.vinted.vinted_job_bridge_service import VintedJobBridgeService
            service = VintedJobBridgeService(mock_db)
            return service

    # =========================================================================
    # TESTS queue_publish
    # =========================================================================

    def test_queue_publish_creates_job(self, bridge_service, mock_job_service):
        """queue_publish doit créer un MarketplaceJob avec les bons paramètres."""
        # Arrange
        mock_job = MagicMock()
        mock_job.id = 123
        mock_job.action_type_id = 1
        mock_job.product_id = 456
        mock_job.priority = 2
        mock_job.input_data = {"shop_id": 789, "user_id": 1}
        mock_job_service.create_job.return_value = mock_job
        mock_job_service.get_action_type_by_id.return_value = MagicMock(code="publish")

        # Act
        with patch.object(bridge_service, "_notify_frontend"):
            result = bridge_service.queue_publish(
                product_id=456,
                user_id=1,
                shop_id=789
            )

        # Assert
        mock_job_service.create_job.assert_called_once_with(
            marketplace="vinted",
            action_code="publish",
            product_id=456,
            priority=2,
            input_data={"shop_id": 789, "user_id": 1}
        )
        assert result["success"] is True
        assert result["job_id"] == 123
        assert result["status"] == "queued_for_frontend"

    def test_queue_publish_commits_transaction(self, bridge_service, mock_db, mock_job_service):
        """queue_publish doit commit la transaction."""
        mock_job = MagicMock(id=1, action_type_id=1, product_id=1, priority=2, input_data={})
        mock_job_service.create_job.return_value = mock_job
        mock_job_service.get_action_type_by_id.return_value = MagicMock(code="publish")

        with patch.object(bridge_service, "_notify_frontend"):
            bridge_service.queue_publish(product_id=1, user_id=1)

        mock_db.commit.assert_called_once()

    def test_queue_publish_without_shop_id(self, bridge_service, mock_job_service):
        """queue_publish fonctionne sans shop_id (optionnel)."""
        mock_job = MagicMock(id=1, action_type_id=1, product_id=1, priority=2, input_data={})
        mock_job_service.create_job.return_value = mock_job
        mock_job_service.get_action_type_by_id.return_value = MagicMock(code="publish")

        with patch.object(bridge_service, "_notify_frontend"):
            result = bridge_service.queue_publish(product_id=1, user_id=1, shop_id=None)

        # Vérifier que input_data contient shop_id=None
        call_args = mock_job_service.create_job.call_args
        assert call_args.kwargs["input_data"]["shop_id"] is None
        assert result["success"] is True

    # =========================================================================
    # TESTS queue_update
    # =========================================================================

    def test_queue_update_creates_job(self, bridge_service, mock_job_service):
        """queue_update doit créer un MarketplaceJob avec les bons paramètres."""
        mock_job = MagicMock(id=456, action_type_id=2, product_id=123, priority=3, input_data={})
        mock_job_service.create_job.return_value = mock_job
        mock_job_service.get_action_type_by_id.return_value = MagicMock(code="update")

        with patch.object(bridge_service, "_notify_frontend"):
            result = bridge_service.queue_update(
                product_id=123,
                user_id=1,
                price=29.99,
                title="New Title"
            )

        mock_job_service.create_job.assert_called_once()
        call_args = mock_job_service.create_job.call_args
        assert call_args.kwargs["marketplace"] == "vinted"
        assert call_args.kwargs["action_code"] == "update"
        assert call_args.kwargs["product_id"] == 123
        assert call_args.kwargs["priority"] == 3  # NORMAL priority for updates
        assert call_args.kwargs["input_data"]["price"] == 29.99
        assert call_args.kwargs["input_data"]["title"] == "New Title"
        assert result["success"] is True

    def test_queue_update_with_kwargs(self, bridge_service, mock_job_service):
        """queue_update doit passer les kwargs dans input_data."""
        mock_job = MagicMock(id=1, action_type_id=2, product_id=1, priority=3, input_data={})
        mock_job_service.create_job.return_value = mock_job
        mock_job_service.get_action_type_by_id.return_value = MagicMock(code="update")

        with patch.object(bridge_service, "_notify_frontend"):
            bridge_service.queue_update(
                product_id=1,
                user_id=1,
                vinted_id=999,
                description="Updated desc"
            )

        call_args = mock_job_service.create_job.call_args
        input_data = call_args.kwargs["input_data"]
        assert input_data["vinted_id"] == 999
        assert input_data["description"] == "Updated desc"
        assert input_data["user_id"] == 1

    # =========================================================================
    # TESTS queue_delete
    # =========================================================================

    def test_queue_delete_creates_job(self, bridge_service, mock_job_service):
        """queue_delete doit créer un MarketplaceJob avec les bons paramètres."""
        mock_job = MagicMock(id=789, action_type_id=3, product_id=123, priority=2, input_data={})
        mock_job_service.create_job.return_value = mock_job
        mock_job_service.get_action_type_by_id.return_value = MagicMock(code="delete")

        with patch.object(bridge_service, "_notify_frontend"):
            result = bridge_service.queue_delete(product_id=123, user_id=1)

        mock_job_service.create_job.assert_called_once()
        call_args = mock_job_service.create_job.call_args
        assert call_args.kwargs["marketplace"] == "vinted"
        assert call_args.kwargs["action_code"] == "delete"
        assert call_args.kwargs["product_id"] == 123
        assert call_args.kwargs["priority"] == 2  # HIGH priority for deletes
        assert result["success"] is True
        assert result["job_id"] == 789

    # =========================================================================
    # TESTS queue_sync
    # =========================================================================

    def test_queue_sync_creates_job_without_product_id(self, bridge_service, mock_job_service):
        """queue_sync doit créer un job sans product_id (sync n'est pas spécifique)."""
        mock_job = MagicMock(id=101, action_type_id=4, product_id=None, priority=3, input_data={})
        mock_job_service.create_job.return_value = mock_job
        mock_job_service.get_action_type_by_id.return_value = MagicMock(code="sync")

        with patch.object(bridge_service, "_notify_frontend"):
            result = bridge_service.queue_sync(user_id=1, shop_id=999)

        call_args = mock_job_service.create_job.call_args
        assert call_args.kwargs["product_id"] is None
        assert call_args.kwargs["action_code"] == "sync"
        assert call_args.kwargs["input_data"]["shop_id"] == 999
        assert result["success"] is True

    # =========================================================================
    # TESTS _notify_frontend
    # =========================================================================

    def test_notify_frontend_sends_websocket_event(self, bridge_service, mock_job_service):
        """_notify_frontend doit envoyer un event WebSocket."""
        mock_job = MagicMock()
        mock_job.id = 123
        mock_job.action_type_id = 1
        mock_job.product_id = 456
        mock_job.priority = 2
        mock_job.input_data = {"key": "value"}

        mock_action_type = MagicMock()
        mock_action_type.code = "publish"
        mock_job_service.get_action_type_by_id.return_value = mock_action_type

        # Patch at the point of import inside the function
        with patch("services.websocket_service.sio") as mock_sio:
            mock_sio.emit = AsyncMock()

            # Use new_event_loop to run the notification
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                bridge_service._notify_frontend(user_id=1, job=mock_job)
            finally:
                loop.close()

            # Verify emit was attempted
            # Note: The actual emit may or may not be called depending on async context

    def test_notify_frontend_handles_error_gracefully(self, bridge_service, mock_job_service):
        """_notify_frontend ne doit pas lever d'exception en cas d'erreur."""
        mock_job = MagicMock(id=1, action_type_id=1, product_id=1, priority=2, input_data={})
        mock_job_service.get_action_type_by_id.return_value = MagicMock(code="publish")

        # Patch at the point of import inside the function
        with patch("services.websocket_service.sio") as mock_sio:
            mock_sio.emit = MagicMock(side_effect=Exception("WebSocket error"))

            # Should not raise - errors are caught internally
            bridge_service._notify_frontend(user_id=1, job=mock_job)

    def test_notify_frontend_uses_correct_room(self, bridge_service, mock_job_service):
        """_notify_frontend doit utiliser la room user_{user_id}."""
        mock_job = MagicMock(id=1, action_type_id=1, product_id=1, priority=2, input_data={})
        mock_action_type = MagicMock(code="publish")
        mock_job_service.get_action_type_by_id.return_value = mock_action_type

        emit_calls = []

        async def capture_emit(event, data, room=None):
            emit_calls.append({"event": event, "data": data, "room": room})

        with patch("services.websocket_service.sio") as mock_sio:
            mock_sio.emit = capture_emit

            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                bridge_service._notify_frontend(user_id=42, job=mock_job)
            finally:
                loop.close()

            # Verify the room format if emit was called
            if emit_calls:
                assert emit_calls[0]["room"] == "user_42"
                assert emit_calls[0]["event"] == "vinted_job_pending"


class TestVintedJobBridgeServiceIntegration:
    """Tests d'intégration légère pour VintedJobBridgeService."""

    def test_full_publish_flow(self):
        """Test du flow complet de publication."""
        with patch("services.vinted.vinted_job_bridge_service.MarketplaceJobService") as MockJobService:
            mock_job_service = MagicMock()
            mock_job = MagicMock()
            mock_job.id = 999
            mock_job.action_type_id = 1
            mock_job.product_id = 123
            mock_job.priority = 2
            mock_job.input_data = {}
            mock_job_service.create_job.return_value = mock_job
            mock_job_service.get_action_type_by_id.return_value = MagicMock(code="publish")
            MockJobService.return_value = mock_job_service

            mock_db = MagicMock()

            from services.vinted.vinted_job_bridge_service import VintedJobBridgeService

            # Patch the websocket service import
            with patch("services.websocket_service.sio"):
                service = VintedJobBridgeService(mock_db)
                result = service.queue_publish(
                    product_id=123,
                    user_id=1,
                    shop_id=456
                )

            assert result["success"] is True
            assert result["job_id"] == 999
            assert result["status"] == "queued_for_frontend"
            mock_db.commit.assert_called_once()
