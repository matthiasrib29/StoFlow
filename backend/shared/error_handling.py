"""
Error Handling Utilities

Helpers for consistent error handling across API endpoints.

Pattern: Let exceptions bubble up to global handlers (middleware/error_handler.py)
Only catch when specific business logic is needed (e.g., rollback, transform).

Created: 2026-01-08
Author: Claude
"""

from functools import wraps
from typing import Callable
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from shared.logging_setup import get_logger

logger = get_logger(__name__)


def with_rollback(db: Session):
    """
    Decorator to automatically rollback database on exceptions.

    Usage:
        @with_rollback(db)
        def some_operation():
            db.add(item)
            # If exception occurs, db will be rolled back

    Note: For routes, prefer letting exceptions bubble up.
          This is mainly for service layer methods.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                db.rollback()
                logger.error(f"[{func.__name__}] Exception occurred, rolled back: {e}", exc_info=True)
                raise
        return wrapper
    return decorator


def business_error(message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> HTTPException:
    """
    Create HTTPException for business logic errors.

    Args:
        message: User-facing error message
        status_code: HTTP status code (default 400 Bad Request)

    Returns:
        HTTPException ready to be raised

    Usage:
        if not item:
            raise business_error("Item not found", status.HTTP_404_NOT_FOUND)
    """
    return HTTPException(status_code=status_code, detail=message)


def not_found(resource: str, identifier: int | str) -> HTTPException:
    """
    Create 404 Not Found exception with consistent message format.

    Args:
        resource: Type of resource (e.g., "Product", "User", "Order")
        identifier: ID or identifier of the resource

    Returns:
        HTTPException with 404 status

    Usage:
        if not product:
            raise not_found("Product", product_id)
    """
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource} #{identifier} not found"
    )


def forbidden(message: str = "Access forbidden") -> HTTPException:
    """
    Create 403 Forbidden exception.

    Args:
        message: Reason for forbidden access

    Returns:
        HTTPException with 403 status
    """
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=message
    )


def bad_request(message: str) -> HTTPException:
    """
    Create 400 Bad Request exception.

    Args:
        message: Validation or business rule error

    Returns:
        HTTPException with 400 status
    """
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message
    )


def internal_error(message: str = "Internal server error occurred") -> HTTPException:
    """
    Create 500 Internal Server Error exception.

    Note: Prefer letting exceptions bubble up to global handler.
          Only use when you need to catch and transform specific errors.

    Args:
        message: Error description (will be logged)

    Returns:
        HTTPException with 500 status
    """
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=message
    )


# Exception handling guidelines:
#
# ✅ DO:
# - Let HTTPException bubble up (don't catch)
# - Let generic Exception bubble up to global handler
# - Catch specific exceptions for business logic (ValueError -> 400)
# - Use db.rollback() only when needed
# - Log errors with context before raising
#
# ❌ DON'T:
# - Catch HTTPException just to re-raise it
# - Catch Exception just to wrap in HTTPException(500)
# - Use bare except: clauses
# - Expose internal error details to clients
