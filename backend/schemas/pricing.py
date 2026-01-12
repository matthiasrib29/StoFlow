"""
Pricing Schemas

Pydantic schemas for the public pricing endpoint.
Used to display subscription plans on the landing page.

Author: Claude
Date: 2024-12-24
Updated: 2026-01-12 - Added PriceInput, PriceOutput, AdjustmentBreakdown
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ===== Pricing Algorithm Schemas =====


class PriceInput(BaseModel):
    """Input data for price calculation."""

    # Product identification
    brand: str = Field(..., description="Brand name")
    category: str = Field(..., description="Product category")
    materials: list[str] = Field(default_factory=list, description="List of materials")
    model_name: Optional[str] = Field(None, description="Optional model name")

    # Condition parameters
    condition_score: int = Field(default=3, ge=1, le=5, description="Condition score 1-5")
    supplements: list[str] = Field(default_factory=list, description="Supplements/accessories")
    condition_sensitivity: Decimal = Field(default=Decimal("1.0"), description="Condition sensitivity factor")

    # Origin parameters
    actual_origin: Optional[str] = Field(None, description="Actual country of origin")
    expected_origins: list[str] = Field(default_factory=list, description="Expected origins for this brand")

    # Decade parameters
    actual_decade: Optional[str] = Field(None, description="Actual decade (e.g., '1990s')")
    expected_decades: list[str] = Field(default_factory=list, description="Expected decades for this model")

    # Trend parameters
    actual_trends: list[str] = Field(default_factory=list, description="Actual trends/styles")
    expected_trends: list[str] = Field(default_factory=list, description="Expected trends for category")

    # Feature parameters
    actual_features: list[str] = Field(default_factory=list, description="Actual features")
    expected_features: list[str] = Field(default_factory=list, description="Expected features for model")

    model_config = ConfigDict(from_attributes=True)


class AdjustmentBreakdown(BaseModel):
    """Breakdown of all price adjustments."""

    condition: Decimal = Field(default=Decimal("0"), description="Condition adjustment")
    origin: Decimal = Field(default=Decimal("0"), description="Origin adjustment")
    decade: Decimal = Field(default=Decimal("0"), description="Decade adjustment")
    trend: Decimal = Field(default=Decimal("0"), description="Trend adjustment")
    feature: Decimal = Field(default=Decimal("0"), description="Feature adjustment")
    total: Decimal = Field(default=Decimal("0"), description="Total adjustment")

    model_config = ConfigDict(from_attributes=True)


class PriceOutput(BaseModel):
    """Output data from price calculation."""

    # Price levels
    quick_price: Decimal = Field(..., description="Quick sale price (75% of standard)")
    standard_price: Decimal = Field(..., description="Standard price")
    premium_price: Decimal = Field(..., description="Premium price (130% of standard)")

    # Breakdown
    base_price: Decimal = Field(..., description="Base price from brand group")
    model_coefficient: Decimal = Field(..., description="Model coefficient multiplier")
    adjustments: AdjustmentBreakdown = Field(..., description="Detailed adjustment breakdown")

    # Metadata
    brand: str = Field(..., description="Brand name")
    group: str = Field(..., description="Determined group (sneakers, bags, etc.)")
    model_name: Optional[str] = Field(None, description="Model name if provided")

    model_config = ConfigDict(from_attributes=True)


# ===== Subscription Pricing Schemas =====


class PricingFeatureResponse(BaseModel):
    """Feature displayed for a pricing plan."""
    feature_text: str
    display_order: int

    model_config = ConfigDict(from_attributes=True)


class PricingPlanResponse(BaseModel):
    """Subscription plan for pricing page display."""
    tier: str
    display_name: str
    description: str | None
    price: int  # Integer price (e.g., 19, not 19.99)
    annual_discount_percent: int
    is_popular: bool
    cta_text: str | None
    display_order: int
    max_products: int
    max_platforms: int
    ai_credits_monthly: int
    features: list[PricingFeatureResponse]

    model_config = ConfigDict(from_attributes=True)
