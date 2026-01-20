"""
Admin Audit Logs API

Endpoints for viewing admin action history.
All endpoints require admin authentication.
"""

from datetime import datetime
from typing import Optional, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.dependencies import require_admin, get_db
from models.public.user import User
from schemas.admin_schemas import (
    AdminAuditLogResponse,
    AdminAuditLogListResponse,
)
from services.admin_audit_service import AdminAuditService
from shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin/audit-logs", tags=["Admin Audit Logs"])


def _log_to_response(log) -> AdminAuditLogResponse:
    """Convert AdminAuditLog to response schema."""
    return AdminAuditLogResponse(
        id=log.id,
        admin_id=log.admin_id,
        admin_email=log.admin.email if log.admin else None,
        action=log.action,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        resource_name=log.resource_name,
        details=log.details,
        ip_address=log.ip_address,
        created_at=log.created_at,
    )


@router.get(
    "",
    response_model=AdminAuditLogListResponse,
    summary="List audit logs",
    description="Get paginated list of admin audit logs with optional filtering.",
)
def list_audit_logs(
    skip: int = Query(default=0, ge=0, description="Records to skip"),
    limit: int = Query(default=50, ge=1, le=100, description="Max records to return"),
    admin_id: Optional[int] = Query(default=None, description="Filter by admin user ID"),
    action: Optional[Literal["CREATE", "UPDATE", "DELETE", "TOGGLE_ACTIVE", "UNLOCK"]] = Query(
        default=None, description="Filter by action type"
    ),
    resource_type: Optional[Literal["user", "brand", "category", "color", "material"]] = Query(
        default=None, description="Filter by resource type"
    ),
    date_from: Optional[datetime] = Query(default=None, description="Filter by start date"),
    date_to: Optional[datetime] = Query(default=None, description="Filter by end date"),
    search: Optional[str] = Query(default=None, description="Search in resource name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminAuditLogListResponse:
    """
    List audit logs with filtering and pagination.

    Requires admin role.
    """
    logger.info(f"Admin {current_user.email} requested audit logs")

    logs, total = AdminAuditService.list_logs(
        db=db,
        skip=skip,
        limit=limit,
        admin_id=admin_id,
        action=action,
        resource_type=resource_type,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )

    return AdminAuditLogListResponse(
        logs=[_log_to_response(log) for log in logs],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{log_id}",
    response_model=AdminAuditLogResponse,
    summary="Get audit log",
    description="Get a single audit log entry by ID.",
)
def get_audit_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminAuditLogResponse:
    """
    Get a single audit log entry.

    Requires admin role.
    """
    from fastapi import HTTPException

    log = AdminAuditService.get_log(db, log_id)

    if not log:
        raise HTTPException(status_code=404, detail=f"Audit log {log_id} not found")

    logger.debug(f"Admin {current_user.email} retrieved audit log {log_id}")

    return _log_to_response(log)


@router.get(
    "/resource/{resource_type}/{resource_id}",
    response_model=AdminAuditLogListResponse,
    summary="Get resource history",
    description="Get action history for a specific resource.",
)
def get_resource_history(
    resource_type: str,
    resource_id: str,
    limit: int = Query(default=50, ge=1, le=100, description="Max records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminAuditLogListResponse:
    """
    Get action history for a specific resource.

    Requires admin role.
    """
    logger.info(
        f"Admin {current_user.email} requested history for {resource_type}:{resource_id}"
    )

    logs = AdminAuditService.get_resource_history(
        db=db,
        resource_type=resource_type,
        resource_id=resource_id,
        limit=limit,
    )

    return AdminAuditLogListResponse(
        logs=[_log_to_response(log) for log in logs],
        total=len(logs),
        skip=0,
        limit=limit,
    )
