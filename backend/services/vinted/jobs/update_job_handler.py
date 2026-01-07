"""
Update Job Handler - Mise à jour de produits sur Vinted

Gère le workflow de mise à jour:
1. Récupération produit local et VintedProduct
2. Validation
3. Recalcul prix/titre/description
4. Mise à jour via plugin
5. Mise à jour VintedProduct local

Author: Claude
Date: 2025-12-19
"""

import time
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from models.user.product import Product
from models.user.vinted_product import VintedProduct
from models.user.marketplace_job import MarketplaceJob
from services.vinted.vinted_mapping_service import VintedMappingService
from services.vinted.vinted_pricing_service import VintedPricingService
from services.vinted.vinted_product_validator import VintedProductValidator
from services.vinted.vinted_title_service import VintedTitleService
from services.vinted.vinted_description_service import VintedDescriptionService
from services.vinted.vinted_product_converter import VintedProductConverter
from shared.vinted_constants import VintedProductAPI
from .base_job_handler import BaseJobHandler


class UpdateJobHandler(BaseJobHandler):
    """
    Handler pour la mise à jour de produits sur Vinted.

    Met à jour prix, titre, description et attributs d'un produit existant.
    """

    ACTION_CODE = "update"

    def __init__(
        self,
        db: Session,
        shop_id: int | None = None,
        job_id: int | None = None
    ):
        super().__init__(db, shop_id, job_id)
        self.mapping_service = VintedMappingService()
        self.pricing_service = VintedPricingService()
        self.validator = VintedProductValidator()
        self.title_service = VintedTitleService()
        self.description_service = VintedDescriptionService()

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Met à jour un produit sur Vinted.

        Args:
            job: MarketplaceJob contenant product_id

        Returns:
            dict: {"success": bool, "product_id": int, "error": str | None}
        """
        product_id = job.product_id
        if not product_id:
            return {"success": False, "error": "product_id required for update"}

        start_time = time.time()

        try:
            self.log_start(f"Mise à jour produit #{product_id}")

            # 1. Récupérer produit local
            product = self._get_product(product_id)

            # 2. Récupérer VintedProduct
            vinted_product = self._get_vinted_product(product_id)

            # 3. Valider pour update
            self._validate_product(product)

            # 4. Mapper attributs
            mapped_attrs = self._map_attributes(product)

            # 5. Calculer prix
            prix_vinted = self.pricing_service.calculate_vinted_price(product)

            # 6. Vérifier si prix identique -> skip optionnel
            prix_actuel = float(vinted_product.price) if vinted_product.price else 0.0
            if abs(prix_vinted - prix_actuel) < 0.01:
                self.log_debug(f"Prix identique ({prix_vinted}EUR)")
                # On continue quand même pour mettre à jour les autres champs

            # 7. Générer titre et description
            title = self.title_service.generate_title(product)
            description = self.description_service.generate_description(product)

            # 8. Construire payload
            payload = VintedProductConverter.build_update_payload(
                product=product,
                vinted_product=vinted_product,
                mapped_attrs=mapped_attrs,
                prix_vinted=prix_vinted,
                title=title,
                description=description
            )

            # 9. Mettre à jour via plugin
            self.log_debug(
                f"Mise à jour listing (prix: {prix_actuel}EUR -> {prix_vinted}EUR)..."
            )
            await self.call_plugin(
                http_method="PUT",
                path=VintedProductAPI.update(vinted_product.vinted_id),
                payload={"body": payload},
                product_id=product_id,
                timeout=60,
                description="Update produit Vinted"
            )

            # 10. Mettre à jour VintedProduct local
            self._update_vinted_product(vinted_product, prix_vinted, title)

            elapsed = time.time() - start_time
            self.log_success(f"Produit #{product_id} mis à jour ({elapsed:.1f}s)")

            return {
                "success": True,
                "product_id": product_id,
                "old_price": prix_actuel,
                "new_price": prix_vinted
            }

        except Exception as e:
            elapsed = time.time() - start_time
            self.log_error(f"Produit #{product_id}: {e} ({elapsed:.1f}s)", exc_info=True)
            self.db.rollback()
            return {"success": False, "product_id": product_id, "error": str(e)}

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    def _get_product(self, product_id: int) -> Product:
        """Récupère le produit local."""
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Produit #{product_id} introuvable")
        return product

    def _get_vinted_product(self, product_id: int) -> VintedProduct:
        """Récupère le VintedProduct existant."""
        vinted_product = self.db.query(VintedProduct).filter(
            VintedProduct.product_id == product_id
        ).first()

        if not vinted_product:
            raise ValueError(f"Produit #{product_id} non publié sur Vinted")

        if vinted_product.status != 'published':
            raise ValueError(
                f"Statut incorrect: {vinted_product.status} (attendu: published)"
            )

        return vinted_product

    def _validate_product(self, product: Product):
        """Valide le produit pour mise à jour."""
        is_valid, error = self.validator.validate_for_update(product)
        if not is_valid:
            raise ValueError(f"Validation échouée: {error}")

    def _map_attributes(self, product: Product) -> dict:
        """Mappe les attributs."""
        mapped_attrs = self.mapping_service.map_all_attributes(self.db, product)

        is_valid, error = self.validator.validate_mapped_attributes(
            mapped_attrs, product.id
        )
        if not is_valid:
            raise ValueError(f"Attributs invalides: {error}")

        return mapped_attrs

    def _update_vinted_product(
        self,
        vinted_product: VintedProduct,
        prix_vinted: float,
        title: str
    ):
        """Met à jour le VintedProduct local."""
        vinted_product.price = Decimal(str(prix_vinted))
        vinted_product.title = title
        self.db.commit()
