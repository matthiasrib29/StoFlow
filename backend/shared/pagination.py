"""
Pagination Helpers

Utilities for consistent pagination across all API endpoints.

Pattern: page-based pagination (1-indexed) with complete metadata.

Created: 2026-01-08
Author: Claude
"""

from typing import Generic, TypeVar
from pydantic import BaseModel, Field


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
