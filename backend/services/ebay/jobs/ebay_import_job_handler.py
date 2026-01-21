"""
eBay Import Job Handler

Imports products from eBay Inventory API with enrichment.

Author: Claude
Date: 2026-01-20
"""

from typing import Any

from models.user.marketplace_job import JobStatus, MarketplaceJob
from services.marketplace.direct_api_job_handler import DirectAPIJobHandler
from services.ebay.ebay_importer import EbayImporter
from shared.logging_setup import get_logger
from shared.schema_utils import configure_schema_translate_map

logger = get_logger(__name__)


class EbayImportJobHandler(DirectAPIJobHandler):
    """
    Handler for importing products from eBay inventory.

    Imports all inventory items from eBay, then enriches with offers data.

    Action code: import_ebay
    """

    ACTION_CODE = "import_ebay"

    # Enrichment batch size for parallel API calls
    ENRICHMENT_BATCH_SIZE = 30

    async def execute(self, job: MarketplaceJob) -> dict[str, Any]:
        """
        Execute the eBay import job.

        Args:
            job: MarketplaceJob to execute

        Returns:
            Result dict with success status
        """
        from sqlalchemy import text
        from concurrent.futures import ThreadPoolExecutor, as_completed

        job_id = job.id
        user_id = self.user_id
        input_data = job.input_data or {}
        marketplace_id = input_data.get("marketplace_id", "EBAY_FR")
        schema_name = f"user_{user_id}"

        logger.info(f"[EbayImportHandler] Starting import for job #{job_id}, user {user_id}")

        try:
            # Configure schema
            configure_schema_translate_map(self.db, schema_name)
            self.db.execute(text(f"SET search_path TO {schema_name}, public"))

            # Update job progress
            job.result_data = {"current": 0, "label": "initialisation..."}
            self.db.commit()
            configure_schema_translate_map(self.db, schema_name)

            # Create importer
            importer = EbayImporter(
                db=self.db,
                user_id=user_id,
                marketplace_id=marketplace_id,
            )

            # Process inventory page by page
            imported_count = 0
            offset = 0
            limit = 100

            while True:
                # Check for cancellation
                if self.is_cancelled(job):
                    logger.info(f"[EbayImportHandler] Job #{job_id} cancelled")
                    return {"success": False, "error": "cancelled", "imported": imported_count}

                # Fetch one page of inventory
                configure_schema_translate_map(self.db, schema_name)
                self.db.execute(text(f"SET search_path TO {schema_name}, public"))

                result = importer.inventory_client.get_inventory_items(
                    limit=limit,
                    offset=offset
                )

                items = result.get("inventoryItems", [])
                if not items:
                    break

                # Import items WITHOUT enrichment first (fast)
                page_products = []
                logger.info(f"[EbayImportHandler] Processing {len(items)} items from API")

                for idx, item in enumerate(items):
                    sku = item.get("sku", "unknown")

                    # Check cancellation periodically
                    if idx % 10 == 0 and self.is_cancelled(job):
                        logger.info(f"[EbayImportHandler] Job #{job_id} cancelled during import")
                        return {"success": False, "error": "cancelled", "imported": imported_count}

                    configure_schema_translate_map(self.db, schema_name)
                    self.db.execute(text(f"SET search_path TO {schema_name}, public"))

                    try:
                        import_result = importer._import_single_item(item, enrich=False)

                        if import_result["status"] in ["imported", "updated"]:
                            product = import_result.get("product")
                            if product:
                                page_products.append(product)

                    except Exception as e:
                        logger.error(f"[EbayImportHandler] Failed to import SKU={sku}: {e}")
                        self.db.rollback()
                        configure_schema_translate_map(self.db, schema_name)
                        self.db.execute(text(f"SET search_path TO {schema_name}, public"))

                self.db.commit()
                configure_schema_translate_map(self.db, schema_name)
                self.db.execute(text(f"SET search_path TO {schema_name}, public"))

                # Enrich in parallel batches
                for i in range(0, len(page_products), self.ENRICHMENT_BATCH_SIZE):
                    # Check cancellation
                    if self.is_cancelled(job):
                        return {"success": False, "error": "cancelled", "imported": imported_count}

                    configure_schema_translate_map(self.db, schema_name)
                    self.db.execute(text(f"SET search_path TO {schema_name}, public"))

                    batch = page_products[i:i + self.ENRICHMENT_BATCH_SIZE]
                    self._enrich_products_parallel(importer, batch, schema_name)

                    configure_schema_translate_map(self.db, schema_name)
                    self.db.execute(text(f"SET search_path TO {schema_name}, public"))

                    # Update progress
                    imported_count += len(batch)
                    self.db.execute(
                        text("UPDATE marketplace_jobs SET result_data = :data WHERE id = :job_id"),
                        {"data": f'{{"current": {imported_count}, "label": "produits importés"}}', "job_id": job_id}
                    )
                    self.db.commit()

                    logger.info(f"[EbayImportHandler] Progress: {imported_count} products enriched")

                # Check if more pages
                total = result.get("total", 0)
                if offset + limit >= total:
                    break

                offset += limit

            # Cleanup: delete products without listing_id
            configure_schema_translate_map(self.db, schema_name)
            self.db.execute(text(f"SET search_path TO {schema_name}, public"))

            cleanup_result = self.db.execute(
                text("DELETE FROM ebay_products WHERE ebay_listing_id IS NULL")
            )
            deleted_count = cleanup_result.rowcount
            self.db.commit()

            if deleted_count > 0:
                logger.info(f"[EbayImportHandler] Cleanup: deleted {deleted_count} products without listing_id")

            final_count = imported_count - deleted_count

            logger.info(
                f"[EbayImportHandler] Import completed for job #{job_id}: "
                f"{final_count} products (deleted {deleted_count} without listing)"
            )

            return {
                "success": True,
                "imported": final_count,
                "deleted": deleted_count,
            }

        except Exception as e:
            logger.exception(f"[EbayImportHandler] Import failed for job #{job_id}: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def _enrich_products_parallel(
        self,
        importer: EbayImporter,
        products: list,
        schema_name: str,
        max_workers: int = 5,  # Reduced from 30 to avoid blocking the main process
    ) -> int:
        """
        Enrich products with offers data in parallel.

        API calls are made in parallel threads, but DB writes happen in main thread.

        Args:
            importer: EbayImporter instance
            products: List of EbayProduct objects to enrich
            schema_name: User schema name
            max_workers: Number of parallel workers

        Returns:
            int: Number of products successfully enriched
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from shared.datetime_utils import utc_now

        if not products:
            return 0

        # Pre-fetch access token BEFORE parallel threads
        try:
            _ = importer.offer_client.get_access_token()
        except Exception as e:
            logger.warning(f"[EbayImportHandler] Token pre-fetch failed: {e}")

        # Build SKU to product mapping
        sku_to_product = {p.ebay_sku: p for p in products}
        skus = list(sku_to_product.keys())

        def fetch_offer_for_sku(sku: str):
            """Fetch offer for a SKU (thread-safe - only API call, no DB)."""
            try:
                offers = importer.fetch_offers_for_sku(sku)
                return (sku, offers)
            except Exception as e:
                logger.warning(f"Failed to fetch offer for SKU {sku}: {e}")
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
                    logger.warning(f"Error fetching offer: {e}")

        # Apply results in main thread (thread-safe DB access)
        enriched_count = 0
        for sku, offers in results:
            product = sku_to_product.get(sku)
            if product and offers:
                self._apply_offer_to_product(product, offers, importer.marketplace_id)
                enriched_count += 1

        # Commit all enrichments at once
        self.db.commit()

        return enriched_count

    def _apply_offer_to_product(self, product, offers: list, marketplace_id: str):
        """Apply offer data to a product."""
        from shared.datetime_utils import utc_now

        if not offers:
            return

        # Select best offer (prefer configured marketplace)
        selected_offer = None
        for offer in offers:
            if offer.get("marketplaceId") == marketplace_id:
                selected_offer = offer
                break
        if not selected_offer:
            selected_offer = offers[0]

        # Update product with offer data
        product.ebay_offer_id = selected_offer.get("offerId")
        product.marketplace_id = selected_offer.get("marketplaceId", marketplace_id)

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
        api_available_qty = selected_offer.get("availableQuantity")
        sold_qty = listing.get("soldQuantity", 0) or 0

        if api_available_qty is not None:
            product.available_quantity = api_available_qty
        else:
            current_qty = product.quantity or 0
            product.available_quantity = max(0, current_qty - sold_qty)

        product.lot_size = selected_offer.get("lotSize")
        product.quantity_limit_per_buyer = selected_offer.get("quantityLimitPerBuyer")

        # Listing description
        product.listing_description = selected_offer.get("listingDescription")

        # Status and availability_type from offer
        offer_status = selected_offer.get("status")
        listing_status = listing.get("listingStatus")

        if offer_status == "PUBLISHED":
            if listing_status == "OUT_OF_STOCK" or product.available_quantity == 0:
                product.status = "inactive"
                product.availability_type = "OUT_OF_STOCK"
            else:
                product.status = "active"
                product.availability_type = "IN_STOCK"
                product.published_at = utc_now()
        elif offer_status == "ENDED":
            product.status = "ended"
            product.availability_type = "OUT_OF_STOCK"
        elif offer_status == "UNPUBLISHED":
            product.status = "inactive"
            product.availability_type = "OUT_OF_STOCK"
        else:
            if product.available_quantity == 0:
                product.status = "inactive"
                product.availability_type = "OUT_OF_STOCK"

    def get_service(self):
        """Not used for import handler."""
        return None

    def get_service_method_name(self) -> str:
        """Not used for import handler."""
        return ""

    def create_tasks(self, job: MarketplaceJob) -> list[str]:
        """Return empty task list."""
        return []
