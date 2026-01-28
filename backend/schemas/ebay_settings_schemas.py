"""
eBay Marketplace Settings Pydantic Schemas

Request/Response schemas for per-marketplace eBay configuration endpoints.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class EbayMarketplaceSettingsResponse(BaseModel):
    """Response schema for ebay_marketplace_settings."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    marketplace_id: str
    payment_policy_id: Optional[str] = None
    fulfillment_policy_id: Optional[str] = None
    return_policy_id: Optional[str] = None
    inventory_location_key: Optional[str] = None
    price_coefficient: Decimal = Decimal("1.00")
    price_fee: Decimal = Decimal("0.00")
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class EbayMarketplaceSettingsUpsert(BaseModel):
    """Upsert schema for ebay_marketplace_settings (create or update)."""

    payment_policy_id: Optional[str] = Field(None, max_length=50)
    fulfillment_policy_id: Optional[str] = Field(None, max_length=50)
    return_policy_id: Optional[str] = Field(None, max_length=50)
    inventory_location_key: Optional[str] = Field(None, max_length=50)
    price_coefficient: Optional[Decimal] = Field(None, ge=0, le=999.99)
    price_fee: Optional[Decimal] = Field(None, ge=0, le=99999999.99)
    is_active: Optional[bool] = None


# ========== CREATE POLICY SCHEMAS ==========


class CreatePaymentPolicyRequest(BaseModel):
    """Request schema for creating an eBay payment policy."""

    name: str = Field(..., min_length=1, max_length=64)
    marketplace_id: str = Field(..., description="eBay marketplace ID (e.g. EBAY_FR)")
    immediate_pay: bool = Field(True, description="Require immediate payment")


class ShippingServiceRequest(BaseModel):
    """Shipping service configuration for fulfillment policy."""

    shipping_carrier_code: str = Field(..., description="e.g. Colissimo")
    shipping_service_code: str = Field(..., description="e.g. FR_ColiPoste")
    shipping_cost: Decimal = Field(..., ge=0, description="Shipping cost")
    currency: str = Field("EUR", max_length=3)
    free_shipping: bool = False
    additional_cost: Optional[Decimal] = Field(None, ge=0)


class CreateFulfillmentPolicyRequest(BaseModel):
    """Request schema for creating an eBay fulfillment policy."""

    name: str = Field(..., min_length=1, max_length=64)
    marketplace_id: str = Field(..., description="eBay marketplace ID (e.g. EBAY_FR)")
    handling_time_value: int = Field(2, ge=0, le=30, description="Handling time in days")
    shipping_services: List[ShippingServiceRequest] = Field(
        ..., min_length=1, description="At least one shipping service required"
    )


class CreateReturnPolicyRequest(BaseModel):
    """Request schema for creating an eBay return policy."""

    name: str = Field(..., min_length=1, max_length=64)
    marketplace_id: str = Field(..., description="eBay marketplace ID (e.g. EBAY_FR)")
    returns_accepted: bool = Field(True, description="Whether returns are accepted")
    return_period_value: int = Field(
        30, ge=0, le=60, description="Return period in days"
    )
    refund_method: str = Field(
        "MONEY_BACK", description="MONEY_BACK or MERCHANDISE_CREDIT"
    )
    return_shipping_cost_payer: str = Field(
        "BUYER", description="BUYER or SELLER"
    )


# ========== APPLY POLICY SCHEMAS ==========


class ApplyPolicyToOffersRequest(BaseModel):
    """Request to apply a policy to all existing eBay offers."""

    policy_type: str = Field(
        ..., description="Type: payment, fulfillment, or return"
    )
    policy_id: str = Field(..., description="eBay policy ID to apply")
    marketplace_id: str = Field(
        "EBAY_FR", description="Target marketplace"
    )
