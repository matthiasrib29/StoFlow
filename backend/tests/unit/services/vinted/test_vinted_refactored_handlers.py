"""
Tests for refactored Vinted handlers (Publish, Update, Delete).

Tests the public API (execute) with mocked services.
Tests for private methods removed (logic moved to services).

Author: Claude
Date: 2026-01-15
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from models.user.marketplace_job import MarketplaceJob
from services.vinted.jobs.publish_job_handler import PublishJobHandler
from services.vinted.jobs.update_job_handler import UpdateJobHandler
from services.vinted.jobs.delete_job_handler import DeleteJobHandler
from services.vinted.jobs.sync_job_handler import SyncJobHandler
from services.vinted.jobs.link_product_job_handler import LinkProductJobHandler
from services.vinted.jobs.message_job_handler import MessageJobHandler
from services.vinted.jobs.orders_job_handler import OrdersJobHandler


class TestPublishJobHandler:
    """Tests for PublishJobHandler."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def handler(self, db_session):
        """Create handler instance."""
        return PublishJobHandler(db_session, shop_id=1, job_id=1)

    @pytest.fixture
    def job(self):
        """Create test job."""
        job = Mock(spec=MarketplaceJob)
        job.product_id = 100
        return job

    def test_get_service(self, handler):
        """Test get_service returns VintedPublicationService."""
        service = handler.get_service()
        assert service is not None
        assert service.__class__.__name__ == "VintedPublicationService"

    def test_get_service_method_name(self, handler):
        """Test get_service_method_name returns correct method."""
        assert handler.get_service_method_name() == "publish_product"

    def test_create_tasks(self, handler, job):
        """Test create_tasks returns task list."""
        tasks = handler.create_tasks(job)
        assert isinstance(tasks, list)
        assert len(tasks) > 0
        assert "Validate" in tasks[0]

    @pytest.mark.asyncio
    async def test_execute_missing_product_id(self, handler):
        """Test execute with missing product_id."""
        job = Mock(spec=MarketplaceJob)
        job.product_id = None

        result = await handler.execute(job)

        assert result["success"] is False
        assert "product_id required" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_success(self, handler, job):
        """Test execute delegates to service successfully."""
        # Mock service
        mock_service = Mock()
        mock_service.publish_product = AsyncMock(return_value={
            "success": True,
            "vinted_id": 12345,
            "url": "https://vinted.com/item/12345"
        })

        with patch.object(handler, 'get_service', return_value=mock_service):
            result = await handler.execute(job)

        assert result["success"] is True
        assert result["vinted_id"] == 12345
        mock_service.publish_product.assert_called_once_with(
            product_id=100,
            user_id=handler.user_id,
            shop_id=1,
            job_id=1
        )

    @pytest.mark.asyncio
    async def test_execute_service_error(self, handler, job):
        """Test execute when service returns error."""
        mock_service = Mock()
        mock_service.publish_product = AsyncMock(return_value={
            "success": False,
            "error": "Product validation failed"
        })

        with patch.object(handler, 'get_service', return_value=mock_service):
            result = await handler.execute(job)

        assert result["success"] is False
        assert "validation failed" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_exception(self, handler, job):
        """Test execute when service raises exception."""
        mock_service = Mock()
        mock_service.publish_product = AsyncMock(side_effect=Exception("Service crashed"))

        with patch.object(handler, 'get_service', return_value=mock_service):
            result = await handler.execute(job)

        assert result["success"] is False
        assert "Service crashed" in result["error"]


class TestUpdateJobHandler:
    """Tests for UpdateJobHandler."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def handler(self, db_session):
        """Create handler instance."""
        return UpdateJobHandler(db_session, shop_id=1, job_id=1)

    @pytest.fixture
    def job(self):
        """Create test job."""
        job = Mock(spec=MarketplaceJob)
        job.product_id = 100
        return job

    def test_get_service(self, handler):
        """Test get_service returns VintedUpdateService."""
        service = handler.get_service()
        assert service is not None
        assert service.__class__.__name__ == "VintedUpdateService"

    def test_get_service_method_name(self, handler):
        """Test get_service_method_name returns correct method."""
        assert handler.get_service_method_name() == "update_product"

    @pytest.mark.asyncio
    async def test_execute_success(self, handler, job):
        """Test execute delegates to service successfully."""
        mock_service = Mock()
        mock_service.update_product = AsyncMock(return_value={
            "success": True,
            "product_id": 100,
            "old_price": 10.0,
            "new_price": 12.0
        })

        with patch.object(handler, 'get_service', return_value=mock_service):
            result = await handler.execute(job)

        assert result["success"] is True
        assert result["product_id"] == 100
        mock_service.update_product.assert_called_once()


class TestDeleteJobHandler:
    """Tests for DeleteJobHandler."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def handler(self, db_session):
        """Create handler instance."""
        return DeleteJobHandler(db_session, shop_id=1, job_id=1)

    @pytest.fixture
    def job(self):
        """Create test job."""
        job = Mock(spec=MarketplaceJob)
        job.product_id = 100
        job.result_data = None
        return job

    def test_get_service(self, handler):
        """Test get_service returns VintedDeletionService."""
        service = handler.get_service()
        assert service is not None
        assert service.__class__.__name__ == "VintedDeletionService"

    def test_get_service_method_name(self, handler):
        """Test get_service_method_name returns correct method."""
        assert handler.get_service_method_name() == "delete_product"

    @pytest.mark.asyncio
    async def test_execute_success_default_check_conditions(self, handler, job):
        """Test execute with default check_conditions (True)."""
        mock_service = Mock()
        mock_service.delete_product = AsyncMock(return_value={
            "success": True,
            "product_id": 100,
            "vinted_id": 12345
        })

        with patch.object(handler, 'get_service', return_value=mock_service):
            result = await handler.execute(job)

        assert result["success"] is True
        # Verify check_conditions=True was passed
        call_args = mock_service.delete_product.call_args
        assert call_args.kwargs["check_conditions"] is True

    @pytest.mark.asyncio
    async def test_execute_success_with_check_conditions_false(self, handler):
        """Test execute with check_conditions=False from job data."""
        job = Mock(spec=MarketplaceJob)
        job.product_id = 100
        job.result_data = {"check_conditions": False}

        mock_service = Mock()
        mock_service.delete_product = AsyncMock(return_value={
            "success": True,
            "product_id": 100
        })

        with patch.object(handler, 'get_service', return_value=mock_service):
            result = await handler.execute(job)

        assert result["success"] is True
        # Verify check_conditions=False was passed
        call_args = mock_service.delete_product.call_args
        assert call_args.kwargs["check_conditions"] is False


# ============================================================================
# TESTS FOR REMAINING HANDLERS (Phase 07-03)
# ============================================================================


class TestSyncJobHandler:
    """Tests for SyncJobHandler."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def handler(self, db_session):
        """Create handler instance."""
        return SyncJobHandler(db_session, shop_id=1, job_id=1)

    @pytest.fixture
    def job(self):
        """Create test job."""
        job = Mock(spec=MarketplaceJob)
        job.product_id = None  # Not used for sync
        return job

    def test_get_service(self, handler):
        """Test get_service returns VintedSyncService."""
        service = handler.get_service()
        assert service is not None
        assert service.__class__.__name__ == "VintedSyncService"

    def test_create_tasks(self, handler, job):
        """Test create_tasks returns task list."""
        tasks = handler.create_tasks(job)
        assert isinstance(tasks, list)
        assert len(tasks) > 0
        assert "Fetch" in tasks[0]

    @pytest.mark.asyncio
    async def test_execute_success(self, handler, job):
        """Test execute delegates to service successfully."""
        mock_service = Mock()
        mock_service.sync_products = AsyncMock(return_value={
            "success": True,
            "products_synced": 15,
            "imported": 10,
            "updated": 5,
            "errors": 0
        })

        with patch.object(handler, 'get_service', return_value=mock_service):
            result = await handler.execute(job)

        assert result["success"] is True
        assert result["products_synced"] == 15
        mock_service.sync_products.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_failure(self, handler, job):
        """Test execute handles service failure."""
        mock_service = Mock()
        mock_service.sync_products = AsyncMock(return_value={
            "success": False,
            "error": "API error"
        })

        with patch.object(handler, 'get_service', return_value=mock_service):
            result = await handler.execute(job)

        assert result["success"] is False
        assert "error" in result


class TestLinkProductJobHandler:
    """Tests for LinkProductJobHandler."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        session = Mock()
        # Mock get_tenant_schema
        with patch("services.vinted.jobs.link_product_job_handler.get_tenant_schema", return_value="user_123"):
            yield session

    @pytest.fixture
    def handler(self, db_session):
        """Create handler instance."""
        return LinkProductJobHandler(db_session, shop_id=1, job_id=1)

    @pytest.fixture
    def job(self):
        """Create test job."""
        job = Mock(spec=MarketplaceJob)
        job.product_id = 12345  # vinted_id
        return job

    def test_get_service(self, handler):
        """Test get_service returns VintedLinkProductService."""
        service = handler.get_service()
        assert service is not None
        assert service.__class__.__name__ == "VintedLinkProductService"

    def test_create_tasks(self, handler, job):
        """Test create_tasks returns task list."""
        tasks = handler.create_tasks(job)
        assert isinstance(tasks, list)
        assert len(tasks) > 0
        assert "Create" in tasks[1]

    @pytest.mark.asyncio
    async def test_execute_success(self, handler, job):
        """Test execute delegates to service successfully."""
        mock_service = Mock()
        mock_service.link_product = AsyncMock(return_value={
            "success": True,
            "linked": True,
            "product_id": 100,
            "vinted_id": 12345,
            "images_copied": 5,
            "images_failed": 0,
            "total_images": 5
        })

        with patch("services.vinted.jobs.link_product_job_handler.get_tenant_schema", return_value="user_123"):
            with patch.object(handler, 'get_service', return_value=mock_service):
                result = await handler.execute(job)

        assert result["success"] is True
        assert result["product_id"] == 100
        mock_service.link_product.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_failure(self, handler, job):
        """Test execute handles service failure."""
        mock_service = Mock()
        mock_service.link_product = AsyncMock(return_value={
            "success": False,
            "linked": False,
            "error": "VintedProduct not found"
        })

        with patch("services.vinted.jobs.link_product_job_handler.get_tenant_schema", return_value="user_123"):
            with patch.object(handler, 'get_service', return_value=mock_service):
                result = await handler.execute(job)

        assert result["success"] is False
        assert result["linked"] is False


class TestMessageJobHandler:
    """Tests for MessageJobHandler."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def handler(self, db_session):
        """Create handler instance."""
        return MessageJobHandler(db_session, shop_id=1, job_id=1)

    @pytest.fixture
    def job_inbox(self):
        """Create test job for inbox sync."""
        job = Mock(spec=MarketplaceJob)
        job.result_data = {}
        return job

    @pytest.fixture
    def job_conversation(self):
        """Create test job for conversation sync."""
        job = Mock(spec=MarketplaceJob)
        job.result_data = {"conversation_id": 456}
        return job

    def test_get_service(self, handler):
        """Test get_service returns VintedMessageService."""
        service = handler.get_service()
        assert service is not None
        assert service.__class__.__name__ == "VintedMessageService"

    def test_create_tasks_inbox(self, handler, job_inbox):
        """Test create_tasks for inbox sync."""
        tasks = handler.create_tasks(job_inbox)
        assert isinstance(tasks, list)
        assert "inbox" in tasks[0].lower()

    def test_create_tasks_conversation(self, handler, job_conversation):
        """Test create_tasks for conversation sync."""
        tasks = handler.create_tasks(job_conversation)
        assert isinstance(tasks, list)
        assert "conversation" in tasks[0].lower()

    @pytest.mark.asyncio
    async def test_execute_inbox_success(self, handler, job_inbox):
        """Test execute inbox sync successfully."""
        mock_service = Mock()
        mock_service.handle_message = AsyncMock(return_value={
            "success": True,
            "message_handled": True,
            "mode": "inbox",
            "synced": 20,
            "created": 5,
            "updated": 15
        })

        with patch.object(handler, 'get_service', return_value=mock_service):
            result = await handler.execute(job_inbox)

        assert result["success"] is True
        assert result["mode"] == "inbox"
        assert result["synced"] == 20

    @pytest.mark.asyncio
    async def test_execute_conversation_success(self, handler, job_conversation):
        """Test execute conversation sync successfully."""
        mock_service = Mock()
        mock_service.handle_message = AsyncMock(return_value={
            "success": True,
            "message_handled": True,
            "mode": "conversation",
            "synced": 10
        })

        with patch.object(handler, 'get_service', return_value=mock_service):
            result = await handler.execute(job_conversation)

        assert result["success"] is True
        assert result["mode"] == "conversation"


class TestOrdersJobHandler:
    """Tests for OrdersJobHandler."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def handler(self, db_session):
        """Create handler instance."""
        return OrdersJobHandler(db_session, shop_id=1, job_id=1)

    @pytest.fixture
    def job_all(self):
        """Create test job for all orders sync."""
        job = Mock(spec=MarketplaceJob)
        job.result_data = {}
        return job

    @pytest.fixture
    def job_month(self):
        """Create test job for month sync."""
        job = Mock(spec=MarketplaceJob)
        job.result_data = {"year": 2026, "month": 1}
        return job

    def test_get_service(self, handler):
        """Test get_service returns VintedOrdersService."""
        service = handler.get_service()
        assert service is not None
        assert service.__class__.__name__ == "VintedOrdersService"

    def test_create_tasks_all(self, handler, job_all):
        """Test create_tasks for all orders sync."""
        tasks = handler.create_tasks(job_all)
        assert isinstance(tasks, list)
        assert "all orders" in tasks[0].lower()

    def test_create_tasks_month(self, handler, job_month):
        """Test create_tasks for month sync."""
        tasks = handler.create_tasks(job_month)
        assert isinstance(tasks, list)
        assert "2026-01" in tasks[0]

    @pytest.mark.asyncio
    async def test_execute_all_success(self, handler, job_all):
        """Test execute all orders sync successfully."""
        mock_service = Mock()
        mock_service.sync_orders = AsyncMock(return_value={
            "success": True,
            "orders_synced": 25,
            "mode": "classic"
        })

        with patch.object(handler, 'get_service', return_value=mock_service):
            result = await handler.execute(job_all)

        assert result["success"] is True
        assert result["orders_synced"] == 25
        assert result["mode"] == "classic"

    @pytest.mark.asyncio
    async def test_execute_month_success(self, handler, job_month):
        """Test execute month sync successfully."""
        mock_service = Mock()
        mock_service.sync_orders = AsyncMock(return_value={
            "success": True,
            "orders_synced": 10,
            "mode": "month",
            "year": 2026,
            "month": 1
        })

        with patch.object(handler, 'get_service', return_value=mock_service):
            result = await handler.execute(job_month)

        assert result["success"] is True
        assert result["orders_synced"] == 10
        assert result["mode"] == "month"
