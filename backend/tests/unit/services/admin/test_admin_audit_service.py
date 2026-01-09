"""
Unit tests for AdminAuditService.

Coverage:
- log_action: basic logging, with request context, without request
- list_logs: pagination, filtering by admin/action/resource/date/search
- get_log: found, not found
- get_admin_actions: returns actions for admin
- get_resource_history: returns history for resource
- build_user_details: with/without changed_fields and before values

Author: Claude
Date: 2026-01-08
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from services.admin_audit_service import AdminAuditService
from models.public.admin_audit_log import AdminAuditLog
from models.public.user import User


class TestLogAction:
    """Tests for AdminAuditService.log_action method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=Session)
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        return db

    @pytest.fixture
    def mock_admin(self):
        """Create mock admin user."""
        admin = Mock(spec=User)
        admin.id = 1
        admin.email = "admin@example.com"
        return admin

    def test_log_action_basic(self, mock_db, mock_admin):
        """Test basic action logging without request."""
        result = AdminAuditService.log_action(
            mock_db,
            admin=mock_admin,
            action="CREATE",
            resource_type="user",
            resource_id="123",
            resource_name="test@example.com"
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_log_action_with_request_context(self, mock_db, mock_admin):
        """Test logging with request context extracts IP and user agent."""
        mock_request = Mock()
        mock_request.headers = {
            "X-Forwarded-For": "192.168.1.1, 10.0.0.1",
            "User-Agent": "Mozilla/5.0 Test Browser"
        }
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        result = AdminAuditService.log_action(
            mock_db,
            admin=mock_admin,
            action="UPDATE",
            resource_type="brand",
            resource_id="Nike",
            resource_name="Nike",
            request=mock_request
        )

        mock_db.add.assert_called_once()
        # Verify the log entry was created with IP from X-Forwarded-For
        added_log = mock_db.add.call_args[0][0]
        assert added_log.ip_address == "192.168.1.1"
        assert added_log.user_agent == "Mozilla/5.0 Test Browser"

    def test_log_action_with_direct_client_ip(self, mock_db, mock_admin):
        """Test logging uses client.host when no X-Forwarded-For."""
        mock_request = Mock()
        mock_request.headers = {"User-Agent": "TestAgent"}
        mock_request.client = Mock()
        mock_request.client.host = "10.0.0.5"

        result = AdminAuditService.log_action(
            mock_db,
            admin=mock_admin,
            action="DELETE",
            resource_type="color",
            request=mock_request
        )

        added_log = mock_db.add.call_args[0][0]
        assert added_log.ip_address == "10.0.0.5"

    def test_log_action_with_details(self, mock_db, mock_admin):
        """Test logging with details dictionary."""
        details = {"changed": {"full_name": "New Name"}, "before": {"full_name": "Old Name"}}

        result = AdminAuditService.log_action(
            mock_db,
            admin=mock_admin,
            action="UPDATE",
            resource_type="user",
            resource_id="123",
            details=details
        )

        added_log = mock_db.add.call_args[0][0]
        assert added_log.details == details

    def test_log_action_truncates_user_agent(self, mock_db, mock_admin):
        """Test that user agent is truncated to 500 characters."""
        mock_request = Mock()
        long_user_agent = "A" * 600
        mock_request.headers = {"User-Agent": long_user_agent}
        mock_request.client = None

        result = AdminAuditService.log_action(
            mock_db,
            admin=mock_admin,
            action="CREATE",
            resource_type="material",
            request=mock_request
        )

        added_log = mock_db.add.call_args[0][0]
        assert len(added_log.user_agent) == 500


class TestListLogs:
    """Tests for AdminAuditService.list_logs method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock(spec=Session)

    def test_list_logs_returns_logs_and_count(self, mock_db):
        """Test list_logs returns tuple of logs and total count."""
        mock_log1 = Mock(spec=AdminAuditLog)
        mock_log2 = Mock(spec=AdminAuditLog)

        mock_query = MagicMock()
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            mock_log1, mock_log2
        ]
        mock_db.query.return_value = mock_query

        logs, total = AdminAuditService.list_logs(mock_db)

        assert total == 2
        assert len(logs) == 2
        mock_db.query.assert_called_once_with(AdminAuditLog)

    def test_list_logs_with_pagination(self, mock_db):
        """Test list_logs with skip and limit parameters."""
        mock_query = MagicMock()
        mock_query.count.return_value = 100
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        AdminAuditService.list_logs(mock_db, skip=20, limit=10)

        mock_query.order_by.return_value.offset.assert_called_once_with(20)
        mock_query.order_by.return_value.offset.return_value.limit.assert_called_once_with(10)

    def test_list_logs_filter_by_admin_id(self, mock_db):
        """Test list_logs with admin_id filter."""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        AdminAuditService.list_logs(mock_db, admin_id=1)

        mock_query.filter.assert_called_once()

    def test_list_logs_filter_by_action(self, mock_db):
        """Test list_logs with action filter."""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        AdminAuditService.list_logs(mock_db, action="CREATE")

        mock_query.filter.assert_called_once()

    def test_list_logs_filter_by_resource_type(self, mock_db):
        """Test list_logs with resource_type filter."""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 8
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        AdminAuditService.list_logs(mock_db, resource_type="user")

        mock_query.filter.assert_called_once()

    def test_list_logs_filter_by_date_range(self, mock_db):
        """Test list_logs with date_from and date_to filters."""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        date_from = datetime(2025, 1, 1)
        date_to = datetime(2025, 12, 31)

        AdminAuditService.list_logs(mock_db, date_from=date_from, date_to=date_to)

        mock_query.filter.assert_called_once()

    def test_list_logs_filter_by_search(self, mock_db):
        """Test list_logs with search filter on resource_name."""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        AdminAuditService.list_logs(mock_db, search="test@example")

        mock_query.filter.assert_called_once()

    def test_list_logs_empty_result(self, mock_db):
        """Test list_logs returns empty list when no logs found."""
        mock_query = MagicMock()
        mock_query.count.return_value = 0
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        logs, total = AdminAuditService.list_logs(mock_db)

        assert total == 0
        assert logs == []


class TestGetLog:
    """Tests for AdminAuditService.get_log method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock(spec=Session)

    def test_get_log_found(self, mock_db):
        """Test get_log returns log when found."""
        mock_log = Mock(spec=AdminAuditLog)
        mock_log.id = 1
        mock_log.action = "CREATE"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_log

        result = AdminAuditService.get_log(mock_db, log_id=1)

        assert result is not None
        assert result.id == 1
        mock_db.query.assert_called_once_with(AdminAuditLog)

    def test_get_log_not_found(self, mock_db):
        """Test get_log returns None when not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = AdminAuditService.get_log(mock_db, log_id=999)

        assert result is None


class TestGetAdminActions:
    """Tests for AdminAuditService.get_admin_actions method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock(spec=Session)

    def test_get_admin_actions_returns_list(self, mock_db):
        """Test get_admin_actions returns list of logs for admin."""
        mock_log1 = Mock(spec=AdminAuditLog)
        mock_log2 = Mock(spec=AdminAuditLog)

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_log1, mock_log2
        ]

        result = AdminAuditService.get_admin_actions(mock_db, admin_id=1)

        assert len(result) == 2
        mock_db.query.assert_called_once_with(AdminAuditLog)

    def test_get_admin_actions_with_custom_limit(self, mock_db):
        """Test get_admin_actions respects limit parameter."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        AdminAuditService.get_admin_actions(mock_db, admin_id=1, limit=50)

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.assert_called_once_with(50)

    def test_get_admin_actions_empty_result(self, mock_db):
        """Test get_admin_actions returns empty list when no actions found."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = AdminAuditService.get_admin_actions(mock_db, admin_id=999)

        assert result == []


class TestGetResourceHistory:
    """Tests for AdminAuditService.get_resource_history method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock(spec=Session)

    def test_get_resource_history_returns_list(self, mock_db):
        """Test get_resource_history returns list of logs for resource."""
        mock_log1 = Mock(spec=AdminAuditLog)
        mock_log2 = Mock(spec=AdminAuditLog)

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_log1, mock_log2
        ]

        result = AdminAuditService.get_resource_history(
            mock_db, resource_type="user", resource_id="123"
        )

        assert len(result) == 2

    def test_get_resource_history_with_custom_limit(self, mock_db):
        """Test get_resource_history respects limit parameter."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        AdminAuditService.get_resource_history(
            mock_db, resource_type="brand", resource_id="Nike", limit=25
        )

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.assert_called_once_with(25)

    def test_get_resource_history_empty_result(self, mock_db):
        """Test get_resource_history returns empty list when no history found."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = AdminAuditService.get_resource_history(
            mock_db, resource_type="color", resource_id="NonExistent"
        )

        assert result == []


class TestBuildUserDetails:
    """Tests for AdminAuditService.build_user_details method."""

    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        return user

    def test_build_user_details_basic(self, mock_user):
        """Test build_user_details returns basic user info."""
        result = AdminAuditService.build_user_details(mock_user)

        assert result["user_id"] == 1
        assert result["email"] == "test@example.com"
        assert "changed" not in result
        assert "before" not in result

    def test_build_user_details_with_changed_fields(self, mock_user):
        """Test build_user_details includes changed fields when provided."""
        changed_fields = {"full_name": "New Name", "is_active": True}

        result = AdminAuditService.build_user_details(mock_user, changed_fields=changed_fields)

        assert result["user_id"] == 1
        assert result["changed"] == changed_fields

    def test_build_user_details_with_before_values(self, mock_user):
        """Test build_user_details includes before values when provided."""
        before = {"full_name": "Old Name", "is_active": False}

        result = AdminAuditService.build_user_details(mock_user, before=before)

        assert result["user_id"] == 1
        assert result["before"] == before

    def test_build_user_details_with_changed_and_before(self, mock_user):
        """Test build_user_details with both changed_fields and before."""
        changed_fields = {"role": "admin"}
        before = {"role": "user"}

        result = AdminAuditService.build_user_details(
            mock_user, changed_fields=changed_fields, before=before
        )

        assert result["user_id"] == 1
        assert result["email"] == "test@example.com"
        assert result["changed"] == {"role": "admin"}
        assert result["before"] == {"role": "user"}


class TestActionConstants:
    """Tests for AdminAuditService action and resource type constants."""

    def test_action_constants_exist(self):
        """Test that action constants are defined."""
        assert AdminAuditService.ACTION_CREATE == "CREATE"
        assert AdminAuditService.ACTION_UPDATE == "UPDATE"
        assert AdminAuditService.ACTION_DELETE == "DELETE"
        assert AdminAuditService.ACTION_TOGGLE_ACTIVE == "TOGGLE_ACTIVE"
        assert AdminAuditService.ACTION_UNLOCK == "UNLOCK"

    def test_resource_constants_exist(self):
        """Test that resource type constants are defined."""
        assert AdminAuditService.RESOURCE_USER == "user"
        assert AdminAuditService.RESOURCE_BRAND == "brand"
        assert AdminAuditService.RESOURCE_CATEGORY == "category"
        assert AdminAuditService.RESOURCE_COLOR == "color"
        assert AdminAuditService.RESOURCE_MATERIAL == "material"
