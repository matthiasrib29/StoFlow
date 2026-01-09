"""
Unit tests for AdminUserService.

Coverage:
- list_users: pagination, filtering, search
- get_user: found, not found
- create_user: success, duplicate email, missing quota, schema creation failure
- update_user: success, not found, email change, password change, unlock account
- delete_user: success, not found, with AI credits

Author: Claude
Date: 2026-01-08
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from services.admin_user_service import AdminUserService
from models.public.user import User, UserRole, SubscriptionTier


class TestListUsers:
    """Tests for AdminUserService.list_users method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock(spec=Session)

    def test_list_users_returns_users_and_count(self, mock_db):
        """Test that list_users returns a tuple of users and total count."""
        mock_user1 = Mock(spec=User)
        mock_user2 = Mock(spec=User)

        mock_query = MagicMock()
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            mock_user1, mock_user2
        ]
        mock_db.query.return_value = mock_query

        users, total = AdminUserService.list_users(mock_db)

        assert total == 2
        assert len(users) == 2
        mock_db.query.assert_called_once_with(User)

    def test_list_users_with_pagination(self, mock_db):
        """Test list_users with skip and limit parameters."""
        mock_query = MagicMock()
        mock_query.count.return_value = 100
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        AdminUserService.list_users(mock_db, skip=20, limit=10)

        mock_query.order_by.return_value.offset.assert_called_once_with(20)
        mock_query.order_by.return_value.offset.return_value.limit.assert_called_once_with(10)

    def test_list_users_with_search(self, mock_db):
        """Test list_users with search filter."""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        AdminUserService.list_users(mock_db, search="test")

        mock_query.filter.assert_called_once()

    def test_list_users_with_role_filter(self, mock_db):
        """Test list_users with role filter."""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        AdminUserService.list_users(mock_db, role=UserRole.ADMIN)

        assert mock_query.filter.called

    def test_list_users_with_is_active_filter(self, mock_db):
        """Test list_users with is_active filter."""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        AdminUserService.list_users(mock_db, is_active=True)

        assert mock_query.filter.called

    def test_list_users_empty_result(self, mock_db):
        """Test list_users returns empty list when no users found."""
        mock_query = MagicMock()
        mock_query.count.return_value = 0
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        users, total = AdminUserService.list_users(mock_db)

        assert total == 0
        assert users == []


class TestGetUser:
    """Tests for AdminUserService.get_user method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock(spec=Session)

    def test_get_user_found(self, mock_db):
        """Test get_user returns user when found."""
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.email = "test@example.com"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = AdminUserService.get_user(mock_db, user_id=1)

        assert result is not None
        assert result.id == 1
        mock_db.query.assert_called_once_with(User)

    def test_get_user_not_found(self, mock_db):
        """Test get_user returns None when user not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = AdminUserService.get_user(mock_db, user_id=999)

        assert result is None


class TestCreateUser:
    """Tests for AdminUserService.create_user method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=Session)
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        db.delete = Mock()
        return db

    @patch('services.user_schema_service.UserSchemaService.create_user_schema')
    @patch('services.admin_user_service.AuthService')
    def test_create_user_success(self, mock_auth, mock_create_schema, mock_db):
        """Test successful user creation."""
        # Mock email check - no existing user
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # First call: email check
            Mock(id=1, tier=SubscriptionTier.FREE),  # Second call: quota check
        ]
        mock_auth.hash_password.return_value = "hashed_password"
        mock_create_schema.return_value = "user_1"

        def refresh_side_effect(user):
            user.id = 1
        mock_db.refresh.side_effect = refresh_side_effect

        result = AdminUserService.create_user(
            mock_db,
            email="new@example.com",
            password="password123",
            full_name="New User"
        )

        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()
        mock_auth.hash_password.assert_called_once_with("password123")

    @patch('services.admin_user_service.AuthService')
    def test_create_user_duplicate_email_raises_error(self, mock_auth, mock_db):
        """Test create_user raises ValueError for duplicate email."""
        mock_existing = Mock(spec=User)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_existing

        with pytest.raises(ValueError, match="Email already exists"):
            AdminUserService.create_user(
                mock_db,
                email="existing@example.com",
                password="password123",
                full_name="Test User"
            )

    @patch('services.admin_user_service.AuthService')
    def test_create_user_missing_quota_raises_error(self, mock_auth, mock_db):
        """Test create_user raises ValueError when subscription quota not found."""
        # First query returns None (no existing email), second returns None (no quota)
        mock_db.query.return_value.filter.return_value.first.side_effect = [None, None]
        mock_auth.hash_password.return_value = "hashed_password"

        with pytest.raises(ValueError, match="Subscription quota not found"):
            AdminUserService.create_user(
                mock_db,
                email="new@example.com",
                password="password123",
                full_name="New User"
            )

    @patch('services.user_schema_service.UserSchemaService.create_user_schema')
    @patch('services.admin_user_service.AuthService')
    def test_create_user_schema_creation_failure_rollback(self, mock_auth, mock_create_schema, mock_db):
        """Test that user is deleted if schema creation fails."""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # No existing email
            Mock(id=1, tier=SubscriptionTier.FREE),  # Quota found
        ]
        mock_auth.hash_password.return_value = "hashed_password"
        mock_create_schema.side_effect = Exception("Schema creation failed")

        def refresh_side_effect(user):
            user.id = 1
        mock_db.refresh.side_effect = refresh_side_effect

        with pytest.raises(ValueError, match="Failed to create user schema"):
            AdminUserService.create_user(
                mock_db,
                email="new@example.com",
                password="password123",
                full_name="New User"
            )

        mock_db.delete.assert_called_once()


class TestUpdateUser:
    """Tests for AdminUserService.update_user method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=Session)
        db.commit = Mock()
        db.refresh = Mock()
        return db

    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        user = Mock(spec=User)
        user.id = 1
        user.email = "original@example.com"
        user.full_name = "Original Name"
        user.role = UserRole.USER
        user.is_active = True
        user.failed_login_attempts = 0
        user.locked_until = None
        user.subscription_tier = SubscriptionTier.FREE
        user.subscription_tier_id = 1
        user.business_name = None
        return user

    def test_update_user_success(self, mock_db, mock_user):
        """Test successful user update."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = AdminUserService.update_user(
            mock_db,
            user_id=1,
            full_name="Updated Name"
        )

        assert result is not None
        assert mock_user.full_name == "Updated Name"
        mock_db.commit.assert_called_once()

    def test_update_user_not_found(self, mock_db):
        """Test update_user returns None when user not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = AdminUserService.update_user(mock_db, user_id=999, full_name="New Name")

        assert result is None

    def test_update_user_email_success(self, mock_db, mock_user):
        """Test successful email update."""
        # First query returns user, second query for email check returns None
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,  # Get user
            None,  # Email check - no duplicate
        ]

        result = AdminUserService.update_user(
            mock_db,
            user_id=1,
            email="newemail@example.com"
        )

        assert result is not None
        assert mock_user.email == "newemail@example.com"

    def test_update_user_email_duplicate_raises_error(self, mock_db, mock_user):
        """Test update_user raises ValueError for duplicate email."""
        mock_existing = Mock(spec=User)
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,  # Get user
            mock_existing,  # Email check - duplicate found
        ]

        with pytest.raises(ValueError, match="Email already exists"):
            AdminUserService.update_user(
                mock_db,
                user_id=1,
                email="existing@example.com"
            )

    @patch('services.admin_user_service.AuthService')
    def test_update_user_password(self, mock_auth, mock_db, mock_user):
        """Test password update hashes new password."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_auth.hash_password.return_value = "new_hashed_password"

        result = AdminUserService.update_user(
            mock_db,
            user_id=1,
            password="newpassword123"
        )

        assert result is not None
        mock_auth.hash_password.assert_called_once_with("newpassword123")
        assert mock_user.hashed_password == "new_hashed_password"

    def test_update_user_unlock_account(self, mock_db, mock_user):
        """Test unlock account resets failed login attempts."""
        mock_user.failed_login_attempts = 5
        mock_user.locked_until = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = AdminUserService.update_user(
            mock_db,
            user_id=1,
            unlock=True
        )

        assert result is not None
        assert mock_user.failed_login_attempts == 0
        assert mock_user.locked_until is None

    def test_update_user_activate_resets_login_attempts(self, mock_db, mock_user):
        """Test activating user resets failed login attempts."""
        mock_user.is_active = False
        mock_user.failed_login_attempts = 3
        mock_user.locked_until = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = AdminUserService.update_user(
            mock_db,
            user_id=1,
            is_active=True
        )

        assert result is not None
        assert mock_user.is_active is True
        assert mock_user.failed_login_attempts == 0
        assert mock_user.locked_until is None

    def test_update_user_subscription_tier(self, mock_db, mock_user):
        """Test updating subscription tier."""
        mock_quota = Mock(id=2, tier=SubscriptionTier.PRO)
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,  # Get user
            mock_quota,  # Get quota
        ]

        result = AdminUserService.update_user(
            mock_db,
            user_id=1,
            subscription_tier=SubscriptionTier.PRO
        )

        assert result is not None
        assert mock_user.subscription_tier == SubscriptionTier.PRO
        assert mock_user.subscription_tier_id == 2


class TestDeleteUser:
    """Tests for AdminUserService.delete_user method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=Session)
        db.delete = Mock()
        db.commit = Mock()
        db.execute = Mock()
        return db

    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        user = Mock(spec=User)
        user.id = 1
        user.schema_name = "user_1"
        user.ai_credit = None
        return user

    def test_delete_user_success(self, mock_db, mock_user):
        """Test successful user deletion."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = AdminUserService.delete_user(mock_db, user_id=1)

        assert result is True
        mock_db.execute.assert_called_once()  # DROP SCHEMA
        mock_db.delete.assert_called_once_with(mock_user)
        mock_db.commit.assert_called_once()

    def test_delete_user_not_found(self, mock_db):
        """Test delete_user returns False when user not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = AdminUserService.delete_user(mock_db, user_id=999)

        assert result is False
        mock_db.delete.assert_not_called()

    def test_delete_user_with_ai_credits(self, mock_db, mock_user):
        """Test delete user also deletes AI credits."""
        mock_ai_credit = Mock()
        mock_user.ai_credit = mock_ai_credit
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = AdminUserService.delete_user(mock_db, user_id=1)

        assert result is True
        # Check AI credit was deleted
        assert mock_db.delete.call_count == 2  # AI credit + user

    def test_delete_user_schema_drop_failure_continues(self, mock_db, mock_user):
        """Test user deletion continues even if schema drop fails."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.execute.side_effect = Exception("Schema drop failed")

        result = AdminUserService.delete_user(mock_db, user_id=1)

        assert result is True
        mock_db.delete.assert_called_once_with(mock_user)
        mock_db.commit.assert_called_once()
