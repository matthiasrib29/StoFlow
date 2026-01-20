"""
Admin Stats API

Endpoints for admin dashboard statistics.
All endpoints require admin authentication.
"""

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.dependencies import require_admin, get_db
from models.public.user import User
from schemas.admin_schemas import (
    AdminStatsOverview,
    AdminStatsSubscriptions,
    AdminStatsRegistrations,
    AdminStatsRecentActivity,
)
from services.admin_stats_service import AdminStatsService
from shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin/stats", tags=["Admin Stats"])


@router.get(
    "/overview",
    response_model=AdminStatsOverview,
    summary="Get overview statistics",
    description="Get total users, active/inactive counts, locked accounts, and role distribution.",
)
def get_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminStatsOverview:
    """
    Get overview statistics for admin dashboard.

    Requires admin role.
    """
    logger.info(f"Admin {current_user.email} requested stats overview")
    stats = AdminStatsService.get_overview(db)
    return AdminStatsOverview(**stats)


@router.get(
    "/subscriptions",
    response_model=AdminStatsSubscriptions,
    summary="Get subscription statistics",
    description="Get user distribution by subscription tier and estimated MRR.",
)
def get_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminStatsSubscriptions:
    """
    Get subscription statistics.

    Requires admin role.
    """
    logger.info(f"Admin {current_user.email} requested subscription stats")
    stats = AdminStatsService.get_subscriptions(db)
    return AdminStatsSubscriptions(**stats)


@router.get(
    "/registrations",
    response_model=AdminStatsRegistrations,
    summary="Get registration statistics",
    description="Get daily registration counts for graphs (week, month, or 3 months).",
)
def get_registrations(
    period: Literal["week", "month", "3months"] = Query(
        default="month",
        description="Time period: 'week' (7 days), 'month' (30 days), or '3months' (90 days)",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminStatsRegistrations:
    """
    Get registration statistics for a period.

    Requires admin role.
    """
    logger.info(f"Admin {current_user.email} requested registration stats (period={period})")
    stats = AdminStatsService.get_registrations(db, period=period)
    return AdminStatsRegistrations(**stats)


@router.get(
    "/recent-activity",
    response_model=AdminStatsRecentActivity,
    summary="Get recent activity",
    description="Get recent logins (last 24h) and new registrations (last 7 days).",
)
def get_recent_activity(
    limit: int = Query(default=10, ge=1, le=50, description="Maximum entries to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminStatsRecentActivity:
    """
    Get recent user activity.

    Requires admin role.
    """
    logger.info(f"Admin {current_user.email} requested recent activity (limit={limit})")
    stats = AdminStatsService.get_recent_activity(db, limit=limit)
    return AdminStatsRecentActivity(**stats)
