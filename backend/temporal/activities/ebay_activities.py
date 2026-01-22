"""
eBay Sync Activities for Temporal.

These activities wrap the existing eBay sync logic to work with Temporal.
Each activity is designed to be:
- Idempotent where possible
- Retryable
- Independent (no shared state between activities)

Activities handle their own DB sessions since they run in the worker process.

Architecture:
- fetch_and_sync_page: Fetch one page from eBay and upsert directly to DB
- cleanup_orphan_products: Delete products not seen in current sync
- update_job_progress: Update job progress in DB
- mark_job_completed/failed: Update job status
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from temporalio import activity

from shared.database import SessionLocal
from shared.logging import get_logger
from shared.schema import configure_schema_translate_map

logger = get_logger(__name__)


def _get_schema_name(user_id: int) -> str:
    """Get schema name for user."""
    return f"user_{user_id}"


def _configure_session(db, user_id: int) -> None:
    """Configure DB session for user schema."""
    schema_name = _get_schema_name(user_id)
    configure_schema_translate_map(db, schema_name)
    db.execute(text(f"SET search_path TO {schema_name}, public"))


@activity.defn
async def fetch_and_sync_page(
    user_id: int,
    marketplace_id: str,
    limit: int,
    offset: int,
    sync_start_time: str,
) -> dict:
    """
    Fetch a page of inventory items from eBay and sync directly to DB.

    This activity:
    1. Fetches one page from eBay Inventory API
    2. For each item, upserts to ebay_products table (inventory data only)
    3. Updates last_synced_at to sync_start_time
    4. Returns only counts (not the items themselves)

    Note: Offer data (listing_id, price, etc.) is NOT fetched here to avoid
    100+ HTTP calls per page which would cause Temporal deadlock detection.
    Use the separate enrichProducts endpoint for offer enrichment.

    Args:
        user_id: User ID for OAuth credentials and schema
        marketplace_id: eBay marketplace (EBAY_FR, etc.)
        limit: Number of items per page
        offset: Page offset
        sync_start_time: ISO timestamp for this sync run

    Returns:
        Dict with 'synced', 'errors', 'total', 'has_more'
    """
    activity.logger.info(f"Fetching and syncing page: offset={offset}, limit={limit}")

    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        # Import here to avoid circular imports
        from models.user.ebay_product import EbayProduct
        from services.ebay.ebay_inventory_client import EbayInventoryClient
        from services.ebay.ebay_importer import EbayImporter

        # Parse sync_start_time
        sync_time = datetime.fromisoformat(sync_start_time.replace("Z", "+00:00"))

        # Fetch page from eBay
        client = EbayInventoryClient(db, user_id, marketplace_id)
        result = client.get_inventory_items(limit=limit, offset=offset)

        items = result.get("inventoryItems", [])
        total = result.get("total", 0)

        activity.logger.info(f"Fetched {len(items)} items (total={total}, offset={offset})")

        if not items:
            return {
                "synced": 0,
                "errors": 0,
                "total": total,
                "has_more": False,
            }

        # Initialize importer for data extraction
        importer = EbayImporter(db, user_id, marketplace_id)

        synced = 0
        errors = 0

        for item in items:
            try:
                sku = item.get("sku")
                if not sku:
                    continue

                # Extract product data from inventory item (no offer fetch)
                product_data = importer._extract_product_data(item)

                # Check if exists
                existing = db.query(EbayProduct).filter(EbayProduct.ebay_sku == sku).first()

                if existing:
                    # UPDATE existing product
                    for key, value in product_data.items():
                        if hasattr(existing, key) and value is not None:
                            setattr(existing, key, value)
                    existing.last_synced_at = sync_time
                    existing.updated_at = sync_time
                else:
                    # INSERT new product
                    product = EbayProduct(
                        ebay_sku=sku,
                        **product_data,
                        last_synced_at=sync_time,
                    )
                    db.add(product)

                synced += 1

            except Exception as e:
                activity.logger.warning(f"Error syncing SKU={item.get('sku')}: {e}")
                errors += 1
                db.rollback()
                _configure_session(db, user_id)

        db.commit()

        # Check if there are more pages
        has_more = (offset + len(items)) < total

        activity.logger.info(
            f"Page synced: synced={synced}, errors={errors}, has_more={has_more}"
        )

        return {
            "synced": synced,
            "errors": errors,
            "total": total,
            "has_more": has_more,
        }

    finally:
        db.close()


def _apply_offer_to_product(product, offer: dict, marketplace_id: str) -> None:
    """Apply offer data to a product."""
    if not offer:
        return

    product.ebay_offer_id = offer.get("offerId")
    product.marketplace_id = offer.get("marketplaceId", marketplace_id)

    # Listing details
    listing = offer.get("listing", {})
    product.ebay_listing_id = listing.get("listingId")
    product.sold_quantity = listing.get("soldQuantity")

    # Price
    pricing = offer.get("pricingSummary", {})
    price_obj = pricing.get("price", {})
    if price_obj:
        product.price = float(price_obj.get("value", 0))
        product.currency = price_obj.get("currency", "EUR")

    # Listing format
    product.listing_format = offer.get("format")
    product.listing_duration = offer.get("listingDuration")

    # Categories
    product.category_id = offer.get("categoryId")
    product.secondary_category_id = offer.get("secondaryCategoryId")

    # Location & quantity
    product.merchant_location_key = offer.get("merchantLocationKey")
    product.available_quantity = offer.get("availableQuantity")
    product.lot_size = offer.get("lotSize")
    product.quantity_limit_per_buyer = offer.get("quantityLimitPerBuyer")
    product.listing_description = offer.get("listingDescription")

    # Status based on offer status
    offer_status = offer.get("status")
    if offer_status == "PUBLISHED":
        product.status = "active"
        if not product.published_at:
            product.published_at = datetime.now(timezone.utc)
    elif offer_status == "ENDED":
        product.status = "ended"


@activity.defn
async def enrich_single_product(
    user_id: int,
    marketplace_id: str,
    sku: str,
) -> dict:
    """
    Enrich a single product with offer data (price, listing_id, etc.).

    Args:
        user_id: User ID for schema isolation
        marketplace_id: eBay marketplace ID
        sku: Product SKU to enrich

    Returns:
        Dict with 'success' bool and 'sku'
    """
    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from models.user.ebay_product import EbayProduct
        from services.ebay.ebay_offer_client import EbayOfferClient

        product = db.query(EbayProduct).filter(EbayProduct.ebay_sku == sku).first()
        if not product:
            return {"success": False, "sku": sku, "error": "not_found"}

        client = EbayOfferClient(db, user_id, marketplace_id)

        try:
            # Get offers for this SKU
            result = client.get_offers(sku=sku)
            offers = result.get("offers", [])

            if offers:
                # Use first offer (typically one offer per SKU per marketplace)
                offer = offers[0]
                _apply_offer_to_product(product, offer, marketplace_id)
                db.commit()
                return {"success": True, "sku": sku}
            else:
                return {"success": False, "sku": sku, "error": "no_offer"}
        except Exception as e:
            return {"success": False, "sku": sku, "error": str(e)[:100]}

    finally:
        db.close()


@activity.defn
async def get_skus_to_enrich(
    user_id: int,
    sync_start_time: str,
    limit: int = 30,
    offset: int = 0,
) -> list:
    """
    Get a batch of SKUs to enrich from the current sync session.

    Args:
        user_id: User ID for schema isolation
        sync_start_time: ISO timestamp - only products synced at/after this time
        limit: Max SKUs to return
        offset: Pagination offset

    Returns:
        List of SKUs to enrich
    """
    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from models.user.ebay_product import EbayProduct

        # Parse sync_start_time
        sync_time = datetime.fromisoformat(sync_start_time.replace("Z", "+00:00"))

        # Get products synced in this session (all of them, not just those without listing_id)
        products = (
            db.query(EbayProduct.ebay_sku)
            .filter(EbayProduct.last_synced_at >= sync_time)
            .order_by(EbayProduct.id)
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [p.ebay_sku for p in products]

    finally:
        db.close()


@activity.defn
async def cleanup_orphan_products(
    user_id: int,
    sync_start_time: str,
    marketplace_id: str = "EBAY_FR",
) -> dict:
    """
    Delete orphan products that were not seen in the current sync.

    SAFETY: Only deletes products WITHOUT a listing_id (no active listing).
    Products with an active listing are NEVER deleted to avoid data loss.

    For each orphan:
    1. Delete from eBay inventory (API call)
    2. Delete from local database

    Args:
        user_id: User ID for schema isolation
        sync_start_time: ISO timestamp when sync started
        marketplace_id: eBay marketplace for API calls

    Returns:
        Dict with 'deleted' and 'errors' counts
    """
    activity.logger.info(f"Cleaning up orphan products for user {user_id}")

    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from models.user.ebay_product import EbayProduct
        from services.ebay.ebay_inventory_client import EbayInventoryClient

        # Parse sync_start_time
        sync_time = datetime.fromisoformat(sync_start_time.replace("Z", "+00:00"))

        # Find orphan products:
        # - Not seen in this sync (last_synced_at < sync_start_time)
        # - AND no active listing (listing_id IS NULL)
        # Products WITH listing_id are NEVER deleted for safety
        orphans = db.query(EbayProduct).filter(
            EbayProduct.last_synced_at < sync_time,
            EbayProduct.ebay_listing_id.is_(None),
        ).all()

        activity.logger.info(
            f"Found {len(orphans)} orphan products without listing to cleanup"
        )

        deleted_count = 0
        error_count = 0

        if orphans:
            # Initialize eBay client for deletion
            client = EbayInventoryClient(db, user_id, marketplace_id)

            for orphan in orphans:
                sku = orphan.ebay_sku
                try:
                    # Step 1: Delete from eBay inventory
                    activity.logger.debug(f"Deleting SKU={sku} from eBay inventory")
                    client.delete_inventory_item(sku)

                    # Step 2: Delete from local DB
                    db.delete(orphan)
                    deleted_count += 1

                    activity.logger.debug(f"Deleted orphan: SKU={sku}")

                except Exception as e:
                    # Log error but continue with other deletions
                    activity.logger.warning(
                        f"Failed to delete SKU={sku} from eBay: {e}"
                    )
                    error_count += 1
                    # Still delete from local DB if eBay deletion fails
                    # (product might already be gone from eBay)
                    db.delete(orphan)
                    deleted_count += 1

            db.commit()

        activity.logger.info(
            f"Cleanup complete: deleted {deleted_count} orphan products, "
            f"{error_count} eBay API errors"
        )

        return {"deleted": deleted_count, "errors": error_count}

    finally:
        db.close()


@activity.defn
async def update_job_progress(
    user_id: int,
    job_id: int,
    current: int,
    label: str,
) -> None:
    """
    Update job progress in the database.

    Args:
        user_id: User ID for schema isolation
        job_id: MarketplaceJob ID
        current: Current progress count
        label: Progress label text
    """
    db = SessionLocal()
    try:
        schema_name = _get_schema_name(user_id)
        db.execute(text(f"SET search_path TO {schema_name}, public"))

        import json

        data = json.dumps({"current": current, "label": label})

        db.execute(
            text("UPDATE marketplace_jobs SET result_data = :data WHERE id = :job_id"),
            {"data": data, "job_id": job_id},
        )
        db.commit()

        activity.logger.debug(f"Job #{job_id} progress: {current} - {label}")

    finally:
        db.close()


@activity.defn
async def mark_job_completed(
    user_id: int,
    job_id: int,
    final_count: int,
) -> None:
    """
    Mark job as completed.

    Args:
        user_id: User ID for schema isolation
        job_id: MarketplaceJob ID
        final_count: Final synced product count
    """
    db = SessionLocal()
    try:
        schema_name = _get_schema_name(user_id)
        db.execute(text(f"SET search_path TO {schema_name}, public"))

        import json

        data = json.dumps({"current": final_count, "label": "produits synchronisés"})

        db.execute(
            text(
                "UPDATE marketplace_jobs SET status = 'completed', result_data = :data "
                "WHERE id = :job_id"
            ),
            {"data": data, "job_id": job_id},
        )
        db.commit()

        activity.logger.info(f"Job #{job_id} completed: {final_count} products")

    finally:
        db.close()


@activity.defn
async def mark_job_failed(
    user_id: int,
    job_id: int,
    error_msg: str,
) -> None:
    """
    Mark job as failed.

    Args:
        user_id: User ID for schema isolation
        job_id: MarketplaceJob ID
        error_msg: Error message
    """
    db = SessionLocal()
    try:
        schema_name = _get_schema_name(user_id)
        db.execute(text(f"SET search_path TO {schema_name}, public"))

        safe_error = error_msg[:500]

        db.execute(
            text(
                "UPDATE marketplace_jobs SET status = 'failed', error_message = :error "
                "WHERE id = :job_id"
            ),
            {"error": safe_error, "job_id": job_id},
        )
        db.commit()

        activity.logger.info(f"Job #{job_id} failed: {safe_error}")

    finally:
        db.close()


# Export all activities for registration
EBAY_ACTIVITIES = [
    fetch_and_sync_page,
    cleanup_orphan_products,
    update_job_progress,
    mark_job_completed,
    mark_job_failed,
    enrich_single_product,
    get_skus_to_enrich,
]
