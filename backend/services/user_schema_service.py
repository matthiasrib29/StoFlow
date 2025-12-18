"""
User Schema Service

Service pour gérer la création automatique des schemas user_X et leurs tables.

Business Rules (2025-12-08):
- Chaque user doit avoir son propre schema PostgreSQL (user_{id})
- Le schema contient 6 tables isolées par user
- Création automatique lors de l'enregistrement d'un user

Author: Claude
Date: 2025-12-08
Updated: 2025-12-11 - Added specific exception handling
"""
import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError, OperationalError
from sqlalchemy.orm import Session

from models.public.user import User
from shared.exceptions import SchemaCreationError, DatabaseError

logger = logging.getLogger(__name__)


class UserSchemaService:
    """Service pour gérer les schemas utilisateur."""

    # Tables à créer dans chaque schema user_X
    SCHEMA_TABLES = {
        "products": """
            CREATE TABLE IF NOT EXISTS {schema}.products (
                LIKE public.products INCLUDING ALL
            )
        """,
        "product_images": """
            CREATE TABLE IF NOT EXISTS {schema}.product_images (
                LIKE public.product_images INCLUDING ALL
            )
        """,
        "vinted_products": """
            CREATE TABLE IF NOT EXISTS {schema}.vinted_products (
                LIKE public.vinted_products INCLUDING ALL
            )
        """,
        "ai_generation_logs": """
            CREATE TABLE IF NOT EXISTS {schema}.ai_generation_logs (
                LIKE public.ai_generation_logs INCLUDING ALL
            )
        """,
        "publication_history": """
            CREATE TABLE IF NOT EXISTS {schema}.publication_history (
                LIKE public.publication_history INCLUDING ALL
            )
        """,
        "plugin_tasks": """
            CREATE TABLE IF NOT EXISTS {schema}.plugin_tasks (
                id SERIAL PRIMARY KEY,
                task_type VARCHAR(100),
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                payload JSONB NOT NULL DEFAULT '{}',
                result JSONB,
                error_message TEXT,
                product_id INTEGER,
                platform VARCHAR(50),
                http_method VARCHAR(10),
                path VARCHAR(500),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                started_at TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE,
                retry_count INTEGER DEFAULT 0 NOT NULL,
                max_retries INTEGER DEFAULT 3 NOT NULL
            )
        """,
        "vinted_connection": """
            CREATE TABLE IF NOT EXISTS {schema}.vinted_connection (
                vinted_user_id INTEGER PRIMARY KEY,
                login VARCHAR(255) NOT NULL,
                is_connected BOOLEAN NOT NULL DEFAULT TRUE,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                last_sync TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                disconnected_at TIMESTAMP WITH TIME ZONE
            )
        """
    }

    @classmethod
    def create_user_schema(cls, db: Session, user_id: int) -> str:
        """
        Crée le schema PostgreSQL pour un utilisateur et toutes ses tables.

        Business Rules (Updated 2025-12-09):
        - Schema nommé user_{id}
        - Contient 6 tables isolées
        - ID auto-incrémenté pour les produits (PostgreSQL SERIAL)
        - Idempotent (ne fait rien si le schema existe)

        Args:
            db: Session SQLAlchemy
            user_id: ID de l'utilisateur

        Returns:
            str: Nom du schema créé (user_{id})

        Raises:
            Exception: Si erreur lors de la création
        """
        schema_name = f"user_{user_id}"

        try:
            # 1. Créer le schema
            db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
            db.commit()

            # 2. Créer toutes les tables
            for table_name, create_sql in cls.SCHEMA_TABLES.items():
                sql = create_sql.format(schema=schema_name)
                db.execute(text(sql))
                db.commit()

            logger.info(f"Schema {schema_name} created successfully")
            return schema_name

        except ProgrammingError as e:
            db.rollback()
            logger.error(f"SQL syntax error creating schema {schema_name}: {e}")
            raise SchemaCreationError(
                f"Erreur SQL lors de la création du schema {schema_name}",
                details={"schema": schema_name, "error": str(e)}
            )
        except OperationalError as e:
            db.rollback()
            logger.error(f"Database connection error creating schema {schema_name}: {e}")
            raise DatabaseError(
                f"Erreur de connexion DB lors de la création du schema {schema_name}",
                details={"schema": schema_name, "error": str(e)}
            )
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error creating schema {schema_name}: {e}")
            raise SchemaCreationError(
                f"Erreur DB lors de la création du schema {schema_name}",
                details={"schema": schema_name, "error": str(e)}
            )

    @classmethod
    def delete_user_schema(cls, db: Session, user_id: int) -> None:
        """
        Supprime le schema d'un utilisateur (CASCADE).

        WARNING: Supprime TOUTES les données de l'utilisateur!

        Args:
            db: Session SQLAlchemy
            user_id: ID de l'utilisateur
        """
        schema_name = f"user_{user_id}"

        try:
            db.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
            db.commit()
            logger.info(f"Schema {schema_name} deleted successfully")

        except OperationalError as e:
            db.rollback()
            logger.error(f"Database connection error deleting schema {schema_name}: {e}")
            raise DatabaseError(
                f"Erreur de connexion DB lors de la suppression du schema {schema_name}",
                details={"schema": schema_name, "error": str(e)}
            )
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error deleting schema {schema_name}: {e}")
            raise DatabaseError(
                f"Erreur DB lors de la suppression du schema {schema_name}",
                details={"schema": schema_name, "error": str(e)}
            )

    @classmethod
    def verify_user_schema(cls, db: Session, user_id: int) -> dict:
        """
        Vérifie qu'un schema utilisateur existe et est complet.

        Args:
            db: Session SQLAlchemy
            user_id: ID de l'utilisateur

        Returns:
            dict: {
                "schema_exists": bool,
                "schema_name": str,
                "tables": list[str],
                "missing_tables": list[str],
                "is_complete": bool
            }
        """
        schema_name = f"user_{user_id}"

        # Vérifier si le schema existe
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.schemata
                WHERE schema_name = :schema
            )
        """), {"schema": schema_name})
        schema_exists = result.scalar()

        if not schema_exists:
            return {
                "schema_exists": False,
                "schema_name": schema_name,
                "tables": [],
                "missing_tables": list(cls.SCHEMA_TABLES.keys()),
                "is_complete": False
            }

        # Lister les tables présentes
        result = db.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = :schema
            ORDER BY table_name
        """), {"schema": schema_name})

        existing_tables = [row[0] for row in result.fetchall()]

        # Tables manquantes
        expected_tables = set(cls.SCHEMA_TABLES.keys())
        actual_tables = set(existing_tables)
        missing_tables = expected_tables - actual_tables

        return {
            "schema_exists": True,
            "schema_name": schema_name,
            "tables": existing_tables,
            "missing_tables": list(missing_tables),
            "is_complete": len(missing_tables) == 0
        }
