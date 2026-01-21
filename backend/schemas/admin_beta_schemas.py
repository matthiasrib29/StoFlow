"""
Admin Beta Schemas - Pydantic models for beta management endpoints

These schemas define the request/response models for the admin beta management API.

Author: Claude
Date: 2026-01-20
"""

from datetime import datetime
from pydantic import BaseModel, Field


class RevokeDiscountRequest(BaseModel):
    """Request to revoke a beta tester's discount."""
    reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Reason for revoking the discount (min 10 characters)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "reason": "User requested removal of beta status for billing reasons"
            }
        }
    }


class BetaSignupListItem(BaseModel):
    """Beta signup item in list response."""
    id: int
    email: str
    name: str | None
    vendor_type: str | None
    monthly_volume: str | None
    status: str
    user_id: int | None
    discount_applied_at: datetime | None
    discount_revoked_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class BetaSignupDetailResponse(BaseModel):
    """Detailed beta signup response with related user info."""
    id: int
    email: str
    name: str | None
    vendor_type: str | None
    monthly_volume: str | None
    status: str
    user_id: int | None
    user_email: str | None = None
    user_username: str | None = None
    discount_applied_at: datetime | None
    discount_revoked_at: datetime | None
    revoked_by_username: str | None = None
    revocation_reason: str | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class BetaSignupListResponse(BaseModel):
    """Paginated list of beta signups."""
    items: list[BetaSignupListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class BetaStatsResponse(BaseModel):
    """Statistics about the beta program."""
    total_signups: int = Field(..., description="Total number of beta signups")
    pending: int = Field(..., description="Signups awaiting conversion")
    converted: int = Field(..., description="Signups that converted to paid users")
    revoked: int = Field(..., description="Signups with revoked discount")
    cancelled: int = Field(..., description="Signups that cancelled")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_signups": 150,
                "pending": 100,
                "converted": 40,
                "revoked": 5,
                "cancelled": 5
            }
        }
    }


class RevokeDiscountResponse(BaseModel):
    """Response after revoking a discount."""
    success: bool
    message: str
    beta_signup_id: int
    revoked_at: datetime
