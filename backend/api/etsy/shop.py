"""
Etsy Shop, Orders & Shipping Routes

Endpoints for shop management, orders/receipts, and shipping profiles.

Author: Claude
Date: 2025-12-17
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from models.public.user import User
from services.etsy import (
    EtsyReceiptClient,
    EtsyShippingClient,
    EtsyShopClient,
)
from shared.logging_setup import get_logger

from .schemas import (
    ReceiptResponse,
    ShippingProfileResponse,
    ShopResponse,
    ShopSectionResponse,
)

router = APIRouter()
logger = get_logger(__name__)


# ========== SHOP MANAGEMENT ==========


@router.get("/shop", response_model=ShopResponse)
def get_shop_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recupere les informations du shop Etsy.
    """
    try:
        client = EtsyShopClient(db, current_user.id)
        shop = client.get_shop()

        return ShopResponse(
            shop_id=shop["shop_id"],
            shop_name=shop["shop_name"],
            title=shop.get("title"),
            url=shop["url"],
            listing_active_count=shop["listing_active_count"],
            currency_code=shop["currency_code"],
        )

    except Exception as e:
        logger.error(f"Error getting shop info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting shop: {str(e)}",
        )


@router.get("/shop/sections", response_model=List[ShopSectionResponse])
def get_shop_sections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recupere les sections du shop Etsy.
    """
    try:
        client = EtsyShopClient(db, current_user.id)
        sections = client.get_shop_sections()

        return [
            ShopSectionResponse(
                shop_section_id=section["shop_section_id"],
                title=section["title"],
                rank=section["rank"],
                active_listing_count=section["active_listing_count"],
            )
            for section in sections
        ]

    except Exception as e:
        logger.error(f"Error getting shop sections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting sections: {str(e)}",
        )


# ========== ORDERS (RECEIPTS) ==========


@router.get("/orders", response_model=List[ReceiptResponse])
def get_shop_orders(
    status_filter: Optional[str] = Query(
        None, description="Status filter (open, completed, canceled)"
    ),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recupere les commandes (receipts) du shop Etsy.
    """
    try:
        client = EtsyReceiptClient(db, current_user.id)
        result = client.get_shop_receipts(
            status=status_filter,
            limit=limit,
            offset=offset,
        )

        receipts = result.get("results", [])

        return receipts

    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting orders: {str(e)}",
        )


@router.get("/orders/{receipt_id}")
def get_order_details(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recupere les details d'une commande Etsy.
    """
    try:
        client = EtsyReceiptClient(db, current_user.id)
        receipt = client.get_shop_receipt(receipt_id)

        return receipt

    except Exception as e:
        logger.error(f"Error getting order {receipt_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting order: {str(e)}",
        )


# ========== SHIPPING ==========


@router.get("/shipping/profiles", response_model=List[ShippingProfileResponse])
def get_shipping_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recupere les shipping profiles du shop.
    """
    try:
        client = EtsyShippingClient(db, current_user.id)
        profiles = client.get_shop_shipping_profiles()

        return [
            ShippingProfileResponse(
                shipping_profile_id=profile["shipping_profile_id"],
                title=profile["title"],
                user_id=profile["user_id"],
                min_processing_days=profile["min_processing_days"],
                max_processing_days=profile["max_processing_days"],
                processing_days_display_label=profile["processing_days_display_label"],
                origin_country_iso=profile["origin_country_iso"],
            )
            for profile in profiles
        ]

    except Exception as e:
        logger.error(f"Error getting shipping profiles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting shipping profiles: {str(e)}",
        )
