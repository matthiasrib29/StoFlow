"""
Schema Utils for Multi-Tenant Isolation

This module provides utilities for configuring schema_translate_map on SQLAlchemy sessions.

Migration: SET LOCAL search_path → schema_translate_map (2026-01-13)
====================================================================

BEFORE (fragile - lost after COMMIT/ROLLBACK):
    db.execute(text(f"SET LOCAL search_path TO {schema}, public"))
    # ... do work ...
    db.commit()  # search_path LOST!

AFTER (robust - survives COMMIT/ROLLBACK):
    configure_schema_translate_map(db, schema)
    # ... do work ...
    db.commit()  # schema_translate_map PRESERVED!

Important: Session doesn't have execution_options() - use this helper instead.

See ROADMAP.md Phase 4 for migration details.

Author: Claude
Date: 2026-01-13
"""

from sqlalchemy.orm import Session


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


__all__ = ["configure_schema_translate_map", "get_schema_translate_map"]
