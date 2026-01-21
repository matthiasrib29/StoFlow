"""
Admin Beta Routes

API routes for managing beta signups and discounts.
All routes require ADMIN role.

Author: Claude
Date: 2026-01-20
"""

import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.dependencies import require_admin
from models.beta_signup import BetaSignup, BetaSignupStatus
from models.public.user import User
from schemas.admin_beta_schemas import (
    BetaSignupListItem,
    BetaSignupListResponse,
    BetaSignupDetailResponse,
    BetaStatsResponse,
    RevokeDiscountRequest,
    RevokeDiscountResponse,
)
from services.beta_discount_service import BetaDiscountService, BetaDiscountError
from shared.database import get_db
from shared.logging_setup import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin/beta", tags=["Admin Beta"])


@router.get("/signups", response_model=BetaSignupListResponse)
def list_beta_signups(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by status (pending, converted, revoked, cancelled)"
    ),
    search: Optional[str] = Query(None, description="Search by email or name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    List all beta signups with pagination and filtering.

    Requires ADMIN role.

    Args:
        skip: Number of records to skip (pagination)
        limit: Max number of records to return
        status_filter: Optional filter by status
        search: Optional search by email or name
        db: Database session
        current_user: Authenticated admin user

    Returns:
        Paginated list of beta signups
    """
    query = db.query(BetaSignup)

    # Apply status filter
    if status_filter:
        try:
            status_enum = BetaSignupStatus(status_filter)
            query = query.filter(BetaSignup.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}. Valid values: pending, converted, revoked, cancelled"
            )

    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (BetaSignup.email.ilike(search_pattern)) |
            (BetaSignup.name.ilike(search_pattern))
        )

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    signups = query.order_by(BetaSignup.created_at.desc()).offset(skip).limit(limit).all()

    # Calculate pagination info
    page = (skip // limit) + 1 if limit > 0 else 1
    total_pages = math.ceil(total / limit) if limit > 0 else 1

    # Convert to response
    items = [
        BetaSignupListItem(
            id=s.id,
            email=s.email,
            name=s.name,
            vendor_type=s.vendor_type,
            monthly_volume=s.monthly_volume,
            status=s.status.value,
            user_id=s.user_id,
            discount_applied_at=s.discount_applied_at,
            discount_revoked_at=s.discount_revoked_at,
            created_at=s.created_at,
        )
        for s in signups
    ]

    return BetaSignupListResponse(
        items=items,
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages,
    )


@router.get("/signups/{signup_id}", response_model=BetaSignupDetailResponse)
def get_beta_signup(
    signup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Get detailed information about a specific beta signup.

    Requires ADMIN role.

    Args:
        signup_id: ID of the beta signup
        db: Database session
        current_user: Authenticated admin user

    Returns:
        Detailed beta signup information
    """
    signup = db.query(BetaSignup).filter(BetaSignup.id == signup_id).first()

    if not signup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Beta signup {signup_id} not found"
        )

    # Get related user info if converted
    user_email = None
    user_username = None
    if signup.user_id:
        user = db.query(User).filter(User.id == signup.user_id).first()
        if user:
            user_email = user.email
            user_username = user.username

    # Get revoking admin info
    revoked_by_username = None
    if signup.discount_revoked_by:
        admin = db.query(User).filter(User.id == signup.discount_revoked_by).first()
        if admin:
            revoked_by_username = admin.username

    return BetaSignupDetailResponse(
        id=signup.id,
        email=signup.email,
        name=signup.name,
        vendor_type=signup.vendor_type,
        monthly_volume=signup.monthly_volume,
        status=signup.status.value,
        user_id=signup.user_id,
        user_email=user_email,
        user_username=user_username,
        discount_applied_at=signup.discount_applied_at,
        discount_revoked_at=signup.discount_revoked_at,
        revoked_by_username=revoked_by_username,
        revocation_reason=signup.revocation_reason,
        created_at=signup.created_at,
        updated_at=signup.updated_at,
    )


@router.post("/signups/{signup_id}/revoke", response_model=RevokeDiscountResponse)
def revoke_beta_discount(
    signup_id: int,
    request: RevokeDiscountRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Revoke the beta discount for a specific signup.

    This will:
    1. Update the beta_signup status to REVOKED
    2. Remove the coupon from the user's Stripe subscription (if active)

    Requires ADMIN role.

    Args:
        signup_id: ID of the beta signup to revoke
        request: Revocation request with reason
        db: Database session
        current_user: Authenticated admin user

    Returns:
        Confirmation of revocation
    """
    try:
        signup = BetaDiscountService.revoke_discount(
            db=db,
            beta_signup_id=signup_id,
            admin_id=current_user.id,
            reason=request.reason,
        )

        logger.info(
            f"Admin {current_user.id} ({current_user.email}) revoked beta discount "
            f"for signup {signup_id}: {request.reason}"
        )

        return RevokeDiscountResponse(
            success=True,
            message=f"Beta discount revoked for {signup.email}",
            beta_signup_id=signup.id,
            revoked_at=signup.discount_revoked_at,
        )

    except BetaDiscountError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/stats", response_model=BetaStatsResponse)
def get_beta_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Get statistics about the beta program.

    Requires ADMIN role.

    Args:
        db: Database session
        current_user: Authenticated admin user

    Returns:
        Beta program statistics
    """
    stats = BetaDiscountService.get_beta_stats(db)

    return BetaStatsResponse(**stats)
