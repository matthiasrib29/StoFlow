"""
Timing and performance monitoring utilities

Provides decorators and context managers for measuring operation duration
and logging performance metrics in a centralized way.
"""

import logging
import time
from functools import wraps
from contextlib import contextmanager
from typing import Any, Callable, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def timed_operation(
    operation_name: str,
    level: str = 'info',
    threshold_ms: Optional[float] = None,
    include_args: bool = False
):
    """
    Decorator to automatically log the duration of an operation.

    Logs timing information in a structured format for monitoring and debugging.
    If duration exceeds threshold_ms, logs at 'warning' level regardless of `level`.

    Args:
        operation_name: Name of the operation for logging
        level: Logging level ('debug', 'info', 'warning', 'error')
        threshold_ms: If set, log warning if duration exceeds this milliseconds
        include_args: Include function arguments in logs (useful for debugging)

    Example:
        @timed_operation("product_creation", threshold_ms=1000)
        def create_product(db, product_data):
            # Long operation
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            start_datetime = datetime.utcnow()
            func_name = f"{func.__module__}.{func.__name__}"

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                # Determine log level based on threshold
                log_level = level
                if threshold_ms and duration_ms > threshold_ms:
                    log_level = 'warning'

                log_func = getattr(logger, log_level)

                log_data = {
                    'operation': operation_name,
                    'function': func_name,
                    'duration_ms': round(duration_ms, 2),
                    'status': 'success',
                    'timestamp': start_datetime.isoformat()
                }

                if include_args:
                    log_data['args_count'] = len(args)
                    log_data['kwargs_count'] = len(kwargs)

                log_func(
                    f"Operation '{operation_name}' completed",
                    extra=log_data
                )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                logger.error(
                    f"Operation '{operation_name}' failed after {duration_ms:.2f}ms",
                    extra={
                        'operation': operation_name,
                        'function': func_name,
                        'duration_ms': round(duration_ms, 2),
                        'status': 'error',
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'timestamp': start_datetime.isoformat()
                    },
                    exc_info=True
                )
                raise

        return wrapper

    return decorator


@contextmanager
def measure_operation(operation_name: str, level: str = 'info', threshold_ms: Optional[float] = None):
    """
    Context manager to measure the duration of a code block.

    Useful for timing code blocks that can't be decorated (loops, async operations, etc.)

    Args:
        operation_name: Name of the operation for logging
        level: Logging level for success
        threshold_ms: If set, log warning if duration exceeds this milliseconds

    Example:
        with measure_operation("database_query", threshold_ms=500):
            results = db.query(...)
    """
    start_time = time.time()
    start_datetime = datetime.utcnow()

    try:
        yield
        duration_ms = (time.time() - start_time) * 1000

        log_level = level
        if threshold_ms and duration_ms > threshold_ms:
            log_level = 'warning'

        log_func = getattr(logger, log_level)

        log_func(
            f"Operation '{operation_name}' completed",
            extra={
                'operation': operation_name,
                'duration_ms': round(duration_ms, 2),
                'status': 'success',
                'timestamp': start_datetime.isoformat()
            }
        )

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            f"Operation '{operation_name}' failed after {duration_ms:.2f}ms",
            extra={
                'operation': operation_name,
                'duration_ms': round(duration_ms, 2),
                'status': 'error',
                'error_type': type(e).__name__,
                'error_message': str(e),
                'timestamp': start_datetime.isoformat()
            },
            exc_info=True
        )
        raise


def get_duration_ms(start_time: float) -> float:
    """Calculate duration in milliseconds from a start time."""
    return (time.time() - start_time) * 1000
