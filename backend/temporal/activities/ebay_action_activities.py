"""
eBay Action Activities for Temporal.

These activities wrap existing eBay services to execute marketplace actions
(publish, update, delete, import) via Temporal workflows.

Each activity is designed to be:
- Idempotent where possible
- Retryable (Temporal handles retry policy)
- Independent (no shared state between activities)

IMPORTANT: Activities are defined as regular `def` (not `async def`) because:
- The eBay client uses `requests` (synchronous HTTP library)
- Temporal executes sync activities in a threadpool (max_concurrent_activities threads)
- This allows true parallel execution for eBay (30 concurrent HTTP calls)
- Using `async def` with sync code would block the event loop = no parallelism

Author: Claude
Date: 2026-01-27
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


# ═══════════════════════════════════════════════════════════════════
# PUBLISH / UPDATE / DELETE
# ═══════════════════════════════════════════════════════════════════


@activity.defn(name="ebay_publish_product")
def ebay_publish_product(
    user_id: int,
    product_id: int,
    marketplace_id: str = "EBAY_FR",
) -> dict:
    """
    Publish a product to eBay via direct API.

    Creates inventory item and offer on eBay marketplace.

    Args:
        user_id: User ID for OAuth credentials and schema
        product_id: StoFlow product ID to publish
        marketplace_id: eBay marketplace (default EBAY_FR)

    Returns:
        Dict with 'success', 'ebay_listing_id', 'offer_id', 'sku', 'error'
    """
    activity.logger.info(
        f"Publishing product #{product_id} to eBay ({marketplace_id})"
    )

    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from services.ebay.ebay_publication_service import EbayPublicationService

        service = EbayPublicationService(db, user_id)
        result = service.publish_product(
            product_id=product_id,
            marketplace_id=marketplace_id,
        )

        activity.logger.info(
            f"Product #{product_id} published to eBay "
            f"(listing_id={result.get('listing_id')})"
        )

        return {"success": True, **result}

    except Exception as e:
        activity.logger.error(f"eBay publish failed for product #{product_id}: {e}")
        return {"success": False, "product_id": product_id, "error": str(e)}

    finally:
        db.close()


@activity.defn(name="ebay_update_product")
def ebay_update_product(
    user_id: int,
    product_id: int,
    marketplace_id: str = "EBAY_FR",
) -> dict:
    """
    Update a product listing on eBay via direct API.

    Updates inventory item and/or offer on eBay marketplace.

    Args:
        user_id: User ID for OAuth credentials and schema
        product_id: StoFlow product ID to update
        marketplace_id: eBay marketplace (default EBAY_FR)

    Returns:
        Dict with 'success', 'product_id', 'error'
    """
    activity.logger.info(
        f"Updating product #{product_id} on eBay ({marketplace_id})"
    )

    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from services.ebay.ebay_publication_service import EbayPublicationService

        service = EbayPublicationService(db, user_id)
        result = service.update_product(product_id)

        activity.logger.info(f"Product #{product_id} updated on eBay")

        if isinstance(result, dict):
            return {"success": True, **result}
        return {"success": True, "product_id": product_id}

    except Exception as e:
        activity.logger.error(f"eBay update failed for product #{product_id}: {e}")
        return {"success": False, "product_id": product_id, "error": str(e)}

    finally:
        db.close()


@activity.defn(name="ebay_delete_product")
def ebay_delete_product(
    user_id: int,
    product_id: int,
    marketplace_id: str = "EBAY_FR",
) -> dict:
    """
    Delete (unpublish) a product listing from eBay via direct API.

    Withdraws the offer and optionally deletes the inventory item.

    Args:
        user_id: User ID for OAuth credentials and schema
        product_id: StoFlow product ID to delete
        marketplace_id: eBay marketplace (default EBAY_FR)

    Returns:
        Dict with 'success', 'product_id', 'error'
    """
    activity.logger.info(
        f"Deleting product #{product_id} from eBay ({marketplace_id})"
    )

    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from services.ebay.ebay_publication_service import EbayPublicationService

        service = EbayPublicationService(db, user_id)
        result = service.delete_product(product_id)

        activity.logger.info(f"Product #{product_id} deleted from eBay")

        if isinstance(result, dict):
            return {"success": True, **result}
        return {"success": True, "product_id": product_id}

    except Exception as e:
        activity.logger.error(f"eBay delete failed for product #{product_id}: {e}")
        return {"success": False, "product_id": product_id, "error": str(e)}

    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════
# ORDERS SYNC
# ═══════════════════════════════════════════════════════════════════


@activity.defn(name="ebay_sync_orders")
def ebay_sync_orders(
    user_id: int,
    marketplace_id: str = "EBAY_FR",
) -> dict:
    """
    Synchronize orders from eBay Fulfillment API.

    Args:
        user_id: User ID for OAuth credentials and schema
        marketplace_id: eBay marketplace (default EBAY_FR)

    Returns:
        Dict with 'success', 'orders_synced', 'created', 'updated', 'errors', 'error'
    """
    activity.logger.info(f"Syncing eBay orders for user {user_id} ({marketplace_id})")

    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from services.ebay.ebay_order_sync_service import EbayOrderSyncService

        service = EbayOrderSyncService(db, user_id)
        result = service.sync_orders()

        if isinstance(result, dict):
            if result.get("success", True):
                activity.logger.info(
                    f"eBay orders synced: {result.get('orders_synced', 0)}"
                )
            else:
                activity.logger.warning(f"eBay orders sync failed: {result.get('error')}")
            return result

        return {"success": True, "orders_synced": 0}

    except Exception as e:
        activity.logger.error(f"eBay orders sync failed: {e}")
        return {"success": False, "error": str(e)}

    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════
# IMPORT (page-level granularity for workflow orchestration)
# ═══════════════════════════════════════════════════════════════════


@activity.defn(name="ebay_import_inventory_page")
def ebay_import_inventory_page(
    user_id: int,
    marketplace_id: str,
    limit: int,
    offset: int,
) -> dict:
    """
    Import one page of eBay inventory items WITHOUT enrichment.

    Fast import: creates/updates EbayProduct records from inventory data only.
    Enrichment (offer data) is done separately via ebay_enrich_products_batch.

    Args:
        user_id: User ID for OAuth credentials and schema
        marketplace_id: eBay marketplace (EBAY_FR, etc.)
        limit: Number of items per page
        offset: Page offset

    Returns:
        Dict with 'imported', 'updated', 'errors', 'total', 'has_more', 'skus'
    """
    activity.logger.info(
        f"Importing eBay inventory page: offset={offset}, limit={limit}"
    )

    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from services.ebay.ebay_importer import EbayImporter

        importer = EbayImporter(
            db=db,
            user_id=user_id,
            marketplace_id=marketplace_id,
        )

        # Fetch one page of inventory
        result = importer.inventory_client.get_inventory_items(
            limit=limit,
            offset=offset,
        )

        items = result.get("inventoryItems", [])
        total = result.get("total", 0)

        if not items:
            return {
                "imported": 0,
                "updated": 0,
                "errors": 0,
                "total": total,
                "has_more": False,
                "skus": [],
            }

        imported = 0
        updated = 0
        errors = 0
        skus = []

        for item in items:
            sku = item.get("sku", "unknown")
            try:
                # Re-configure session (safety after potential rollback)
                _configure_session(db, user_id)

                import_result = importer._import_single_item(item, enrich=False)
                status = import_result.get("status")

                if status == "imported":
                    imported += 1
                    skus.append(sku)
                elif status == "updated":
                    updated += 1
                    skus.append(sku)

            except Exception as e:
                activity.logger.warning(f"Failed to import SKU={sku}: {e}")
                errors += 1
                db.rollback()
                _configure_session(db, user_id)

        db.commit()

        has_more = (offset + len(items)) < total

        activity.logger.info(
            f"Page imported: {imported} new, {updated} updated, "
            f"{errors} errors, has_more={has_more}"
        )

        return {
            "imported": imported,
            "updated": updated,
            "errors": errors,
            "total": total,
            "has_more": has_more,
            "skus": skus,
        }

    finally:
        db.close()


@activity.defn(name="ebay_enrich_products_batch")
def ebay_enrich_products_batch(
    user_id: int,
    marketplace_id: str,
    skus: list,
) -> dict:
    """
    Enrich a batch of eBay products with offer data (price, listing_id, status).

    Fetches offers in parallel threads for each SKU, then applies results
    sequentially in the main thread for thread-safe DB access.

    Args:
        user_id: User ID for OAuth credentials and schema
        marketplace_id: eBay marketplace (EBAY_FR, etc.)
        skus: List of SKUs to enrich

    Returns:
        Dict with 'enriched', 'errors' counts
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    activity.logger.info(f"Enriching {len(skus)} eBay products")

    if not skus:
        return {"enriched": 0, "errors": 0}

    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from models.user.ebay_product import EbayProduct
        from services.ebay.ebay_importer import EbayImporter
        from shared.datetime_utils import utc_now

        importer = EbayImporter(
            db=db,
            user_id=user_id,
            marketplace_id=marketplace_id,
        )

        # Pre-fetch access token BEFORE parallel threads
        try:
            _ = importer.offer_client.get_access_token()
        except Exception as e:
            activity.logger.warning(f"Token pre-fetch failed: {e}")

        # Load products from DB
        products = db.query(EbayProduct).filter(
            EbayProduct.ebay_sku.in_(skus)
        ).all()
        sku_to_product = {p.ebay_sku: p for p in products}

        def fetch_offer_for_sku(sku: str):
            """Fetch offer for a SKU (thread-safe - only API call, no DB)."""
            try:
                offers = importer.fetch_offers_for_sku(sku)
                return (sku, offers)
            except Exception as e:
                activity.logger.warning(f"Failed to fetch offer for SKU {sku}: {e}")
                return (sku, None)

        # Parallel API calls
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(fetch_offer_for_sku, sku): sku
                for sku in skus
                if sku in sku_to_product
            }
            for future in as_completed(futures):
                try:
                    sku, offers = future.result()
                    if offers:
                        results.append((sku, offers))
                except Exception as e:
                    activity.logger.warning(f"Error fetching offer: {e}")

        # Apply results in main thread (thread-safe DB access)
        enriched = 0
        errors = 0
        for sku, offers in results:
            product = sku_to_product.get(sku)
            if product and offers:
                try:
                    _apply_offer_to_product(product, offers, marketplace_id)
                    enriched += 1
                except Exception as e:
                    activity.logger.warning(f"Error applying offer for SKU {sku}: {e}")
                    errors += 1

        db.commit()

        activity.logger.info(
            f"Enrichment done: {enriched} enriched, {errors} errors"
        )

        return {"enriched": enriched, "errors": errors}

    finally:
        db.close()


def _apply_offer_to_product(product, offers: list, marketplace_id: str) -> None:
    """Apply offer data to an EbayProduct instance."""
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


@activity.defn(name="ebay_cleanup_orphan_imports")
def ebay_cleanup_orphan_imports(user_id: int) -> dict:
    """
    Delete imported eBay products that have no listing_id.

    Called after import + enrichment to clean up products that
    don't have an active listing on eBay.

    Args:
        user_id: User ID for schema isolation

    Returns:
        Dict with 'deleted' count
    """
    activity.logger.info(f"Cleaning up orphan eBay imports for user {user_id}")

    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        result = db.execute(
            text("DELETE FROM ebay_products WHERE ebay_listing_id IS NULL")
        )
        deleted = result.rowcount
        db.commit()

        activity.logger.info(f"Deleted {deleted} orphan eBay products")
        return {"deleted": deleted}

    finally:
        db.close()


# Export all activities for registration
EBAY_ACTION_ACTIVITIES = [
    ebay_publish_product,
    ebay_update_product,
    ebay_delete_product,
    ebay_sync_orders,
    ebay_import_inventory_page,
    ebay_enrich_products_batch,
    ebay_cleanup_orphan_imports,
]
