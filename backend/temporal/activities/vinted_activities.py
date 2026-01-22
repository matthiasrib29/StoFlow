"""
Vinted Sync Activities for Temporal.

These activities wrap the existing Vinted sync logic to work with Temporal.
Each activity is designed to be:
- Idempotent where possible
- Retryable
- Independent (no shared state between activities)

Activities handle their own DB sessions since they run in the worker process.

Architecture:
- fetch_and_sync_page: Fetch one page from Vinted via plugin and upsert to DB
- mark_missing_as_sold: Mark products not seen in current sync as sold
- get_vinted_ids_to_enrich: Get batch of vinted_ids to enrich
- enrich_single_product: Enrich one product via item_upload API
- update_job_progress: Update job progress in DB
- mark_job_completed/failed: Update job status

Key differences from eBay:
- Uses WebSocket plugin for API calls (not direct HTTP)
- Sequential fetching (DataDome protection)
- Mark as "sold" instead of delete for missing products
- Enrichment in small batches (15) with longer pauses (20-30s)

Author: Claude
Date: 2026-01-22
"""

import asyncio
import json
import random
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


@activity.defn(name="vinted_fetch_and_sync_page")
async def fetch_and_sync_page(
    user_id: int,
    shop_id: int,
    page: int,
    sync_start_time: str,
) -> dict:
    """
    Fetch a page of wardrobe items from Vinted via plugin and sync to DB.

    This activity:
    1. Fetches one page from Vinted API via WebSocket plugin
    2. For each item, upserts to vinted_products table
    3. Updates last_synced_at to sync_start_time
    4. Returns counts and list of synced vinted_ids

    Note: Unlike eBay, Vinted uses sequential fetching due to DataDome protection.
    The plugin handles request delays internally.

    Args:
        user_id: User ID for schema and plugin WebSocket
        shop_id: Vinted shop ID (vinted_user_id)
        page: Page number to fetch
        sync_start_time: ISO timestamp for this sync run

    Returns:
        Dict with 'synced', 'errors', 'total_pages', 'vinted_ids'
    """
    activity.logger.info(f"Fetching and syncing page {page} for shop {shop_id}")

    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        # Import here to avoid circular imports
        from models.user.vinted_product import VintedProduct
        from services.plugin_websocket_helper import PluginWebSocketHelper
        from services.vinted.vinted_data_extractor import VintedDataExtractor
        from shared.vinted import VintedProductAPI
        from shared.config import settings

        # Parse sync_start_time
        sync_time = datetime.fromisoformat(sync_start_time.replace("Z", "+00:00"))

        # Fetch page from Vinted via plugin
        result = await PluginWebSocketHelper.call_plugin_http(
            db=db,
            user_id=user_id,
            http_method="GET",
            path=VintedProductAPI.get_shop_items(shop_id, page=page),
            timeout=settings.plugin_timeout_sync,
            description=f"Sync products page {page}"
        )

        items = result.get("items", [])
        pagination = result.get("pagination", {})
        total_pages = pagination.get("total_pages", 1)

        activity.logger.info(f"Fetched {len(items)} items (page {page}/{total_pages})")

        if not items:
            return {
                "synced": 0,
                "errors": 0,
                "total_pages": total_pages,
                "vinted_ids": [],
            }

        extractor = VintedDataExtractor()
        synced = 0
        errors = 0
        vinted_ids = []

        for item in items:
            try:
                vinted_id = item.get("id")
                if not vinted_id:
                    continue

                # Extract product data
                product_data = _extract_product_data(item, extractor)

                # Check if exists
                existing = db.query(VintedProduct).filter(
                    VintedProduct.vinted_id == vinted_id
                ).first()

                if existing:
                    # UPDATE existing product
                    for key, value in product_data.items():
                        if hasattr(existing, key) and value is not None:
                            setattr(existing, key, value)
                    existing.last_synced_at = sync_time
                    existing.updated_at = sync_time
                else:
                    # INSERT new product
                    product = VintedProduct(
                        vinted_id=vinted_id,
                        **product_data,
                        last_synced_at=sync_time,
                    )
                    db.add(product)

                vinted_ids.append(vinted_id)
                synced += 1

            except Exception as e:
                activity.logger.warning(f"Error syncing vinted_id={item.get('id')}: {e}")
                errors += 1
                db.rollback()
                _configure_session(db, user_id)

        db.commit()

        activity.logger.info(
            f"Page {page} synced: synced={synced}, errors={errors}"
        )

        return {
            "synced": synced,
            "errors": errors,
            "total_pages": total_pages,
            "vinted_ids": vinted_ids,
        }

    finally:
        db.close()


def _extract_product_data(api_product: dict, extractor) -> dict:
    """
    Extract product data from Vinted API response.

    IMPORTANT: The listing API returns LIMITED data.
    IDs and detailed data are obtained via enrichment (item_upload API).

    Args:
        api_product: Raw product data from API
        extractor: VintedDataExtractor instance

    Returns:
        Dict with extracted fields for VintedProduct
    """
    title = api_product.get("title", "")
    price = extractor.extract_price(api_product.get("price"))
    currency = api_product.get("currency", "EUR")
    total_price = extractor.extract_price(api_product.get("total_item_price"))
    service_fee = extractor.extract_price(api_product.get("service_fee"))

    # Brand and Size: direct STRING values (not objects with IDs)
    brand = api_product.get("brand")
    size = api_product.get("size")
    condition = api_product.get("status")

    # Publication status
    is_draft = api_product.get("is_draft", False)
    is_closed = api_product.get("is_closed", False)
    is_reserved = api_product.get("is_reserved", False)
    is_hidden = api_product.get("is_hidden", False)
    status = extractor.map_api_status(
        is_draft=is_draft,
        is_closed=is_closed,
        closing_action=api_product.get("item_closing_action")
    )

    # Seller info
    user = api_product.get("user") or {}
    seller_id = user.get("id") if isinstance(user, dict) else api_product.get("user_id")
    seller_login = user.get("login") if isinstance(user, dict) else None

    # Analytics
    view_count = api_product.get("view_count", 0)
    favourite_count = api_product.get("favourite_count", 0)

    # URLs & Images
    url = api_product.get("url", "")
    photos = api_product.get("photos", [])
    photos_data = json.dumps(photos) if photos else None

    # Publication date
    published_at = None
    if photos and isinstance(photos[0], dict):
        high_res = photos[0].get("high_resolution") or {}
        if isinstance(high_res, dict) and high_res.get("timestamp"):
            try:
                published_at = datetime.fromtimestamp(high_res["timestamp"])
            except (ValueError, OSError):
                pass

    if not published_at and api_product.get("created_at_ts"):
        try:
            published_at = datetime.fromtimestamp(api_product["created_at_ts"])
        except (ValueError, OSError):
            pass

    return {
        "title": title,
        "price": price,
        "currency": currency or "EUR",
        "total_price": total_price,
        "service_fee": service_fee,
        "brand": brand,
        "size": size,
        "condition": condition,
        "status": status,
        "is_draft": is_draft,
        "is_closed": is_closed,
        "is_reserved": is_reserved,
        "is_hidden": is_hidden,
        "seller_id": seller_id,
        "seller_login": seller_login,
        "view_count": view_count,
        "favourite_count": favourite_count,
        "url": url,
        "photos_data": photos_data,
        "published_at": published_at,
    }


@activity.defn(name="vinted_get_ids_to_enrich")
async def get_vinted_ids_to_enrich(
    user_id: int,
    sync_start_time: str,
    limit: int = 15,
    offset: int = 0,
) -> list[int]:
    """
    Get a batch of vinted_ids to enrich from the current sync session.

    Filters products that:
    - Were synced in this session (last_synced_at >= sync_start_time)
    - Don't have a description yet
    - Are not sold/deleted/closed/hidden

    Args:
        user_id: User ID for schema isolation
        sync_start_time: ISO timestamp - only products synced at/after this time
        limit: Max vinted_ids to return (default 15 for DataDome protection)
        offset: Pagination offset

    Returns:
        List of vinted_ids to enrich
    """
    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from models.user.vinted_product import VintedProduct

        # Parse sync_start_time
        sync_time = datetime.fromisoformat(sync_start_time.replace("Z", "+00:00"))

        # Get products synced in this session without description
        products = (
            db.query(VintedProduct.vinted_id)
            .filter(
                VintedProduct.last_synced_at >= sync_time,
                (VintedProduct.description.is_(None)) | (VintedProduct.description == ""),
                VintedProduct.status.notin_(["sold", "deleted"]),
                VintedProduct.is_closed == False,
                VintedProduct.is_hidden == False,
            )
            .order_by(VintedProduct.id)
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [p.vinted_id for p in products]

    finally:
        db.close()


@activity.defn(name="vinted_enrich_single_product")
async def enrich_single_product(
    user_id: int,
    vinted_id: int,
) -> dict:
    """
    Enrich a single product with data from item_upload API.

    Calls /api/v2/item_upload/items/{id} via plugin to get:
    - Description
    - brand_id, size_id, catalog_id, status_id
    - Colors (color1, color1_id, color2, color2_id)
    - Measurements

    Args:
        user_id: User ID for schema isolation
        vinted_id: Vinted product ID to enrich

    Returns:
        Dict with 'success' bool and 'vinted_id'
    """
    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from models.user.vinted_product import VintedProduct
        from services.plugin_websocket_helper import (
            PluginWebSocketHelper,
            PluginHTTPError,
            PLUGIN_SUCCESS,
            PLUGIN_NOT_FOUND,
            PLUGIN_FORBIDDEN,
            PLUGIN_UNAUTHORIZED,
            PLUGIN_ERROR,
        )
        from services.vinted.vinted_item_upload_parser import VintedItemUploadParser
        from shared.config import settings

        product = db.query(VintedProduct).filter(
            VintedProduct.vinted_id == vinted_id
        ).first()

        if not product:
            return {"success": False, "vinted_id": vinted_id, "error": "not_found_db"}

        try:
            # Fetch item_upload data via plugin
            api_path = f"/api/v2/item_upload/items/{vinted_id}"
            result = await PluginWebSocketHelper.call_plugin_http(
                db=db,
                user_id=user_id,
                http_method="GET",
                path=api_path,
                timeout=settings.plugin_timeout_sync,
                description=f"Get item_upload for {vinted_id}"
            )

            if not result or not isinstance(result, dict):
                return {"success": False, "vinted_id": vinted_id, "error": "invalid_response"}

            # Parse the API response
            extracted = VintedItemUploadParser.parse_item_response(result)

            if not extracted:
                return {"success": False, "vinted_id": vinted_id, "error": "parse_failed"}

            # Update product with extracted data
            _update_product_from_extracted(product, extracted)
            db.commit()

            return {"success": True, "vinted_id": vinted_id}

        except PluginHTTPError as e:
            if e.is_not_found():
                # Mark as closed if 404 (sold/deleted on Vinted)
                product.is_closed = True
                db.commit()
                return {"success": False, "vinted_id": vinted_id, "error": "not_found_vinted"}

            if e.is_forbidden():
                return {"success": False, "vinted_id": vinted_id, "error": "forbidden"}

            if e.is_unauthorized():
                return {"success": False, "vinted_id": vinted_id, "error": "unauthorized"}

            return {"success": False, "vinted_id": vinted_id, "error": str(e)[:100]}

        except TimeoutError:
            return {"success": False, "vinted_id": vinted_id, "error": "timeout"}

        except RuntimeError as e:
            error_msg = str(e).lower()
            if "not connected" in error_msg or "disconnected" in error_msg:
                return {"success": False, "vinted_id": vinted_id, "error": "disconnected"}
            return {"success": False, "vinted_id": vinted_id, "error": str(e)[:100]}

    finally:
        db.close()


def _update_product_from_extracted(product, extracted: dict) -> None:
    """
    Update VintedProduct with data from item_upload API.

    Args:
        product: VintedProduct to update
        extracted: Data parsed by VintedItemUploadParser
    """
    import json

    # Description (priority)
    if extracted.get("description"):
        product.description = extracted["description"]

    # IDs - Brand
    if extracted.get("brand_id"):
        product.brand_id = extracted["brand_id"]
    if extracted.get("brand") and not product.brand:
        product.brand = extracted["brand"]

    # IDs - Size
    if extracted.get("size_id"):
        product.size_id = extracted["size_id"]

    # IDs - Catalog/Category
    if extracted.get("catalog_id"):
        product.catalog_id = extracted["catalog_id"]

    # IDs - Condition/Status
    if extracted.get("status_id"):
        product.status_id = extracted["status_id"]
    if extracted.get("condition") and not product.condition:
        product.condition = extracted["condition"]

    # Colors
    if extracted.get("color1"):
        product.color1 = extracted["color1"]
    if extracted.get("color1_id"):
        product.color1_id = extracted["color1_id"]
    if extracted.get("color2"):
        product.color2 = extracted["color2"]
    if extracted.get("color2_id"):
        product.color2_id = extracted["color2_id"]

    # Dimensions
    if extracted.get("measurement_width"):
        product.measurement_width = extracted["measurement_width"]
    if extracted.get("measurement_length"):
        product.measurement_length = extracted["measurement_length"]
    if extracted.get("measurement_unit"):
        product.measurement_unit = extracted["measurement_unit"]

    # Additional fields
    if "is_unisex" in extracted:
        product.is_unisex = extracted["is_unisex"]
    if extracted.get("manufacturer_labelling"):
        product.manufacturer_labelling = extracted["manufacturer_labelling"]
    if extracted.get("item_attributes") is not None:
        product.item_attributes = extracted["item_attributes"]

    # Status flags
    if "is_draft" in extracted:
        product.is_draft = extracted["is_draft"]

    # Photos
    if extracted.get("photos_data"):
        photos_list = extracted["photos_data"]
        if photos_list:
            product.photos_data = json.dumps(photos_list)

    # URL
    if extracted.get("url") and not product.url:
        product.url = extracted["url"]

    # Price
    if extracted.get("price"):
        product.price = extracted["price"]
    if extracted.get("currency"):
        product.currency = extracted["currency"]


@activity.defn(name="vinted_update_job_progress")
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

        data = json.dumps({"current": current, "label": label})

        db.execute(
            text("UPDATE marketplace_jobs SET result_data = :data WHERE id = :job_id"),
            {"data": data, "job_id": job_id},
        )
        db.commit()

        activity.logger.debug(f"Job #{job_id} progress: {current} - {label}")

    finally:
        db.close()


@activity.defn(name="vinted_mark_job_completed")
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


@activity.defn(name="vinted_mark_job_failed")
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
VINTED_ACTIVITIES = [
    fetch_and_sync_page,
    get_vinted_ids_to_enrich,
    enrich_single_product,
    update_job_progress,
    mark_job_completed,
    mark_job_failed,
]
