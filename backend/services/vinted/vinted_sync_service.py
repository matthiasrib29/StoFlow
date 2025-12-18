"""
Vinted Sync Service - Service principal de synchronisation Vinted

Orchestration des operations de publication, mise a jour et suppression
de produits sur Vinted via plugin browser.

Note: La synchronisation API et commandes sont deleguees a:
- VintedApiSyncService (vinted_api_sync.py)
- VintedOrderSyncService (vinted_order_sync.py)

Author: Claude
Date: 2025-12-17
"""

import time
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from models.user.product import Product, ProductStatus
from models.user.vinted_product import VintedProduct
from models.user.vinted_deletion import VintedDeletion
from services.plugin_task_helper import create_and_wait
from services.vinted.vinted_api_sync import VintedApiSyncService
from services.vinted.vinted_order_sync import VintedOrderSyncService
from services.vinted.vinted_mapping_service import VintedMappingService
from services.vinted.vinted_product_converter import VintedProductConverter
from services.vinted.vinted_pricing_service import VintedPricingService
from services.vinted.vinted_product_validator import VintedProductValidator
from services.vinted.vinted_title_service import VintedTitleService
from services.vinted.vinted_description_service import VintedDescriptionService
from services.vinted.vinted_product_helpers import (
    upload_product_images,
    save_new_vinted_product,
    should_delete_product,
)
from shared.vinted_constants import VintedProductAPI
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class VintedSyncService:
    """
    Service principal d'orchestration Vinted.

    Gere la publication, mise a jour et suppression de produits.
    Delegue la synchronisation API et commandes aux services dedies.

    Usage:
        service = VintedSyncService(shop_id=123)
        result = await service.publish_product(db, product_id=456)
    """

    def __init__(self, shop_id: int | None = None):
        """
        Initialize VintedSyncService.

        Args:
            shop_id: ID du shop Vinted (pour operations de sync)
        """
        self.shop_id = shop_id
        self.mapping_service = VintedMappingService()
        self.pricing_service = VintedPricingService()
        self.validator = VintedProductValidator()
        self.title_service = VintedTitleService()
        self.description_service = VintedDescriptionService()

        # Services delegues
        self._api_sync: VintedApiSyncService | None = None
        self._order_sync: VintedOrderSyncService | None = None

    @property
    def api_sync(self) -> VintedApiSyncService:
        """Lazy-load API sync service."""
        if self._api_sync is None:
            if not self.shop_id:
                raise ValueError("shop_id requis pour sync API")
            self._api_sync = VintedApiSyncService(shop_id=self.shop_id)
        return self._api_sync

    @property
    def order_sync(self) -> VintedOrderSyncService:
        """Lazy-load order sync service."""
        if self._order_sync is None:
            self._order_sync = VintedOrderSyncService()
        return self._order_sync

    # =========================================================================
    # PUBLICATION DE PRODUIT
    # =========================================================================

    async def publish_product(self, db: Session, product_id: int) -> dict[str, Any]:
        """
        Publie un produit sur Vinted avec workflow step-by-step via plugin.

        Args:
            db: Session SQLAlchemy (user schema)
            product_id: ID du produit a publier

        Returns:
            dict: {
                "success": bool,
                "vinted_id": int | None,
                "url": str | None,
                "product_id": int,
                "error": str | None
            }
        """
        start_time = time.time()

        try:
            logger.info(f"[PUBLISH] Debut publication produit #{product_id}")

            # 1. Recuperer produit
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise ValueError(f"Produit #{product_id} introuvable")

            logger.info(f"  Produit: {product.title[:50] if product.title else 'Sans titre'}...")

            # 2. Verifier si deja publie
            existing = db.query(VintedProduct).filter(
                VintedProduct.product_id == product_id
            ).first()
            if existing:
                raise ValueError(
                    f"Produit #{product_id} deja publie sur Vinted "
                    f"(vinted_id: {existing.vinted_id})"
                )

            # 3. Valider produit
            logger.info(f"  Validation...")
            is_valid, error = self.validator.validate_for_creation(product)
            if not is_valid:
                raise ValueError(f"Validation echouee: {error}")

            # 4. Mapper attributs
            logger.info(f"  Mapping attributs...")
            mapped_attrs = self.mapping_service.map_all_attributes(db, product)
            is_valid, error = self.validator.validate_mapped_attributes(
                mapped_attrs, product_id
            )
            if not is_valid:
                raise ValueError(f"Attributs invalides: {error}")

            # 5. Calculer prix
            logger.info(f"  Calcul prix...")
            prix_vinted = self.pricing_service.calculate_vinted_price(product)
            logger.info(f"  Prix: {prix_vinted}EUR")

            # 6. Generer titre et description
            title = self.title_service.generate_title(product)
            description = self.description_service.generate_description(product)

            # 7. Upload photos
            logger.info(f"  Upload photos...")
            photo_ids = await upload_product_images(db, product)
            is_valid, error = self.validator.validate_images(photo_ids)
            if not is_valid:
                raise ValueError(f"Images invalides: {error}")
            logger.info(f"  {len(photo_ids)} photos uploadees")

            # 8. Construire payload
            payload = VintedProductConverter.build_create_payload(
                product=product,
                photo_ids=photo_ids,
                mapped_attrs=mapped_attrs,
                prix_vinted=prix_vinted,
                title=title,
                description=description
            )

            # 9. Creer produit via plugin
            logger.info(f"  Creation listing Vinted...")
            result = await create_and_wait(
                db,
                http_method="POST",
                path=VintedProductAPI.CREATE,
                payload={"body": payload},
                platform="vinted",
                product_id=product_id,
                timeout=60,
                description="Creation produit Vinted"
            )

            # 10. Extraire resultat
            item_data = result.get('item', result)
            vinted_id = item_data.get('id')
            vinted_url = item_data.get('url')

            if not vinted_id:
                raise ValueError("vinted_id manquant dans la reponse")

            # 11. Post-processing: creer VintedProduct
            logger.info(f"  Post-processing...")
            save_new_vinted_product(
                db=db,
                product_id=product_id,
                response_data=result,
                prix_vinted=prix_vinted,
                image_ids=photo_ids,
                title=title
            )

            # Mettre a jour Product.status
            product.status = ProductStatus.PUBLISHED
            db.commit()

            elapsed = time.time() - start_time
            logger.info(
                f"[PUBLISH] Succes produit #{product_id} -> "
                f"vinted_id={vinted_id} ({elapsed:.1f}s)"
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
            logger.error(
                f"[PUBLISH] Erreur produit #{product_id}: {e} ({elapsed:.1f}s)",
                exc_info=True
            )
            db.rollback()
            return {
                "success": False,
                "vinted_id": None,
                "url": None,
                "product_id": product_id,
                "error": str(e)
            }

    # =========================================================================
    # MISE A JOUR DE PRODUIT
    # =========================================================================

    async def update_product(self, db: Session, product_id: int) -> dict[str, Any]:
        """
        Met a jour un produit Vinted existant.

        Args:
            db: Session SQLAlchemy
            product_id: ID du produit a mettre a jour

        Returns:
            dict: {"success": bool, "error": str | None}
        """
        start_time = time.time()

        try:
            logger.info(f"[UPDATE] Debut mise a jour produit #{product_id}")

            # 1. Recuperer produit local
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise ValueError(f"Produit #{product_id} introuvable")

            # 2. Recuperer VintedProduct
            vinted_product = db.query(VintedProduct).filter(
                VintedProduct.product_id == product_id
            ).first()
            if not vinted_product:
                raise ValueError(f"Produit #{product_id} non publie sur Vinted")

            if vinted_product.status != 'published':
                raise ValueError(
                    f"Statut incorrect: {vinted_product.status} (attendu: published)"
                )

            # 3. Valider pour update
            is_valid, error = self.validator.validate_for_update(product)
            if not is_valid:
                raise ValueError(f"Validation echouee: {error}")

            # 4. Mapper attributs
            mapped_attrs = self.mapping_service.map_all_attributes(db, product)
            is_valid, error = self.validator.validate_mapped_attributes(
                mapped_attrs, product_id
            )
            if not is_valid:
                raise ValueError(f"Attributs invalides: {error}")

            # 5. Calculer prix
            prix_vinted = self.pricing_service.calculate_vinted_price(product)

            # 6. Verifier si prix identique -> skip
            prix_actuel = float(vinted_product.price) if vinted_product.price else 0.0
            if abs(prix_vinted - prix_actuel) < 0.01:
                logger.debug(f"  Prix identique ({prix_vinted}EUR) - Skip update")
                return {"success": False, "error": "Prix identique, pas de mise a jour"}

            # 7. Generer titre et description
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

            # 9. Mettre a jour via plugin
            logger.info(
                f"  Mise a jour listing Vinted "
                f"(prix: {prix_actuel}EUR -> {prix_vinted}EUR)..."
            )
            await create_and_wait(
                db,
                http_method="PUT",
                path=VintedProductAPI.update(vinted_product.vinted_id),
                payload={"body": payload},
                platform="vinted",
                product_id=product_id,
                timeout=60,
                description="Update produit Vinted"
            )

            # 10. Mettre a jour VintedProduct local
            vinted_product.price = Decimal(str(prix_vinted))
            vinted_product.title = title
            db.commit()

            elapsed = time.time() - start_time
            logger.info(f"[UPDATE] Produit #{product_id} mis a jour ({elapsed:.1f}s)")

            return {"success": True, "product_id": product_id}

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"[UPDATE] Erreur produit #{product_id}: {e} ({elapsed:.1f}s)",
                exc_info=True
            )
            db.rollback()
            return {"success": False, "error": str(e)}

    # =========================================================================
    # SUPPRESSION DE PRODUIT
    # =========================================================================

    async def delete_product(
        self,
        db: Session,
        product_id: int,
        check_conditions: bool = True
    ) -> dict[str, Any]:
        """
        Supprime un produit Vinted.

        Args:
            db: Session SQLAlchemy
            product_id: ID du produit a supprimer
            check_conditions: Si True, verifie les conditions avant suppression

        Returns:
            dict: {"success": bool, "error": str | None}
        """
        start_time = time.time()

        try:
            logger.info(f"[DELETE] Debut suppression produit #{product_id}")

            # 1. Recuperer VintedProduct
            vinted_product = db.query(VintedProduct).filter(
                VintedProduct.product_id == product_id
            ).first()
            if not vinted_product:
                raise ValueError(f"Produit #{product_id} non trouve sur Vinted")

            # 2. Verifier conditions (optionnel)
            if check_conditions:
                if not should_delete_product(vinted_product):
                    logger.debug(f"  Conditions non remplies - Skip suppression")
                    return {"success": False, "error": "Conditions non remplies"}

            # 3. Archiver dans VintedDeletion
            deletion = VintedDeletion.from_vinted_product(vinted_product)
            db.add(deletion)

            # 4. Supprimer via plugin
            logger.info(f"  Suppression listing Vinted...")
            await create_and_wait(
                db,
                http_method="POST",
                path=VintedProductAPI.delete(vinted_product.vinted_id),
                payload={},
                platform="vinted",
                product_id=product_id,
                timeout=30,
                description="Suppression produit Vinted"
            )

            # 5. Supprimer VintedProduct local
            db.delete(vinted_product)
            db.commit()

            elapsed = time.time() - start_time
            logger.info(f"[DELETE] Produit #{product_id} supprime ({elapsed:.1f}s)")

            return {"success": True, "product_id": product_id}

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"[DELETE] Erreur produit #{product_id}: {e} ({elapsed:.1f}s)",
                exc_info=True
            )
            db.rollback()
            return {"success": False, "error": str(e)}

    # =========================================================================
    # DELEGATION AUX SERVICES SPECIALISES
    # =========================================================================

    async def sync_products_from_api(self, db: Session) -> dict[str, Any]:
        """Delegue a VintedApiSyncService."""
        return await self.api_sync.sync_products_from_api(db)

    async def sync_orders(
        self,
        db: Session,
        duplicate_threshold: float = 0.8,
        per_page: int = 20
    ) -> dict[str, Any]:
        """Delegue a VintedOrderSyncService."""
        return await self.order_sync.sync_orders(db, duplicate_threshold, per_page)

    async def sync_orders_by_month(
        self,
        db: Session,
        year: int,
        month: int
    ) -> dict[str, Any]:
        """
        Synchronise les commandes d'un mois specifique.

        Delegue a VintedOrderSyncService.

        Args:
            db: Session SQLAlchemy
            year: Annee (ex: 2025)
            month: Mois (1-12)

        Returns:
            dict: Resultat de la sync
        """
        return await self.order_sync.sync_orders_by_month(db, year, month)
