"""
Unit tests for database security functions.

Tests SQL injection prevention in schema name validation.

Author: Claude
Date: 2026-01-12
"""

import pytest

from shared.database import validate_schema_name


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


# NOTE (2026-01-13): TestSetSearchPathSafe class removed
# The set_search_path_safe() function was deprecated and removed as part of
# the schema_translate_map migration. See ROADMAP.md Phase 4.
#
# The new approach uses execution_options(schema_translate_map={"tenant": schema})
# which doesn't require user_id validation at the database layer since the schema
# name is never interpolated into SQL strings.
#
# Tests for schema_translate_map behavior are in test_schema_translate_map.py
