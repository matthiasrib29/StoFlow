"""
Vinted Action Activities for Temporal.

These activities wrap existing Vinted services to execute marketplace actions
(publish, update, delete, etc.) via Temporal workflows.

Each activity is designed to be:
- Idempotent where possible
- Retryable (Temporal handles retry policy)
- Independent (no shared state between activities)

Activities handle their own DB sessions since they run in the worker process.

Key differences from sync activities (vinted_activities.py):
- These wrap marketplace ACTIONS (publish, update, delete)
- Sync activities wrap SYNC operations (fetch pages, enrich)
- Both use WebSocket plugin (async) for Vinted API calls

Author: Claude
Date: 2026-01-27
"""

import asyncio
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


@activity.defn(name="vinted_publish_product")
async def vinted_publish_product(user_id: int, product_id: int, shop_id: int) -> dict:
    """
    Publish a product to Vinted via plugin.

    Delegates to VintedPublicationService which handles:
    validation, attribute mapping, price calculation, image upload, listing creation.

    Args:
        user_id: User ID for schema isolation and plugin communication
        product_id: StoFlow product ID to publish
        shop_id: Vinted shop ID (vinted_user_id)

    Returns:
        Dict with 'success', 'vinted_id', 'url', 'product_id', 'price', 'error'
    """
    activity.logger.info(f"Publishing product #{product_id} to Vinted (shop={shop_id})")

    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from services.vinted.vinted_publication_service import VintedPublicationService

        service = VintedPublicationService(db)
        result = await service.publish_product(
            product_id=product_id,
            user_id=user_id,
            shop_id=shop_id,
        )

        if result.get("success"):
            activity.logger.info(
                f"Product #{product_id} published to Vinted "
                f"(vinted_id={result.get('vinted_id')})"
            )
        else:
            activity.logger.warning(
                f"Product #{product_id} publish failed: {result.get('error')}"
            )

        return result

    except Exception as e:
        activity.logger.error(f"Vinted publish failed for product #{product_id}: {e}")
        return {"success": False, "product_id": product_id, "error": str(e)}

    finally:
        db.close()


@activity.defn(name="vinted_update_product")
async def vinted_update_product(user_id: int, product_id: int, shop_id: int) -> dict:
    """
    Update a product listing on Vinted via plugin.

    Delegates to VintedUpdateService which handles:
    validation, attribute recalculation, listing update.

    Args:
        user_id: User ID for schema isolation and plugin communication
        product_id: StoFlow product ID to update
        shop_id: Vinted shop ID (vinted_user_id)

    Returns:
        Dict with 'success', 'product_id', 'old_price', 'new_price', 'error'
    """
    activity.logger.info(f"Updating product #{product_id} on Vinted (shop={shop_id})")

    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from services.vinted.vinted_update_service import VintedUpdateService

        service = VintedUpdateService(db)
        result = await service.update_product(
            product_id=product_id,
            user_id=user_id,
            shop_id=shop_id,
        )

        if result.get("success"):
            activity.logger.info(f"Product #{product_id} updated on Vinted")
        else:
            activity.logger.warning(
                f"Product #{product_id} update failed: {result.get('error')}"
            )

        return result

    except Exception as e:
        activity.logger.error(f"Vinted update failed for product #{product_id}: {e}")
        return {"success": False, "product_id": product_id, "error": str(e)}

    finally:
        db.close()


@activity.defn(name="vinted_delete_product")
async def vinted_delete_product(
    user_id: int,
    product_id: int,
    shop_id: int,
    check_conditions: bool = True,
) -> dict:
    """
    Delete a product listing from Vinted via plugin.

    Delegates to VintedDeletionService which handles:
    condition checks, stats archiving, listing deletion.

    Args:
        user_id: User ID for schema isolation and plugin communication
        product_id: StoFlow product ID to delete
        shop_id: Vinted shop ID (vinted_user_id)
        check_conditions: Whether to check deletion conditions (default True)

    Returns:
        Dict with 'success', 'product_id', 'vinted_id', 'error'
    """
    activity.logger.info(
        f"Deleting product #{product_id} from Vinted "
        f"(shop={shop_id}, check_conditions={check_conditions})"
    )

    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from services.vinted.vinted_deletion_service import VintedDeletionService

        service = VintedDeletionService(db)
        result = await service.delete_product(
            product_id=product_id,
            user_id=user_id,
            shop_id=shop_id,
            check_conditions=check_conditions,
        )

        if result.get("success"):
            activity.logger.info(f"Product #{product_id} deleted from Vinted")
        else:
            activity.logger.warning(
                f"Product #{product_id} deletion failed: {result.get('error')}"
            )

        return result

    except Exception as e:
        activity.logger.error(f"Vinted delete failed for product #{product_id}: {e}")
        return {"success": False, "product_id": product_id, "error": str(e)}

    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════
# ORDERS SYNC
# ═══════════════════════════════════════════════════════════════════


@activity.defn(name="vinted_sync_orders")
async def vinted_sync_orders(
    user_id: int,
    shop_id: int,
    year: int = 0,
    month: int = 0,
) -> dict:
    """
    Synchronize orders from Vinted via plugin.

    Supports two modes:
    - Default (year=0, month=0): Fetch all orders from /my_orders
    - Monthly (year>0, month>0): Fetch specific month from /wallet/invoices

    Args:
        user_id: User ID for schema isolation and plugin communication
        shop_id: Vinted shop ID (vinted_user_id)
        year: Year filter (0 = all orders)
        month: Month filter (0 = all orders)

    Returns:
        Dict with 'success', 'orders_synced', 'mode', 'error'
    """
    params = {}
    if year > 0 and month > 0:
        params = {"year": year, "month": month}
        mode = f"month {year}-{month:02d}"
    else:
        mode = "all orders"

    activity.logger.info(f"Syncing Vinted orders ({mode}) for user {user_id}")

    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from services.vinted.vinted_orders_service import VintedOrdersService

        service = VintedOrdersService(db)
        result = await service.sync_orders(
            shop_id=shop_id,
            user_id=user_id,
            params=params if params else None,
        )

        if result.get("success"):
            activity.logger.info(
                f"Orders synced: {result.get('orders_synced', 0)} ({mode})"
            )
        else:
            activity.logger.warning(f"Orders sync failed: {result.get('error')}")

        return result

    except Exception as e:
        activity.logger.error(f"Vinted orders sync failed: {e}")
        return {"success": False, "error": str(e)}

    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════
# MESSAGES
# ═══════════════════════════════════════════════════════════════════


@activity.defn(name="vinted_send_message")
async def vinted_send_message(
    user_id: int,
    shop_id: int,
    conversation_id: int = 0,
) -> dict:
    """
    Synchronize messages from Vinted via plugin.

    Supports two modes:
    - Inbox sync (conversation_id=0): Fetch all conversations
    - Conversation sync (conversation_id>0): Fetch specific conversation

    Args:
        user_id: User ID for schema isolation and plugin communication
        shop_id: Vinted shop ID (vinted_user_id)
        conversation_id: Specific conversation ID (0 = sync inbox)

    Returns:
        Dict with 'success', 'synced', 'created', 'updated', 'error'
    """
    message_id = conversation_id if conversation_id > 0 else None
    mode = "conversation" if message_id else "inbox"

    activity.logger.info(f"Syncing Vinted messages ({mode}) for user {user_id}")

    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from services.vinted.vinted_message_service import VintedMessageService

        service = VintedMessageService(db)
        result = await service.handle_message(
            message_id=message_id,
            user_id=user_id,
            shop_id=shop_id,
        )

        if result.get("success"):
            activity.logger.info(f"Messages synced ({mode}): {result.get('synced', 0)}")
        else:
            activity.logger.warning(f"Messages sync failed: {result.get('error')}")

        return result

    except Exception as e:
        activity.logger.error(f"Vinted message sync failed: {e}")
        return {"success": False, "error": str(e)}

    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════
# LINK PRODUCT
# ═══════════════════════════════════════════════════════════════════


@activity.defn(name="vinted_link_product")
async def vinted_link_product(user_id: int, vinted_product_id: int) -> dict:
    """
    Link a VintedProduct to an internal Product model.

    Creates a new Product from VintedProduct data and downloads images to R2.

    Args:
        user_id: User ID for schema isolation
        vinted_product_id: Vinted product ID (not StoFlow product ID)

    Returns:
        Dict with 'success', 'product_id', 'vinted_id', 'images_copied', 'error'
    """
    activity.logger.info(
        f"Linking VintedProduct #{vinted_product_id} for user {user_id}"
    )

    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from services.vinted.vinted_link_product_service import VintedLinkProductService

        service = VintedLinkProductService(db)
        result = await service.link_product(
            vinted_product_id=vinted_product_id,
            product_id=None,
            user_id=user_id,
        )

        if result.get("success"):
            activity.logger.info(
                f"Linked VintedProduct #{vinted_product_id} -> Product #{result.get('product_id')}"
            )
        else:
            activity.logger.warning(
                f"Link failed for VintedProduct #{vinted_product_id}: {result.get('error')}"
            )

        return result

    except Exception as e:
        activity.logger.error(
            f"Vinted link failed for VintedProduct #{vinted_product_id}: {e}"
        )
        return {
            "success": False,
            "vinted_id": vinted_product_id,
            "error": str(e),
        }

    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════
# FETCH USERS (page-level granularity for workflow orchestration)
# ═══════════════════════════════════════════════════════════════════


@activity.defn(name="vinted_fetch_users_page")
async def vinted_fetch_users_page(
    user_id: int,
    search_text: str,
    page: int,
    per_page: int = 100,
    country_code: str = "FR",
    min_items: int = 200,
) -> dict:
    """
    Fetch a page of Vinted users via plugin and filter for prospection.

    Uses VINTED_API_CALL via call_plugin to search users, then filters
    by country and minimum items count.

    Args:
        user_id: User ID for WebSocket plugin communication
        search_text: Search text (e.g., a single letter 'a', 'b', etc.)
        page: Page number (1-indexed)
        per_page: Results per page (default 100)
        country_code: Country filter (default "FR")
        min_items: Minimum items count filter (default 200)

    Returns:
        Dict with:
        - users: list of filtered user dicts
        - total_fetched: total users fetched before filter
        - has_more: whether there are more pages
        - error: error code if any (disconnected, rate_limited, etc.)
    """
    activity.logger.info(
        f"Fetching users: search='{search_text}', page={page}, per_page={per_page}"
    )

    db = SessionLocal()
    try:
        from services.plugin_websocket_helper import PluginWebSocketHelper, PluginHTTPError

        try:
            result = await PluginWebSocketHelper.call_plugin(
                db=db,
                user_id=user_id,
                http_method="GET",
                path="/api/v2/users",
                params={
                    "search_text": search_text,
                    "page": page,
                    "per_page": per_page,
                },
                timeout=60,
                description=f"Fetch users '{search_text}' page {page}",
            )

            users = result.get("users", [])

            # Filter by country and minimum items
            filtered = [
                u for u in users
                if u.get("country_iso_code") == country_code
                and u.get("item_count", 0) >= min_items
            ]

            has_more = len(users) >= per_page

            activity.logger.info(
                f"Page {page} for '{search_text}': "
                f"{len(users)} fetched, {len(filtered)} filtered"
            )

            return {
                "users": filtered,
                "total_fetched": len(users),
                "has_more": has_more,
                "error": None,
            }

        except PluginHTTPError as e:
            error_code = e.get_result_code()
            activity.logger.warning(
                f"Plugin HTTP error [{e.status}] fetching users "
                f"'{search_text}' page {page}: {e.message}"
            )
            return {
                "users": [],
                "total_fetched": 0,
                "has_more": False,
                "error": error_code,
            }

        except TimeoutError:
            activity.logger.warning(
                f"Timeout fetching users '{search_text}' page {page}"
            )
            return {
                "users": [],
                "total_fetched": 0,
                "has_more": False,
                "error": "timeout",
            }

        except RuntimeError as e:
            error_msg = str(e).lower()
            if any(pattern in error_msg for pattern in (
                "not connected", "disconnected", "receiving end does not exist",
                "could not establish connection", "no plugin",
            )):
                activity.logger.warning(
                    f"Plugin disconnected fetching users "
                    f"'{search_text}' page {page}: {e}"
                )
                return {
                    "users": [],
                    "total_fetched": 0,
                    "has_more": False,
                    "error": "disconnected",
                }
            raise

    finally:
        db.close()


@activity.defn(name="vinted_save_prospects_batch")
async def vinted_save_prospects_batch(
    prospects_data: list,
    created_by: int,
) -> dict:
    """
    Save a batch of user prospects to the database.

    Checks for duplicates by vinted_user_id before inserting.

    Args:
        prospects_data: List of user dicts from Vinted API (already filtered)
        created_by: User ID who triggered the fetch

    Returns:
        Dict with 'saved', 'duplicates', 'errors' counts
    """
    from shared.database import get_db_context

    saved = 0
    duplicates = 0
    errors = 0

    with get_db_context() as db:
        from models.public.vinted_prospect import VintedProspect

        for user_data in prospects_data:
            try:
                vinted_user_id = user_data.get("id")
                if not vinted_user_id:
                    continue

                # Check duplicate
                existing = db.query(VintedProspect).filter(
                    VintedProspect.vinted_user_id == vinted_user_id
                ).first()

                if existing:
                    duplicates += 1
                    continue

                prospect = VintedProspect(
                    vinted_user_id=vinted_user_id,
                    login=user_data.get("login", "unknown"),
                    country_code=user_data.get("country_iso_code"),
                    item_count=user_data.get("item_count", 0),
                    total_items_count=user_data.get("total_items_count", 0),
                    feedback_count=user_data.get("feedback_count", 0),
                    feedback_reputation=user_data.get("feedback_reputation"),
                    is_business=user_data.get("business", False),
                    profile_url=f"https://www.vinted.fr/member/{vinted_user_id}",
                    status="new",
                    created_by=created_by,
                )
                db.add(prospect)
                saved += 1

            except Exception as e:
                activity.logger.warning(
                    f"Error saving prospect {user_data.get('id')}: {e}"
                )
                errors += 1

        db.commit()

    activity.logger.info(
        f"Prospects batch: {saved} saved, {duplicates} duplicates, {errors} errors"
    )

    return {"saved": saved, "duplicates": duplicates, "errors": errors}


# ═══════════════════════════════════════════════════════════════════
# CHECK CONNECTION
# ═══════════════════════════════════════════════════════════════════


@activity.defn(name="vinted_check_connection")
async def vinted_check_connection(user_id: int) -> dict:
    """
    Check Vinted connection status via plugin.

    Calls GET /api/v2/users/current and creates/updates VintedConnection record.

    Args:
        user_id: User ID for schema isolation and plugin communication

    Returns:
        Dict with 'success', 'connected', 'vinted_user_id', 'login', 'error'
    """
    activity.logger.info(f"Checking Vinted connection for user {user_id}")

    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from services.plugin_websocket_helper import PluginWebSocketHelper, PluginHTTPError
        from models.user.vinted_connection import VintedConnection

        # Call Vinted API via plugin
        try:
            result = await PluginWebSocketHelper.call_plugin(
                db=db,
                user_id=user_id,
                http_method="GET",
                path="/api/v2/users/current",
                timeout=30,
                description="Check Vinted connection",
            )
        except PluginHTTPError as e:
            activity.logger.warning(f"Plugin HTTP error checking connection: {e.message}")
            _update_connection_status(db, user_id, connected=False)
            return {
                "success": False,
                "connected": False,
                "vinted_user_id": None,
                "login": None,
                "error": e.get_result_code(),
            }
        except (TimeoutError, RuntimeError) as e:
            activity.logger.warning(f"Plugin error checking connection: {e}")
            _update_connection_status(db, user_id, connected=False)
            return {
                "success": False,
                "connected": False,
                "vinted_user_id": None,
                "login": None,
                "error": "disconnected",
            }

        # Parse response
        user_data = result if isinstance(result, dict) else {}
        vinted_user_id = user_data.get("id")
        login = user_data.get("login")

        if not vinted_user_id or not login:
            activity.logger.error("Missing required fields (id, login) in response")
            return {
                "success": False,
                "connected": False,
                "vinted_user_id": None,
                "login": None,
                "error": "Invalid response: missing user id or login",
            }

        # Update connection record
        connection = _update_connection_status(
            db, user_id,
            connected=True,
            vinted_user_id=int(vinted_user_id),
            login=login,
            user_data=user_data,
        )

        activity.logger.info(
            f"Connected as {login} (Vinted ID: {vinted_user_id})"
        )

        return {
            "success": True,
            "connected": True,
            "vinted_user_id": connection.vinted_user_id if connection else int(vinted_user_id),
            "login": connection.username if connection else login,
            "error": None,
        }

    except Exception as e:
        activity.logger.error(f"Check connection failed: {e}")
        return {
            "success": False,
            "connected": False,
            "vinted_user_id": None,
            "login": None,
            "error": str(e),
        }

    finally:
        db.close()


def _update_connection_status(
    db,
    user_id: int,
    connected: bool,
    vinted_user_id: int = None,
    login: str = None,
    user_data: dict = None,
):
    """Create or update VintedConnection record."""
    from models.user.vinted_connection import VintedConnection

    now = datetime.now(timezone.utc)

    connection = db.query(VintedConnection).filter(
        VintedConnection.user_id == user_id
    ).first()

    if connected:
        if connection:
            connection.connect(vinted_user_id=vinted_user_id, username=login)
        else:
            connection = VintedConnection(
                user_id=user_id,
                vinted_user_id=vinted_user_id,
                username=login,
                is_connected=True,
                created_at=now,
                last_synced_at=now,
            )
            db.add(connection)

        if user_data:
            connection.update_seller_stats(user_data)

        db.commit()
        return connection
    else:
        if connection:
            connection.disconnect()
            db.commit()
        return connection


# Export all activities for registration
VINTED_ACTION_ACTIVITIES = [
    vinted_publish_product,
    vinted_update_product,
    vinted_delete_product,
    vinted_sync_orders,
    vinted_send_message,
    vinted_link_product,
    vinted_fetch_users_page,
    vinted_save_prospects_batch,
    vinted_check_connection,
]
