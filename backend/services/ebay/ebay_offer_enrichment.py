"""
eBay Offer Enrichment

Enrichment of eBay products with data from the Offer API.
Extracted from ebay_importer.py for separation of concerns.

Responsibilities:
- Enrich products with offer data (price, listing_id, status, etc.)
- Batch enrichment for multiple products
- Refresh aspects using DB mapping (multi-language support)

Author: Claude
Date: 2026-01-27 - Extracted from ebay_importer.py
"""

import json
from typing import Optional

from sqlalchemy.orm import Session

from models.user.ebay_product import EbayProduct
from models.user.marketplace_job import JobStatus, MarketplaceJob
from shared.datetime_utils import utc_now
from shared.logging import get_logger

logger = get_logger(__name__)


class EbayOfferEnrichment:
    """Service for enriching eBay products with Offer API data."""

    def __init__(
        self,
        db: Session,
        offer_client,
        aspect_reverse_map: dict,
        job: Optional[MarketplaceJob] = None,
    ):
        """
        Args:
            db: SQLAlchemy session
            offer_client: EbayOfferClient instance
            aspect_reverse_map: Reverse mapping from aspect names to aspect keys
            job: Optional MarketplaceJob for cooperative cancellation
        """
        self.db = db
        self.offer_client = offer_client
        self._aspect_reverse_map = aspect_reverse_map
        self.job = job

    def _fetch_offers(self, sku: str) -> list[dict]:
        """Fetch offers for a SKU from eBay Offer API."""
        try:
            result = self.offer_client.get_offers(sku=sku)
            return result.get("offers", [])
        except Exception as e:
            logger.warning(f"Could not fetch offers for SKU {sku}: {e}", exc_info=True)
            return []

    def _get_aspect_by_key(self, aspects: dict, aspect_key: str) -> Optional[str]:
        """
        Extract an aspect value using the DB reverse mapping.

        Args:
            aspects: Dict of eBay aspects {name: [values]}
            aspect_key: Normalized aspect key ('brand', 'color', 'size', etc.)

        Returns:
            str | None: First value found or None
        """
        for aspect_name, values in aspects.items():
            mapped_key = self._aspect_reverse_map.get(aspect_name)
            if mapped_key == aspect_key:
                if isinstance(values, list) and values:
                    return values[0]
                elif isinstance(values, str):
                    return values
        return None

    def enrich_with_offers(self, ebay_product: EbayProduct) -> None:
        """
        Enrich an EbayProduct with data from the Offer API.

        Updates ALL fields from the Offer API:
        - price, currency
        - ebay_offer_id, ebay_listing_id
        - sold_quantity, available_quantity
        - status (based on offer status + listing status)
        - listing_format, listing_duration
        - category_id, secondary_category_id
        - merchant_location_key
        - lot_size, quantity_limit_per_buyer
        - listing_description

        Note: Does NOT update Inventory API fields (quantity, title, etc.)

        Args:
            ebay_product: eBay product to enrich
        """
        try:
            offers = self._fetch_offers(ebay_product.ebay_sku)

            if not offers:
                current_qty = ebay_product.quantity or 0
                ebay_product.availability_type = "IN_STOCK" if current_qty > 0 else "OUT_OF_STOCK"
                ebay_product.available_quantity = current_qty
                ebay_product.status = "active" if current_qty > 0 else "inactive"
                return

            # Find offer for configured marketplace, or take first one
            selected_offer = next(
                (o for o in offers if o.get("marketplaceId") == ebay_product.marketplace_id),
                offers[0],
            )

            self._apply_offer_data(ebay_product, selected_offer)

        except Exception as e:
            logger.warning(f"Could not enrich product {ebay_product.ebay_sku}: {e}", exc_info=True)

    def _apply_offer_data(self, ebay_product: EbayProduct, offer: dict) -> None:
        """Apply offer data to an eBay product."""
        ebay_product.ebay_offer_id = offer.get("offerId")
        ebay_product.marketplace_id = offer.get("marketplaceId", ebay_product.marketplace_id)

        # Listing details
        listing = offer.get("listing", {})
        ebay_product.ebay_listing_id = listing.get("listingId")
        ebay_product.sold_quantity = listing.get("soldQuantity")

        # Price from offer
        pricing = offer.get("pricingSummary", {})
        price_obj = pricing.get("price", {})
        if price_obj:
            ebay_product.price = float(price_obj.get("value", 0))
            ebay_product.currency = price_obj.get("currency", "EUR")

        # Listing format and duration
        ebay_product.listing_format = offer.get("format")
        ebay_product.listing_duration = offer.get("listingDuration")

        # Categories
        ebay_product.category_id = offer.get("categoryId")
        ebay_product.secondary_category_id = offer.get("secondaryCategoryId")

        # Location
        ebay_product.merchant_location_key = offer.get("merchantLocationKey")

        # Quantity details
        ebay_product.available_quantity = offer.get("availableQuantity")

        # Fallback: calculate available_quantity from inventory minus sold
        if ebay_product.available_quantity is None:
            current_qty = ebay_product.quantity or 0
            sold_qty = ebay_product.sold_quantity or 0
            ebay_product.available_quantity = max(0, current_qty - sold_qty)
            logger.debug(
                f"[Enrich] Calculated available_quantity={ebay_product.available_quantity} "
                f"for SKU {ebay_product.ebay_sku} (qty={current_qty}, sold={sold_qty})"
            )

        ebay_product.lot_size = offer.get("lotSize")
        ebay_product.quantity_limit_per_buyer = offer.get("quantityLimitPerBuyer")

        # Listing description (may differ from product description)
        ebay_product.listing_description = offer.get("listingDescription")

        # Update availability_type based on current quantity
        current_qty = ebay_product.quantity or 0
        ebay_product.availability_type = "IN_STOCK" if current_qty > 0 else "OUT_OF_STOCK"

        # Status from offer
        self._apply_offer_status(ebay_product, offer)

        ebay_product.last_synced_at = utc_now()

    def _apply_offer_status(self, ebay_product: EbayProduct, offer: dict) -> None:
        """Determine product status from offer and listing status."""
        offer_status = offer.get("status")
        listing = offer.get("listing", {})
        listing_status = listing.get("listingStatus")

        if offer_status == "PUBLISHED":
            if listing_status == "OUT_OF_STOCK":
                ebay_product.status = "inactive"
            else:
                ebay_product.status = "active"
                ebay_product.published_at = utc_now()
        elif offer_status == "UNPUBLISHED":
            ebay_product.status = "inactive"
        elif offer_status == "ENDED":
            ebay_product.status = "ended"
        else:
            logger.warning(
                f"[Enrich] Unknown offer status '{offer_status}' for SKU {ebay_product.ebay_sku}"
            )

    def enrich_products_batch(
        self,
        limit: int = 100,
        only_without_price: bool = True,
    ) -> dict:
        """
        Enrich products with offer data in batches.

        Args:
            limit: Max number of products to enrich
            only_without_price: If True, only enrich products without a price

        Returns:
            dict with 'enriched', 'errors', 'remaining', 'details'
        """
        results = {
            "enriched": 0,
            "errors": 0,
            "remaining": 0,
            "details": [],
        }

        query = self.db.query(EbayProduct)
        if only_without_price:
            query = query.filter(EbayProduct.price.is_(None))

        results["remaining"] = query.count()
        products = query.limit(limit).all()

        for product in products:
            try:
                self.enrich_with_offers(product)
                results["enriched"] += 1
                results["details"].append({
                    "sku": product.ebay_sku,
                    "status": "enriched",
                    "price": product.price,
                })
            except Exception as e:
                logger.warning(f"Error enriching {product.ebay_sku}: {e}", exc_info=True)
                results["errors"] += 1
                results["details"].append({
                    "sku": product.ebay_sku,
                    "status": "error",
                    "error": str(e),
                })

        try:
            self.db.commit()
            results["remaining"] -= results["enriched"]
        except Exception as e:
            logger.error(f"Error committing enrichment: {e}", exc_info=True)
            self.db.rollback()
            raise

        return results

    def enrich_all_with_offers(self, batch_size: int = 100) -> dict:
        """
        Enrich ALL products with Offer API data.

        This is the second step of a full_sync().

        Args:
            batch_size: Commit every N products

        Returns:
            dict with 'enriched', 'errors', 'total'
        """
        results = {
            "enriched": 0,
            "errors": 0,
            "total": 0,
        }

        products = self.db.query(EbayProduct).all()
        results["total"] = len(products)

        logger.info(f"[EnrichOffers] Starting enrichment for {len(products)} products")

        for i, product in enumerate(products):
            if self.job:
                self.db.refresh(self.job)
                if self.job.cancel_requested or self.job.status == JobStatus.CANCELLED:
                    logger.info(f"[EnrichOffers] Job cancelled at {i}/{len(products)}")
                    self.db.commit()
                    return {**results, "status": "cancelled"}

            try:
                self.enrich_with_offers(product)
                results["enriched"] += 1
            except Exception as e:
                logger.warning(f"[EnrichOffers] Error enriching {product.ebay_sku}: {e}", exc_info=True)
                results["errors"] += 1

            if (i + 1) % batch_size == 0:
                try:
                    self.db.commit()
                    logger.info(f"[EnrichOffers] Progress: {i + 1}/{len(products)} products")
                except Exception as e:
                    logger.error(f"[EnrichOffers] Error committing batch: {e}", exc_info=True)
                    self.db.rollback()

        try:
            self.db.commit()
            logger.info(
                f"[EnrichOffers] Completed: {results['enriched']} enriched, "
                f"{results['errors']} errors"
            )
        except Exception as e:
            logger.error(f"[EnrichOffers] Error committing: {e}", exc_info=True)
            self.db.rollback()
            raise

        return results

    def refresh_aspects_batch(self, limit: int = 100) -> dict:
        """
        Re-extract aspects (brand, color, size, material) from existing products.

        Useful after updating the multi-language aspect mapping.

        Args:
            limit: Max number of products to process

        Returns:
            dict with 'updated', 'errors', 'remaining'
        """
        results = {"updated": 0, "errors": 0, "remaining": 0}

        query = self.db.query(EbayProduct).filter(
            EbayProduct.aspects.isnot(None),
            EbayProduct.brand.is_(None),
        )
        results["remaining"] = query.count()
        products = query.limit(limit).all()

        for product in products:
            try:
                aspects = json.loads(product.aspects) if product.aspects else {}

                product.brand = self._get_aspect_by_key(aspects, "brand")
                product.color = self._get_aspect_by_key(aspects, "color")
                product.size = self._get_aspect_by_key(aspects, "size")
                product.material = self._get_aspect_by_key(aspects, "material")

                results["updated"] += 1
            except Exception as e:
                logger.warning(f"Error refreshing aspects for {product.ebay_sku}: {e}", exc_info=True)
                results["errors"] += 1

        try:
            self.db.commit()
            results["remaining"] -= results["updated"]
        except Exception as e:
            logger.error(f"Error committing aspect refresh: {e}", exc_info=True)
            self.db.rollback()
            raise

        return results
