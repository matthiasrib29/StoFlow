"""
Unified Workflow Management API Routes

Marketplace-agnostic endpoints for managing Temporal workflows:
- GET /workflows: List active workflows (with marketplace filter)
- GET /workflows/{workflow_id}/progress: Query workflow progress
- POST /workflows/{workflow_id}/cancel: Cancel a running workflow

These endpoints replace the per-marketplace job listing/management endpoints.

Author: Claude
Date: 2026-01-27
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.dependencies import get_user_db
from shared.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/workflows", tags=["Workflows"])


# ===== SCHEMAS =====


class WorkflowSummary(BaseModel):
    """Summary of a Temporal workflow."""

    workflow_id: str = Field(..., description="Temporal workflow ID")
    workflow_type: str = Field(..., description="Workflow type name")
    status: str = Field(..., description="Execution status (Running, Completed, Failed, etc.)")
    start_time: Optional[str] = Field(None, description="ISO timestamp when workflow started")
    marketplace: Optional[str] = Field(None, description="Marketplace (vinted, ebay, etsy)")


class WorkflowListResponse(BaseModel):
    """Response for listing workflows."""

    workflows: list[WorkflowSummary] = Field(default_factory=list)
    total: int = Field(0, description="Total matching workflows")


class WorkflowProgressResponse(BaseModel):
    """Response for workflow progress query."""

    workflow_id: str = Field(..., description="Temporal workflow ID")
    status: str = Field(..., description="Current status")
    result: Optional[dict] = Field(None, description="Result data if available")
    error: Optional[str] = Field(None, description="Error message if failed")


class WorkflowStartResponse(BaseModel):
    """Standard response when starting a workflow."""

    workflow_id: str = Field(..., description="Temporal workflow ID")
    status: str = Field("started", description="Always 'started'")


class CancelResponse(BaseModel):
    """Response for cancel request."""

    workflow_id: str = Field(..., description="Temporal workflow ID")
    status: str = Field(..., description="Cancel status")


# ===== HELPERS =====


def _extract_marketplace(workflow_id: str) -> Optional[str]:
    """Extract marketplace from workflow ID convention: {marketplace}-{action}-user-..."""
    for mp in ("vinted", "ebay", "etsy"):
        if workflow_id.startswith(mp):
            return mp
    return None


# ===== ENDPOINTS =====


@router.get("", response_model=WorkflowListResponse)
async def list_workflows(
    user_db: tuple = Depends(get_user_db),
    marketplace: Optional[str] = Query(None, description="Filter by marketplace (vinted, ebay, etsy)"),
    workflow_status: str = Query("Running", description="Execution status filter (Running, Completed, Failed)"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
):
    """
    List Temporal workflows for the current user.

    Supports filtering by marketplace and execution status.
    """
    from temporal.client import get_temporal_client
    from temporal.config import get_temporal_config

    config = get_temporal_config()

    if not config.temporal_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal is disabled",
        )

    db, current_user = user_db

    # Build Temporal query
    query_parts = [
        f'ExecutionStatus = "{workflow_status}"',
    ]

    # Filter by user (all our workflow IDs contain user-{id})
    query_parts.append(f'WorkflowId LIKE "%user-{current_user.id}%"')

    # Filter by marketplace via workflow type prefix
    if marketplace:
        mp_prefix = marketplace.capitalize()
        query_parts.append(f'WorkflowType LIKE "{mp_prefix}%"')

    query = " AND ".join(query_parts)

    try:
        client = await get_temporal_client()
        workflows = []

        async for wf in client.list_workflows(query=query):
            if len(workflows) >= limit:
                break

            workflows.append(
                WorkflowSummary(
                    workflow_id=wf.id,
                    workflow_type=wf.workflow_type,
                    status=wf.status.name if wf.status else workflow_status,
                    start_time=wf.start_time.isoformat() if wf.start_time else None,
                    marketplace=_extract_marketplace(wf.id),
                )
            )

        return WorkflowListResponse(workflows=workflows, total=len(workflows))

    except Exception as e:
        logger.error(f"Failed to list workflows for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workflows: {str(e)}",
        )


@router.get("/{workflow_id}/progress", response_model=WorkflowProgressResponse)
async def get_workflow_progress(
    workflow_id: str,
    user_db: tuple = Depends(get_user_db),
):
    """
    Query workflow progress via Temporal query.

    All workflows implement get_progress() query returning
    {status, result, error}.
    """
    from temporal.client import get_temporal_client
    from temporal.config import get_temporal_config

    config = get_temporal_config()

    if not config.temporal_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal is disabled",
        )

    db, current_user = user_db

    # Verify workflow belongs to this user
    if f"user-{current_user.id}" not in workflow_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this workflow",
        )

    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)

        progress = await handle.query("get_progress")

        return WorkflowProgressResponse(
            workflow_id=workflow_id,
            **progress,
        )

    except Exception as e:
        logger.error(f"Failed to get progress for workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow progress: {str(e)}",
        )


@router.post("/{workflow_id}/cancel", response_model=CancelResponse)
async def cancel_workflow(
    workflow_id: str,
    user_db: tuple = Depends(get_user_db),
):
    """
    Cancel a running workflow.

    Sends a 'cancel' signal. Workflows with cooperative cancellation
    will stop gracefully after completing current activity.
    Simple workflows are cancelled via Temporal cancellation.
    """
    from temporal.client import get_temporal_client
    from temporal.config import get_temporal_config

    config = get_temporal_config()

    if not config.temporal_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal is disabled",
        )

    db, current_user = user_db

    # Verify workflow belongs to this user
    if f"user-{current_user.id}" not in workflow_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this workflow",
        )

    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)

        # Try signal-based cancel first (cooperative)
        try:
            await handle.signal("cancel")
        except Exception:
            # Fallback to Temporal cancellation
            await handle.cancel()

        logger.info(f"Sent cancel to workflow {workflow_id}")

        return CancelResponse(
            workflow_id=workflow_id,
            status="cancel_requested",
        )

    except Exception as e:
        logger.error(f"Failed to cancel workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel workflow: {str(e)}",
        )
