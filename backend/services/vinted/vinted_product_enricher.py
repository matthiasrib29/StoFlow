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

from models.user.marketplace_job import JobStatus, MarketplaceJob
from shared.advisory_locks import AdvisoryLockHelper
from models.user.vinted_product import VintedProduct
from services.plugin_websocket_helper import (
    PluginWebSocketHelper,
    PluginHTTPError,
    # Generic result codes for plugin communication
    PLUGIN_SUCCESS,
    PLUGIN_NOT_FOUND,
    PLUGIN_FORBIDDEN,
    PLUGIN_UNAUTHORIZED,
    PLUGIN_DISCONNECTED,
    PLUGIN_TIMEOUT,
    PLUGIN_SERVER_ERROR,
    PLUGIN_ERROR,
)
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

    def _is_job_cancelled(self, db: Session, job_id: int) -> bool:
        """
        Check if job cancellation was signaled using advisory locks (2026-01-19).

        Primary check: Advisory lock (instant, non-blocking)
        Fallback: ORM query for cancel_requested flag

        Args:
            db: SQLAlchemy session
            job_id: Job ID to check

        Returns:
            True if job should stop
        """
        try:
            # Primary: Check advisory lock signal (instant, non-blocking)
            if AdvisoryLockHelper.is_cancel_signaled(db, job_id):
                return True

            # Fallback: Check cancel_requested flag via ORM (uses schema_translate_map)
            job = db.query(MarketplaceJob).filter(
                MarketplaceJob.id == job_id
            ).first()

            if job:
                return job.cancel_requested or job.status == JobStatus.CANCELLED
            return False
        except Exception as e:
            # If transaction is aborted, try to rollback and check again
            try:
                db.rollback()
                # After rollback, just check advisory lock (simplest)
                return AdvisoryLockHelper.is_cancel_signaled(db, job_id)
            except Exception:
                pass
            logger.warning(f"Error checking job cancellation: {e}")
            return False

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
        # Filter: products without description, excluding inactive products
        # (sold/deleted/hidden/closed products return 404 on item_upload API)
        products_to_enrich = db.query(VintedProduct).filter(
            VintedProduct.url.isnot(None),
            (VintedProduct.description.is_(None)) | (VintedProduct.description == ""),
            VintedProduct.status.notin_(['sold', 'deleted']),  # Skip sold/deleted
            VintedProduct.is_closed == False,   # Skip closed products
            VintedProduct.is_hidden == False    # Skip hidden products
        ).all()

        if not products_to_enrich:
            logger.info("Aucun produit a enrichir")
            return {"enriched": 0, "errors": 0, "skipped": 0}

        total = len(products_to_enrich)
        logger.info(f"Enrichissement de {total} produits via HTML")

        enriched = 0
        errors = 0
        not_found = 0      # Products sold/deleted on Vinted (404)
        forbidden = 0      # DataDome blocks (403)
        unauthorized = 0   # Session expired (401)
        disconnected = 0   # Plugin/WebSocket disconnected
        server_errors = 0  # Server errors (5xx like 524 Cloudflare timeout)

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
            # CRITICAL: Check if job was cancelled via advisory lock (2026-01-19)
            if job and self._is_job_cancelled(db, job.id):
                logger.info(f"Job #{job.id} cancel signal received, stopping enrichment")
                # Cleanup: commit enriched products before stopping
                db.commit()
                break

            if i > 0 and i % batch_size == 0:
                pause = random.uniform(batch_pause_min, batch_pause_max)
                logger.info(
                    f"  Pause de {pause:.1f}s apres {i} produits "
                    f"({enriched} enrichis, {errors} erreurs)"
                )
                await asyncio.sleep(pause)

            try:
                result = await self._enrich_single_product(db, product)

                # Handle result codes
                if result == PLUGIN_SUCCESS:
                    enriched += 1
                    logger.debug(
                        f"  [{i+1}/{total}] Enrichi: {product.vinted_id} - "
                        f"{product.title[:30] if product.title else 'N/A'}..."
                    )
                    # Mettre a jour le progress apres chaque enrichissement (2026-01-14)
                    update_enrichment_progress()

                elif result == PLUGIN_NOT_FOUND:
                    not_found += 1
                    logger.debug(
                        f"  [{i+1}/{total}] Not found (sold/deleted): {product.vinted_id}"
                    )

                elif result == PLUGIN_FORBIDDEN:
                    forbidden += 1
                    logger.warning(
                        f"  [{i+1}/{total}] Forbidden (DataDome?): {product.vinted_id}"
                    )
                    # Consider pausing if we get too many 403s (DataDome protection)
                    if forbidden >= 3:
                        logger.warning(
                            "Multiple 403 errors - possible DataDome block. Consider stopping."
                        )

                elif result == PLUGIN_UNAUTHORIZED:
                    unauthorized += 1
                    logger.warning(
                        f"  [{i+1}/{total}] Unauthorized (session expired): {product.vinted_id}"
                    )
                    # If session expired, stop the enrichment - user needs to re-auth
                    if unauthorized >= 2:
                        logger.error(
                            "Multiple 401 errors - Vinted session expired. Stopping enrichment."
                        )
                        break

                elif result == PLUGIN_DISCONNECTED:
                    disconnected += 1
                    logger.warning(
                        f"  [{i+1}/{total}] Disconnected: {product.vinted_id}"
                    )
                    # If disconnected, stop immediately - no point continuing
                    logger.error(
                        "Plugin/WebSocket disconnected. Stopping enrichment. "
                        "Please reconnect and try again."
                    )
                    break

                elif result == PLUGIN_SERVER_ERROR:
                    server_errors += 1
                    logger.warning(
                        f"  [{i+1}/{total}] Server error (5xx): {product.vinted_id} - retried but still failed"
                    )

                else:
                    # PLUGIN_ERROR, PLUGIN_TIMEOUT, etc.
                    errors += 1
                    logger.warning(
                        f"  [{i+1}/{total}] Error ({result}): {product.vinted_id}"
                    )

            except Exception as e:
                errors += 1
                logger.error(
                    f"Erreur enrichissement {product.vinted_id}: {e}",
                    exc_info=True
                )
                db.rollback()
                # schema_translate_map survives rollback - no need to restore

        logger.info(
            f"Enrichissement termine: {enriched} enrichis, {errors} erreurs, "
            f"{not_found} not_found, {forbidden} forbidden, {unauthorized} unauthorized, "
            f"{disconnected} disconnected, {server_errors} server_errors"
        )

        return {
            "enriched": enriched,
            "errors": errors,
            "skipped": 0,
            "not_found": not_found,         # Products sold/deleted on Vinted (404)
            "forbidden": forbidden,          # DataDome blocks (403)
            "unauthorized": unauthorized,    # Session expired (401)
            "disconnected": disconnected,    # Plugin/WebSocket disconnected
            "server_errors": server_errors   # Server errors (5xx like 524)
        }

    async def _enrich_single_product(
        self,
        db: Session,
        product: VintedProduct
    ) -> str:
        """
        Enrichit un seul produit via l'API item_upload.

        UPDATED 2026-01-05:
        Utilise /api/v2/item_upload/items/{id} au lieu du parsing HTML.
        Retourne du JSON structure, beaucoup plus fiable.

        UPDATED 2026-01-19:
        Returns specific status codes for different HTTP errors using
        centralized PLUGIN_* constants from plugin_websocket_helper.
        Server error retry (5xx) is now handled centrally in PluginWebSocketHelper.

        Args:
            db: Session SQLAlchemy
            product: VintedProduct a enrichir

        Returns:
            str: Result code (PLUGIN_SUCCESS, PLUGIN_NOT_FOUND, PLUGIN_FORBIDDEN, etc.)
        """
        if not product.vinted_id:
            return PLUGIN_ERROR

        try:
            # Fetch item data (retry for 5xx errors is handled in PluginWebSocketHelper)
            result = await self._fetch_item_upload(db, product)
            # Process and return
            return self._process_enrich_result(db, product, result)

        except PluginHTTPError as e:
            # Handle specific HTTP errors (4xx) - server errors (5xx) already handled above
            if e.is_not_found():
                logger.info(
                    f"Product {product.vinted_id} not found (404) - likely sold or deleted on Vinted"
                )
                # Mark product as sold/closed if we get 404
                product.is_closed = True
                db.commit()
                return PLUGIN_NOT_FOUND

            if e.is_forbidden():
                logger.warning(
                    f"Product {product.vinted_id} forbidden (403) - DataDome block or access denied"
                )
                return PLUGIN_FORBIDDEN

            if e.is_unauthorized():
                logger.warning(
                    f"Product {product.vinted_id} unauthorized (401) - Vinted session expired"
                )
                return PLUGIN_UNAUTHORIZED

            # Other HTTP errors - use the generic result code from exception
            logger.error(f"HTTP error for {product.vinted_id}: {e}")
            return e.get_result_code()

        except TimeoutError:
            logger.warning(f"Timeout pour {product.vinted_id}")
            return PLUGIN_TIMEOUT

        except RuntimeError as e:
            # Handle WebSocket disconnection
            error_msg = str(e).lower()
            if "not connected" in error_msg or "disconnected" in error_msg:
                logger.warning(
                    f"Product {product.vinted_id}: Plugin/WebSocket disconnected"
                )
                return PLUGIN_DISCONNECTED
            # Other RuntimeErrors - re-raise
            logger.error(
                f"Erreur enrichissement {product.vinted_id}: {e}",
                exc_info=True
            )
            raise

        except Exception as e:
            logger.error(
                f"Erreur enrichissement {product.vinted_id}: {e}",
                exc_info=True
            )
            raise

    async def _fetch_item_upload(
        self,
        db: Session,
        product: VintedProduct
    ) -> dict:
        """
        Fetch item_upload data from Vinted API via plugin.

        Args:
            db: SQLAlchemy session
            product: VintedProduct to fetch

        Returns:
            dict: API response data

        Raises:
            PluginHTTPError: On HTTP errors (4xx, 5xx)
            TimeoutError: On timeout
            RuntimeError: On WebSocket disconnection
        """
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

        return result

    def _process_enrich_result(
        self,
        db: Session,
        product: VintedProduct,
        result: dict
    ) -> str:
        """
        Process the API result and update the product.

        Args:
            db: SQLAlchemy session
            product: VintedProduct to update
            result: API response data

        Returns:
            str: Result code (PLUGIN_SUCCESS or PLUGIN_ERROR)
        """
        logger.debug(
            f"API response for {product.vinted_id}: "
            f"keys={list(result.keys()) if isinstance(result, dict) else 'not dict'}"
        )

        if not result or not isinstance(result, dict):
            logger.warning(
                f"Invalid API response for {product.vinted_id}: {type(result)}"
            )
            return PLUGIN_ERROR

        # Parse the API response
        extracted = VintedItemUploadParser.parse_item_response(result)

        if not extracted:
            logger.warning(f"Parsing failed for {product.vinted_id}")
            return PLUGIN_ERROR

        self._update_product_from_extracted(product, extracted)
        db.commit()

        return PLUGIN_SUCCESS

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

