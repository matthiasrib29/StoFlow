"""
Admin Audit Service

Service for logging and querying admin actions.
Provides audit trail for security and accountability.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Any

from fastapi import Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from models.public.admin_audit_log import AdminAuditLog
from models.public.user import User
from shared.logging import get_logger

logger = get_logger(__name__)


class AdminAuditService:
    """Service for admin audit logging and retrieval."""

    # Action types
    ACTION_CREATE = "CREATE"
    ACTION_UPDATE = "UPDATE"
    ACTION_DELETE = "DELETE"
    ACTION_TOGGLE_ACTIVE = "TOGGLE_ACTIVE"
    ACTION_UNLOCK = "UNLOCK"

    # Resource types
    RESOURCE_USER = "user"
    RESOURCE_BRAND = "brand"
    RESOURCE_CATEGORY = "category"
    RESOURCE_COLOR = "color"
    RESOURCE_MATERIAL = "material"

    @staticmethod
    def log_action(
        db: Session,
        admin: User,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        details: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> AdminAuditLog:
        """
        Log an admin action.

        Args:
            db: SQLAlchemy session
            admin: Admin user performing the action
            action: Action type (CREATE, UPDATE, DELETE, etc.)
            resource_type: Type of resource (user, brand, etc.)
            resource_id: Primary key of the resource
            resource_name: Human-readable name
            details: Additional details (changed fields, before/after values)
            request: FastAPI request for extracting IP/user agent

        Returns:
            Created AdminAuditLog entry
        """
        # Extract request context
        ip_address = None
        user_agent = None

        if request:
            # Get client IP (handle proxies)
            ip_address = request.headers.get("X-Forwarded-For")
            if ip_address:
                ip_address = ip_address.split(",")[0].strip()
            else:
                ip_address = request.client.host if request.client else None

            user_agent = request.headers.get("User-Agent", "")[:500]

        log_entry = AdminAuditLog(
            admin_id=admin.id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            resource_name=resource_name,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        logger.info(
            f"Audit: admin={admin.email} action={action} "
            f"resource={resource_type}:{resource_id} name={resource_name}"
        )

        return log_entry

    @staticmethod
    def list_logs(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        admin_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search: Optional[str] = None,
    ) -> tuple[List[AdminAuditLog], int]:
        """
        List audit logs with filtering and pagination.

        Args:
            db: SQLAlchemy session
            skip: Number of records to skip
            limit: Maximum records to return
            admin_id: Filter by admin user ID
            action: Filter by action type
            resource_type: Filter by resource type
            date_from: Filter by start date
            date_to: Filter by end date
            search: Search in resource_name

        Returns:
            Tuple of (list of logs, total count)
        """
        query = db.query(AdminAuditLog)

        # Apply filters
        filters = []

        if admin_id:
            filters.append(AdminAuditLog.admin_id == admin_id)

        if action:
            filters.append(AdminAuditLog.action == action)

        if resource_type:
            filters.append(AdminAuditLog.resource_type == resource_type)

        if date_from:
            filters.append(AdminAuditLog.created_at >= date_from)

        if date_to:
            # Include entire end day
            end_of_day = date_to + timedelta(days=1)
            filters.append(AdminAuditLog.created_at < end_of_day)

        if search:
            filters.append(AdminAuditLog.resource_name.ilike(f"%{search}%"))

        if filters:
            query = query.filter(and_(*filters))

        # Get total count
        total = query.count()

        # Apply ordering and pagination
        logs = (
            query
            .order_by(desc(AdminAuditLog.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

        logger.debug(f"Admin audit list: found {total} logs, returning {len(logs)}")

        return logs, total

    @staticmethod
    def get_log(db: Session, log_id: int) -> Optional[AdminAuditLog]:
        """
        Get a single audit log by ID.

        Args:
            db: SQLAlchemy session
            log_id: Audit log ID

        Returns:
            AdminAuditLog if found, None otherwise
        """
        return db.query(AdminAuditLog).filter(AdminAuditLog.id == log_id).first()

    @staticmethod
    def get_admin_actions(db: Session, admin_id: int, limit: int = 100) -> List[AdminAuditLog]:
        """
        Get recent actions by a specific admin.

        Args:
            db: SQLAlchemy session
            admin_id: Admin user ID
            limit: Maximum records to return

        Returns:
            List of AdminAuditLog entries
        """
        return (
            db.query(AdminAuditLog)
            .filter(AdminAuditLog.admin_id == admin_id)
            .order_by(desc(AdminAuditLog.created_at))
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_resource_history(
        db: Session,
        resource_type: str,
        resource_id: str,
        limit: int = 50,
    ) -> List[AdminAuditLog]:
        """
        Get action history for a specific resource.

        Args:
            db: SQLAlchemy session
            resource_type: Type of resource
            resource_id: Resource ID
            limit: Maximum records to return

        Returns:
            List of AdminAuditLog entries
        """
        return (
            db.query(AdminAuditLog)
            .filter(
                and_(
                    AdminAuditLog.resource_type == resource_type,
                    AdminAuditLog.resource_id == resource_id,
                )
            )
            .order_by(desc(AdminAuditLog.created_at))
            .limit(limit)
            .all()
        )

    @staticmethod
    def build_user_details(
        user: User,
        changed_fields: Optional[dict] = None,
        before: Optional[dict] = None,
    ) -> dict:
        """
        Build details dict for user-related actions.

        Args:
            user: User object
            changed_fields: Dict of field names to new values
            before: Dict of field names to previous values

        Returns:
            Details dict for audit log
        """
        details = {
            "user_id": user.id,
            "email": user.email,
        }

        if changed_fields:
            details["changed"] = changed_fields

        if before:
            details["before"] = before

        return details
