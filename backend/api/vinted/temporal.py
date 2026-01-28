"""
Vinted Temporal Sync API Routes

Endpoints for Vinted product sync via Temporal workflows:
- Start sync workflow
- Get workflow progress
- Cancel running workflow
- Pause running workflow
- Resume paused workflow
- Health check for Temporal connection
- List recent workflows

These routes use Temporal for durable execution:
- Survives backend crashes/restarts
- Automatic retries with backoff
- Real-time progress tracking
- Cancellation support
- Pause/Resume support
- Automatic reconnection waiting on plugin disconnect

Author: Claude
Date: 2026-01-22
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.dependencies import get_user_db
from shared.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/temporal", tags=["Vinted Temporal"])


# ===== SCHEMAS =====


class TemporalHealthResponse(BaseModel):
    """Response for Temporal health check."""

    status: str = Field(..., description="Health status (healthy/unhealthy/disabled)")
    host: Optional[str] = Field(None, description="Temporal server host")
    namespace: Optional[str] = Field(None, description="Temporal namespace")
    connected: bool = Field(False, description="Whether connected to Temporal")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class StartSyncRequest(BaseModel):
    """Request to start Vinted sync workflow."""

    shop_id: Optional[int] = Field(None, description="Vinted shop ID (defaults to user's vinted_user_id)")


class StartSyncResponse(BaseModel):
    """Response from starting Vinted sync workflow."""

    workflow_id: str = Field(..., description="Temporal workflow ID")
    run_id: str = Field(..., description="Temporal run ID")
    status: str = Field(..., description="Workflow status (started/error)")
    message: str = Field(..., description="Status message")


class SyncProgressResponse(BaseModel):
    """Response for sync progress query."""

    workflow_id: str = Field(..., description="Temporal workflow ID")
    status: str = Field(..., description="Current status")
    phase: str = Field("", description="Current phase (sync/enrich)")
    current: int = Field(0, description="Number of products synced so far")
    total: int = Field(0, description="Total products (if known)")
    label: str = Field("", description="Progress label")
    error: Optional[str] = Field(None, description="Error message if failed")
    # Resilience fields
    paused_at: Optional[str] = Field(None, description="ISO timestamp when paused")
    pause_reason: Optional[str] = Field(None, description="Reason for pause")
    reconnection_attempts: int = Field(0, description="Number of reconnection attempts")
    can_pause: bool = Field(False, description="Whether workflow can be paused")
    can_resume: bool = Field(False, description="Whether workflow can be resumed")


class CancelSyncRequest(BaseModel):
    """Request to cancel a sync workflow."""

    workflow_id: str = Field(..., description="Temporal workflow ID to cancel")


class CancelSyncResponse(BaseModel):
    """Response from cancelling sync workflow."""

    workflow_id: str = Field(..., description="Temporal workflow ID")
    cancelled: bool = Field(..., description="Whether cancellation was successful")
    message: str = Field(..., description="Status message")


class PauseSyncRequest(BaseModel):
    """Request to pause a sync workflow."""

    workflow_id: str = Field(..., description="Temporal workflow ID to pause")


class PauseSyncResponse(BaseModel):
    """Response from pausing sync workflow."""

    workflow_id: str = Field(..., description="Temporal workflow ID")
    paused: bool = Field(..., description="Whether pause signal was sent successfully")
    message: str = Field(..., description="Status message")


class ResumeSyncRequest(BaseModel):
    """Request to resume a paused sync workflow."""

    workflow_id: str = Field(..., description="Temporal workflow ID to resume")


class ResumeSyncResponse(BaseModel):
    """Response from resuming sync workflow."""

    workflow_id: str = Field(..., description="Temporal workflow ID")
    resumed: bool = Field(..., description="Whether resume signal was sent successfully")
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
    Start Vinted sync workflow via Temporal.

    Creates a new Temporal workflow to sync products from Vinted.
    The workflow:
    - Fetches wardrobe pages from Vinted API (via plugin)
    - Syncs products into the database (INSERT/UPDATE)
    - Marks missing products as sold
    - Enriches with detailed data (description, IDs, etc.)

    Returns immediately with workflow_id for progress tracking.
    """
    from temporal.client import get_temporal_client
    from temporal.config import get_temporal_config
    from temporal.workflows.vinted.sync_workflow import VintedSyncParams, VintedSyncWorkflow

    db, current_user = user_db
    config = get_temporal_config()

    if not config.temporal_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal is disabled. Use legacy sync endpoint.",
        )

    # Get shop_id from request or user settings
    shop_id = request.shop_id
    if not shop_id:
        # Try to get from user's Vinted connection
        from models.user.vinted_connection import VintedConnection

        connection = db.query(VintedConnection).first()
        if not connection or not connection.vinted_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No Vinted shop ID provided and no Vinted connection found. "
                       "Please connect your Vinted account first.",
            )
        shop_id = connection.vinted_user_id

    try:
        # Check if a Vinted sync workflow is already running for this user
        client = await get_temporal_client()
        query = f'WorkflowType = "VintedSyncWorkflow" AND ExecutionStatus = "Running" AND WorkflowId STARTS_WITH "vinted-sync-user-{current_user.id}"'

        async for workflow in client.list_workflows(query=query):
            # Found a running workflow - reject new sync
            logger.warning(
                f"Rejected sync request: workflow {workflow.id} already running for user {current_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Un sync Vinted est déjà en cours (workflow: {workflow.id}). "
                       f"Attendez qu'il se termine ou annulez-le.",
            )

        # Start Temporal workflow directly
        workflow_id = f"vinted-sync-user-{current_user.id}"

        params = VintedSyncParams(
            user_id=current_user.id,
            shop_id=shop_id,
        )

        handle = await client.start_workflow(
            VintedSyncWorkflow.run,
            params,
            id=workflow_id,
            task_queue=config.temporal_vinted_task_queue,
        )

        logger.info(
            f"Started Temporal Vinted sync workflow: {workflow_id} for user {current_user.id}"
        )

        return StartSyncResponse(
            workflow_id=workflow_id,
            run_id=handle.result_run_id,
            status="started",
            message=f"Sync workflow started. Track progress with workflow_id: {workflow_id}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start Temporal Vinted sync for user {current_user.id}: {e}")
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


@router.post("/sync/pause", response_model=PauseSyncResponse)
async def pause_sync(
    request: PauseSyncRequest,
    user_db: tuple = Depends(get_user_db),
):
    """
    Pause a running sync workflow.

    Sends a pause signal to the Temporal workflow.
    The workflow will pause after completing current activity.
    Use /sync/resume to continue.
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
            detail="Not authorized to pause this workflow",
        )

    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(request.workflow_id)

        # Send pause signal
        await handle.signal("pause_sync")

        logger.info(f"Sent pause signal to workflow {request.workflow_id}")

        return PauseSyncResponse(
            workflow_id=request.workflow_id,
            paused=True,
            message="Pause signal sent. Workflow will pause after current activity.",
        )

    except Exception as e:
        logger.error(f"Failed to pause workflow {request.workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause workflow: {str(e)}",
        )


@router.post("/sync/resume", response_model=ResumeSyncResponse)
async def resume_sync(
    request: ResumeSyncRequest,
    user_db: tuple = Depends(get_user_db),
):
    """
    Resume a paused sync workflow.

    Sends a resume signal to the Temporal workflow.
    The workflow will continue from where it was paused.
    Also works for workflows waiting for plugin reconnection.
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
            detail="Not authorized to resume this workflow",
        )

    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(request.workflow_id)

        # Send resume signal
        await handle.signal("resume_sync")

        logger.info(f"Sent resume signal to workflow {request.workflow_id}")

        return ResumeSyncResponse(
            workflow_id=request.workflow_id,
            resumed=True,
            message="Resume signal sent. Workflow will continue from where it was paused.",
        )

    except Exception as e:
        logger.error(f"Failed to resume workflow {request.workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume workflow: {str(e)}",
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
        query = f'WorkflowId STARTS_WITH "vinted-sync-user-{current_user.id}"'

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
