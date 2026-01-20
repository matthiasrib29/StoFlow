"""
Vinted API Sync Service - Synchronisation depuis l'API Vinted

Service dedie a la synchronisation des produits depuis l'API Vinted
vers la base de donnees locale.

=============================================================================
ARCHITECTURE DES DONNEES VINTED (2025-12-19)
=============================================================================

Il y a DEUX sources de donnees avec des formats DIFFERENTS :

1. API LISTING (GET /api/v2/wardrobe/{shop_id}/items)
   - Retourne une liste de produits avec donnees LIMITEES
   - Format des champs :
     * brand: STRING direct ("Lee", "Wrangler") - PAS d'objet avec ID !
     * size: STRING direct ("W34 | FR 44") - PAS d'objet avec ID !
     * status: STRING direct ("Bon etat") - condition texte, PAS d'ID !
     * price: OBJET {amount: "28.9", currency_code: "EUR"}
   - Champs NON DISPONIBLES dans l'API listing :
     * description, catalog_id, brand_id, size_id, condition_id
     * color, material, measurements

2. PAGE HTML PRODUIT (GET https://www.vinted.fr/items/{id}-...)
   - Contient des donnees Next.js Flight dans <script> tags
   - Donnees completes: IDs, description, attributs, frais

WORKFLOW:
1. Phase 1 : Sync API -> Donnees de base (brand texte, size texte, stats)
2. Phase 2 : Enrichissement HTML -> IDs, description, couleur, dimensions

Modules associes:
- vinted_product_enricher.py: Enrichissement via HTML parsing
- vinted_data_extractor.py: Extraction des donnees

Author: Claude
Date: 2025-12-17
Updated: 2025-12-22 - Refactored enrichment to separate module
"""

import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from models.user.marketplace_job import JobStatus, MarketplaceJob
from models.user.product import Product, ProductStatus
from models.user.vinted_product import VintedProduct
from services.plugin_websocket_helper import PluginWebSocketHelper  # WebSocket architecture (2026-01-12)
from services.product_status_manager import ProductStatusManager
from services.vinted.vinted_data_extractor import VintedDataExtractor
from services.vinted.vinted_product_enricher import VintedProductEnricher
from shared.vinted import VintedProductAPI
from shared.logging import get_logger
from shared.config import settings

logger = get_logger(__name__)


class VintedApiSyncService:
    """
    Service de synchronisation depuis l'API Vinted.

    Recupere les produits de la garde-robe Vinted et les synchronise
    avec la base de donnees locale.
    """

    def __init__(self, shop_id: int, user_id: int | None = None):
        """
        Initialize VintedApiSyncService.

        Args:
            shop_id: ID du shop Vinted (vinted_user_id)
            user_id: ID utilisateur (requis pour WebSocket) (2026-01-12)
        """
        if not shop_id:
            raise ValueError("shop_id requis pour VintedApiSyncService")
        self.shop_id = shop_id
        self.user_id = user_id
        self.extractor = VintedDataExtractor()
        self.enricher = VintedProductEnricher(user_id=user_id)

    async def sync_products_from_api(
        self,
        db: Session,
        job: MarketplaceJob | None = None
    ) -> dict[str, Any]:
        """
        Synchronise les produits depuis l'API Vinted vers la BDD.

        Business Rules:
        - Commit apres chaque produit pour eviter perte de donnees
        - Si erreur sur un produit, les precedents sont preserves
        - Met a jour job.result_data.progress si job fourni (2026-01-14)
        - Marque comme "sold" les produits qui n'apparaissent plus dans l'API (2026-01-19)

        Args:
            db: Session SQLAlchemy
            job: MarketplaceJob optionnel pour mise a jour progress

        Returns:
            dict: {"created": int, "updated": int, "errors": int, ...}
        """
        logger.info("Synchronisation API Vinted -> BDD")

        created = 0
        updated = 0
        errors = 0
        page = 1
        last_error = None
        synced_vinted_ids: set[int] = set()  # Track all products returned by API

        # Helper pour mettre a jour le progress dans job.result_data (2026-01-14)
        def update_progress():
            if job:
                total_processed = created + updated + errors
                job.result_data = {
                    **(job.result_data or {}),
                    "progress": {
                        "current": total_processed,
                        "label": "produits traités"
                    }
                }
                try:
                    db.commit()
                    db.expire(job)  # Force refresh from DB
                except Exception as e:
                    logger.warning(f"Failed to update progress: {e}")
                    db.rollback()  # CRITICAL: Rollback to prevent idle transaction

        while True:
            # CRITICAL: Check if job was cancelled (cooperative pattern - 2026-01-15)
            if job:
                db.refresh(job)  # Get latest status from DB
                if job.cancel_requested or job.status == JobStatus.CANCELLED:
                    logger.info(f"Job #{job.id} cancellation detected, stopping sync")
                    # Cleanup: commit current progress before stopping
                    db.commit()
                    break

            try:
                # WebSocket architecture (2026-01-12)
                result = await PluginWebSocketHelper.call_plugin_http(
                    db=db,
                    user_id=self.user_id,
                    http_method="GET",
                    path=VintedProductAPI.get_shop_items(self.shop_id, page=page),
                    timeout=settings.plugin_timeout_sync,
                    description=f"Sync products page {page}"
                )
            except Exception as e:
                logger.error(f"Erreur recuperation page {page}: {e}")
                last_error = str(e)
                break

            items = result.get('items', [])
            if not items:
                break

            logger.info(f"Page {page}: {len(items)} produits recuperes")

            for item in items:
                # CRITICAL: Check if job was cancelled (cooperative pattern - 2026-01-15)
                if job:
                    db.refresh(job)  # Get latest status from DB
                    if job.cancel_requested or job.status == JobStatus.CANCELLED:
                        logger.info(f"Job #{job.id} cancellation detected, stopping sync")
                        # Cleanup: commit current progress before stopping
                        db.commit()
                        break

                try:
                    processed = await self._process_api_product(db, item)
                    db.commit()

                    # Track this product as seen in API (2026-01-19)
                    vinted_id = item.get('id')
                    if vinted_id:
                        synced_vinted_ids.add(vinted_id)

                    if processed == 'created':
                        created += 1
                    elif processed == 'synced':
                        updated += 1

                    # Mettre a jour le progress apres chaque produit (2026-01-14)
                    update_progress()

                except Exception as e:
                    logger.error(f"Erreur sync produit {item.get('id')}: {e}")
                    errors += 1
                    db.rollback()

                    # Mettre a jour le progress meme en cas d'erreur (2026-01-14)
                    update_progress()

            pagination = result.get('pagination', {})
            if page >= pagination.get('total_pages', 1):
                break
            page += 1

        logger.info(
            f"Sync API terminee: {created} crees, {updated} mis a jour, "
            f"{errors} erreurs"
        )

        # Phase 1.5: Mark products NOT in API response as sold/closed (2026-01-19)
        # Products that disappear from the wardrobe are usually sold or deleted
        vinted_marked_sold = 0
        stoflow_marked_sold = 0
        if synced_vinted_ids and not last_error:  # Only if we got some products and no fatal error
            vinted_marked_sold, stoflow_marked_sold = self._mark_missing_products_as_sold(
                db, synced_vinted_ids
            )
            logger.info(
                f"Marked as sold: {vinted_marked_sold} VintedProducts, "
                f"{stoflow_marked_sold} StoFlow Products"
            )

        # Phase 1.6: Double-check - catch up any mismatched statuses from history (2026-01-19)
        catchup_synced = self._sync_existing_sold_status(db)
        if catchup_synced > 0:
            logger.info(f"[Catchup] {catchup_synced} StoFlow products synced from history")
            stoflow_marked_sold += catchup_synced

        # Phase 2: Enrichir les produits sans description via HTML
        enrichment_result = await self.enricher.enrich_products_without_description(
            db,
            job=job  # Pass job for progress tracking (2026-01-14)
        )

        result = {
            "created": created,
            "updated": updated,
            "errors": errors,
            "marked_sold": vinted_marked_sold,  # VintedProducts no longer in wardrobe (2026-01-19)
            "stoflow_marked_sold": stoflow_marked_sold,  # Linked StoFlow Products marked SOLD (2026-01-19)
            "enriched": enrichment_result.get("enriched", 0),
            "enrichment_errors": enrichment_result.get("errors", 0),
        }
        if last_error:
            result["last_error"] = last_error

        return result

    async def _process_api_product(self, db: Session, api_product: dict) -> str:
        """
        Importe un produit depuis l'API Vinted vers VintedProduct.

        IMPORTANT: L'API listing retourne des donnees LIMITEES.
        Les IDs et donnees detaillees sont obtenues via l'enrichissement HTML.

        Args:
            db: Session SQLAlchemy
            api_product: Donnees produit depuis API

        Returns:
            'synced' | 'created' | 'skipped'
        """
        vinted_id = api_product.get('id')
        if not vinted_id:
            return 'skipped'

        # Extraire les donnees disponibles dans l'API
        title = api_product.get('title', '')
        price = self.extractor.extract_price(api_product.get('price'))
        currency = api_product.get('currency', 'EUR')
        total_price = self.extractor.extract_price(api_product.get('total_item_price'))
        service_fee = self.extractor.extract_price(api_product.get('service_fee'))

        # Brand et Size : STRING directs
        brand = api_product.get('brand')
        size = api_product.get('size')
        condition = api_product.get('status')

        # Status de publication
        is_draft = api_product.get('is_draft', False)
        is_closed = api_product.get('is_closed', False)
        is_reserved = api_product.get('is_reserved', False)
        is_hidden = api_product.get('is_hidden', False)
        status = self.extractor.map_api_status(
            is_draft=is_draft,
            is_closed=is_closed,
            closing_action=api_product.get('item_closing_action')
        )

        # Seller info
        user = api_product.get('user') or {}
        seller_id = user.get('id') if isinstance(user, dict) else api_product.get('user_id')
        seller_login = user.get('login') if isinstance(user, dict) else None

        # Analytics
        view_count = api_product.get('view_count', 0)
        favourite_count = api_product.get('favourite_count', 0)

        # URLs & Images
        url = api_product.get('url', '')
        photos = api_product.get('photos', [])
        photos_data = json.dumps(photos) if photos else None

        # Publication date
        published_at = self._extract_published_at(photos, api_product)

        # Check if exists
        vinted_product = db.query(VintedProduct).filter(
            VintedProduct.vinted_id == vinted_id
        ).first()

        if vinted_product:
            return self._update_existing_product(
                vinted_product, title, price, currency, total_price, service_fee,
                brand, size, condition, status, is_draft, is_closed, is_reserved,
                is_hidden, seller_id, seller_login, view_count, favourite_count,
                url, photos_data, published_at
            )
        else:
            return self._create_new_product(
                db, vinted_id, title, price, currency, total_price, service_fee,
                brand, size, condition, status, is_draft, is_closed, is_reserved,
                is_hidden, seller_id, seller_login, view_count, favourite_count,
                url, photos_data, published_at
            )

    def _extract_published_at(
        self,
        photos: list,
        api_product: dict
    ) -> datetime | None:
        """Extract publication date from photos or API."""
        published_at = None
        if photos and isinstance(photos[0], dict):
            high_res = photos[0].get('high_resolution') or {}
            if isinstance(high_res, dict) and high_res.get('timestamp'):
                try:
                    published_at = datetime.fromtimestamp(high_res['timestamp'])
                except (ValueError, OSError):
                    pass

        if not published_at and api_product.get('created_at_ts'):
            try:
                published_at = datetime.fromtimestamp(api_product['created_at_ts'])
            except (ValueError, OSError):
                pass

        return published_at

    def _update_existing_product(
        self,
        vinted_product: VintedProduct,
        title: str,
        price,
        currency: str,
        total_price,
        service_fee,
        brand: str | None,
        size: str | None,
        condition: str | None,
        status: str,
        is_draft: bool,
        is_closed: bool,
        is_reserved: bool,
        is_hidden: bool,
        seller_id: int | None,
        seller_login: str | None,
        view_count: int,
        favourite_count: int,
        url: str,
        photos_data: str | None,
        published_at: datetime | None
    ) -> str:
        """Update existing VintedProduct."""
        vinted_product.title = title
        vinted_product.price = price
        vinted_product.currency = currency or 'EUR'
        vinted_product.total_price = total_price
        vinted_product.service_fee = service_fee
        vinted_product.brand = brand
        vinted_product.size = size
        vinted_product.condition = condition
        vinted_product.status = status
        vinted_product.is_draft = is_draft
        vinted_product.is_closed = is_closed
        vinted_product.is_reserved = is_reserved
        vinted_product.is_hidden = is_hidden
        vinted_product.seller_id = seller_id
        vinted_product.seller_login = seller_login
        vinted_product.view_count = view_count
        vinted_product.favourite_count = favourite_count
        vinted_product.url = url
        vinted_product.photos_data = photos_data

        if published_at:
            vinted_product.published_at = published_at

        return 'synced'

    def _create_new_product(
        self,
        db: Session,
        vinted_id: int,
        title: str,
        price,
        currency: str,
        total_price,
        service_fee,
        brand: str | None,
        size: str | None,
        condition: str | None,
        status: str,
        is_draft: bool,
        is_closed: bool,
        is_reserved: bool,
        is_hidden: bool,
        seller_id: int | None,
        seller_login: str | None,
        view_count: int,
        favourite_count: int,
        url: str,
        photos_data: str | None,
        published_at: datetime | None
    ) -> str:
        """Create new VintedProduct."""
        vinted_product = VintedProduct(
            vinted_id=vinted_id,
            title=title,
            price=price,
            currency=currency or 'EUR',
            total_price=total_price,
            service_fee=service_fee,
            brand=brand,
            size=size,
            condition=condition,
            status=status,
            is_draft=is_draft,
            is_closed=is_closed,
            is_reserved=is_reserved,
            is_hidden=is_hidden,
            seller_id=seller_id,
            seller_login=seller_login,
            view_count=view_count,
            favourite_count=favourite_count,
            url=url,
            photos_data=photos_data,
            published_at=published_at,
        )
        db.add(vinted_product)
        return 'created'

    def _mark_missing_products_as_sold(
        self,
        db: Session,
        synced_vinted_ids: set[int]
    ) -> tuple[int, int]:
        """
        Mark products NOT in API response as sold/closed.

        Products that disappear from the wardrobe are usually sold or deleted.
        This prevents the enrichment from trying to fetch 404 products.

        Also propagates SOLD status to linked StoFlow Products (2026-01-19).

        Args:
            db: SQLAlchemy session
            synced_vinted_ids: Set of vinted_ids that were returned by the API

        Returns:
            tuple[int, int]: (vinted_products_marked, stoflow_products_marked)
        """
        # Find products in DB that are still "active" but not in the API response
        missing_products = db.query(VintedProduct).filter(
            VintedProduct.vinted_id.notin_(synced_vinted_ids),
            VintedProduct.status == 'published',  # Only update "active" products
            VintedProduct.is_closed == False
        ).all()

        vinted_count = 0
        stoflow_count = 0

        for vinted_product in missing_products:
            logger.debug(
                f"Marking VintedProduct {vinted_product.vinted_id} as sold (no longer in wardrobe)"
            )
            vinted_product.status = 'sold'
            vinted_product.is_closed = True
            vinted_count += 1

            # Propagate to linked StoFlow Product if exists (2026-01-19)
            if vinted_product.product_id:
                try:
                    linked_product = vinted_product.product
                    if linked_product and linked_product.status == ProductStatus.PUBLISHED:
                        ProductStatusManager.update_status(
                            db,
                            vinted_product.product_id,
                            ProductStatus.SOLD
                        )
                        logger.info(
                            f"Product #{vinted_product.product_id} marked as SOLD "
                            f"(linked to VintedProduct {vinted_product.vinted_id})"
                        )
                        stoflow_count += 1
                except Exception as e:
                    logger.warning(
                        f"Failed to mark Product #{vinted_product.product_id} as SOLD: {e}"
                    )

        if vinted_count > 0:
            db.commit()

        return vinted_count, stoflow_count

    def _sync_existing_sold_status(self, db: Session) -> int:
        """
        Double vérification: synchronise le statut SOLD pour les produits
        déjà marqués sold sur Vinted mais pas encore sur StoFlow.

        Ceci rattrape les incohérences historiques à chaque sync (2026-01-19).

        Returns:
            int: Number of StoFlow products marked as SOLD
        """
        # Find VintedProducts that are sold but linked Product is still PUBLISHED
        mismatched = db.query(VintedProduct).join(
            Product, VintedProduct.product_id == Product.id
        ).filter(
            VintedProduct.status == 'sold',
            VintedProduct.product_id.isnot(None),
            Product.status == ProductStatus.PUBLISHED
        ).all()

        synced = 0
        for vinted_product in mismatched:
            try:
                ProductStatusManager.update_status(
                    db,
                    vinted_product.product_id,
                    ProductStatus.SOLD
                )
                db.commit()
                synced += 1
                logger.info(
                    f"[Catchup] Product #{vinted_product.product_id} marked as SOLD "
                    f"(VintedProduct {vinted_product.vinted_id} was already sold)"
                )
            except Exception as e:
                db.rollback()
                logger.warning(
                    f"[Catchup] Failed to mark Product #{vinted_product.product_id} as SOLD: {e}"
                )

        return synced

    async def delete_orphan_product(self, db: Session, vinted_id: int):
        """
        Supprime un produit orphelin sur Vinted.

        Args:
            db: Session SQLAlchemy
            vinted_id: ID Vinted du produit
        """
        try:
            # WebSocket architecture (2026-01-12)
            await PluginWebSocketHelper.call_plugin_http(
                db=db,
                user_id=self.user_id,
                http_method="POST",
                path=VintedProductAPI.delete(vinted_id),
                timeout=settings.plugin_timeout_delete,
                description=f"Delete orphan {vinted_id}"
            )
        except Exception as e:
            logger.error(f"Erreur suppression orphelin {vinted_id}: {e}")

