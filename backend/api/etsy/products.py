"""
Etsy Products & Listings Routes

Endpoints for product publication and listing management.

Author: Claude
Date: 2025-12-17
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import get_user_db
from models.user.product import Product
from services.etsy import (
    EtsyListingClient,
    EtsyPublicationService,
    ProductValidationError,
)
from shared.logging_setup import get_logger

from .schemas import (
    ListingResponse,
    PublishProductRequest,
    PublishProductResponse,
    UpdateListingRequest,
)

router = APIRouter()
logger = get_logger(__name__)


# ========== PRODUCT PUBLICATION ==========


@router.post("/products/publish", response_model=PublishProductResponse)
def publish_product_to_etsy(
    request: PublishProductRequest,
    user_db: tuple = Depends(get_user_db),
):
    """
    Publie un produit Stoflow sur Etsy.

    Args:
        request: Donnees de publication (product_id, taxonomy_id, etc.)

    Returns:
        Resultat de la publication avec listing_id et URL
    """
    db, current_user = user_db

    product = (
        db.query(Product)
        .filter(
            Product.id == request.product_id,
            Product.user_id == current_user.id,
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {request.product_id} not found",
        )

    try:
        service = EtsyPublicationService(db, current_user.id)
        result = service.publish_product(
            product=product,
            taxonomy_id=request.taxonomy_id,
            shipping_profile_id=request.shipping_profile_id,
            return_policy_id=request.return_policy_id,
            shop_section_id=request.shop_section_id,
            state=request.state,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        logger.info(
            f"Product {product.id} published to Etsy: {result['listing_id']}"
        )

        return PublishProductResponse(**result)

    except ProductValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error publishing to Etsy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error publishing to Etsy: {str(e)}",
        )


@router.put("/products/{listing_id}")
def update_etsy_listing(
    listing_id: int,
    request: UpdateListingRequest,
    user_db: tuple = Depends(get_user_db),
):
    """
    Met a jour un listing Etsy avec les donnees d'un produit Stoflow.

    Args:
        listing_id: ID du listing Etsy a mettre a jour
        request.product_id: ID du produit Stoflow source

    Returns:
        Resultat de la mise a jour
    """
    db, current_user = user_db

    product = (
        db.query(Product)
        .filter(
            Product.id == request.product_id,
            Product.user_id == current_user.id,
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {request.product_id} not found",
        )

    try:
        service = EtsyPublicationService(db, current_user.id)
        result = service.update_product(product, listing_id)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        logger.info(f"Etsy listing {listing_id} updated")

        return result

    except Exception as e:
        logger.error(f"Error updating Etsy listing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating listing: {str(e)}",
        )


@router.delete("/products/{listing_id}", status_code=status.HTTP_200_OK)
def delete_etsy_listing(
    listing_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """
    Supprime un listing Etsy.

    Args:
        listing_id: ID du listing Etsy a supprimer

    Returns:
        Resultat de la suppression
    """
    db, current_user = user_db

    try:
        service = EtsyPublicationService(db, current_user.id)
        result = service.delete_product(listing_id)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        logger.info(f"Etsy listing {listing_id} deleted")

        return result

    except Exception as e:
        logger.error(f"Error deleting Etsy listing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting listing: {str(e)}",
        )


# ========== LISTINGS MANAGEMENT ==========


@router.get("/listings/active", response_model=List[ListingResponse])
def get_active_listings(
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_db: tuple = Depends(get_user_db),
):
    """
    Recupere les listings actifs du shop Etsy.
    """
    db, current_user = user_db

    try:
        client = EtsyListingClient(db, current_user.id)
        result = client.get_shop_listings_active(limit=limit, offset=offset)

        listings = result.get("results", [])

        return [
            ListingResponse(
                listing_id=listing["listing_id"],
                title=listing["title"],
                state=listing["state"],
                price=float(listing["price"]["amount"]) / listing["price"]["divisor"],
                quantity=listing["quantity"],
                url=listing.get("url"),
                created_timestamp=listing.get("created_timestamp"),
                updated_timestamp=listing.get("updated_timestamp"),
            )
            for listing in listings
        ]

    except Exception as e:
        logger.error(f"Error getting active listings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting listings: {str(e)}",
        )


@router.get("/listings/{listing_id}")
def get_listing_details(
    listing_id: int,
    user_db: tuple = Depends(get_user_db),
):
    """
    Recupere les details d'un listing Etsy.
    """
    db, current_user = user_db

    try:
        client = EtsyListingClient(db, current_user.id)
        listing = client.get_listing(listing_id)

        return listing

    except Exception as e:
        logger.error(f"Error getting listing {listing_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting listing: {str(e)}",
        )
