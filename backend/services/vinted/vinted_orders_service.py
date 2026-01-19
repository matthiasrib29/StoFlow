"""
Vinted Orders Service - Service wrapper for order synchronization

Wraps VintedOrderSyncService to follow standard service pattern.

Author: Claude
Date: 2026-01-15
"""

from typing import Any
from sqlalchemy.orm import Session

from services.vinted.vinted_order_sync import VintedOrderSyncService


class VintedOrdersService:
    """
    Service for synchronizing orders from Vinted.

    Wraps VintedOrderSyncService to provide consistent interface
    with other Vinted services.
    """

    def __init__(self, db: Session):
        """
        Initialize orders service.

        Args:
            db: Database session
        """
        self.db = db

    async def sync_orders(
        self,
        shop_id: int,
        user_id: int,
        params: dict | None = None
    ) -> dict[str, Any]:
        """
        Synchronize orders from Vinted.

        Args:
            shop_id: Shop ID (unused, kept for signature compatibility)
            user_id: User ID
            params: Optional parameters:
                - year: int - Year for month-based sync
                - month: int - Month for month-based sync

        Returns:
            dict: {
                "success": bool,
                "orders_synced": int,
                "synced": int,
                "mode": "classic" | "month",
                "duplicates": int,
                "errors": int,
                "error": str | None
            }
        """
        try:
            order_sync = VintedOrderSyncService(user_id=user_id)
            params = params or {}

            # Extract year/month if provided
            year = params.get("year")
            month = params.get("month")

            # Sync by month if year+month provided
            if year and month:
                result = await order_sync.sync_orders_by_month(
                    self.db, year, month
                )
                return {
                    "success": True,
                    "orders_synced": result.get("synced", 0),
                    "mode": "month",
                    "year": year,
                    "month": month,
                    **result
                }

            # Default: sync all orders
            result = await order_sync.sync_orders(self.db)
            return {
                "success": True,
                "orders_synced": result.get("synced", 0),
                "mode": "classic",
                **result
            }

        except Exception as e:
            return {
                "success": False,
                "orders_synced": 0,
                "error": str(e)
            }
