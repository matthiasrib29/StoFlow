"""
Admin Vinted Pro Sellers Routes

API routes for managing Vinted professional sellers (business accounts).
All routes require ADMIN role.

Author: Claude
Date: 2026-01-27
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.dependencies import require_admin
from models.public.user import User
from schemas.vinted_pro_seller_schemas import (
    VintedProSellerResponse,
    VintedProSellerListResponse,
    VintedProSellerStatsResponse,
    StartProSellerScanRequest,
    StartProSellerScanResponse,
    ProSellerScanProgressResponse,
    VintedProSellerUpdateRequest,
    VintedProSellerBulkUpdateRequest,
)
from services.vinted_pro_seller_service import VintedProSellerService
from shared.database import get_db_context
from shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin/vinted-pro-sellers", tags=["Admin Vinted Pro Sellers"])


# ===== CRUD Routes =====

@router.get("", response_model=VintedProSellerListResponse)
def list_sellers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    country_code: Optional[str] = Query(None),
    marketplace: Optional[str] = Query(None),
    min_items: Optional[int] = Query(None, ge=0),
    search: Optional[str] = Query(None, description="Search in login or business_name"),
    has_email: Optional[bool] = Query(None),
    has_instagram: Optional[bool] = Query(None),
    current_user: User = Depends(require_admin),
) -> VintedProSellerListResponse:
    """List all pro sellers with pagination and filtering."""
    with get_db_context() as db:
        sellers, total = VintedProSellerService.list_sellers(
            db=db,
            skip=skip,
            limit=limit,
            status=status_filter,
            country_code=country_code,
            marketplace=marketplace,
            min_items=min_items,
            search=search,
            has_email=has_email,
            has_instagram=has_instagram,
        )

        return VintedProSellerListResponse(
            sellers=[VintedProSellerResponse.model_validate(s) for s in sellers],
            total=total,
            skip=skip,
            limit=limit,
        )


@router.get("/stats", response_model=VintedProSellerStatsResponse)
def get_stats(
    current_user: User = Depends(require_admin),
) -> VintedProSellerStatsResponse:
    """Get pro seller statistics."""
    with get_db_context() as db:
        stats = VintedProSellerService.get_stats(db)
        return VintedProSellerStatsResponse(**stats)


@router.get("/{seller_id}", response_model=VintedProSellerResponse)
def get_seller(
    seller_id: int,
    current_user: User = Depends(require_admin),
) -> VintedProSellerResponse:
    """Get a specific pro seller by ID."""
    with get_db_context() as db:
        seller = VintedProSellerService.get_seller(db, seller_id)
        if not seller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pro seller with id {seller_id} not found"
            )
        return VintedProSellerResponse.model_validate(seller)


@router.patch("/{seller_id}", response_model=VintedProSellerResponse)
def update_seller(
    seller_id: int,
    request: VintedProSellerUpdateRequest,
    current_user: User = Depends(require_admin),
) -> VintedProSellerResponse:
    """Update a pro seller (status, notes)."""
    with get_db_context() as db:
        seller = VintedProSellerService.update_seller(
            db=db,
            seller_id=seller_id,
            status=request.status,
            notes=request.notes,
        )

        if not seller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pro seller with id {seller_id} not found"
            )

        return VintedProSellerResponse.model_validate(seller)


@router.post("/bulk-update")
def bulk_update_sellers(
    request: VintedProSellerBulkUpdateRequest,
    current_user: User = Depends(require_admin),
) -> dict:
    """Bulk update status for multiple pro sellers."""
    if not request.status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="status is required for bulk update"
        )

    with get_db_context() as db:
        updated = VintedProSellerService.bulk_update_status(
            db=db,
            seller_ids=request.seller_ids,
            status=request.status,
        )

        return {
            "success": True,
            "updated_count": updated,
            "message": f"Updated {updated} sellers to status '{request.status}'"
        }


@router.delete("/{seller_id}")
def delete_seller(
    seller_id: int,
    current_user: User = Depends(require_admin),
) -> dict:
    """Delete a pro seller."""
    with get_db_context() as db:
        deleted = VintedProSellerService.delete_seller(db, seller_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pro seller with id {seller_id} not found"
            )

        return {"success": True, "message": f"Pro seller {seller_id} deleted"}


# ===== Scan Logs =====

@router.get("/scan/logs")
def get_scan_logs(
    marketplace: str = Query("vinted_fr"),
    current_user: User = Depends(require_admin),
) -> dict:
    """Get keyword scan history for a marketplace."""
    from models.vinted.vinted_keyword_scan_log import VintedKeywordScanLog

    with get_db_context() as db:
        logs = db.query(VintedKeywordScanLog).filter(
            VintedKeywordScanLog.marketplace == marketplace
        ).all()

        return {
            "logs": {
                log.keyword: {
                    "last_page": log.last_page_scanned,
                    "exhausted": log.exhausted,
                    "total_found": log.total_pro_sellers_found,
                    "last_scanned_at": log.last_scanned_at.isoformat() if log.last_scanned_at else None,
                }
                for log in logs
            }
        }


# ===== Scan Workflow Routes =====

@router.post("/scan/start", response_model=StartProSellerScanResponse)
async def start_scan(
    request: StartProSellerScanRequest,
    current_user: User = Depends(require_admin),
) -> StartProSellerScanResponse:
    """
    Start a Temporal workflow to scan Vinted for pro sellers.

    The workflow iterates through search keywords (business terms, legal forms,
    niches), fetches user search results via the plugin, filters for business=true,
    and stores them in the database with extracted contacts.
    """
    from temporal.client import get_temporal_client
    from temporal.config import get_temporal_config
    from temporal.workflows.vinted.pro_seller_scan_workflow import (
        VintedProSellerScanWorkflow,
        VintedProSellerScanParams,
    )

    temporal_config = get_temporal_config()

    if not temporal_config.temporal_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal is not enabled"
        )

    params = VintedProSellerScanParams(
        user_id=current_user.id,
        job_id=0,  # No MarketplaceJob tracking for now
        keywords=request.keywords,
        marketplace=request.marketplace,
        per_page=request.per_page,
    )

    workflow_id = f"pro-seller-scan-{current_user.id}-{int(workflow_now_ms())}"

    client = await get_temporal_client()
    handle = await client.start_workflow(
        VintedProSellerScanWorkflow.run,
        params,
        id=workflow_id,
        task_queue=temporal_config.temporal_vinted_task_queue,
    )

    logger.info(
        f"Admin {current_user.email} started pro seller scan workflow {workflow_id}"
    )

    return StartProSellerScanResponse(
        workflow_id=workflow_id,
        run_id=handle.result_run_id,
        status="started",
    )


@router.get("/scan/progress/{workflow_id}", response_model=ProSellerScanProgressResponse)
async def get_scan_progress(
    workflow_id: str,
    current_user: User = Depends(require_admin),
) -> ProSellerScanProgressResponse:
    """Get progress of a running pro seller scan workflow."""
    from temporal.client import get_temporal_client
    from temporal.workflows.vinted.pro_seller_scan_workflow import VintedProSellerScanWorkflow

    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)

        progress = await handle.query(VintedProSellerScanWorkflow.get_progress)

        return ProSellerScanProgressResponse(**progress)

    except Exception as e:
        logger.error(f"Error querying scan progress for {workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found or not queryable"
        )


@router.post("/scan/cancel")
async def cancel_scan(
    workflow_id: str = Query(..., description="Workflow ID to cancel"),
    current_user: User = Depends(require_admin),
) -> dict:
    """Cancel a running pro seller scan workflow."""
    from temporal.client import get_temporal_client
    from temporal.workflows.vinted.pro_seller_scan_workflow import VintedProSellerScanWorkflow

    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        await handle.signal(VintedProSellerScanWorkflow.cancel_scan)

        logger.info(f"Admin {current_user.email} cancelled scan {workflow_id}")
        return {"success": True, "message": f"Cancel signal sent to {workflow_id}"}

    except Exception as e:
        logger.error(f"Error cancelling scan {workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )


@router.post("/scan/pause")
async def pause_scan(
    workflow_id: str = Query(..., description="Workflow ID to pause"),
    current_user: User = Depends(require_admin),
) -> dict:
    """Pause a running pro seller scan workflow."""
    from temporal.client import get_temporal_client
    from temporal.workflows.vinted.pro_seller_scan_workflow import VintedProSellerScanWorkflow

    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        await handle.signal(VintedProSellerScanWorkflow.pause_scan)

        logger.info(f"Admin {current_user.email} paused scan {workflow_id}")
        return {"success": True, "message": f"Pause signal sent to {workflow_id}"}

    except Exception as e:
        logger.error(f"Error pausing scan {workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )


@router.post("/scan/resume")
async def resume_scan(
    workflow_id: str = Query(..., description="Workflow ID to resume"),
    current_user: User = Depends(require_admin),
) -> dict:
    """Resume a paused pro seller scan workflow."""
    from temporal.client import get_temporal_client
    from temporal.workflows.vinted.pro_seller_scan_workflow import VintedProSellerScanWorkflow

    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        await handle.signal(VintedProSellerScanWorkflow.resume_scan)

        logger.info(f"Admin {current_user.email} resumed scan {workflow_id}")
        return {"success": True, "message": f"Resume signal sent to {workflow_id}"}

    except Exception as e:
        logger.error(f"Error resuming scan {workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )


def workflow_now_ms() -> int:
    """Get current time in milliseconds (for workflow ID generation)."""
    import time
    return int(time.time() * 1000)
