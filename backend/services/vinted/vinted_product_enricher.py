"""
Vinted Product Enricher - Enrichissement des produits via HTML

Service dedie a l'enrichissement des produits Vinted via parsing
des pages HTML pour recuperer les donnees non disponibles dans l'API.

Author: Claude
Date: 2025-12-22 (refactored from vinted_api_sync.py)
"""

import asyncio
import json
import random
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from models.user.vinted_product import VintedProduct
from services.plugin_task_helper import create_and_wait, _commit_and_restore_path
from services.vinted.vinted_data_extractor import VintedDataExtractor
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class VintedProductEnricher:
    """
    Service d'enrichissement des produits Vinted via HTML parsing.

    Complete les donnees manquantes de l'API listing avec les informations
    extraites des pages HTML des produits (description, IDs, attributs).
    """

    def __init__(self):
        """Initialize VintedProductEnricher."""
        pass

    async def enrich_products_without_description(
        self,
        db: Session,
        batch_size: int = 30,
        batch_pause_min: float = 10.0,
        batch_pause_max: float = 15.0
    ) -> dict[str, Any]:
        """
        Enrichit les produits sans description via parsing HTML.

        Pour chaque produit sans description:
        1. Fetch la page HTML via le plugin
        2. Extrait TOUTES les donnees (description, IDs, dimensions, frais)
        3. Met a jour le produit en BDD

        Business Rules:
        - Delai 1-2s entre requetes (gere cote plugin)
        - Pause 10-15s tous les 30 produits
        - Traite TOUS les produits sans description
        - Commit apres chaque produit enrichi
        - Si erreur/timeout: skipper et continuer

        Args:
            db: Session SQLAlchemy
            batch_size: Nombre de produits avant pause longue
            batch_pause_min: Duree min pause entre batches
            batch_pause_max: Duree max pause entre batches

        Returns:
            dict: {"enriched": int, "errors": int, "skipped": int}
        """
        products_to_enrich = db.query(VintedProduct).filter(
            VintedProduct.url.isnot(None),
            (VintedProduct.description.is_(None)) | (VintedProduct.description == "")
        ).all()

        if not products_to_enrich:
            logger.info("Aucun produit a enrichir")
            return {"enriched": 0, "errors": 0, "skipped": 0}

        total = len(products_to_enrich)
        logger.info(f"Enrichissement de {total} produits via HTML")

        enriched = 0
        errors = 0

        for i, product in enumerate(products_to_enrich):
            if i > 0 and i % batch_size == 0:
                pause = random.uniform(batch_pause_min, batch_pause_max)
                logger.info(
                    f"  Pause de {pause:.1f}s apres {i} produits "
                    f"({enriched} enrichis, {errors} erreurs)"
                )
                await asyncio.sleep(pause)

            try:
                success = await self._enrich_single_product(db, product)
                if success:
                    enriched += 1
                    logger.debug(
                        f"  [{i+1}/{total}] Enrichi: {product.vinted_id} - "
                        f"{product.title[:30] if product.title else 'N/A'}..."
                    )
            except Exception as e:
                errors += 1
                logger.error(
                    f"Erreur enrichissement {product.vinted_id}: {e}",
                    exc_info=True
                )
                db.rollback()
                self._restore_search_path(db)

        logger.info(f"Enrichissement termine: {enriched} enrichis, {errors} erreurs")

        return {"enriched": enriched, "errors": errors, "skipped": 0}

    async def _enrich_single_product(
        self,
        db: Session,
        product: VintedProduct
    ) -> bool:
        """
        Enrichit un seul produit via HTML parsing.

        Args:
            db: Session SQLAlchemy
            product: VintedProduct a enrichir

        Returns:
            bool: True si enrichi avec succes
        """
        if not product.url:
            return False

        try:
            result = await create_and_wait(
                db,
                http_method="GET",
                path=product.url,
                timeout=30,
                rate_limit=False,
                description=f"Fetch HTML for {product.vinted_id}"
            )

            html = result.get("data", "") if isinstance(result, dict) else str(result)

            logger.debug(
                f"HTML recu pour {product.vinted_id}: {len(html)} chars, "
                f"starts with: {html[:200] if html else 'EMPTY'}"
            )

            if not html or len(html) < 1000:
                logger.warning(
                    f"HTML trop court pour {product.vinted_id}: "
                    f"{len(html) if html else 0} chars"
                )
                return False

            extracted = VintedDataExtractor.extract_product_from_html(html)

            if not extracted:
                logger.warning(f"Extraction echouee pour {product.vinted_id}")
                return False

            self._update_product_from_extracted(product, extracted)
            _commit_and_restore_path(db)

            return True

        except TimeoutError:
            logger.warning(f"Timeout pour {product.vinted_id}")
            return False
        except Exception as e:
            logger.error(
                f"Erreur enrichissement {product.vinted_id}: {e}",
                exc_info=True
            )
            raise

    def _update_product_from_extracted(
        self,
        product: VintedProduct,
        extracted: dict
    ) -> None:
        """
        Met a jour un VintedProduct avec les donnees extraites du HTML.

        Cette methode complete les donnees manquantes de l'API listing
        avec les donnees extraites de la page HTML du produit.

        Args:
            product: VintedProduct a mettre a jour
            extracted: Donnees extraites par VintedDataExtractor
        """
        logger.debug(
            f"Product {product.vinted_id} extracted data: "
            f"description={'Yes' if extracted.get('description') else 'No'}, "
            f"color={extracted.get('color', 'No')}, "
            f"material={extracted.get('material', 'No')}, "
            f"size={extracted.get('size_title', 'No')}, "
            f"condition={extracted.get('condition_title', 'No')}, "
            f"brand={extracted.get('brand_name', 'No')}"
        )

        # Description (prioritaire)
        if extracted.get('description'):
            product.description = extracted['description']

        # IDs Vinted
        if extracted.get('brand_id'):
            product.brand_id = extracted['brand_id']
        if extracted.get('brand_name') and not product.brand:
            product.brand = extracted['brand_name']

        if extracted.get('size_id'):
            product.size_id = extracted['size_id']
        if extracted.get('size_title') and not product.size:
            product.size = extracted['size_title']

        if extracted.get('catalog_id'):
            product.catalog_id = extracted['catalog_id']

        if extracted.get('condition_id'):
            product.condition_id = extracted['condition_id']
        if extracted.get('condition_title') and not product.condition:
            product.condition = extracted['condition_title']

        # Attributs supplementaires
        if extracted.get('color') and not product.color:
            product.color = extracted['color']

        if extracted.get('material'):
            product.material = extracted['material']

        if extracted.get('measurements'):
            product.measurements = extracted['measurements']
        if extracted.get('measurement_width'):
            product.measurement_width = extracted['measurement_width']
        if extracted.get('measurement_length'):
            product.measurement_length = extracted['measurement_length']

        if extracted.get('manufacturer_labelling'):
            product.manufacturer_labelling = extracted['manufacturer_labelling']

        # Frais
        if extracted.get('service_fee'):
            product.service_fee = extracted['service_fee']
        if extracted.get('buyer_protection_fee'):
            product.buyer_protection_fee = extracted['buyer_protection_fee']
        if extracted.get('shipping_price'):
            product.shipping_price = extracted['shipping_price']
        if extracted.get('total_item_price'):
            product.total_price = extracted['total_item_price']

        # Seller info
        if extracted.get('seller_id'):
            product.seller_id = extracted['seller_id']
        if extracted.get('seller_login'):
            product.seller_login = extracted['seller_login']

        # Status flags
        if 'is_reserved' in extracted:
            product.is_reserved = extracted['is_reserved']
        if 'is_hidden' in extracted:
            product.is_hidden = extracted['is_hidden']

        # Photos
        if extracted.get('photos'):
            photos_list = extracted['photos']
            if photos_list:
                if not product.photo_url and photos_list[0].get('url'):
                    product.photo_url = photos_list[0]['url']
                product.photos_data = json.dumps(photos_list)

        # Date de publication
        if extracted.get('published_at') and not product.published_at:
            product.published_at = extracted['published_at']

    def _restore_search_path(self, db: Session) -> None:
        """
        Restaure le search_path PostgreSQL apres rollback.

        CRITICAL: Gere le cas InFailedSqlTransaction
        - Apres rollback, la session peut etre dans un etat invalide
        - On doit terminer toute transaction via un rollback
        - Puis reconfigurer le search_path
        """
        try:
            try:
                db.rollback()
            except Exception:
                pass

            path_result = db.execute(text("SHOW search_path"))
            current_path = path_result.scalar()
            if current_path:
                for s in current_path.split(","):
                    s = s.strip().strip('"')
                    if s.startswith("user_"):
                        db.execute(text(f"SET LOCAL search_path TO {s}, public"))
                        break
        except Exception as e:
            logger.warning(f"Impossible de restaurer search_path: {e}")
