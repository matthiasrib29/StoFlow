"""
Vinted Publishing Routes

Endpoints pour la publication et préparation des produits:
- POST /products/{product_id}/prepare: Préparer un produit (preview)
- POST /products/publish/batch: Publication batch via système de jobs
- POST /products/{product_id}/publish: Publication unitaire via système de jobs

Note: Les endpoints fetch-description ont été supprimés (2025-12-18).
L'enrichissement des descriptions se fait automatiquement lors de la sync.

Updated: 2025-12-19 - Intégration système de jobs

Author: Claude
Date: 2025-12-17
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import get_user_db
from models.user.product import Product
from services.vinted import (
    VintedSyncService,
    VintedJobService,
    VintedJobProcessor,
    VintedPricingService,
    VintedMappingService,
    VintedProductValidator,
    VintedTitleService,
    VintedDescriptionService,
)
from .shared import get_active_vinted_connection

router = APIRouter()


@router.post("/products/{product_id}/prepare")
async def prepare_product(
    product_id: int,
    user_db: tuple = Depends(get_user_db),
) -> dict:
    """
    Prépare/preview un produit avant publication.

    Génère titre, description, prix sans publier.
    Utile pour valider avant publication.

    Returns:
        {
            "product_id": int,
            "title": str,
            "description": str,
            "price": float,
            "mapped_attributes": dict,
            "ready_to_publish": bool,
            "validation_errors": list
        }
    """
    db, current_user = user_db

    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produit #{product_id} non trouvé"
            )

        # Validation
        validation_errors = []
        is_valid, error = VintedProductValidator.validate_for_creation(product)
        if not is_valid:
            validation_errors.append(error)

        # Générer titre et description
        title = VintedTitleService.generate_title(product)
        description = VintedDescriptionService.generate_description(product)

        # Calculer prix
        try:
            price = VintedPricingService.calculate_vinted_price(db, product)
        except ValueError as e:
            price = product.price
            validation_errors.append(f"Prix: {str(e)}")

        # Mapper attributs
        mapped_attrs = VintedMappingService.map_all_attributes(db, product)

        # Valider attributs
        attrs_valid, attrs_error = VintedProductValidator.validate_mapped_attributes(mapped_attrs, product.id)
        if not attrs_valid:
            validation_errors.append(attrs_error)

        return {
            "product_id": product_id,
            "title": title,
            "description": description,
            "price": price,
            "mapped_attributes": mapped_attrs,
            "ready_to_publish": len(validation_errors) == 0,
            "validation_errors": validation_errors
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur préparation: {str(e)}"
        )


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
        db.commit()

        response = {
            "job_id": job.id,
            "status": job.status.value,
            "product_id": product_id,
        }

        # Exécuter immédiatement si demandé
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
            processor = VintedJobProcessor(db, shop_id=connection.vinted_user_id)
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
