"""
eBay Background Import Service

Handles background tasks for eBay product import and enrichment.
Extracted from api/ebay/products.py for better separation of concerns.

Features:
- Import products from eBay Inventory API
- Parallel enrichment with offer data
- Job progress tracking

Note: Uses its own DB session since background tasks run outside request lifecycle.

Created: 2026-01-20
Author: Claude
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from models.user.marketplace_job import JobStatus, MarketplaceJob
from services.ebay.ebay_importer import EbayImporter
from shared.database import SessionLocal
from shared.datetime_utils import utc_now
from shared.logging import get_logger
from shared.schema import configure_schema_translate_map

logger = get_logger(__name__)

# Constants
ENRICHMENT_BATCH_SIZE = 30  # Number of parallel API calls for enrichment


class EbayBackgroundImportService:
    """
    Service for running eBay import operations in background tasks.

    Note: Creates its own DB session since it runs outside the request lifecycle.
    """

    def __init__(self, user_id: int, marketplace_id: str = "EBAY_FR"):
        """
        Initialize background import service.

        Args:
            user_id: User ID for schema isolation
            marketplace_id: eBay marketplace ID (default: EBAY_FR)
        """
        self.user_id = user_id
        self.marketplace_id = marketplace_id
        self.schema_name = f"user_{user_id}"

    def run_import(self, job_id: int) -> None:
        """
        Execute import in background task with its own DB session.

        Optimized: imports products first, then enriches in parallel batches.

        Args:
            job_id: MarketplaceJob ID for progress tracking
        """
        db = SessionLocal()
        try:
            self._configure_schema(db)
            logger.info(f"[Background Import] Schema configured: {self.schema_name}")

            # Get the job
            job = db.query(MarketplaceJob).filter(MarketplaceJob.id == job_id).first()
            if not job:
                logger.error(f"[Background Import] Job #{job_id} not found")
                return

            # Initialize progress
            job.result_data = {"current": 0, "label": "initialisation..."}
            db.commit()
            self._configure_schema(db)

            # Create importer
            importer = EbayImporter(
                db=db,
                user_id=self.user_id,
                marketplace_id=self.marketplace_id,
            )

            # Process inventory page by page
            imported_count = self._import_all_pages(db, importer, job_id)

            # Cleanup: delete products without listing_id
            deleted_count = self._cleanup_products_without_listing(db)

            # Mark job as completed
            final_count = imported_count - deleted_count
            self._update_job_completed(db, job_id, final_count)

            logger.info(
                f"[Background Import] eBay import completed for user {self.user_id}: "
                f"{final_count} products (deleted {deleted_count} without listing)"
            )

        except Exception as e:
            logger.error(f"[Background Import] eBay import failed for user {self.user_id}: {e}", exc_info=True)
            self._mark_job_failed(db, job_id, str(e))

        finally:
            db.close()

    def run_enrichment(self, marketplace_id: Optional[str] = None) -> None:
        """
        Execute enrichment in background after import completes.

        Args:
            marketplace_id: Optional marketplace override
        """
        marketplace = marketplace_id or self.marketplace_id
        db = SessionLocal()
        try:
            self._configure_schema(db)

            importer = EbayImporter(
                db=db,
                user_id=self.user_id,
                marketplace_id=marketplace,
            )

            # Enrich all products without price
            result = importer.enrichment.enrich_products_batch(limit=50000, only_without_price=True)

            logger.info(
                f"[Background Enrich] eBay enrichment for user {self.user_id}: "
                f"enriched={result['enriched']}, errors={result['errors']}, "
                f"remaining={result['remaining']}"
            )

        except Exception as e:
            logger.error(f"[Background Enrich] eBay enrichment failed for user {self.user_id}: {e}", exc_info=True)

        finally:
            db.close()

    def _configure_schema(self, db: Session) -> None:
        """Configure DB session for user schema."""
        configure_schema_translate_map(db, self.schema_name)
        db.execute(text(f"SET search_path TO {self.schema_name}, public"))

    def _import_all_pages(self, db: Session, importer: EbayImporter, job_id: int) -> int:
        """
        Import all inventory pages and enrich products.

        Returns:
            Total number of imported products
        """
        imported_count = 0
        offset = 0
        limit = 100

        while True:
            # Fetch one page of inventory
            result = importer.inventory_client.get_inventory_items(limit=limit, offset=offset)
            items = result.get("inventoryItems", [])

            if not items:
                break

            # Import items WITHOUT enrichment first (fast)
            page_products = self._import_page(db, importer, items)

            # Enrich in parallel batches
            for i in range(0, len(page_products), ENRICHMENT_BATCH_SIZE):
                self._configure_schema(db)
                batch = page_products[i : i + ENRICHMENT_BATCH_SIZE]

                # Parallel enrichment
                self._enrich_products_parallel(importer, batch, db)
                self._configure_schema(db)

                # Update progress
                imported_count += len(batch)
                self._update_job_progress(db, job_id, imported_count)
                logger.info(f"[Background Import] Progress: {imported_count} products enriched")

            # Check if more pages
            total = result.get("total", 0)
            logger.info(
                f"[Background Import] Processed page (offset={offset}), "
                f"total={total}, imported={imported_count}"
            )

            if offset + limit >= total:
                break

            offset += limit

        return imported_count

    def _import_page(self, db: Session, importer: EbayImporter, items: list) -> list:
        """
        Import a page of inventory items.

        Returns:
            List of EbayProduct objects successfully imported
        """
        page_products = []
        logger.info(f"[Background Import] Processing {len(items)} items from API")

        for idx, item in enumerate(items):
            sku = item.get("sku", "unknown")
            logger.debug(f"[Background Import] Item {idx + 1}/{len(items)}: SKU={sku}")

            try:
                import_result = importer._import_single_item(item, enrich=False)
                logger.debug(
                    f"[Background Import] _import_single_item result: "
                    f"status={import_result['status']}, id={import_result.get('id')}"
                )

                if import_result["status"] in ["imported", "updated"]:
                    product = import_result.get("product")
                    if product:
                        page_products.append(product)
                        logger.debug(f"[Background Import] Added product ID={product.id} to batch")
                    else:
                        logger.warning(
                            f"[Background Import] No product object in result for SKU={sku}"
                        )

            except Exception as e:
                logger.error(
                    f"[Background Import] Failed to import item SKU={sku}: "
                    f"{type(e).__name__}: {e}"
                )
                db.rollback()
                self._configure_schema(db)

        db.commit()
        self._configure_schema(db)
        return page_products

    def _enrich_products_parallel(
        self, importer: EbayImporter, products: list, db: Session, max_workers: int = 10
    ) -> int:
        """
        Enrich products with offers data in parallel.

        API calls are made in parallel threads, but DB writes happen in main thread
        (SQLAlchemy sessions are not thread-safe).

        Returns:
            Number of products successfully enriched
        """
        if not products:
            return 0

        # Pre-fetch access token BEFORE parallel threads
        try:
            _ = importer.offer_client.get_access_token()
            logger.debug("[Enrich Parallel] Token pre-fetched")
        except Exception as e:
            logger.warning(f"[Enrich Parallel] Token pre-fetch failed: {e}", exc_info=True)

        # Build SKU to product mapping
        sku_to_product = {p.ebay_sku: p for p in products}
        skus = list(sku_to_product.keys())

        def fetch_offer_for_sku(sku: str):
            """Fetch offer for a SKU (thread-safe - only API call, no DB)."""
            try:
                offers = importer.fetch_offers_for_sku(sku)
                return (sku, offers)
            except Exception as e:
                logger.warning(f"Failed to fetch offer for SKU {sku}: {e}", exc_info=True)
                return (sku, None)

        # Collect results from parallel API calls
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_offer_for_sku, sku): sku for sku in skus}

            for future in as_completed(futures):
                try:
                    sku, offers = future.result()
                    if offers:
                        results.append((sku, offers))
                except Exception as e:
                    logger.warning(f"Error fetching offer: {e}", exc_info=True)

        # Apply results in main thread (thread-safe DB access)
        enriched_count = 0
        for sku, offers in results:
            product = sku_to_product.get(sku)
            if product and offers:
                self._apply_offer_to_product(product, offers)
                enriched_count += 1

        db.commit()
        return enriched_count

    def _apply_offer_to_product(self, product, offers: list) -> None:
        """Apply offer data to a product."""
        if not offers:
            return

        # Select best offer (prefer configured marketplace)
        selected_offer = None
        for offer in offers:
            if offer.get("marketplaceId") == self.marketplace_id:
                selected_offer = offer
                break
        if not selected_offer:
            selected_offer = offers[0]

        # Update product with offer data
        product.ebay_offer_id = selected_offer.get("offerId")
        product.marketplace_id = selected_offer.get("marketplaceId", self.marketplace_id)

        # Listing details
        listing = selected_offer.get("listing", {})
        product.ebay_listing_id = listing.get("listingId")
        product.sold_quantity = listing.get("soldQuantity")

        # Price from offer
        pricing = selected_offer.get("pricingSummary", {})
        price_obj = pricing.get("price", {})
        if price_obj:
            product.price = float(price_obj.get("value", 0))
            product.currency = price_obj.get("currency", "EUR")

        # Listing format and duration
        product.listing_format = selected_offer.get("format")
        product.listing_duration = selected_offer.get("listingDuration")

        # Categories
        product.category_id = selected_offer.get("categoryId")
        product.secondary_category_id = selected_offer.get("secondaryCategoryId")

        # Location
        product.merchant_location_key = selected_offer.get("merchantLocationKey")

        # Quantity details
        product.available_quantity = selected_offer.get("availableQuantity")
        product.lot_size = selected_offer.get("lotSize")
        product.quantity_limit_per_buyer = selected_offer.get("quantityLimitPerBuyer")

        # Listing description
        product.listing_description = selected_offer.get("listingDescription")

        # Status from offer
        offer_status = selected_offer.get("status")
        if offer_status == "PUBLISHED":
            product.status = "active"
            product.published_at = utc_now()
        elif offer_status == "ENDED":
            product.status = "ended"

    def _cleanup_products_without_listing(self, db: Session) -> int:
        """
        Delete products without listing_id (inventory items without active listings).

        Returns:
            Number of deleted products
        """
        db.execute(text(f"SET search_path TO {self.schema_name}, public"))
        cleanup_result = db.execute(text("DELETE FROM ebay_products WHERE ebay_listing_id IS NULL"))
        deleted_count = cleanup_result.rowcount
        db.commit()

        if deleted_count > 0:
            logger.info(
                f"[Background Import] Cleanup: deleted {deleted_count} products without listing_id"
            )

        return deleted_count

    def _update_job_progress(self, db: Session, job_id: int, current: int) -> None:
        """Update job progress in database."""
        db.execute(
            text("UPDATE marketplace_jobs SET result_data = :data WHERE id = :job_id"),
            {"data": f'{{"current": {current}, "label": "produits importés"}}', "job_id": job_id},
        )
        db.commit()

    def _update_job_completed(self, db: Session, job_id: int, final_count: int) -> None:
        """Mark job as completed."""
        db.execute(
            text(
                "UPDATE marketplace_jobs SET status = 'completed', result_data = :data "
                "WHERE id = :job_id"
            ),
            {
                "data": f'{{"current": {final_count}, "label": "produits importés"}}',
                "job_id": job_id,
            },
        )
        db.commit()

    def _mark_job_failed(self, db: Session, job_id: int, error_msg: str) -> None:
        """Mark job as failed."""
        try:
            safe_error = error_msg[:500].replace("'", "''")
            db.execute(
                text(
                    "UPDATE marketplace_jobs SET status = 'failed', error_message = :error "
                    "WHERE id = :job_id"
                ),
                {"error": safe_error, "job_id": job_id},
            )
            db.commit()
        except Exception as inner_e:
            logger.error(f"[Background Import] Could not mark job as failed: {inner_e}")


# Convenience functions for backward compatibility with router
def run_import_in_background(job_id: int, user_id: int, marketplace_id: str) -> None:
    """Run import in background (convenience function for router)."""
    service = EbayBackgroundImportService(user_id, marketplace_id)
    service.run_import(job_id)


def run_enrichment_in_background(user_id: int, marketplace_id: str) -> None:
    """Run enrichment in background (convenience function for router)."""
    service = EbayBackgroundImportService(user_id, marketplace_id)
    service.run_enrichment()
