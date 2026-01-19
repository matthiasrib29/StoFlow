"""
eBay Pydantic Schemas

Request/Response schemas for eBay API endpoints.

Business Rules:
- All prices in EUR (base currency)
- Marketplace-specific pricing via coefficients + fees
- User-specific settings (credentials, policies, pricing)
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# PUBLISH / UNPUBLISH
# ============================================================================


class EbayPublishRequest(BaseModel):
    """Request to publish product on eBay."""

    sku: int = Field(..., description="Product SKU")
    marketplace_ids: Optional[List[str]] = Field(
        None,
        description="Target marketplaces (EBAY_FR, EBAY_GB, etc.). If None, publish to all active.",
    )


class EbayUnpublishRequest(BaseModel):
    """Request to unpublish product from eBay."""

    sku: int = Field(..., description="Product SKU")
    marketplace_ids: Optional[List[str]] = Field(
        None,
        description="Marketplaces to unpublish from. If None, unpublish from all.",
    )


# ============================================================================
# PRODUCT MARKETPLACE
# ============================================================================


class EbayProductMarketplaceResponse(BaseModel):
    """eBay product marketplace status."""

    sku_derived: str
    product_id: int
    marketplace_id: str
    status: str
    ebay_listing_id: Optional[int]
    ebay_offer_id: Optional[int]
    error_message: Optional[str]
    published_at: Optional[datetime]
    sold_at: Optional[datetime]
    last_sync_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SETTINGS
# ============================================================================


class EbaySettingsResponse(BaseModel):
    """User eBay settings (read)."""

    # OAuth Credentials
    has_credentials: bool = Field(..., description="Whether user has connected eBay account")

    # Business Policies
    payment_policy_id: Optional[int]
    fulfillment_policy_id: Optional[int]
    return_policy_id: Optional[int]
    inventory_location: Optional[str]

    # Pricing Coefficients (8 marketplaces)
    price_coefficient_fr: Decimal
    price_coefficient_gb: Decimal
    price_coefficient_de: Decimal
    price_coefficient_it: Decimal
    price_coefficient_es: Decimal
    price_coefficient_nl: Decimal
    price_coefficient_be: Decimal
    price_coefficient_pl: Decimal

    # Pricing Fees (8 marketplaces)
    price_fee_fr: Decimal
    price_fee_gb: Decimal
    price_fee_de: Decimal
    price_fee_it: Decimal
    price_fee_es: Decimal
    price_fee_nl: Decimal
    price_fee_be: Decimal
    price_fee_pl: Decimal

    # Best Offer
    best_offer_enabled: bool
    best_offer_auto_accept_pct: Decimal
    best_offer_auto_decline_pct: Decimal

    # Promoted Listings
    promoted_listings_enabled: bool
    promoted_listings_bid_pct: Decimal

    model_config = ConfigDict(from_attributes=True)


class EbaySettingsUpdate(BaseModel):
    """User eBay settings (write)."""

    # Business Policies
    payment_policy_id: Optional[int] = None
    fulfillment_policy_id: Optional[int] = None
    return_policy_id: Optional[int] = None
    inventory_location: Optional[str] = None

    # Pricing Coefficients
    price_coefficient_fr: Optional[Decimal] = None
    price_coefficient_gb: Optional[Decimal] = None
    price_coefficient_de: Optional[Decimal] = None
    price_coefficient_it: Optional[Decimal] = None
    price_coefficient_es: Optional[Decimal] = None
    price_coefficient_nl: Optional[Decimal] = None
    price_coefficient_be: Optional[Decimal] = None
    price_coefficient_pl: Optional[Decimal] = None

    # Pricing Fees
    price_fee_fr: Optional[Decimal] = None
    price_fee_gb: Optional[Decimal] = None
    price_fee_de: Optional[Decimal] = None
    price_fee_it: Optional[Decimal] = None
    price_fee_es: Optional[Decimal] = None
    price_fee_nl: Optional[Decimal] = None
    price_fee_be: Optional[Decimal] = None
    price_fee_pl: Optional[Decimal] = None

    # Best Offer
    best_offer_enabled: Optional[bool] = None
    best_offer_auto_accept_pct: Optional[Decimal] = None
    best_offer_auto_decline_pct: Optional[Decimal] = None

    # Promoted Listings
    promoted_listings_enabled: Optional[bool] = None
    promoted_listings_bid_pct: Optional[Decimal] = None


# ============================================================================
# MARKETPLACE INFO
# ============================================================================


class EbayMarketplaceInfo(BaseModel):
    """eBay marketplace information."""

    marketplace_id: str
    country_code: str
    site_id: int
    currency: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PROMOTED LISTINGS
# ============================================================================


class EbayPromotedListingResponse(BaseModel):
    """eBay promoted listing info."""

    id: int
    campaign_id: str
    campaign_name: Optional[str]
    marketplace_id: str
    product_id: int
    sku_derived: str
    ad_id: str
    bid_percentage: Decimal
    ad_status: str
    total_clicks: int
    total_impressions: int
    total_sales: int
    total_sales_amount: Decimal
    total_ad_fees: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ORDERS
# ============================================================================


class EbayOrderProductResponse(BaseModel):
    """eBay order line item."""

    id: int
    order_id: str
    line_item_id: Optional[str]
    sku: Optional[str]
    sku_original: Optional[str]
    title: Optional[str]
    quantity: Optional[int]
    unit_price: Optional[float]
    total_price: Optional[float]
    currency: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class EbayOrderResponse(BaseModel):
    """eBay order info."""

    id: int
    order_id: str
    marketplace_id: Optional[str]
    buyer_username: Optional[str]
    buyer_email: Optional[str]
    shipping_name: Optional[str]
    shipping_address: Optional[str]
    shipping_city: Optional[str]
    shipping_postal_code: Optional[str]
    shipping_country: Optional[str]
    total_price: Optional[float]
    currency: Optional[str]
    shipping_cost: Optional[float]
    order_fulfillment_status: Optional[str]
    order_payment_status: Optional[str]
    creation_date: Optional[datetime]
    paid_date: Optional[datetime]
    tracking_number: Optional[str]
    shipping_carrier: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# OAUTH
# ============================================================================


class EbayOAuthConnectRequest(BaseModel):
    """Request to initiate eBay OAuth flow."""

    redirect_uri: str = Field(..., description="OAuth redirect URI")


class EbayOAuthCallbackRequest(BaseModel):
    """OAuth callback data."""

    code: str = Field(..., description="Authorization code from eBay")
    state: Optional[str] = Field(None, description="State parameter for CSRF protection")


# ============================================================================
# LINK / UNLINK (Product Linking)
# ============================================================================


class EbayLinkRequest(BaseModel):
    """Request to link an EbayProduct to a Product."""

    product_id: Optional[int] = Field(
        None,
        description="ID of existing Product to link. If None, creates a new Product from eBay data."
    )

    # Optional overrides when creating new Product (ignored if product_id is set)
    title: Optional[str] = Field(None, description="Override title for new Product")
    description: Optional[str] = Field(None, description="Override description for new Product")
    price: Optional[float] = Field(None, description="Override price for new Product")
    category: Optional[str] = Field(None, description="Override category for new Product")
    brand: Optional[str] = Field(None, description="Override brand for new Product")


class EbayLinkResponse(BaseModel):
    """Response for link/create operation."""

    success: bool = Field(..., description="Operation success")
    ebay_product_id: int = Field(..., description="eBay product internal ID")
    product_id: int = Field(..., description="Stoflow Product ID")
    created: bool = Field(..., description="True if new Product created, False if linked to existing")
    images_copied: Optional[int] = Field(None, description="Number of images copied (if created)")
    product: Optional[dict] = Field(None, description="Created Product details (if created)")


class EbayUnlinkResponse(BaseModel):
    """Response for unlink operation."""

    success: bool = Field(..., description="Operation success")
    ebay_product_id: int = Field(..., description="eBay product internal ID")
