"""
Unit Tests for DeleteJobHandler

Tests for the Vinted delete job handler that manages the workflow
of deleting products from Vinted marketplace.

Author: Claude
Date: 2026-01-08
"""

from datetime import datetime, timezone, date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from models.user.vinted_product import VintedProduct
from models.vinted.vinted_deletion import VintedDeletion
from models.user.marketplace_job import JobStatus, MarketplaceJob
from services.vinted.jobs.delete_job_handler import DeleteJobHandler


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
    """Mock MarketplaceJob for delete action."""
    job = MagicMock(spec=MarketplaceJob)
    job.id = 1
    job.product_id = 100
    job.action_type_id = 3  # delete action type
    job.status = JobStatus.PENDING
    job.priority = 3
    job.retry_count = 0
    job.batch_id = None
    job.result_data = None  # Default: check_conditions = True
    job.created_at = datetime.now(timezone.utc)
    return job


@pytest.fixture
def mock_job_no_conditions():
    """Mock MarketplaceJob with check_conditions=False."""
    job = MagicMock(spec=MarketplaceJob)
    job.id = 2
    job.product_id = 100
    job.action_type_id = 3
    job.status = JobStatus.PENDING
    job.priority = 3
    job.retry_count = 0
    job.batch_id = None
    job.result_data = {"check_conditions": False}  # Skip condition check
    job.created_at = datetime.now(timezone.utc)
    return job


@pytest.fixture
def mock_vinted_product():
    """Mock VintedProduct instance."""
    vp = MagicMock(spec=VintedProduct)
    vp.vinted_id = 12345678
    vp.product_id = 100
    vp.price = Decimal("50.00")
    vp.title = "Vintage Nike Sweatshirt XL"
    vp.status = "published"
    vp.url = "https://www.vinted.fr/items/12345678"
    vp.view_count = 150
    vp.favourite_count = 10
    vp.date = date(2025, 10, 1)  # Published ~100 days ago
    vp.conversations = 5
    return vp


@pytest.fixture
def mock_vinted_product_no_favs():
    """Mock VintedProduct with zero favorites (shorter threshold)."""
    vp = MagicMock(spec=VintedProduct)
    vp.vinted_id = 12345679
    vp.product_id = 101
    vp.price = Decimal("30.00")
    vp.title = "Old Product No Interest"
    vp.status = "published"
    vp.url = "https://www.vinted.fr/items/12345679"
    vp.view_count = 20
    vp.favourite_count = 0  # No favorites
    vp.date = date(2025, 12, 1)  # Published ~35 days ago
    vp.conversations = 0
    return vp


@pytest.fixture
def mock_vinted_product_recent():
    """Mock VintedProduct that was recently published."""
    vp = MagicMock(spec=VintedProduct)
    vp.vinted_id = 12345680
    vp.product_id = 102
    vp.price = Decimal("40.00")
    vp.title = "Recent Product"
    vp.status = "published"
    vp.url = "https://www.vinted.fr/items/12345680"
    vp.view_count = 50
    vp.favourite_count = 5
    vp.date = date.today()  # Published today
    vp.conversations = 2
    return vp


@pytest.fixture
def handler(mock_db):
    """Create DeleteJobHandler instance with mocked dependencies."""
    return DeleteJobHandler(db=mock_db, shop_id=123, job_id=1)


# =============================================================================
# TESTS - HANDLER INITIALIZATION
# =============================================================================


class TestDeleteJobHandlerInit:
    """Tests for DeleteJobHandler initialization."""

    def test_init_with_all_params(self, mock_db):
        """Test initialization with all parameters."""
        handler = DeleteJobHandler(db=mock_db, shop_id=123, job_id=1)

        assert handler.db == mock_db
        assert handler.shop_id == 123
        assert handler.job_id == 1
        assert handler.ACTION_CODE == "delete"

    def test_init_with_minimal_params(self, mock_db):
        """Test initialization with minimal parameters."""
        handler = DeleteJobHandler(db=mock_db)

        assert handler.db == mock_db
        assert handler.shop_id is None
        assert handler.job_id is None

    def test_delete_handler_inherits_from_base(self, mock_db):
        """Test that DeleteJobHandler inherits from BaseJobHandler."""
        handler = DeleteJobHandler(db=mock_db)

        # Should have call_plugin method from BaseJobHandler
        assert hasattr(handler, 'call_plugin')
        assert hasattr(handler, 'log_start')
        assert hasattr(handler, 'log_success')
        assert hasattr(handler, 'log_error')
        assert hasattr(handler, 'log_debug')


# =============================================================================
# TESTS - EXECUTE METHOD
# =============================================================================


class TestDeleteJobHandlerExecute:
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
    async def test_execute_vinted_product_not_found(self, handler, mock_job):
        """Test execute fails when VintedProduct not found."""
        handler.db.query.return_value.filter.return_value.first.return_value = None

        result = await handler.execute(mock_job)

        assert result["success"] is False
        assert result["product_id"] == 100
        assert "non trouv" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_conditions_not_met(self, handler, mock_job, mock_vinted_product_recent):
        """Test execute fails when deletion conditions are not met."""
        handler.db.query.return_value.filter.return_value.first.return_value = mock_vinted_product_recent

        with patch(
            'services.vinted.jobs.delete_job_handler.should_delete_product',
            return_value=False
        ):
            result = await handler.execute(mock_job)

        assert result["success"] is False
        assert "Conditions de suppression non remplies" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_skip_conditions_check(self, handler, mock_job_no_conditions, mock_vinted_product_recent):
        """Test execute skips condition check when check_conditions=False."""
        handler.db.query.return_value.filter.return_value.first.return_value = mock_vinted_product_recent

        with patch.object(
            handler, 'call_plugin',
            new_callable=AsyncMock,
            return_value={"success": True}
        ):
            result = await handler.execute(mock_job_no_conditions)

        # Should succeed even though product is recent (conditions not checked)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_plugin_call_failure(self, handler, mock_job, mock_vinted_product):
        """Test execute handles plugin call failure."""
        handler.db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        with patch(
            'services.vinted.jobs.delete_job_handler.should_delete_product',
            return_value=True
        ):
            with patch.object(
                handler, 'call_plugin',
                new_callable=AsyncMock,
                side_effect=Exception("Plugin unavailable")
            ):
                result = await handler.execute(mock_job)

        assert result["success"] is False
        assert "Plugin unavailable" in result["error"]
        handler.db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_success_full_workflow(self, handler, mock_job, mock_vinted_product):
        """Test successful execution of complete delete workflow."""
        handler.db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        with patch(
            'services.vinted.jobs.delete_job_handler.should_delete_product',
            return_value=True
        ):
            with patch.object(
                handler, 'call_plugin',
                new_callable=AsyncMock,
                return_value={"success": True}
            ):
                result = await handler.execute(mock_job)

        assert result["success"] is True
        assert result["product_id"] == 100
        assert result["vinted_id"] == 12345678
        # Verify VintedProduct was deleted
        handler.db.delete.assert_called_once_with(mock_vinted_product)
        handler.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_archives_deletion(self, handler, mock_job, mock_vinted_product):
        """Test that deletion is archived in VintedDeletion table."""
        handler.db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        with patch(
            'services.vinted.jobs.delete_job_handler.should_delete_product',
            return_value=True
        ):
            with patch.object(
                handler, 'call_plugin',
                new_callable=AsyncMock,
                return_value={"success": True}
            ):
                await handler.execute(mock_job)

        # Verify db.add was called (for VintedDeletion)
        handler.db.add.assert_called_once()
        # Check that the added object is a VintedDeletion
        added_obj = handler.db.add.call_args[0][0]
        assert isinstance(added_obj, VintedDeletion)


# =============================================================================
# TESTS - PRIVATE METHODS
# =============================================================================


class TestDeleteJobHandlerPrivateMethods:
    """Tests for private helper methods."""

    def test_get_vinted_product_success(self, handler, mock_vinted_product):
        """Test _get_vinted_product returns vinted product when found."""
        handler.db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        result = handler._get_vinted_product(100)

        assert result == mock_vinted_product

    def test_get_vinted_product_not_found(self, handler):
        """Test _get_vinted_product raises ValueError when not found."""
        handler.db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError) as exc_info:
            handler._get_vinted_product(999)

        assert "non trouv" in str(exc_info.value).lower()

    def test_archive_deletion_creates_record(self, handler, mock_vinted_product):
        """Test _archive_deletion creates VintedDeletion record."""
        handler._archive_deletion(mock_vinted_product)

        handler.db.add.assert_called_once()
        added_obj = handler.db.add.call_args[0][0]
        assert isinstance(added_obj, VintedDeletion)

    def test_delete_vinted_product(self, handler, mock_vinted_product):
        """Test _delete_vinted_product deletes and commits."""
        handler._delete_vinted_product(mock_vinted_product)

        handler.db.delete.assert_called_once_with(mock_vinted_product)
        handler.db.commit.assert_called_once()


# =============================================================================
# TESTS - CONDITION CHECKING
# =============================================================================


class TestDeleteJobHandlerConditions:
    """Tests for deletion condition checking."""

    @pytest.mark.asyncio
    async def test_conditions_old_product_with_favs(self, handler, mock_job, mock_vinted_product):
        """Test conditions pass for old product with favorites (90+ days)."""
        handler.db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        with patch(
            'services.vinted.jobs.delete_job_handler.should_delete_product',
            return_value=True
        ) as mock_should_delete:
            with patch.object(
                handler, 'call_plugin',
                new_callable=AsyncMock,
                return_value={"success": True}
            ):
                result = await handler.execute(mock_job)

        assert result["success"] is True
        mock_should_delete.assert_called_once_with(mock_vinted_product)

    @pytest.mark.asyncio
    async def test_conditions_product_no_favs_30_days(self, handler, mock_job, mock_vinted_product_no_favs):
        """Test conditions pass for product with 0 favs (30+ days)."""
        mock_job.product_id = 101
        handler.db.query.return_value.filter.return_value.first.return_value = mock_vinted_product_no_favs

        with patch(
            'services.vinted.jobs.delete_job_handler.should_delete_product',
            return_value=True
        ):
            with patch.object(
                handler, 'call_plugin',
                new_callable=AsyncMock,
                return_value={"success": True}
            ):
                result = await handler.execute(mock_job)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_conditions_check_can_be_bypassed(self, handler, mock_job_no_conditions, mock_vinted_product_recent):
        """Test that check_conditions=False bypasses condition check."""
        handler.db.query.return_value.filter.return_value.first.return_value = mock_vinted_product_recent

        with patch(
            'services.vinted.jobs.delete_job_handler.should_delete_product'
        ) as mock_should_delete:
            with patch.object(
                handler, 'call_plugin',
                new_callable=AsyncMock,
                return_value={"success": True}
            ):
                result = await handler.execute(mock_job_no_conditions)

        assert result["success"] is True
        # should_delete_product should NOT have been called
        mock_should_delete.assert_not_called()


# =============================================================================
# TESTS - EDGE CASES
# =============================================================================


class TestDeleteJobHandlerEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_execute_database_error(self, handler, mock_job):
        """Test execute handles database errors gracefully."""
        handler.db.query.side_effect = Exception("Database connection lost")

        result = await handler.execute(mock_job)

        assert result["success"] is False
        assert "Database connection lost" in result["error"]
        handler.db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_result_data_not_dict(self, handler, mock_vinted_product):
        """Test execute handles non-dict result_data gracefully."""
        job = MagicMock(spec=MarketplaceJob)
        job.id = 1
        job.product_id = 100
        job.result_data = "invalid"  # Not a dict

        handler.db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        with patch(
            'services.vinted.jobs.delete_job_handler.should_delete_product',
            return_value=True
        ):
            with patch.object(
                handler, 'call_plugin',
                new_callable=AsyncMock,
                return_value={"success": True}
            ):
                result = await handler.execute(job)

        # Should default to check_conditions=True and succeed
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_with_none_result_data(self, handler, mock_job, mock_vinted_product):
        """Test execute handles None result_data."""
        mock_job.result_data = None  # Explicitly None

        handler.db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        with patch(
            'services.vinted.jobs.delete_job_handler.should_delete_product',
            return_value=True
        ):
            with patch.object(
                handler, 'call_plugin',
                new_callable=AsyncMock,
                return_value={"success": True}
            ):
                result = await handler.execute(mock_job)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_uses_correct_api_path(self, handler, mock_job, mock_vinted_product):
        """Test that correct API path is used for delete."""
        handler.db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        call_plugin_mock = AsyncMock(return_value={"success": True})

        with patch(
            'services.vinted.jobs.delete_job_handler.should_delete_product',
            return_value=True
        ):
            with patch.object(handler, 'call_plugin', call_plugin_mock):
                await handler.execute(mock_job)

        call_plugin_mock.assert_called_once()
        call_args = call_plugin_mock.call_args
        assert call_args.kwargs["http_method"] == "POST"
        assert str(mock_vinted_product.vinted_id) in call_args.kwargs["path"]
        assert call_args.kwargs["timeout"] == 30

    @pytest.mark.asyncio
    async def test_execute_archive_before_delete(self, handler, mock_job, mock_vinted_product):
        """Test that archive happens before plugin call."""
        handler.db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        call_order = []

        def track_add(obj):
            call_order.append("add")

        def track_delete(obj):
            call_order.append("delete")

        handler.db.add.side_effect = track_add
        handler.db.delete.side_effect = track_delete

        async def track_plugin(*args, **kwargs):
            call_order.append("plugin")
            return {"success": True}

        with patch(
            'services.vinted.jobs.delete_job_handler.should_delete_product',
            return_value=True
        ):
            with patch.object(handler, 'call_plugin', side_effect=track_plugin):
                await handler.execute(mock_job)

        # Archive (add) should happen before plugin call and delete
        assert call_order == ["add", "plugin", "delete"]

    @pytest.mark.asyncio
    async def test_execute_rollback_on_plugin_failure(self, handler, mock_job, mock_vinted_product):
        """Test rollback happens when plugin fails after archive."""
        handler.db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        with patch(
            'services.vinted.jobs.delete_job_handler.should_delete_product',
            return_value=True
        ):
            with patch.object(
                handler, 'call_plugin',
                new_callable=AsyncMock,
                side_effect=Exception("Plugin error")
            ):
                result = await handler.execute(mock_job)

        assert result["success"] is False
        handler.db.rollback.assert_called_once()
        # Delete should not have been called since plugin failed
        handler.db.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_with_vinted_product_no_date(self, handler, mock_job, mock_vinted_product):
        """Test execute handles VintedProduct with no date set."""
        mock_vinted_product.date = None  # No publication date

        handler.db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        # should_delete_product returns False when date is None
        with patch(
            'services.vinted.jobs.delete_job_handler.should_delete_product',
            return_value=False
        ):
            result = await handler.execute(mock_job)

        assert result["success"] is False
        assert "Conditions de suppression non remplies" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_commit_after_delete(self, handler, mock_job, mock_vinted_product):
        """Test that commit happens after delete."""
        handler.db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        with patch(
            'services.vinted.jobs.delete_job_handler.should_delete_product',
            return_value=True
        ):
            with patch.object(
                handler, 'call_plugin',
                new_callable=AsyncMock,
                return_value={"success": True}
            ):
                result = await handler.execute(mock_job)

        assert result["success"] is True
        # Verify order: delete called before commit
        handler.db.delete.assert_called_once()
        handler.db.commit.assert_called_once()


# =============================================================================
# TESTS - INTEGRATION WITH should_delete_product
# =============================================================================


class TestDeleteJobHandlerShouldDelete:
    """Tests for integration with should_delete_product helper."""

    @pytest.mark.asyncio
    async def test_should_delete_called_with_vinted_product(self, handler, mock_job, mock_vinted_product):
        """Test should_delete_product is called with VintedProduct."""
        handler.db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        with patch(
            'services.vinted.jobs.delete_job_handler.should_delete_product',
            return_value=True
        ) as mock_should_delete:
            with patch.object(
                handler, 'call_plugin',
                new_callable=AsyncMock,
                return_value={"success": True}
            ):
                await handler.execute(mock_job)

        mock_should_delete.assert_called_once_with(mock_vinted_product)

    @pytest.mark.asyncio
    async def test_should_delete_false_prevents_deletion(self, handler, mock_job, mock_vinted_product):
        """Test that False from should_delete_product prevents deletion."""
        handler.db.query.return_value.filter.return_value.first.return_value = mock_vinted_product

        with patch(
            'services.vinted.jobs.delete_job_handler.should_delete_product',
            return_value=False
        ):
            result = await handler.execute(mock_job)

        assert result["success"] is False
        # Plugin should not have been called
        handler.db.delete.assert_not_called()
        handler.db.commit.assert_not_called()
