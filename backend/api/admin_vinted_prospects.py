"""
Admin Vinted Prospects Routes

API routes for managing Vinted prospects for prospection.
All routes require ADMIN role.

Author: Claude
Date: 2026-01-19
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.dependencies import require_admin
from models.public.user import User
from schemas.vinted_prospect_schemas import (
    VintedProspectFetchJobResponse,
    VintedProspectFetchRequest,
    VintedProspectListResponse,
    VintedProspectResponse,
    VintedProspectStatsResponse,
    VintedProspectUpdateRequest,
    VintedProspectBulkUpdateRequest,
)
from services.vinted_prospect_service import VintedProspectService
from shared.database import get_db, get_db_context
from shared.logging import get_logger
from temporal.client import get_temporal_client
from temporal.workflows.vinted.fetch_users_workflow import (
    VintedFetchUsersWorkflow,
    VintedFetchUsersParams,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/admin/vinted-prospects", tags=["Admin Vinted Prospects"])


@router.get("", response_model=VintedProspectListResponse)
def list_prospects(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    status: Optional[str] = Query(None, description="Filter by status (new, contacted, converted, ignored)"),
    country_code: Optional[str] = Query(None, description="Filter by country code (FR, DE, etc.)"),
    min_items: Optional[int] = Query(None, ge=0, description="Filter by minimum item count"),
    is_business: Optional[bool] = Query(None, description="Filter by business account status"),
    search: Optional[str] = Query(None, description="Search in login"),
    current_user: User = Depends(require_admin),
) -> VintedProspectListResponse:
    """
    List all Vinted prospects with pagination and filtering.

    Requires ADMIN role.
    """
    with get_db_context() as db:
        prospects, total = VintedProspectService.list_prospects(
            db=db,
            skip=skip,
            limit=limit,
            status=status,
            country_code=country_code,
            min_items=min_items,
            is_business=is_business,
            search=search,
        )

        return VintedProspectListResponse(
            prospects=[VintedProspectResponse.model_validate(p) for p in prospects],
            total=total,
            skip=skip,
            limit=limit,
        )


@router.get("/stats", response_model=VintedProspectStatsResponse)
def get_stats(
    current_user: User = Depends(require_admin),
) -> VintedProspectStatsResponse:
    """
    Get prospect statistics.

    Requires ADMIN role.
    """
    with get_db_context() as db:
        stats = VintedProspectService.get_stats(db)
        return VintedProspectStatsResponse(**stats)


@router.get("/{prospect_id}", response_model=VintedProspectResponse)
def get_prospect(
    prospect_id: int,
    current_user: User = Depends(require_admin),
) -> VintedProspectResponse:
    """
    Get a specific prospect by ID.

    Requires ADMIN role.
    """
    with get_db_context() as db:
        prospect = VintedProspectService.get_prospect(db, prospect_id)
        if not prospect:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prospect with id {prospect_id} not found"
            )
        return VintedProspectResponse.model_validate(prospect)


@router.post("/fetch", response_model=VintedProspectFetchJobResponse)
async def trigger_fetch(
    request: VintedProspectFetchRequest,
    current_user: User = Depends(require_admin),
) -> VintedProspectFetchJobResponse:
    """
    Trigger a Temporal workflow to fetch Vinted users for prospection.

    Starts a VintedFetchUsersWorkflow that iterates through keyword searches
    to find users and save matching ones as prospects.

    Requires ADMIN role.
    """
    client = await get_temporal_client()

    workflow_id = f"vinted-fetch-users-admin-{current_user.id}"
    params = VintedFetchUsersParams(
        user_id=current_user.id,
        country_code=request.country_code,
        min_items=request.min_items,
        max_pages_per_search=request.max_pages_per_search,
    )

    await client.start_workflow(
        VintedFetchUsersWorkflow.run,
        params,
        id=workflow_id,
        task_queue="stoflow-vinted-queue",
    )

    logger.info(f"Admin {current_user.email} triggered fetch_users workflow {workflow_id}")

    return VintedProspectFetchJobResponse(
        workflow_id=workflow_id,
        status="started",
        message=f"Fetch workflow started. Will search for {request.country_code} users with {request.min_items}+ items."
    )


@router.patch("/{prospect_id}", response_model=VintedProspectResponse)
def update_prospect(
    prospect_id: int,
    request: VintedProspectUpdateRequest,
    current_user: User = Depends(require_admin),
) -> VintedProspectResponse:
    """
    Update a prospect (status, notes).

    Requires ADMIN role.
    """
    with get_db_context() as db:
        prospect = VintedProspectService.update_prospect(
            db=db,
            prospect_id=prospect_id,
            status=request.status,
            notes=request.notes,
        )

        if not prospect:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prospect with id {prospect_id} not found"
            )

        return VintedProspectResponse.model_validate(prospect)


@router.post("/bulk-update")
def bulk_update_prospects(
    request: VintedProspectBulkUpdateRequest,
    current_user: User = Depends(require_admin),
) -> dict:
    """
    Bulk update status for multiple prospects.

    Requires ADMIN role.
    """
    if not request.status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="status is required for bulk update"
        )

    with get_db_context() as db:
        updated = VintedProspectService.bulk_update_status(
            db=db,
            prospect_ids=request.prospect_ids,
            status=request.status,
        )

        return {
            "success": True,
            "updated_count": updated,
            "message": f"Updated {updated} prospects to status '{request.status}'"
        }


@router.delete("/{prospect_id}")
def delete_prospect(
    prospect_id: int,
    current_user: User = Depends(require_admin),
) -> dict:
    """
    Delete a prospect.

    Requires ADMIN role.
    """
    with get_db_context() as db:
        deleted = VintedProspectService.delete_prospect(db, prospect_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prospect with id {prospect_id} not found"
            )

        return {
            "success": True,
            "message": f"Prospect {prospect_id} deleted"
        }
