"""
Admin Schemas

Pydantic schemas for admin user management operations.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, field_validator


class AdminUserBase(BaseModel):
    """Base schema for user data."""

    email: EmailStr = Field(..., description="User email (globally unique)")
    full_name: str = Field(..., min_length=1, max_length=255, description="User's full name")
    role: str = Field(default="user", description="User role: 'admin', 'user', or 'support'")
    is_active: bool = Field(default=True, description="Whether the user account is active")
    subscription_tier: str = Field(default="free", description="Subscription tier")
    business_name: Optional[str] = Field(None, max_length=255, description="Business name")

    @field_validator('role')
    @classmethod
    def validate_role(cls, value: str) -> str:
        """Validate role is one of the allowed values."""
        valid_roles = ['admin', 'user', 'support']
        if value.lower() not in valid_roles:
            raise ValueError(f"role must be one of: {', '.join(valid_roles)}")
        return value.lower()

    @field_validator('subscription_tier')
    @classmethod
    def validate_subscription_tier(cls, value: str) -> str:
        """Validate subscription_tier is one of the allowed values."""
        valid_tiers = ['free', 'starter', 'pro', 'enterprise']
        if value.lower() not in valid_tiers:
            raise ValueError(f"subscription_tier must be one of: {', '.join(valid_tiers)}")
        return value.lower()


class AdminUserCreate(AdminUserBase):
    """Schema for creating a new user (admin)."""

    password: str = Field(
        ...,
        min_length=8,
        description="User password (min 8 characters)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "full_name": "John Doe",
                "role": "user",
                "is_active": True,
                "subscription_tier": "free",
                "business_name": "John's Shop"
            }
        }
    }


class AdminUserUpdate(BaseModel):
    """Schema for updating a user (admin). All fields optional."""

    email: Optional[EmailStr] = Field(None, description="New email")
    full_name: Optional[str] = Field(None, min_length=1, max_length=255, description="New full name")
    role: Optional[str] = Field(None, description="New role: 'admin', 'user', or 'support'")
    is_active: Optional[bool] = Field(None, description="New active status")
    subscription_tier: Optional[str] = Field(None, description="New subscription tier")
    business_name: Optional[str] = Field(None, max_length=255, description="New business name")
    password: Optional[str] = Field(None, min_length=8, description="New password (min 8 characters)")

    @field_validator('role')
    @classmethod
    def validate_role(cls, value: Optional[str]) -> Optional[str]:
        """Validate role if provided."""
        if value is None:
            return None
        valid_roles = ['admin', 'user', 'support']
        if value.lower() not in valid_roles:
            raise ValueError(f"role must be one of: {', '.join(valid_roles)}")
        return value.lower()

    @field_validator('subscription_tier')
    @classmethod
    def validate_subscription_tier(cls, value: Optional[str]) -> Optional[str]:
        """Validate subscription_tier if provided."""
        if value is None:
            return None
        valid_tiers = ['free', 'starter', 'pro', 'enterprise']
        if value.lower() not in valid_tiers:
            raise ValueError(f"subscription_tier must be one of: {', '.join(valid_tiers)}")
        return value.lower()

    model_config = {
        "json_schema_extra": {
            "example": {
                "full_name": "John Updated",
                "role": "admin",
                "is_active": True
            }
        }
    }


class AdminUserResponse(BaseModel):
    """Schema for user response (admin view)."""

    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    full_name: str = Field(..., description="User's full name")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="Whether the account is active")
    subscription_tier: str = Field(..., description="Subscription tier")
    subscription_status: str = Field(..., description="Subscription status")
    business_name: Optional[str] = Field(None, description="Business name")
    account_type: Optional[str] = Field(None, description="Account type")
    phone: Optional[str] = Field(None, description="Phone number")
    country: str = Field(..., description="Country code")
    language: str = Field(..., description="Language code")
    email_verified: bool = Field(..., description="Whether email is verified")
    failed_login_attempts: int = Field(..., description="Number of failed login attempts")
    locked_until: Optional[datetime] = Field(None, description="Account locked until this time")
    last_login: Optional[datetime] = Field(None, description="Last login time")
    current_products_count: int = Field(..., description="Current number of products")
    current_platforms_count: int = Field(..., description="Current number of connected platforms")
    created_at: datetime = Field(..., description="Account creation time")
    updated_at: datetime = Field(..., description="Last update time")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "full_name": "John Doe",
                "role": "user",
                "is_active": True,
                "subscription_tier": "free",
                "subscription_status": "active",
                "business_name": "John's Shop",
                "account_type": "individual",
                "phone": "+33612345678",
                "country": "FR",
                "language": "fr",
                "email_verified": True,
                "failed_login_attempts": 0,
                "locked_until": None,
                "last_login": "2024-12-20T10:30:00Z",
                "current_products_count": 25,
                "current_platforms_count": 2,
                "created_at": "2024-01-15T08:00:00Z",
                "updated_at": "2024-12-20T10:30:00Z"
            }
        }
    }


class AdminUserListResponse(BaseModel):
    """Schema for paginated user list response."""

    users: List[AdminUserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users matching the query")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")

    model_config = {
        "json_schema_extra": {
            "example": {
                "users": [],
                "total": 100,
                "skip": 0,
                "limit": 50
            }
        }
    }


class AdminUserDeleteResponse(BaseModel):
    """Schema for user deletion response."""

    success: bool = Field(..., description="Whether deletion was successful")
    message: str = Field(..., description="Status message")
    user_id: int = Field(..., description="ID of deleted user")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "User deleted successfully",
                "user_id": 42
            }
        }
    }
