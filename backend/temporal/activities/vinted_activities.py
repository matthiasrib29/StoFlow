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
- get_vinted_ids_to_enrich: Get batch of vinted_ids to enrich
- enrich_single_product: Enrich one product via item_upload API

Job state management: see job_state_activities.py
Sold status reconciliation: see vinted_sync_reconciliation_activities.py

Key differences from eBay:
- Uses WebSocket plugin for API calls (not direct HTTP)
- Sequential fetching (DataDome protection)
- Mark as "sold" instead of delete for missing products
- Sequential enrichment (one product at a time)

Author: Claude
Date: 2026-01-22
Updated: 2026-01-27 - Extracted job state and reconciliation activities
"""

import json
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from temporalio import activity

from shared.database import SessionLocal
from shared.logging import get_logger
from temporal.activities.job_state_activities import (
    configure_activity_session,
    JOB_STATE_ACTIVITIES,
)
from temporal.activities.vinted_sync_reconciliation_activities import (
    VINTED_RECONCILIATION_ACTIVITIES,
)

logger = get_logger(__name__)


async def _call_vinted_api(
    db,
    user_id: int,
    http_method: str,
    path: str,
    timeout: int,
    description: str,
    body: Optional[dict] = None,
) -> dict:
    """
    Universal wrapper for Vinted API calls via plugin.

    Handles all error types consistently:
    - 401 Unauthorized -> error: "unauthorized"
    - 403 Forbidden -> error: "forbidden" (DataDome block)
    - 404 Not Found -> error: "not_found"
    - 429 Rate Limited -> error: "rate_limited"
    - 5xx Server Error -> error: "server_error"
    - Timeout -> error: "timeout"
    - Disconnected -> error: "disconnected"

    Returns:
        Dict with either:
        - {"success": True, "data": <response_data>}
        - {"success": False, "error": "<error_code>", "message": "<details>"}
    """
    from services.plugin_websocket_helper import PluginWebSocketHelper, PluginHTTPError

    try:
        result = await PluginWebSocketHelper.call_plugin_http(
            db=db,
            user_id=user_id,
            http_method=http_method,
            path=path,
            payload=body,
            timeout=timeout,
            description=description,
        )
        return {"success": True, "data": result}

    except PluginHTTPError as e:
        error_code = e.get_result_code()
        activity.logger.warning(f"Vinted API error [{e.status}] for {description}: {e.message}")

        return {
            "success": False,
            "error": error_code,
            "status": e.status,
            "message": e.message,
        }

    except TimeoutError:
        activity.logger.warning(f"Timeout for {description}")
        return {
            "success": False,
            "error": "timeout",
            "message": f"Request timeout for {description}",
        }

    except RuntimeError as e:
        error_msg = str(e).lower()
        if any(pattern in error_msg for pattern in (
            "not connected", "disconnected", "receiving end does not exist",
            "could not establish connection", "no plugin",
        )):
            activity.logger.warning(f"Plugin disconnected for {description}: {e}")
            return {
                "success": False,
                "error": "disconnected",
                "message": str(e),
            }
        # Unknown RuntimeError - re-raise for Temporal retry
        raise

    except Exception as e:
        activity.logger.error(f"Unexpected error for {description}: {e}")
        raise


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
        configure_activity_session(db, user_id)

        from models.user.vinted_product import VintedProduct
        from services.vinted.vinted_data_extractor import VintedDataExtractor
        from shared.vinted import VintedProductAPI
        from shared.config import settings

        sync_time = datetime.fromisoformat(sync_start_time.replace("Z", "+00:00"))

        api_result = await _call_vinted_api(
            db=db,
            user_id=user_id,
            http_method="GET",
            path=VintedProductAPI.get_shop_items(shop_id, page=page),
            timeout=settings.plugin_timeout_sync,
            description=f"Sync products page {page}",
        )

        if not api_result["success"]:
            return {
                "synced": 0,
                "errors": 0,
                "total_pages": 0,
                "vinted_ids": [],
                "error": api_result["error"],
            }

        result = api_result["data"]
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

                product_data = _extract_product_data(item, extractor)

                existing = db.query(VintedProduct).filter(
                    VintedProduct.vinted_id == vinted_id
                ).first()

                if existing:
                    for key, value in product_data.items():
                        if hasattr(existing, key) and value is not None:
                            setattr(existing, key, value)
                    existing.last_synced_at = sync_time
                    existing.updated_at = sync_time
                else:
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
                configure_activity_session(db, user_id)

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
    """
    title = api_product.get("title", "")
    price = extractor.extract_price(api_product.get("price"))
    currency = api_product.get("currency", "EUR")
    total_price = extractor.extract_price(api_product.get("total_item_price"))
    service_fee = extractor.extract_price(api_product.get("service_fee"))

    brand = api_product.get("brand")
    size = api_product.get("size")
    condition = api_product.get("status")

    is_draft = api_product.get("is_draft", False)
    is_closed = api_product.get("is_closed", False)
    is_reserved = api_product.get("is_reserved", False)
    is_hidden = api_product.get("is_hidden", False)
    status = extractor.map_api_status(is_draft=is_draft, is_closed=is_closed)

    user = api_product.get("user") or {}
    seller_id = user.get("id") if isinstance(user, dict) else api_product.get("user_id")
    seller_login = user.get("login") if isinstance(user, dict) else None

    view_count = api_product.get("view_count", 0)
    favourite_count = api_product.get("favourite_count", 0)

    url = api_product.get("url", "")
    photos = api_product.get("photos", [])
    photos_data = json.dumps(photos) if photos else None

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
) -> list[int]:
    """
    Get all vinted_ids to enrich from the current sync session.

    Filters products that:
    - Were synced in this session (last_synced_at >= sync_start_time)
    - Don't have a description yet
    - Are not sold/deleted/closed/hidden

    Args:
        user_id: User ID for schema isolation
        sync_start_time: ISO timestamp

    Returns:
        List of vinted_ids to enrich
    """
    db = SessionLocal()
    try:
        configure_activity_session(db, user_id)

        from models.user.vinted_product import VintedProduct

        sync_time = datetime.fromisoformat(sync_start_time.replace("Z", "+00:00"))

        products = (
            db.query(VintedProduct.vinted_id)
            .filter(
                VintedProduct.updated_at >= sync_time,
                (VintedProduct.description.is_(None)) | (VintedProduct.description == ""),
                VintedProduct.status.notin_(["sold", "deleted"]),
                VintedProduct.is_closed == False,
                VintedProduct.is_hidden == False,
            )
            .order_by(VintedProduct.vinted_id)
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
        configure_activity_session(db, user_id)

        from models.user.vinted_product import VintedProduct
        from services.vinted.vinted_item_upload_parser import VintedItemUploadParser
        from shared.config import settings

        product = db.query(VintedProduct).filter(
            VintedProduct.vinted_id == vinted_id
        ).first()

        if not product:
            return {"success": False, "vinted_id": vinted_id, "error": "not_found_db"}

        api_path = f"/api/v2/item_upload/items/{vinted_id}"
        api_result = await _call_vinted_api(
            db=db,
            user_id=user_id,
            http_method="GET",
            path=api_path,
            timeout=settings.plugin_timeout_sync,
            description=f"Get item_upload for {vinted_id}",
        )

        if not api_result["success"]:
            error = api_result["error"]

            if error == "not_found":
                product.is_closed = True
                db.commit()
                return {"success": False, "vinted_id": vinted_id, "error": "not_found_vinted"}

            return {"success": False, "vinted_id": vinted_id, "error": error}

        result = api_result["data"]
        if not result or not isinstance(result, dict):
            return {"success": False, "vinted_id": vinted_id, "error": "invalid_response"}

        extracted = VintedItemUploadParser.parse_item_response(result)

        if not extracted:
            return {"success": False, "vinted_id": vinted_id, "error": "parse_failed"}

        _update_product_from_extracted(product, extracted)
        db.commit()

        return {"success": True, "vinted_id": vinted_id}

    finally:
        db.close()


def _update_product_from_extracted(product, extracted: dict) -> None:
    """Update VintedProduct with data from item_upload API."""
    import json

    if extracted.get("description"):
        product.description = extracted["description"]

    if extracted.get("brand_id"):
        product.brand_id = extracted["brand_id"]
    if extracted.get("brand") and not product.brand:
        product.brand = extracted["brand"]

    if extracted.get("size_id"):
        product.size_id = extracted["size_id"]

    if extracted.get("catalog_id"):
        product.catalog_id = extracted["catalog_id"]

    if extracted.get("status_id"):
        product.status_id = extracted["status_id"]
    if extracted.get("condition") and not product.condition:
        product.condition = extracted["condition"]

    if extracted.get("color1"):
        product.color1 = extracted["color1"]
    if extracted.get("color1_id"):
        product.color1_id = extracted["color1_id"]
    if extracted.get("color2"):
        product.color2 = extracted["color2"]
    if extracted.get("color2_id"):
        product.color2_id = extracted["color2_id"]

    if extracted.get("measurement_width"):
        product.measurement_width = extracted["measurement_width"]
    if extracted.get("measurement_length"):
        product.measurement_length = extracted["measurement_length"]
    if extracted.get("measurement_unit"):
        product.measurement_unit = extracted["measurement_unit"]

    if "is_unisex" in extracted:
        product.is_unisex = extracted["is_unisex"]
    if extracted.get("manufacturer_labelling"):
        product.manufacturer_labelling = extracted["manufacturer_labelling"]
    if extracted.get("item_attributes") is not None:
        product.item_attributes = extracted["item_attributes"]

    if "is_draft" in extracted:
        product.is_draft = extracted["is_draft"]

    if extracted.get("photos_data"):
        photos_list = extracted["photos_data"]
        if photos_list:
            product.photos_data = json.dumps(photos_list)

    if extracted.get("url") and not product.url:
        product.url = extracted["url"]

    if extracted.get("price"):
        product.price = extracted["price"]
    if extracted.get("currency"):
        product.currency = extracted["currency"]


# Export all activities for Temporal worker registration
VINTED_ACTIVITIES = [
    fetch_and_sync_page,
    get_vinted_ids_to_enrich,
    enrich_single_product,
    *JOB_STATE_ACTIVITIES,
    *VINTED_RECONCILIATION_ACTIVITIES,
]
