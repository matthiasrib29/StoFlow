"""
Structured Logging Helpers

Utilities for consistent, structured logging across the application.

Format: [module_name] action: key1=value1, key2=value2

Benefits:
- Consistent format across all modules
- Easily parsable by log aggregation tools (Datadog, Sentry)
- Structured context for debugging
- Performance metrics tracking

Created: 2026-01-08
Author: Claude
"""

from typing import Any, Optional
from shared.logging_setup import get_logger as _get_logger


class StructuredLogger:
    """
    Structured logger with consistent formatting.

    Usage:
        log = StructuredLogger("vinted_sync")
        log.info("sync_started", user_id=123, product_count=45)
        # Output: [vinted_sync] sync_started: user_id=123, product_count=45

        log.error("sync_failed", user_id=123, error=str(e), exc_info=True)
        # Output: [vinted_sync] sync_failed: user_id=123, error=Connection timeout
    """

    def __init__(self, module_name: str):
        """
        Initialize structured logger.

        Args:
            module_name: Module/component name (e.g., "vinted_sync", "ebay_import")
        """
        self.module_name = module_name
        self.logger = _get_logger(module_name)

    def _format_message(self, action: str, **context) -> str:
        """
        Format log message with structured context.

        Args:
            action: Action being performed (e.g., "sync_started", "product_created")
            **context: Key-value pairs for context

        Returns:
            Formatted message: "[module] action: key1=value1, key2=value2"
        """
        if not context:
            return f"[{self.module_name}] {action}"

        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        return f"[{self.module_name}] {action}: {context_str}"

    def debug(self, action: str, **context):
        """Log debug message with structured context."""
        self.logger.debug(self._format_message(action, **context))

    def info(self, action: str, **context):
        """Log info message with structured context."""
        self.logger.info(self._format_message(action, **context))

    def warning(self, action: str, **context):
        """Log warning message with structured context."""
        self.logger.warning(self._format_message(action, **context))

    def error(self, action: str, exc_info: bool = False, **context):
        """
        Log error message with structured context.

        Args:
            action: Action that failed
            exc_info: Include exception traceback (default False)
            **context: Key-value pairs for context
        """
        self.logger.error(self._format_message(action, **context), exc_info=exc_info)


# Convenience functions for common logging patterns

def log_operation_start(module: str, operation: str, **context):
    """
    Log operation start with timing capability.

    Usage:
        log_operation_start("vinted_sync", "sync_products", user_id=123)
    """
    log = StructuredLogger(module)
    log.info(f"{operation}_started", **context)


def log_operation_success(module: str, operation: str, duration_ms: Optional[float] = None, **context):
    """
    Log successful operation completion.

    Args:
        module: Module name
        operation: Operation name
        duration_ms: Optional duration in milliseconds
        **context: Additional context
    """
    log = StructuredLogger(module)
    if duration_ms:
        context["duration_ms"] = round(duration_ms, 2)
    log.info(f"{operation}_completed", **context)


def log_operation_failure(module: str, operation: str, error: Exception, **context):
    """
    Log failed operation with error details.

    Args:
        module: Module name
        operation: Operation name
        error: Exception that occurred
        **context: Additional context
    """
    log = StructuredLogger(module)
    context["error"] = str(error)
    context["error_type"] = error.__class__.__name__
    log.error(f"{operation}_failed", exc_info=True, **context)


# Example usage patterns:

# Basic usage:
# log = StructuredLogger("vinted_products")
# log.info("product_created", product_id=123, vinted_id=456)
# log.error("creation_failed", product_id=123, error="Invalid data", exc_info=True)

# Operation tracking:
# log_operation_start("vinted_sync", "sync_products", user_id=123)
# ... perform sync ...
# log_operation_success("vinted_sync", "sync_products", duration_ms=1234.56, synced_count=45)

# Error handling:
# try:
#     ... operation ...
# except Exception as e:
#     log_operation_failure("vinted_sync", "sync_products", e, user_id=123)
#     raise
