"""
Logging Setup (Compatibility Layer)

This module provides backwards compatibility for imports from `shared.logging_setup`.
The actual implementation has been consolidated into `shared.logging`.

Usage:
    # Both imports work:
    from shared.logging import get_logger
    from shared.logging_setup import get_logger  # Deprecated but still works

Created: 2026-01-20 - Compatibility layer
"""

# Re-export available functions from shared.logging
from shared.logging import (
    setup_logging,
    get_logger,
    redact_email,
    redact_password,
    sanitize_for_log,
    StructuredLogger,
    log_operation_start,
    log_operation_success,
    log_operation_failure,
)

__all__ = [
    "setup_logging",
    "get_logger",
    "redact_email",
    "redact_password",
    "sanitize_for_log",
    "StructuredLogger",
    "log_operation_start",
    "log_operation_success",
    "log_operation_failure",
]
