"""
Pricing Schemas

Pydantic schemas for the pricing algorithm API.
Input/output validation for price calculation requests.

Architecture:
- PriceInput: Request schema with all product attributes and adjustment inputs
- AdjustmentBreakdown: Detailed breakdown of all 6 adjustment components
- PriceOutput: Response schema with 3 price levels and full breakdown

Created: 2026-01-12
Author: Claude
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PriceInput(BaseModel):
    """
    Input schema for price calculation request.

    Contains all product attributes and adjustment parameters needed
    for the pricing algorithm to calculate prices.
    """

    # Product attributes
    brand: str = Field(..., description="Brand name (e.g., 'Nike', 'Levi\\'s')")
    category: str = Field(..., description="Product category (e.g., 'sneakers', 'jeans')")
    materials: list[str] = Field(..., description="List of materials (e.g., ['leather', 'cotton'])")
    model_name: Optional[str] = Field(None, description="Model name (e.g., 'Air Max 90', '501')")

    # Adjustment inputs
    condition_score: int = Field(..., ge=0, le=5, description="Condition score (0-5, where 3 is baseline)")
    supplements: list[str] = Field(
        default_factory=list,
        description="List of supplement keys (e.g., ['original_box', 'tags'])"
    )
    condition_sensitivity: Decimal = Field(
        ...,
        ge=Decimal("0.5"),
        le=Decimal("1.5"),
        description="Condition sensitivity multiplier (0.5-1.5)"
    )

    actual_origin: str = Field(..., description="Actual product origin country")
    expected_origins: list[str] = Field(
        default_factory=list,
        description="Expected origin countries for this product group"
    )

    actual_decade: str = Field(..., description="Actual product decade (e.g., '1990s', '2010s')")
    expected_decades: list[str] = Field(
        default_factory=list,
        description="Expected decades for this product group"
    )

    actual_trends: list[str] = Field(
        default_factory=list,
        description="Actual product trends (e.g., ['y2k', 'vintage'])"
    )
    expected_trends: list[str] = Field(
        default_factory=list,
        description="Expected trends for this product group"
    )

    actual_features: list[str] = Field(
        default_factory=list,
        description="Actual product features (e.g., ['deadstock', 'selvedge'])"
    )
    expected_features: list[str] = Field(
        default_factory=list,
        description="Expected features for this product group"
    )

    model_config = ConfigDict(from_attributes=True)


class AdjustmentBreakdown(BaseModel):
    """
    Breakdown of all adjustment components.

    Shows the individual contribution of each adjustment calculator
    for transparency and debugging.
    """

    condition: Decimal = Field(..., description="Condition adjustment (±0.30)")
    origin: Decimal = Field(..., description="Origin adjustment (-0.10 to +0.15)")
    decade: Decimal = Field(..., description="Decade adjustment (0.00 to +0.20)")
    trend: Decimal = Field(..., description="Trend adjustment (0.00 to +0.20)")
    feature: Decimal = Field(..., description="Feature adjustment (0.00 to +0.30)")
    total: Decimal = Field(..., description="Sum of all adjustments")

    model_config = ConfigDict(from_attributes=True)


class PriceOutput(BaseModel):
    """
    Output schema for price calculation response.

    Contains 3 price levels, calculation breakdown, and metadata.
    """

    # Price levels
    quick_price: Decimal = Field(..., description="Quick sale price (×0.75)")
    standard_price: Decimal = Field(..., description="Standard price (×1.0)")
    premium_price: Decimal = Field(..., description="Premium price (×1.30)")

    # Calculation breakdown
    base_price: Decimal = Field(..., description="Base price from BrandGroup")
    model_coefficient: Decimal = Field(..., description="Model coefficient (0.5-3.0)")
    adjustments: AdjustmentBreakdown = Field(..., description="Detailed adjustment breakdown")

    # Metadata
    brand: str = Field(..., description="Brand name")
    group: str = Field(..., description="Pricing group")
    model_name: Optional[str] = Field(None, description="Model name if provided")

    model_config = ConfigDict(from_attributes=True)
