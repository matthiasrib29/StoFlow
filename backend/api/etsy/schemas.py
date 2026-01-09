"""
Etsy API Pydantic Schemas

Schemas for request/response validation.

Author: Claude
Date: 2025-12-17
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class EtsyConnectionStatusResponse(BaseModel):
    """Status de la connexion Etsy."""

    connected: bool
    shop_id: Optional[str] = None
    shop_name: Optional[str] = None
    access_token_expires_at: Optional[str] = None
    refresh_token_expires_at: Optional[str] = None


class PublishProductRequest(BaseModel):
    """Request pour publier un produit sur Etsy."""

    product_id: int = Field(..., description="ID du produit a publier")
    taxonomy_id: int = Field(..., description="Etsy taxonomy ID (category)")
    shipping_profile_id: Optional[int] = Field(None, description="Shipping profile ID")
    return_policy_id: Optional[int] = Field(None, description="Return policy ID")
    shop_section_id: Optional[int] = Field(None, description="Shop section ID")
    state: str = Field("draft", description="Etat du listing (draft ou active)")


class PublishProductResponse(BaseModel):
    """Response apres publication d'un produit."""

    success: bool
    listing_id: Optional[int] = None
    listing_url: Optional[str] = None
    state: Optional[str] = None
    error: Optional[str] = None


class UpdateListingRequest(BaseModel):
    """Request pour mettre a jour un listing Etsy."""

    product_id: int = Field(..., description="ID du produit Stoflow")


class ListingResponse(BaseModel):
    """Response pour un listing Etsy."""

    listing_id: int
    title: str
    state: str
    price: float
    quantity: int
    url: Optional[str] = None
    created_timestamp: Optional[int] = None
    updated_timestamp: Optional[int] = None


class ShopResponse(BaseModel):
    """Response pour les infos du shop Etsy."""

    shop_id: int
    shop_name: str
    title: Optional[str] = None
    url: str
    listing_active_count: int
    currency_code: str


class ShopSectionResponse(BaseModel):
    """Response pour une section de shop."""

    shop_section_id: int
    title: str
    rank: int
    active_listing_count: int


class ReceiptResponse(BaseModel):
    """Response pour un receipt (order) Etsy."""

    receipt_id: int
    receipt_type: int
    buyer_user_id: int
    buyer_email: str
    name: str
    first_line: str
    city: str
    state: Optional[str] = None
    zip: str
    status: str
    formatted_address: str
    country_iso: str
    payment_method: str
    payment_email: str
    message_from_seller: Optional[str] = None
    message_from_buyer: Optional[str] = None
    message_from_payment: Optional[str] = None
    is_paid: bool
    is_shipped: bool
    create_timestamp: int
    created_timestamp: int
    update_timestamp: int
    updated_timestamp: int
    grandtotal: dict
    subtotal: dict
    total_price: dict
    total_shipping_cost: dict
    total_tax_cost: dict
    total_vat_cost: dict
    discount_amt: dict
    gift_message: Optional[str] = None
    shipments: List[dict] = []
    transactions: List[dict] = []


class ShippingProfileResponse(BaseModel):
    """Response pour un shipping profile."""

    shipping_profile_id: int
    title: str
    user_id: int
    min_processing_days: int
    max_processing_days: int
    processing_days_display_label: str
    origin_country_iso: str


class TaxonomyNodeResponse(BaseModel):
    """Response pour un taxonomy node (categorie)."""

    id: int
    level: int
    name: str
    parent_id: Optional[int] = None
    children: List[int] = []
    full_path_taxonomy_ids: List[int] = []


class PollingResultsResponse(BaseModel):
    """Response pour les resultats de polling."""

    timestamp: str
    new_orders_count: int
    updated_listings_count: int
    low_stock_count: int
    new_orders: List[dict] = []
    updated_listings: List[dict] = []
    low_stock_listings: List[dict] = []
