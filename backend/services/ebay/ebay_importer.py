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

Author: Claude
Date: 2025-12-19
"""

import json
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from models.public.ebay_aspect_mapping import AspectMapping
from models.user.ebay_product import EbayProduct
from services.ebay.ebay_inventory_client import EbayInventoryClient
from services.ebay.ebay_offer_client import EbayOfferClient
from shared.datetime_utils import utc_now
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class EbayImporter:
    """Service pour importer produits depuis eBay Inventory API."""

    def __init__(self, db: Session, user_id: int, marketplace_id: str = "EBAY_FR"):
        """
        Initialise l'importeur avec les credentials OAuth eBay.

        Args:
            db: Session SQLAlchemy
            user_id: ID utilisateur Stoflow
            marketplace_id: Marketplace eBay (EBAY_FR, EBAY_GB, etc.)
        """
        self.db = db
        self.user_id = user_id
        self.marketplace_id = marketplace_id
        self.inventory_client = EbayInventoryClient(db, user_id, marketplace_id)
        self.offer_client = EbayOfferClient(db, user_id, marketplace_id)

        # Load aspect reverse mapping from DB (all languages → aspect_key)
        self._aspect_reverse_map = AspectMapping.get_reverse_mapping(db)
        logger.debug(f"Loaded {len(self._aspect_reverse_map)} aspect mappings")

    def fetch_all_inventory_items(self) -> list[dict]:
        """
        Récupère TOUS les inventory items de l'utilisateur.

        Returns:
            list[dict]: Liste de tous les inventory items eBay
        """
        all_items = []
        offset = 0
        limit = 100

        while True:
            try:
                result = self.inventory_client.get_inventory_items(
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

    def import_all_products(self) -> dict:
        """
        Importe tous les produits eBay vers Stoflow.

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

        # Fetch all inventory items
        inventory_items = self.fetch_all_inventory_items()

        if not inventory_items:
            logger.info("No inventory items found on eBay")
            return results

        for item in inventory_items:
            try:
                result = self._import_single_item(item)

                if result["status"] == "imported":
                    results["imported"] += 1
                elif result["status"] == "updated":
                    results["updated"] += 1
                elif result["status"] == "skipped":
                    results["skipped"] += 1

                results["details"].append(result)

            except Exception as e:
                sku = item.get("sku", "unknown")
                logger.error(f"Error importing item {sku}: {e}")
                results["errors"] += 1
                results["details"].append({
                    "sku": sku,
                    "status": "error",
                    "error": str(e)
                })

        # Commit all changes
        try:
            self.db.commit()
        except Exception as e:
            logger.error(f"Error committing changes: {e}")
            self.db.rollback()
            raise

        return results

    def _import_single_item(self, inventory_item: dict) -> dict:
        """
        Importe un seul inventory item vers Stoflow.

        Args:
            inventory_item: Inventory item eBay

        Returns:
            dict: Résultat de l'import
        """
        sku = inventory_item.get("sku")
        if not sku:
            return {"sku": None, "status": "skipped", "reason": "no_sku"}

        # Extract product data
        product_data = self._extract_product_data(inventory_item)

        # Check if already exists
        existing = self.db.query(EbayProduct).filter(
            EbayProduct.ebay_sku == sku
        ).first()

        if existing:
            # Update existing
            for key, value in product_data.items():
                if hasattr(existing, key) and value is not None:
                    setattr(existing, key, value)
            existing.last_synced_at = utc_now()
            existing.updated_at = utc_now()

            return {
                "sku": sku,
                "status": "updated",
                "id": existing.id,
                "title": product_data.get("title")
            }

        # Create new
        ebay_product = EbayProduct(
            ebay_sku=sku,
            **product_data,
            last_synced_at=utc_now()
        )

        self.db.add(ebay_product)
        self.db.flush()  # Get ID without committing

        return {
            "sku": sku,
            "status": "imported",
            "id": ebay_product.id,
            "title": product_data.get("title")
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

    def enrich_with_offers(self, ebay_product: EbayProduct) -> None:
        """
        Enrichit un EbayProduct avec les données des offers.

        Prend le premier offer disponible (priorité au marketplace configuré).

        Args:
            ebay_product: Produit eBay à enrichir
        """
        try:
            offers = self.fetch_offers_for_sku(ebay_product.ebay_sku)

            if not offers:
                return

            # Try to find offer for configured marketplace first, otherwise take first one
            selected_offer = None
            for offer in offers:
                if offer.get("marketplaceId") == self.marketplace_id:
                    selected_offer = offer
                    break
            if not selected_offer:
                selected_offer = offers[0]  # Take first available offer

            # Update with offer data
            ebay_product.ebay_offer_id = selected_offer.get("offerId")
            ebay_product.marketplace_id = selected_offer.get("marketplaceId", self.marketplace_id)

            # Listing details
            listing = selected_offer.get("listing", {})
            ebay_product.ebay_listing_id = listing.get("listingId")
            ebay_product.sold_quantity = listing.get("soldQuantity")

            # Price from offer
            pricing = selected_offer.get("pricingSummary", {})
            price_obj = pricing.get("price", {})
            if price_obj:
                ebay_product.price = float(price_obj.get("value", 0))
                ebay_product.currency = price_obj.get("currency", "EUR")

            # Listing format and duration
            ebay_product.listing_format = selected_offer.get("format")
            ebay_product.listing_duration = selected_offer.get("listingDuration")

            # Categories
            ebay_product.category_id = selected_offer.get("categoryId")
            ebay_product.secondary_category_id = selected_offer.get("secondaryCategoryId")

            # Location
            ebay_product.merchant_location_key = selected_offer.get("merchantLocationKey")

            # Quantity details
            ebay_product.available_quantity = selected_offer.get("availableQuantity")
            ebay_product.lot_size = selected_offer.get("lotSize")
            ebay_product.quantity_limit_per_buyer = selected_offer.get("quantityLimitPerBuyer")

            # Listing description (may differ from product description)
            ebay_product.listing_description = selected_offer.get("listingDescription")

            # Status from offer
            offer_status = selected_offer.get("status")
            if offer_status == "PUBLISHED":
                ebay_product.status = "active"
                ebay_product.published_at = utc_now()
            elif offer_status == "ENDED":
                ebay_product.status = "ended"

        except Exception as e:
            logger.warning(f"Could not enrich product {ebay_product.ebay_sku}: {e}")

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
                    self.enrich_with_offers(ebay_product)
                    self.db.commit()
                    return ebay_product

        except Exception as e:
            logger.error(f"Error syncing product {sku}: {e}")
            self.db.rollback()

        return None

    def enrich_products_batch(
        self,
        limit: int = 100,
        only_without_price: bool = True
    ) -> dict:
        """
        Enrichit les produits avec les données des offers par lot.

        Args:
            limit: Nombre max de produits à enrichir
            only_without_price: Si True, enrichit seulement les produits sans prix

        Returns:
            dict: {
                "enriched": int,
                "errors": int,
                "details": [...]
            }
        """
        results = {
            "enriched": 0,
            "errors": 0,
            "remaining": 0,
            "details": []
        }

        # Build query
        query = self.db.query(EbayProduct)
        if only_without_price:
            query = query.filter(EbayProduct.price.is_(None))

        # Count remaining
        results["remaining"] = query.count()

        # Limit to batch size
        products = query.limit(limit).all()

        for product in products:
            try:
                self.enrich_with_offers(product)
                results["enriched"] += 1
                results["details"].append({
                    "sku": product.ebay_sku,
                    "status": "enriched",
                    "price": product.price
                })
            except Exception as e:
                logger.warning(f"Error enriching {product.ebay_sku}: {e}")
                results["errors"] += 1
                results["details"].append({
                    "sku": product.ebay_sku,
                    "status": "error",
                    "error": str(e)
                })

        # Commit changes
        try:
            self.db.commit()
            results["remaining"] -= results["enriched"]
        except Exception as e:
            logger.error(f"Error committing enrichment: {e}")
            self.db.rollback()
            raise

        return results

    def refresh_aspects_batch(self, limit: int = 100) -> dict:
        """
        Re-extrait les aspects (brand, color, size, material) des produits existants.

        Utile après mise à jour du mapping multi-langue.

        Args:
            limit: Nombre max de produits à traiter

        Returns:
            dict: {"updated": int, "errors": int, "remaining": int}
        """
        results = {"updated": 0, "errors": 0, "remaining": 0}

        # Get products with aspects but missing brand
        query = self.db.query(EbayProduct).filter(
            EbayProduct.aspects.isnot(None),
            EbayProduct.brand.is_(None)
        )
        results["remaining"] = query.count()
        products = query.limit(limit).all()

        for product in products:
            try:
                aspects = json.loads(product.aspects) if product.aspects else {}

                # Re-extract using DB mapping (multi-language support)
                product.brand = self._get_aspect_by_key(aspects, "brand")
                product.color = self._get_aspect_by_key(aspects, "color")
                product.size = self._get_aspect_by_key(aspects, "size")
                product.material = self._get_aspect_by_key(aspects, "material")

                results["updated"] += 1
            except Exception as e:
                logger.warning(f"Error refreshing aspects for {product.ebay_sku}: {e}")
                results["errors"] += 1

        try:
            self.db.commit()
            results["remaining"] -= results["updated"]
        except Exception as e:
            logger.error(f"Error committing aspect refresh: {e}")
            self.db.rollback()
            raise

        return results
