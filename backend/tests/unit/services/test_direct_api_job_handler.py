"""
Unit Tests for DirectAPIJobHandler

Tests the DirectAPI base class created in Phase 3 to factorize eBay/Etsy handlers.

Created: 2026-01-15
Phase: 03-01 DirectAPI Handler Base
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from models.user.marketplace_job import MarketplaceJob, JobStatus
from services.marketplace.direct_api_job_handler import DirectAPIJobHandler


# ===== TEST HANDLER IMPLEMENTATIONS =====

class MockEbayService:
    """Mock eBay service for testing."""

    def __init__(self, db):
        self.db = db

    async def publish_product(self, product_id: int) -> dict:
        """Mock publish method."""
        if product_id == 999:
            raise ValueError("Invalid product ID")
        if product_id == 888:
            return {"success": False, "error": "Product not found"}
        return {"success": True, "ebay_listing_id": f"ebay-{product_id}"}


class MockEtsyService:
    """Mock Etsy service for testing."""

    def __init__(self, db):
        self.db = db

    async def update_product(self, product_id: int) -> dict:
        """Mock update method."""
        return {"success": True, "etsy_listing_id": f"etsy-{product_id}"}


class ConcreteEbayHandler(DirectAPIJobHandler):
    """Concrete implementation for eBay testing."""

    ACTION_CODE = "ebay_test"

    def get_service(self) -> MockEbayService:
        return MockEbayService(self.db)

    def get_service_method_name(self) -> str:
        return "publish_product"

    def create_tasks(self, job: MarketplaceJob) -> list[str]:
        """Return empty task list for tests (DirectAPI handlers don't use tasks)."""
        return []


class ConcreteEtsyHandler(DirectAPIJobHandler):
    """Concrete implementation for Etsy testing."""

    ACTION_CODE = "etsy_test"

    def get_service(self) -> MockEtsyService:
        return MockEtsyService(self.db)

    def get_service_method_name(self) -> str:
        return "update_product"

    def create_tasks(self, job: MarketplaceJob) -> list[str]:
        """Return empty task list for tests (DirectAPI handlers don't use tasks)."""
        return []


class IncompleteHandler(DirectAPIJobHandler):
    """Handler missing abstract method implementations (should fail instantiation)."""

    ACTION_CODE = "incomplete"

    def get_service(self):
        return MockEbayService(self.db)

    # Missing: get_service_method_name()


# ===== FIXTURES =====

@pytest.fixture
def db_session():
    """Mock database session."""
    session = Mock(spec=["query", "add", "flush", "commit", "rollback", "refresh"])
    return session


@pytest.fixture
def sample_job():
    """Sample MarketplaceJob for testing."""
    return MarketplaceJob(
        id=1,
        marketplace="ebay",
        action_type_id=1,
        product_id=101,
        status=JobStatus.PENDING,
        priority=3,
        retry_count=0,
        max_retries=3,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def ebay_handler(db_session):
    """Instantiate eBay test handler."""
    return ConcreteEbayHandler(db=db_session, shop_id=123, job_id=1)


@pytest.fixture
def etsy_handler(db_session):
    """Instantiate Etsy test handler."""
    return ConcreteEtsyHandler(db=db_session, shop_id=456, job_id=2)


# ===== TESTS =====

class TestDirectAPIJobHandlerValidation:
    """Tests for input validation."""

    @pytest.mark.asyncio
    async def test_execute_fails_when_product_id_is_none(self, ebay_handler):
        """Should return error when product_id is None."""
        job = MarketplaceJob(
            id=1,
            marketplace="ebay",
            action_type_id=1,
            product_id=None,  # Missing product_id
            status=JobStatus.PENDING,
            priority=3,
            retry_count=0,
            max_retries=3,
            created_at=datetime.now(timezone.utc),
        )

        result = await ebay_handler.execute(job)

        assert result["success"] is False
        assert result["error"] == "product_id required"

    @pytest.mark.asyncio
    async def test_execute_fails_when_product_id_is_zero(self, ebay_handler):
        """Should return error when product_id is 0."""
        job = MarketplaceJob(
            id=1,
            marketplace="ebay",
            action_type_id=1,
            product_id=0,  # Invalid product_id
            status=JobStatus.PENDING,
            priority=3,
            retry_count=0,
            max_retries=3,
            created_at=datetime.now(timezone.utc),
        )

        result = await ebay_handler.execute(job)

        assert result["success"] is False
        assert result["error"] == "product_id required"


class TestDirectAPIJobHandlerServiceDelegation:
    """Tests for service instantiation and method delegation."""

    @pytest.mark.asyncio
    async def test_get_service_returns_correct_service_instance(self, ebay_handler):
        """Should instantiate correct service class."""
        service = ebay_handler.get_service()

        assert isinstance(service, MockEbayService)
        assert service.db == ebay_handler.db

    @pytest.mark.asyncio
    async def test_get_service_method_name_returns_correct_method(self, ebay_handler):
        """Should return correct method name."""
        method_name = ebay_handler.get_service_method_name()

        assert method_name == "publish_product"

    @pytest.mark.asyncio
    async def test_execute_calls_service_method_with_product_id(
        self, ebay_handler, sample_job
    ):
        """Should call service method with correct product_id."""
        with patch.object(
            MockEbayService, "publish_product", new_callable=AsyncMock
        ) as mock_method:
            mock_method.return_value = {
                "success": True,
                "ebay_listing_id": "ebay-101",
            }

            result = await ebay_handler.execute(sample_job)

            # Verify method was called with correct product_id
            mock_method.assert_called_once_with(101)
            assert result["success"] is True


class TestDirectAPIJobHandlerResultHandling:
    """Tests for result handling and logging."""

    @pytest.mark.asyncio
    async def test_execute_returns_success_when_service_succeeds(
        self, ebay_handler, sample_job
    ):
        """Should return success=True when service succeeds."""
        result = await ebay_handler.execute(sample_job)

        assert result["success"] is True
        assert result["ebay_listing_id"] == "ebay-101"

    @pytest.mark.asyncio
    async def test_execute_returns_failure_when_service_fails(
        self, ebay_handler, db_session
    ):
        """Should return success=False when service returns error."""
        job = MarketplaceJob(
            id=1,
            marketplace="ebay",
            action_type_id=1,
            product_id=888,  # Product that triggers failure in mock
            status=JobStatus.PENDING,
            priority=3,
            retry_count=0,
            max_retries=3,
            created_at=datetime.now(timezone.utc),
        )

        result = await ebay_handler.execute(job)

        assert result["success"] is False
        assert result["error"] == "Product not found"

    @pytest.mark.asyncio
    async def test_execute_logs_success_with_listing_id(
        self, ebay_handler, sample_job
    ):
        """Should log success with eBay listing ID."""
        with patch.object(ebay_handler, "log_success") as mock_log:
            result = await ebay_handler.execute(sample_job)

            # Verify success was logged
            mock_log.assert_called_once()
            call_args = mock_log.call_args[0][0]
            assert "product 101" in call_args
            assert "ebay-101" in call_args

    @pytest.mark.asyncio
    async def test_execute_logs_error_with_error_message(self, ebay_handler, db_session):
        """Should log error with detailed error message."""
        job = MarketplaceJob(
            id=1,
            marketplace="ebay",
            action_type_id=1,
            product_id=888,
            status=JobStatus.PENDING,
            priority=3,
            retry_count=0,
            max_retries=3,
            created_at=datetime.now(timezone.utc),
        )

        with patch.object(ebay_handler, "log_error") as mock_log:
            result = await ebay_handler.execute(job)

            # Verify error was logged
            mock_log.assert_called_once()
            call_args = mock_log.call_args[0][0]
            assert "product 888" in call_args
            assert "Product not found" in call_args


class TestDirectAPIJobHandlerExceptionHandling:
    """Tests for exception handling."""

    @pytest.mark.asyncio
    async def test_execute_catches_exceptions_and_returns_error(
        self, ebay_handler, db_session
    ):
        """Should catch exceptions and return error dict."""
        job = MarketplaceJob(
            id=1,
            marketplace="ebay",
            action_type_id=1,
            product_id=999,  # Product that triggers exception in mock
            status=JobStatus.PENDING,
            priority=3,
            retry_count=0,
            max_retries=3,
            created_at=datetime.now(timezone.utc),
        )

        result = await ebay_handler.execute(job)

        assert result["success"] is False
        assert "Invalid product ID" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_logs_exception_with_traceback(
        self, ebay_handler, db_session
    ):
        """Should log exception with full traceback."""
        job = MarketplaceJob(
            id=1,
            marketplace="ebay",
            action_type_id=1,
            product_id=999,
            status=JobStatus.PENDING,
            priority=3,
            retry_count=0,
            max_retries=3,
            created_at=datetime.now(timezone.utc),
        )

        with patch.object(ebay_handler, "log_error") as mock_log:
            result = await ebay_handler.execute(job)

            # Verify exception was logged with exc_info=True
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[1]["exc_info"] is True


class TestDirectAPIJobHandlerEtsyIntegration:
    """Tests specific to Etsy handlers."""

    @pytest.mark.asyncio
    async def test_etsy_handler_returns_etsy_listing_id(
        self, etsy_handler, sample_job
    ):
        """Should return etsy_listing_id in result."""
        result = await etsy_handler.execute(sample_job)

        assert result["success"] is True
        assert result["etsy_listing_id"] == "etsy-101"

    @pytest.mark.asyncio
    async def test_etsy_handler_logs_success_with_etsy_listing_id(
        self, etsy_handler, sample_job
    ):
        """Should log Etsy listing ID in success message."""
        with patch.object(etsy_handler, "log_success") as mock_log:
            result = await etsy_handler.execute(sample_job)

            # Verify Etsy listing ID appears in log
            call_args = mock_log.call_args[0][0]
            assert "etsy-101" in call_args


class TestDirectAPIJobHandlerAbstractMethods:
    """Tests for abstract method enforcement."""

    def test_cannot_instantiate_handler_without_get_service(self, db_session):
        """Should fail to instantiate handler missing get_service()."""

        class MissingGetService(DirectAPIJobHandler):
            ACTION_CODE = "missing"

            def get_service_method_name(self) -> str:
                return "test"

        with pytest.raises(TypeError) as exc_info:
            MissingGetService(db=db_session, shop_id=1, job_id=1)

        assert "get_service" in str(exc_info.value)

    def test_cannot_instantiate_handler_without_get_service_method_name(
        self, db_session
    ):
        """Should fail to instantiate handler missing get_service_method_name()."""

        class MissingGetMethod(DirectAPIJobHandler):
            ACTION_CODE = "missing"

            def get_service(self):
                return MockEbayService(self.db)

        with pytest.raises(TypeError) as exc_info:
            MissingGetMethod(db=db_session, shop_id=1, job_id=1)

        assert "get_service_method_name" in str(exc_info.value)


class TestDirectAPIJobHandlerLogging:
    """Tests for logging behavior."""

    @pytest.mark.asyncio
    async def test_logs_start_before_execution(self, ebay_handler, sample_job):
        """Should log start before calling service."""
        with patch.object(ebay_handler, "log_start") as mock_log:
            result = await ebay_handler.execute(sample_job)

            # Verify start was logged
            mock_log.assert_called_once()
            call_args = mock_log.call_args[0][0]
            assert "publish_product" in call_args
            assert "101" in call_args
