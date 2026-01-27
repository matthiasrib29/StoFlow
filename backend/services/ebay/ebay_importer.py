"""
eBay Importer

Import de produits depuis eBay Inventory API vers Stoflow.

Business Rules:
- Import via OAuth2 (pas de cookies, API directe)
- Récupère tous les inventory items de l'utilisateur
- Stocke dans ebay_products table
- Relation 1:1 optionnelle avec Product
- Supporte multi-marketplace (détection via offers)
- Utilise AspectMapping pour extraction multi-langue des aspects

Offer enrichment logic is in ebay_offer_enrichment.py.

Author: Claude
Date: 2025-12-19
Updated: 2026-01-27 - Extracted offer enrichment to ebay_offer_enrichment.py
"""

import asyncio
import json
from typing import Optional

from sqlalchemy.orm import Session

from models.public.ebay_aspect_mapping import AspectMapping
from models.user.ebay_product import EbayProduct
from models.user.marketplace_job import JobStatus, MarketplaceJob
from services.ebay.ebay_inventory_client import EbayInventoryClient
from services.ebay.ebay_offer_client import EbayOfferClient
from services.ebay.ebay_offer_enrichment import EbayOfferEnrichment
from shared.datetime_utils import utc_now
from shared.logging import get_logger

logger = get_logger(__name__)


class EbayImporter:
    """Service pour importer produits depuis eBay Inventory API."""

    def __init__(
        self,
        db: Session,
        user_id: int,
        marketplace_id: str = "EBAY_FR",
        job: Optional[MarketplaceJob] = None
    ):
        """
        Initialise l'importeur avec les credentials OAuth eBay.

        Args:
            db: Session SQLAlchemy
            user_id: ID utilisateur Stoflow
            marketplace_id: Marketplace eBay (EBAY_FR, EBAY_GB, etc.)
            job: Optional MarketplaceJob for cooperative cancellation
        """
        self.db = db
        self.user_id = user_id
        self.marketplace_id = marketplace_id
        self.job = job
        self.inventory_client = EbayInventoryClient(db, user_id, marketplace_id)
        self.offer_client = EbayOfferClient(db, user_id, marketplace_id)

        # Load aspect reverse mapping from DB (all languages → aspect_key)
        self._aspect_reverse_map = AspectMapping.get_reverse_mapping(db)
        logger.debug(f"Loaded {len(self._aspect_reverse_map)} aspect mappings")

        # Compose enrichment service
        self.enrichment = EbayOfferEnrichment(
            db=db,
            offer_client=self.offer_client,
            aspect_reverse_map=self._aspect_reverse_map,
            job=job,
        )

    async def fetch_all_inventory_items(self) -> list[dict]:
        """
        Récupère TOUS les inventory items de l'utilisateur.

        Returns:
            list[dict]: Liste de tous les inventory items eBay
        """
        all_items = []
        offset = 0
        limit = 100

        while True:
            # Check cancellation every page (cooperative pattern - 2026-01-15)
            if self.job:
                self.db.refresh(self.job)
                if self.job.cancel_requested or self.job.status == JobStatus.CANCELLED:
                    logger.info(f"Job #{self.job.id} cancelled, stopping import at offset {offset}")
                    self.db.commit()  # Save partial progress
                    return all_items

            try:
                # Make blocking call async-compatible
                result = await asyncio.to_thread(
                    self.inventory_client.get_inventory_items,
                    limit=limit,
                    offset=offset
                )

                items = result.get("inventoryItems", [])
                if not items:
                    break

                all_items.extend(items)
                logger.info(f"Fetched {len(items)} items (offset={offset})")

                # Check if more pages
                total = result.get("total", 0)
                if offset + limit >= total:
                    break

                offset += limit

            except Exception as e:
                logger.error(f"Error fetching inventory items at offset {offset}: {e}")
                break

        logger.info(f"Total inventory items fetched: {len(all_items)}")
        return all_items

    def fetch_offers_for_sku(self, sku: str) -> list[dict]:
        """
        Récupère les offers pour un SKU donné.

        Args:
            sku: SKU de l'inventory item

        Returns:
            list[dict]: Liste des offers (par marketplace)
        """
        try:
            result = self.offer_client.get_offers(sku=sku)
            return result.get("offers", [])
        except Exception as e:
            logger.warning(f"Could not fetch offers for SKU {sku}: {e}")
            return []

    async def import_all_products(self, enrich: bool = False) -> dict:
        """
        Importe tous les produits eBay vers Stoflow.

        Args:
            enrich: If True, enrichit chaque produit avec les données offers (lent).
                    If False (default), import rapide sans enrichissement.
                    L'enrichissement peut être fait après via enrich_products_batch().

        Returns:
            dict: {
                "imported": int,
                "updated": int,
                "skipped": int,
                "errors": int,
                "details": [...]
            }
        """
        results = {
            "imported": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "details": []
        }

        # Fetch all inventory items (now async)
        inventory_items = await self.fetch_all_inventory_items()

        if not inventory_items:
            logger.info("No inventory items found on eBay")
            return results

        for i, item in enumerate(inventory_items):
            # Check cancellation every 10 items (cooperative pattern - 2026-01-15)
            if i % 10 == 0 and self.job:
                self.db.refresh(self.job)
                if self.job.cancel_requested or self.job.status == JobStatus.CANCELLED:
                    logger.info(f"Job #{self.job.id} cancelled, stopping import at item {i}/{len(inventory_items)}")
                    self.db.commit()  # Save partial progress
                    return {
                        **results,
                        "status": "cancelled",
                        "imported_count": i
                    }

            try:
                result = self._import_single_item(item, enrich=enrich)

                if result["status"] == "imported":
                    results["imported"] += 1
                elif result["status"] == "updated":
                    results["updated"] += 1
                elif result["status"] == "skipped":
                    results["skipped"] += 1

                results["details"].append(result)

                # Batch commits every 100 items for rollback safety
                if (i + 1) % 100 == 0:
                    try:
                        self.db.commit()
                        logger.info(f"Progress saved: {i + 1}/{len(inventory_items)} items processed")
                    except Exception as e:
                        logger.error(f"Error committing batch: {e}")
                        self.db.rollback()

            except Exception as e:
                sku = item.get("sku", "unknown")
                logger.error(f"Error importing item {sku}: {e}")
                results["errors"] += 1
                results["details"].append({
                    "sku": sku,
                    "status": "error",
                    "error": str(e)
                })

        # Commit final changes
        try:
            self.db.commit()
        except Exception as e:
            logger.error(f"Error committing changes: {e}")
            self.db.rollback()
            raise

        return results

    def _import_single_item(self, inventory_item: dict, enrich: bool = True) -> dict:
        """
        Importe un seul inventory item vers Stoflow.

        Args:
            inventory_item: Inventory item eBay
            enrich: Si True, enrichit immédiatement avec les données offers (prix, listing_id)

        Returns:
            dict: Résultat de l'import
        """
        sku = inventory_item.get("sku")
        if not sku:
            return {"sku": None, "status": "skipped", "reason": "no_sku"}

        # Extract product data
        product_data = self._extract_product_data(inventory_item)

        # Check if already exists
        # Use noload to avoid JOIN with relations (search_path safety)
        from sqlalchemy.orm import noload
        from sqlalchemy import text

        # Debug: check search_path before query
        sp_before = self.db.execute(text("SHOW search_path")).scalar()
        logger.debug(f"[EbayImporter] search_path before SKU query: {sp_before}")

        existing = self.db.query(EbayProduct).options(noload('*')).filter(
            EbayProduct.ebay_sku == sku
        ).first()

        logger.debug(f"[EbayImporter] SKU query result: existing={existing is not None}")

        if existing:
            # Update existing
            for key, value in product_data.items():
                if hasattr(existing, key) and value is not None:
                    setattr(existing, key, value)
            existing.last_synced_at = utc_now()
            existing.updated_at = utc_now()

            # Enrich with offers data (price, listing_id, etc.)
            if enrich:
                self.enrichment.enrich_with_offers(existing)

            return {
                "sku": sku,
                "status": "updated",
                "id": existing.id,
                "title": product_data.get("title"),
                "price": existing.price,
                "listing_id": existing.ebay_listing_id,
                "product": existing,  # Return object to avoid extra ORM query
            }

        # Create new
        ebay_product = EbayProduct(
            ebay_sku=sku,
            **product_data,
            last_synced_at=utc_now()
        )

        self.db.add(ebay_product)
        self.db.flush()  # Get ID without committing

        # Enrich with offers data (price, listing_id, etc.)
        if enrich:
            self.enrichment.enrich_with_offers(ebay_product)

        return {
            "sku": sku,
            "status": "imported",
            "id": ebay_product.id,
            "title": product_data.get("title"),
            "price": ebay_product.price,
            "listing_id": ebay_product.ebay_listing_id,
            "product": ebay_product,  # Return object to avoid extra ORM query
        }

    def _extract_product_data(self, inventory_item: dict) -> dict:
        """
        Extrait les données produit d'un inventory item eBay.

        Args:
            inventory_item: Inventory item de l'API eBay

        Returns:
            dict: Données formatées pour EbayProduct
        """
        product = inventory_item.get("product", {})
        availability = inventory_item.get("availability", {})
        ship_to_location = availability.get("shipToLocationAvailability", {})

        # Package details
        package_weight_and_size = inventory_item.get("packageWeightAndSize", {})
        package_weight = package_weight_and_size.get("weight", {})
        package_dimensions = package_weight_and_size.get("dimensions", {})

        # Extract aspects (Brand, Color, Size, etc.)
        aspects = product.get("aspects", {})
        aspects_json = json.dumps(aspects) if aspects else None

        # Extract aspects using DB mapping (multi-language support)
        brand = self._get_aspect_by_key(aspects, "brand")
        color = self._get_aspect_by_key(aspects, "color")
        size = self._get_aspect_by_key(aspects, "size")
        material = self._get_aspect_by_key(aspects, "material")

        # Extract image URLs
        image_urls = product.get("imageUrls", [])
        image_urls_json = json.dumps(image_urls) if image_urls else None

        # Condition mapping
        condition = inventory_item.get("condition")
        condition_description = inventory_item.get("conditionDescription")

        # Get quantity
        quantity = ship_to_location.get("quantity", 0)

        return {
            "title": product.get("title"),
            "description": product.get("description"),
            "brand": brand,
            "color": color,
            "size": size,
            "material": material,
            "condition": condition,
            "condition_description": condition_description,
            "quantity": quantity,
            "availability_type": "IN_STOCK" if quantity > 0 else "OUT_OF_STOCK",
            "marketplace_id": self.marketplace_id,
            "image_urls": image_urls_json,
            "aspects": aspects_json,
            "package_weight_value": package_weight.get("value"),
            "package_weight_unit": package_weight.get("unit"),
            "package_length_value": package_dimensions.get("length"),
            "package_length_unit": package_dimensions.get("unit"),
            "package_width_value": package_dimensions.get("width"),
            "package_width_unit": package_dimensions.get("unit"),
            "package_height_value": package_dimensions.get("height"),
            "package_height_unit": package_dimensions.get("unit"),
            "status": "active" if quantity > 0 else "inactive",
        }

    def _get_aspect_by_key(self, aspects: dict, aspect_key: str) -> Optional[str]:
        """
        Extrait une valeur d'aspect en utilisant le mapping DB.

        Parcourt tous les aspects du produit et trouve celui qui correspond
        à la clé demandée, quelle que soit la langue.

        Args:
            aspects: Dict d'aspects eBay {name: [values]}
            aspect_key: Clé d'aspect normalisée ('brand', 'color', 'size', etc.)

        Returns:
            str | None: Première valeur trouvée ou None
        """
        for aspect_name, values in aspects.items():
            # Use the reverse mapping to find if this aspect name maps to the key
            mapped_key = self._aspect_reverse_map.get(aspect_name)
            if mapped_key == aspect_key:
                if isinstance(values, list) and values:
                    return values[0]
                elif isinstance(values, str):
                    return values
        return None

    def _get_first_aspect(
        self,
        aspects: dict,
        aspect_names: str | list[str]
    ) -> Optional[str]:
        """
        Extrait la première valeur d'un aspect eBay (fallback method).

        Args:
            aspects: Dict des aspects eBay
            aspect_names: Nom(s) de l'aspect à chercher

        Returns:
            str | None: Première valeur trouvée
        """
        if isinstance(aspect_names, str):
            aspect_names = [aspect_names]

        for name in aspect_names:
            values = aspects.get(name, [])
            if values and isinstance(values, list):
                return values[0]

        return None

    def sync_single_product(self, sku: str) -> Optional[EbayProduct]:
        """
        Synchronise un seul produit par SKU.

        Args:
            sku: SKU eBay

        Returns:
            EbayProduct | None
        """
        try:
            # Fetch from eBay
            inventory_item = self.inventory_client.get_inventory_item(sku)

            # Import/update
            result = self._import_single_item(inventory_item)

            if result["status"] in ["imported", "updated"]:
                ebay_product = self.db.query(EbayProduct).filter(
                    EbayProduct.ebay_sku == sku
                ).first()

                if ebay_product:
                    # Enrich with offer data
                    self.enrichment.enrich_with_offers(ebay_product)
                    self.db.commit()
                    return ebay_product

        except Exception as e:
            logger.error(f"Error syncing product {sku}: {e}")
            self.db.rollback()

        return None

    async def sync_from_inventory_bulk(self) -> dict:
        """
        Synchronise TOUS les produits depuis l'Inventory API (bulk).

        Cette méthode :
        1. Récupère tous les inventory items depuis eBay (paginé)
        2. Met à jour TOUS les champs Inventory API pour chaque produit existant :
           - quantity, availability_type
           - title, description
           - brand, color, size, material (via aspects)
           - condition, condition_description
           - image_urls, aspects
           - package dimensions/weight

        C'est la première étape d'un full_sync(). Après cette étape,
        appeler enrich_all_with_offers() pour compléter avec les données Offer API.

        Returns:
            dict: {
                "synced": int,
                "not_found": int,
                "errors": int,
                "total_inventory_items": int
            }
        """
        results = {
            "synced": 0,
            "not_found": 0,
            "errors": 0,
            "total_inventory_items": 0
        }

        # 1. Fetch all inventory items from eBay
        logger.info("[SyncInventory] Fetching all inventory items from eBay...")
        inventory_items = await self.fetch_all_inventory_items()
        results["total_inventory_items"] = len(inventory_items)

        if not inventory_items:
            logger.info("[SyncInventory] No inventory items found on eBay")
            return results

        # 2. Build a map of SKU -> inventory_item for fast lookup
        inventory_map = {item.get("sku"): item for item in inventory_items if item.get("sku")}

        # 3. Get all existing products from DB
        existing_products = self.db.query(EbayProduct).all()
        logger.info(f"[SyncInventory] Found {len(existing_products)} products in DB to sync")

        # 4. Update each product with fresh inventory data
        for product in existing_products:
            # Check cancellation
            if self.job:
                self.db.refresh(self.job)
                if self.job.cancel_requested or self.job.status == JobStatus.CANCELLED:
                    logger.info(f"[SyncInventory] Job cancelled, stopping sync")
                    self.db.commit()
                    return {**results, "status": "cancelled"}

            inventory_item = inventory_map.get(product.ebay_sku)

            if not inventory_item:
                # Product exists in DB but not in eBay inventory
                results["not_found"] += 1
                logger.debug(f"[SyncInventory] SKU {product.ebay_sku} not found in eBay inventory")
                continue

            try:
                # Extract and update ALL inventory fields
                product_data = self._extract_product_data(inventory_item)

                # Update all fields from inventory
                for key, value in product_data.items():
                    if hasattr(product, key) and value is not None:
                        setattr(product, key, value)

                product.last_synced_at = utc_now()
                results["synced"] += 1

                logger.debug(
                    f"[SyncInventory] Updated SKU {product.ebay_sku}: "
                    f"qty={product.quantity}, status={product.status}"
                )

            except Exception as e:
                logger.warning(f"[SyncInventory] Error updating {product.ebay_sku}: {e}")
                results["errors"] += 1

        # 5. Commit changes
        try:
            self.db.commit()
            logger.info(
                f"[SyncInventory] Completed: {results['synced']} synced, "
                f"{results['not_found']} not found, {results['errors']} errors"
            )
        except Exception as e:
            logger.error(f"[SyncInventory] Error committing: {e}")
            self.db.rollback()
            raise

        return results

    async def full_sync(self) -> dict:
        """
        Synchronisation complète : Inventory API (bulk) puis Offer API (un par un).

        Flow:
        1. Fetch ALL inventory items from eBay → update quantity, title, etc.
        2. For each product, fetch offers → update price, status, sold_quantity, etc.

        C'est la méthode recommandée pour une sync complète des données eBay.

        Returns:
            dict: {
                "inventory_sync": {...},
                "offers_enrichment": {...}
            }
        """
        logger.info("[FullSync] Starting full sync...")

        # Step 1: Sync from Inventory API (bulk)
        logger.info("[FullSync] Step 1/2: Syncing from Inventory API...")
        inventory_results = await self.sync_from_inventory_bulk()

        if inventory_results.get("status") == "cancelled":
            return {"inventory_sync": inventory_results, "offers_enrichment": None, "status": "cancelled"}

        # Step 2: Enrich with Offer API (one by one)
        logger.info("[FullSync] Step 2/2: Enriching with Offer API...")
        offers_results = self.enrichment.enrich_all_with_offers()

        logger.info("[FullSync] Full sync completed!")

        return {
            "inventory_sync": inventory_results,
            "offers_enrichment": offers_results
        }
