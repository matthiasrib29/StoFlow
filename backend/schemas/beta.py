"""
Pydantic schemas for beta signup endpoints.
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class BetaSignupCreate(BaseModel):
    """Schema for creating a new beta signup."""

    email: EmailStr = Field(..., description="Email address for beta access")
    first_name: str | None = Field(None, max_length=100, description="First name (optional)")
    vendor_type: Literal["particular", "semi-pro", "pro"] | None = Field(
        None, description="Type of vendor"
    )
    monthly_volume: Literal["<10", "10-50", "50-200", "200+"] | None = Field(
        None, description="Monthly volume of products"
    )


class BetaSignupResponse(BaseModel):
    """Schema for beta signup response."""

    model_config = {"from_attributes": True}

    id: int
    email: str
    first_name: str | None
    vendor_type: str | None
    monthly_volume: str | None
    status: str
    created_at: datetime


class BetaSignupSuccessMessage(BaseModel):
    """Schema for successful signup message."""

    success: bool = True
    message: str = "Inscription réussie ! Vérifiez votre email."
    data: BetaSignupResponse


class BetaSignupErrorMessage(BaseModel):
    """Schema for error message."""

    success: bool = False
    message: str
    detail: str | None = None
