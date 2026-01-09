"""
Security Helpers

Utilities for security checks and access control.

Defense-in-depth helpers for multi-tenant schema isolation.

Created: 2026-01-08
Author: Claude
"""

from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from shared.logging_setup import get_logger

logger = get_logger(__name__)


def verify_schema_isolation(db: Session, expected_user_id: int) -> bool:
    """
    Verify that the database session is using the correct user schema.

    Defense-in-depth check: Ensures that the session's search_path
    matches the expected user schema.

    Args:
        db: SQLAlchemy session
        expected_user_id: User ID that should own this session

    Returns:
        True if schema isolation is correct

    Raises:
        HTTPException: 500 if schema mismatch detected (security violation)
    """
    try:
        # Get current search_path
        result = db.execute(text("SHOW search_path")).fetchone()
        current_path = result[0] if result else ""

        expected_schema = f"user_{expected_user_id}"

        # Check if user schema is first in search_path
        if not current_path.startswith(expected_schema):
            logger.error(
                f"[SecurityViolation] Schema mismatch detected! "
                f"Expected: {expected_schema}, Got: {current_path}, "
                f"User ID: {expected_user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Security violation detected"
            )

        return True

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SecurityCheck] Failed to verify schema: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Security check failed"
        )


def ensure_resource_ownership(
    resource: Optional[object],
    resource_name: str,
    identifier: int | str,
    user_id: int
) -> object:
    """
    Ensure a resource exists and belongs to the current user.

    For models WITH user_id field: Checks user_id matches.
    For models WITHOUT user_id field: Relies on schema isolation (already verified by get_user_db).

    Args:
        resource: Database object (or None if not found)
        resource_name: Type of resource for error message (e.g., "Product", "Order")
        identifier: Resource identifier for error message
        user_id: Current user ID (for logging)

    Returns:
        The resource object if valid

    Raises:
        HTTPException: 404 if resource not found
        HTTPException: 403 if resource belongs to different user
    """
    if resource is None:
        logger.warning(
            f"[AccessDenied] {resource_name} {identifier} not found "
            f"(user_id: {user_id})"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_name} not found"
        )

    # If resource has user_id field, verify ownership
    if hasattr(resource, "user_id"):
        if resource.user_id != user_id:
            logger.error(
                f"[SecurityViolation] User {user_id} attempted to access "
                f"{resource_name} {identifier} owned by user {resource.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

    # Note: For resources without user_id, ownership is enforced by schema isolation
    # (the query wouldn't find the resource if it's in a different user's schema)

    return resource


def require_permission(user_role: str, required_roles: list[str]) -> bool:
    """
    Check if user has required role/permission.

    Args:
        user_role: Current user's role (e.g., "user", "admin")
        required_roles: List of allowed roles (e.g., ["admin", "moderator"])

    Returns:
        True if user has permission

    Raises:
        HTTPException: 403 if user lacks required permission
    """
    if user_role not in required_roles:
        logger.warning(
            f"[AccessDenied] User with role '{user_role}' attempted to access "
            f"resource requiring roles: {required_roles}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    return True


def is_admin(user_role: str) -> bool:
    """
    Check if user is admin.

    Args:
        user_role: User's role

    Returns:
        True if admin

    Raises:
        HTTPException: 403 if not admin
    """
    return require_permission(user_role, ["admin"])


# Usage examples:

# Schema isolation verification (optional defense-in-depth check):
# verify_schema_isolation(db, current_user.id)

# Resource ownership check:
# product = db.query(Product).filter(Product.id == product_id).first()
# ensure_resource_ownership(product, "Product", product_id, current_user.id)

# Permission check:
# require_permission(current_user.role, ["admin", "moderator"])
# is_admin(current_user.role)
