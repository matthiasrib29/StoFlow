"""
Orders Job Handler - Synchronisation des commandes Vinted

Délègue à VintedOrderSyncService pour:
- Récupération des transactions (toutes ou par mois)
- Parsing et sauvegarde des commandes
- Gestion des doublons

Usage:
- Sans paramètres: sync toutes les commandes récentes
- Avec year/month dans result_data: sync un mois spécifique
- Batch: créer plusieurs jobs avec différents mois

Author: Claude
Date: 2025-12-19
"""

import time
from typing import Any

from sqlalchemy.orm import Session

from models.user.vinted_job import VintedJob
from .base_job_handler import BaseJobHandler


class OrdersJobHandler(BaseJobHandler):
    """
    Handler pour la synchronisation des commandes Vinted.

    Modes de fonctionnement:
    - Sync globale: job.result_data = None ou {}
    - Sync par mois: job.result_data = {"year": 2025, "month": 12}

    Pour sync plusieurs mois, créer un batch de jobs avec différents mois.
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
            self._order_sync = VintedOrderSyncService()
        return self._order_sync

    async def execute(self, job: VintedJob) -> dict[str, Any]:
        """
        Synchronise les commandes depuis Vinted.

        Args:
            job: VintedJob avec result_data optionnel:
                - {} ou None: sync toutes les commandes récentes
                - {"year": int, "month": int}: sync un mois spécifique
                - {"duplicate_threshold": float}: seuil de doublons (défaut 0.8)

        Returns:
            dict: {
                "success": bool,
                "synced": int,
                "duplicates": int,
                "errors": int,
                "mode": "all" | "month",
                "error": str | None
            }
        """
        start_time = time.time()

        # Extraire paramètres du job
        params = job.result_data if isinstance(job.result_data, dict) else {}
        year = params.get('year')
        month = params.get('month')
        duplicate_threshold = params.get('duplicate_threshold', 0.8)
        per_page = params.get('per_page', 20)

        try:
            # Déterminer le mode
            if year and month:
                return await self._sync_by_month(year, month, start_time)
            else:
                return await self._sync_all(duplicate_threshold, per_page, start_time)

        except Exception as e:
            elapsed = time.time() - start_time
            self.log_error(f"Erreur sync commandes: {e} ({elapsed:.1f}s)", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _sync_all(
        self,
        duplicate_threshold: float,
        per_page: int,
        start_time: float
    ) -> dict[str, Any]:
        """Sync toutes les commandes récentes."""
        self.log_start("Synchronisation de toutes les commandes")

        result = await self.order_sync.sync_orders(
            self.db,
            duplicate_threshold=duplicate_threshold,
            per_page=per_page
        )

        elapsed = time.time() - start_time
        synced = result.get('synced', 0)
        duplicates = result.get('duplicates', 0)
        errors = result.get('errors', 0)

        self.log_success(
            f"{synced} commandes sync, {duplicates} doublons, "
            f"{errors} erreurs ({elapsed:.1f}s)"
        )

        return {
            "success": True,
            "mode": "all",
            "synced": synced,
            "duplicates": duplicates,
            "errors": errors,
            **result
        }

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
