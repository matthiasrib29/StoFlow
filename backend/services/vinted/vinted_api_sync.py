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
     * user: OBJET {id, login, photo, ...}
     * photos: ARRAY avec high_resolution.timestamp
   - Champs NON DISPONIBLES dans l'API listing :
     * description (toujours vide)
     * catalog_id, brand_id, size_id, condition_id
     * color, material, measurements

2. PAGE HTML PRODUIT (GET https://www.vinted.fr/items/{id}-...)
   - Contient des donnees Next.js Flight dans <script> tags
   - Format des champs (dans self.__next_f.push) :
     * brand_dto: OBJET {id: 259, title: "Wrangler"}
     * catalog_id: INTEGER direct (1819)
     * attributes[code=size]: OBJET {id: 1233, value: "W26 | FR 36"}
     * attributes[code=status]: OBJET {id: 50, value: "Bon etat"}
       NOTE: L'ID 50 est different du status_id API (1-6) !
     * attributes[code=color]: OBJET {value: "Bleu"} - PAS d'ID !
     * description: disponible
     * service_fee, total_item_price: disponibles

WORKFLOW:
1. Phase 1 : Sync API -> Donnees de base (brand texte, size texte, stats)
2. Phase 2 : Enrichissement HTML -> IDs, description, couleur, dimensions

Author: Claude
Date: 2025-12-17
Updated: 2025-12-18 - Added automatic HTML enrichment for products without description
Updated: 2025-12-19 - Fixed API extraction to match real API format
"""

import asyncio
import json
import random
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from models.user.vinted_product import VintedProduct
from services.plugin_task_helper import create_and_wait, _commit_and_restore_path
from services.vinted.vinted_data_extractor import VintedDataExtractor
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

    async def sync_products_from_api(self, db: Session) -> dict[str, Any]:
        """
        Synchronise les produits depuis l'API Vinted vers la BDD.

        Business Rules (2025-12-17):
        - Commit apres chaque produit pour eviter perte de donnees
        - Si erreur sur un produit, les precedents sont preserves

        Args:
            db: Session SQLAlchemy

        Returns:
            dict: {"created": int, "updated": int, "errors": int}
        """
        logger.info("Synchronisation API Vinted -> BDD")

        created = 0
        updated = 0
        errors = 0
        page = 1
        last_error = None

        while True:
            # Recuperer page de produits
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

                    # Commit apres chaque produit traite
                    _commit_and_restore_path(db)

                    if processed == 'created':
                        created += 1
                    elif processed == 'synced':
                        updated += 1
                except Exception as e:
                    logger.error(f"Erreur sync produit {item.get('id')}: {e}")
                    errors += 1
                    # Utiliser la methode centralisee pour rollback + restore
                    self._restore_search_path(db)

            # Pagination
            pagination = result.get('pagination', {})
            if page >= pagination.get('total_pages', 1):
                break
            page += 1

        logger.info(
            f"Sync API terminee: {created} crees, {updated} mis a jour, "
            f"{errors} erreurs"
        )

        # Phase 2: Enrichir les produits sans description via HTML parsing
        enrichment_result = await self._enrich_products_without_description(db)

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
        Les IDs (brand_id, size_id, catalog_id, condition_id) et autres
        donnees detaillees (description, color, material) sont obtenues
        via l'enrichissement HTML (Phase 2).

        Format API listing (GET /api/v2/wardrobe/{shop_id}/items):
        {
            "id": 7750837522,
            "title": "Lee Jeans loose...",
            "brand": "Lee",                    # STRING direct, pas d'objet !
            "size": "W34 | FR 44",             # STRING direct, pas d'objet !
            "status": "Bon etat",              # Condition texte, pas d'ID !
            "price": {"amount": "28.9", "currency_code": "EUR"},
            "user": {"id": 29535217, "login": "shop.ton.outfit"},
            "photos": [{"high_resolution": {"timestamp": 1765555585}}],
            "view_count": 6,
            "favourite_count": 2,
            ...
        }

        Args:
            db: Session SQLAlchemy
            api_product: Donnees produit depuis API

        Returns:
            'synced' | 'created' | 'skipped'
        """
        vinted_id = api_product.get('id')
        if not vinted_id:
            return 'skipped'

        # =====================================================================
        # DONNEES DISPONIBLES DANS L'API LISTING
        # =====================================================================

        title = api_product.get('title', '')

        # Prix : objet {amount, currency_code}
        price = self.extractor.extract_price(api_product.get('price'))
        currency = api_product.get('currency', 'EUR')
        total_price = self.extractor.extract_price(api_product.get('total_item_price'))
        service_fee = self.extractor.extract_price(api_product.get('service_fee'))

        # Brand et Size : STRING directs dans l'API (pas d'objets avec ID !)
        # Les IDs seront recuperes via l'enrichissement HTML
        brand = api_product.get('brand')  # STRING: "Lee", "Wrangler", etc.
        size = api_product.get('size')    # STRING: "W34 | FR 44", "M", etc.

        # Condition : STRING dans le champ "status" (pas d'ID dans l'API listing !)
        # Ex: "Bon etat", "Tres bon etat", "Neuf avec etiquette"
        condition = api_product.get('status')

        # Status de publication : derive des flags is_draft, is_closed, etc.
        is_draft = api_product.get('is_draft', False)
        is_closed = api_product.get('is_closed', False)
        is_reserved = api_product.get('is_reserved', False)
        is_hidden = api_product.get('is_hidden', False)
        status = self.extractor.map_api_status(
            is_draft=is_draft,
            is_closed=is_closed,
            closing_action=api_product.get('item_closing_action')
        )

        # Seller info : objet "user" avec id et login
        user = api_product.get('user') or {}
        seller_id = user.get('id') if isinstance(user, dict) else api_product.get('user_id')
        seller_login = user.get('login') if isinstance(user, dict) else None

        # Analytics : disponibles dans l'API
        view_count = api_product.get('view_count', 0)
        favourite_count = api_product.get('favourite_count', 0)

        # URLs & Images
        url = api_product.get('url', '')
        photos = api_product.get('photos', [])
        photo_url = photos[0].get('url') if photos else None
        photos_data = json.dumps(photos) if photos else None

        # Publication date : depuis le timestamp de la premiere photo
        published_at = None
        if photos and isinstance(photos[0], dict):
            high_res = photos[0].get('high_resolution') or {}
            if isinstance(high_res, dict) and high_res.get('timestamp'):
                try:
                    published_at = datetime.fromtimestamp(high_res['timestamp'])
                except (ValueError, OSError):
                    pass
        # Fallback to API created_at_ts (si disponible)
        if not published_at and api_product.get('created_at_ts'):
            try:
                published_at = datetime.fromtimestamp(api_product['created_at_ts'])
            except (ValueError, OSError):
                pass

        # =====================================================================
        # DONNEES NON DISPONIBLES DANS L'API LISTING
        # Seront remplies par l'enrichissement HTML (Phase 2)
        # =====================================================================
        # - description (toujours vide dans l'API)
        # - brand_id, size_id, catalog_id, condition_id
        # - color, material, measurements
        # - manufacturer_labelling
        # - buyer_protection_fee, shipping_price

        # Check if exists
        vinted_product = db.query(VintedProduct).filter(
            VintedProduct.vinted_id == vinted_id
        ).first()

        if vinted_product:
            # Update existing - seulement les champs disponibles dans l'API
            vinted_product.title = title
            vinted_product.price = price
            vinted_product.currency = currency or 'EUR'
            vinted_product.total_price = total_price
            vinted_product.service_fee = service_fee

            # Brand/Size : texte seulement (IDs via enrichissement HTML)
            vinted_product.brand = brand
            vinted_product.size = size

            # Condition : texte seulement (ID via enrichissement HTML)
            vinted_product.condition = condition

            # Status de publication
            vinted_product.status = status
            vinted_product.is_draft = is_draft
            vinted_product.is_closed = is_closed
            vinted_product.is_reserved = is_reserved
            vinted_product.is_hidden = is_hidden

            # Seller info
            vinted_product.seller_id = seller_id
            vinted_product.seller_login = seller_login

            # Analytics
            vinted_product.view_count = view_count
            vinted_product.favourite_count = favourite_count

            # URLs & Images
            vinted_product.url = url
            vinted_product.photo_url = photo_url
            vinted_product.photos_data = photos_data

            if published_at:
                vinted_product.published_at = published_at

            return 'synced'
        else:
            # Create new - seulement les champs disponibles dans l'API
            # Les autres champs (IDs, description, color, etc.) seront
            # remplis par l'enrichissement HTML
            vinted_product = VintedProduct(
                vinted_id=vinted_id,
                title=title,
                price=price,
                currency=currency or 'EUR',
                total_price=total_price,
                service_fee=service_fee,
                # Brand/Size : texte seulement
                brand=brand,
                size=size,
                # Condition : texte seulement
                condition=condition,
                # Status de publication
                status=status,
                is_draft=is_draft,
                is_closed=is_closed,
                is_reserved=is_reserved,
                is_hidden=is_hidden,
                # Seller info
                seller_id=seller_id,
                seller_login=seller_login,
                # Analytics
                view_count=view_count,
                favourite_count=favourite_count,
                # URLs & Images
                url=url,
                photo_url=photo_url,
                photos_data=photos_data,
                published_at=published_at,
                # Les champs suivants restent NULL jusqu'a l'enrichissement HTML:
                # description, brand_id, size_id, catalog_id, condition_id,
                # color, material, measurements, manufacturer_labelling,
                # buyer_protection_fee, shipping_price
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

    # =========================================================================
    # ENRICHISSEMENT VIA HTML PARSING
    # =========================================================================

    async def _enrich_products_without_description(
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
        2. Extrait TOUTES les donnees (description, IDs, dimensions, frais, etc.)
        3. Met a jour le produit en BDD

        Business Rules:
        - Delai 1-2s entre requetes (gere cote plugin via execute_delay_ms)
        - Pause 10-15s tous les 30 produits
        - Traite TOUS les produits sans description
        - Commit apres chaque produit enrichi
        - Si erreur/timeout: skipper et continuer

        Args:
            db: Session SQLAlchemy
            batch_size: Nombre de produits avant pause longue (default: 30)
            batch_pause_min: Duree min pause entre batches (default: 10s)
            batch_pause_max: Duree max pause entre batches (default: 15s)

        Returns:
            dict: {"enriched": int, "errors": int, "skipped": int}
        """
        # Trouver TOUS les produits sans description
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
            # Pause longue tous les batch_size produits
            if i > 0 and i % batch_size == 0:
                pause = random.uniform(batch_pause_min, batch_pause_max)
                logger.info(
                    f"  Pause de {pause:.1f}s apres {i} produits "
                    f"({enriched} enrichis, {errors} erreurs)"
                )
                await asyncio.sleep(pause)
            # Note: le delai 1-2s entre requetes est gere cote plugin via execute_delay_ms

            try:
                success = await self._enrich_single_product(db, product)
                if success:
                    enriched += 1
                    logger.debug(
                        f"  [{i+1}/{total}] "
                        f"Enrichi: {product.vinted_id} - {product.title[:30] if product.title else 'N/A'}..."
                    )
            except Exception as e:
                errors += 1
                logger.error(
                    f"Erreur enrichissement {product.vinted_id}: {e}",
                    exc_info=True
                )
                db.rollback()
                # Restaurer search_path apres rollback
                self._restore_search_path(db)

        logger.info(f"Enrichissement termine: {enriched} enrichis, {errors} erreurs")

        return {"enriched": enriched, "errors": errors, "skipped": 0}

    async def _enrich_single_product(self, db: Session, product: VintedProduct) -> bool:
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
            # Fetch HTML via plugin
            # Timeout 30s - si dépassé, la tâche est annulée (CANCELLED)
            result = await create_and_wait(
                db,
                http_method="GET",
                path=product.url,
                timeout=30,
                rate_limit=False,
                description=f"Fetch HTML for {product.vinted_id}"
            )

            html = result.get("data", "") if isinstance(result, dict) else str(result)

            # DEBUG: Log what we received
            logger.debug(f"HTML recu pour {product.vinted_id}: {len(html)} chars, starts with: {html[:200] if html else 'EMPTY'}")

            if not html or len(html) < 1000:
                logger.warning(f"HTML trop court pour {product.vinted_id}: {len(html) if html else 0} chars")
                return False

            # Extraire les donnees via VintedDataExtractor
            extracted = VintedDataExtractor.extract_product_from_html(html)

            if not extracted:
                logger.warning(f"Extraction echouee pour {product.vinted_id}")
                return False

            # Mettre a jour le produit avec les donnees extraites
            self._update_product_from_extracted(product, extracted)

            # Commit et restaurer search_path
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

        Format des donnees extraites (depuis VintedDataExtractor):
        {
            'vinted_id': 7751078047,
            'title': '...',
            'description': 'Texte complet...',

            # IDs Vinted (depuis brand_dto et attributes)
            'brand_id': 259,
            'brand_name': 'Wrangler',
            'size_id': 1233,
            'size_title': 'W26 | FR 36',
            'catalog_id': 1819,
            'condition_id': 50,           # NOTE: ID HTML != status_id API !
            'condition_title': 'Bon etat',

            # Attributs (depuis attributes block)
            'color': 'Bleu',              # NOTE: Pas d'ID disponible !
            'material': 'Denim',
            'measurements': 'l 47 cm / L 70 cm',
            'measurement_width': 47,
            'measurement_length': 70,
            'manufacturer_labelling': '...',

            # Frais (depuis item block)
            'service_fee': 1.37,
            'buyer_protection_fee': 1.37,
            'shipping_price': 2.83,
            'total_item_price': 20.27,

            # Date publication (depuis photo timestamp)
            'published_at': datetime(2025, 12, 12, ...),
        }

        Args:
            product: VintedProduct a mettre a jour
            extracted: Donnees extraites par VintedDataExtractor
        """
        # Log what we extracted for debugging (DEBUG level en production)
        logger.debug(
            f"Product {product.vinted_id} extracted data: "
            f"description={'Yes' if extracted.get('description') else 'No'}, "
            f"color={extracted.get('color', 'No')}, "
            f"material={extracted.get('material', 'No')}, "
            f"size={extracted.get('size_title', 'No')}, "
            f"condition={extracted.get('condition_title', 'No')}, "
            f"brand={extracted.get('brand_name', 'No')}"
        )

        # =====================================================================
        # DESCRIPTION (prioritaire - c'est pour ca qu'on fait l'enrichissement)
        # =====================================================================
        if extracted.get('description'):
            product.description = extracted['description']

        # =====================================================================
        # IDs VINTED (pour operations futures comme la publication)
        # NOTE: Ces IDs viennent du HTML, pas de l'API listing !
        # =====================================================================

        # Brand ID (depuis brand_dto dans le HTML)
        if extracted.get('brand_id'):
            product.brand_id = extracted['brand_id']
        if extracted.get('brand_name') and not product.brand:
            product.brand = extracted['brand_name']

        # Size ID (depuis attributes[code=size].data.id)
        if extracted.get('size_id'):
            product.size_id = extracted['size_id']
        if extracted.get('size_title') and not product.size:
            product.size = extracted['size_title']

        # Catalog ID (depuis item.catalog_id)
        if extracted.get('catalog_id'):
            product.catalog_id = extracted['catalog_id']

        # Condition ID (depuis attributes[code=status].data.id)
        # ATTENTION: Cet ID (ex: 50) est DIFFERENT du status_id API (1-6) !
        if extracted.get('condition_id'):
            product.condition_id = extracted['condition_id']
        if extracted.get('condition_title') and not product.condition:
            product.condition = extracted['condition_title']

        # =====================================================================
        # ATTRIBUTS SUPPLEMENTAIRES (depuis attributes block)
        # =====================================================================

        # Couleur : TEXTE seulement, pas d'ID disponible dans le HTML !
        if extracted.get('color') and not product.color:
            product.color = extracted['color']

        # Matiere
        if extracted.get('material'):
            product.material = extracted['material']

        # Dimensions
        if extracted.get('measurements'):
            product.measurements = extracted['measurements']
        if extracted.get('measurement_width'):
            product.measurement_width = extracted['measurement_width']
        if extracted.get('measurement_length'):
            product.measurement_length = extracted['measurement_length']

        # Etiquetage fabricant
        if extracted.get('manufacturer_labelling'):
            product.manufacturer_labelling = extracted['manufacturer_labelling']

        # =====================================================================
        # FRAIS (utile pour calculs de marge)
        # =====================================================================
        if extracted.get('service_fee'):
            product.service_fee = extracted['service_fee']
        if extracted.get('buyer_protection_fee'):
            product.buyer_protection_fee = extracted['buyer_protection_fee']
        if extracted.get('shipping_price'):
            product.shipping_price = extracted['shipping_price']
        if extracted.get('total_item_price'):
            product.total_price = extracted['total_item_price']

        # =====================================================================
        # SELLER INFO (normalement deja rempli par l'API, mais on complete)
        # =====================================================================
        if extracted.get('seller_id'):
            product.seller_id = extracted['seller_id']
        if extracted.get('seller_login'):
            product.seller_login = extracted['seller_login']

        # Status flags
        if 'is_reserved' in extracted:
            product.is_reserved = extracted['is_reserved']
        if 'is_hidden' in extracted:
            product.is_hidden = extracted['is_hidden']

        # =====================================================================
        # DATE DE PUBLICATION (depuis photos[0].high_resolution.timestamp)
        # =====================================================================
        if extracted.get('published_at') and not product.published_at:
            product.published_at = extracted['published_at']

    def _restore_search_path(self, db: Session) -> None:
        """
        Restaure le search_path PostgreSQL apres rollback.

        CRITICAL (2025-12-18): Gere le cas InFailedSqlTransaction
        - Apres rollback, la session peut encore etre dans un etat invalide
        - On doit d'abord terminer toute transaction en cours via un rollback
        - Puis reconfigurer le search_path
        """
        try:
            # Forcer un rollback propre pour s'assurer qu'on est hors transaction
            # Cela evite InFailedSqlTransaction si un rollback precedent a echoue
            try:
                db.rollback()
            except Exception:
                pass  # Ignore si deja rollback

            # Maintenant on peut lire le search_path
            path_result = db.execute(text("SHOW search_path"))
            current_path = path_result.scalar()
            if current_path:
                for s in current_path.split(","):
                    s = s.strip().strip('"')
                    if s.startswith("user_"):
                        db.execute(text(f"SET LOCAL search_path TO {s}, public"))
                        break
        except Exception as e:
            # Log mais ne pas re-raise - on continue avec le search_path par defaut
            logger.warning(f"Impossible de restaurer search_path: {e}")
