"""
eBay Temporal Sync API Routes

Endpoints for eBay product sync via Temporal workflows:
- Start sync workflow
- Get workflow progress
- Cancel running workflow
- Health check for Temporal connection

These routes use Temporal for durable execution:
- Survives backend crashes/restarts
- Automatic retries with backoff
- Real-time progress tracking
- Cancellation support

Author: Claude
Date: 2026-01-21
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.dependencies import get_user_db
from shared.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/ebay/temporal", tags=["eBay Temporal"])


# ===== SCHEMAS =====


class TemporalHealthResponse(BaseModel):
    """Response for Temporal health check."""

    status: str = Field(..., description="Health status (healthy/unhealthy/disabled)")
    host: Optional[str] = Field(None, description="Temporal server host")
    namespace: Optional[str] = Field(None, description="Temporal namespace")
    connected: bool = Field(False, description="Whether connected to Temporal")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class StartSyncRequest(BaseModel):
    """Request to start eBay sync workflow."""

    marketplace_id: str = Field("EBAY_FR", description="eBay marketplace ID")


class StartSyncResponse(BaseModel):
    """Response from starting eBay sync workflow."""

    workflow_id: str = Field(..., description="Temporal workflow ID")
    run_id: str = Field(..., description="Temporal run ID")
    status: str = Field(..., description="Workflow status (started/error)")
    message: str = Field(..., description="Status message")


class SyncProgressResponse(BaseModel):
    """Response for sync progress query."""

    workflow_id: str = Field(..., description="Temporal workflow ID")
    status: str = Field(..., description="Current status")
    current: int = Field(0, description="Number of products synced so far")
    total_fetched: int = Field(0, description="Total products fetched from eBay")
    label: str = Field("", description="Progress label")
    error: Optional[str] = Field(None, description="Error message if failed")


class CancelSyncRequest(BaseModel):
    """Request to cancel a sync workflow."""

    workflow_id: str = Field(..., description="Temporal workflow ID to cancel")


class CancelSyncResponse(BaseModel):
    """Response from cancelling sync workflow."""

    workflow_id: str = Field(..., description="Temporal workflow ID")
    cancelled: bool = Field(..., description="Whether cancellation was successful")
    message: str = Field(..., description="Status message")


# ===== ENDPOINTS =====


@router.get("/health", response_model=TemporalHealthResponse)
async def temporal_health():
    """
    Check Temporal server health.

    Returns status of connection to Temporal server.
    Used by frontend to determine if Temporal features are available.
    """
    from temporal.client import check_temporal_health

    result = await check_temporal_health()
    return TemporalHealthResponse(**result)


@router.post("/sync/start", response_model=StartSyncResponse)
async def start_sync(
    request: StartSyncRequest,
    user_db: tuple = Depends(get_user_db),
):
    """
    Start eBay sync workflow via Temporal.

    Creates a new Temporal workflow to sync products from eBay.
    The workflow:
    - Fetches inventory pages from eBay API
    - Syncs products into the database (INSERT/UPDATE/DELETE)
    - Enriches with offer data (price, listing_id)

    Returns immediately with workflow_id for progress tracking.
    """
    from temporal.client import get_temporal_client
    from temporal.config import get_temporal_config
    from temporal.workflows.ebay.sync_workflow import EbaySyncParams, EbaySyncWorkflow

    db, current_user = user_db
    config = get_temporal_config()

    if not config.temporal_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal is disabled. Use legacy sync endpoint.",
        )

    try:
        # Start Temporal workflow directly (no job record needed)
        client = await get_temporal_client()

        workflow_id = f"ebay-sync-user-{current_user.id}"

        params = EbaySyncParams(
            user_id=current_user.id,
            marketplace_id=request.marketplace_id,
        )

        handle = await client.start_workflow(
            EbaySyncWorkflow.run,
            params,
            id=workflow_id,
            task_queue=config.temporal_task_queue,
        )

        logger.info(
            f"Started Temporal sync workflow: {workflow_id} for user {current_user.id}"
        )

        return StartSyncResponse(
            workflow_id=workflow_id,
            run_id=handle.result_run_id,
            status="started",
            message=f"Sync workflow started. Track progress with workflow_id: {workflow_id}",
        )

    except Exception as e:
        logger.error(f"Failed to start Temporal sync for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start sync workflow: {str(e)}",
        )


@router.get("/sync/progress/{workflow_id}", response_model=SyncProgressResponse)
async def get_sync_progress(
    workflow_id: str,
    user_db: tuple = Depends(get_user_db),
):
    """
    Get progress of a running sync workflow.

    Queries the Temporal workflow for current progress.
    """
    from temporal.client import get_temporal_client
    from temporal.config import get_temporal_config

    db, current_user = user_db
    config = get_temporal_config()

    if not config.temporal_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal is disabled",
        )

    # Verify workflow belongs to this user
    if f"user-{current_user.id}" not in workflow_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this workflow",
        )

    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)

        # Query workflow for progress
        progress = await handle.query("get_progress")

        return SyncProgressResponse(
            workflow_id=workflow_id,
            **progress,
        )

    except Exception as e:
        logger.error(f"Failed to get progress for workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow progress: {str(e)}",
        )


@router.post("/sync/cancel", response_model=CancelSyncResponse)
async def cancel_sync(
    request: CancelSyncRequest,
    user_db: tuple = Depends(get_user_db),
):
    """
    Cancel a running sync workflow.

    Sends a cancellation signal to the Temporal workflow.
    The workflow will stop gracefully after completing current activity.
    """
    from temporal.client import get_temporal_client
    from temporal.config import get_temporal_config

    db, current_user = user_db
    config = get_temporal_config()

    if not config.temporal_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal is disabled",
        )

    # Verify workflow belongs to this user
    if f"user-{current_user.id}" not in request.workflow_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this workflow",
        )

    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(request.workflow_id)

        # Send cancellation signal
        await handle.signal("cancel_sync")

        logger.info(f"Sent cancel signal to workflow {request.workflow_id}")

        return CancelSyncResponse(
            workflow_id=request.workflow_id,
            cancelled=True,
            message="Cancellation signal sent. Workflow will stop after current activity.",
        )

    except Exception as e:
        logger.error(f"Failed to cancel workflow {request.workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel workflow: {str(e)}",
        )


@router.get("/sync/list")
async def list_syncs(
    limit: int = Query(10, ge=1, le=50, description="Number of workflows to return"),
    user_db: tuple = Depends(get_user_db),
):
    """
    List recent sync workflows for the current user.

    Returns recent Temporal workflows for this user.
    """
    from temporal.client import get_temporal_client
    from temporal.config import get_temporal_config

    db, current_user = user_db
    config = get_temporal_config()

    if not config.temporal_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal is disabled",
        )

    try:
        client = await get_temporal_client()

        # Query for user's workflows
        query = f'WorkflowId STARTS_WITH "ebay-sync-user-{current_user.id}"'

        workflows = []
        async for workflow in client.list_workflows(query=query):
            workflows.append({
                "workflow_id": workflow.id,
                "run_id": workflow.run_id,
                "status": str(workflow.status),
                "start_time": workflow.start_time.isoformat() if workflow.start_time else None,
                "close_time": workflow.close_time.isoformat() if workflow.close_time else None,
            })
            if len(workflows) >= limit:
                break

        return {
            "workflows": workflows,
            "total": len(workflows),
        }

    except Exception as e:
        logger.error(f"Failed to list workflows for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workflows: {str(e)}",
        )
