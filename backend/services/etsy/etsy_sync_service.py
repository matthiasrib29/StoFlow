"""
Etsy Sync Service (STUB)

Stub service for syncing individual products from Etsy.

This service is currently not implemented. It serves as a placeholder
for the EtsySyncJobHandler to work with DirectAPIJobHandler pattern.

Author: Claude
Date: 2026-01-15
Phase: 05-01 Etsy Handlers Refactoring
"""

from sqlalchemy.orm import Session


class EtsySyncService:
    """
    Service for syncing individual Etsy products.

    NOTE: This is a STUB implementation. The actual sync logic needs to be
    implemented in a future phase.

    Current behavior: Returns not implemented error.

    Future implementation should:
    - Fetch product data from Etsy API by listing_id
    - Update local product in database
    - Handle conflicts and errors
    - Return standardized result dict
    """

    def __init__(self, db: Session):
        """
        Initialize Etsy sync service.

        Args:
            db: SQLAlchemy session
        """
        self.db = db

    async def sync_product(self, product_id: int) -> dict:
        """
        Sync a single product from Etsy (NOT IMPLEMENTED YET).

        Args:
            product_id: Local product ID to sync

        Returns:
            dict: {
                "success": False,
                "error": "not implemented"
            }

        Future implementation should:
        1. Get product from DB
        2. Get etsy_listing_id from product
        3. Fetch listing data from Etsy API
        4. Update product in database
        5. Return success with updated_fields
        """
        return {
            "success": False,
            "error": "EtsySyncService.sync_product() not implemented yet. "
            "Use EtsyPollingService.sync_all_products() for batch sync.",
        }
