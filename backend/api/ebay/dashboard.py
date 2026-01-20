"""
eBay Dashboard API Endpoints

Provides unified dashboard endpoints for eBay post-sale management:
- GET /statistics - Aggregated statistics from all domains
- GET /urgent - Items requiring urgent seller action
- GET /activity - Recent activity timeline

Created: 2026-01-14
Author: Claude
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.dependencies import get_user_db
from models.public import User
from schemas.ebay_dashboard_schemas import (
    ActivityItem,
    CancellationStatistics,
    DashboardStatisticsResponse,
    InquiryStatistics,
    PaymentDisputeStatistics,
    RecentActivityResponse,
    RefundStatistics,
    ReturnStatistics,
    TotalsStatistics,
    UrgentItem,
    UrgentItemsResponse,
)
from services.ebay.ebay_dashboard_service import EbayDashboardService
from shared.logging import setup_logging

logger = setup_logging()

router = APIRouter(prefix="/ebay/dashboard", tags=["eBay Dashboard"])


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/statistics", response_model=DashboardStatisticsResponse)
def get_dashboard_statistics(
    db_and_user: tuple[Session, User] = Depends(get_user_db),
) -> DashboardStatisticsResponse:
    """
    Get unified statistics across all eBay post-sale domains.

    Returns aggregated statistics for:
    - Returns: open, closed, needs_action, past_deadline
    - Cancellations: pending, closed, needs_action, past_due
    - Refunds: pending, completed, failed, total_refunded
    - Payment Disputes: open, action_needed, closed, total_disputed
    - INR Inquiries: open, closed, needs_action, past_deadline
    - Totals: open, needs_action, past_deadline (combined)
    """
    db, user = db_and_user
    logger.debug(f"Fetching dashboard statistics for user {user.id}")

    service = EbayDashboardService(db)
    stats = service.get_unified_statistics()

    return DashboardStatisticsResponse(
        returns=ReturnStatistics(**stats.get("returns", {})),
        cancellations=CancellationStatistics(**stats.get("cancellations", {})),
        refunds=RefundStatistics(**stats.get("refunds", {})),
        payment_disputes=PaymentDisputeStatistics(**stats.get("payment_disputes", {})),
        inquiries=InquiryStatistics(**stats.get("inquiries", {})),
        totals=TotalsStatistics(**stats.get("totals", {})),
        generated_at=datetime.fromisoformat(stats.get("generated_at", datetime.now(timezone.utc).isoformat())),
    )


@router.get("/urgent", response_model=UrgentItemsResponse)
def get_urgent_items(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of items per category",
    ),
    db_and_user: tuple[Session, User] = Depends(get_user_db),
) -> UrgentItemsResponse:
    """
    Get all items requiring urgent seller action.

    Returns urgent items grouped by domain type:
    - Returns needing action or past deadline
    - Cancellations needing response
    - Payment disputes needing action
    - INR inquiries needing response

    Items are marked with urgency level:
    - "critical": Past deadline or escalated
    - "high": Needs action but not past deadline
    """
    db, user = db_and_user
    logger.debug(f"Fetching urgent items for user {user.id} with limit={limit}")

    service = EbayDashboardService(db)
    urgent = service.get_urgent_items(limit=limit)

    return UrgentItemsResponse(
        returns=[UrgentItem(**item) for item in urgent.get("returns", [])],
        cancellations=[UrgentItem(**item) for item in urgent.get("cancellations", [])],
        payment_disputes=[UrgentItem(**item) for item in urgent.get("payment_disputes", [])],
        inquiries=[UrgentItem(**item) for item in urgent.get("inquiries", [])],
        total_count=urgent.get("total_count", 0),
        generated_at=datetime.fromisoformat(urgent.get("generated_at", datetime.now(timezone.utc).isoformat())),
    )


@router.get("/activity", response_model=RecentActivityResponse)
def get_recent_activity(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of recent items",
    ),
    db_and_user: tuple[Session, User] = Depends(get_user_db),
) -> RecentActivityResponse:
    """
    Get recent activity across all eBay post-sale domains.

    Returns a timeline of recent items sorted by most recent first.
    Includes returns, cancellations, refunds, payment disputes, and INR inquiries.
    """
    db, user = db_and_user
    logger.debug(f"Fetching recent activity for user {user.id} with limit={limit}")

    service = EbayDashboardService(db)
    activities = service.get_recent_activity(limit=limit)

    return RecentActivityResponse(
        items=[ActivityItem(**item) for item in activities],
        total_count=len(activities),
    )
