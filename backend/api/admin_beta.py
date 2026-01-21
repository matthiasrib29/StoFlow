"""
Admin Beta Routes

API routes for managing beta signups.
All routes require ADMIN role.

Note: This is a simplified version for the beta landing page.
Advanced features (discount revocation, conversion tracking) will be
enabled after the required database migration is applied.

Author: Claude
Date: 2026-01-20 (simplified 2026-01-21)
"""

import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.dependencies import require_admin
from models.beta_signup import BetaSignup
from models.public.user import User
from schemas.admin_beta_schemas import (
    BetaSignupListItem,
    BetaSignupListResponse,
    BetaSignupDetailResponse,
    BetaStatsResponse,
)
from services.beta_discount_service import BetaDiscountService
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
        description="Filter by status (pending, converted, cancelled)"
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
        valid_statuses = ["pending", "converted", "cancelled"]
        if status_filter not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}. Valid values: {', '.join(valid_statuses)}"
            )
        query = query.filter(BetaSignup.status == status_filter)

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

    # Convert to response (simplified - no user tracking columns)
    items = [
        BetaSignupListItem(
            id=s.id,
            email=s.email,
            name=s.name,
            vendor_type=s.vendor_type,
            monthly_volume=s.monthly_volume,
            status=s.status,
            user_id=None,  # Not available yet
            discount_applied_at=None,  # Not available yet
            discount_revoked_at=None,  # Not available yet
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

    # Simplified response - no user tracking data available yet
    return BetaSignupDetailResponse(
        id=signup.id,
        email=signup.email,
        name=signup.name,
        vendor_type=signup.vendor_type,
        monthly_volume=signup.monthly_volume,
        status=signup.status,
        user_id=None,  # Not available yet
        user_email=None,
        user_username=None,
        discount_applied_at=None,  # Not available yet
        discount_revoked_at=None,  # Not available yet
        revoked_by_username=None,
        revocation_reason=None,
        created_at=signup.created_at,
        updated_at=None,  # Not available yet
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


# ========================================
# ADVANCED FEATURES (disabled for now)
# ========================================
# The discount revocation endpoint requires additional database columns.
# It will be re-enabled after the migration is applied.
#
# @router.post("/signups/{signup_id}/revoke", response_model=RevokeDiscountResponse)
# def revoke_beta_discount(...):
#     ...
