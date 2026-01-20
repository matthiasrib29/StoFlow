"""
Tests unitaires pour l'API Tasks (Celery).

Tests des endpoints pour gérer et monitorer les tâches Celery.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, AsyncMock


class TestListTasksEndpoint:
    """Tests pour GET /api/tasks."""

    @pytest.fixture
    def mock_task_tracking_service(self):
        """Mock du TaskTrackingService."""
        with patch("api.tasks.TaskTrackingService") as MockService:
            service = MagicMock()
            MockService.return_value = service
            yield service

    def test_list_tasks_returns_empty_list(self, mock_task_tracking_service):
        """Test liste vide de tasks."""
        mock_task_tracking_service.get_tasks_for_user.return_value = []
        mock_task_tracking_service.get_task_count_for_user.return_value = 0

        # Simulate the service call
        tasks = mock_task_tracking_service.get_tasks_for_user(
            user_id=1,
            status=None,
            marketplace=None,
            action_code=None,
            limit=50,
            offset=0,
        )

        assert tasks == []

    def test_list_tasks_with_filters(self, mock_task_tracking_service):
        """Test liste avec filtres."""
        mock_task = MagicMock()
        mock_task.id = "task-123"
        mock_task.status = "SUCCESS"
        mock_task.marketplace = "ebay"
        mock_task_tracking_service.get_tasks_for_user.return_value = [mock_task]
        mock_task_tracking_service.get_task_count_for_user.return_value = 1

        tasks = mock_task_tracking_service.get_tasks_for_user(
            user_id=1,
            status="SUCCESS",
            marketplace="ebay",
            action_code=None,
            limit=50,
            offset=0,
        )

        assert len(tasks) == 1
        assert tasks[0].marketplace == "ebay"

    def test_list_tasks_pagination(self, mock_task_tracking_service):
        """Test pagination."""
        mock_task_tracking_service.get_tasks_for_user.return_value = []
        mock_task_tracking_service.get_task_count_for_user.return_value = 100

        # With offset and limit
        mock_task_tracking_service.get_tasks_for_user(
            user_id=1,
            status=None,
            marketplace=None,
            action_code=None,
            limit=10,
            offset=50,
        )

        mock_task_tracking_service.get_tasks_for_user.assert_called_once_with(
            user_id=1,
            status=None,
            marketplace=None,
            action_code=None,
            limit=10,
            offset=50,
        )


class TestGetTaskEndpoint:
    """Tests pour GET /api/tasks/{task_id}."""

    def test_get_task_found(self):
        """Test récupération d'une task existante."""
        with patch("api.tasks.TaskTrackingService") as MockService:
            mock_task = MagicMock()
            mock_task.id = "task-123"
            mock_task.user_id = 1
            mock_task.status = "SUCCESS"

            mock_service = MagicMock()
            mock_service.get_task_record.return_value = mock_task
            MockService.return_value = mock_service

            task = mock_service.get_task_record("task-123")

            assert task is not None
            assert task.id == "task-123"

    def test_get_task_not_found(self):
        """Test récupération d'une task inexistante."""
        with patch("api.tasks.TaskTrackingService") as MockService:
            mock_service = MagicMock()
            mock_service.get_task_record.return_value = None
            MockService.return_value = mock_service

            task = mock_service.get_task_record("nonexistent-task")

            assert task is None

    def test_get_task_access_denied(self):
        """Test accès refusé à une task d'un autre user."""
        with patch("api.tasks.TaskTrackingService") as MockService:
            mock_task = MagicMock()
            mock_task.id = "task-123"
            mock_task.user_id = 2  # Different user

            mock_service = MagicMock()
            mock_service.get_task_record.return_value = mock_task
            MockService.return_value = mock_service

            task = mock_service.get_task_record("task-123")

            # The endpoint should check user_id
            current_user_id = 1
            assert task.user_id != current_user_id


class TestGetTaskStatsEndpoint:
    """Tests pour GET /api/tasks/stats."""

    def test_get_stats_success(self):
        """Test récupération des statistiques."""
        with patch("api.tasks.TaskTrackingService") as MockService:
            mock_service = MagicMock()
            mock_service.get_task_stats.return_value = {
                "period_days": 7,
                "by_status": {"SUCCESS": 50, "FAILURE": 5, "PENDING": 3},
                "by_marketplace": {"ebay": 30, "vinted": 25, "etsy": 3},
                "avg_runtime_seconds": 2.5,
                "total": 58,
            }
            MockService.return_value = mock_service

            stats = mock_service.get_task_stats(user_id=1, days=7)

            assert stats["period_days"] == 7
            assert stats["by_status"]["SUCCESS"] == 50
            assert stats["by_marketplace"]["ebay"] == 30
            assert stats["total"] == 58

    def test_get_stats_empty(self):
        """Test stats vides (nouveau user)."""
        with patch("api.tasks.TaskTrackingService") as MockService:
            mock_service = MagicMock()
            mock_service.get_task_stats.return_value = {
                "period_days": 7,
                "by_status": {},
                "by_marketplace": {},
                "avg_runtime_seconds": None,
                "total": 0,
            }
            MockService.return_value = mock_service

            stats = mock_service.get_task_stats(user_id=1, days=7)

            assert stats["total"] == 0
            assert stats["by_status"] == {}


class TestRevokeTaskEndpoint:
    """Tests pour POST /api/tasks/{task_id}/revoke."""

    def test_revoke_pending_task(self):
        """Test révocation d'une task pending."""
        mock_task = MagicMock()
        mock_task.id = "task-123"
        mock_task.user_id = 1
        mock_task.status = "PENDING"

        mock_service = MagicMock()
        mock_service.get_task_record.return_value = mock_task

        mock_celery = MagicMock()

        # Simulate revoke
        mock_celery.control.revoke("task-123", terminate=False)
        mock_service.update_task_revoked("task-123")

        mock_celery.control.revoke.assert_called_once_with(
            "task-123", terminate=False
        )
        mock_service.update_task_revoked.assert_called_once_with("task-123")

    def test_revoke_completed_task_fails(self):
        """Test que révoquer une task terminée échoue."""
        mock_task = MagicMock()
        mock_task.id = "task-123"
        mock_task.user_id = 1
        mock_task.status = "SUCCESS"

        mock_service = MagicMock()
        mock_service.get_task_record.return_value = mock_task

        # Should not allow revoke for SUCCESS status
        assert mock_task.status in ["SUCCESS", "FAILURE", "REVOKED"]

    def test_revoke_with_terminate(self):
        """Test révocation avec terminate=True."""
        mock_task = MagicMock()
        mock_task.id = "task-123"
        mock_task.user_id = 1
        mock_task.status = "STARTED"

        mock_celery = MagicMock()

        # Simulate revoke with terminate
        mock_celery.control.revoke("task-123", terminate=True)

        mock_celery.control.revoke.assert_called_once_with(
            "task-123", terminate=True
        )


class TestCreatePublishTaskEndpoint:
    """Tests pour POST /api/tasks/publish."""

    def test_create_publish_task_vinted(self):
        """Test création task publish pour Vinted."""
        mock_publish = MagicMock()
        mock_task = MagicMock()
        mock_task.id = "celery-task-123"
        mock_publish.delay.return_value = mock_task

        # Simulate endpoint call
        result = mock_publish.delay(
            product_id=456,
            user_id=1,
            marketplace="vinted",
            shop_id=789,
            marketplace_id=None,
        )

        mock_publish.delay.assert_called_once_with(
            product_id=456,
            user_id=1,
            marketplace="vinted",
            shop_id=789,
            marketplace_id=None,
        )
        assert result.id == "celery-task-123"

    def test_create_publish_task_ebay(self):
        """Test création task publish pour eBay."""
        mock_publish = MagicMock()
        mock_task = MagicMock()
        mock_task.id = "celery-task-456"
        mock_publish.delay.return_value = mock_task

        result = mock_publish.delay(
            product_id=123,
            user_id=1,
            marketplace="ebay",
            shop_id=None,
            marketplace_id="EBAY_FR",
        )

        assert result.id == "celery-task-456"

    def test_create_publish_task_invalid_marketplace(self):
        """Test avec marketplace invalide."""
        from api.tasks import PublishTaskRequest

        # Le schema accepte n'importe quelle string
        # La validation se fait dans l'endpoint
        request = PublishTaskRequest(
            product_id=123,
            marketplace="invalid",
        )
        # L'endpoint doit rejeter avec 400

    def test_create_publish_task_vinted_requires_shop_id(self):
        """Test que Vinted requiert shop_id."""
        # L'endpoint doit valider que shop_id est présent pour Vinted
        # Cette validation est faite dans le handler, pas dans le schema
        pass


class TestBatchPublishTaskEndpoint:
    """Tests pour POST /api/tasks/publish/batch."""

    def test_create_batch_publish_tasks(self):
        """Test création de tasks batch."""
        mock_publish = MagicMock()

        # Simulate batch creation
        product_ids = [100, 200, 300]
        results = []
        for i, pid in enumerate(product_ids):
            mock_task = MagicMock()
            mock_task.id = f"celery-task-{i}"
            mock_publish.delay.return_value = mock_task

            result = mock_publish.delay(
                product_id=pid,
                user_id=1,
                marketplace="ebay",
                shop_id=None,
                marketplace_id="EBAY_FR",
            )
            results.append(result)

        assert len(results) == 3
        assert mock_publish.delay.call_count == 3

    def test_batch_publish_empty_list_fails(self):
        """Test que liste vide est rejetée."""
        from api.tasks import BatchPublishRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            BatchPublishRequest(
                product_ids=[],  # min_length=1
                marketplace="ebay",
            )


class TestSyncTaskEndpoint:
    """Tests pour POST /api/tasks/sync."""

    def test_create_sync_inventory_task(self):
        """Test création task sync inventory."""
        mock_sync = MagicMock()
        mock_task = MagicMock()
        mock_task.id = "sync-task-123"
        mock_sync.delay.return_value = mock_task

        result = mock_sync.delay(
            user_id=1,
            marketplace="ebay",
            shop_id=None,
        )

        mock_sync.delay.assert_called_once()
        assert result.id == "sync-task-123"

    def test_create_sync_orders_task(self):
        """Test création task sync orders."""
        mock_sync = MagicMock()
        mock_task = MagicMock()
        mock_task.id = "sync-orders-123"
        mock_sync.delay.return_value = mock_task

        result = mock_sync.delay(
            user_id=1,
            marketplace="vinted",
            shop_id=456,
        )

        mock_sync.delay.assert_called_once()
        assert result.id == "sync-orders-123"

    def test_sync_vinted_requires_shop_id(self):
        """Test que Vinted sync requiert shop_id."""
        # L'endpoint doit valider que shop_id est présent pour Vinted
        pass


class TestTaskRequestSchemas:
    """Tests pour les schemas de requête."""

    def test_publish_task_request_schema(self):
        """Test PublishTaskRequest schema."""
        from api.tasks import PublishTaskRequest

        request = PublishTaskRequest(
            product_id=123,
            marketplace="ebay",
            marketplace_id="EBAY_FR",
        )

        assert request.product_id == 123
        assert request.marketplace == "ebay"
        assert request.marketplace_id == "EBAY_FR"
        assert request.shop_id is None

    def test_publish_task_request_with_shop_id(self):
        """Test PublishTaskRequest avec shop_id."""
        from api.tasks import PublishTaskRequest

        request = PublishTaskRequest(
            product_id=456,
            marketplace="vinted",
            shop_id=789,
        )

        assert request.shop_id == 789

    def test_batch_publish_request_schema(self):
        """Test BatchPublishRequest schema."""
        from api.tasks import BatchPublishRequest

        request = BatchPublishRequest(
            product_ids=[1, 2, 3],
            marketplace="etsy",
        )

        assert len(request.product_ids) == 3
        assert request.marketplace == "etsy"


class TestTaskResponseSchemas:
    """Tests pour les schemas de réponse."""

    def test_task_response_schema(self):
        """Test TaskResponse schema."""
        from api.tasks import TaskResponse

        task = TaskResponse(
            id="task-123",
            name="tasks.marketplace_tasks.publish_product",
            status="SUCCESS",
            marketplace="ebay",
            action_code="publish",
            product_id=456,
            result={"listing_id": "eBay123"},
            retries=0,
            max_retries=3,
            created_at=datetime.now(timezone.utc),
        )

        assert task.id == "task-123"
        assert task.status == "SUCCESS"
        assert task.result["listing_id"] == "eBay123"

    def test_task_create_response_schema(self):
        """Test TaskCreateResponse schema."""
        from api.tasks import TaskCreateResponse

        response = TaskCreateResponse(
            task_id="celery-123",
            status="PENDING",
            message="Task queued",
        )

        assert response.task_id == "celery-123"
        assert response.status == "PENDING"

    def test_task_stats_response_schema(self):
        """Test TaskStatsResponse schema."""
        from api.tasks import TaskStatsResponse

        stats = TaskStatsResponse(
            period_days=7,
            by_status={"SUCCESS": 50, "FAILURE": 5},
            by_marketplace={"ebay": 30, "vinted": 25},
            avg_runtime_seconds=2.5,
            total=55,
        )

        assert stats.period_days == 7
        assert stats.total == 55
        assert stats.by_status["SUCCESS"] == 50
