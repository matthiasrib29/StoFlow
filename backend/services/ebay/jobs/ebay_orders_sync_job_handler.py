"""
eBay Orders Sync Job Handler - Synchronisation des commandes eBay

Délègue à EbayOrderSyncService pour:
- Récupération des commandes depuis eBay Fulfillment API
- Import/update dans la base locale

Author: Claude
Date: 2026-01-07
"""

import time
from typing import Any

from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class EbayOrdersSyncJobHandler:
    """
    Handler pour la synchronisation des commandes eBay.

    Récupère les commandes depuis l'API eBay Fulfillment et les importe localement.
    """

    ACTION_CODE = "sync_orders"

    def __init__(
        self,
        db: Session,
        shop_id: int | None = None,
        job_id: int | None = None
    ):
        """
        Initialize the handler.

        Args:
            db: SQLAlchemy session (user schema)
            shop_id: User ID (for multi-tenant context)
            job_id: Parent job ID for tracking
        """
        self.db = db
        self.shop_id = shop_id
        self.job_id = job_id

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Synchronise les commandes depuis l'API eBay.

        Args:
            job: MarketplaceJob with input_data: {hours: 24, status_filter: None}

        Returns:
            dict: {
                "success": bool,
                "created": int,
                "updated": int,
                "skipped": int,
                "errors": int,
                "total_fetched": int
            }
        """
        start_time = time.time()

        try:
            if not self.shop_id:
                return {"success": False, "error": "shop_id requis pour sync"}

            # Extract params from job input_data
            hours = job.input_data.get("hours", 24) if job.input_data else 24
            status_filter = job.input_data.get("status_filter") if job.input_data else None

            logger.info(
                f"[{self.ACTION_CODE.upper()}] Synchronisation commandes eBay "
                f"(shop_id={self.shop_id}, hours={hours}, status={status_filter})"
            )

            # Note: schema already configured via schema_translate_map in job processor

            # Delegate to existing EbayOrderSyncService
            from services.ebay.ebay_order_sync_service import EbayOrderSyncService
            sync_service = EbayOrderSyncService(self.db, self.shop_id)

            stats = sync_service.sync_orders(
                modified_since_hours=hours,
                status_filter=status_filter
            )

            elapsed = time.time() - start_time

            created = stats.get("created", 0)
            updated = stats.get("updated", 0)
            errors = stats.get("errors", 0)

            logger.info(
                f"[{self.ACTION_CODE.upper()}] ✓ {created} créées, {updated} mises à jour, "
                f"{errors} erreurs ({elapsed:.1f}s)"
            )

            return {
                "success": True,
                "created": created,
                "updated": updated,
                "skipped": stats.get("skipped", 0),
                "errors": errors,
                "total_fetched": stats.get("total_fetched", 0),
                "details": stats.get("details", [])
            }

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"[{self.ACTION_CODE.upper()}] ✗ Erreur sync: {e} ({elapsed:.1f}s)",
                exc_info=True
            )
            return {"success": False, "error": str(e)}
