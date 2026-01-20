"""
Cleanup Abandoned Draft Products

Supprime les produits DRAFT abandonnés (title="" et créés il y a plus de 7 jours).

Ces produits sont créés automatiquement lors de l'upload d'images AVANT de remplir
le formulaire. S'ils ne sont jamais complétés, ils polluent la base de données.

Usage:
    python cleanup_abandoned_drafts.py [--dry-run] [--days=7]

Options:
    --dry-run: Affiche ce qui serait supprimé sans rien supprimer
    --days=N:  Nombre de jours avant suppression (défaut: 7)

Author: Claude
Date: 2026-01-07
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Ajouter le répertoire parent au PYTHONPATH
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from shared.database import SessionLocal
from shared.logging import get_logger

logger = get_logger(__name__)


def cleanup_abandoned_drafts(dry_run: bool = False, days: int = 7):
    """
    Supprime les produits DRAFT abandonnés.

    Args:
        dry_run: Si True, affiche seulement ce qui serait supprimé
        days: Nombre de jours avant qu'un draft soit considéré abandonné
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    logger.info(
        f"[Cleanup] Starting cleanup of abandoned drafts "
        f"(older than {days} days, cutoff={cutoff_date})"
    )

    db = SessionLocal()

    try:
        # 1. Récupérer tous les schemas user_*
        result = db.execute(text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name LIKE 'user_%'
            ORDER BY schema_name
        """))

        user_schemas = [row[0] for row in result]

        logger.info(f"[Cleanup] Found {len(user_schemas)} user schemas")

        total_deleted = 0

        # 2. Pour chaque schema, supprimer les drafts abandonnés
        for schema in user_schemas:
            # Use schema_translate_map for this schema iteration
            # Also set search_path for text() queries
            schema_db = db.execution_options(schema_translate_map={"tenant": schema})
            db.execute(text(f"SET search_path TO {schema}, public"))

            # Compter les drafts abandonnés
            count_result = db.execute(text("""
                SELECT COUNT(*)
                FROM products
                WHERE status = 'draft'
                  AND (title IS NULL OR title = '')
                  AND created_at < :cutoff_date
                  AND deleted_at IS NULL
            """), {"cutoff_date": cutoff_date})

            count = count_result.scalar()

            if count > 0:
                if dry_run:
                    logger.info(f"[Cleanup] {schema}: Would delete {count} abandoned draft(s)")

                    # Afficher les IDs qui seraient supprimés
                    ids_result = db.execute(text("""
                        SELECT id, created_at
                        FROM products
                        WHERE status = 'draft'
                          AND (title IS NULL OR title = '')
                          AND created_at < :cutoff_date
                          AND deleted_at IS NULL
                        ORDER BY created_at
                    """), {"cutoff_date": cutoff_date})

                    for product_id, created_at in ids_result:
                        age_days = (datetime.utcnow() - created_at).days
                        logger.info(
                            f"[Cleanup]   - Product ID {product_id} "
                            f"(created {age_days} days ago)"
                        )
                else:
                    # SOFT DELETE (set deleted_at)
                    db.execute(text("""
                        UPDATE products
                        SET deleted_at = NOW()
                        WHERE status = 'draft'
                          AND (title IS NULL OR title = '')
                          AND created_at < :cutoff_date
                          AND deleted_at IS NULL
                    """), {"cutoff_date": cutoff_date})

                    db.commit()

                    logger.info(
                        f"[Cleanup] {schema}: Soft deleted {count} abandoned draft(s)"
                    )

                total_deleted += count

        # Note: no need to reset search_path with schema_translate_map

        if dry_run:
            logger.info(
                f"[Cleanup] DRY RUN: Would soft delete {total_deleted} "
                f"abandoned draft(s) in total"
            )
        else:
            logger.info(
                f"[Cleanup] Successfully soft deleted {total_deleted} "
                f"abandoned draft(s) in total"
            )

    except Exception as e:
        logger.error(f"[Cleanup] Error during cleanup: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Cleanup abandoned draft products"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without deleting"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days before a draft is considered abandoned (default: 7)"
    )

    args = parser.parse_args()

    cleanup_abandoned_drafts(dry_run=args.dry_run, days=args.days)
