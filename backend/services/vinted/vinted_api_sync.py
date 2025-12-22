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

from sqlalchemy import text
from sqlalchemy.orm import Session

from models.user.vinted_product import VintedProduct
from services.plugin_task_helper import create_and_wait, _commit_and_restore_path
from services.vinted.vinted_data_extractor import VintedDataExtractor
from services.vinted.vinted_product_enricher import VintedProductEnricher
from shared.vinted_constants import VintedProductAPI
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class VintedApiSyncService:
    """
    Service de synchronisation depuis l'API Vinted.

    Recupere les produits de la garde-robe Vinted et les synchronise
    avec la base de donnees locale.
    """

    def __init__(self, shop_id: int):
        """
        Initialize VintedApiSyncService.

        Args:
            shop_id: ID du shop Vinted (vinted_user_id)
        """
        if not shop_id:
            raise ValueError("shop_id requis pour VintedApiSyncService")
        self.shop_id = shop_id
        self.extractor = VintedDataExtractor()
        self.enricher = VintedProductEnricher()

    async def sync_products_from_api(self, db: Session) -> dict[str, Any]:
        """
        Synchronise les produits depuis l'API Vinted vers la BDD.

        Business Rules:
        - Commit apres chaque produit pour eviter perte de donnees
        - Si erreur sur un produit, les precedents sont preserves

        Args:
            db: Session SQLAlchemy

        Returns:
            dict: {"created": int, "updated": int, "errors": int, ...}
        """
        logger.info("Synchronisation API Vinted -> BDD")

        created = 0
        updated = 0
        errors = 0
        page = 1
        last_error = None

        while True:
            try:
                result = await create_and_wait(
                    db,
                    http_method="GET",
                    path=VintedProductAPI.get_shop_items(self.shop_id, page=page),
                    payload={},
                    platform="vinted",
                    timeout=30,
                    description=f"Get products page {page}"
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
                try:
                    processed = await self._process_api_product(db, item)
                    _commit_and_restore_path(db)

                    if processed == 'created':
                        created += 1
                    elif processed == 'synced':
                        updated += 1
                except Exception as e:
                    logger.error(f"Erreur sync produit {item.get('id')}: {e}")
                    errors += 1
                    self._restore_search_path(db)

            pagination = result.get('pagination', {})
            if page >= pagination.get('total_pages', 1):
                break
            page += 1

        logger.info(
            f"Sync API terminee: {created} crees, {updated} mis a jour, "
            f"{errors} erreurs"
        )

        # Phase 2: Enrichir les produits sans description via HTML
        enrichment_result = await self.enricher.enrich_products_without_description(db)

        result = {
            "created": created,
            "updated": updated,
            "errors": errors,
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
        photo_url = photos[0].get('url') if photos else None
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
                url, photo_url, photos_data, published_at
            )
        else:
            return self._create_new_product(
                db, vinted_id, title, price, currency, total_price, service_fee,
                brand, size, condition, status, is_draft, is_closed, is_reserved,
                is_hidden, seller_id, seller_login, view_count, favourite_count,
                url, photo_url, photos_data, published_at
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
        photo_url: str | None,
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
        vinted_product.photo_url = photo_url
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
        photo_url: str | None,
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
            photo_url=photo_url,
            photos_data=photos_data,
            published_at=published_at,
        )
        db.add(vinted_product)
        return 'created'

    async def delete_orphan_product(self, db: Session, vinted_id: int):
        """
        Supprime un produit orphelin sur Vinted.

        Args:
            db: Session SQLAlchemy
            vinted_id: ID Vinted du produit
        """
        try:
            await create_and_wait(
                db,
                http_method="POST",
                path=VintedProductAPI.delete(vinted_id),
                payload={},
                platform="vinted",
                timeout=30,
                description=f"Delete orphan {vinted_id}"
            )
        except Exception as e:
            logger.error(f"Erreur suppression orphelin {vinted_id}: {e}")

    def _restore_search_path(self, db: Session) -> None:
        """Restaure le search_path PostgreSQL apres rollback."""
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
