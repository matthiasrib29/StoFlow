# Plan 03-03 Summary

## Execution

**Status**: Completed
**Duration**: 20 min
**Date**: 2026-01-13

## Changes Made

### Category A: Schedulers (3 files)

1. **services/marketplace/job_cleanup_scheduler.py**
   - Added `execution_options(schema_translate_map={"tenant": schema})` for ORM queries
   - Kept SET search_path for text() queries (table existence check)
   - Changed `JobCleanupService.cleanup_expired_jobs(db)` → `cleanup_expired_jobs(schema_db)`

2. **services/datadome_scheduler.py**
   - Added `execution_options(schema_translate_map={"tenant": schema})` in `get_connected_vinted_users()`
   - Replaced SET LOCAL with execution_options
   - Changed `db.query(VintedConnection)` → `schema_db.query(VintedConnection)`

3. **services/etsy_polling_cron.py**
   - Removed import: `from shared.database import set_user_schema`
   - Replaced `set_user_schema(db, user.id)` → `schema_db = db.execution_options(...)`
   - Removed `db.execute(text("SET search_path TO public"))` (reset not needed)

### Category B: API Files (2 files)

4. **api/products/ai.py**
   - Removed import: `from sqlalchemy import text`
   - Removed redundant SET search_path block (schema already configured via get_user_db)
   - Removed regex validation of schema_name (now handled upstream)

5. **api/ebay/products.py** (MAJOR - 15+ SET calls removed)
   - Added `execution_options` at start of background functions
   - Removed ALL redundant re-SET calls after commits/API calls
   - Functions modified:
     - `_run_enrichment_in_background()` - Added execution_options, kept one SET
     - `_update_job_progress()` - Removed SET call
     - `_enrich_products_parallel()` - Removed token refresh SET, commit SET
     - `_run_import_in_background()` - Added execution_options, removed ~8 SET calls

### Category C: Job Handler (1 file)

6. **services/ebay/jobs/ebay_orders_sync_job_handler.py**
   - Removed dynamic import of `set_user_schema`
   - Removed `set_user_schema(self.db, self.shop_id)` call (job processor already configures)

### Category D: Scripts (4 files)

7. **scripts/cleanup_abandoned_drafts.py**
   - Added `execution_options` at start of loop
   - Removed `db.execute(text("SET search_path TO public"))` at end

8. **scripts/migrate_existing_jobs_to_batch.py**
   - Added `execution_options` before SET in `migrate_schema()`

9. **scripts/migrate_oauth_tokens_encryption.py**
   - Replaced SET with `execution_options` in `migrate_ebay_tokens()`
   - Replaced SET with `execution_options` in `migrate_etsy_tokens()`

10. **scripts/migrate_from_pythonapiwoo.py**
    - Added `execution_options` before SET for target_session

## Commit

```
feat(03-03): migrate schedulers and scripts to schema_translate_map

Replace direct SET search_path SQL with schema_translate_map pattern
in schedulers, scripts, and remaining API files.

- Schedulers: job_cleanup, datadome, etsy_polling use execution_options
- API: Removed redundant SET calls in products/ai.py and ebay/products.py
- Handler: Removed set_user_schema in ebay_orders_sync_job_handler
- Scripts: Added execution_options to all migration scripts
```

## Verification

```bash
# Check for deprecated patterns
grep -r "set_user_schema\|set_user_search_path\|from shared.schema_utils import" backend/ --include="*.py"
# Result: No deprecated patterns in application code (only in shared/ where they're defined)
```

## Key Insight

### Pattern for Background Tasks
When creating own sessions in background tasks:
```python
schema_name = f"user_{user_id}"
db = SessionLocal()
db = db.execution_options(schema_translate_map={"tenant": schema_name})
# Also set search_path for text() queries if needed
db.execute(text(f"SET search_path TO {schema_name}, public"))
```

### Pattern for Schema Iteration
When iterating through all user schemas:
```python
for schema in get_all_user_schemas(db):
    schema_db = db.execution_options(schema_translate_map={"tenant": schema})
    # Use schema_db for ORM queries
    results = schema_db.query(Model).filter(...).all()
```

## Phase 3 Complete

All 3 plans in Phase 3 are now complete:
- 03-01: ✅ Removed set_user_search_path from API files
- 03-02: ✅ Removed schema_utils from services
- 03-03: ✅ Migrated schedulers, scripts & remaining files

## Next Phase

Phase 4: Nettoyage Code Legacy
- Remove deprecated functions from shared/database.py and shared/schema_utils.py

---
*Completed: 2026-01-13*
