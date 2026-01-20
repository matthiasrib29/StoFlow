"""
Cleanup Old Jobs and Batches

Deletes all jobs, tasks, and batches created before a cutoff date.
Used before production launch to clean test data accumulated during development.

DELETION ORDER (respects FK constraints):
    1. marketplace_tasks (FK to marketplace_jobs)
    2. marketplace_jobs (FK to batch_jobs)
    3. batch_jobs (parent table)

Usage:
    python cleanup_old_jobs.py [--dry-run] [--cutoff-date=2026-01-01]

Options:
    --dry-run: Show what would be deleted without deleting
    --cutoff-date: Delete records created BEFORE this date (default: 2026-01-01)

Safety:
    - Always use --dry-run first to preview deletions
    - Script uses transactions - partial runs are rolled back on error
    - DO NOT run on production without explicit approval

Author: Claude
Date: 2026-01-19
"""

import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to PYTHONPATH
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from shared.database import SessionLocal
from shared.logging import get_logger

logger = get_logger(__name__)


def table_exists(db, schema: str, table_name: str) -> bool:
    """Check if a table exists in the given schema."""
    result = db.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table_name
        )
    """), {"schema": schema, "table_name": table_name})
    return result.scalar()


def cleanup_old_jobs(dry_run: bool = False, cutoff_date: str = "2026-01-01"):
    """
    Delete old jobs/batches from all tenant schemas.

    Order of deletion (FK constraints):
    1. marketplace_tasks (FK to marketplace_jobs)
    2. marketplace_jobs (FK to batch_jobs)
    3. batch_jobs (parent)

    Args:
        dry_run: If True, only show what would be deleted
        cutoff_date: Delete records created before this date (YYYY-MM-DD)
    """
    try:
        cutoff = datetime.strptime(cutoff_date, "%Y-%m-%d")
    except ValueError:
        logger.error(f"Invalid cutoff date format: {cutoff_date}. Use YYYY-MM-DD.")
        return

    logger.info(
        f"[Cleanup] Starting cleanup of old jobs/batches "
        f"(created before {cutoff_date})"
    )

    if dry_run:
        logger.info("[Cleanup] DRY RUN MODE - no data will be deleted")

    db = SessionLocal()

    try:
        # 1. Get all user_* schemas
        result = db.execute(text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name LIKE 'user_%'
            ORDER BY schema_name
        """))

        user_schemas = [row[0] for row in result]

        logger.info(f"[Cleanup] Found {len(user_schemas)} user schemas")

        # Track totals across all schemas
        total_tasks = 0
        total_jobs = 0
        total_batches = 0

        # 2. Process each schema
        for schema in user_schemas:
            db.execute(text(f"SET search_path TO {schema}, public"))

            # Check if tables exist in this schema
            has_tasks = table_exists(db, schema, "marketplace_tasks")
            has_jobs = table_exists(db, schema, "marketplace_jobs")
            has_batches = table_exists(db, schema, "batch_jobs")

            if not has_jobs and not has_batches:
                logger.debug(f"[Cleanup] {schema}: No job tables found, skipping")
                continue

            schema_tasks = 0
            schema_jobs = 0
            schema_batches = 0

            # 2a. Count and delete marketplace_tasks (must be first due to FK)
            if has_tasks:
                count_result = db.execute(text("""
                    SELECT COUNT(*)
                    FROM marketplace_tasks
                    WHERE created_at < :cutoff
                """), {"cutoff": cutoff})
                schema_tasks = count_result.scalar() or 0

                if schema_tasks > 0 and not dry_run:
                    db.execute(text("""
                        DELETE FROM marketplace_tasks
                        WHERE created_at < :cutoff
                    """), {"cutoff": cutoff})

            # 2b. Count and delete marketplace_jobs (must be before batch_jobs)
            if has_jobs:
                count_result = db.execute(text("""
                    SELECT COUNT(*)
                    FROM marketplace_jobs
                    WHERE created_at < :cutoff
                """), {"cutoff": cutoff})
                schema_jobs = count_result.scalar() or 0

                if schema_jobs > 0 and not dry_run:
                    db.execute(text("""
                        DELETE FROM marketplace_jobs
                        WHERE created_at < :cutoff
                    """), {"cutoff": cutoff})

            # 2c. Count and delete batch_jobs (parent table, delete last)
            if has_batches:
                count_result = db.execute(text("""
                    SELECT COUNT(*)
                    FROM batch_jobs
                    WHERE created_at < :cutoff
                """), {"cutoff": cutoff})
                schema_batches = count_result.scalar() or 0

                if schema_batches > 0 and not dry_run:
                    db.execute(text("""
                        DELETE FROM batch_jobs
                        WHERE created_at < :cutoff
                    """), {"cutoff": cutoff})

            # Log per-schema results
            if schema_tasks > 0 or schema_jobs > 0 or schema_batches > 0:
                action = "Would delete" if dry_run else "Deleted"
                logger.info(
                    f"[Cleanup] {schema}: {action} "
                    f"{schema_tasks} tasks, {schema_jobs} jobs, {schema_batches} batches"
                )

            total_tasks += schema_tasks
            total_jobs += schema_jobs
            total_batches += schema_batches

        # Commit all changes (only if not dry_run)
        if not dry_run and (total_tasks > 0 or total_jobs > 0 or total_batches > 0):
            db.commit()
            logger.info("[Cleanup] Changes committed successfully")

        # Final summary
        logger.info(
            f"[Cleanup] {'DRY RUN SUMMARY' if dry_run else 'CLEANUP COMPLETE'}: "
            f"{total_tasks} tasks, {total_jobs} jobs, {total_batches} batches "
            f"{'would be deleted' if dry_run else 'deleted'}"
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
        description="Cleanup old jobs and batches from all user schemas"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without deleting"
    )
    parser.add_argument(
        "--cutoff-date",
        type=str,
        default="2026-01-01",
        help="Delete records created BEFORE this date (default: 2026-01-01)"
    )

    args = parser.parse_args()

    cleanup_old_jobs(dry_run=args.dry_run, cutoff_date=args.cutoff_date)
