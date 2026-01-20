"""
Schema Module

Utilities for multi-tenant schema isolation in PostgreSQL.

Combines:
- Schema translate map configuration (robust, survives COMMIT/ROLLBACK)
- Schema context manager for background tasks

Created: 2026-01-13
Updated: 2026-01-20 - Consolidated from schema_utils.py, schema_context.py
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import text
from sqlalchemy.orm import Session

from shared.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# SCHEMA TRANSLATE MAP (Recommended for Request Handlers)
# =============================================================================


def configure_schema_translate_map(db: Session, schema_name: str) -> None:
    """
    Configure schema_translate_map on a Session's connection.

    This configures the underlying connection to remap the "tenant" placeholder
    to the actual user schema at query time. Models with schema="tenant" in
    their __table_args__ will have queries executed against the specified schema.

    Args:
        db: The SQLAlchemy Session to configure
        schema_name: The actual schema name (e.g., "user_1")

    Example:
        # Before
        db = db.execution_options(schema_translate_map={"tenant": schema})  # WRONG!

        # After
        configure_schema_translate_map(db, schema)  # CORRECT!

    Note:
        Session doesn't have execution_options(), but Connection does.
        Calling db.connection(execution_options=...) configures the underlying connection.
        The schema_translate_map survives COMMIT and ROLLBACK operations.
    """
    db.connection(execution_options={"schema_translate_map": {"tenant": schema_name}})


def get_schema_translate_map(db: Session) -> dict:
    """
    Get the current schema_translate_map from a Session's connection.

    Args:
        db: The SQLAlchemy Session to query

    Returns:
        The schema_translate_map dict, or empty dict if not configured.

    Example:
        configure_schema_translate_map(db, "user_1")
        schema_map = get_schema_translate_map(db)
        assert schema_map.get("tenant") == "user_1"
    """
    conn = db.connection()
    return conn.get_execution_options().get("schema_translate_map", {})


# =============================================================================
# SCHEMA CONTEXT MANAGER (For Background Tasks)
# =============================================================================


@contextmanager
def managed_schema(db: Session, user_id: int) -> Generator[Session, None, None]:
    """
    Context manager that sets and restores search_path for multi-tenant operations.

    Use this in background tasks that need to access user-specific tables.
    Sets search_path to user schema, yields the session, then restores to public.

    Usage:
        with managed_schema(db, user_id) as scoped_db:
            products = scoped_db.query(Product).all()
            # Products from user_{user_id} schema

    Args:
        db: SQLAlchemy session
        user_id: User ID to set schema for

    Yields:
        Session with search_path configured for user schema

    Note:
        - Uses SET (not SET LOCAL) because background tasks may commit
        - Restores to 'public' after context exits
        - Logs schema changes for debugging
    """
    schema_name = f"user_{user_id}"

    try:
        db.execute(text(f"SET search_path TO {schema_name}, public"))
        logger.debug(f"[managed_schema] Set search_path to {schema_name}, public")
        yield db
    finally:
        db.execute(text("SET search_path TO public"))
        logger.debug("[managed_schema] Reset search_path to public")


def set_user_schema(db: Session, user_id: int) -> None:
    """
    Set search_path to user schema (non-context manager version).

    Use when you need to set schema without the context manager pattern,
    e.g., in long-running operations where you manually manage commits.

    Args:
        db: SQLAlchemy session
        user_id: User ID to set schema for

    Warning:
        Remember to call reset_to_public_schema() when done!
    """
    schema_name = f"user_{user_id}"
    db.execute(text(f"SET search_path TO {schema_name}, public"))
    logger.debug(f"[set_user_schema] Set search_path to {schema_name}, public")


def reset_to_public_schema(db: Session) -> None:
    """
    Reset search_path to public schema.

    Call this after set_user_schema() when done with user-specific operations.

    Args:
        db: SQLAlchemy session
    """
    db.execute(text("SET search_path TO public"))
    logger.debug("[reset_to_public_schema] Reset search_path to public")


__all__ = [
    "configure_schema_translate_map",
    "get_schema_translate_map",
    "managed_schema",
    "set_user_schema",
    "reset_to_public_schema",
]
