"""
API Routes eBay.

Endpoints pour l'intégration eBay multi-marketplace.

Fonctionnalités:
- Publication produits (publish/unpublish)
- Gestion business policies
- Gestion inventory locations
- Listing des marketplaces disponibles

Author: Claude
Date: 2025-12-10
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from api.ebay import orders
from models.public.ebay_marketplace_config import MarketplaceConfig
from models.public.user import User
from models.user.ebay_product_marketplace import EbayProductMarketplace
from services.ebay import (
    EbayAccountClient,
    EbayFulfillmentClient,
    EbayPublicationError,
    EbayPublicationService,
    ProductValidationError,
)

router = APIRouter(prefix="/ebay", tags=["eBay"])

# Include orders router
router.include_router(orders.router, tags=["eBay Orders"])


# ========== PYDANTIC SCHEMAS ==========


class PublishProductRequest(BaseModel):
    """Request pour publier un produit sur eBay."""

    product_id: int = Field(..., description="ID du produit à publier")
    marketplace_id: str = Field(..., description="Marketplace eBay (EBAY_FR, EBAY_GB, etc.)")
    category_id: Optional[str] = Field(None, description="eBay category ID (ex: '11450' pour T-shirts)")


class PublishProductResponse(BaseModel):
    """Response après publication d'un produit."""

    success: bool
    sku_derived: str
    offer_id: str
    listing_id: str
    marketplace_id: str
    message: str


class UnpublishProductRequest(BaseModel):
    """Request pour dé-publier un produit."""

    product_id: int = Field(..., description="ID du produit à dé-publier")
    marketplace_id: str = Field(..., description="Marketplace eBay")


class UnpublishProductResponse(BaseModel):
    """Response après dé-publication."""

    success: bool
    sku_derived: str
    message: str


class MarketplaceResponse(BaseModel):
    """Response pour une marketplace eBay."""

    marketplace_id: str
    country_code: str
    site_id: int
    currency: str
    is_active: bool
    language: str
    content_language: str


class ProductMarketplaceStatusResponse(BaseModel):
    """Response pour le status d'un produit sur une marketplace."""

    sku_derived: str
    product_id: int
    marketplace_id: str
    status: str
    ebay_offer_id: Optional[int]
    ebay_listing_id: Optional[int]
    error_message: Optional[str]
    published_at: Optional[str]


class BusinessPoliciesResponse(BaseModel):
    """Response pour les business policies du user."""

    payment_policies: List[dict]
    fulfillment_policies: List[dict]
    return_policies: List[dict]


# ========== ROUTES ==========


@router.post("/publish", response_model=PublishProductResponse, status_code=status.HTTP_201_CREATED)
def publish_product(
    request: PublishProductRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Publie un produit sur une marketplace eBay.

    Workflow:
    1. Convertit le produit en Inventory Item eBay
    2. Crée/Update l'Inventory Item
    3. Crée une Offer
    4. Publie l'Offer
    5. Enregistre dans ebay_products_marketplace

    **Pré-requis:**
    - User doit avoir configuré ses credentials eBay (OAuth)
    - Business policies configurées (payment, fulfillment, return)
    - Inventory location configurée

    **Exemple:**
    ```bash
    curl -X POST "http://localhost:8000/api/ebay/publish" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "product_id": 12345,
        "marketplace_id": "EBAY_FR",
        "category_id": "11450"
      }'
    ```
    """
    try:
        # Initialiser service de publication
        service = EbayPublicationService(db, current_user.id)

        # Publier produit
        result = service.publish_product(
            product_id=request.product_id,
            marketplace_id=request.marketplace_id,
            category_id=request.category_id,
        )

        return PublishProductResponse(
            success=True,
            sku_derived=result["sku_derived"],
            offer_id=result["offer_id"],
            listing_id=result["listing_id"],
            marketplace_id=result["marketplace_id"],
            message=f"Produit publié avec succès sur {request.marketplace_id}",
        )

    except ProductValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation produit échouée: {str(e)}",
        )
    except EbayPublicationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Publication eBay échouée: {str(e)}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.post("/unpublish", response_model=UnpublishProductResponse)
def unpublish_product(
    request: UnpublishProductRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dé-publie un produit d'une marketplace eBay (withdraw).

    Le produit ne sera plus visible sur eBay mais reste dans la base de données.

    **Exemple:**
    ```bash
    curl -X POST "http://localhost:8000/api/ebay/unpublish" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "product_id": 12345,
        "marketplace_id": "EBAY_FR"
      }'
    ```
    """
    try:
        service = EbayPublicationService(db, current_user.id)

        result = service.unpublish_product(
            product_id=request.product_id, marketplace_id=request.marketplace_id
        )

        return UnpublishProductResponse(
            success=True,
            sku_derived=result["sku_derived"],
            message=f"Produit dé-publié avec succès de {request.marketplace_id}",
        )

    except EbayPublicationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dé-publication échouée: {str(e)}",
        )


@router.get("/marketplaces", response_model=List[MarketplaceResponse])
def list_marketplaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Liste toutes les marketplaces eBay disponibles.

    Retourne les 8 marketplaces supportées avec leurs configurations.

    **Exemple:**
    ```bash
    curl "http://localhost:8000/api/ebay/marketplaces" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```
    """
    marketplaces = db.query(MarketplaceConfig).filter(
        MarketplaceConfig.is_active == True
    ).all()

    return [
        MarketplaceResponse(
            marketplace_id=m.marketplace_id,
            country_code=m.country_code,
            site_id=m.site_id,
            currency=m.currency,
            is_active=m.is_active,
            language=m.get_language(),
            content_language=m.get_content_language(),
        )
        for m in marketplaces
    ]


@router.get("/products/{product_id}/status", response_model=List[ProductMarketplaceStatusResponse])
def get_product_status(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Récupère le status de publication d'un produit sur toutes les marketplaces.

    Retourne la liste des marketplaces où le produit est publié ou en erreur.

    **Exemple:**
    ```bash
    curl "http://localhost:8000/api/ebay/products/12345/status" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```
    """
    # Récupérer tous les statuts du produit
    product_marketplaces = (
        db.query(EbayProductMarketplace)
        .filter(EbayProductMarketplace.product_id == product_id)
        .all()
    )

    if not product_marketplaces:
        return []

    return [
        ProductMarketplaceStatusResponse(
            sku_derived=pm.sku_derived,
            product_id=pm.product_id,
            marketplace_id=pm.marketplace_id,
            status=pm.status,
            ebay_offer_id=pm.ebay_offer_id,
            ebay_listing_id=pm.ebay_listing_id,
            error_message=pm.error_message,
            published_at=pm.published_at.isoformat() if pm.published_at else None,
        )
        for pm in product_marketplaces
    ]


@router.get("/policies", response_model=BusinessPoliciesResponse)
def get_business_policies(
    marketplace_id: str = "EBAY_FR",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Récupère les business policies eBay du user pour une marketplace.

    Retourne les payment, fulfillment et return policies configurées.

    **Exemple:**
    ```bash
    curl "http://localhost:8000/api/ebay/policies?marketplace_id=EBAY_FR" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```
    """
    try:
        client = EbayAccountClient(db, current_user.id, marketplace_id=marketplace_id)

        # Récupérer les 3 types de policies
        payment_policies_result = client.get_payment_policies(marketplace_id)
        fulfillment_policies_result = client.get_fulfillment_policies(marketplace_id)
        return_policies_result = client.get_return_policies(marketplace_id)

        return BusinessPoliciesResponse(
            payment_policies=payment_policies_result.get("paymentPolicies", []),
            fulfillment_policies=fulfillment_policies_result.get(
                "fulfillmentPolicies", []
            ),
            return_policies=return_policies_result.get("returnPolicies", []),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User eBay non configuré: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur récupération policies: {str(e)}",
        )
