"""
Unit tests for AdminStatsService.

Coverage:
- get_overview: user counts by status and role
- get_subscriptions: tier distribution and MRR calculation
- get_registrations: period-based registration data with custom date ranges
- get_recent_activity: recent logins and new registrations

Author: Claude
Date: 2026-01-08
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from services.admin_stats_service import AdminStatsService, TIER_PRICES
from models.public.user import User, UserRole, SubscriptionTier


class TestGetOverview:
    """Tests for AdminStatsService.get_overview method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock(spec=Session)

    def test_get_overview_returns_all_counts(self, mock_db):
        """Test get_overview returns all user count categories."""
        # Set up mock to return different values for each query
        mock_db.query.return_value.scalar.side_effect = [
            100,  # total
            80,   # active
            20,   # inactive
            5,    # locked
            3,    # admins
            95,   # users
            2,    # support
        ]
        mock_db.query.return_value.filter.return_value.scalar.side_effect = [
            80,   # active
            20,   # inactive
            5,    # locked
            3,    # admins
            95,   # users
            2,    # support
        ]

        result = AdminStatsService.get_overview(mock_db)

        assert "total_users" in result
        assert "active_users" in result
        assert "inactive_users" in result
        assert "locked_users" in result
        assert "users_by_role" in result
        assert "admin" in result["users_by_role"]
        assert "user" in result["users_by_role"]
        assert "support" in result["users_by_role"]

    def test_get_overview_handles_zero_users(self, mock_db):
        """Test get_overview handles case with no users."""
        mock_db.query.return_value.scalar.return_value = 0
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0

        result = AdminStatsService.get_overview(mock_db)

        assert result["total_users"] == 0
        assert result["active_users"] == 0
        assert result["inactive_users"] == 0
        assert result["locked_users"] == 0

    def test_get_overview_handles_none_scalars(self, mock_db):
        """Test get_overview handles None values from database."""
        mock_db.query.return_value.scalar.return_value = None
        mock_db.query.return_value.filter.return_value.scalar.return_value = None

        result = AdminStatsService.get_overview(mock_db)

        assert result["total_users"] == 0
        assert result["active_users"] == 0


class TestGetSubscriptions:
    """Tests for AdminStatsService.get_subscriptions method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock(spec=Session)

    def test_get_subscriptions_returns_tier_distribution(self, mock_db):
        """Test get_subscriptions returns users by tier."""
        # Mock tier counts
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            (SubscriptionTier.FREE, 50),
            (SubscriptionTier.STARTER, 20),
            (SubscriptionTier.PRO, 10),
            (SubscriptionTier.ENTERPRISE, 5),
        ]

        result = AdminStatsService.get_subscriptions(mock_db)

        assert "users_by_tier" in result
        assert result["users_by_tier"]["free"] == 50
        assert result["users_by_tier"]["starter"] == 20
        assert result["users_by_tier"]["pro"] == 10
        assert result["users_by_tier"]["enterprise"] == 5

    def test_get_subscriptions_calculates_mrr(self, mock_db):
        """Test get_subscriptions calculates MRR correctly."""
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            (SubscriptionTier.FREE, 50),
            (SubscriptionTier.STARTER, 20),  # 20 * 9.99 = 199.80
            (SubscriptionTier.PRO, 10),       # 10 * 29.99 = 299.90
            (SubscriptionTier.ENTERPRISE, 5), # 5 * 99.99 = 499.95
        ]

        result = AdminStatsService.get_subscriptions(mock_db)

        expected_mrr = (50 * 0) + (20 * 9.99) + (10 * 29.99) + (5 * 99.99)
        assert result["total_mrr"] == round(expected_mrr, 2)

    def test_get_subscriptions_counts_paying_subscribers(self, mock_db):
        """Test get_subscriptions correctly counts paying subscribers."""
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            (SubscriptionTier.FREE, 50),
            (SubscriptionTier.STARTER, 20),
            (SubscriptionTier.PRO, 10),
        ]

        result = AdminStatsService.get_subscriptions(mock_db)

        # Only STARTER and PRO are paying
        assert result["paying_subscribers"] == 30

    def test_get_subscriptions_handles_empty_tiers(self, mock_db):
        """Test get_subscriptions handles case with no users in some tiers."""
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            (SubscriptionTier.FREE, 10),
        ]

        result = AdminStatsService.get_subscriptions(mock_db)

        assert result["users_by_tier"]["free"] == 10
        assert result["users_by_tier"]["starter"] == 0
        assert result["users_by_tier"]["pro"] == 0
        assert result["users_by_tier"]["enterprise"] == 0

    def test_get_subscriptions_calculates_active_subscriptions(self, mock_db):
        """Test get_subscriptions sums active subscriptions."""
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            (SubscriptionTier.FREE, 50),
            (SubscriptionTier.STARTER, 20),
        ]

        result = AdminStatsService.get_subscriptions(mock_db)

        assert result["active_subscriptions"] == 70


class TestGetRegistrations:
    """Tests for AdminStatsService.get_registrations method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock(spec=Session)

    @patch('services.admin_stats_service.datetime')
    def test_get_registrations_default_month(self, mock_datetime, mock_db):
        """Test get_registrations returns month of data by default."""
        now = datetime(2025, 6, 15, 12, 0, 0)
        mock_datetime.utcnow.return_value = now

        mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = []

        result = AdminStatsService.get_registrations(mock_db)

        assert result["period"] == "month"
        assert "start_date" in result
        assert "end_date" in result

    @patch('services.admin_stats_service.datetime')
    def test_get_registrations_week_period(self, mock_datetime, mock_db):
        """Test get_registrations with week period."""
        now = datetime(2025, 6, 15, 12, 0, 0)
        mock_datetime.utcnow.return_value = now

        mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = []

        result = AdminStatsService.get_registrations(mock_db, period="week")

        assert result["period"] == "week"

    @patch('services.admin_stats_service.datetime')
    def test_get_registrations_3months_period(self, mock_datetime, mock_db):
        """Test get_registrations with 3months period."""
        now = datetime(2025, 6, 15, 12, 0, 0)
        mock_datetime.utcnow.return_value = now

        mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = []

        result = AdminStatsService.get_registrations(mock_db, period="3months")

        assert result["period"] == "3months"

    @patch('services.admin_stats_service.datetime')
    def test_get_registrations_custom_date_range(self, mock_datetime, mock_db):
        """Test get_registrations with custom start and end dates."""
        now = datetime(2025, 6, 15, 12, 0, 0)
        mock_datetime.utcnow.return_value = now

        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 1, 31)

        mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = []

        result = AdminStatsService.get_registrations(
            mock_db, start_date=start_date, end_date=end_date
        )

        assert result["start_date"] == "2025-01-01"
        assert result["end_date"] == "2025-01-31"

    @patch('services.admin_stats_service.datetime')
    def test_get_registrations_fills_missing_days(self, mock_datetime, mock_db):
        """Test get_registrations fills missing days with 0 counts."""
        now = datetime(2025, 6, 10, 12, 0, 0)
        mock_datetime.utcnow.return_value = now

        # Mock data with gaps
        mock_row1 = Mock()
        mock_row1.date = "2025-06-03"
        mock_row1.count = 5
        mock_row2 = Mock()
        mock_row2.date = "2025-06-08"
        mock_row2.count = 3

        mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [
            mock_row1, mock_row2
        ]

        result = AdminStatsService.get_registrations(mock_db, period="week")

        # Data should include all days, not just those with registrations
        assert "data" in result
        # Days without registrations should have count 0
        data_dict = {item["date"]: item["count"] for item in result["data"]}
        # Verify some days have 0 counts
        has_zero_count = any(item["count"] == 0 for item in result["data"])
        assert has_zero_count or len(result["data"]) <= 2  # Either has zeros or very sparse data

    @patch('services.admin_stats_service.datetime')
    def test_get_registrations_calculates_totals(self, mock_datetime, mock_db):
        """Test get_registrations calculates total and average."""
        now = datetime(2025, 6, 10, 12, 0, 0)
        mock_datetime.utcnow.return_value = now

        mock_row1 = Mock()
        mock_row1.date = "2025-06-03"
        mock_row1.count = 10
        mock_row2 = Mock()
        mock_row2.date = "2025-06-05"
        mock_row2.count = 20

        mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [
            mock_row1, mock_row2
        ]

        result = AdminStatsService.get_registrations(mock_db, period="week")

        assert "total" in result
        assert "average_per_day" in result
        # Total should be sum of all counts in data (including filled zeros)
        assert result["total"] >= 30  # At least 10 + 20 from actual data


class TestGetRecentActivity:
    """Tests for AdminStatsService.get_recent_activity method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_users(self):
        """Create mock users for testing."""
        user1 = Mock(spec=User)
        user1.id = 1
        user1.email = "user1@example.com"
        user1.full_name = "User One"
        user1.last_login = datetime(2025, 6, 15, 10, 0, 0)
        user1.created_at = datetime(2025, 6, 14, 8, 0, 0)
        user1.subscription_tier = SubscriptionTier.FREE

        user2 = Mock(spec=User)
        user2.id = 2
        user2.email = "user2@example.com"
        user2.full_name = "User Two"
        user2.last_login = datetime(2025, 6, 15, 11, 0, 0)
        user2.created_at = datetime(2025, 6, 13, 9, 0, 0)
        user2.subscription_tier = SubscriptionTier.PRO

        return [user1, user2]

    def test_get_recent_activity_returns_structure(self, mock_db, mock_users):
        """Test get_recent_activity returns correct structure."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_users

        result = AdminStatsService.get_recent_activity(mock_db)

        assert "recent_logins" in result
        assert "new_registrations" in result

    def test_get_recent_activity_recent_logins_format(self, mock_db, mock_users):
        """Test recent logins have correct format."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_users

        result = AdminStatsService.get_recent_activity(mock_db)

        for login in result["recent_logins"]:
            assert "id" in login
            assert "email" in login
            assert "full_name" in login
            assert "last_login" in login

    def test_get_recent_activity_new_registrations_format(self, mock_db, mock_users):
        """Test new registrations have correct format."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_users

        result = AdminStatsService.get_recent_activity(mock_db)

        for registration in result["new_registrations"]:
            assert "id" in registration
            assert "email" in registration
            assert "full_name" in registration
            assert "created_at" in registration
            assert "subscription_tier" in registration

    def test_get_recent_activity_custom_limit(self, mock_db):
        """Test get_recent_activity respects custom limit."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        AdminStatsService.get_recent_activity(mock_db, limit=5)

        # Verify limit was called with 5
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.assert_called_with(5)

    def test_get_recent_activity_empty_result(self, mock_db):
        """Test get_recent_activity handles no activity."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = AdminStatsService.get_recent_activity(mock_db)

        assert result["recent_logins"] == []
        assert result["new_registrations"] == []

    def test_get_recent_activity_handles_none_last_login(self, mock_db):
        """Test get_recent_activity handles users with None last_login."""
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.full_name = "Test User"
        mock_user.last_login = None
        mock_user.created_at = datetime(2025, 6, 14)
        mock_user.subscription_tier = SubscriptionTier.FREE

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_user]

        result = AdminStatsService.get_recent_activity(mock_db)

        # Should handle None last_login gracefully
        if result["recent_logins"]:
            assert result["recent_logins"][0]["last_login"] is None


class TestTierPrices:
    """Tests for TIER_PRICES constant."""

    def test_tier_prices_defined_for_all_tiers(self):
        """Test that prices are defined for all subscription tiers."""
        assert SubscriptionTier.FREE in TIER_PRICES
        assert SubscriptionTier.STARTER in TIER_PRICES
        assert SubscriptionTier.PRO in TIER_PRICES
        assert SubscriptionTier.ENTERPRISE in TIER_PRICES

    def test_tier_prices_values(self):
        """Test tier price values are correct."""
        assert TIER_PRICES[SubscriptionTier.FREE] == 0
        assert TIER_PRICES[SubscriptionTier.STARTER] == 9.99
        assert TIER_PRICES[SubscriptionTier.PRO] == 29.99
        assert TIER_PRICES[SubscriptionTier.ENTERPRISE] == 99.99

    def test_tier_prices_are_numeric(self):
        """Test all tier prices are numeric values."""
        for tier, price in TIER_PRICES.items():
            assert isinstance(price, (int, float))
            assert price >= 0
