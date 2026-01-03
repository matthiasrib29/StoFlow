"""
Vinted Orders Routes

Endpoints pour la gestion des commandes Vinted:
- GET /orders: Liste des commandes
- POST /orders/sync: Synchroniser les commandes depuis Vinted (via jobs)
- GET /orders/{transaction_id}/label: Télécharger le bordereau
- GET /deletions: Historique des suppressions
- POST /orders/labels/batch: Téléchargement batch des labels

Updated: 2025-12-19 - Intégration système de jobs

Author: Claude
Date: 2025-12-17
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.dependencies import get_user_db
from models.vinted.vinted_order import VintedOrder
from models.vinted.vinted_deletion import VintedDeletion
from services.vinted import (
    VintedSyncService,
    VintedJobService,
    VintedJobProcessor,
    VintedBordereauService,
)
from .shared import get_active_vinted_connection

router = APIRouter()


@router.get("/orders")
async def list_orders(
    user_db: tuple = Depends(get_user_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    """
    Liste les commandes Vinted en BDD.

    Returns:
        {"orders": list, "total": int}
    """
    db, current_user = user_db

    try:
        total = db.query(VintedOrder).count()
        orders = db.query(VintedOrder).order_by(
            VintedOrder.transaction_id.desc()
        ).offset(offset).limit(limit).all()

        orders_data = []
        for order in orders:
            orders_data.append({
                "transaction_id": order.transaction_id,
                "buyer_id": order.buyer_id,
                "buyer_login": order.buyer_login,
                "status": order.status,
                "total_price": float(order.total_price) if order.total_price else None,
                "currency": order.currency,
                "shipping_price": float(order.shipping_price) if order.shipping_price else None,
                "service_fee": float(order.service_fee) if order.service_fee else None,
                "seller_revenue": float(order.seller_revenue) if order.seller_revenue else None,
                "carrier": order.carrier,
                "tracking_number": order.tracking_number,
                "created_at_vinted": order.created_at_vinted.isoformat() if order.created_at_vinted else None,
                "shipped_at": order.shipped_at.isoformat() if order.shipped_at else None,
                "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
                "completed_at": order.completed_at.isoformat() if order.completed_at else None,
                "products": [
                    {
                        "id": p.id,
                        "vinted_item_id": p.vinted_item_id,
                        "product_id": p.product_id,
                        "title": p.title,
                        "price": float(p.price) if p.price else None,
                        "size": p.size,
                        "brand": p.brand,
                        "photo_url": p.photo_url
                    }
                    for p in order.products
                ]
            })

        return {"orders": orders_data, "total": total, "limit": limit, "offset": offset}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur liste commandes: {str(e)}"
        )


@router.post("/orders/sync")
async def sync_orders(
    user_db: tuple = Depends(get_user_db),
    duplicate_threshold: float = Query(0.8, ge=0, le=1, description="% doublons pour arrêter"),
    process_now: bool = Query(True, description="Exécuter immédiatement ou créer job uniquement"),
) -> dict:
    """
    Synchronise les commandes depuis Vinted via le système de jobs.

    Args:
        duplicate_threshold: % de doublons pour arrêter la sync
        process_now: Si True, exécute immédiatement. Sinon, crée juste le job.

    Returns:
        {
            "job_id": int,
            "status": str,
            "result": dict (si process_now=True)
        }
    """
    db, current_user = user_db

    connection = get_active_vinted_connection(db, current_user.id)

    try:
        job_service = VintedJobService(db)

        # Créer le job de sync commandes
        job = job_service.create_job(
            action_code="orders",
            product_id=None  # Pas de produit spécifique pour sync commandes
        )
        db.commit()

        response = {
            "job_id": job.id,
            "status": job.status.value,
        }

        # Exécuter immédiatement si demandé
        if process_now:
            processor = VintedJobProcessor(db, shop_id=connection.vinted_user_id)
            result = await processor._execute_job(job)
            response["result"] = result.get("result", result)
            response["status"] = "completed" if result.get("success") else "failed"

        return response

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur sync commandes: {str(e)}"
        )


@router.post("/orders/sync/month")
async def sync_orders_by_month(
    user_db: tuple = Depends(get_user_db),
    year: int = Query(..., ge=2020, le=2100, description="Année"),
    month: int = Query(..., ge=1, le=12, description="Mois (1-12)"),
    process_now: bool = Query(True, description="Exécuter immédiatement ou créer job uniquement"),
) -> dict:
    """
    Synchronise les commandes d'un mois spécifique depuis Vinted.

    Crée un VintedJob pour tracer l'opération dans l'UI.

    Args:
        year: Année (ex: 2025)
        month: Mois (1-12)
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

        # Create orders sync job with month parameters
        job = job_service.create_job(
            action_code="orders",
            product_id=None,
            result_data={"year": year, "month": month, "mode": "monthly"}
        )
        db.commit()

        response = {
            "job_id": job.id,
            "status": job.status.value,
            "month": f"{year}-{month:02d}",
        }

        # Execute immediately if requested
        if process_now:
            processor = VintedJobProcessor(db, shop_id=connection.vinted_user_id)
            result = await processor._execute_job(job)
            response["result"] = result.get("result", result)
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
            detail=f"Erreur sync commandes {year}-{month:02d}: {str(e)}"
        )


@router.get("/orders/{transaction_id}/label")
async def download_label(
    transaction_id: int,
    user_db: tuple = Depends(get_user_db),
) -> dict:
    """
    Télécharge le bordereau d'expédition d'une commande.

    Returns:
        {"transaction_id": int, "file_path": str, "success": bool}
    """
    db, current_user = user_db

    try:
        service = VintedBordereauService()
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Téléchargement label via task plugin - à implémenter"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur téléchargement label: {str(e)}"
        )


@router.get("/deletions")
async def list_deletions(
    user_db: tuple = Depends(get_user_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    """
    Liste l'historique des suppressions Vinted.

    Returns:
        {"deletions": list, "total": int}
    """
    db, current_user = user_db

    try:
        total = db.query(VintedDeletion).count()
        deletions = db.query(VintedDeletion).order_by(
            VintedDeletion.date_deleted.desc()
        ).offset(offset).limit(limit).all()

        deletions_data = [
            {
                "id": d.id,
                "id_vinted": d.id_vinted,
                "id_site": d.id_site,
                "price": float(d.price) if d.price else None,
                "date_published": d.date_published.isoformat() if d.date_published else None,
                "date_deleted": d.date_deleted.isoformat() if d.date_deleted else None,
                "view_count": d.view_count,
                "favourite_count": d.favourite_count,
                "days_active": d.days_active
            }
            for d in deletions
        ]

        return {"deletions": deletions_data, "total": total, "limit": limit, "offset": offset}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur liste deletions: {str(e)}"
        )


@router.post("/orders/labels/batch")
async def download_labels_batch(
    transaction_ids: list[int],
    user_db: tuple = Depends(get_user_db),
) -> dict:
    """
    Télécharge plusieurs bordereaux d'expédition.

    Returns:
        {
            "total": int,
            "success_count": int,
            "failed_count": int,
            "results": list
        }
    """
    db, current_user = user_db

    try:
        service = VintedBordereauService()

        results = []
        success_count = 0
        failed_count = 0

        for transaction_id in transaction_ids:
            # À implémenter avec le plugin
            results.append({
                "transaction_id": transaction_id,
                "success": False,
                "error": "Non implémenté - nécessite task plugin"
            })
            failed_count += 1

        return {
            "total": len(transaction_ids),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur batch labels: {str(e)}"
        )
