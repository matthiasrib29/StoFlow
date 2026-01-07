# BatchJob Retroactive Migration Script

## Overview

This script migrates existing `MarketplaceJob` records with legacy `batch_id` strings to the new `BatchJob` architecture.

**Created:** 2026-01-07
**Phase:** 5.1 - Data Migration

---

## What It Does

The script performs the following operations for each user schema:

1. **Find old batches**: Identifies all unique `batch_id` strings where `batch_job_id IS NULL`
2. **Create BatchJob parents**: Creates a `BatchJob` parent for each unique `batch_id`
3. **Link jobs**: Updates all `MarketplaceJob` records to reference the new `BatchJob` via `batch_job_id` FK
4. **Calculate stats**: Computes batch progress counters (completed, failed, cancelled)

---

## Before Running

### 1. Backup Database

**CRITICAL**: Always backup your database before running data migrations.

```bash
# PostgreSQL backup
pg_dump -U postgres -d stoflow_db > backup_before_batch_migration_$(date +%Y%m%d_%H%M%S).sql

# Or via Docker
docker exec stoflow-postgres pg_dump -U postgres stoflow_db > backup_before_batch_migration_$(date +%Y%m%d_%H%M%S).sql
```

### 2. Check Data to Migrate

Run this command to see how many old batches exist:

```bash
cd backend
source venv/bin/activate

python3 -c "
from sqlalchemy import text, create_engine
from shared.config import settings

engine = create_engine(settings.database_url, echo=False)

with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
          AND schema_name <> 'user_invalid'
    '''))
    schemas = [row[0] for row in result.fetchall()]

    total_batches = 0
    for schema in schemas:
        result = conn.execute(text(f'''
            SELECT COUNT(DISTINCT batch_id)
            FROM {schema}.marketplace_jobs
            WHERE batch_id IS NOT NULL
              AND batch_job_id IS NULL
        '''))
        count = result.scalar()
        if count > 0:
            print(f'{schema}: {count} old batches')
            total_batches += count

    print(f'Total: {total_batches} old batches to migrate')
"
```

---

## Running the Script

### Production

```bash
cd backend
source venv/bin/activate

# Run the migration script
python3 scripts/migrate_existing_jobs_to_batch.py
```

### Test Environment

Run against a test database first:

```bash
cd backend
source venv/bin/activate

# Export test database URL
export DATABASE_URL="postgresql://stoflow_test:test_password_123@localhost:5434/stoflow_test"

# Run migration
python3 scripts/migrate_existing_jobs_to_batch.py
```

---

## Output Example

```
================================================================================
🚀 Starting retroactive BatchJob migration
================================================================================

📋 Found 3 user schemas to migrate

🔄 Migrating schema: user_1
   Found 5 unique batch_ids to migrate
   ✅ Created BatchJob #1 for batch_id 'publish_20260105_143022_abc123' (25 jobs, status=completed)
   ✅ Created BatchJob #2 for batch_id 'link_product_20260106_091530_def456' (10 jobs, status=running)
   ...

🔄 Migrating schema: user_2
   Found 0 unique batch_ids to migrate
   ✅ No batches to migrate in user_2

🔄 Migrating schema: user_3
   Found 2 unique batch_ids to migrate
   ✅ Created BatchJob #10 for batch_id 'sync_20260107_120000_xyz789' (50 jobs, status=partially_failed)

================================================================================
📊 MIGRATION SUMMARY
================================================================================
✅ Schemas migrated:    3
✅ BatchJobs created:   7
✅ Jobs linked:         85
❌ Errors:              0
⏱️  Duration:            1.23s
================================================================================

🎉 Migration completed successfully!
```

---

## What Gets Migrated

For each old `batch_id`:

- **BatchJob.batch_id** = Original batch_id string (preserved for backward compatibility)
- **BatchJob.marketplace** = Extracted from first job (default: 'vinted')
- **BatchJob.action_code** = Extracted from batch_id (e.g., 'publish', 'link_product')
- **BatchJob.total_count** = Number of jobs in batch
- **BatchJob.completed_count** = Count of COMPLETED jobs
- **BatchJob.failed_count** = Count of FAILED jobs
- **BatchJob.cancelled_count** = Count of CANCELLED jobs
- **BatchJob.status** = Calculated from job statuses
- **BatchJob.created_at** = Min created_at from jobs
- **BatchJob.started_at** = Min started_at from jobs (if any)
- **BatchJob.completed_at** = Max completed_at from jobs (if terminal status)

All `MarketplaceJob.batch_job_id` fields are updated to reference the new `BatchJob.id`.

---

## Batch Status Calculation

| Condition | Status |
|-----------|--------|
| All jobs completed | `completed` |
| All jobs failed | `failed` |
| All jobs cancelled | `cancelled` |
| Some completed, some failed (no pending) | `partially_failed` |
| Any job running | `running` |
| Default | `pending` |

---

## Safety Features

1. **Per-batch transactions**: Each batch creation is in its own try/catch
2. **Rollback on error**: Failed batches don't affect others
3. **Error tracking**: Script reports how many errors occurred
4. **Idempotent**: Can be run multiple times (only migrates where `batch_job_id IS NULL`)

---

## Verification After Migration

Check that all jobs are now linked to a BatchJob:

```bash
cd backend
source venv/bin/activate

python3 -c "
from sqlalchemy import text, create_engine
from shared.config import settings

engine = create_engine(settings.database_url, echo=False)

with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'user_%'
          AND schema_name <> 'user_invalid'
    '''))
    schemas = [row[0] for row in result.fetchall()]

    for schema in schemas:
        result = conn.execute(text(f'''
            SELECT
                COUNT(*) FILTER (WHERE batch_id IS NOT NULL AND batch_job_id IS NULL) AS orphaned,
                COUNT(*) FILTER (WHERE batch_job_id IS NOT NULL) AS linked
            FROM {schema}.marketplace_jobs
        '''))
        orphaned, linked = result.fetchone()
        print(f'{schema}: {orphaned} orphaned, {linked} linked')
"
```

**Expected output:** All orphaned counts should be 0.

---

## Rollback

If you need to rollback (before production deployment):

```sql
-- Restore from backup
psql -U postgres -d stoflow_db < backup_before_batch_migration_YYYYMMDD_HHMMSS.sql

-- Or manual rollback per schema
SET search_path TO user_1, public;

-- Unlink jobs from BatchJobs
UPDATE marketplace_jobs SET batch_job_id = NULL WHERE batch_job_id IS NOT NULL;

-- Delete BatchJobs
DELETE FROM batch_jobs;
```

---

## Troubleshooting

### "No module named 'sqlalchemy'"

You forgot to activate the virtual environment:
```bash
source venv/bin/activate
```

### "connection refused"

Database is not running:
```bash
docker-compose up -d
```

### "schema X does not exist"

Normal - migration will skip schemas that don't exist.

### Errors during migration

Check the logs for details. The script continues even if individual batches fail.

---

## Notes

- **Backward compatibility**: The old `batch_id` string field is preserved for 3 months
- **No downtime**: Migration can run while the app is running (reads are not affected)
- **Production timing**: Run during low-traffic hours for best performance
- **Multiple runs**: Safe to run multiple times - only processes unmigrated batches

---

*For questions or issues, check the logs or contact the development team.*
