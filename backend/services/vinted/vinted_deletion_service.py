"""
Vinted Deletion Service - Service for deleting products from Vinted.

Handles:
- VintedProduct retrieval
- Deletion condition checking
- Archival (VintedDeletion table)
- Deletion via plugin
- Local VintedProduct deletion

This service extracts business logic from DeleteJobHandler to improve
separation of concerns and testability.

Author: Claude
Date: 2026-01-15
"""

import time
from typing import Any

from sqlalchemy.orm import Session

from models.user.vinted_product import VintedProduct
from models.vinted.vinted_deletion import VintedDeletion
from services.vinted.vinted_product_helpers import should_delete_product
from services.plugin_websocket_helper import PluginWebSocketHelper
from shared.vinted import VintedProductAPI
from shared.logging import get_logger

logger = get_logger(__name__)


class VintedDeletionService:
    """
    Service for deleting products from Vinted.

    Handles:
    - VintedProduct retrieval
    - Deletion condition checking
    - Archival (VintedDeletion table)
    - Deletion via plugin
    - Local VintedProduct deletion
    """

    def __init__(self, db: Session):
        """
        Initialize the deletion service.

        Args:
            db: SQLAlchemy session
        """
        self.db = db

    async def delete_product(
        self,
        product_id: int,
        user_id: int,
        shop_id: int | None = None,
        job_id: int | None = None,
        check_conditions: bool = True
    ) -> dict[str, Any]:
        """
        Deletes a product from Vinted.

        Args:
            product_id: Product ID to delete
            user_id: User ID for plugin communication
            shop_id: Optional shop ID
            job_id: Optional job ID
            check_conditions: Whether to check deletion conditions

        Returns:
            dict: {
                "success": bool,
                "product_id": int,
                "vinted_id": int | None,
                "error": str | None
            }
        """
        start_time = time.time()

        try:
            logger.info(f"Starting deletion for product #{product_id}")

            # 1. Retrieve VintedProduct
            vinted_product = self._get_vinted_product(product_id)

            # 2. Check conditions (optional)
            if check_conditions:
                if not should_delete_product(vinted_product):
                    logger.debug("Deletion conditions not met - Skipping deletion")
                    return {
                        "success": False,
                        "product_id": product_id,
                        "error": "Deletion conditions not met"
                    }

            # 3. Archive in VintedDeletion
            self._archive_deletion(vinted_product)

            # 4. Delete via plugin
            logger.debug("Deleting Vinted listing...")
            await self._call_plugin(
                user_id=user_id,
                job_id=job_id,
                http_method="POST",
                path=VintedProductAPI.delete(vinted_product.vinted_id),
                payload={},
                product_id=product_id,
                timeout=30,
                description="Delete Vinted product"
            )

            # 5. Delete local VintedProduct
            vinted_id = vinted_product.vinted_id
            self._delete_vinted_product(vinted_product)

            elapsed = time.time() - start_time
            logger.info(f"Product #{product_id} deleted successfully ({elapsed:.1f}s)")

            return {
                "success": True,
                "product_id": product_id,
                "vinted_id": vinted_id
            }

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"Deletion failed for product #{product_id}: {e} ({elapsed:.1f}s)",
                exc_info=True
            )
            self.db.rollback()
            return {"success": False, "product_id": product_id, "error": str(e)}

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    def _get_vinted_product(self, product_id: int) -> VintedProduct:
        """Retrieve VintedProduct."""
        vinted_product = self.db.query(VintedProduct).filter(
            VintedProduct.product_id == product_id
        ).first()

        if not vinted_product:
            raise ValueError(f"Product #{product_id} not found on Vinted")

        return vinted_product

    def _archive_deletion(self, vinted_product: VintedProduct):
        """Archive stats in VintedDeletion."""
        deletion = VintedDeletion.from_vinted_product(vinted_product)
        self.db.add(deletion)
        logger.debug(
            f"Archived: {vinted_product.view_count} views, "
            f"{vinted_product.favourite_count} favorites"
        )

    async def _call_plugin(
        self,
        user_id: int,
        job_id: int | None,
        http_method: str,
        path: str,
        payload: dict,
        product_id: int,
        timeout: int,
        description: str
    ) -> dict:
        """Call plugin via WebSocket helper."""
        result = await PluginWebSocketHelper.call_plugin(
            db=self.db,
            user_id=user_id,
            http_method=http_method,
            path=path,
            payload=payload,
            timeout=timeout,
            description=description,
        )
        return result

    def _delete_vinted_product(self, vinted_product: VintedProduct):
        """Delete local VintedProduct."""
        self.db.delete(vinted_product)
        self.db.commit()
