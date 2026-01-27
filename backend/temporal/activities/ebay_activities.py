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

IMPORTANT: Activities are defined as regular `def` (not `async def`) because:
- The eBay client uses `requests` (synchronous HTTP library)
- Temporal executes sync activities in a threadpool (max_concurrent_activities threads)
- This allows true parallel execution (50 concurrent HTTP calls)
- Using `async def` with sync code would block the event loop = no parallelism
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
def fetch_and_sync_page(
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
def enrich_single_product(
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
                # Mark as enriched to skip in future syncs (within 12h window)
                product.last_enriched_at = datetime.now(timezone.utc)
                db.commit()
                return {"success": True, "sku": sku}
            else:
                # No offer found, but still mark as enriched to avoid retrying
                product.last_enriched_at = datetime.now(timezone.utc)
                db.commit()
                return {"success": False, "sku": sku, "error": "no_offer"}
        except Exception as e:
            # Mark as enriched even on error to avoid infinite retry loop
            product.last_enriched_at = datetime.now(timezone.utc)
            db.commit()
            return {"success": False, "sku": sku, "error": str(e)[:100]}

    finally:
        db.close()


@activity.defn
def get_skus_to_enrich(
    user_id: int,
    sync_start_time: str,
    limit: int = 30,
    offset: int = 0,
) -> list:
    """
    Get a batch of SKUs to enrich from the current sync session.

    Skips products that were enriched less than 12 hours ago.

    Args:
        user_id: User ID for schema isolation
        sync_start_time: ISO timestamp - only products synced at/after this time
        limit: Max SKUs to return
        offset: Pagination offset

    Returns:
        List of SKUs to enrich
    """
    from datetime import timedelta
    from sqlalchemy import or_

    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from models.user.ebay_product import EbayProduct

        # Parse sync_start_time
        sync_time = datetime.fromisoformat(sync_start_time.replace("Z", "+00:00"))

        # Skip products enriched less than 12 hours ago
        enrich_threshold = datetime.now(timezone.utc) - timedelta(hours=12)

        # Get products synced in this session that need enrichment:
        # - last_enriched_at is NULL (never enriched)
        # - OR last_enriched_at < 12 hours ago (stale)
        products = (
            db.query(EbayProduct.ebay_sku)
            .filter(EbayProduct.last_synced_at >= sync_time)
            .filter(
                or_(
                    EbayProduct.last_enriched_at.is_(None),
                    EbayProduct.last_enriched_at < enrich_threshold,
                )
            )
            .order_by(EbayProduct.id)
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [p.ebay_sku for p in products]

    finally:
        db.close()


@activity.defn
def get_skus_to_delete(
    user_id: int,
    limit: int = 500,
    offset: int = 0,
) -> list:
    """
    Get a batch of SKUs to delete (products without listing_id).

    SAFETY: Only returns products WITHOUT a listing_id (no active listing).
    Products with an active listing are NEVER deleted to avoid data loss.

    Args:
        user_id: User ID for schema isolation
        limit: Max SKUs to return
        offset: Pagination offset

    Returns:
        List of SKUs to delete
    """
    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from models.user.ebay_product import EbayProduct

        # Find orphan products: no active listing (listing_id IS NULL)
        products = (
            db.query(EbayProduct.ebay_sku)
            .filter(EbayProduct.ebay_listing_id.is_(None))
            .order_by(EbayProduct.id)
            .offset(offset)
            .limit(limit)
            .all()
        )

        skus = [p.ebay_sku for p in products]
        activity.logger.info(f"Found {len(skus)} products to delete (offset={offset})")

        return skus

    finally:
        db.close()


@activity.defn
def delete_single_product(
    user_id: int,
    marketplace_id: str,
    sku: str,
) -> dict:
    """
    Delete a single product from eBay inventory and local DB.

    Args:
        user_id: User ID for schema isolation
        marketplace_id: eBay marketplace for API calls
        sku: Product SKU to delete

    Returns:
        Dict with 'success' bool and 'sku'
    """
    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from models.user.ebay_product import EbayProduct
        from services.ebay.ebay_inventory_client import EbayInventoryClient

        product = db.query(EbayProduct).filter(EbayProduct.ebay_sku == sku).first()
        if not product:
            return {"success": False, "sku": sku, "error": "not_found"}

        client = EbayInventoryClient(db, user_id, marketplace_id)

        try:
            # Step 1: Delete from eBay inventory
            client.delete_inventory_item(sku)
        except Exception as e:
            # Log but continue - product might already be gone from eBay
            activity.logger.warning(f"eBay API delete failed for SKU={sku}: {e}")

        # Step 2: Delete from local DB (always, even if eBay API failed)
        db.delete(product)
        db.commit()

        activity.logger.debug(f"Deleted product: SKU={sku}")
        return {"success": True, "sku": sku}

    except Exception as e:
        activity.logger.error(f"Failed to delete SKU={sku}: {e}")
        return {"success": False, "sku": sku, "error": str(e)[:100]}

    finally:
        db.close()


@activity.defn
def sync_sold_status(user_id: int) -> dict:
    """
    Sync sold status from eBay to StoFlow products.

    Creates pending actions for eBay products with sold_quantity >= 1.
    Any product that has been sold at least once is considered no longer
    available, regardless of current eBay quantity.

    Args:
        user_id: User ID for schema isolation

    Returns:
        Dict with 'pending_count' and 'product_ids' affected
    """
    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from services.pending_action_service import PendingActionService
        from models.user.pending_action import PendingActionType

        # Find eBay products with sold_quantity >= 1 (sold at least once)
        # Exclude products already SOLD or PENDING_DELETION
        # Use DISTINCT ON to avoid duplicate pending actions for same product
        result = db.execute(
            text("""
                SELECT DISTINCT ON (ep.product_id)
                       ep.ebay_sku, ep.product_id, ep.title, ep.sold_quantity,
                       ep.price, p.status::text as stoflow_status
                FROM ebay_products ep
                JOIN products p ON p.id = ep.product_id
                WHERE ep.sold_quantity >= 1
                  AND ep.product_id IS NOT NULL
                  AND p.status::text NOT IN ('SOLD', 'PENDING_DELETION')
                ORDER BY ep.product_id, ep.sold_quantity DESC
            """)
        ).fetchall()

        if not result:
            activity.logger.info("No products to update - all sold statuses are in sync")
            return {"pending_count": 0, "product_ids": []}

        # Create pending actions for each product
        service = PendingActionService(db)
        product_ids = []

        for sku, product_id, title, sold_qty, price, stoflow_status in result:
            action = service.create_pending_action(
                product_id=product_id,
                action_type=PendingActionType.MARK_SOLD,
                marketplace="ebay",
                reason=f"Produit vendu sur eBay (SKU={sku}, qty vendue={sold_qty})",
                context_data={
                    "ebay_sku": sku,
                    "title": title,
                    "sold_quantity": sold_qty,
                    "price": float(price) if price else None,
                    "previous_status": stoflow_status,
                },
            )
            if action:
                product_ids.append(product_id)
                activity.logger.info(
                    f"Created pending action for StoFlow #{product_id} "
                    f"(eBay SKU={sku} sold_qty={sold_qty}, was {stoflow_status})"
                )

        db.commit()

        activity.logger.info(
            f"Created {len(product_ids)} pending actions for sold eBay products"
        )

        return {
            "pending_count": len(product_ids),
            "product_ids": product_ids,
        }

    finally:
        db.close()


@activity.defn
def get_skus_sold_elsewhere(user_id: int, batch_size: int = 500) -> list:
    """
    Get SKUs of eBay products that are SOLD on Stoflow but not sold on eBay.

    These are products sold elsewhere (Vinted, etc.) that should be deleted from eBay.

    Criteria:
    - Stoflow product status = SOLD
    - eBay sold_quantity is NULL or < 1 (not sold on eBay)

    Args:
        user_id: User ID for schema isolation
        batch_size: Max SKUs to return

    Returns:
        List of SKUs to delete
    """
    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        result = db.execute(
            text("""
                SELECT ep.ebay_sku
                FROM ebay_products ep
                JOIN products p ON p.id = ep.product_id
                WHERE p.status::text = 'SOLD'
                  AND ep.product_id IS NOT NULL
                  AND (ep.sold_quantity IS NULL OR ep.sold_quantity < 1)
                LIMIT :batch_size
            """),
            {"batch_size": batch_size}
        ).fetchall()

        skus = [row[0] for row in result]
        activity.logger.info(f"Found {len(skus)} eBay products sold elsewhere to delete")
        return skus

    finally:
        db.close()


@activity.defn
def update_job_progress(
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
def mark_job_completed(
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
def mark_job_failed(
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


@activity.defn
def detect_ebay_sold_elsewhere(user_id: int) -> dict:
    """
    Detect products SOLD on StoFlow but still listed on eBay (not sold on eBay).

    Creates PendingAction (DELETE_EBAY_LISTING) for each product found,
    so the user can confirm or reject the eBay listing deletion.

    Criteria:
    - StoFlow product status = SOLD
    - eBay sold_quantity is NULL or < 1 (not sold on eBay)

    Args:
        user_id: User ID for schema isolation

    Returns:
        Dict with 'pending_count' and 'product_ids'
    """
    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from services.pending_action_service import PendingActionService
        from models.user.pending_action import PendingActionType

        result = db.execute(
            text("""
                SELECT ep.ebay_sku, ep.product_id, ep.title, ep.price,
                       p.status::text as stoflow_status
                FROM ebay_products ep
                JOIN products p ON p.id = ep.product_id
                WHERE p.status::text = 'SOLD'
                  AND ep.product_id IS NOT NULL
                  AND (ep.sold_quantity IS NULL OR ep.sold_quantity < 1)
            """)
        ).fetchall()

        if not result:
            activity.logger.info(
                "No eBay products sold elsewhere to clean up"
            )
            return {"pending_count": 0, "product_ids": []}

        service = PendingActionService(db)
        product_ids = []

        for sku, product_id, title, price, stoflow_status in result:
            action = service.create_pending_action(
                product_id=product_id,
                action_type=PendingActionType.DELETE_EBAY_LISTING,
                marketplace="ebay",
                reason=f"Produit vendu ailleurs — listing eBay (SKU={sku}) encore actif",
                context_data={
                    "ebay_sku": sku,
                    "title": title,
                    "price": float(price) if price else None,
                },
            )
            if action:
                product_ids.append(product_id)
                activity.logger.info(
                    f"Created pending action for StoFlow #{product_id} "
                    f"(eBay SKU={sku}, was {stoflow_status})"
                )

        db.commit()

        activity.logger.info(
            f"Created {len(product_ids)} pending actions for eBay products sold elsewhere"
        )

        return {
            "pending_count": len(product_ids),
            "product_ids": product_ids,
        }

    finally:
        db.close()


@activity.defn
def delete_ebay_listing(user_id: int, product_id: int, marketplace_id: str = "EBAY_FR") -> dict:
    """
    Delete an eBay listing for a product (API + local DB).

    Called by EbayCleanupWorkflow when user confirms a DELETE_EBAY_LISTING pending action.

    Args:
        user_id: User ID for schema isolation
        product_id: StoFlow product ID
        marketplace_id: eBay marketplace (default EBAY_FR)

    Returns:
        Dict with 'success', 'product_id', optional 'error'
    """
    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from models.user.ebay_product import EbayProduct
        from services.ebay.ebay_inventory_client import EbayInventoryClient

        ebay_product = db.query(EbayProduct).filter_by(product_id=product_id).first()
        if not ebay_product:
            activity.logger.warning(f"No eBay product found for product #{product_id}")
            return {"success": False, "product_id": product_id, "error": "not_found"}

        sku = ebay_product.ebay_sku
        client = EbayInventoryClient(db, user_id, marketplace_id)

        try:
            client.delete_inventory_item(sku)
        except Exception as e:
            activity.logger.warning(f"eBay API delete failed for SKU={sku}: {e}")

        # Delete from local DB (always, even if eBay API failed)
        db.delete(ebay_product)
        db.commit()

        activity.logger.info(f"Deleted eBay listing for product #{product_id} (SKU={sku})")
        return {"success": True, "product_id": product_id}

    except Exception as e:
        activity.logger.error(f"Failed to delete eBay listing for product #{product_id}: {e}")
        return {"success": False, "product_id": product_id, "error": str(e)[:100]}

    finally:
        db.close()


# Export all activities for registration
EBAY_ACTIVITIES = [
    fetch_and_sync_page,
    get_skus_to_delete,
    delete_single_product,
    sync_sold_status,
    get_skus_sold_elsewhere,
    update_job_progress,
    mark_job_completed,
    mark_job_failed,
    enrich_single_product,
    get_skus_to_enrich,
    detect_ebay_sold_elsewhere,
    delete_ebay_listing,
]
