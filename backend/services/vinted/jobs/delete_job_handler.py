"""
Delete Job Handler - Suppression de produits sur Vinted

Gère le workflow de suppression:
1. Récupération VintedProduct
2. Vérification des conditions (optionnel)
3. Archivage dans VintedDeletion
4. Suppression via plugin
5. Suppression VintedProduct local

Author: Claude
Date: 2025-12-19
"""

import time
from typing import Any

from sqlalchemy.orm import Session

from models.user.vinted_product import VintedProduct
from models.vinted.vinted_deletion import VintedDeletion
from models.user.vinted_job import VintedJob
from services.vinted.vinted_product_helpers import should_delete_product
from shared.vinted_constants import VintedProductAPI
from .base_job_handler import BaseJobHandler


class DeleteJobHandler(BaseJobHandler):
    """
    Handler pour la suppression de produits sur Vinted.

    Archive les stats avant suppression pour analyse future.
    """

    ACTION_CODE = "delete"

    async def execute(self, job: VintedJob) -> dict[str, Any]:
        """
        Supprime un produit sur Vinted.

        Args:
            job: VintedJob contenant product_id

        Returns:
            dict: {"success": bool, "product_id": int, "error": str | None}
        """
        product_id = job.product_id
        if not product_id:
            return {"success": False, "error": "product_id required for delete"}

        # Extraire check_conditions du job si présent
        check_conditions = True
        if job.result_data and isinstance(job.result_data, dict):
            check_conditions = job.result_data.get('check_conditions', True)

        start_time = time.time()

        try:
            self.log_start(f"Suppression produit #{product_id}")

            # 1. Récupérer VintedProduct
            vinted_product = self._get_vinted_product(product_id)

            # 2. Vérifier conditions (optionnel)
            if check_conditions:
                if not should_delete_product(vinted_product):
                    self.log_debug("Conditions non remplies - Skip suppression")
                    return {
                        "success": False,
                        "product_id": product_id,
                        "error": "Conditions de suppression non remplies"
                    }

            # 3. Archiver dans VintedDeletion
            self._archive_deletion(vinted_product)

            # 4. Supprimer via plugin
            self.log_debug("Suppression listing Vinted...")
            await self.call_plugin(
                http_method="POST",
                path=VintedProductAPI.delete(vinted_product.vinted_id),
                payload={},
                product_id=product_id,
                timeout=30,
                description="Suppression produit Vinted"
            )

            # 5. Supprimer VintedProduct local
            self._delete_vinted_product(vinted_product)

            elapsed = time.time() - start_time
            self.log_success(f"Produit #{product_id} supprimé ({elapsed:.1f}s)")

            return {
                "success": True,
                "product_id": product_id,
                "vinted_id": vinted_product.vinted_id
            }

        except Exception as e:
            elapsed = time.time() - start_time
            self.log_error(f"Produit #{product_id}: {e} ({elapsed:.1f}s)", exc_info=True)
            self.db.rollback()
            return {"success": False, "product_id": product_id, "error": str(e)}

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    def _get_vinted_product(self, product_id: int) -> VintedProduct:
        """Récupère le VintedProduct."""
        vinted_product = self.db.query(VintedProduct).filter(
            VintedProduct.product_id == product_id
        ).first()

        if not vinted_product:
            raise ValueError(f"Produit #{product_id} non trouvé sur Vinted")

        return vinted_product

    def _archive_deletion(self, vinted_product: VintedProduct):
        """Archive les stats dans VintedDeletion."""
        deletion = VintedDeletion.from_vinted_product(vinted_product)
        self.db.add(deletion)
        self.log_debug(
            f"Archivé: {vinted_product.view_count} vues, "
            f"{vinted_product.favourite_count} favoris"
        )

    def _delete_vinted_product(self, vinted_product: VintedProduct):
        """Supprime le VintedProduct local."""
        self.db.delete(vinted_product)
        self.db.commit()
