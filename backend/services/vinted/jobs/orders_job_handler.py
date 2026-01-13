"""
Orders Job Handler - Synchronisation des commandes Vinted

Délègue à VintedOrderSyncService pour:
- Récupération des transactions via /my_orders ou /wallet/invoices
- Parsing et sauvegarde des commandes
- Gestion des doublons

Usage:
- Sans paramètres: sync via /my_orders (captures ALL orders)
- Avec year/month: sync via /wallet/invoices (wallet transactions only)

Note: sync_orders() (via /my_orders) est la méthode par défaut car
      /wallet/invoices ne capture pas les paiements par carte directe.

Author: Claude
Date: 2025-12-19
Updated: 2026-01-13 - sync_orders() par défaut, sync_orders_by_month optionnel
"""

import time
from typing import Any

from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob
from .base_job_handler import BaseJobHandler


class OrdersJobHandler(BaseJobHandler):
    """
    Handler pour la synchronisation des commandes Vinted.

    Modes de fonctionnement:
    - Sans paramètres: sync_orders() via /my_orders (ALL orders)
    - Avec year/month: sync_orders_by_month() via /wallet/invoices

    sync_orders() est la méthode par défaut car /wallet/invoices
    ne capture que les transactions wallet, pas les paiements carte.
    """

    ACTION_CODE = "orders"

    def __init__(
        self,
        db: Session,
        shop_id: int | None = None,
        job_id: int | None = None
    ):
        super().__init__(db, shop_id, job_id)
        self._order_sync = None

    @property
    def order_sync(self):
        """Lazy-load order sync service."""
        if self._order_sync is None:
            from services.vinted.vinted_order_sync import VintedOrderSyncService
            self._order_sync = VintedOrderSyncService(user_id=self.user_id)
        return self._order_sync

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Synchronise les commandes depuis Vinted.

        Args:
            job: MarketplaceJob avec result_data optionnel:
                - {} ou None: sync via /my_orders (DEFAULT - all orders)
                - {"year": int, "month": int}: sync via /wallet/invoices

        Returns:
            dict: {
                "success": bool,
                "synced": int,
                "duplicates": int,
                "errors": int,
                "mode": "classic" | "month",
                "error": str | None
            }
        """
        start_time = time.time()

        # Extraire paramètres du job
        params = job.result_data if isinstance(job.result_data, dict) else {}
        year = params.get('year')
        month = params.get('month')

        try:
            # With year+month: sync by month (wallet/invoices)
            if year and month:
                return await self._sync_by_month(year, month, start_time)

            # Default: sync all orders via /my_orders
            return await self._sync_all(start_time)

        except Exception as e:
            elapsed = time.time() - start_time
            self.log_error(f"Erreur sync commandes: {e} ({elapsed:.1f}s)", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _sync_by_month(
        self,
        year: int,
        month: int,
        start_time: float
    ) -> dict[str, Any]:
        """Sync les commandes d'un mois spécifique."""
        self.log_start(f"Synchronisation commandes {year}-{month:02d}")

        result = await self.order_sync.sync_orders_by_month(
            self.db, year, month
        )

        elapsed = time.time() - start_time
        synced = result.get('synced', 0)

        self.log_success(
            f"{synced} commandes {year}-{month:02d} ({elapsed:.1f}s)"
        )

        return {
            "success": True,
            "mode": "month",
            "year": year,
            "month": month,
            "synced": synced,
            **result
        }

    async def _sync_all(self, start_time: float) -> dict[str, Any]:
        """
        Sync all orders via /my_orders (default method).

        This captures ALL completed orders, including direct card payments.
        """
        self.log_start("Synchronisation commandes (via /my_orders)")

        result = await self.order_sync.sync_orders(self.db)

        elapsed = time.time() - start_time
        synced = result.get('synced', 0)

        self.log_success(f"{synced} commandes sync ({elapsed:.1f}s)")

        return {
            "success": True,
            "mode": "classic",
            "synced": synced,
            **result
        }
