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

from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, status

from shared.logging import get_logger

logger = get_logger("api.ebay")
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db, get_user_db
from api.ebay import orders
from models.public.ebay_marketplace_config import MarketplaceConfig
from models.public.user import User
from models.user.ebay_marketplace_settings import EbayMarketplaceSettings
from models.user.ebay_product import EbayProduct
from schemas.ebay_settings_schemas import (
    ApplyPolicyToOffersRequest,
    CreateFulfillmentPolicyRequest,
    CreatePaymentPolicyRequest,
    CreateReturnPolicyRequest,
    EbayMarketplaceSettingsResponse,
    EbayMarketplaceSettingsUpsert,
)
from services.ebay import (
    EbayAccountClient,
    EbayFulfillmentClient,
    EbayOfferClient,
    EbayPublicationError,
    EbayPublicationService,
    ProductValidationError,
)
from shared.exceptions import EbayAPIError

router = APIRouter(prefix="/ebay", tags=["eBay"])

# Include sub-routers
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
    Récupère le status de publication d'un produit sur eBay.

    Retourne une liste avec le statut de publication (ou vide si non publié).

    **Exemple:**
    ```bash
    curl "http://localhost:8000/api/ebay/products/12345/status" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```
    """
    # Find EbayProduct linked to this product_id
    ebay_product = (
        db.query(EbayProduct)
        .filter(EbayProduct.product_id == product_id)
        .first()
    )

    if not ebay_product or not ebay_product.sku_derived:
        return []

    return [
        ProductMarketplaceStatusResponse(
            sku_derived=ebay_product.sku_derived,
            product_id=ebay_product.product_id,
            marketplace_id=ebay_product.marketplace_id,
            status=ebay_product.status,
            ebay_offer_id=ebay_product.ebay_offer_id,
            ebay_listing_id=ebay_product.ebay_listing_id,
            error_message=ebay_product.error_message,
            published_at=ebay_product.published_at.isoformat() if ebay_product.published_at else None,
        )
    ]


@router.get("/policies", response_model=BusinessPoliciesResponse)
def get_business_policies(
    marketplace_id: str = "EBAY_FR",
    db_user: Tuple[Session, User] = Depends(get_user_db),
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
    db, current_user = db_user

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


# ========== CREATE POLICIES ==========


@router.post("/policies/payment", status_code=status.HTTP_201_CREATED)
def create_payment_policy(
    body: CreatePaymentPolicyRequest,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """Create a new eBay payment policy."""
    db, current_user = db_user

    try:
        client = EbayAccountClient(db, current_user.id, marketplace_id=body.marketplace_id)
        policy_data = {
            "name": body.name,
            "marketplaceId": body.marketplace_id,
            "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
            "immediatePay": body.immediate_pay,
        }
        return client.create_payment_policy(policy_data)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur création payment policy: {str(e)}",
        )


@router.post("/policies/fulfillment", status_code=status.HTTP_201_CREATED)
def create_fulfillment_policy(
    body: CreateFulfillmentPolicyRequest,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """Create a new eBay fulfillment (shipping) policy."""
    db, current_user = db_user

    try:
        client = EbayAccountClient(db, current_user.id, marketplace_id=body.marketplace_id)

        shipping_options = []
        for svc in body.shipping_services:
            shipping_service = {
                "shippingCarrierCode": svc.shipping_carrier_code,
                "shippingServiceCode": svc.shipping_service_code,
                "freeShipping": svc.free_shipping,
                "shippingCost": {
                    "value": str(svc.shipping_cost),
                    "currency": svc.currency,
                },
            }
            if svc.additional_cost is not None:
                shipping_service["additionalCost"] = {
                    "value": str(svc.additional_cost),
                    "currency": svc.currency,
                }
            shipping_options.append(
                {
                    "optionType": "DOMESTIC",
                    "shippingServices": [shipping_service],
                }
            )

        policy_data = {
            "name": body.name,
            "marketplaceId": body.marketplace_id,
            "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
            "handlingTime": {"value": body.handling_time_value, "unit": "DAY"},
            "shippingOptions": shipping_options,
        }
        return client.create_fulfillment_policy(policy_data)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur création fulfillment policy: {str(e)}",
        )


@router.post("/policies/return", status_code=status.HTTP_201_CREATED)
def create_return_policy(
    body: CreateReturnPolicyRequest,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """Create a new eBay return policy."""
    db, current_user = db_user

    try:
        client = EbayAccountClient(db, current_user.id, marketplace_id=body.marketplace_id)
        policy_data = {
            "name": body.name,
            "marketplaceId": body.marketplace_id,
            "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
            "returnsAccepted": body.returns_accepted,
            "returnPeriod": {"value": body.return_period_value, "unit": "DAY"},
            "refundMethod": body.refund_method,
            "returnShippingCostPayer": body.return_shipping_cost_payer,
        }
        return client.create_return_policy(policy_data)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur création return policy: {str(e)}",
        )


def _extract_ebay_error_detail(e: EbayAPIError, context: str) -> str:
    """Extract detailed error message from EbayAPIError response_body."""
    if e.response_body:
        errors = e.response_body.get("errors", [])
        if errors:
            parts = []
            for err in errors:
                msg = err.get("longMessage") or err.get("message", str(err))
                params = err.get("parameters")
                if params:
                    param_details = ", ".join(
                        f"{p.get('name', '?')}={p.get('value', '?')}" for p in params
                    )
                    msg = f"{msg} ({param_details})"
                parts.append(msg)
            return f"Erreur {context}: {'; '.join(parts)}"
    return f"Erreur {context}: {str(e)}"


# ========== DELETE POLICIES ==========


@router.delete("/policies/payment/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_policy(
    policy_id: str,
    marketplace_id: str = "EBAY_FR",
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """Delete an eBay payment policy."""
    db, current_user = db_user

    try:
        client = EbayAccountClient(db, current_user.id, marketplace_id=marketplace_id)
        client.delete_payment_policy(policy_id)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except EbayAPIError as e:
        detail = _extract_ebay_error_detail(e, "suppression payment policy")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur suppression payment policy: {str(e)}",
        )


@router.delete("/policies/fulfillment/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fulfillment_policy(
    policy_id: str,
    marketplace_id: str = "EBAY_FR",
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """Delete an eBay fulfillment (shipping) policy."""
    db, current_user = db_user

    try:
        client = EbayAccountClient(db, current_user.id, marketplace_id=marketplace_id)
        client.delete_fulfillment_policy(policy_id)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except EbayAPIError as e:
        detail = _extract_ebay_error_detail(e, "suppression fulfillment policy")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur suppression fulfillment policy: {str(e)}",
        )


@router.delete("/policies/return/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_return_policy(
    policy_id: str,
    marketplace_id: str = "EBAY_FR",
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """Delete an eBay return policy."""
    db, current_user = db_user

    try:
        client = EbayAccountClient(db, current_user.id, marketplace_id=marketplace_id)
        client.delete_return_policy(policy_id)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except EbayAPIError as e:
        detail = _extract_ebay_error_detail(e, "suppression return policy")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur suppression return policy: {str(e)}",
        )


# ========== UPDATE POLICIES ==========

# Fields from GET response that must not be sent back on PUT
_POLICY_READONLY_FIELDS = {
    "warnings", "errors",
}


def _prepare_policy_for_update(existing: dict, overrides: dict) -> dict:
    """Merge overrides into existing policy and strip read-only fields.

    Keeps all other fields (including categoryTypes) exactly as returned
    by the GET response to preserve eBay's expected format.
    """
    merged = {**existing, **overrides}
    for field in _POLICY_READONLY_FIELDS:
        merged.pop(field, None)
    return merged


@router.put("/policies/payment/{policy_id}")
def update_payment_policy(
    policy_id: str,
    body: CreatePaymentPolicyRequest,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """Update an existing eBay payment policy."""
    db, current_user = db_user

    try:
        client = EbayAccountClient(db, current_user.id, marketplace_id=body.marketplace_id)

        # GET existing then re-submit full object with overrides (eBay recommended approach)
        existing = client.get_payment_policy(policy_id)
        overrides = {
            "name": body.name,
            "immediatePay": body.immediate_pay,
        }
        policy_data = _prepare_policy_for_update(existing, overrides)
        return client.update_payment_policy(policy_id, policy_data)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except EbayAPIError as e:
        logger.error("eBay update payment policy error: %s", e.response_body)
        detail = _extract_ebay_error_detail(e, "modification payment policy")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur modification payment policy: {str(e)}",
        )


@router.put("/policies/fulfillment/{policy_id}")
def update_fulfillment_policy(
    policy_id: str,
    body: CreateFulfillmentPolicyRequest,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """Update an existing eBay fulfillment (shipping) policy."""
    db, current_user = db_user

    try:
        client = EbayAccountClient(db, current_user.id, marketplace_id=body.marketplace_id)

        shipping_options = []
        for svc in body.shipping_services:
            shipping_service = {
                "shippingCarrierCode": svc.shipping_carrier_code,
                "shippingServiceCode": svc.shipping_service_code,
                "freeShipping": svc.free_shipping,
                "shippingCost": {
                    "value": str(svc.shipping_cost),
                    "currency": svc.currency,
                },
            }
            if svc.additional_cost is not None:
                shipping_service["additionalCost"] = {
                    "value": str(svc.additional_cost),
                    "currency": svc.currency,
                }
            shipping_options.append(
                {
                    "optionType": "DOMESTIC",
                    "shippingServices": [shipping_service],
                }
            )

        # Fetch existing policy, then override only user-editable fields
        existing = client.get_fulfillment_policy(policy_id)
        overrides = {
            "name": body.name,
            "handlingTime": {"value": body.handling_time_value, "unit": "DAY"},
            "shippingOptions": shipping_options,
        }
        policy_data = _prepare_policy_for_update(existing, overrides)
        return client.update_fulfillment_policy(policy_id, policy_data)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except EbayAPIError as e:
        logger.error("eBay update fulfillment policy error: %s", e.response_body)
        detail = _extract_ebay_error_detail(e, "modification fulfillment policy")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur modification fulfillment policy: {str(e)}",
        )


@router.put("/policies/return/{policy_id}")
def update_return_policy(
    policy_id: str,
    body: CreateReturnPolicyRequest,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """Update an existing eBay return policy."""
    db, current_user = db_user

    try:
        client = EbayAccountClient(db, current_user.id, marketplace_id=body.marketplace_id)

        # Fetch existing policy, then override only user-editable fields
        existing = client.get_return_policy(policy_id)
        overrides = {
            "name": body.name,
            "returnsAccepted": body.returns_accepted,
            "returnPeriod": {"value": body.return_period_value, "unit": "DAY"},
            "refundMethod": body.refund_method,
            "returnShippingCostPayer": body.return_shipping_cost_payer,
        }
        policy_data = _prepare_policy_for_update(existing, overrides)
        return client.update_return_policy(policy_id, policy_data)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except EbayAPIError as e:
        logger.error("eBay update return policy error: %s", e.response_body)
        detail = _extract_ebay_error_detail(e, "modification return policy")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur modification return policy: {str(e)}",
        )


# ========== APPLY POLICY TO OFFERS ==========


# Read-only fields returned by eBay that must not be sent back on update
OFFER_READONLY_FIELDS = {"offerId", "status", "listing", "errors", "warnings"}

POLICY_TYPE_TO_FIELD = {
    "payment": "paymentPolicyId",
    "fulfillment": "fulfillmentPolicyId",
    "return": "returnPolicyId",
}

POLICY_TYPE_TO_SETTINGS_FIELD = {
    "payment": "payment_policy_id",
    "fulfillment": "fulfillment_policy_id",
    "return": "return_policy_id",
}


@router.post("/policies/apply-to-offers")
async def apply_policy_to_offers(
    body: ApplyPolicyToOffersRequest,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """
    Apply a policy to ALL existing eBay offers for a marketplace.

    Updates marketplace settings in DB synchronously, then launches a
    Temporal workflow to apply the policy to each offer asynchronously.
    Returns immediately with workflow/job info for progress tracking.
    """
    db, current_user = db_user

    if body.policy_type not in POLICY_TYPE_TO_FIELD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"policy_type must be one of: {list(POLICY_TYPE_TO_FIELD.keys())}",
        )

    policy_field = POLICY_TYPE_TO_FIELD[body.policy_type]
    settings_field = POLICY_TYPE_TO_SETTINGS_FIELD[body.policy_type]

    try:
        # 1. Update marketplace settings in DB (synchronous, fast)
        settings = (
            db.query(EbayMarketplaceSettings)
            .filter(EbayMarketplaceSettings.marketplace_id == body.marketplace_id)
            .first()
        )
        if not settings:
            settings = EbayMarketplaceSettings(marketplace_id=body.marketplace_id)
            db.add(settings)
        setattr(settings, settings_field, body.policy_id)
        db.flush()

        # 2. Get all offer IDs from our DB (products with an ebay_offer_id)
        ebay_products = (
            db.query(EbayProduct)
            .filter(
                EbayProduct.marketplace_id == body.marketplace_id,
                EbayProduct.ebay_offer_id.isnot(None),
                EbayProduct.status == "active",
            )
            .all()
        )

        offer_ids = [str(p.ebay_offer_id) for p in ebay_products]

        if not offer_ids:
            return {
                "status": "no_offers",
                "message": "Aucune annonce active trouvée pour cette marketplace",
                "settings_updated": True,
                "total_offers": 0,
            }

        db.commit()

        # 3. Start Temporal workflow
        from temporal.client import get_temporal_client
        from temporal.config import get_temporal_config
        from temporal.workflows.ebay.apply_policy_workflow import (
            ApplyPolicyParams,
            EbayApplyPolicyWorkflow,
        )

        config = get_temporal_config()

        if not config.temporal_enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Temporal is disabled",
            )

        client = await get_temporal_client()
        import time
        workflow_id = f"ebay-apply-policy-user-{current_user.id}-{int(time.time() * 1000)}"

        params = ApplyPolicyParams(
            user_id=current_user.id,
            marketplace_id=body.marketplace_id,
            policy_type=body.policy_type,
            policy_id=body.policy_id,
            policy_field=policy_field,
            offer_ids=offer_ids,
        )

        handle = await client.start_workflow(
            EbayApplyPolicyWorkflow.run,
            params,
            id=workflow_id,
            task_queue=config.temporal_task_queue,
        )

        logger.info(
            "Started apply_policy workflow: %s (user=%s, offers=%d)",
            workflow_id,
            current_user.id,
            len(offer_ids),
        )

        return {
            "status": "started",
            "workflow_id": workflow_id,
            "total_offers": len(offer_ids),
            "settings_updated": True,
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Failed to start apply_policy workflow: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur application policy: {str(e)}",
        )


# ========== MARKETPLACE SETTINGS ==========


@router.get(
    "/settings",
    response_model=List[EbayMarketplaceSettingsResponse],
    summary="List all marketplace settings",
)
def list_marketplace_settings(
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """Return all per-marketplace eBay settings for the current user."""
    db, current_user = db_user
    return (
        db.query(EbayMarketplaceSettings)
        .order_by(EbayMarketplaceSettings.marketplace_id)
        .all()
    )


@router.get(
    "/settings/{marketplace_id}",
    response_model=EbayMarketplaceSettingsResponse,
    summary="Get settings for one marketplace",
)
def get_marketplace_settings(
    marketplace_id: str,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """Return eBay settings for a specific marketplace."""
    db, current_user = db_user
    settings = (
        db.query(EbayMarketplaceSettings)
        .filter(EbayMarketplaceSettings.marketplace_id == marketplace_id)
        .first()
    )
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No settings found for marketplace {marketplace_id}",
        )
    return settings


@router.put(
    "/settings/{marketplace_id}",
    response_model=EbayMarketplaceSettingsResponse,
    summary="Create or update marketplace settings",
)
def upsert_marketplace_settings(
    marketplace_id: str,
    body: EbayMarketplaceSettingsUpsert,
    db_user: Tuple[Session, User] = Depends(get_user_db),
):
    """Create or update eBay settings for a specific marketplace (upsert)."""
    db, current_user = db_user
    settings = (
        db.query(EbayMarketplaceSettings)
        .filter(EbayMarketplaceSettings.marketplace_id == marketplace_id)
        .first()
    )

    if not settings:
        settings = EbayMarketplaceSettings(marketplace_id=marketplace_id)
        db.add(settings)

    # Apply only provided fields
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)

    db.flush()
    db.refresh(settings)
    return settings
