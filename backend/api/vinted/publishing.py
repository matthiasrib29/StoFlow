"""
Vinted Publishing Routes

Endpoints pour la publication des produits:
- POST /products/{product_id}/publish: Publication unitaire via système de jobs
- POST /products/publish/batch: Publication batch via système de jobs

Updated: 2025-12-19 - Intégration système de jobs
Updated: 2026-01-05 - Suppression endpoint prepare

Author: Claude
Date: 2025-12-17
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import get_user_db
from models.user.product import Product
from services.vinted import VintedJobService
from services.marketplace.marketplace_job_processor import MarketplaceJobProcessor
from shared.database import set_user_search_path
from .shared import get_active_vinted_connection

router = APIRouter()


@router.post("/products/{product_id}/publish")
async def publish_single_product(
    product_id: int,
    user_db: tuple = Depends(get_user_db),
    process_now: bool = Query(True, description="Exécuter immédiatement ou créer job uniquement"),
) -> dict:
    """
    Publie un produit unique sur Vinted.

    Args:
        product_id: ID du produit à publier
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

        # Créer le job
        job = job_service.create_job(
            action_code="publish",
            product_id=product_id
        )

        # Store values BEFORE commit (SET LOCAL search_path resets on commit)
        job_id = job.id
        job_status = job.status.value
        shop_id = connection.vinted_user_id

        db.commit()
        set_user_search_path(db, current_user.id)  # Re-set after commit
        db.refresh(job)  # Reload job with correct search_path

        response = {
            "job_id": job_id,
            "status": job_status,
            "product_id": product_id,
        }

        # Exécuter immédiatement si demandé
        if process_now:
            processor = MarketplaceJobProcessor(db, user_id=current_user.id, shop_id=shop_id, marketplace="vinted")
            result = await processor._execute_job(job)
            response["result"] = result
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
            detail=f"Erreur publication: {str(e)}"
        )


@router.post("/products/publish/batch")
async def publish_batch(
    product_ids: list[int],
    user_db: tuple = Depends(get_user_db),
    process_now: bool = Query(False, description="Exécuter immédiatement ou créer jobs uniquement"),
) -> dict:
    """
    Crée des jobs de publication pour plusieurs produits.

    Args:
        product_ids: Liste des IDs produits à publier
        process_now: Si True, exécute tous les jobs immédiatement.
                     Si False (défaut), crée les jobs et retourne le batch_id.

    Returns:
        {
            "batch_id": str,
            "jobs_created": int,
            "status": str,
            "results": list (si process_now=True)
        }
    """
    db, current_user = user_db

    connection = get_active_vinted_connection(db, current_user.id)

    # Store BEFORE any potential commit (SET LOCAL search_path resets on commit)
    shop_id = connection.vinted_user_id

    try:
        job_service = VintedJobService(db)

        # Créer le batch de jobs
        batch_id, jobs = job_service.create_batch_jobs(
            action_code="publish",
            product_ids=product_ids
        )

        response = {
            "batch_id": batch_id,
            "jobs_created": len(jobs),
            "status": "pending",
            "jobs": [
                {
                    "job_id": job.id,
                    "product_id": job.product_id,
                    "status": job.status.value
                }
                for job in jobs
            ]
        }

        # Exécuter immédiatement si demandé
        if process_now:
            processor = MarketplaceJobProcessor(db, user_id=current_user.id, shop_id=shop_id, marketplace="vinted")
            batch_result = await processor.process_batch(batch_id)
            response["status"] = "processed"
            response["success_count"] = batch_result["success_count"]
            response["failed_count"] = batch_result["failed_count"]
            response["results"] = batch_result["results"]

        return response

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur batch: {str(e)}"
        )


# Note: fetch-description endpoints removed (2025-12-18)
# Description enrichment is now done automatically during sync_products_from_api
# See VintedApiSyncService._enrich_products_without_description()
