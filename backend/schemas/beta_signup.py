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
    product_count: str = Field(
        ...,
        description="Number of products range"
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

    @field_validator('product_count')
    @classmethod
    def validate_product_count(cls, v: str) -> str:
        """Validate product_count is one of the allowed values."""
        allowed = ['0-100', '100-1000', '1000+']
        if v not in allowed:
            raise ValueError(f'product_count must be one of {allowed}')
        return v


class BetaSignupResponse(BaseModel):
    """Schema for beta signup response."""

    id: int
    email: str
    name: str
    vendor_type: str
    product_count: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_db(cls, db_obj):
        """Create response from DB object, mapping monthly_volume to product_count."""
        return cls(
            id=db_obj.id,
            email=db_obj.email,
            name=db_obj.name or "",
            vendor_type=db_obj.vendor_type or "",
            product_count=db_obj.monthly_volume or "",
            status=db_obj.status.value if hasattr(db_obj.status, 'value') else db_obj.status,
            created_at=db_obj.created_at
        )
