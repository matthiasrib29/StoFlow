"""
Admin Dependencies

Helpers and dependencies for admin attribute routes.
Factorizes common logic for CREATE and UPDATE operations.
"""

from typing import Any, Optional

from fastapi import HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.public.user import User
from services.admin_attribute_service import AdminAttributeService
from services.admin_audit_service import AdminAuditService
from shared.logging import get_logger

logger = get_logger(__name__)


# Mapping of attr_type -> audit details extractor
AUDIT_DETAILS_MAP = {
    "brands": lambda data: {"name_fr": data.name_fr, "monitoring": data.monitoring},
    "categories": lambda data: {"parent_category": data.parent_category, "genders": data.genders},
    "colors": lambda data: {"hex_code": data.hex_code},
    "materials": lambda data: {"vinted_id": data.vinted_id},
}


def get_pk_value(attr_type: str, data: BaseModel) -> str:
    """Get primary key value from data based on attribute type."""
    if attr_type == "brands":
        return data.name
    return data.name_en


def create_attribute_with_audit(
    db: Session,
    current_user: User,
    request: Request,
    attr_type: str,
    data: BaseModel,
) -> Any:
    """
    Create an attribute with audit logging.

    Factorizes common logic for all CREATE endpoints.

    Args:
        db: Database session
        current_user: Admin user performing the action
        request: FastAPI request for IP logging
        attr_type: Attribute type (brands, categories, colors, materials)
        data: Validated Pydantic schema

    Returns:
        Created attribute model

    Raises:
        HTTPException: 400 if validation fails or attribute exists
    """
    pk_value = get_pk_value(attr_type, data)
    audit_details = AUDIT_DETAILS_MAP[attr_type](data)

    try:
        item = AdminAttributeService.create_attribute(db, attr_type, data.model_dump())

        AdminAuditService.log_action(
            db=db,
            admin=current_user,
            action=AdminAuditService.ACTION_CREATE,
            resource_type=attr_type[:-1],  # Remove 's' (brands -> brand)
            resource_id=pk_value,
            resource_name=pk_value,
            details=audit_details,
            request=request,
        )

        logger.info(f"Admin {current_user.email} created {attr_type[:-1]}: {pk_value}")
        return item

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


def update_attribute_with_audit(
    db: Session,
    current_user: User,
    request: Request,
    attr_type: str,
    pk: str,
    data: BaseModel,
) -> Any:
    """
    Update an attribute with audit logging.

    Factorizes common logic for all UPDATE endpoints.

    Args:
        db: Database session
        current_user: Admin user performing the action
        request: FastAPI request for IP logging
        attr_type: Attribute type (brands, categories, colors, materials)
        pk: Primary key of the attribute to update
        data: Validated Pydantic schema with update fields

    Returns:
        Updated attribute model

    Raises:
        HTTPException: 404 if not found
    """
    # Get before state for audit
    item_before = AdminAttributeService.get_attribute(db, attr_type, pk)
    if not item_before:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{attr_type[:-1].title()} '{pk}' not found"
        )

    # Filter out None values
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}

    item = AdminAttributeService.update_attribute(db, attr_type, pk, update_data)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{attr_type[:-1].title()} '{pk}' not found"
        )

    # Build changed fields for audit
    changed = {}
    for key, value in update_data.items():
        old_value = getattr(item_before, key, None)
        if old_value != value:
            changed[key] = value

    if changed:
        AdminAuditService.log_action(
            db=db,
            admin=current_user,
            action=AdminAuditService.ACTION_UPDATE,
            resource_type=attr_type[:-1],
            resource_id=pk,
            resource_name=pk,
            details={"changed": changed},
            request=request,
        )

    logger.info(f"Admin {current_user.email} updated {attr_type[:-1]}: {pk}")
    return item
