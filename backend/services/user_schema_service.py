"""
User Schema Service

Service pour gérer la création automatique des schemas user_X et leurs tables.

Business Rules (2025-12-08):
- Chaque user doit avoir son propre schema PostgreSQL (user_{id})
- Le schema est cloné depuis template_tenant
- Création automatique lors de l'enregistrement d'un user

Author: Claude
Date: 2025-12-08
Updated: 2025-12-11 - Added specific exception handling
Updated: 2025-12-22 - Fixed to use template_tenant instead of public schema
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

    # Tables à créer dans chaque schema user_X (copiées depuis template_tenant)
    # L'ordre est important pour respecter les dépendances de foreign keys
    SCHEMA_TABLES = [
        "products",
        "product_images",
        "vinted_products",
        "ai_generation_logs",
        "publication_history",
        "plugin_tasks",
        "vinted_connection",
        "vinted_jobs",
        "vinted_job_stats",
        "vinted_conversations",
        "vinted_messages",
        "vinted_error_logs",
        "ebay_credentials",
        "ebay_products",
        "ebay_products_marketplace",
        "ebay_orders",
        "ebay_orders_products",
        "ebay_promoted_listings",
    ]

    @classmethod
    def create_user_schema(cls, db: Session, user_id: int) -> str:
        """
        Crée le schema PostgreSQL pour un utilisateur en clonant template_tenant.

        Business Rules (Updated 2025-12-22):
        - Schema nommé user_{id}
        - Clone toutes les tables depuis template_tenant
        - Idempotent (ne fait rien si le schema existe)

        Args:
            db: Session SQLAlchemy
            user_id: ID de l'utilisateur

        Returns:
            str: Nom du schema créé (user_{id})

        Raises:
            SchemaCreationError: Si erreur lors de la création
        """
        schema_name = f"user_{user_id}"

        try:
            # 1. Créer le schema
            db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
            db.commit()

            # 2. Créer toutes les tables en les clonant depuis template_tenant
            for table_name in cls.SCHEMA_TABLES:
                # Vérifier si la table existe dans template_tenant
                check_sql = text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = 'template_tenant'
                        AND table_name = :table_name
                    )
                """)
                result = db.execute(check_sql, {"table_name": table_name})
                table_exists = result.scalar()

                if table_exists:
                    # Cloner la table depuis template_tenant
                    create_sql = f"""
                        CREATE TABLE IF NOT EXISTS {schema_name}.{table_name} (
                            LIKE template_tenant.{table_name} INCLUDING ALL
                        )
                    """
                    db.execute(text(create_sql))
                    db.commit()
                else:
                    logger.warning(
                        f"Table template_tenant.{table_name} not found, skipping"
                    )

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
                "missing_tables": cls.SCHEMA_TABLES,
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
        expected_tables = set(cls.SCHEMA_TABLES)
        actual_tables = set(existing_tables)
        missing_tables = expected_tables - actual_tables

        return {
            "schema_exists": True,
            "schema_name": schema_name,
            "tables": existing_tables,
            "missing_tables": list(missing_tables),
            "is_complete": len(missing_tables) == 0
        }
