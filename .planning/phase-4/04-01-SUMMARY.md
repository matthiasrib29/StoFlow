# Plan 04-01 Summary

## Execution

**Status**: Completed
**Duration**: 10 min
**Date**: 2026-01-13

## Changes Made

### 1. api/ebay_oauth.py

**In `ebay_callback()` function:**
- Removed: `from shared.database import set_search_path_safe`
- Removed: `set_search_path_safe(db, user_id)`
- Added: `db = db.execution_options(schema_translate_map={"tenant": f"user_{user_id}"})`

### 2. services/ebay/ebay_oauth_service.py

**Removed import:**
- `from shared.database import set_search_path_safe`

**In `fetch_and_save_account_info()`:**
- Replaced `set_search_path_safe(db, user_id)` with `execution_options`

**In `process_oauth_callback()`:**
- Replaced `set_search_path_safe(db, user_id)` with `execution_options`
- Updated comment about `fetch_and_save_account_info`

### 3. shared/database.py

**Removed deprecated functions:**
- `set_search_path_safe()` (lines 176-200)
- `set_user_schema()` (lines 203-230)
- `set_user_search_path()` (lines 233-270)

**Added comment block explaining removal:**
```python
# REMOVED (2026-01-13): Deprecated functions removed as part of schema_translate_map migration
# - set_search_path_safe() - Use execution_options(schema_translate_map={"tenant": schema}) instead
# - set_user_schema() - Use execution_options(schema_translate_map={"tenant": schema}) instead
# - set_user_search_path() - Use execution_options(schema_translate_map={"tenant": schema}) instead
# See ROADMAP.md Phase 4 for details
```

### 4. shared/schema_utils.py

**Entire module deprecated:**
- Replaced entire file with deprecation notice and helpful error message
- `__getattr__` raises ImportError with migration instructions
- No functions exported (`__all__ = []`)

**Removed functions:**
- `get_current_schema()`
- `restore_search_path()`
- `restore_search_path_after_rollback()`
- `commit_and_restore_path()`
- `SchemaManager` class

## Commit

```
b1ddf80 feat(04-01): remove deprecated SET search_path functions

Phase 4 of schema_translate_map migration - cleanup legacy code.

Changes:
- Remove set_search_path_safe(), set_user_schema(), set_user_search_path()
  from shared/database.py
- Deprecate shared/schema_utils.py (all functions removed, helpful error
  message on import)
- Migrate api/ebay_oauth.py and services/ebay/ebay_oauth_service.py to
  use execution_options(schema_translate_map={"tenant": schema}) instead
```

## Verification

```bash
# Verified no application code uses deprecated functions
grep -r "set_user_schema\|set_user_search_path\|set_search_path_safe" backend/ --include="*.py" | grep -v "tests/" | grep -v "shared/"
# Result: No matches (only tests and comments remain)
```

## Remaining SET search_path Usages (Acceptable)

| Location | Reason |
|----------|--------|
| tests/* | Phase 5 will update |
| scripts/* | One-time migration scripts, use dual pattern |
| migrations/* | Alembic needs SET for autogenerate |
| api/ebay/products.py | Background tasks need both patterns for text() |

## Key Insight

**Dual pattern for background tasks that create own sessions:**
```python
schema_name = f"user_{user_id}"
db = SessionLocal()
# For ORM queries (models with schema="tenant")
db = db.execution_options(schema_translate_map={"tenant": schema_name})
# For text() queries (still need SET)
db.execute(text(f"SET search_path TO {schema_name}, public"))
```

## Phase 4 Complete

Plan 04-01 was the only plan in Phase 4.

## Next Phase

Phase 5: Tests & Validation
- Update tests that import deprecated functions
- Add new tests for schema_translate_map behavior
- Verify isolation after COMMIT/ROLLBACK

---
*Completed: 2026-01-13*
