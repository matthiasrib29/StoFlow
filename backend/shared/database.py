"""
Database session management avec support multi-tenant.
"""
import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text, MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.orm import Session, DeclarativeBase, sessionmaker

from shared.logging import get_logger

logger = get_logger(__name__)

from shared.config import settings


# Naming convention for constraints and indexes
# This ensures predictable, consistent names across all migrations
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


# Base class for all SQLAlchemy models
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


# Alias for tenant models (models/user/*)
# All tenant models should inherit from UserBase for clarity
# The actual schema is set via __table_args__ = {"schema": "tenant"}
UserBase = Base


def get_tenant_schema(db: Session) -> str | None:
    """
    Get tenant schema name from session's schema_translate_map.

    This function extracts the schema name that was configured via
    execution_options(schema_translate_map={"tenant": "user_X"}).

    Usage:
        schema = get_tenant_schema(db)
        # Returns "user_X" if schema_translate_map was set
        # Returns None if not using schema_translate_map

    Args:
        db: SQLAlchemy session with schema_translate_map configured

    Returns:
        Schema name (e.g., "user_123") or None if not set
    """
    # Access execution options from the session's bind
    execution_options = db.get_bind().execution_options
    schema_map = execution_options.get("schema_translate_map", {})
    return schema_map.get("tenant")


# Engine PostgreSQL (connexion globale)
engine = create_engine(
    str(settings.database_url),
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=True,  # Vérifier connexion avant usage
    echo=False,  # Disable SQL query logging (too verbose)
)

# TESTING: Hook pour ignorer SET search_path en SQLite (tests)
# Enregistré inconditionnellement mais actif uniquement en mode TEST
@event.listens_for(engine, "before_cursor_execute")
def intercept_search_path(conn, cursor, statement, params, context, executemany):
    # Ne s'active qu'en mode test (SQLite ne supporte pas SET search_path)
    if os.getenv("TESTING") and statement.startswith("SET search_path"):
        # SQLite ne supporte pas search_path, remplacer par SELECT 1 (no-op)
        return "SELECT 1", ()
    return statement, params

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Event listener for database connection (future use)."""
    pass


def get_db() -> Generator[Session, None, None]:
    """
    Dependency pour FastAPI : fournit une session database.

    Auto-commits on success, rollbacks on exception.
    Services should use flush() instead of commit() to stay in transaction.

    Usage dans routes:
        @app.get("/api/endpoint")
        def my_endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Auto-commit on success
    except SQLAlchemyError:
        db.rollback()  # Rollback on error
        raise
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager pour sessions DB hors FastAPI.

    Usage:
        with get_db_context() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def validate_schema_name(schema_name: str) -> str:
    """
    Validate PostgreSQL schema name for safe interpolation.

    Security: Prevents SQL injection via schema names (2026-01-12)

    Validation rules:
    - Must start with letter or underscore
    - Can only contain alphanumeric and underscore
    - Max length 63 bytes (PostgreSQL limit)
    - Cannot be a reserved schema (pg_catalog, information_schema, pg_toast)

    Args:
        schema_name: Schema name to validate

    Returns:
        Validated schema name

    Raises:
        ValueError: If schema name is invalid
    """
    import re

    # Allow only: alphanumeric, underscore
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', schema_name):
        raise ValueError(
            f"Invalid schema name: {schema_name}. "
            f"Must match ^[a-zA-Z_][a-zA-Z0-9_]*$"
        )

    # Max length check (PostgreSQL limit: 63 bytes)
    if len(schema_name) > 63:
        raise ValueError(f"Schema name too long: {len(schema_name)} > 63")

    # Blacklist reserved schemas
    reserved = {'pg_catalog', 'information_schema', 'pg_toast'}
    if schema_name.lower() in reserved:
        raise ValueError(f"Schema name is reserved: {schema_name}")

    return schema_name


# REMOVED (2026-01-13): Deprecated functions removed as part of schema_translate_map migration
# - set_search_path_safe() - Use execution_options(schema_translate_map={"tenant": schema}) instead
# - set_user_schema() - Use execution_options(schema_translate_map={"tenant": schema}) instead
# - set_user_search_path() - Use execution_options(schema_translate_map={"tenant": schema}) instead
# See ROADMAP.md Phase 4 for details


# NOTE (2025-12-08): La fonction create_user_schema() a été déplacée vers
# services/user_schema_service.py pour une meilleure organisation et fonctionnalités étendues.
# Utiliser UserSchemaService.create_user_schema() à la place.


def check_database_connection() -> bool:
    """
    Vérifie la connexion à la base de données.

    Returns:
        True si connexion OK, False sinon
    """
    try:
        with get_db_context() as db:
            db.execute(text("SELECT 1"))
        return True
    except (OperationalError, SQLAlchemyError) as e:
        logger.error(f"Database connection failed: {e}")
        return False
