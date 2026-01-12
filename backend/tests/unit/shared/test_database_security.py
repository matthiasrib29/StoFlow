"""
Unit tests for database security functions.

Tests SQL injection prevention in schema name validation.

Author: Claude
Date: 2026-01-12
"""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from shared.database import validate_schema_name, set_search_path_safe


class TestValidateSchemaName:
    """Test schema name validation."""

    def test_validate_schema_name_valid(self):
        """Valid schema names should pass validation."""
        # Alphanumeric with underscore
        assert validate_schema_name("user_1") == "user_1"
        assert validate_schema_name("user_123") == "user_123"
        assert validate_schema_name("test_schema") == "test_schema"

        # Start with letter
        assert validate_schema_name("schema123") == "schema123"

        # Start with underscore
        assert validate_schema_name("_private") == "_private"

    def test_validate_schema_name_with_sql_injection_attempt(self):
        """SQL injection attempts should be rejected."""
        # SQL comment
        with pytest.raises(ValueError, match="Invalid schema name"):
            validate_schema_name("user_1-- comment")

        # SQL command
        with pytest.raises(ValueError, match="Invalid schema name"):
            validate_schema_name("user_1; DROP SCHEMA public CASCADE")

        # Whitespace injection
        with pytest.raises(ValueError, match="Invalid schema name"):
            validate_schema_name("user_1 ; DROP TABLE users")

    def test_validate_schema_name_with_semicolon(self):
        """Semicolon should be rejected (SQL statement separator)."""
        with pytest.raises(ValueError, match="Invalid schema name"):
            validate_schema_name("user_1;")

        with pytest.raises(ValueError, match="Invalid schema name"):
            validate_schema_name("user;1")

    def test_validate_schema_name_too_long(self):
        """Schema names > 63 bytes should be rejected (PostgreSQL limit)."""
        # 64 characters (too long)
        long_name = "a" * 64
        with pytest.raises(ValueError, match="Schema name too long"):
            validate_schema_name(long_name)

        # 63 characters (exactly at limit - should pass)
        max_length_name = "a" * 63
        assert validate_schema_name(max_length_name) == max_length_name

    def test_validate_schema_name_reserved(self):
        """Reserved PostgreSQL schema names should be rejected."""
        with pytest.raises(ValueError, match="Schema name is reserved"):
            validate_schema_name("pg_catalog")

        with pytest.raises(ValueError, match="Schema name is reserved"):
            validate_schema_name("information_schema")

        with pytest.raises(ValueError, match="Schema name is reserved"):
            validate_schema_name("pg_toast")

        # Case insensitive check
        with pytest.raises(ValueError, match="Schema name is reserved"):
            validate_schema_name("PG_CATALOG")


class TestSetSearchPathSafe:
    """Test safe search path setting."""

    def test_set_search_path_safe_with_valid_user_id(self, db_session: Session):
        """Valid user_id should set search_path successfully."""
        # Valid positive integer
        set_search_path_safe(db_session, 1)

        # Verify search_path was set
        result = db_session.execute(text("SHOW search_path")).scalar()
        assert "user_1" in result
        assert "public" in result

    def test_set_search_path_safe_with_invalid_user_id(self):
        """Invalid user_id (zero, negative) should raise ValueError."""
        from sqlalchemy.orm import Session
        from unittest.mock import Mock

        # Mock session (we don't need real DB for validation-only test)
        mock_session = Mock(spec=Session)

        # Zero user_id
        with pytest.raises(ValueError, match="Invalid user_id: 0"):
            set_search_path_safe(mock_session, 0)

        # Negative user_id
        with pytest.raises(ValueError, match="Invalid user_id: -1"):
            set_search_path_safe(mock_session, -1)

    def test_set_search_path_safe_with_string_user_id_raises_error(self):
        """String user_id should raise ValueError (type check)."""
        from sqlalchemy.orm import Session
        from unittest.mock import Mock

        # Mock session
        mock_session = Mock(spec=Session)

        # String instead of int
        with pytest.raises(ValueError, match="Invalid user_id"):
            set_search_path_safe(mock_session, "1")  # type: ignore

        # SQL injection attempt via user_id
        with pytest.raises(ValueError, match="Invalid user_id"):
            set_search_path_safe(mock_session, "1; DROP SCHEMA public")  # type: ignore
