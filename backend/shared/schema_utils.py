"""
Schema Utils - Utilities for PostgreSQL schema management in multi-tenant context.

Provides centralized functions for capturing and restoring PostgreSQL search_path,
especially useful after commits or rollbacks in multi-tenant architecture.

Business Rules:
- Each user has isolated schema: user_{user_id}
- SET LOCAL search_path is lost after COMMIT
- After ROLLBACK, session may be in InFailedSqlTransaction state
- Always restore search_path after transaction boundary operations

Author: Claude
Date: 2025-01-05
"""

from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from shared.logging_setup import get_logger

logger = get_logger(__name__)


def get_current_schema(db: Session) -> Optional[str]:
    """
    Get current user schema from PostgreSQL search_path.

    Parses the search_path and returns the first schema matching 'user_*' pattern.

    Args:
        db: SQLAlchemy session

    Returns:
        Schema name (e.g., 'user_123') or None if not found
    """
    try:
        result = db.execute(text("SHOW search_path"))
        path = result.scalar()
        if path:
            for schema in path.split(","):
                schema = schema.strip().strip('"')
                if schema.startswith("user_"):
                    return schema
    except Exception as e:
        logger.warning(f"Failed to get current schema: {e}")
    return None


def restore_search_path(db: Session, schema_name: str) -> None:
    """
    Restore PostgreSQL search_path to specified schema.

    Use this after db.commit() since SET LOCAL doesn't persist across transactions.

    Args:
        db: SQLAlchemy session
        schema_name: Schema name to restore (e.g., 'user_123')
    """
    try:
        db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    except Exception as e:
        logger.warning(f"Failed to restore search_path to {schema_name}: {e}")


def restore_search_path_after_rollback(db: Session, schema_name: Optional[str] = None) -> None:
    """
    Restore PostgreSQL search_path after a rollback.

    CRITICAL: Handles InFailedSqlTransaction state.
    - After rollback, session may still be in invalid state
    - Forces a clean rollback first
    - Then reconfigures search_path

    Args:
        db: SQLAlchemy session
        schema_name: Schema to restore. If None, detects from current search_path.
    """
    try:
        # Force clean rollback to exit any failed transaction state
        try:
            db.rollback()
        except Exception:
            pass  # Ignore if already rolled back

        # Get schema from parameter or detect from search_path
        target_schema = schema_name
        if not target_schema:
            target_schema = get_current_schema(db)

        if target_schema:
            db.execute(text(f"SET LOCAL search_path TO {target_schema}, public"))
    except Exception as e:
        logger.warning(f"Failed to restore search_path after rollback: {e}")


def commit_and_restore_path(db: Session) -> None:
    """
    Commit transaction and restore search_path.

    Pattern to avoid losing SET LOCAL after commit.
    Captures schema before commit, then restores it after.

    Args:
        db: SQLAlchemy session
    """
    # Capture schema before commit
    schema = get_current_schema(db)

    # Commit
    db.commit()

    # Restore search_path
    if schema:
        restore_search_path(db, schema)


class SchemaManager:
    """
    Context manager for schema capture and restoration.

    Use this class when you need to track schema across multiple operations
    that may involve commits or rollbacks.

    Usage:
        schema_mgr = SchemaManager()
        schema_mgr.capture(db)
        # ... do operations that may rollback ...
        schema_mgr.restore_after_rollback(db)

    Or as instance attribute in services:
        class MyService:
            def __init__(self):
                self._schema_manager = SchemaManager()

            def process(self, db):
                self._schema_manager.capture(db)
                try:
                    # ... operations ...
                except Exception:
                    db.rollback()
                    self._schema_manager.restore_after_rollback(db)
    """

    def __init__(self) -> None:
        self._captured_schema: Optional[str] = None

    @property
    def schema(self) -> Optional[str]:
        """Return the captured schema name."""
        return self._captured_schema

    def capture(self, db: Session) -> Optional[str]:
        """
        Capture current schema for later restoration.

        Args:
            db: SQLAlchemy session

        Returns:
            Captured schema name or None
        """
        self._captured_schema = get_current_schema(db)
        return self._captured_schema

    def restore(self, db: Session) -> None:
        """
        Restore search_path to captured schema.

        Args:
            db: SQLAlchemy session
        """
        if self._captured_schema:
            restore_search_path(db, self._captured_schema)

    def restore_after_rollback(self, db: Session) -> None:
        """
        Restore search_path after rollback, handling InFailedSqlTransaction.

        Args:
            db: SQLAlchemy session
        """
        restore_search_path_after_rollback(db, self._captured_schema)

    def commit_and_restore(self, db: Session) -> None:
        """
        Commit and restore search_path.

        If no schema was captured, captures current schema before commit.

        Args:
            db: SQLAlchemy session
        """
        if not self._captured_schema:
            self.capture(db)
        commit_and_restore_path(db)


__all__ = [
    "get_current_schema",
    "restore_search_path",
    "restore_search_path_after_rollback",
    "commit_and_restore_path",
    "SchemaManager",
]
