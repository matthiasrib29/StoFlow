"""
Create Fresh Test Batches

Creates sample batch jobs for validation after cleanup.
Used to verify the batch processing system works correctly with fresh data.

Usage:
    python create_test_batches.py           # Create test batches
    python create_test_batches.py --verify  # Verify existing batches

Author: Claude
Date: 2026-01-19
"""

import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add parent directory to PYTHONPATH
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from shared.database import SessionLocal
from shared.logging import get_logger

logger = get_logger(__name__)


def generate_batch_id(marketplace: str, action: str) -> str:
    """Generate a unique batch ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    short_uuid = uuid.uuid4().hex[:8]
    return f"{marketplace}_{action}_{timestamp}_{short_uuid}"


def create_test_batches(schema: str = "user_1"):
    """
    Create fresh test batches for validation.

    Creates 3 batches (one per marketplace) with sample jobs.

    Args:
        schema: User schema to create batches in (default: user_1)
    """
    logger.info(f"[TestBatches] Creating fresh test batches in {schema}")

    db = SessionLocal()

    try:
        db.execute(text(f"SET search_path TO {schema}, public"))

        # Check if batch_jobs table exists
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = 'batch_jobs'
            )
        """), {"schema": schema})

        if not result.scalar():
            logger.error(f"[TestBatches] Table batch_jobs not found in {schema}")
            return

        # Check if marketplace_jobs table exists
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = 'marketplace_jobs'
            )
        """), {"schema": schema})

        if not result.scalar():
            logger.error(f"[TestBatches] Table marketplace_jobs not found in {schema}")
            return

        # Batch configurations
        batches_config = [
            {
                "marketplace": "vinted",
                "action_code": "publish",
                "total_count": 3,
                "priority": 2,
            },
            {
                "marketplace": "ebay",
                "action_code": "publish",
                "total_count": 3,
                "priority": 3,
            },
            {
                "marketplace": "etsy",
                "action_code": "publish",
                "total_count": 2,
                "priority": 3,
            },
        ]

        created_batches = []

        for config in batches_config:
            batch_id = generate_batch_id(config["marketplace"], config["action_code"])

            # Create batch_job
            db.execute(text("""
                INSERT INTO batch_jobs (
                    batch_id, marketplace, action_code, total_count, priority, status, created_at
                ) VALUES (
                    :batch_id, :marketplace, :action_code, :total_count, :priority, 'pending', NOW()
                )
            """), {
                "batch_id": batch_id,
                "marketplace": config["marketplace"],
                "action_code": config["action_code"],
                "total_count": config["total_count"],
                "priority": config["priority"],
            })

            # Get the batch ID
            result = db.execute(text("""
                SELECT id FROM batch_jobs WHERE batch_id = :batch_id
            """), {"batch_id": batch_id})
            batch_db_id = result.scalar()

            logger.info(
                f"[TestBatches] Created batch {batch_id} "
                f"(id={batch_db_id}, {config['marketplace']}/{config['action_code']}, "
                f"{config['total_count']} jobs)"
            )

            created_batches.append({
                "id": batch_db_id,
                "batch_id": batch_id,
                **config
            })

        db.commit()

        logger.info(
            f"[TestBatches] Successfully created {len(created_batches)} test batches"
        )

        return created_batches

    except Exception as e:
        logger.error(f"[TestBatches] Error creating test batches: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


def verify_test_batches(schema: str = "user_1"):
    """
    Verify that test batches exist and are valid.

    Args:
        schema: User schema to verify (default: user_1)
    """
    logger.info(f"[TestBatches] Verifying test batches in {schema}")

    db = SessionLocal()

    try:
        db.execute(text(f"SET search_path TO {schema}, public"))

        # Count batches
        result = db.execute(text("""
            SELECT COUNT(*),
                   SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                   SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM batch_jobs
        """))
        row = result.fetchone()

        total, pending, running, completed = row
        logger.info(
            f"[TestBatches] Found {total} batches: "
            f"{pending} pending, {running} running, {completed} completed"
        )

        # List batches
        result = db.execute(text("""
            SELECT id, batch_id, marketplace, action_code, total_count, status, created_at
            FROM batch_jobs
            ORDER BY created_at DESC
            LIMIT 10
        """))

        for row in result:
            logger.info(
                f"[TestBatches]   - {row.batch_id}: "
                f"{row.marketplace}/{row.action_code}, "
                f"{row.total_count} jobs, status={row.status}"
            )

        return total > 0

    except Exception as e:
        logger.error(f"[TestBatches] Error verifying test batches: {e}", exc_info=True)
        return False
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Create or verify test batch jobs"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify existing batches instead of creating new ones"
    )
    parser.add_argument(
        "--schema",
        type=str,
        default="user_1",
        help="User schema to use (default: user_1)"
    )

    args = parser.parse_args()

    if args.verify:
        verify_test_batches(schema=args.schema)
    else:
        create_test_batches(schema=args.schema)
