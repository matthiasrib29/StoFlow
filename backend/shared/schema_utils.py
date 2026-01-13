"""
Schema Utils - DEPRECATED (2026-01-13)

This entire module has been deprecated as part of the schema_translate_map migration.

Migration: SET LOCAL search_path → schema_translate_map
=======================================================

BEFORE (fragile - lost after COMMIT/ROLLBACK):
    db.execute(text(f"SET LOCAL search_path TO {schema}, public"))
    # ... do work ...
    db.commit()  # search_path LOST!
    restore_search_path(db, schema)  # Had to manually restore

AFTER (robust - survives COMMIT/ROLLBACK):
    db = db.execution_options(schema_translate_map={"tenant": schema})
    # ... do work ...
    db.commit()  # schema_translate_map PRESERVED!
    # No restoration needed

Removed Functions:
- get_current_schema() - No longer needed (schema persists in session)
- restore_search_path() - No longer needed (schema survives commit)
- restore_search_path_after_rollback() - No longer needed (schema survives rollback)
- commit_and_restore_path() - Just use db.commit() now
- SchemaManager class - No longer needed

See ROADMAP.md Phase 4 for details.

Author: Claude
Date: 2025-01-05 (original)
Deprecated: 2026-01-13
"""

# Raise ImportError with helpful message for any remaining imports
def __getattr__(name):
    raise ImportError(
        f"'{name}' has been removed from shared.schema_utils (2026-01-13). "
        f"Use execution_options(schema_translate_map={{'tenant': schema}}) instead. "
        f"See ROADMAP.md Phase 4 for migration details."
    )


__all__ = []  # Nothing to export
