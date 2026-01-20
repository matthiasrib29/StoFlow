"""
Admin Attributes Routes

API routes for managing reference data (brands, categories, colors, materials).
All routes require ADMIN role.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status
from sqlalchemy.orm import Session

from api.dependencies import require_admin, create_attribute_with_audit, update_attribute_with_audit
from models.public.user import User
from schemas.admin_schemas import (
    AdminAttributeListResponse,
    AdminBrandCreate,
    AdminBrandResponse,
    AdminBrandUpdate,
    AdminCategoryCreate,
    AdminCategoryResponse,
    AdminCategoryUpdate,
    AdminColorCreate,
    AdminColorResponse,
    AdminColorUpdate,
    AdminMaterialCreate,
    AdminMaterialResponse,
    AdminMaterialUpdate,
)
from services.admin_attribute_service import AdminAttributeService
from services.admin_audit_service import AdminAuditService
from shared.database import get_db
from shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin/attributes", tags=["Admin Attributes"])

# Valid attribute types
VALID_TYPES = ["brands", "categories", "colors", "materials"]


def validate_attr_type(attr_type: str) -> str:
    """Validate attribute type parameter."""
    if attr_type not in VALID_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid attribute type: {attr_type}. Must be one of: {', '.join(VALID_TYPES)}"
        )
    return attr_type


# ============================================================================
# Generic Endpoints
# ============================================================================


@router.get("/{attr_type}", response_model=AdminAttributeListResponse)
def list_attributes(
    attr_type: str = Path(..., description="Attribute type: brands, categories, colors, materials"),
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max records to return"),
    search: Optional[str] = Query(None, description="Search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminAttributeListResponse:
    """
    List attributes with pagination and search.

    Requires ADMIN role.

    Args:
        attr_type: Type of attribute (brands, categories, colors, materials)
        skip: Number of records to skip
        limit: Maximum records to return
        search: Optional search term

    Returns:
        Paginated list of attributes
    """
    validate_attr_type(attr_type)

    items, total = AdminAttributeService.list_attributes(
        db=db,
        attr_type=attr_type,
        skip=skip,
        limit=limit,
        search=search,
    )

    # Convert to dict format
    items_dict = [AdminAttributeService.attribute_to_dict(item, attr_type) for item in items]

    return AdminAttributeListResponse(
        items=items_dict,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{attr_type}/{pk}")
def get_attribute(
    attr_type: str = Path(..., description="Attribute type"),
    pk: str = Path(..., description="Primary key"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """
    Get a single attribute by primary key.

    Requires ADMIN role.

    Args:
        attr_type: Type of attribute
        pk: Primary key value

    Returns:
        Attribute details

    Raises:
        HTTPException: 404 if not found
    """
    validate_attr_type(attr_type)

    item = AdminAttributeService.get_attribute(db, attr_type, pk)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{attr_type[:-1].title()} '{pk}' not found"
        )

    return AdminAttributeService.attribute_to_dict(item, attr_type)


@router.delete("/{attr_type}/{pk}")
def delete_attribute(
    request: Request,
    attr_type: str = Path(..., description="Attribute type"),
    pk: str = Path(..., description="Primary key"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """
    Delete an attribute.

    Requires ADMIN role.

    Args:
        attr_type: Type of attribute
        pk: Primary key value

    Returns:
        Success message

    Raises:
        HTTPException: 404 if not found, 400 if in use
    """
    validate_attr_type(attr_type)

    # Get resource name for audit
    item = AdminAttributeService.get_attribute(db, attr_type, pk)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{attr_type[:-1].title()} '{pk}' not found"
        )

    name_field = AdminAttributeService.get_name_field(attr_type)
    resource_name = getattr(item, name_field, pk)

    try:
        success = AdminAttributeService.delete_attribute(db, attr_type, pk)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{attr_type[:-1].title()} '{pk}' not found"
            )

        # Log audit
        AdminAuditService.log_action(
            db=db,
            admin=current_user,
            action=AdminAuditService.ACTION_DELETE,
            resource_type=attr_type[:-1],  # Remove 's' (brands -> brand)
            resource_id=pk,
            resource_name=resource_name,
            details=None,
            request=request,
        )

        logger.info(f"Admin {current_user.email} deleted {attr_type[:-1]}: {pk}")
        return {"success": True, "message": f"{attr_type[:-1].title()} deleted successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Brand-specific Endpoints
# ============================================================================


@router.post("/brands", response_model=AdminBrandResponse, status_code=status.HTTP_201_CREATED)
def create_brand(
    data: AdminBrandCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminBrandResponse:
    """Create a new brand. Requires ADMIN role."""
    item = create_attribute_with_audit(db, current_user, request, "brands", data)
    return AdminBrandResponse(**AdminAttributeService.attribute_to_dict(item, "brands"))


@router.patch("/brands/{pk}", response_model=AdminBrandResponse)
def update_brand(
    data: AdminBrandUpdate,
    request: Request,
    pk: str = Path(..., description="Brand name (primary key)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminBrandResponse:
    """Update a brand. Requires ADMIN role."""
    item = update_attribute_with_audit(db, current_user, request, "brands", pk, data)
    return AdminBrandResponse(**AdminAttributeService.attribute_to_dict(item, "brands"))


# ============================================================================
# Category-specific Endpoints
# ============================================================================


@router.post("/categories", response_model=AdminCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    data: AdminCategoryCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminCategoryResponse:
    """Create a new category. Requires ADMIN role."""
    item = create_attribute_with_audit(db, current_user, request, "categories", data)
    return AdminCategoryResponse(**AdminAttributeService.attribute_to_dict(item, "categories"))


@router.patch("/categories/{pk}", response_model=AdminCategoryResponse)
def update_category(
    data: AdminCategoryUpdate,
    request: Request,
    pk: str = Path(..., description="Category name_en (primary key)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminCategoryResponse:
    """Update a category. Requires ADMIN role."""
    item = update_attribute_with_audit(db, current_user, request, "categories", pk, data)
    return AdminCategoryResponse(**AdminAttributeService.attribute_to_dict(item, "categories"))


# ============================================================================
# Color-specific Endpoints
# ============================================================================


@router.post("/colors", response_model=AdminColorResponse, status_code=status.HTTP_201_CREATED)
def create_color(
    data: AdminColorCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminColorResponse:
    """Create a new color. Requires ADMIN role."""
    item = create_attribute_with_audit(db, current_user, request, "colors", data)
    return AdminColorResponse(**AdminAttributeService.attribute_to_dict(item, "colors"))


@router.patch("/colors/{pk}", response_model=AdminColorResponse)
def update_color(
    data: AdminColorUpdate,
    request: Request,
    pk: str = Path(..., description="Color name_en (primary key)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminColorResponse:
    """Update a color. Requires ADMIN role."""
    item = update_attribute_with_audit(db, current_user, request, "colors", pk, data)
    return AdminColorResponse(**AdminAttributeService.attribute_to_dict(item, "colors"))


# ============================================================================
# Material-specific Endpoints
# ============================================================================


@router.post("/materials", response_model=AdminMaterialResponse, status_code=status.HTTP_201_CREATED)
def create_material(
    data: AdminMaterialCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminMaterialResponse:
    """Create a new material. Requires ADMIN role."""
    item = create_attribute_with_audit(db, current_user, request, "materials", data)
    return AdminMaterialResponse(**AdminAttributeService.attribute_to_dict(item, "materials"))


@router.patch("/materials/{pk}", response_model=AdminMaterialResponse)
def update_material(
    data: AdminMaterialUpdate,
    request: Request,
    pk: str = Path(..., description="Material name_en (primary key)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AdminMaterialResponse:
    """Update a material. Requires ADMIN role."""
    item = update_attribute_with_audit(db, current_user, request, "materials", pk, data)
    return AdminMaterialResponse(**AdminAttributeService.attribute_to_dict(item, "materials"))
