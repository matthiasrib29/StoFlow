"""
Beta signup schemas.

Pydantic models for beta signup validation and serialization.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator


class BetaSignupCreate(BaseModel):
    """Schema for creating a beta signup."""

    email: EmailStr = Field(..., description="Email address")
    name: str = Field(..., min_length=1, max_length=255, description="Full name")
    vendor_type: str = Field(
        ...,
        description="Type of vendor (particulier or professionnel)"
    )
    monthly_volume: str = Field(
        ...,
        description="Monthly sales volume range"
    )
    # Honeypot field: invisible to users, bots fill it
    # Security Fix 2026-01-20: Anti-spam protection
    website: str | None = Field(
        default=None,
        max_length=255,
        description="Honeypot field - should remain empty"
    )

    @field_validator('vendor_type')
    @classmethod
    def validate_vendor_type(cls, v: str) -> str:
        """Validate vendor_type is one of the allowed values."""
        allowed = ['particulier', 'professionnel']
        if v not in allowed:
            raise ValueError(f'vendor_type must be one of {allowed}')
        return v

    @field_validator('monthly_volume')
    @classmethod
    def validate_monthly_volume(cls, v: str) -> str:
        """Validate monthly_volume is one of the allowed values."""
        allowed = ['0-10', '10-50', '50+']
        if v not in allowed:
            raise ValueError(f'monthly_volume must be one of {allowed}')
        return v


class BetaSignupResponse(BaseModel):
    """Schema for beta signup response."""

    id: int
    email: str
    name: str
    vendor_type: str
    monthly_volume: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
