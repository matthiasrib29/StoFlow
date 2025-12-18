"""
Vinted Publishing Routes

Endpoints pour la publication et préparation des produits:
- POST /products/{product_id}/prepare: Préparer un produit (preview)
- POST /products/publish/batch: Publication batch

Note: Les endpoints fetch-description ont été supprimés (2025-12-18).
L'enrichissement des descriptions se fait automatiquement lors de la sync.

Author: Claude
Date: 2025-12-17
"""

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_user_db
from models.user.product import Product
from services.vinted import (
    VintedSyncService,
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


@router.post("/products/publish/batch")
async def publish_batch(
    product_ids: list[int],
    user_db: tuple = Depends(get_user_db),
) -> dict:
    """
    Publie plusieurs produits sur Vinted.

    Returns:
        {
            "total": int,
            "success_count": int,
            "failed_count": int,
            "results": list
        }
    """
    db, current_user = user_db

    connection = get_active_vinted_connection(db, current_user.id)

    try:
        service = VintedSyncService(shop_id=connection.vinted_user_id)

        results = []
        success_count = 0
        failed_count = 0

        for product_id in product_ids:
            try:
                result = await service.publish_product(db, product_id)
                results.append({
                    "product_id": product_id,
                    "success": result.get("success", False),
                    "vinted_id": result.get("vinted_id"),
                    "error": result.get("error")
                })
                if result.get("success"):
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                results.append({
                    "product_id": product_id,
                    "success": False,
                    "error": str(e)
                })
                failed_count += 1

        return {
            "total": len(product_ids),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur batch: {str(e)}"
        )


# Note: fetch-description endpoints removed (2025-12-18)
# Description enrichment is now done automatically during sync_products_from_api
# See VintedApiSyncService._enrich_products_without_description()
