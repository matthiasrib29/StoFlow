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


# ============================================================================
# Admin Stats Schemas
# ============================================================================


class AdminStatsUsersByRole(BaseModel):
    """User count by role."""

    admin: int = Field(default=0, description="Number of admin users")
    user: int = Field(default=0, description="Number of regular users")
    support: int = Field(default=0, description="Number of support users")


class AdminStatsOverview(BaseModel):
    """Overview statistics for admin dashboard."""

    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    inactive_users: int = Field(..., description="Number of inactive users")
    locked_users: int = Field(..., description="Number of locked accounts")
    users_by_role: AdminStatsUsersByRole = Field(..., description="Users grouped by role")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_users": 150,
                "active_users": 120,
                "inactive_users": 30,
                "locked_users": 2,
                "users_by_role": {
                    "admin": 3,
                    "user": 145,
                    "support": 2
                }
            }
        }
    }


class AdminStatsUsersByTier(BaseModel):
    """User count by subscription tier."""

    free: int = Field(default=0, description="Users on free tier")
    starter: int = Field(default=0, description="Users on starter tier")
    pro: int = Field(default=0, description="Users on pro tier")
    enterprise: int = Field(default=0, description="Users on enterprise tier")


class AdminStatsSubscriptions(BaseModel):
    """Subscription statistics."""

    users_by_tier: AdminStatsUsersByTier = Field(..., description="Users grouped by tier")
    total_mrr: float = Field(..., description="Estimated monthly recurring revenue (EUR)")
    paying_subscribers: int = Field(..., description="Number of paying subscribers")
    active_subscriptions: int = Field(..., description="Total active subscriptions")

    model_config = {
        "json_schema_extra": {
            "example": {
                "users_by_tier": {
                    "free": 100,
                    "starter": 30,
                    "pro": 15,
                    "enterprise": 5
                },
                "total_mrr": 1049.55,
                "paying_subscribers": 50,
                "active_subscriptions": 150
            }
        }
    }


class AdminStatsRegistrationData(BaseModel):
    """Single day registration data."""

    date: str = Field(..., description="Date (YYYY-MM-DD)")
    count: int = Field(..., description="Number of registrations")


class AdminStatsRegistrations(BaseModel):
    """Registration statistics over a period."""

    period: str = Field(..., description="Period: week, month, or 3months")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    data: List[AdminStatsRegistrationData] = Field(..., description="Daily registration data")
    total: int = Field(..., description="Total registrations in period")
    average_per_day: float = Field(..., description="Average registrations per day")

    model_config = {
        "json_schema_extra": {
            "example": {
                "period": "week",
                "start_date": "2024-12-17",
                "end_date": "2024-12-24",
                "data": [
                    {"date": "2024-12-17", "count": 3},
                    {"date": "2024-12-18", "count": 5}
                ],
                "total": 25,
                "average_per_day": 3.57
            }
        }
    }


class AdminRecentLogin(BaseModel):
    """Recent login entry."""

    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    full_name: str = Field(..., description="User full name")
    last_login: Optional[str] = Field(None, description="Last login timestamp (ISO format)")


class AdminNewRegistration(BaseModel):
    """New registration entry."""

    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    full_name: str = Field(..., description="User full name")
    created_at: Optional[str] = Field(None, description="Registration timestamp (ISO format)")
    subscription_tier: str = Field(..., description="Subscription tier")


class AdminStatsRecentActivity(BaseModel):
    """Recent activity statistics."""

    recent_logins: List[AdminRecentLogin] = Field(..., description="Recent logins (last 24h)")
    new_registrations: List[AdminNewRegistration] = Field(..., description="New registrations (last 7 days)")


# ============================================================================
# Admin Audit Log Schemas
# ============================================================================


class AdminAuditLogResponse(BaseModel):
    """Response schema for a single audit log entry."""

    id: int = Field(..., description="Audit log ID")
    admin_id: Optional[int] = Field(None, description="Admin user ID")
    admin_email: Optional[str] = Field(None, description="Admin email")
    action: str = Field(..., description="Action type")
    resource_type: str = Field(..., description="Resource type")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    resource_name: Optional[str] = Field(None, description="Resource name")
    details: Optional[dict] = Field(None, description="Action details (changed fields)")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    created_at: datetime = Field(..., description="Timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "admin_id": 1,
                "admin_email": "admin@example.com",
                "action": "UPDATE",
                "resource_type": "user",
                "resource_id": "42",
                "resource_name": "user@example.com",
                "details": {"changed": {"role": "admin"}, "before": {"role": "user"}},
                "ip_address": "192.168.1.1",
                "created_at": "2024-12-24T15:30:00Z"
            }
        }
    }


class AdminAuditLogListResponse(BaseModel):
    """Paginated list of audit logs."""

    logs: List[AdminAuditLogResponse] = Field(..., description="List of audit logs")
    total: int = Field(..., description="Total count")
    skip: int = Field(..., description="Records skipped")
    limit: int = Field(..., description="Maximum records")

    model_config = {
        "json_schema_extra": {
            "example": {
                "logs": [],
                "total": 100,
                "skip": 0,
                "limit": 50
            }
        }
    }


# ============================================================================
# Admin Attribute Schemas (Brands, Categories, Colors, Materials)
# ============================================================================


# ----- Brand Schemas -----

class AdminBrandCreate(BaseModel):
    """Schema for creating a brand."""

    name: str = Field(..., min_length=1, max_length=100, description="Brand name (EN, primary key)")
    name_fr: Optional[str] = Field(None, max_length=100, description="Brand name (FR)")
    description: Optional[str] = Field(None, description="Brand description")
    vinted_id: Optional[str] = Field(None, description="Vinted marketplace ID")
    monitoring: bool = Field(default=False, description="Special tracking flag")
    sector_jeans: Optional[str] = Field(None, max_length=20, description="Jeans market segment")
    sector_jacket: Optional[str] = Field(None, max_length=20, description="Jacket market segment")


class AdminBrandUpdate(BaseModel):
    """Schema for updating a brand. All fields optional except PK."""

    name_fr: Optional[str] = Field(None, max_length=100, description="Brand name (FR)")
    description: Optional[str] = Field(None, description="Brand description")
    vinted_id: Optional[str] = Field(None, description="Vinted marketplace ID")
    monitoring: Optional[bool] = Field(None, description="Special tracking flag")
    sector_jeans: Optional[str] = Field(None, max_length=20, description="Jeans market segment")
    sector_jacket: Optional[str] = Field(None, max_length=20, description="Jacket market segment")


class AdminBrandResponse(BaseModel):
    """Response schema for a brand."""

    pk: str = Field(..., description="Primary key (name)")
    name: str = Field(..., description="Brand name (EN)")
    name_fr: Optional[str] = Field(None, description="Brand name (FR)")
    description: Optional[str] = Field(None, description="Brand description")
    vinted_id: Optional[str] = Field(None, description="Vinted marketplace ID")
    monitoring: bool = Field(..., description="Special tracking flag")
    sector_jeans: Optional[str] = Field(None, description="Jeans market segment")
    sector_jacket: Optional[str] = Field(None, description="Jacket market segment")


# ----- Category Schemas -----

class AdminCategoryCreate(BaseModel):
    """Schema for creating a category."""

    name_en: str = Field(..., min_length=1, max_length=100, description="Category name (EN, primary key)")
    parent_category: Optional[str] = Field(None, max_length=100, description="Parent category name")
    name_fr: Optional[str] = Field(None, max_length=255, description="Category name (FR)")
    name_de: Optional[str] = Field(None, max_length=255, description="Category name (DE)")
    name_it: Optional[str] = Field(None, max_length=255, description="Category name (IT)")
    name_es: Optional[str] = Field(None, max_length=255, description="Category name (ES)")
    genders: Optional[List[str]] = Field(None, description="Available genders (men, women, boys, girls)")


class AdminCategoryUpdate(BaseModel):
    """Schema for updating a category. All fields optional except PK."""

    parent_category: Optional[str] = Field(None, max_length=100, description="Parent category name")
    name_fr: Optional[str] = Field(None, max_length=255, description="Category name (FR)")
    name_de: Optional[str] = Field(None, max_length=255, description="Category name (DE)")
    name_it: Optional[str] = Field(None, max_length=255, description="Category name (IT)")
    name_es: Optional[str] = Field(None, max_length=255, description="Category name (ES)")
    genders: Optional[List[str]] = Field(None, description="Available genders (men, women, boys, girls)")


class AdminCategoryResponse(BaseModel):
    """Response schema for a category."""

    pk: str = Field(..., description="Primary key (name_en)")
    name_en: str = Field(..., description="Category name (EN)")
    name_fr: Optional[str] = Field(None, description="Category name (FR)")
    name_de: Optional[str] = Field(None, description="Category name (DE)")
    name_it: Optional[str] = Field(None, description="Category name (IT)")
    name_es: Optional[str] = Field(None, description="Category name (ES)")
    parent_category: Optional[str] = Field(None, description="Parent category name")
    genders: Optional[List[str]] = Field(None, description="Available genders")


# ----- Color Schemas -----

class AdminColorCreate(BaseModel):
    """Schema for creating a color."""

    name_en: str = Field(..., min_length=1, max_length=100, description="Color name (EN, primary key)")
    name_fr: Optional[str] = Field(None, max_length=100, description="Color name (FR)")
    name_de: Optional[str] = Field(None, max_length=100, description="Color name (DE)")
    name_it: Optional[str] = Field(None, max_length=100, description="Color name (IT)")
    name_es: Optional[str] = Field(None, max_length=100, description="Color name (ES)")
    name_nl: Optional[str] = Field(None, max_length=100, description="Color name (NL)")
    name_pl: Optional[str] = Field(None, max_length=100, description="Color name (PL)")
    hex_code: Optional[str] = Field(None, max_length=7, pattern=r"^#[0-9A-Fa-f]{6}$", description="Hex color code")


class AdminColorUpdate(BaseModel):
    """Schema for updating a color. All fields optional except PK."""

    name_fr: Optional[str] = Field(None, max_length=100, description="Color name (FR)")
    name_de: Optional[str] = Field(None, max_length=100, description="Color name (DE)")
    name_it: Optional[str] = Field(None, max_length=100, description="Color name (IT)")
    name_es: Optional[str] = Field(None, max_length=100, description="Color name (ES)")
    name_nl: Optional[str] = Field(None, max_length=100, description="Color name (NL)")
    name_pl: Optional[str] = Field(None, max_length=100, description="Color name (PL)")
    hex_code: Optional[str] = Field(None, max_length=7, pattern=r"^#[0-9A-Fa-f]{6}$", description="Hex color code")


class AdminColorResponse(BaseModel):
    """Response schema for a color."""

    pk: str = Field(..., description="Primary key (name_en)")
    name_en: str = Field(..., description="Color name (EN)")
    name_fr: Optional[str] = Field(None, description="Color name (FR)")
    name_de: Optional[str] = Field(None, description="Color name (DE)")
    name_it: Optional[str] = Field(None, description="Color name (IT)")
    name_es: Optional[str] = Field(None, description="Color name (ES)")
    name_nl: Optional[str] = Field(None, description="Color name (NL)")
    name_pl: Optional[str] = Field(None, description="Color name (PL)")
    hex_code: Optional[str] = Field(None, description="Hex color code")


# ----- Material Schemas -----

class AdminMaterialCreate(BaseModel):
    """Schema for creating a material."""

    name_en: str = Field(..., min_length=1, max_length=100, description="Material name (EN, primary key)")
    name_fr: Optional[str] = Field(None, max_length=100, description="Material name (FR)")
    name_de: Optional[str] = Field(None, max_length=100, description="Material name (DE)")
    name_it: Optional[str] = Field(None, max_length=100, description="Material name (IT)")
    name_es: Optional[str] = Field(None, max_length=100, description="Material name (ES)")
    name_nl: Optional[str] = Field(None, max_length=100, description="Material name (NL)")
    name_pl: Optional[str] = Field(None, max_length=100, description="Material name (PL)")
    vinted_id: Optional[int] = Field(None, description="Vinted material ID")


class AdminMaterialUpdate(BaseModel):
    """Schema for updating a material. All fields optional except PK."""

    name_fr: Optional[str] = Field(None, max_length=100, description="Material name (FR)")
    name_de: Optional[str] = Field(None, max_length=100, description="Material name (DE)")
    name_it: Optional[str] = Field(None, max_length=100, description="Material name (IT)")
    name_es: Optional[str] = Field(None, max_length=100, description="Material name (ES)")
    name_nl: Optional[str] = Field(None, max_length=100, description="Material name (NL)")
    name_pl: Optional[str] = Field(None, max_length=100, description="Material name (PL)")
    vinted_id: Optional[int] = Field(None, description="Vinted material ID")


class AdminMaterialResponse(BaseModel):
    """Response schema for a material."""

    pk: str = Field(..., description="Primary key (name_en)")
    name_en: str = Field(..., description="Material name (EN)")
    name_fr: Optional[str] = Field(None, description="Material name (FR)")
    name_de: Optional[str] = Field(None, description="Material name (DE)")
    name_it: Optional[str] = Field(None, description="Material name (IT)")
    name_es: Optional[str] = Field(None, description="Material name (ES)")
    name_nl: Optional[str] = Field(None, description="Material name (NL)")
    name_pl: Optional[str] = Field(None, description="Material name (PL)")
    vinted_id: Optional[int] = Field(None, description="Vinted material ID")


# ----- Generic Attribute List Response -----

class AdminAttributeListResponse(BaseModel):
    """Generic paginated list response for attributes."""

    items: List[dict] = Field(..., description="List of attribute items")
    total: int = Field(..., description="Total count")
    skip: int = Field(..., description="Records skipped")
    limit: int = Field(..., description="Maximum records")
