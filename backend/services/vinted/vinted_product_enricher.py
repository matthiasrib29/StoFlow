"""
Vinted Product Enricher - Enrichissement des produits via API item_upload

Service dedie a l'enrichissement des produits Vinted via l'API
/api/v2/item_upload/items/{id} pour recuperer les donnees completes.

UPDATED 2026-01-05:
- Remplace le parsing HTML par l'API item_upload (plus fiable)
- L'API retourne du JSON structure avec toutes les donnees

Author: Claude
Date: 2025-12-22 (refactored from vinted_api_sync.py)
Updated: 2026-01-05 (replaced HTML parsing with item_upload API)
"""

import asyncio
import json
import random
from typing import Any

from sqlalchemy.orm import Session

from models.user.marketplace_job import MarketplaceJob
from models.user.vinted_product import VintedProduct
from services.plugin_websocket_helper import PluginWebSocketHelper  # WebSocket architecture (2026-01-12)
from services.vinted.vinted_item_upload_parser import VintedItemUploadParser
from shared.logging_setup import get_logger
from shared.config import settings

logger = get_logger(__name__)


class VintedProductEnricher:
    """
    Service d'enrichissement des produits Vinted via API item_upload.

    Complete les donnees manquantes de l'API listing avec les informations
    de l'API /api/v2/item_upload/items/{id} (description, IDs, attributs).

    UPDATED 2026-01-05:
    Utilise maintenant l'API item_upload au lieu du parsing HTML.
    Plus fiable car retourne du JSON structure.
    """

    # API endpoint pattern for item_upload
    ITEM_UPLOAD_API = "/api/v2/item_upload/items/{vinted_id}"

    def __init__(self, user_id: int | None = None):
        """
        Initialize VintedProductEnricher.

        Args:
            user_id: ID utilisateur (requis pour WebSocket) (2026-01-12)
        """
        self.user_id = user_id
        self.parser = VintedItemUploadParser()

    async def enrich_products_without_description(
        self,
        db: Session,
        job: MarketplaceJob | None = None,
        batch_size: int = 15,           # Reduced from 30 to avoid DataDome 403
        batch_pause_min: float = 20.0,  # Increased from 10s
        batch_pause_max: float = 30.0   # Increased from 15s
    ) -> dict[str, Any]:
        """
        Enrichit les produits sans description via parsing HTML.

        Pour chaque produit sans description:
        1. Fetch la page HTML via le plugin
        2. Extrait TOUTES les donnees (description, IDs, dimensions, frais)
        3. Met a jour le produit en BDD

        Business Rules (UPDATED 2025-12-22):
        - Delai 2.5-4.5s entre requetes (gere cote plugin via execute_delay_ms)
        - Pause 20-30s tous les 15 produits (more conservative to avoid DataDome 403)
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

        # Helper pour mettre a jour le progress dans job.result_data (2026-01-14)
        def update_enrichment_progress():
            if job:
                # Initialiser result_data si None
                if job.result_data is None:
                    job.result_data = {}

                # Récupérer le compteur de sync (produits API importés)
                existing_progress = job.result_data.get("progress", {})
                sync_count = existing_progress.get("current", 0)

                # Ajouter les produits enrichis au compteur
                job.result_data = {
                    **job.result_data,
                    "progress": {
                        "current": sync_count + enriched,
                        "label": "produits enrichis"
                    }
                }
                try:
                    db.commit()
                    db.expire(job)  # Force refresh from DB
                except Exception as e:
                    logger.warning(f"Failed to update enrichment progress: {e}")
                    db.rollback()  # CRITICAL: Rollback to prevent idle transaction

        for i, product in enumerate(products_to_enrich):
            # CRITICAL: Check if job was cancelled (2026-01-14)
            if job:
                db.refresh(job)  # Get latest status from DB
                if job.status == 'cancelled':
                    logger.info(f"Job #{job.id} cancelled, stopping enrichment")
                    break

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

                    # Mettre a jour le progress apres chaque enrichissement (2026-01-14)
                    update_enrichment_progress()
            except Exception as e:
                errors += 1
                logger.error(
                    f"Erreur enrichissement {product.vinted_id}: {e}",
                    exc_info=True
                )
                db.rollback()
                # schema_translate_map survives rollback - no need to restore

        logger.info(f"Enrichissement termine: {enriched} enrichis, {errors} erreurs")

        return {"enriched": enriched, "errors": errors, "skipped": 0}

    async def _enrich_single_product(
        self,
        db: Session,
        product: VintedProduct
    ) -> bool:
        """
        Enrichit un seul produit via l'API item_upload.

        UPDATED 2026-01-05:
        Utilise /api/v2/item_upload/items/{id} au lieu du parsing HTML.
        Retourne du JSON structure, beaucoup plus fiable.

        Args:
            db: Session SQLAlchemy
            product: VintedProduct a enrichir

        Returns:
            bool: True si enrichi avec succes
        """
        if not product.vinted_id:
            return False

        try:
            # Build API path
            api_path = self.ITEM_UPLOAD_API.format(vinted_id=product.vinted_id)

            # WebSocket architecture (2026-01-12)
            result = await PluginWebSocketHelper.call_plugin_http(
                db=db,
                user_id=self.user_id,
                http_method="GET",
                path=api_path,
                timeout=settings.plugin_timeout_sync,
                description=f"Get item_upload for {product.vinted_id}"
            )

            logger.debug(
                f"API response for {product.vinted_id}: "
                f"keys={list(result.keys()) if isinstance(result, dict) else 'not dict'}"
            )

            if not result or not isinstance(result, dict):
                logger.warning(
                    f"Invalid API response for {product.vinted_id}: {type(result)}"
                )
                return False

            # Parse the API response
            extracted = VintedItemUploadParser.parse_item_response(result)

            if not extracted:
                logger.warning(f"Parsing failed for {product.vinted_id}")
                return False

            self._update_product_from_extracted(product, extracted)
            db.commit()

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
        Met a jour un VintedProduct avec les donnees de l'API item_upload.

        UPDATED 2026-01-05:
        Adapte pour le format JSON de l'API item_upload.

        Args:
            product: VintedProduct a mettre a jour
            extracted: Donnees parsees par VintedItemUploadParser
        """
        logger.debug(
            f"Product {product.vinted_id} extracted data: "
            f"description={'Yes' if extracted.get('description') else 'No'}, "
            f"color={extracted.get('color', 'No')}, "
            f"color1_id={extracted.get('color1_id', 'No')}, "
            f"brand={extracted.get('brand', 'No')}, "
            f"brand_id={extracted.get('brand_id', 'No')}"
        )

        # Description (prioritaire)
        if extracted.get('description'):
            product.description = extracted['description']

        # IDs Vinted - Brand
        if extracted.get('brand_id'):
            product.brand_id = extracted['brand_id']
        if extracted.get('brand') and not product.brand:
            product.brand = extracted['brand']

        # IDs Vinted - Size
        if extracted.get('size_id'):
            product.size_id = extracted['size_id']

        # IDs Vinted - Catalog/Category
        if extracted.get('catalog_id'):
            product.catalog_id = extracted['catalog_id']

        # IDs Vinted - Condition/Status
        if extracted.get('status_id'):
            product.status_id = extracted['status_id']
        if extracted.get('condition') and not product.condition:
            product.condition = extracted['condition']

        # Colors (NEW from item_upload API)
        if extracted.get('color1'):
            product.color1 = extracted['color1']
        if extracted.get('color1_id'):
            product.color1_id = extracted['color1_id']
        if extracted.get('color2'):
            product.color2 = extracted['color2']
        if extracted.get('color2_id'):
            product.color2_id = extracted['color2_id']

        # Dimensions
        if extracted.get('measurement_width'):
            product.measurement_width = extracted['measurement_width']
        if extracted.get('measurement_length'):
            product.measurement_length = extracted['measurement_length']
        if extracted.get('measurement_unit'):
            product.measurement_unit = extracted['measurement_unit']

        # NEW fields from item_upload API
        if 'is_unisex' in extracted:
            product.is_unisex = extracted['is_unisex']
        if extracted.get('manufacturer_labelling'):
            product.manufacturer_labelling = extracted['manufacturer_labelling']
        if extracted.get('item_attributes') is not None:
            product.item_attributes = extracted['item_attributes']

        # Status flags
        if 'is_draft' in extracted:
            product.is_draft = extracted['is_draft']

        # Photos
        if extracted.get('photos_data'):
            photos_list = extracted['photos_data']
            if photos_list:
                product.photos_data = json.dumps(photos_list)

        # URL
        if extracted.get('url') and not product.url:
            product.url = extracted['url']

        # Price (update if provided)
        if extracted.get('price'):
            product.price = extracted['price']
        if extracted.get('currency'):
            product.currency = extracted['currency']

