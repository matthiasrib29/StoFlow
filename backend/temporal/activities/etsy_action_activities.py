"""
Etsy Action Activities for Temporal.

These activities wrap existing Etsy services to execute marketplace actions
(publish, update, delete) via Temporal workflows.

Each activity is designed to be:
- Idempotent where possible
- Retryable (Temporal handles retry policy)
- Independent (no shared state between activities)

IMPORTANT: Activities are defined as regular `def` (not `async def`) because:
- The Etsy client uses `requests` (synchronous HTTP library)
- Temporal executes sync activities in a threadpool
- This allows true parallel execution

Author: Claude
Date: 2026-01-27
"""

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
# PUBLISH
# ═══════════════════════════════════════════════════════════════════


@activity.defn(name="etsy_publish_product")
def etsy_publish_product(
    user_id: int,
    product_id: int,
    taxonomy_id: int,
    shipping_profile_id: int = 0,
    return_policy_id: int = 0,
    shop_section_id: int = 0,
    state: str = "draft",
) -> dict:
    """
    Publish a product to Etsy via direct API.

    Loads the Product from DB and delegates to EtsyPublicationService.

    Args:
        user_id: User ID for OAuth credentials and schema
        product_id: StoFlow product ID to publish
        taxonomy_id: Etsy category/taxonomy ID (required)
        shipping_profile_id: Etsy shipping profile ID (0 = None)
        return_policy_id: Etsy return policy ID (0 = None)
        shop_section_id: Etsy shop section ID (0 = None)
        state: Listing state ("draft" or "active")

    Returns:
        Dict with 'success', 'listing_id', 'listing_url', 'state', 'error'
    """
    activity.logger.info(
        f"Publishing product #{product_id} to Etsy (taxonomy={taxonomy_id}, state={state})"
    )

    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from models.user.product import Product
        from services.etsy.etsy_publication_service import EtsyPublicationService

        # Load product from DB
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {
                "success": False,
                "listing_id": None,
                "error": f"Product #{product_id} not found",
            }

        service = EtsyPublicationService(db, user_id)
        result = service.publish_product(
            product=product,
            taxonomy_id=taxonomy_id,
            shipping_profile_id=shipping_profile_id if shipping_profile_id > 0 else None,
            return_policy_id=return_policy_id if return_policy_id > 0 else None,
            shop_section_id=shop_section_id if shop_section_id > 0 else None,
            state=state,
        )

        if result.get("success"):
            activity.logger.info(
                f"Product #{product_id} published to Etsy "
                f"(listing_id={result.get('listing_id')})"
            )
        else:
            activity.logger.warning(
                f"Product #{product_id} Etsy publish failed: {result.get('error')}"
            )

        return result

    except Exception as e:
        activity.logger.error(f"Etsy publish failed for product #{product_id}: {e}")
        return {"success": False, "listing_id": None, "error": str(e)}

    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════
# UPDATE
# ═══════════════════════════════════════════════════════════════════


@activity.defn(name="etsy_update_product")
def etsy_update_product(
    user_id: int,
    product_id: int,
) -> dict:
    """
    Update a product listing on Etsy via direct API.

    Loads the Product and its EtsyProduct from DB to get the listing_id,
    then delegates to EtsyPublicationService.

    Args:
        user_id: User ID for OAuth credentials and schema
        product_id: StoFlow product ID to update

    Returns:
        Dict with 'success', 'listing_id', 'error'
    """
    activity.logger.info(f"Updating product #{product_id} on Etsy")

    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from models.user.product import Product
        from models.user.etsy_product import EtsyProduct
        from services.etsy.etsy_publication_service import EtsyPublicationService

        # Load product and Etsy listing
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {
                "success": False,
                "listing_id": None,
                "error": f"Product #{product_id} not found",
            }

        etsy_product = db.query(EtsyProduct).filter(
            EtsyProduct.product_id == product_id
        ).first()
        if not etsy_product or not etsy_product.etsy_listing_id:
            return {
                "success": False,
                "listing_id": None,
                "error": f"No Etsy listing found for product #{product_id}",
            }

        service = EtsyPublicationService(db, user_id)
        result = service.update_product(
            product=product,
            listing_id=etsy_product.etsy_listing_id,
        )

        if result.get("success"):
            activity.logger.info(
                f"Product #{product_id} updated on Etsy "
                f"(listing_id={etsy_product.etsy_listing_id})"
            )
        else:
            activity.logger.warning(
                f"Product #{product_id} Etsy update failed: {result.get('error')}"
            )

        return result

    except Exception as e:
        activity.logger.error(f"Etsy update failed for product #{product_id}: {e}")
        return {"success": False, "listing_id": None, "error": str(e)}

    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════
# DELETE
# ═══════════════════════════════════════════════════════════════════


@activity.defn(name="etsy_delete_product")
def etsy_delete_product(
    user_id: int,
    product_id: int,
) -> dict:
    """
    Delete a product listing from Etsy via direct API.

    Loads EtsyProduct from DB to get the listing_id, then delegates
    to EtsyPublicationService.

    Args:
        user_id: User ID for OAuth credentials and schema
        product_id: StoFlow product ID to delete

    Returns:
        Dict with 'success', 'product_id', 'error'
    """
    activity.logger.info(f"Deleting product #{product_id} from Etsy")

    db = SessionLocal()
    try:
        _configure_session(db, user_id)

        from models.user.etsy_product import EtsyProduct
        from services.etsy.etsy_publication_service import EtsyPublicationService

        etsy_product = db.query(EtsyProduct).filter(
            EtsyProduct.product_id == product_id
        ).first()
        if not etsy_product or not etsy_product.etsy_listing_id:
            return {
                "success": False,
                "product_id": product_id,
                "error": f"No Etsy listing found for product #{product_id}",
            }

        service = EtsyPublicationService(db, user_id)
        result = service.delete_product(
            listing_id=etsy_product.etsy_listing_id,
        )

        if result.get("success"):
            activity.logger.info(
                f"Product #{product_id} deleted from Etsy "
                f"(listing_id={etsy_product.etsy_listing_id})"
            )
        else:
            activity.logger.warning(
                f"Product #{product_id} Etsy delete failed: {result.get('error')}"
            )

        return {**result, "product_id": product_id}

    except Exception as e:
        activity.logger.error(f"Etsy delete failed for product #{product_id}: {e}")
        return {"success": False, "product_id": product_id, "error": str(e)}

    finally:
        db.close()


# Export all activities for registration
ETSY_ACTION_ACTIVITIES = [
    etsy_publish_product,
    etsy_update_product,
    etsy_delete_product,
]
