"""
eBay Products API Routes

Endpoints for eBay product management:
- List imported eBay products
- Get single eBay product
- Import products from eBay (with inline enrichment)
- Enrich products with offers data
- Delete local eBay product
- Get eBay stats summary
- Link/unlink eBay products to Stoflow products

Author: Claude
Date: 2025-12-19
Refactored: 2026-01-20
"""

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from api.dependencies import get_user_db
from models.public.user import User
from models.user.ebay_product import EbayProduct
from schemas.ebay_product_schemas import (
    EbayLinkResponse,
    EbayProductListResponse,
    EbayProductResponse,
    EbayUnlinkResponse,
    EnrichRequest,
    EnrichResponse,
    ImportRequest,
    ImportResponse,
    LinkProductRequest,
    RefreshAspectsResponse,
)
from services.ebay.ebay_background_import_service import run_import_in_background
from services.ebay.ebay_importer import EbayImporter
from services.ebay.ebay_link_service import EbayLinkService
from shared.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/ebay/products", tags=["eBay Products"])


# ===== LIST & GET ENDPOINTS =====


@router.get("", response_model=EbayProductListResponse)
async def list_ebay_products(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    marketplace_id: Optional[str] = Query(None, description="Filter by marketplace"),
    search: Optional[str] = Query(None, description="Search in title"),
    user_db: tuple = Depends(get_user_db),
):
    """List imported eBay products with pagination and filters."""
    db, current_user = user_db

    query = db.query(EbayProduct)

    # Apply filters
    if status:
        if status == "out_of_stock":
            # Out of stock = sold_quantity >= 1 (product has been sold)
            query = query.filter(EbayProduct.sold_quantity >= 1)
        else:
            query = query.filter(EbayProduct.status == status)

    if marketplace_id:
        query = query.filter(EbayProduct.marketplace_id == marketplace_id)

    if search:
        query = query.filter(EbayProduct.title.ilike(f"%{search}%"))

    # Get total and pagination
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    offset = (page - 1) * page_size
    items = query.order_by(EbayProduct.created_at.desc()).offset(offset).limit(page_size).all()

    # Calculate global stats
    stats_query = db.query(EbayProduct)
    if marketplace_id:
        stats_query = stats_query.filter(EbayProduct.marketplace_id == marketplace_id)

    # Out of stock = sold_quantity >= 1 (product has been sold)
    out_of_stock_count = stats_query.filter(EbayProduct.sold_quantity >= 1).count()

    # Active = status active AND not sold (sold_quantity is NULL or 0)
    active_count = stats_query.filter(
        EbayProduct.status == "active",
        or_(EbayProduct.sold_quantity.is_(None), EbayProduct.sold_quantity < 1)
    ).count()

    # Inactive/draft = not sold (exclude products with sold_quantity >= 1)
    inactive_count = stats_query.filter(
        EbayProduct.status.in_(["inactive", "draft", "ended"]),
        or_(EbayProduct.sold_quantity.is_(None), EbayProduct.sold_quantity < 1)
    ).count()

    return EbayProductListResponse(
        items=[EbayProductResponse.from_orm_with_parsed_images(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        active_count=active_count,
        inactive_count=inactive_count,
        out_of_stock_count=out_of_stock_count,
    )


@router.get("/{product_id}", response_model=EbayProductResponse)
async def get_ebay_product(
    product_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """Get a single eBay product by ID."""
    db, current_user = user_db

    product = db.query(EbayProduct).filter(EbayProduct.id == product_id).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"eBay product {product_id} not found",
        )

    return EbayProductResponse.from_orm_with_parsed_images(product)


# ===== IMPORT & ENRICH ENDPOINTS =====


@router.post("/import")
async def import_ebay_products(
    request: ImportRequest = Body(default=ImportRequest()),
    user_db: tuple = Depends(get_user_db),
):
    """
    Import products from eBay Inventory API via Temporal workflow.

    Starts EbayImportWorkflow and returns immediately.
    Track progress via GET /workflows/{workflow_id}/progress.
    """
    from temporal.client import get_temporal_client
    from temporal.config import get_temporal_config
    from temporal.workflows.ebay.import_workflow import EbayImportParams, EbayImportWorkflow

    config = get_temporal_config()
    if not config.temporal_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal is disabled",
        )

    db, current_user = user_db

    workflow_id = f"ebay-import-user-{current_user.id}"
    params = EbayImportParams(
        user_id=current_user.id,
        marketplace_id=request.marketplace_id,
    )

    try:
        client = await get_temporal_client()
        await client.start_workflow(
            EbayImportWorkflow.run,
            params,
            id=workflow_id,
            task_queue=config.temporal_task_queue,
        )

        logger.info(f"Started eBay import workflow: {workflow_id} for user {current_user.id}")

        return {
            "workflow_id": workflow_id,
            "status": "started",
            "imported": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "details": [{"status": "started", "message": "Import workflow started via Temporal"}],
        }

    except Exception as e:
        logger.error(f"eBay import failed to start for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed to start: {str(e)}",
        )


@router.post("/enrich", response_model=EnrichResponse)
async def enrich_ebay_products(
    request: EnrichRequest = Body(default=EnrichRequest()),
    user_db: tuple = Depends(get_user_db),
):
    """Enrich eBay products with offer data (prices, listing info)."""
    db, current_user = user_db

    try:
        importer = EbayImporter(db=db, user_id=current_user.id)
        result = importer.enrichment.enrich_products_batch(
            limit=request.batch_size,
            only_without_price=request.only_without_price,
        )

        logger.info(
            f"eBay enrichment for user {current_user.id}: "
            f"enriched={result['enriched']}, errors={result['errors']}"
        )

        return EnrichResponse(**result)

    except Exception as e:
        logger.error(f"eBay enrichment failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enrichment failed: {str(e)}",
        )


@router.post("/refresh-aspects", response_model=RefreshAspectsResponse)
async def refresh_ebay_aspects(
    batch_size: int = Query(100, ge=1, le=1000, description="Batch size"),
    user_db: tuple = Depends(get_user_db),
):
    """Update aspects (brand, color, size, material) from stored data."""
    db, current_user = user_db

    try:
        importer = EbayImporter(db=db, user_id=current_user.id)
        result = importer.enrichment.refresh_aspects_batch(limit=batch_size)

        logger.info(
            f"eBay aspects refresh for user {current_user.id}: "
            f"updated={result['updated']}, errors={result['errors']}"
        )

        return RefreshAspectsResponse(**result)

    except Exception as e:
        logger.error(f"eBay aspects refresh failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refresh failed: {str(e)}",
        )


# ===== DELETE & STATS ENDPOINTS =====


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ebay_product(
    product_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """Delete an eBay product from local database (not from eBay)."""
    db, current_user = user_db

    product = db.query(EbayProduct).filter(EbayProduct.id == product_id).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"eBay product {product_id} not found",
        )

    db.delete(product)
    db.commit()


@router.get("/stats/summary")
async def get_ebay_stats(
    user_db: tuple = Depends(get_user_db),
):
    """Get eBay products statistics."""
    db, current_user = user_db

    total = db.query(EbayProduct).count()

    # By status
    status_counts = {}
    for status_value in ["active", "inactive", "sold", "ended"]:
        count = db.query(EbayProduct).filter(EbayProduct.status == status_value).count()
        status_counts[status_value] = count

    # By marketplace
    marketplace_counts = {}
    marketplaces = db.query(EbayProduct.marketplace_id).distinct().all()
    for (marketplace,) in marketplaces:
        count = db.query(EbayProduct).filter(EbayProduct.marketplace_id == marketplace).count()
        marketplace_counts[marketplace] = count

    return {
        "total": total,
        "by_status": status_counts,
        "by_marketplace": marketplace_counts,
    }


# ===== LINK / UNLINK ENDPOINTS =====


@router.post("/products/{ebay_product_id}/link", response_model=EbayLinkResponse)
async def link_ebay_product(
    ebay_product_id: int,
    request: LinkProductRequest = Body(default=None),
    user_db: tuple = Depends(get_user_db),
):
    """
    Link an eBay product to a Stoflow product.

    - If product_id provided: link to existing Product
    - If product_id absent: create new Product from EbayProduct
    """
    db, current_user = user_db

    try:
        link_service = EbayLinkService(db, current_user.id)

        # Case 1: Link to existing Product
        if request and request.product_id:
            ebay_product = link_service.link_to_existing_product(
                ebay_product_id=ebay_product_id,
                product_id=request.product_id,
            )
            db.commit()

            return EbayLinkResponse(
                success=True,
                ebay_product_id=ebay_product_id,
                product_id=ebay_product.product_id,
                created=False,
            )

        # Case 2: Create new Product from EbayProduct
        override_data = {}
        if request:
            if request.title:
                override_data["title"] = request.title
            if request.description:
                override_data["description"] = request.description
            if request.price:
                override_data["price"] = Decimal(str(request.price))
            if request.category:
                override_data["category"] = request.category
            if request.brand:
                override_data["brand"] = request.brand

        product, ebay_product = link_service.create_product_from_ebay(
            ebay_product_id=ebay_product_id,
            override_data=override_data if override_data else None,
        )
        db.commit()

        return EbayLinkResponse(
            success=True,
            ebay_product_id=ebay_product_id,
            product_id=product.id,
            created=True,
            images_copied=0,
            product={
                "id": product.id,
                "title": product.title,
                "description": product.description,
                "price": float(product.price) if product.price else None,
                "category": product.category,
                "brand": product.brand,
                "condition": product.condition,
                "status": product.status.value if product.status else None,
            },
        )

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to link eBay product {ebay_product_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to link product: {str(e)}",
        )


@router.delete("/products/{ebay_product_id}/link", response_model=EbayUnlinkResponse)
async def unlink_ebay_product(
    ebay_product_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """Unlink an eBay product from its Stoflow product."""
    db, current_user = user_db

    try:
        link_service = EbayLinkService(db, current_user.id)
        link_service.unlink(ebay_product_id=ebay_product_id)
        db.commit()

        return EbayUnlinkResponse(success=True, ebay_product_id=ebay_product_id)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to unlink eBay product {ebay_product_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unlink product: {str(e)}",
        )
