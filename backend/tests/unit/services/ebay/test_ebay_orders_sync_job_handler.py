"""
Unit tests for EbayOrdersSyncJobHandler.

Tests the eBay orders synchronization job handler including:
- Job execution workflow
- Delegation to EbayOrderSyncService
- Input data extraction from jobs
- Error handling and reporting
- Multi-tenant schema setup

Author: Claude
Date: 2026-01-08
"""

from unittest.mock import MagicMock, Mock, patch

import pytest


class TestEbayOrdersSyncJobHandlerInit:
    """Tests for EbayOrdersSyncJobHandler initialization."""

    def test_class_action_code(self):
        """Test that ACTION_CODE constant is correct."""
        from services.ebay.jobs.ebay_orders_sync_job_handler import (
            EbayOrdersSyncJobHandler,
        )

        assert EbayOrdersSyncJobHandler.ACTION_CODE == "sync_orders"

    def test_init_stores_parameters(self):
        """Test that __init__ stores all parameters correctly."""
        from services.ebay.jobs.ebay_orders_sync_job_handler import (
            EbayOrdersSyncJobHandler,
        )

        mock_db = MagicMock()
        handler = EbayOrdersSyncJobHandler(db=mock_db, shop_id=42, job_id=100)

        assert handler.db == mock_db
        assert handler.shop_id == 42
        assert handler.job_id == 100

    def test_init_with_none_values(self):
        """Test that __init__ accepts None values for optional parameters."""
        from services.ebay.jobs.ebay_orders_sync_job_handler import (
            EbayOrdersSyncJobHandler,
        )

        mock_db = MagicMock()
        handler = EbayOrdersSyncJobHandler(db=mock_db, shop_id=None, job_id=None)

        assert handler.db == mock_db
        assert handler.shop_id is None
        assert handler.job_id is None


class TestEbayOrdersSyncJobHandlerExecute:
    """Tests for execute method."""

    @pytest.fixture
    def mock_handler(self):
        """Create a handler with mocked dependencies."""
        from services.ebay.jobs.ebay_orders_sync_job_handler import (
            EbayOrdersSyncJobHandler,
        )

        mock_db = MagicMock()
        handler = EbayOrdersSyncJobHandler(db=mock_db, shop_id=1, job_id=10)
        return handler

    @pytest.fixture
    def mock_job(self):
        """Create a mock MarketplaceJob."""
        job = MagicMock()
        job.input_data = {"hours": 24, "status_filter": None}
        return job

    @pytest.mark.asyncio
    async def test_execute_success(self, mock_handler, mock_job):
        """Test successful execution returns expected statistics."""
        mock_sync_stats = {
            "created": 5,
            "updated": 3,
            "skipped": 2,
            "errors": 0,
            "total_fetched": 10,
            "details": [
                {"order_id": "12-1", "action": "created"},
                {"order_id": "12-2", "action": "updated"},
            ],
        }

        with patch(
            "shared.database.set_user_schema"
        ) as mock_set_schema:
            with patch(
                "services.ebay.ebay_order_sync_service.EbayOrderSyncService"
            ) as MockSyncService:
                mock_service_instance = MagicMock()
                mock_service_instance.sync_orders.return_value = mock_sync_stats
                MockSyncService.return_value = mock_service_instance

                result = await mock_handler.execute(mock_job)

                assert result["success"] is True
                assert result["created"] == 5
                assert result["updated"] == 3
                assert result["skipped"] == 2
                assert result["errors"] == 0
                assert result["total_fetched"] == 10
                assert len(result["details"]) == 2

                mock_set_schema.assert_called_once_with(mock_handler.db, 1)
                MockSyncService.assert_called_once_with(mock_handler.db, 1)
                mock_service_instance.sync_orders.assert_called_once_with(
                    modified_since_hours=24, status_filter=None
                )

    @pytest.mark.asyncio
    async def test_execute_with_custom_hours(self, mock_handler):
        """Test execution with custom hours parameter."""
        mock_job = MagicMock()
        mock_job.input_data = {"hours": 48, "status_filter": None}

        mock_sync_stats = {
            "created": 10,
            "updated": 5,
            "skipped": 3,
            "errors": 1,
            "total_fetched": 19,
            "details": [],
        }

        with patch(
            "shared.database.set_user_schema"
        ):
            with patch(
                "services.ebay.ebay_order_sync_service.EbayOrderSyncService"
            ) as MockSyncService:
                mock_service_instance = MagicMock()
                mock_service_instance.sync_orders.return_value = mock_sync_stats
                MockSyncService.return_value = mock_service_instance

                result = await mock_handler.execute(mock_job)

                mock_service_instance.sync_orders.assert_called_once_with(
                    modified_since_hours=48, status_filter=None
                )

    @pytest.mark.asyncio
    async def test_execute_with_status_filter(self, mock_handler):
        """Test execution with status filter parameter."""
        mock_job = MagicMock()
        mock_job.input_data = {"hours": 24, "status_filter": "NOT_STARTED"}

        mock_sync_stats = {
            "created": 2,
            "updated": 1,
            "skipped": 0,
            "errors": 0,
            "total_fetched": 3,
            "details": [],
        }

        with patch(
            "shared.database.set_user_schema"
        ):
            with patch(
                "services.ebay.ebay_order_sync_service.EbayOrderSyncService"
            ) as MockSyncService:
                mock_service_instance = MagicMock()
                mock_service_instance.sync_orders.return_value = mock_sync_stats
                MockSyncService.return_value = mock_service_instance

                result = await mock_handler.execute(mock_job)

                mock_service_instance.sync_orders.assert_called_once_with(
                    modified_since_hours=24, status_filter="NOT_STARTED"
                )

    @pytest.mark.asyncio
    async def test_execute_with_fulfilled_status_filter(self, mock_handler):
        """Test execution with FULFILLED status filter."""
        mock_job = MagicMock()
        mock_job.input_data = {"hours": 12, "status_filter": "FULFILLED"}

        mock_sync_stats = {
            "created": 0,
            "updated": 15,
            "skipped": 5,
            "errors": 0,
            "total_fetched": 20,
            "details": [],
        }

        with patch(
            "shared.database.set_user_schema"
        ):
            with patch(
                "services.ebay.ebay_order_sync_service.EbayOrderSyncService"
            ) as MockSyncService:
                mock_service_instance = MagicMock()
                mock_service_instance.sync_orders.return_value = mock_sync_stats
                MockSyncService.return_value = mock_service_instance

                result = await mock_handler.execute(mock_job)

                mock_service_instance.sync_orders.assert_called_once_with(
                    modified_since_hours=12, status_filter="FULFILLED"
                )

    @pytest.mark.asyncio
    async def test_execute_without_shop_id(self, mock_job):
        """Test execution without shop_id returns error."""
        from services.ebay.jobs.ebay_orders_sync_job_handler import (
            EbayOrdersSyncJobHandler,
        )

        mock_db = MagicMock()
        handler = EbayOrdersSyncJobHandler(db=mock_db, shop_id=None, job_id=10)

        result = await handler.execute(mock_job)

        assert result["success"] is False
        assert "shop_id" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_with_none_input_data(self, mock_handler):
        """Test execution with None input_data uses defaults."""
        mock_job = MagicMock()
        mock_job.input_data = None

        mock_sync_stats = {
            "created": 1,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "total_fetched": 1,
            "details": [],
        }

        with patch(
            "shared.database.set_user_schema"
        ):
            with patch(
                "services.ebay.ebay_order_sync_service.EbayOrderSyncService"
            ) as MockSyncService:
                mock_service_instance = MagicMock()
                mock_service_instance.sync_orders.return_value = mock_sync_stats
                MockSyncService.return_value = mock_service_instance

                result = await mock_handler.execute(mock_job)

                # Default hours should be 24, status_filter should be None
                mock_service_instance.sync_orders.assert_called_once_with(
                    modified_since_hours=24, status_filter=None
                )

    @pytest.mark.asyncio
    async def test_execute_exception_returns_error(self, mock_handler, mock_job):
        """Test execution exception returns error dict."""
        with patch(
            "shared.database.set_user_schema"
        ):
            with patch(
                "services.ebay.ebay_order_sync_service.EbayOrderSyncService"
            ) as MockSyncService:
                mock_service_instance = MagicMock()
                mock_service_instance.sync_orders.side_effect = Exception(
                    "API connection failed"
                )
                MockSyncService.return_value = mock_service_instance

                result = await mock_handler.execute(mock_job)

                assert result["success"] is False
                assert "API connection failed" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_value_error_returns_error(self, mock_handler, mock_job):
        """Test execution ValueError returns error dict."""
        mock_job.input_data = {"hours": 1000}  # Invalid hours

        with patch(
            "shared.database.set_user_schema"
        ):
            with patch(
                "services.ebay.ebay_order_sync_service.EbayOrderSyncService"
            ) as MockSyncService:
                mock_service_instance = MagicMock()
                mock_service_instance.sync_orders.side_effect = ValueError(
                    "modified_since_hours must be between 1 and 720"
                )
                MockSyncService.return_value = mock_service_instance

                result = await mock_handler.execute(mock_job)

                assert result["success"] is False
                assert "720" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_sets_user_schema_for_multi_tenant(
        self, mock_handler, mock_job
    ):
        """Test that user schema is correctly set for multi-tenant isolation."""
        mock_sync_stats = {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "total_fetched": 0,
            "details": [],
        }

        with patch(
            "shared.database.set_user_schema"
        ) as mock_set_schema:
            with patch(
                "services.ebay.ebay_order_sync_service.EbayOrderSyncService"
            ) as MockSyncService:
                mock_service_instance = MagicMock()
                mock_service_instance.sync_orders.return_value = mock_sync_stats
                MockSyncService.return_value = mock_service_instance

                await mock_handler.execute(mock_job)

                # Verify set_user_schema was called before sync
                mock_set_schema.assert_called_once_with(mock_handler.db, 1)

    @pytest.mark.asyncio
    async def test_execute_empty_results(self, mock_handler, mock_job):
        """Test execution with no orders to sync."""
        mock_sync_stats = {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "total_fetched": 0,
            "details": [],
        }

        with patch(
            "shared.database.set_user_schema"
        ):
            with patch(
                "services.ebay.ebay_order_sync_service.EbayOrderSyncService"
            ) as MockSyncService:
                mock_service_instance = MagicMock()
                mock_service_instance.sync_orders.return_value = mock_sync_stats
                MockSyncService.return_value = mock_service_instance

                result = await mock_handler.execute(mock_job)

                assert result["success"] is True
                assert result["created"] == 0
                assert result["updated"] == 0
                assert result["total_fetched"] == 0

    @pytest.mark.asyncio
    async def test_execute_partial_errors(self, mock_handler, mock_job):
        """Test execution with some order processing errors."""
        mock_sync_stats = {
            "created": 8,
            "updated": 5,
            "skipped": 2,
            "errors": 3,
            "total_fetched": 18,
            "details": [
                {"order_id": "12-1", "action": "created"},
                {"order_id": "12-2", "action": "error", "error": "Invalid data"},
            ],
        }

        with patch(
            "shared.database.set_user_schema"
        ):
            with patch(
                "services.ebay.ebay_order_sync_service.EbayOrderSyncService"
            ) as MockSyncService:
                mock_service_instance = MagicMock()
                mock_service_instance.sync_orders.return_value = mock_sync_stats
                MockSyncService.return_value = mock_service_instance

                result = await mock_handler.execute(mock_job)

                # Should still be successful even with partial errors
                assert result["success"] is True
                assert result["errors"] == 3
                assert result["created"] == 8
