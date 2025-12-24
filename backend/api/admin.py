"""
Admin Routes

API routes for admin user management.
All routes require ADMIN role.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from api.dependencies import require_admin
from models.public.user import User, UserRole, SubscriptionTier
from schemas.admin_schemas import (
    AdminUserCreate,
    AdminUserUpdate,
    AdminUserResponse,
    AdminUserListResponse,
    AdminUserDeleteResponse,
)
from services.admin_audit_service import AdminAuditService
from services.admin_user_service import AdminUserService
from shared.database import get_db
from shared.logging_setup import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


def _user_to_response(user: User) -> AdminUserResponse:
    """Convert User model to AdminUserResponse schema."""
    return AdminUserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        subscription_tier=user.subscription_tier.value,
        subscription_status=user.subscription_status,
        business_name=user.business_name,
        account_type=user.account_type.value if user.account_type else None,
        phone=user.phone,
        country=user.country,
        language=user.language,
        email_verified=user.email_verified,
        failed_login_attempts=user.failed_login_attempts,
        locked_until=user.locked_until,
        last_login=user.last_login,
        current_products_count=user.current_products_count,
        current_platforms_count=user.current_platforms_count,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("/users", response_model=AdminUserListResponse)
def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    search: Optional[str] = Query(None, description="Search in email, name, or business name"),
    role: Optional[str] = Query(None, description="Filter by role (admin, user, support)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminUserListResponse:
    """
    List all users with pagination and filtering.

    Requires ADMIN role.

    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (1-100)
        search: Optional search term for email, name, or business name
        role: Optional role filter
        is_active: Optional active status filter

    Returns:
        Paginated list of users
    """
    # Convert role string to enum if provided
    role_enum = None
    if role:
        try:
            role_enum = UserRole(role.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}. Must be one of: admin, user, support"
            )

    users, total = AdminUserService.list_users(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        role=role_enum,
        is_active=is_active,
    )

    return AdminUserListResponse(
        users=[_user_to_response(u) for u in users],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/users/{user_id}", response_model=AdminUserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminUserResponse:
    """
    Get a specific user by ID.

    Requires ADMIN role.

    Args:
        user_id: ID of the user to retrieve

    Returns:
        User details

    Raises:
        HTTPException: 404 if user not found
    """
    user = AdminUserService.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    return _user_to_response(user)


@router.post("/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: AdminUserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminUserResponse:
    """
    Create a new user.

    Requires ADMIN role.
    Admin-created users have their email pre-verified.

    Args:
        user_data: User creation data

    Returns:
        Created user

    Raises:
        HTTPException: 400 if email already exists or invalid data
    """
    try:
        user = AdminUserService.create_user(
            db=db,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            role=UserRole(user_data.role),
            is_active=user_data.is_active,
            subscription_tier=SubscriptionTier(user_data.subscription_tier),
            business_name=user_data.business_name,
        )

        # Log audit
        AdminAuditService.log_action(
            db=db,
            admin=current_user,
            action=AdminAuditService.ACTION_CREATE,
            resource_type=AdminAuditService.RESOURCE_USER,
            resource_id=str(user.id),
            resource_name=user.email,
            details={
                "role": user_data.role,
                "subscription_tier": user_data.subscription_tier,
                "is_active": user_data.is_active,
            },
            request=request,
        )

        logger.info(f"Admin {current_user.email} created user {user.email}")
        return _user_to_response(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
def update_user(
    user_id: int,
    user_data: AdminUserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminUserResponse:
    """
    Update a user.

    Requires ADMIN role.

    Args:
        user_id: ID of the user to update
        user_data: Fields to update (all optional)

    Returns:
        Updated user

    Raises:
        HTTPException: 404 if user not found, 400 if invalid data
    """
    # Prevent self-demotion (admin cannot remove their own admin role)
    if user_id == current_user.id and user_data.role and user_data.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own admin role"
        )

    # Get user before update for audit
    user_before = AdminUserService.get_user(db, user_id)
    if not user_before:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

    try:
        user = AdminUserService.update_user(
            db=db,
            user_id=user_id,
            email=user_data.email,
            full_name=user_data.full_name,
            role=UserRole(user_data.role) if user_data.role else None,
            is_active=user_data.is_active,
            subscription_tier=SubscriptionTier(user_data.subscription_tier) if user_data.subscription_tier else None,
            business_name=user_data.business_name,
            password=user_data.password,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )

        # Build changed fields for audit
        changed = {}
        if user_data.email and user_data.email != user_before.email:
            changed["email"] = user_data.email
        if user_data.full_name and user_data.full_name != user_before.full_name:
            changed["full_name"] = user_data.full_name
        if user_data.role and user_data.role != user_before.role.value:
            changed["role"] = user_data.role
        if user_data.is_active is not None and user_data.is_active != user_before.is_active:
            changed["is_active"] = user_data.is_active
        if user_data.subscription_tier and user_data.subscription_tier != user_before.subscription_tier.value:
            changed["subscription_tier"] = user_data.subscription_tier
        if user_data.password:
            changed["password"] = "(changed)"

        # Log audit
        AdminAuditService.log_action(
            db=db,
            admin=current_user,
            action=AdminAuditService.ACTION_UPDATE,
            resource_type=AdminAuditService.RESOURCE_USER,
            resource_id=str(user_id),
            resource_name=user.email,
            details={"changed": changed} if changed else None,
            request=request,
        )

        logger.info(f"Admin {current_user.email} updated user {user_id}")
        return _user_to_response(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/users/{user_id}", response_model=AdminUserDeleteResponse)
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminUserDeleteResponse:
    """
    Delete a user (hard delete).

    Requires ADMIN role.
    This will permanently delete the user and their PostgreSQL schema.

    Args:
        user_id: ID of the user to delete

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: 404 if user not found, 400 if trying to delete self
    """
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    # Get user info before delete for audit
    user_before = AdminUserService.get_user(db, user_id)
    if not user_before:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

    user_email = user_before.email

    success = AdminUserService.delete_user(db, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

    # Log audit
    AdminAuditService.log_action(
        db=db,
        admin=current_user,
        action=AdminAuditService.ACTION_DELETE,
        resource_type=AdminAuditService.RESOURCE_USER,
        resource_id=str(user_id),
        resource_name=user_email,
        details={"hard_delete": True},
        request=request,
    )

    logger.info(f"Admin {current_user.email} deleted user {user_id}")
    return AdminUserDeleteResponse(
        success=True,
        message="User deleted successfully",
        user_id=user_id,
    )


@router.post("/users/{user_id}/toggle-active", response_model=AdminUserResponse)
def toggle_user_active(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminUserResponse:
    """
    Toggle a user's active status.

    Requires ADMIN role.

    Args:
        user_id: ID of the user

    Returns:
        Updated user

    Raises:
        HTTPException: 404 if user not found, 400 if trying to deactivate self
    """
    # Prevent self-deactivation
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )

    user = AdminUserService.toggle_active(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

    action_str = "activated" if user.is_active else "deactivated"

    # Log audit
    AdminAuditService.log_action(
        db=db,
        admin=current_user,
        action=AdminAuditService.ACTION_TOGGLE_ACTIVE,
        resource_type=AdminAuditService.RESOURCE_USER,
        resource_id=str(user_id),
        resource_name=user.email,
        details={"is_active": user.is_active},
        request=request,
    )

    logger.info(f"Admin {current_user.email} {action_str} user {user_id}")
    return _user_to_response(user)


@router.post("/users/{user_id}/unlock", response_model=AdminUserResponse)
def unlock_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminUserResponse:
    """
    Unlock a locked user account.

    Requires ADMIN role.
    Resets failed login attempts and removes lock.

    Args:
        user_id: ID of the user to unlock

    Returns:
        Updated user

    Raises:
        HTTPException: 404 if user not found
    """
    user = AdminUserService.unlock_user(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

    # Log audit
    AdminAuditService.log_action(
        db=db,
        admin=current_user,
        action=AdminAuditService.ACTION_UNLOCK,
        resource_type=AdminAuditService.RESOURCE_USER,
        resource_id=str(user_id),
        resource_name=user.email,
        details={"unlocked": True},
        request=request,
    )

    logger.info(f"Admin {current_user.email} unlocked user {user_id}")
    return _user_to_response(user)
