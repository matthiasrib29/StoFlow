"""
Schema Utils (Compatibility Layer)

This module provides backwards compatibility for imports from `shared.schema_utils`.
The actual implementation is in `shared.schema`.

Usage:
    # Both imports work:
    from shared.schema import configure_schema_translate_map
    from shared.schema_utils import configure_schema_translate_map  # Deprecated but still works

Created: 2026-01-20 - Compatibility layer
"""

# Re-export from shared.schema
from shared.schema import (
    configure_schema_translate_map,
)

__all__ = [
    "configure_schema_translate_map",
]
