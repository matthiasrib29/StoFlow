"""
Vinted Products Routes

Endpoints pour la gestion des produits Vinted:
- GET /stats: Statistiques agrégées
- GET /products: Liste des produits
- GET /products/{vinted_id}: Détail d'un produit
- POST /products/sync: Synchroniser depuis Vinted
- POST /products/{product_id}/publish: Publier un produit
- PUT /products/{product_id}: Mettre à jour un produit
- DELETE /products/{vinted_id}: Supprimer un produit

Author: Claude
Date: 2025-12-17
"""

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.dependencies import get_user_db
from models.user.vinted_product import VintedProduct
from services.vinted import VintedSyncService, VintedJobService, VintedJobProcessor
from .shared import get_active_vinted_connection

router = APIRouter()


@router.get("/stats")
async def get_vinted_stats(
    user_db: tuple = Depends(get_user_db),
) -> dict:
    """
    Récupère les statistiques agrégées Vinted.

    Returns:
        {
            "activePublications": int,
            "totalViews": int,
            "totalFavourites": int,
            "potentialRevenue": float,
            "totalProducts": int
        }
    """
    db, current_user = user_db

    try:
        active_count = db.query(func.count(VintedProduct.id)).filter(
            VintedProduct.status == 'published'
        ).scalar() or 0

        total_views = db.query(func.sum(VintedProduct.view_count)).scalar() or 0
        total_favourites = db.query(func.sum(VintedProduct.favourite_count)).scalar() or 0

        potential_revenue = db.query(func.sum(VintedProduct.price)).filter(
            VintedProduct.status == 'published'
        ).scalar() or Decimal('0')

        total_products = db.query(func.count(VintedProduct.id)).scalar() or 0

        return {
            "activePublications": active_count,
            "totalViews": int(total_views),
            "totalFavourites": int(total_favourites),
            "potentialRevenue": float(potential_revenue),
            "totalProducts": total_products
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur stats: {str(e)}"
        )


@router.get("/products")
async def list_products(
    user_db: tuple = Depends(get_user_db),
    status_filter: Optional[str] = Query(None, description="Filter: published, sold, pending"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict:
    """
    Liste les produits Vinted en BDD.

    Returns:
        {"products": list, "total": int}
    """
    db, current_user = user_db

    try:
        query = db.query(VintedProduct)

        if status_filter:
            query = query.filter(VintedProduct.status == status_filter)

        total = query.count()
        products = query.order_by(VintedProduct.published_at.desc().nullslast()).offset(offset).limit(limit).all()

        products_data = []
        for vp in products:
            products_data.append({
                "id": vp.id,
                "vinted_id": vp.vinted_id,
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
                "color": vp.color,
                "material": vp.material,
                "category": vp.category,
                "catalog_id": vp.catalog_id,
                "measurements": vp.measurements,
                "image_url": vp.photo_url,
                "is_draft": vp.is_draft,
                "is_closed": vp.is_closed,
                "is_reserved": vp.is_reserved,
                "published_at": vp.published_at.isoformat() if vp.published_at else None,
            })

        return {"products": products_data, "total": total, "limit": limit, "offset": offset}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur liste produits: {str(e)}"
        )


@router.get("/products/{vinted_id}")
async def get_product(
    vinted_id: int,
    user_db: tuple = Depends(get_user_db),
) -> dict:
    """
    Récupère un produit Vinted par son ID Vinted.
    """
    db, current_user = user_db

    vinted_product = db.query(VintedProduct).filter(
        VintedProduct.vinted_id == vinted_id
    ).first()

    if not vinted_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Produit Vinted #{vinted_id} non trouvé"
        )

    return {
        "id": vinted_product.id,
        "vinted_id": vinted_product.vinted_id,
        "title": vinted_product.title,
        "description": vinted_product.description,
        "price": float(vinted_product.price) if vinted_product.price else None,
        "total_price": float(vinted_product.total_price) if vinted_product.total_price else None,
        "currency": vinted_product.currency,
        "url": vinted_product.url,
        "status": vinted_product.status,
        "condition": vinted_product.condition,
        "condition_id": vinted_product.condition_id,
        "view_count": vinted_product.view_count,
        "favourite_count": vinted_product.favourite_count,
        "brand": vinted_product.brand,
        "brand_id": vinted_product.brand_id,
        "size": vinted_product.size,
        "size_id": vinted_product.size_id,
        "color": vinted_product.color,
        "material": vinted_product.material,
        "category": vinted_product.category,
        "catalog_id": vinted_product.catalog_id,
        "measurements": vinted_product.measurements,
        "measurement_width": vinted_product.measurement_width,
        "measurement_length": vinted_product.measurement_length,
        "manufacturer_labelling": vinted_product.manufacturer_labelling,
        "image_url": vinted_product.photo_url,
        "is_draft": vinted_product.is_draft,
        "is_closed": vinted_product.is_closed,
        "is_reserved": vinted_product.is_reserved,
        "is_hidden": vinted_product.is_hidden,
        "seller_id": vinted_product.seller_id,
        "seller_login": vinted_product.seller_login,
        "service_fee": float(vinted_product.service_fee) if vinted_product.service_fee else None,
        "buyer_protection_fee": float(vinted_product.buyer_protection_fee) if vinted_product.buyer_protection_fee else None,
        "shipping_price": float(vinted_product.shipping_price) if vinted_product.shipping_price else None,
        "published_at": vinted_product.published_at.isoformat() if vinted_product.published_at else None,
        "created_at": vinted_product.created_at.isoformat() if vinted_product.created_at else None,
        "updated_at": vinted_product.updated_at.isoformat() if vinted_product.updated_at else None,
    }


@router.post("/products/sync")
async def sync_products(
    user_db: tuple = Depends(get_user_db),
    process_now: bool = Query(True, description="Exécuter immédiatement ou créer job uniquement"),
) -> dict:
    """
    Synchronise les produits depuis la garde-robe Vinted.

    Crée un VintedJob pour tracer l'opération dans l'UI.

    Args:
        process_now: Si True, exécute immédiatement. Sinon, crée juste le job.

    Returns:
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

        # Create sync job (product_id=None for sync operations)
        job = job_service.create_job(
            action_code="sync",
            product_id=None
        )
        db.commit()

        response = {
            "job_id": job.id,
            "status": job.status.value,
        }

        # Execute immediately if requested
        if process_now:
            processor = VintedJobProcessor(db, shop_id=connection.vinted_user_id)
            result = await processor._execute_job(job)
            response["result"] = result
            response["status"] = "completed" if result.get("success") else "failed"

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur sync: {str(e)}"
        )


# Note: POST /products/{product_id}/publish is in publishing.py (uses job system)


@router.put("/products/{product_id}")
async def update_product(
    product_id: int,
    user_db: tuple = Depends(get_user_db),
    process_now: bool = Query(True, description="Exécuter immédiatement ou créer job uniquement"),
) -> dict:
    """
    Met à jour un produit Vinted (prix, titre, description).

    Crée un VintedJob pour tracer l'opération dans l'UI.

    Args:
        product_id: ID du produit à mettre à jour
        process_now: Si True, exécute immédiatement. Sinon, crée juste le job.

    Returns:
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
        db.commit()

        response = {
            "job_id": job.id,
            "status": job.status.value,
            "product_id": product_id,
        }

        # Execute immediately if requested
        if process_now:
            processor = VintedJobProcessor(db, shop_id=connection.vinted_user_id)
            result = await processor._execute_job(job)
            response["result"] = result
            response["status"] = "completed" if result.get("success") else "failed"

        return response

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur mise à jour: {str(e)}"
        )


@router.delete("/products/{vinted_id}")
async def delete_product(
    vinted_id: int,
    force: bool = Query(False, description="Supprimer sans vérifier les conditions"),
    user_db: tuple = Depends(get_user_db),
) -> dict:
    """
    Supprime un produit Vinted de la BDD.

    Note: La suppression sur Vinted doit passer par le plugin browser.

    Returns:
        {"success": bool, "vinted_id": int}
    """
    db, current_user = user_db

    try:
        vinted_product = db.query(VintedProduct).filter(
            VintedProduct.vinted_id == vinted_id
        ).first()

        if not vinted_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produit Vinted #{vinted_id} non trouvé"
            )

        db.delete(vinted_product)
        db.commit()

        return {"success": True, "vinted_id": vinted_id}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur suppression: {str(e)}"
        )
