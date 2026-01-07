"""
Publish Job Handler - Publication de produits sur Vinted

Gère le workflow complet de publication:
1. Validation du produit
2. Mapping des attributs
3. Calcul du prix
4. Génération titre/description
5. Upload des images
6. Création du listing Vinted
7. Sauvegarde VintedProduct

Author: Claude
Date: 2025-12-19
"""

import time
from typing import Any

from sqlalchemy.orm import Session

from models.user.product import Product, ProductStatus
from models.user.vinted_product import VintedProduct
from models.user.marketplace_job import MarketplaceJob
from services.vinted.vinted_mapping_service import VintedMappingService
from services.vinted.vinted_pricing_service import VintedPricingService
from services.vinted.vinted_product_validator import VintedProductValidator
from services.vinted.vinted_title_service import VintedTitleService
from services.vinted.vinted_description_service import VintedDescriptionService
from services.vinted.vinted_product_converter import VintedProductConverter
from services.vinted.vinted_product_helpers import (
    upload_product_images,
    save_new_vinted_product,
)
from shared.vinted_constants import VintedProductAPI
from .base_job_handler import BaseJobHandler


class PublishJobHandler(BaseJobHandler):
    """
    Handler pour la publication de produits sur Vinted.

    Workflow complet depuis le produit local jusqu'au listing Vinted.
    """

    ACTION_CODE = "publish"

    def __init__(
        self,
        db: Session,
        shop_id: int | None = None,
        job_id: int | None = None
    ):
        super().__init__(db, shop_id, job_id)
        # Services helpers
        self.mapping_service = VintedMappingService()
        self.pricing_service = VintedPricingService()
        self.validator = VintedProductValidator()
        self.title_service = VintedTitleService()
        self.description_service = VintedDescriptionService()

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Publie un produit sur Vinted.

        Args:
            job: MarketplaceJob contenant product_id

        Returns:
            dict: {
                "success": bool,
                "vinted_id": int | None,
                "url": str | None,
                "product_id": int,
                "error": str | None
            }
        """
        product_id = job.product_id
        if not product_id:
            return {"success": False, "error": "product_id required for publish"}

        start_time = time.time()

        try:
            self.log_start(f"Publication produit #{product_id}")

            # 1. Récupérer produit
            product = self._get_product(product_id)

            # 2. Vérifier si déjà publié
            self._check_not_already_published(product_id)

            # 3. Valider produit
            self._validate_product(product)

            # 4. Mapper attributs
            mapped_attrs = self._map_attributes(product)

            # 5. Calculer prix
            prix_vinted = self._calculate_price(product)

            # 6. Générer titre et description
            title = self.title_service.generate_title(product)
            description = self.description_service.generate_description(product)

            # 7. Upload photos
            photo_ids = await self._upload_images(product)

            # 8. Construire payload
            payload = VintedProductConverter.build_create_payload(
                product=product,
                photo_ids=photo_ids,
                mapped_attrs=mapped_attrs,
                prix_vinted=prix_vinted,
                title=title,
                description=description
            )

            # 9. Créer produit via plugin
            self.log_debug("Création listing Vinted...")
            result = await self.call_plugin(
                http_method="POST",
                path=VintedProductAPI.CREATE,
                payload={"body": payload},
                product_id=product_id,
                timeout=60,
                description="Création produit Vinted"
            )

            # 10. Extraire résultat
            item_data = result.get('item', result)
            vinted_id = item_data.get('id')
            vinted_url = item_data.get('url')

            if not vinted_id:
                raise ValueError("vinted_id manquant dans la réponse")

            # 11. Post-processing
            self._save_vinted_product(
                product_id, result, prix_vinted, photo_ids, title
            )
            self._update_product_status(product)

            elapsed = time.time() - start_time
            self.log_success(
                f"Produit #{product_id} -> vinted_id={vinted_id} ({elapsed:.1f}s)"
            )

            return {
                "success": True,
                "vinted_id": vinted_id,
                "url": vinted_url,
                "product_id": product_id,
                "price": prix_vinted
            }

        except Exception as e:
            elapsed = time.time() - start_time
            self.log_error(f"Produit #{product_id}: {e} ({elapsed:.1f}s)", exc_info=True)
            self.db.rollback()
            return {
                "success": False,
                "vinted_id": None,
                "url": None,
                "product_id": product_id,
                "error": str(e)
            }

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    def _get_product(self, product_id: int) -> Product:
        """Récupère le produit ou lève une exception."""
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Produit #{product_id} introuvable")

        self.log_debug(
            f"Produit: {product.title[:50] if product.title else 'Sans titre'}..."
        )
        return product

    def _check_not_already_published(self, product_id: int):
        """Vérifie que le produit n'est pas déjà publié."""
        existing = self.db.query(VintedProduct).filter(
            VintedProduct.product_id == product_id
        ).first()

        if existing:
            raise ValueError(
                f"Produit #{product_id} déjà publié sur Vinted "
                f"(vinted_id: {existing.vinted_id})"
            )

    def _validate_product(self, product: Product):
        """Valide le produit pour publication."""
        self.log_debug("Validation...")
        is_valid, error = self.validator.validate_for_creation(product)
        if not is_valid:
            raise ValueError(f"Validation échouée: {error}")

    def _map_attributes(self, product: Product) -> dict:
        """Mappe les attributs du produit vers Vinted."""
        self.log_debug("Mapping attributs...")
        mapped_attrs = self.mapping_service.map_all_attributes(self.db, product)

        is_valid, error = self.validator.validate_mapped_attributes(
            mapped_attrs, product.id
        )
        if not is_valid:
            raise ValueError(f"Attributs invalides: {error}")

        return mapped_attrs

    def _calculate_price(self, product: Product) -> float:
        """Calcule le prix Vinted."""
        self.log_debug("Calcul prix...")
        prix_vinted = self.pricing_service.calculate_vinted_price(product)
        self.log_debug(f"Prix: {prix_vinted}EUR")
        return prix_vinted

    async def _upload_images(self, product: Product) -> list[int]:
        """Upload les images sur Vinted."""
        self.log_debug("Upload photos...")
        photo_ids = await upload_product_images(
            self.db, product, job_id=self.job_id
        )

        is_valid, error = self.validator.validate_images(photo_ids)
        if not is_valid:
            raise ValueError(f"Images invalides: {error}")

        self.log_debug(f"{len(photo_ids)} photos uploadées")
        return photo_ids

    def _save_vinted_product(
        self,
        product_id: int,
        response_data: dict,
        prix_vinted: float,
        photo_ids: list[int],
        title: str
    ):
        """Sauvegarde le VintedProduct après création."""
        self.log_debug("Post-processing...")
        save_new_vinted_product(
            db=self.db,
            product_id=product_id,
            response_data=response_data,
            prix_vinted=prix_vinted,
            image_ids=photo_ids,
            title=title
        )

    def _update_product_status(self, product: Product):
        """Met à jour le statut du produit local."""
        product.status = ProductStatus.PUBLISHED
        self.db.commit()
