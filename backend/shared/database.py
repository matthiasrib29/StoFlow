"""
Database session management avec support multi-tenant.
"""
import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from shared.config import settings

# Base pour models SQLAlchemy
Base = declarative_base()

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
    except Exception:
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
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def set_user_schema(db: Session, user_id: int) -> None:
    """
    Configure le search_path PostgreSQL pour isoler l'utilisateur.

    DEPRECATED (2025-12-17): Use `get_user_db` dependency from api.dependencies instead.
    This function is kept for unit tests only.

    For production code, use:
        from api.dependencies import get_user_db

        @router.get("/endpoint")
        def my_endpoint(user_db: tuple = Depends(get_user_db)):
            db, current_user = user_db
            # db is already configured with search_path

    Args:
        db: Session SQLAlchemy
        user_id: ID de l'utilisateur

    Raises:
        ValueError: Si user_id n'est pas un entier valide (Security: 2025-12-07)
    """
    import re

    # ===== SECURITY FIX (2025-12-07, updated 2025-12-23): SQL Injection Protection =====
    # Step 1: Validation stricte: user_id DOIT être un integer positif
    if not isinstance(user_id, int):
        raise ValueError(
            f"Invalid user_id: must be integer, got {type(user_id).__name__}"
        )

    if user_id <= 0:
        raise ValueError(f"Invalid user_id: must be positive, got {user_id}")

    # Step 2: Build and validate schema_name
    schema_name = f"user_{user_id}"

    # Step 3: Defense-in-depth - verify pattern matches expected format
    if not re.match(r'^user_\d+$', schema_name):
        raise ValueError(f"Invalid schema_name generated: {schema_name}")

    db.execute(text(f"SET search_path TO {schema_name}, public"))


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
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
