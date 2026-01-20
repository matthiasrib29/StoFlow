"""
Route Utilities

Helpers and decorators for FastAPI routes.

Combines:
- Pagination utilities (page-based with metadata)
- Error handling decorators for routes

Created: 2026-01-08
Updated: 2026-01-20 - Consolidated from pagination.py, route_helpers.py
"""

from functools import wraps
from typing import Callable, Generic, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from shared.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# PAGINATION
# =============================================================================


# Generic type for paginated items
T = TypeVar("T")


class PaginationParams(BaseModel):
    """
    Standard pagination parameters for list endpoints.

    Usage:
        @router.get("/items")
        def list_items(pagination: PaginationParams = Depends()):
            offset = (pagination.page - 1) * pagination.page_size
            items = query.offset(offset).limit(pagination.page_size).all()
            return create_paginated_response(items, total, pagination)
    """

    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page (max 100)")

    def get_offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size

    def get_limit(self) -> int:
        """Get limit for database query (alias for clarity)."""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standard paginated response with metadata.

    Generic type T represents the item type.

    Example:
        PaginatedResponse[ProductResponse](
            items=[...],
            total=100,
            page=1,
            page_size=20,
            total_pages=5
        )
    """

    items: list[T] = Field(..., description="List of items for current page")
    total: int = Field(..., description="Total number of items across all pages")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")


def create_paginated_response(
    items: list[T],
    total: int,
    pagination: PaginationParams,
) -> PaginatedResponse[T]:
    """
    Helper function to create paginated response with calculated metadata.

    Args:
        items: List of items for current page
        total: Total count of items across all pages
        pagination: Pagination parameters used for the query

    Returns:
        PaginatedResponse with complete metadata
    """
    total_pages = (total + pagination.page_size - 1) // pagination.page_size

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


def calculate_total_pages(total: int, page_size: int) -> int:
    """
    Calculate total number of pages.

    Args:
        total: Total number of items
        page_size: Items per page

    Returns:
        Total pages (minimum 1 if total > 0, else 0)
    """
    if total == 0:
        return 0
    return (total + page_size - 1) // page_size


# =============================================================================
# ERROR HANDLING DECORATORS
# =============================================================================


def handle_service_errors(func: Callable) -> Callable:
    """
    Decorator to handle common service exceptions in async routes.

    Automatically converts:
    - ValueError with "not found" -> 404 Not Found
    - ValueError -> 400 Bad Request
    - RuntimeError -> 500 Internal Server Error
    - HTTPException -> re-raised as-is
    - Other Exception -> 500 Internal Server Error

    Usage:
        @router.get("/items/{id}")
        @handle_service_errors
        async def get_item(item_id: int, service: ItemService = Depends(get_service)):
            return service.get_item(item_id)

    Args:
        func: Async route function to wrap

    Returns:
        Wrapped function with exception handling
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            error_msg = str(e).lower()
            if "not found" in error_msg:
                logger.warning(f"[{func.__name__}] Not found: {e}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e)
                )
            logger.warning(f"[{func.__name__}] Validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except RuntimeError as e:
            logger.error(f"[{func.__name__}] Runtime error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except HTTPException:
            # Let HTTP exceptions pass through unchanged
            raise
        except Exception as e:
            logger.error(f"[{func.__name__}] Unexpected error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal error: {str(e)}"
            )

    return wrapper


def handle_service_errors_sync(func: Callable) -> Callable:
    """
    Decorator to handle common service exceptions in sync routes.

    Same behavior as handle_service_errors but for synchronous functions.

    Usage:
        @router.get("/items")
        @handle_service_errors_sync
        def list_items(service: ItemService = Depends(get_service)):
            return service.list_items()
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            error_msg = str(e).lower()
            if "not found" in error_msg:
                logger.warning(f"[{func.__name__}] Not found: {e}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e)
                )
            logger.warning(f"[{func.__name__}] Validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except RuntimeError as e:
            logger.error(f"[{func.__name__}] Runtime error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[{func.__name__}] Unexpected error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal error: {str(e)}"
            )

    return wrapper


__all__ = [
    # Pagination
    "PaginationParams",
    "PaginatedResponse",
    "create_paginated_response",
    "calculate_total_pages",
    # Error handling
    "handle_service_errors",
    "handle_service_errors_sync",
]
