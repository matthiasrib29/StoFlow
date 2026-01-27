"""
eBay Marketplace Settings Pydantic Schemas

Request/Response schemas for per-marketplace eBay configuration endpoints.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

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
