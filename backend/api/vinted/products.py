"""
Vinted Products Routes

Endpoints pour la gestion des produits Vinted:
- GET /stats: Statistiques agrégées
- GET /products: Liste des produits
- GET /products/{vinted_id}: Détail d'un produit
- POST /products/sync: Synchroniser depuis Vinted
- PUT /products/{product_id}: Mettre à jour un produit
- DELETE /products/{vinted_id}: Supprimer un produit (local)
- POST /products/{vinted_id}/link: Lier/créer Product Stoflow
- DELETE /products/{vinted_id}/link: Délier Product Stoflow

Updated: 2026-01-05 - Suppression linkable, fusion link/create

Author: Claude
Date: 2025-12-17

Updated 2026-01-05:
- create_and_link now copies images from Vinted to R2
"""

import asyncio
import json
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from pydantic import BaseModel

from api.dependencies import get_user_db
from models.user.vinted_product import VintedProduct
from schemas.vinted_schemas import (
    VintedStatsResponse,
    VintedProductsListResponse,
    VintedProductDetailResponse,
    VintedJobResponse,
    VintedDeleteResponse,
    VintedLinkResponse,
    VintedUnlinkResponse,
)
from shared.error_handling import not_found, bad_request
from services.file_service import FileService
from services.product_service import ProductService
from services.vinted import VintedSyncService, VintedJobService
from services.marketplace.marketplace_job_processor import MarketplaceJobProcessor
from services.vinted.vinted_link_service import VintedLinkService
from services.vinted.vinted_stats_service import VintedStatsService
from services.vinted.vinted_image_sync_service import VintedImageSyncService
from shared.logging_setup import get_logger
from .shared import get_active_vinted_connection

logger = get_logger(__name__)


# ===== SCHEMAS =====

class LinkProductRequest(BaseModel):
    """
    Request body for linking VintedProduct to Product.

    - If product_id is provided: link to existing Product
    - If product_id is None: create new Product from VintedProduct data
    """
    product_id: Optional[int] = None  # None = create new Product

    # Optional overrides when creating new Product (ignored if product_id is set)
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    brand: Optional[str] = None

router = APIRouter()


@router.get("/stats", response_model=VintedStatsResponse)
async def get_vinted_stats(
    user_db: tuple = Depends(get_user_db),
):
    """
    Récupère les statistiques agrégées Vinted.

    Returns:
        VintedStatsResponse: Statistiques (publications actives, vues, favoris, revenu, total)
    """
    db, current_user = user_db

    try:
        stats_service = VintedStatsService(db)
        return stats_service.get_publication_stats()

    except Exception as e:
        logger.error(f"Failed to get Vinted stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur stats: {str(e)}"
        )


@router.get("/products", response_model=VintedProductsListResponse)
async def list_products(
    user_db: tuple = Depends(get_user_db),
    status_filter: Optional[str] = Query(None, description="Filter: published, sold, pending"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Liste les produits Vinted en BDD.

    Returns:
        VintedProductsListResponse: Liste paginée avec offset/limit
    """
    db, current_user = user_db

    query = db.query(VintedProduct)

    if status_filter:
        query = query.filter(VintedProduct.status == status_filter)

    total = query.count()
    products = query.order_by(VintedProduct.published_at.desc().nullslast()).offset(offset).limit(limit).all()

    products_data = []
    for vp in products:
        products_data.append({
            "vinted_id": vp.vinted_id,
            "product_id": vp.product_id,  # Link to Stoflow Product
            "title": vp.title,
            "description": vp.description,
            "price": float(vp.price) if vp.price else None,
            "currency": vp.currency,
            "url": vp.url,
            "status": vp.status,
            "condition": vp.condition,
            "view_count": vp.view_count,
            "favourite_count": vp.favourite_count,
            "brand": vp.brand,
            "brand_id": vp.brand_id,
            "size": vp.size,
            "size_id": vp.size_id,
            "color1": vp.color1,
            "catalog_id": vp.catalog_id,
            "image_url": vp.primary_photo_url,
            "is_draft": vp.is_draft,
            "is_closed": vp.is_closed,
            "is_reserved": vp.is_reserved,
            "published_at": vp.published_at.isoformat() if vp.published_at else None,
        })

    return {"products": products_data, "total": total, "limit": limit, "offset": offset}


@router.get("/products/{vinted_id}", response_model=VintedProductDetailResponse)
async def get_product(
    vinted_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """
    Récupère un produit Vinted par son ID Vinted.

    Returns:
        VintedProductDetailResponse: Détails complets du produit
    """
    db, current_user = user_db

    vinted_product = db.query(VintedProduct).filter(
        VintedProduct.vinted_id == vinted_id
    ).first()

    if not vinted_product:
        raise not_found("Produit Vinted", vinted_id)

    return {
        "vinted_id": vinted_product.vinted_id,
        "product_id": vinted_product.product_id,  # Link to Stoflow Product
        "title": vinted_product.title,
        "description": vinted_product.description,
        "price": float(vinted_product.price) if vinted_product.price else None,
        "total_price": float(vinted_product.total_price) if vinted_product.total_price else None,
        "currency": vinted_product.currency,
        "url": vinted_product.url,
        "status": vinted_product.status,
        "condition": vinted_product.condition,
        "status_id": vinted_product.status_id,
        "view_count": vinted_product.view_count,
        "favourite_count": vinted_product.favourite_count,
        "brand": vinted_product.brand,
        "brand_id": vinted_product.brand_id,
        "size": vinted_product.size,
        "size_id": vinted_product.size_id,
        "color1": vinted_product.color1,
        "catalog_id": vinted_product.catalog_id,
        "measurement_width": vinted_product.measurement_width,
        "measurement_length": vinted_product.measurement_length,
        "manufacturer_labelling": vinted_product.manufacturer_labelling,
        "image_url": vinted_product.primary_photo_url,
        "is_draft": vinted_product.is_draft,
        "is_closed": vinted_product.is_closed,
        "is_reserved": vinted_product.is_reserved,
        "is_hidden": vinted_product.is_hidden,
        "seller_id": vinted_product.seller_id,
        "seller_login": vinted_product.seller_login,
        "service_fee": float(vinted_product.service_fee) if vinted_product.service_fee else None,
        "published_at": vinted_product.published_at.isoformat() if vinted_product.published_at else None,
        "created_at": vinted_product.created_at.isoformat() if vinted_product.created_at else None,
        "updated_at": vinted_product.updated_at.isoformat() if vinted_product.updated_at else None,
    }


@router.post("/products/sync", response_model=VintedJobResponse)
async def sync_products(
    user_db: tuple = Depends(get_user_db),
    process_now: bool = Query(True, description="Exécuter immédiatement ou créer job uniquement"),
):
    """
    Synchronise les produits depuis la garde-robe Vinted.

    Crée un MarketplaceJob pour tracer l'opération dans l'UI.

    Args:
        process_now: Si True, exécute immédiatement. Sinon, crée juste le job.

    Returns:
        VintedJobResponse: Job info avec statut et résultat optionnel
    """
    db, current_user = user_db

    connection = get_active_vinted_connection(db, current_user.id)

    job_service = VintedJobService(db)

    # Create sync job (product_id=None for sync operations)
    job = job_service.create_job(
        action_code="sync",
        product_id=None
    )

    # Store values BEFORE commit (SET LOCAL search_path resets on commit)
    job_id = job.id
    job_status = job.status.value
    shop_id = connection.vinted_user_id

    db.commit()
    db.refresh(job)

    response = {
        "job_id": job_id,
        "status": job_status,
    }

    # Execute immediately if requested
    if process_now:
        processor = MarketplaceJobProcessor(db, user_id=current_user.id, shop_id=shop_id, marketplace="vinted")
        result = await processor._execute_job(job)
        response["result"] = result
        response["status"] = "completed" if result.get("success") else "failed"

    return response


# Note: POST /products/{product_id}/publish is in publishing.py (uses job system)


@router.put("/products/{product_id}", response_model=VintedJobResponse)
async def update_product(
    product_id: int,
    user_db: tuple = Depends(get_user_db),
    process_now: bool = Query(True, description="Exécuter immédiatement ou créer job uniquement"),
):
    """
    Met à jour un produit Vinted (prix, titre, description).

    Crée un MarketplaceJob pour tracer l'opération dans l'UI.

    Args:
        product_id: ID du produit à mettre à jour
        process_now: Si True, exécute immédiatement. Sinon, crée juste le job.

    Returns:
        VintedJobResponse: Job info avec statut et résultat optionnel

    Old returns:
        {
            "job_id": int,
            "status": str,
            "result": dict | None (si process_now=True)
        }
    """
    db, current_user = user_db

    connection = get_active_vinted_connection(db, current_user.id)

    try:
        job_service = VintedJobService(db)

        # Create update job
        job = job_service.create_job(
            action_code="update",
            product_id=product_id
        )

        # Store values BEFORE commit (SET LOCAL search_path resets on commit)
        job_id = job.id
        job_status = job.status.value
        shop_id = connection.vinted_user_id

        db.commit()
        db.refresh(job)

        response = {
            "job_id": job_id,
            "status": job_status,
            "product_id": product_id,
        }

        # Execute immediately if requested
        if process_now:
            processor = MarketplaceJobProcessor(db, user_id=current_user.id, shop_id=shop_id, marketplace="vinted")
            result = await processor._execute_job(job)
            response["result"] = result
            response["status"] = "completed" if result.get("success") else "failed"

        return response

    except ValueError as e:
        # Business logic error from service
        raise bad_request(str(e))


@router.delete("/products/{vinted_id}", response_model=VintedDeleteResponse)
async def delete_product(
    vinted_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """
    Supprime un produit Vinted de la BDD locale.

    Note: Ne supprime PAS le listing sur Vinted (nécessite plugin browser).

    Returns:
        VintedDeleteResponse: Confirmation de suppression avec vinted_id
    """
    db, current_user = user_db

    vinted_product = db.query(VintedProduct).filter(
        VintedProduct.vinted_id == vinted_id
    ).first()

    if not vinted_product:
        raise not_found("Produit Vinted", vinted_id)

    try:
        db.delete(vinted_product)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete Vinted product {vinted_id}: {e}", exc_info=True)
        raise

    return {"success": True, "vinted_id": vinted_id}


# ===== LINK ENDPOINTS =====


@router.post("/products/{vinted_id}/link", response_model=VintedLinkResponse)
async def link_product(
    vinted_id: int,
    request: LinkProductRequest = None,
    user_db: tuple = Depends(get_user_db),
):
    """
    Lie un produit Vinted à un produit Stoflow.

    - Si product_id fourni : lie au Product existant
    - Si product_id absent/null : crée un nouveau Product depuis VintedProduct

    Args:
        vinted_id: ID Vinted du produit
        request.product_id: ID Product existant (optionnel)
        request.title/description/...: Overrides pour création (optionnel)

    Returns:
        VintedLinkResponse: Résultat liaison/création avec images_copied si créé

    Note: When creating new Product, images are downloaded from Vinted and uploaded to R2.
          If any image fails, the entire operation is rolled back.
    """
    db, current_user = user_db

    try:
        link_service = VintedLinkService(db)

        # Case 1: Link to existing Product
        if request and request.product_id:
            vinted_product = link_service.link_to_existing_product(
                vinted_id=vinted_id,
                product_id=request.product_id
            )
            db.commit()

            return {
                "success": True,
                "vinted_id": vinted_id,
                "product_id": vinted_product.product_id,
                "created": False
            }

        # Case 2: Create new Product from VintedProduct
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

        product, vinted_product = link_service.create_product_from_vinted(
            vinted_id=vinted_id,
            override_data=override_data if override_data else None
        )

        # ===== COPY IMAGES FROM VINTED TO R2 (2026-01-08 - Refactored) =====
        images_copied, images_failed = await VintedImageSyncService.sync_images_to_product(
            db=db,
            vinted_product=vinted_product,
            product=product,
            user_id=current_user.id
        )

        db.commit()

        return {
            "success": True,
            "vinted_id": vinted_id,
            "product_id": product.id,
            "created": True,
            "images_copied": images_copied,
            "images_failed": images_failed,
            "product": {
                "id": product.id,
                "title": product.title,
                "description": product.description,
                "price": float(product.price) if product.price else None,
                "category": product.category,
                "brand": product.brand,
                "condition": product.condition,
                "status": product.status.value if product.status else None,
                "images": product.images or [],
            }
        }

    except ValueError as e:
        db.rollback()
        # Business logic error from service
        raise bad_request(str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to link Vinted product {vinted_id}: {e}", exc_info=True)
        raise


@router.delete("/products/{vinted_id}/link", response_model=VintedUnlinkResponse)
async def unlink_product(
    vinted_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """
    Délie un produit Vinted de son produit Stoflow.

    Args:
        vinted_id: ID Vinted du produit

    Returns:
        VintedUnlinkResponse: Confirmation de déliaison
    """
    db, current_user = user_db

    try:
        link_service = VintedLinkService(db)
        link_service.unlink(vinted_id=vinted_id)
        db.commit()

        return {
            "success": True,
            "vinted_id": vinted_id
        }

    except ValueError as e:
        # Business logic error from service
        raise bad_request(str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to unlink Vinted product {vinted_id}: {e}", exc_info=True)
        raise


