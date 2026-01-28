"""
Vinted Prospect Schemas

Pydantic schemas for Vinted prospect API endpoints (admin only).

Author: Claude
Date: 2026-01-19
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


# ===== Response Schemas =====

class VintedProspectResponse(BaseModel):
    """Response schema for a single Vinted prospect."""

    id: int = Field(..., description="Prospect ID")
    vinted_user_id: int = Field(..., description="Vinted user ID")
    login: str = Field(..., description="Vinted username")
    country_code: Optional[str] = Field(None, description="Country code (FR, DE, etc.)")
    item_count: int = Field(0, description="Number of active items")
    total_items_count: int = Field(0, description="Total items ever listed")
    feedback_count: int = Field(0, description="Number of feedback reviews")
    feedback_reputation: Optional[Decimal] = Field(None, description="Feedback reputation score")
    is_business: bool = Field(False, description="Is a business account")
    profile_url: Optional[str] = Field(None, description="URL to Vinted profile")
    status: str = Field("new", description="Prospection status: new, contacted, converted, ignored")
    notes: Optional[str] = Field(None, description="Admin notes")
    discovered_at: datetime = Field(..., description="Discovery timestamp")
    last_synced_at: datetime = Field(..., description="Last sync timestamp")
    contacted_at: Optional[datetime] = Field(None, description="Contact timestamp")
    created_by: Optional[int] = Field(None, description="Admin user ID")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class VintedProspectListResponse(BaseModel):
    """Response schema for paginated list of prospects."""

    prospects: List[VintedProspectResponse] = Field(..., description="List of prospects")
    total: int = Field(..., description="Total count")
    skip: int = Field(..., description="Offset")
    limit: int = Field(..., description="Limit per page")


class VintedProspectStatsResponse(BaseModel):
    """Response schema for prospect statistics."""

    total_prospects: int = Field(..., description="Total prospects discovered")
    by_status: dict = Field(..., description="Count by status (new, contacted, converted, ignored)")
    by_country: dict = Field(..., description="Count by country")
    avg_item_count: float = Field(..., description="Average item count per prospect")
    business_count: int = Field(..., description="Number of business accounts")


# ===== Request Schemas =====

class VintedProspectFetchRequest(BaseModel):
    """Request to trigger prospect fetching."""

    min_items: int = Field(200, ge=1, description="Minimum items count to include")
    country_code: str = Field("FR", description="Country code filter")
    max_pages_per_search: int = Field(50, ge=1, le=100, description="Max pages per search character")


class VintedProspectUpdateRequest(BaseModel):
    """Request to update a prospect."""

    status: Optional[str] = Field(None, description="New status: new, contacted, converted, ignored")
    notes: Optional[str] = Field(None, max_length=5000, description="Admin notes")


class VintedProspectBulkUpdateRequest(BaseModel):
    """Request to bulk update prospects."""

    prospect_ids: List[int] = Field(..., min_length=1, max_length=100, description="Prospect IDs to update")
    status: Optional[str] = Field(None, description="New status for all")
    notes: Optional[str] = Field(None, max_length=5000, description="Notes to append")


# ===== Job Response Schemas =====

class VintedProspectFetchJobResponse(BaseModel):
    """Response after triggering a fetch workflow."""

    workflow_id: str = Field(..., description="Temporal workflow ID")
    status: str = Field(..., description="Workflow status (started, running, etc.)")
    message: str = Field(..., description="Confirmation message")


class VintedProspectFetchResultResponse(BaseModel):
    """Response schema for fetch operation result."""

    success: bool = Field(..., description="Operation success")
    total_found: int = Field(0, description="Total users found")
    total_saved: int = Field(0, description="Users saved to database")
    duplicates_skipped: int = Field(0, description="Duplicates skipped")
    errors: int = Field(0, description="Errors encountered")
