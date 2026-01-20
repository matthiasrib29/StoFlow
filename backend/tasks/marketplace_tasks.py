"""
Celery tasks for marketplace operations.

Handles publication, sync, and deletion for all marketplaces (Vinted, eBay, Etsy).
"""
import asyncio
from typing import Any

from celery import shared_task
from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session

from shared.database import SessionLocal
from shared.exceptions import MarketplaceError

logger = get_task_logger(__name__)


def get_user_session(user_id: int) -> Session:
    """
    Create a database session with tenant schema configured.

    Args:
        user_id: User ID for schema isolation

    Returns:
        SQLAlchemy session with schema_translate_map set
    """
    session = SessionLocal()
    schema_name = f"user_{user_id}"
    session = session.execution_options(
        schema_translate_map={"tenant": schema_name}
    )
    return session


def run_async(coro):
    """Run an async coroutine from sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# =============================================================================
# PUBLISH TASKS
# =============================================================================

@shared_task(
    bind=True,
    name="tasks.marketplace_tasks.publish_product",
    autoretry_for=(MarketplaceError, TimeoutError, ConnectionError),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=5,
    acks_late=True,
)
def publish_product(
    self,
    product_id: int,
    user_id: int,
    marketplace: str,
    shop_id: int | None = None,
    marketplace_id: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    """
    Publish a product to a marketplace.

    Args:
        product_id: Product ID to publish
        user_id: User ID for schema isolation
        marketplace: Target marketplace (vinted, ebay, etsy)
        shop_id: Shop ID (required for Vinted)
        marketplace_id: Marketplace ID for eBay (e.g., EBAY_FR)
        **kwargs: Additional marketplace-specific parameters

    Returns:
        Dict with publication result
    """
    logger.info(
        f"Publishing product {product_id} to {marketplace} "
        f"(user={user_id}, attempt={self.request.retries + 1})"
    )

    db = get_user_session(user_id)
    try:
        if marketplace == "vinted":
            result = _publish_vinted(db, product_id, user_id, shop_id)
        elif marketplace == "ebay":
            result = _publish_ebay(
                db, product_id, user_id, marketplace_id or "EBAY_FR", **kwargs
            )
        elif marketplace == "etsy":
            result = _publish_etsy(db, product_id, user_id, **kwargs)
        else:
            raise ValueError(f"Unknown marketplace: {marketplace}")

        logger.info(f"Published product {product_id} to {marketplace}: {result}")
        return result

    except Exception as exc:
        logger.error(
            f"Failed to publish product {product_id} to {marketplace}: {exc}",
            exc_info=True,
        )
        db.rollback()
        raise
    finally:
        db.close()


def _publish_vinted(
    db: Session,
    product_id: int,
    user_id: int,
    shop_id: int | None,
) -> dict[str, Any]:
    """
    Create a MarketplaceJob for Vinted publish (cannot execute directly).

    Celery workers don't have WebSocket access, so we create a MarketplaceJob
    and notify the frontend to execute it via the browser plugin.

    The frontend will:
    1. Receive 'vinted_job_pending' WebSocket event
    2. Execute the job via the plugin
    3. Call PATCH /api/vinted/jobs/{job_id}/complete or /fail
    """
    from services.vinted.vinted_job_bridge_service import VintedJobBridgeService

    bridge = VintedJobBridgeService(db)
    return bridge.queue_publish(product_id, user_id, shop_id)


def _publish_ebay(
    db: Session,
    product_id: int,
    user_id: int,
    marketplace_id: str,
    category_id: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Publish product to eBay via direct API."""
    from services.ebay.ebay_publication_service import EbayPublicationService

    service = EbayPublicationService(db, user_id)
    # EbayPublicationService.publish_product is sync
    result = service.publish_product(
        product_id=product_id,
        marketplace_id=marketplace_id,
        category_id=category_id,
    )

    if not result.get("success"):
        raise MarketplaceError(result.get("error", "Unknown eBay error"))

    return result


def _publish_etsy(
    db: Session,
    product_id: int,
    user_id: int,
    taxonomy_id: int | None = None,
    shipping_profile_id: int | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Publish product to Etsy via direct API."""
    from services.etsy.etsy_publication_service import EtsyPublicationService
    from models.user.product import Product

    # Load product
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise ValueError(f"Product {product_id} not found")

    service = EtsyPublicationService(db, user_id)
    # EtsyPublicationService.publish_product is sync
    result = service.publish_product(
        product=product,
        taxonomy_id=taxonomy_id,
        shipping_profile_id=shipping_profile_id,
        state="active",
    )

    if not result.get("success"):
        raise MarketplaceError(result.get("error", "Unknown Etsy error"))

    return result


# =============================================================================
# UPDATE TASKS
# =============================================================================

@shared_task(
    bind=True,
    name="tasks.marketplace_tasks.update_listing",
    autoretry_for=(MarketplaceError, TimeoutError, ConnectionError),
    retry_backoff=True,
    retry_backoff_max=300,
    max_retries=3,
    acks_late=True,
)
def update_listing(
    self,
    product_id: int,
    user_id: int,
    marketplace: str,
    **kwargs,
) -> dict[str, Any]:
    """
    Update a marketplace listing.

    Args:
        product_id: Product ID to update
        user_id: User ID for schema isolation
        marketplace: Target marketplace (vinted, ebay, etsy)
        **kwargs: Additional marketplace-specific parameters

    Returns:
        Dict with update result
    """
    logger.info(
        f"Updating listing for product {product_id} on {marketplace} "
        f"(user={user_id}, attempt={self.request.retries + 1})"
    )

    db = get_user_session(user_id)
    try:
        if marketplace == "vinted":
            result = _update_vinted(db, product_id, user_id, **kwargs)
        elif marketplace == "ebay":
            result = _update_ebay(db, product_id, user_id, **kwargs)
        elif marketplace == "etsy":
            result = _update_etsy(db, product_id, user_id, **kwargs)
        else:
            raise ValueError(f"Unknown marketplace: {marketplace}")

        logger.info(f"Updated listing for product {product_id} on {marketplace}")
        return result

    except Exception as exc:
        logger.error(
            f"Failed to update listing for product {product_id} on {marketplace}: {exc}",
            exc_info=True,
        )
        db.rollback()
        raise
    finally:
        db.close()


def _update_vinted(db: Session, product_id: int, user_id: int, **kwargs) -> dict:
    """
    Create a MarketplaceJob for Vinted update (cannot execute directly).

    See _publish_vinted() for architecture explanation.
    """
    from services.vinted.vinted_job_bridge_service import VintedJobBridgeService

    bridge = VintedJobBridgeService(db)
    return bridge.queue_update(product_id, user_id, **kwargs)


def _update_ebay(db: Session, product_id: int, user_id: int, **kwargs) -> dict:
    """Update eBay listing."""
    from services.ebay.ebay_update_service import EbayUpdateService

    service = EbayUpdateService(db, user_id)
    result = service.update_product(product_id=product_id, **kwargs)
    if not result.get("success"):
        raise MarketplaceError(result.get("error", "Unknown eBay update error"))
    return result


def _update_etsy(db: Session, product_id: int, user_id: int, **kwargs) -> dict:
    """Update Etsy listing."""
    from services.etsy.etsy_update_service import EtsyUpdateService

    service = EtsyUpdateService(db, user_id)
    result = service.update_product(product_id=product_id, **kwargs)
    if not result.get("success"):
        raise MarketplaceError(result.get("error", "Unknown Etsy update error"))
    return result


# =============================================================================
# DELETE TASKS
# =============================================================================

@shared_task(
    bind=True,
    name="tasks.marketplace_tasks.delete_listing",
    autoretry_for=(MarketplaceError, TimeoutError, ConnectionError),
    retry_backoff=True,
    retry_backoff_max=300,
    max_retries=3,
    acks_late=True,
)
def delete_listing(
    self,
    product_id: int,
    user_id: int,
    marketplace: str,
    **kwargs,
) -> dict[str, Any]:
    """
    Delete a marketplace listing.

    Args:
        product_id: Product ID whose listing to delete
        user_id: User ID for schema isolation
        marketplace: Target marketplace (vinted, ebay, etsy)

    Returns:
        Dict with deletion result
    """
    logger.info(
        f"Deleting listing for product {product_id} on {marketplace} "
        f"(user={user_id}, attempt={self.request.retries + 1})"
    )

    db = get_user_session(user_id)
    try:
        if marketplace == "vinted":
            result = _delete_vinted(db, product_id, user_id, **kwargs)
        elif marketplace == "ebay":
            result = _delete_ebay(db, product_id, user_id, **kwargs)
        elif marketplace == "etsy":
            result = _delete_etsy(db, product_id, user_id, **kwargs)
        else:
            raise ValueError(f"Unknown marketplace: {marketplace}")

        logger.info(f"Deleted listing for product {product_id} on {marketplace}")
        return result

    except Exception as exc:
        logger.error(
            f"Failed to delete listing for product {product_id} on {marketplace}: {exc}",
            exc_info=True,
        )
        db.rollback()
        raise
    finally:
        db.close()


def _delete_vinted(db: Session, product_id: int, user_id: int, **kwargs) -> dict:
    """
    Create a MarketplaceJob for Vinted delete (cannot execute directly).

    See _publish_vinted() for architecture explanation.
    """
    from services.vinted.vinted_job_bridge_service import VintedJobBridgeService

    bridge = VintedJobBridgeService(db)
    return bridge.queue_delete(product_id, user_id, **kwargs)


def _delete_ebay(db: Session, product_id: int, user_id: int, **kwargs) -> dict:
    """Delete eBay listing."""
    from services.ebay.ebay_delete_service import EbayDeleteService

    service = EbayDeleteService(db, user_id)
    result = service.delete_product(product_id=product_id, **kwargs)
    if not result.get("success"):
        raise MarketplaceError(result.get("error", "Unknown eBay delete error"))
    return result


def _delete_etsy(db: Session, product_id: int, user_id: int, **kwargs) -> dict:
    """Delete Etsy listing."""
    from services.etsy.etsy_delete_service import EtsyDeleteService

    service = EtsyDeleteService(db, user_id)
    result = service.delete_product(product_id=product_id, **kwargs)
    if not result.get("success"):
        raise MarketplaceError(result.get("error", "Unknown Etsy delete error"))
    return result


# =============================================================================
# SYNC TASKS
# =============================================================================

@shared_task(
    bind=True,
    name="tasks.marketplace_tasks.sync_inventory",
    autoretry_for=(MarketplaceError, TimeoutError, ConnectionError),
    retry_backoff=60,
    max_retries=3,
    acks_late=True,
)
def sync_inventory(
    self,
    user_id: int,
    marketplace: str,
    shop_id: int | None = None,
    **kwargs,
) -> dict[str, Any]:
    """
    Sync inventory from a marketplace.

    Args:
        user_id: User ID for schema isolation
        marketplace: Source marketplace (vinted, ebay, etsy)
        shop_id: Shop ID (required for Vinted)

    Returns:
        Dict with sync result
    """
    logger.info(
        f"Syncing inventory from {marketplace} "
        f"(user={user_id}, attempt={self.request.retries + 1})"
    )

    db = get_user_session(user_id)
    try:
        if marketplace == "vinted":
            result = _sync_vinted_inventory(db, user_id, shop_id, **kwargs)
        elif marketplace == "ebay":
            result = _sync_ebay_inventory(db, user_id, **kwargs)
        elif marketplace == "etsy":
            result = _sync_etsy_inventory(db, user_id, **kwargs)
        else:
            raise ValueError(f"Unknown marketplace: {marketplace}")

        logger.info(f"Synced inventory from {marketplace}: {result}")
        return result

    except Exception as exc:
        logger.error(
            f"Failed to sync inventory from {marketplace}: {exc}",
            exc_info=True,
        )
        db.rollback()
        raise
    finally:
        db.close()


def _sync_vinted_inventory(db: Session, user_id: int, shop_id: int | None, **kwargs) -> dict:
    """Sync Vinted inventory."""
    from services.vinted.vinted_sync_service import VintedSyncService

    service = VintedSyncService(db)
    result = run_async(
        service.sync_inventory(user_id=user_id, shop_id=shop_id, **kwargs)
    )
    return result


def _sync_ebay_inventory(db: Session, user_id: int, **kwargs) -> dict:
    """Sync eBay inventory."""
    from services.ebay.ebay_sync_service import EbaySyncService

    service = EbaySyncService(db, user_id)
    result = service.sync_inventory(**kwargs)
    return result


def _sync_etsy_inventory(db: Session, user_id: int, **kwargs) -> dict:
    """Sync Etsy inventory."""
    from services.etsy.etsy_sync_service import EtsySyncService

    service = EtsySyncService(db, user_id)
    result = service.sync_inventory(**kwargs)
    return result


# =============================================================================
# ORDERS SYNC TASKS
# =============================================================================

@shared_task(
    bind=True,
    name="tasks.marketplace_tasks.sync_orders",
    autoretry_for=(MarketplaceError, TimeoutError, ConnectionError),
    retry_backoff=60,
    max_retries=3,
    acks_late=True,
)
def sync_orders(
    self,
    user_id: int,
    marketplace: str,
    shop_id: int | None = None,
    **kwargs,
) -> dict[str, Any]:
    """
    Sync orders from a marketplace.

    Args:
        user_id: User ID for schema isolation
        marketplace: Source marketplace (vinted, ebay, etsy)
        shop_id: Shop ID (required for Vinted)

    Returns:
        Dict with sync result
    """
    logger.info(
        f"Syncing orders from {marketplace} "
        f"(user={user_id}, attempt={self.request.retries + 1})"
    )

    db = get_user_session(user_id)
    try:
        if marketplace == "vinted":
            result = _sync_vinted_orders(db, user_id, shop_id, **kwargs)
        elif marketplace == "ebay":
            result = _sync_ebay_orders(db, user_id, **kwargs)
        elif marketplace == "etsy":
            result = _sync_etsy_orders(db, user_id, **kwargs)
        else:
            raise ValueError(f"Unknown marketplace: {marketplace}")

        logger.info(f"Synced orders from {marketplace}: {result}")
        return result

    except Exception as exc:
        logger.error(
            f"Failed to sync orders from {marketplace}: {exc}",
            exc_info=True,
        )
        db.rollback()
        raise
    finally:
        db.close()


def _sync_vinted_orders(db: Session, user_id: int, shop_id: int | None, **kwargs) -> dict:
    """Sync Vinted orders."""
    from services.vinted.vinted_orders_service import VintedOrdersService

    service = VintedOrdersService(db)
    result = run_async(
        service.sync_orders(user_id=user_id, shop_id=shop_id, **kwargs)
    )
    return result


def _sync_ebay_orders(db: Session, user_id: int, **kwargs) -> dict:
    """Sync eBay orders."""
    from services.ebay.ebay_orders_service import EbayOrdersService

    service = EbayOrdersService(db, user_id)
    result = service.sync_orders(**kwargs)
    return result


def _sync_etsy_orders(db: Session, user_id: int, **kwargs) -> dict:
    """Sync Etsy orders."""
    from services.etsy.etsy_orders_service import EtsyOrdersService

    service = EtsyOrdersService(db, user_id)
    result = service.sync_orders(**kwargs)
    return result


# =============================================================================
# PERIODIC TASKS
# =============================================================================

@shared_task(
    bind=True,
    name="tasks.marketplace_tasks.sync_all_marketplace_orders",
    max_retries=1,
)
def sync_all_marketplace_orders(self) -> dict[str, Any]:
    """
    Periodic task to sync orders from all marketplaces for all active users.

    This task is called by Celery beat every 15 minutes.
    """
    logger.info("Starting periodic orders sync for all users")

    from models.public.user import User
    from shared.database import SessionLocal

    db = SessionLocal()
    try:
        # Get all active users with marketplace integrations
        users = db.query(User).filter(User.is_active == True).all()

        results = {
            "total_users": len(users),
            "vinted_synced": 0,
            "ebay_synced": 0,
            "etsy_synced": 0,
            "errors": [],
        }

        for user in users:
            # Queue individual sync tasks for each user/marketplace
            # This allows them to run in parallel
            try:
                # Check if user has Vinted integration
                # TODO: Add proper integration check
                sync_orders.delay(
                    user_id=user.id,
                    marketplace="vinted",
                )
                results["vinted_synced"] += 1
            except Exception as e:
                results["errors"].append(f"Vinted user {user.id}: {str(e)}")

            try:
                # Check if user has eBay integration
                sync_orders.delay(
                    user_id=user.id,
                    marketplace="ebay",
                )
                results["ebay_synced"] += 1
            except Exception as e:
                results["errors"].append(f"eBay user {user.id}: {str(e)}")

            try:
                # Check if user has Etsy integration
                sync_orders.delay(
                    user_id=user.id,
                    marketplace="etsy",
                )
                results["etsy_synced"] += 1
            except Exception as e:
                results["errors"].append(f"Etsy user {user.id}: {str(e)}")

        logger.info(f"Periodic orders sync completed: {results}")
        return results

    finally:
        db.close()
