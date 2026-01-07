#!/usr/bin/env python3
"""
Retroactive Migration Script: Create BatchJob Parents for Existing Jobs

This script migrates existing MarketplaceJobs with batch_id string (old system)
to the new BatchJob architecture by creating BatchJob parents.

Workflow:
1. Find all unique batch_id strings in marketplace_jobs where batch_job_id IS NULL
2. For each batch_id:
   - Create a BatchJob parent
   - Link all jobs with that batch_id to the new BatchJob
   - Calculate batch progress counters

Created: 2026-01-07
Phase 5.1: Data migration
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.orm import Session

from models.user.batch_job import BatchJob, BatchJobStatus
from models.user.marketplace_job import MarketplaceJob, JobStatus
from shared.database import engine
from shared.logging_setup import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def extract_action_from_batch_id(batch_id: str) -> str:
    """
    Extract action_code from batch_id string.

    Batch IDs follow pattern: {action}_{timestamp}_{uuid}
    Example: "publish_20260107_120530_abc123" -> "publish"
    Example: "link_product_20260107_120530_abc123" -> "link_product"

    Args:
        batch_id: Batch identifier string

    Returns:
        Action code (publish, link_product, etc.)
    """
    if not batch_id:
        return "unknown"

    parts = batch_id.split("_")

    # If batch_id has at least 3 parts, we need to detect multi-word actions
    # Pattern: {action}_{timestamp}_{time}_{uuid} or {multi_word_action}_{timestamp}_{time}_{uuid}
    # Actions with underscores: link_product
    # Look for timestamp pattern (YYYYMMDD) to know where action ends

    if len(parts) < 2:
        return parts[0] if parts else "unknown"

    # Check if second part looks like a timestamp (8 digits)
    if len(parts) >= 2 and parts[1].isdigit() and len(parts[1]) == 8:
        # Single word action (e.g., "publish_20260107_...")
        return parts[0]

    # Check if third part looks like a timestamp
    if len(parts) >= 3 and parts[2].isdigit() and len(parts[2]) == 8:
        # Two-word action (e.g., "link_product_20260107_...")
        return f"{parts[0]}_{parts[1]}"

    # Fallback: just return first part
    return parts[0]


def calculate_batch_status(jobs: list[MarketplaceJob]) -> BatchJobStatus:
    """
    Calculate batch status from child jobs.

    Args:
        jobs: List of MarketplaceJob instances

    Returns:
        BatchJobStatus enum value
    """
    if not jobs:
        return BatchJobStatus.PENDING

    completed_count = sum(1 for j in jobs if j.status == JobStatus.COMPLETED)
    failed_count = sum(1 for j in jobs if j.status == JobStatus.FAILED)
    cancelled_count = sum(1 for j in jobs if j.status == JobStatus.CANCELLED)
    running_count = sum(1 for j in jobs if j.status == JobStatus.RUNNING)
    pending_count = sum(1 for j in jobs if j.status == JobStatus.PENDING)
    total_count = len(jobs)

    # All completed
    if completed_count == total_count:
        return BatchJobStatus.COMPLETED

    # All failed
    if failed_count == total_count:
        return BatchJobStatus.FAILED

    # All cancelled
    if cancelled_count == total_count:
        return BatchJobStatus.CANCELLED

    # Some running (regardless of other statuses)
    if running_count > 0:
        return BatchJobStatus.RUNNING

    # Some pending (regardless of other statuses, but no running)
    if pending_count > 0:
        return BatchJobStatus.PENDING

    # All terminal statuses (completed, failed, cancelled) with at least one failure
    if completed_count + failed_count + cancelled_count == total_count and failed_count > 0:
        return BatchJobStatus.PARTIALLY_FAILED

    # Default: pending
    return BatchJobStatus.PENDING


# =============================================================================
# MIGRATION LOGIC
# =============================================================================


def migrate_schema(schema_name: str, db: Session) -> dict:
    """
    Migrate jobs in a single schema.

    Args:
        schema_name: Schema to migrate (e.g., 'user_1')
        db: Database session

    Returns:
        Migration stats dict
    """
    logger.info(f"🔄 Migrating schema: {schema_name}")

    # Set search path
    db.execute(text(f"SET search_path TO {schema_name}, public"))
    db.commit()

    stats = {
        "schema": schema_name,
        "batches_created": 0,
        "jobs_linked": 0,
        "errors": 0,
    }

    try:
        # 1. Find all unique batch_id strings where batch_job_id IS NULL
        result = db.execute(
            text("""
                SELECT DISTINCT batch_id
                FROM marketplace_jobs
                WHERE batch_id IS NOT NULL
                  AND batch_job_id IS NULL
                ORDER BY batch_id
            """)
        )
        unique_batch_ids = [row[0] for row in result.fetchall()]

        logger.info(f"   Found {len(unique_batch_ids)} unique batch_ids to migrate")

        if len(unique_batch_ids) == 0:
            logger.info(f"   ✅ No batches to migrate in {schema_name}")
            return stats

        # 2. For each batch_id, create BatchJob parent
        for batch_id_str in unique_batch_ids:
            try:
                # Get all jobs for this batch
                jobs = (
                    db.query(MarketplaceJob)
                    .filter(
                        MarketplaceJob.batch_id == batch_id_str,
                        MarketplaceJob.batch_job_id.is_(None),
                    )
                    .all()
                )

                if not jobs:
                    logger.warning(f"   ⚠️  No jobs found for batch_id: {batch_id_str}")
                    continue

                # Extract metadata from first job
                first_job = jobs[0]
                action_code = extract_action_from_batch_id(batch_id_str)
                marketplace = first_job.marketplace or "vinted"

                # Calculate status and counters
                batch_status = calculate_batch_status(jobs)
                completed_count = sum(1 for j in jobs if j.status == JobStatus.COMPLETED)
                failed_count = sum(1 for j in jobs if j.status == JobStatus.FAILED)
                cancelled_count = sum(1 for j in jobs if j.status == JobStatus.CANCELLED)

                # Find min created_at and max completed_at
                created_at = min(j.created_at for j in jobs)
                started_at = min(
                    (j.started_at for j in jobs if j.started_at), default=None
                )
                completed_at = None
                if batch_status in (
                    BatchJobStatus.COMPLETED,
                    BatchJobStatus.PARTIALLY_FAILED,
                    BatchJobStatus.FAILED,
                    BatchJobStatus.CANCELLED,
                ):
                    completed_at = max(
                        (j.completed_at for j in jobs if j.completed_at), default=None
                    )

                # 3. Create BatchJob parent
                batch = BatchJob(
                    batch_id=batch_id_str,
                    marketplace=marketplace,
                    action_code=action_code,
                    total_count=len(jobs),
                    completed_count=completed_count,
                    failed_count=failed_count,
                    cancelled_count=cancelled_count,
                    status=batch_status,
                    priority=first_job.priority,
                    created_by_user_id=None,  # Unknown for old jobs
                    created_at=created_at,
                    started_at=started_at,
                    completed_at=completed_at,
                )
                db.add(batch)
                db.flush()  # Get batch.id

                # 4. Link all jobs to this BatchJob
                for job in jobs:
                    job.batch_job_id = batch.id

                db.commit()

                stats["batches_created"] += 1
                stats["jobs_linked"] += len(jobs)

                logger.info(
                    f"   ✅ Created BatchJob #{batch.id} for batch_id '{batch_id_str}' "
                    f"({len(jobs)} jobs, status={batch_status.value})"
                )

            except Exception as e:
                db.rollback()
                stats["errors"] += 1
                logger.error(
                    f"   ❌ Error migrating batch_id '{batch_id_str}': {e}",
                    exc_info=True,
                )

    except Exception as e:
        logger.error(f"   ❌ Error migrating schema {schema_name}: {e}", exc_info=True)
        stats["errors"] += 1

    return stats


def migrate_all_schemas() -> dict:
    """
    Migrate all user schemas.

    Returns:
        Global migration stats
    """
    logger.info("=" * 80)
    logger.info("🚀 Starting retroactive BatchJob migration")
    logger.info("=" * 80)

    global_stats = {
        "schemas_migrated": 0,
        "batches_created": 0,
        "jobs_linked": 0,
        "errors": 0,
        "start_time": datetime.now(timezone.utc),
    }

    with Session(engine) as db:
        # Get all user schemas
        result = db.execute(
            text("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name LIKE 'user_%'
                  AND schema_name <> 'user_invalid'
                ORDER BY schema_name
            """)
        )
        schemas = [row[0] for row in result.fetchall()]

        logger.info(f"\n📋 Found {len(schemas)} user schemas to migrate\n")

        # Migrate each schema
        for schema_name in schemas:
            schema_stats = migrate_schema(schema_name, db)

            global_stats["schemas_migrated"] += 1
            global_stats["batches_created"] += schema_stats["batches_created"]
            global_stats["jobs_linked"] += schema_stats["jobs_linked"]
            global_stats["errors"] += schema_stats["errors"]

    global_stats["end_time"] = datetime.now(timezone.utc)
    global_stats["duration"] = (
        global_stats["end_time"] - global_stats["start_time"]
    ).total_seconds()

    return global_stats


# =============================================================================
# MAIN
# =============================================================================


def main():
    """Run migration script."""
    try:
        # Run migration
        stats = migrate_all_schemas()

        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("📊 MIGRATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"✅ Schemas migrated:    {stats['schemas_migrated']}")
        logger.info(f"✅ BatchJobs created:   {stats['batches_created']}")
        logger.info(f"✅ Jobs linked:         {stats['jobs_linked']}")
        logger.info(f"❌ Errors:              {stats['errors']}")
        logger.info(f"⏱️  Duration:            {stats['duration']:.2f}s")
        logger.info("=" * 80)

        if stats["errors"] > 0:
            logger.warning(
                "\n⚠️  Migration completed with errors. Check logs above for details."
            )
            sys.exit(1)
        else:
            logger.info("\n🎉 Migration completed successfully!")
            sys.exit(0)

    except Exception as e:
        logger.error(f"❌ Fatal error during migration: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
