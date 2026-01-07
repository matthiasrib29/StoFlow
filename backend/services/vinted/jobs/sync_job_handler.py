"""
Sync Job Handler - Synchronisation des produits depuis l'API Vinted

Délègue à VintedApiSyncService pour:
- Récupération des produits publiés sur Vinted
- Import dans la base locale
- Enrichissement des descriptions

Author: Claude
Date: 2025-12-19
"""

import time
from typing import Any

from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob
from .base_job_handler import BaseJobHandler


class SyncJobHandler(BaseJobHandler):
    """
    Handler pour la synchronisation des produits depuis l'API Vinted.

    Récupère les produits publiés sur Vinted et les importe localement.
    """

    ACTION_CODE = "sync"

    def __init__(
        self,
        db: Session,
        shop_id: int | None = None,
        job_id: int | None = None
    ):
        super().__init__(db, shop_id, job_id)
        self._api_sync = None

    @property
    def api_sync(self):
        """Lazy-load API sync service."""
        if self._api_sync is None:
            if not self.shop_id:
                raise ValueError("shop_id requis pour sync API")
            from services.vinted.vinted_api_sync import VintedApiSyncService
            self._api_sync = VintedApiSyncService(shop_id=self.shop_id)
        return self._api_sync

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Synchronise les produits depuis l'API Vinted.

        Args:
            job: MarketplaceJob (product_id non utilisé)

        Returns:
            dict: {
                "success": bool,
                "imported": int,
                "updated": int,
                "errors": int
            }
        """
        start_time = time.time()

        try:
            if not self.shop_id:
                return {"success": False, "error": "shop_id requis pour sync"}

            self.log_start(f"Synchronisation produits (shop_id={self.shop_id})")

            # Déléguer à VintedApiSyncService
            result = await self.api_sync.sync_products_from_api(self.db)

            elapsed = time.time() - start_time

            imported = result.get('imported', 0)
            updated = result.get('updated', 0)
            errors = result.get('errors', 0)

            self.log_success(
                f"{imported} importés, {updated} mis à jour, "
                f"{errors} erreurs ({elapsed:.1f}s)"
            )

            return {
                "success": True,
                "imported": imported,
                "updated": updated,
                "errors": errors,
                **result
            }

        except Exception as e:
            elapsed = time.time() - start_time
            self.log_error(f"Erreur sync: {e} ({elapsed:.1f}s)", exc_info=True)
            return {"success": False, "error": str(e)}


