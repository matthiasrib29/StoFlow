"""
Etsy Products & Listings Routes

Endpoints for product publication and listing management.

Author: Claude
Date: 2025-12-17
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import get_user_db
from api.workflows import WorkflowStartResponse
from models.user.product import Product
from services.etsy import (
    EtsyListingClient,
    ProductValidationError,
)
from shared.logging import get_logger

from .schemas import (
    ListingResponse,
    PublishProductRequest,
    PublishProductResponse,
    UpdateListingRequest,
)

router = APIRouter()
logger = get_logger(__name__)


# ========== PRODUCT PUBLICATION ==========


@router.post("/products/publish", response_model=WorkflowStartResponse)
async def publish_product_to_etsy(
    request: PublishProductRequest,
    user_db: tuple = Depends(get_user_db),
):
    """
    Publish a product to Etsy via Temporal workflow.

    Starts EtsyPublishWorkflow and returns immediately.
    Track progress via GET /workflows/{workflow_id}/progress.

    Args:
        request: Publication data (product_id, taxonomy_id, etc.)

    Returns:
        WorkflowStartResponse with workflow_id
    """
    from temporal.client import get_temporal_client
    from temporal.config import get_temporal_config
    from temporal.workflows.etsy.publish_workflow import EtsyPublishParams, EtsyPublishWorkflow

    config = get_temporal_config()
    if not config.temporal_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal is disabled",
        )

    db, current_user = user_db

    # Validate product exists
    product = (
        db.query(Product)
        .filter(
            Product.id == request.product_id,
            Product.user_id == current_user.id,
        )
        .first()
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {request.product_id} not found",
        )

    workflow_id = f"etsy-publish-user-{current_user.id}-product-{request.product_id}"
    params = EtsyPublishParams(
        user_id=current_user.id,
        product_id=request.product_id,
        taxonomy_id=request.taxonomy_id,
        shipping_profile_id=request.shipping_profile_id or 0,
        return_policy_id=request.return_policy_id or 0,
        shop_section_id=request.shop_section_id or 0,
        state=request.state or "draft",
    )

    client = await get_temporal_client()
    await client.start_workflow(
        EtsyPublishWorkflow.run,
        params,
        id=workflow_id,
        task_queue=config.temporal_task_queue,
    )

    logger.info(f"Started Etsy publish workflow: {workflow_id}")
    return WorkflowStartResponse(workflow_id=workflow_id, status="started")


@router.put("/products/{listing_id}", response_model=WorkflowStartResponse)
async def update_etsy_listing(
    listing_id: int,
    request: UpdateListingRequest,
    user_db: tuple = Depends(get_user_db),
):
    """
    Update an Etsy listing via Temporal workflow.

    Starts EtsyUpdateWorkflow and returns immediately.

    Args:
        listing_id: Etsy listing ID to update
        request.product_id: Source Stoflow product ID

    Returns:
        WorkflowStartResponse with workflow_id
    """
    from temporal.client import get_temporal_client
    from temporal.config import get_temporal_config
    from temporal.workflows.etsy.update_workflow import EtsyUpdateParams, EtsyUpdateWorkflow

    config = get_temporal_config()
    if not config.temporal_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal is disabled",
        )

    db, current_user = user_db

    workflow_id = f"etsy-update-user-{current_user.id}-product-{request.product_id}"
    params = EtsyUpdateParams(
        user_id=current_user.id,
        product_id=request.product_id,
    )

    client = await get_temporal_client()
    await client.start_workflow(
        EtsyUpdateWorkflow.run,
        params,
        id=workflow_id,
        task_queue=config.temporal_task_queue,
    )

    logger.info(f"Started Etsy update workflow: {workflow_id}")
    return WorkflowStartResponse(workflow_id=workflow_id, status="started")


@router.delete("/products/{listing_id}", response_model=WorkflowStartResponse)
async def delete_etsy_listing(
    listing_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """
    Delete an Etsy listing via Temporal workflow.

    Starts EtsyDeleteWorkflow and returns immediately.

    Args:
        listing_id: Etsy listing ID to delete

    Returns:
        WorkflowStartResponse with workflow_id
    """
    from temporal.client import get_temporal_client
    from temporal.config import get_temporal_config
    from temporal.workflows.etsy.delete_workflow import EtsyDeleteParams, EtsyDeleteWorkflow

    config = get_temporal_config()
    if not config.temporal_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal is disabled",
        )

    db, current_user = user_db

    # For Etsy delete, we need the product_id. The listing_id maps to an EtsyProduct.
    # The activity will look up the listing_id from the product_id.
    # Since the endpoint receives listing_id, we need to find the product_id.
    from models.user.etsy_product import EtsyProduct

    etsy_product = (
        db.query(EtsyProduct)
        .filter(EtsyProduct.listing_id == listing_id)
        .first()
    )
    if not etsy_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Etsy listing {listing_id} not found",
        )

    workflow_id = f"etsy-delete-user-{current_user.id}-listing-{listing_id}"
    params = EtsyDeleteParams(
        user_id=current_user.id,
        product_id=etsy_product.product_id,
    )

    client = await get_temporal_client()
    await client.start_workflow(
        EtsyDeleteWorkflow.run,
        params,
        id=workflow_id,
        task_queue=config.temporal_task_queue,
    )

    logger.info(f"Started Etsy delete workflow: {workflow_id}")
    return WorkflowStartResponse(workflow_id=workflow_id, status="started")


# ========== LISTINGS MANAGEMENT ==========


@router.get("/listings/active", response_model=List[ListingResponse])
def get_active_listings(
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_db: tuple = Depends(get_user_db),
):
    """
    Recupere les listings actifs du shop Etsy.
    """
    db, current_user = user_db

    try:
        client = EtsyListingClient(db, current_user.id)
        result = client.get_shop_listings_active(limit=limit, offset=offset)

        listings = result.get("results", [])

        return [
            ListingResponse(
                listing_id=listing["listing_id"],
                title=listing["title"],
                state=listing["state"],
                price=float(listing["price"]["amount"]) / listing["price"]["divisor"],
                quantity=listing["quantity"],
                url=listing.get("url"),
                created_timestamp=listing.get("created_timestamp"),
                updated_timestamp=listing.get("updated_timestamp"),
            )
            for listing in listings
        ]

    except Exception as e:
        logger.error(f"Error getting active listings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting listings: {str(e)}",
        )


@router.get("/listings/{listing_id}")
def get_listing_details(
    listing_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """
    Recupere les details d'un listing Etsy.
    """
    db, current_user = user_db

    try:
        client = EtsyListingClient(db, current_user.id)
        listing = client.get_listing(listing_id)

        return listing

    except Exception as e:
        logger.error(f"Error getting listing {listing_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting listing: {str(e)}",
        )
