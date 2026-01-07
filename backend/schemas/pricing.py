"""
Pricing Schemas

Pydantic schemas for the public pricing endpoint.
Used to display subscription plans on the landing page.

Author: Claude
Date: 2024-12-24
"""

from pydantic import BaseModel, ConfigDict


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
