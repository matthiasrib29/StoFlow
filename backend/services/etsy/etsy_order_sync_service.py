"""
Etsy Order Sync Service (STUB)

Stub service for syncing individual orders from Etsy.

This service is currently not implemented. It serves as a placeholder
for the EtsyOrdersSyncJobHandler to work with DirectAPIJobHandler pattern.

Author: Claude
Date: 2026-01-15
Phase: 05-01 Etsy Handlers Refactoring
"""

from sqlalchemy.orm import Session


class EtsyOrderSyncService:
    """
    Service for syncing individual Etsy orders.

    NOTE: This is a STUB implementation. The actual sync logic needs to be
    implemented in a future phase.

    Current behavior: Returns not implemented error.

    Future implementation should:
    - Accept product_id to filter orders for that product
    - OR adapt to batch sync pattern with shop_id
    - Fetch orders from Etsy API
    - Update local orders in database
    - Handle conflicts and errors
    - Return standardized result dict
    """

    def __init__(self, db: Session):
        """
        Initialize Etsy order sync service.

        Args:
            db: SQLAlchemy session
        """
        self.db = db

    async def sync_orders(self, product_id: int) -> dict:
        """
        Sync orders for a product from Etsy (NOT IMPLEMENTED YET).

        Args:
            product_id: Local product ID to sync orders for

        Returns:
            dict: {
                "success": False,
                "error": "not implemented"
            }

        Future implementation should:
        1. Get product from DB
        2. Get etsy_listing_id from product
        3. Fetch orders for that listing from Etsy API
        4. Update orders in database
        5. Return success with synced_count

        Alternative: Adapt signature to match EtsyPollingService.sync_orders()
        which does batch sync without product_id parameter.
        """
        return {
            "success": False,
            "error": "EtsyOrderSyncService.sync_orders() not implemented yet. "
            "Use EtsyPollingService.sync_orders() for batch sync.",
        }
