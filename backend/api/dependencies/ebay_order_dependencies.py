"""
eBay Order Dependencies

Helpers and factories for eBay order routes.
"""

from typing import Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.user.ebay_order import EbayOrder


def get_order_stats(db: Session) -> dict:
    """
    Calculate global order statistics.

    Returns:
        Dict with total_revenue, pending_count, shipped_count
    """
    # Total revenue
    total_revenue = db.query(
        func.coalesce(func.sum(EbayOrder.total_price), 0)
    ).scalar() or 0

    # Pending count (NOT_STARTED + IN_PROGRESS)
    pending_count = db.query(EbayOrder).filter(
        EbayOrder.order_fulfillment_status.in_(["NOT_STARTED", "IN_PROGRESS"])
    ).count()

    # Shipped count (FULFILLED)
    shipped_count = db.query(EbayOrder).filter(
        EbayOrder.order_fulfillment_status == "FULFILLED"
    ).count()

    return {
        "total_revenue": float(total_revenue),
        "pending_count": pending_count,
        "shipped_count": shipped_count,
    }
