"""
Vinted Pro Seller Schemas

Pydantic schemas for Vinted pro seller API endpoints (admin only).

Author: Claude
Date: 2026-01-27
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


# ===== Response Schemas =====

class VintedProSellerResponse(BaseModel):
    """Response schema for a single Vinted pro seller."""

    id: int
    vinted_user_id: int
    login: str
    country_code: Optional[str] = None
    country_id: Optional[int] = None
    country_title: Optional[str] = None

    # Stats
    item_count: int = 0
    total_items_count: int = 0
    given_item_count: int = 0
    taken_item_count: int = 0
    followers_count: int = 0
    following_count: int = 0
    feedback_count: int = 0
    feedback_reputation: Optional[Decimal] = None
    positive_feedback_count: int = 0
    neutral_feedback_count: int = 0
    negative_feedback_count: int = 0
    is_on_holiday: bool = False

    # Business account
    business_account_id: Optional[int] = None
    business_name: Optional[str] = None
    legal_name: Optional[str] = None
    legal_code: Optional[str] = None
    entity_type: Optional[str] = None
    entity_type_title: Optional[str] = None
    nationality: Optional[str] = None
    business_country: Optional[str] = None
    business_city: Optional[str] = None
    verified_identity: Optional[bool] = None
    business_is_active: Optional[bool] = None

    # Profile
    about: Optional[str] = None
    profile_url: Optional[str] = None
    last_loged_on_ts: Optional[str] = None

    # Extracted contacts
    contact_email: Optional[str] = None
    contact_instagram: Optional[str] = None
    contact_tiktok: Optional[str] = None
    contact_youtube: Optional[str] = None
    contact_website: Optional[str] = None
    contact_phone: Optional[str] = None

    # Metadata
    marketplace: str = "vinted_fr"
    status: str = "new"
    notes: Optional[str] = None

    # Timestamps
    discovered_at: datetime
    last_scanned_at: datetime
    contacted_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VintedProSellerListResponse(BaseModel):
    """Response schema for paginated list of pro sellers."""

    sellers: List[VintedProSellerResponse]
    total: int
    skip: int
    limit: int


class VintedProSellerStatsResponse(BaseModel):
    """Response schema for pro seller statistics."""

    total_sellers: int
    by_status: dict
    by_country: dict
    by_marketplace: dict
    with_email: int
    with_instagram: int
    with_any_contact: int


# ===== Request Schemas =====

class StartProSellerScanRequest(BaseModel):
    """Request to start a pro seller scan workflow."""

    search_scope: List[str] = Field(
        default_factory=lambda: list("abcdefghijklmnopqrstuvwxyz"),
        description="List of search characters/texts to scan"
    )
    marketplace: str = Field("vinted_fr", description="Marketplace identifier")
    per_page: int = Field(90, ge=1, le=100, description="Results per page")


class StartProSellerScanResponse(BaseModel):
    """Response after starting a pro seller scan."""

    workflow_id: str
    run_id: str
    status: str = "started"


class ProSellerScanProgressResponse(BaseModel):
    """Response for scan progress query."""

    status: str
    current_letter: Optional[str] = None
    current_page: int = 0
    total_saved: int = 0
    total_updated: int = 0
    total_errors: int = 0
    letters_completed: int = 0
    total_letters: int = 0


class VintedProSellerUpdateRequest(BaseModel):
    """Request to update a pro seller."""

    status: Optional[str] = Field(None, description="New status: new, contacted, converted, ignored")
    notes: Optional[str] = Field(None, max_length=5000, description="Admin notes")


class VintedProSellerBulkUpdateRequest(BaseModel):
    """Request to bulk update pro sellers."""

    seller_ids: List[int] = Field(..., min_length=1, max_length=100)
    status: Optional[str] = Field(None, description="New status for all")
