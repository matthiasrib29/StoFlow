"""
Vinted Publishing Routes

Endpoints pour la publication des produits:
- POST /products/{product_id}/publish: Publication via Temporal workflow
- POST /products/{product_id}/update: Update via Temporal workflow
- POST /products/{product_id}/delete: Delete from marketplace via Temporal workflow

Updated: 2025-12-19 - Intégration système de jobs
Updated: 2026-01-05 - Suppression endpoint prepare
Updated: 2026-01-27 - Migration vers Temporal workflows

Author: Claude
Date: 2025-12-17
"""

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_user_db
from api.workflows import WorkflowStartResponse
from shared.logging import get_logger
from .shared import get_active_vinted_connection

logger = get_logger(__name__)
router = APIRouter()


async def _start_vinted_workflow(
    workflow_class,
    params,
    workflow_id: str,
    task_queue: str,
) -> WorkflowStartResponse:
    """Start a Vinted Temporal workflow and return standard response."""
    from temporal.client import get_temporal_client

    client = await get_temporal_client()

    await client.start_workflow(
        workflow_class.run,
        params,
        id=workflow_id,
        task_queue=task_queue,
    )

    logger.info(f"Started workflow: {workflow_id}")

    return WorkflowStartResponse(workflow_id=workflow_id, status="started")


def _check_temporal_enabled():
    """Check Temporal is enabled, raise 503 if not."""
    from temporal.config import get_temporal_config

    config = get_temporal_config()
    if not config.temporal_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal is disabled",
        )
    return config


@router.post("/products/{product_id}/publish", response_model=WorkflowStartResponse)
async def publish_product(
    product_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """
    Publish a product to Vinted via Temporal workflow.

    Starts VintedPublishWorkflow and returns immediately.
    Track progress via GET /workflows/{workflow_id}/progress.

    Args:
        product_id: ID of the product to publish

    Returns:
        WorkflowStartResponse with workflow_id
    """
    config = _check_temporal_enabled()
    db, current_user = user_db
    connection = get_active_vinted_connection(db, current_user.id)

    from temporal.workflows.vinted.publish_workflow import VintedPublishParams, VintedPublishWorkflow

    workflow_id = f"vinted-publish-user-{current_user.id}-product-{product_id}"
    params = VintedPublishParams(
        user_id=current_user.id,
        product_id=product_id,
        shop_id=connection.vinted_user_id,
    )

    return await _start_vinted_workflow(
        VintedPublishWorkflow, params, workflow_id, config.temporal_vinted_task_queue,
    )


@router.post("/products/{product_id}/update", response_model=WorkflowStartResponse)
async def update_product_on_marketplace(
    product_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """
    Update a product on Vinted via Temporal workflow.

    Starts VintedUpdateWorkflow and returns immediately.

    Args:
        product_id: ID of the product to update

    Returns:
        WorkflowStartResponse with workflow_id
    """
    config = _check_temporal_enabled()
    db, current_user = user_db
    connection = get_active_vinted_connection(db, current_user.id)

    from temporal.workflows.vinted.update_workflow import VintedUpdateParams, VintedUpdateWorkflow

    workflow_id = f"vinted-update-user-{current_user.id}-product-{product_id}"
    params = VintedUpdateParams(
        user_id=current_user.id,
        product_id=product_id,
        shop_id=connection.vinted_user_id,
    )

    return await _start_vinted_workflow(
        VintedUpdateWorkflow, params, workflow_id, config.temporal_vinted_task_queue,
    )


@router.post("/products/{product_id}/delete-listing", response_model=WorkflowStartResponse)
async def delete_product_from_marketplace(
    product_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """
    Delete a product listing from Vinted via Temporal workflow.

    This deletes the listing on Vinted (not the local DB record).

    Args:
        product_id: ID of the product to delete from marketplace

    Returns:
        WorkflowStartResponse with workflow_id
    """
    config = _check_temporal_enabled()
    db, current_user = user_db
    connection = get_active_vinted_connection(db, current_user.id)

    from temporal.workflows.vinted.delete_workflow import VintedDeleteParams, VintedDeleteWorkflow

    workflow_id = f"vinted-delete-user-{current_user.id}-product-{product_id}"
    params = VintedDeleteParams(
        user_id=current_user.id,
        product_id=product_id,
        shop_id=connection.vinted_user_id,
    )

    return await _start_vinted_workflow(
        VintedDeleteWorkflow, params, workflow_id, config.temporal_vinted_task_queue,
    )
