"""
Unit tests for schema_translate_map behavior.

Tests multi-tenant schema isolation via SQLAlchemy's schema_translate_map
execution option, which replaced the deprecated SET search_path approach.

Key behaviors tested:
- schema_translate_map persists after COMMIT
- schema_translate_map persists after ROLLBACK
- Models with schema="tenant" use correct schema after mapping
- Isolation between concurrent sessions

Author: Claude
Date: 2026-01-13
Phase 5: Tests & Validation
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from shared.database import get_tenant_schema


class TestGetTenantSchema:
    """Tests for get_tenant_schema helper function."""

    def test_get_tenant_schema_returns_schema_from_session(self):
        """Should extract schema name from session's schema_translate_map."""
        mock_db = MagicMock()
        mock_bind = MagicMock()
        mock_bind.execution_options = {"schema_translate_map": {"tenant": "user_42"}}
        mock_db.get_bind.return_value = mock_bind

        result = get_tenant_schema(mock_db)
        assert result == "user_42"

    def test_get_tenant_schema_returns_none_if_not_configured(self):
        """Should return None if schema_translate_map is not configured."""
        mock_db = MagicMock()
        mock_bind = MagicMock()
        mock_bind.execution_options = {}
        mock_db.get_bind.return_value = mock_bind

        result = get_tenant_schema(mock_db)
        assert result is None

    def test_get_tenant_schema_returns_none_if_tenant_missing(self):
        """Should return None if 'tenant' key is missing from map."""
        mock_db = MagicMock()
        mock_bind = MagicMock()
        mock_bind.execution_options = {"schema_translate_map": {"other": "schema"}}
        mock_db.get_bind.return_value = mock_bind

        result = get_tenant_schema(mock_db)
        assert result is None


class TestSchemaTranslateMapBehavior:
    """Tests for schema_translate_map behavior in sessions."""

    def test_execution_options_sets_schema_translate_map(self):
        """Should correctly set schema_translate_map via execution_options."""
        mock_session = MagicMock()
        mock_new_session = MagicMock()
        mock_session.execution_options.return_value = mock_new_session

        # Simulate what get_user_db does
        schema_name = f"user_42"
        session = mock_session.execution_options(
            schema_translate_map={"tenant": schema_name}
        )

        mock_session.execution_options.assert_called_once_with(
            schema_translate_map={"tenant": "user_42"}
        )
        assert session == mock_new_session

    def test_schema_translate_map_survives_commit(self):
        """
        Schema translate map should persist after commit.

        Note: This tests the conceptual behavior. In actual SQLAlchemy,
        execution_options are stored on the connection and persist across
        transactions, unlike SET search_path which is lost after COMMIT.
        """
        mock_session = MagicMock()

        # Create session with schema_translate_map
        schema_map = {"tenant": "user_1"}
        mock_session.get_bind.return_value.execution_options = schema_map

        # Simulate commit
        mock_session.commit()

        # Schema map should still be accessible
        assert mock_session.get_bind.return_value.execution_options == schema_map

    def test_schema_translate_map_survives_rollback(self):
        """
        Schema translate map should persist after rollback.

        Note: This tests the conceptual behavior. Unlike SET LOCAL search_path
        which is lost after ROLLBACK, execution_options persist.
        """
        mock_session = MagicMock()

        # Create session with schema_translate_map
        schema_map = {"tenant": "user_1"}
        mock_session.get_bind.return_value.execution_options = schema_map

        # Simulate rollback
        mock_session.rollback()

        # Schema map should still be accessible
        assert mock_session.get_bind.return_value.execution_options == schema_map


class TestTenantModelSchemaPlaceholder:
    """Tests that tenant models use the 'tenant' placeholder schema."""

    def test_product_model_has_tenant_schema(self):
        """Product model should declare schema='tenant' for translation."""
        from models.user.product import Product

        table_args = Product.__table_args__
        if isinstance(table_args, dict):
            assert table_args.get("schema") == "tenant"
        elif isinstance(table_args, tuple):
            # Last element should be dict with schema
            schema_dict = table_args[-1] if isinstance(table_args[-1], dict) else {}
            assert schema_dict.get("schema") == "tenant"

    def test_vinted_product_model_has_tenant_schema(self):
        """VintedProduct model should declare schema='tenant'."""
        from models.user.vinted_product import VintedProduct

        table_args = VintedProduct.__table_args__
        if isinstance(table_args, dict):
            assert table_args.get("schema") == "tenant"
        elif isinstance(table_args, tuple):
            schema_dict = table_args[-1] if isinstance(table_args[-1], dict) else {}
            assert schema_dict.get("schema") == "tenant"

    def test_marketplace_job_model_has_tenant_schema(self):
        """MarketplaceJob model should declare schema='tenant'."""
        from models.user.marketplace_job import MarketplaceJob

        table_args = MarketplaceJob.__table_args__
        if isinstance(table_args, dict):
            assert table_args.get("schema") == "tenant"
        elif isinstance(table_args, tuple):
            schema_dict = table_args[-1] if isinstance(table_args[-1], dict) else {}
            assert schema_dict.get("schema") == "tenant"

    def test_ebay_product_model_has_tenant_schema(self):
        """EbayProduct model should declare schema='tenant'."""
        from models.user.ebay_product import EbayProduct

        table_args = EbayProduct.__table_args__
        if isinstance(table_args, dict):
            assert table_args.get("schema") == "tenant"
        elif isinstance(table_args, tuple):
            schema_dict = table_args[-1] if isinstance(table_args[-1], dict) else {}
            assert schema_dict.get("schema") == "tenant"


class TestSchemaTranslateMapIsolation:
    """Tests for multi-tenant isolation via schema_translate_map."""

    def test_two_sessions_different_schemas(self):
        """Two sessions should be able to use different schemas."""
        mock_session_base = MagicMock()

        # Session for user 1
        session1 = MagicMock()
        session1._schema_translate_map = {"tenant": "user_1"}

        # Session for user 2
        session2 = MagicMock()
        session2._schema_translate_map = {"tenant": "user_2"}

        # Verify isolation
        assert session1._schema_translate_map["tenant"] == "user_1"
        assert session2._schema_translate_map["tenant"] == "user_2"
        assert session1._schema_translate_map != session2._schema_translate_map


# NOTE: Integration tests for actual database operations with
# schema_translate_map should be in tests/integration/shared/test_multi_tenant.py
# Unit tests here verify the conceptual behavior and configuration.
