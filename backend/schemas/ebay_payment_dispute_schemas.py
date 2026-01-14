"""
eBay Payment Dispute Pydantic Schemas

Schemas for request/response validation in payment dispute API endpoints.

Dispute States:
- OPEN: Dispute is active, no seller action required yet
- ACTION_NEEDED: Seller must respond before deadline
- CLOSED: Dispute has been resolved

Seller Responses:
- CONTEST: Seller disputes the claim
- ACCEPT: Seller accepts the claim (agrees to refund)

Created: 2026-01-14
Author: Claude
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, computed_field


# =============================================================================
# Enums as Literals for Validation
# =============================================================================

DisputeState = Literal["OPEN", "ACTION_NEEDED", "CLOSED"]

DisputeReason = Literal[
    "ITEM_NOT_RECEIVED",
    "SIGNIFICANTLY_NOT_AS_DESCRIBED",
    "FRAUD",
    "COUNTERFEIT",
    "DUPLICATE_AMOUNT",
    "INCORRECT_AMOUNT",
    "CANCELLATION",
    "RETURN_REFUND_NOT_PROCESSED",
    "OTHER",
]

SellerResponse = Literal["CONTEST", "ACCEPT"]

EvidenceType = Literal[
    "PROOF_OF_DELIVERY",
    "PROOF_OF_AUTHENTICITY",
    "PROOF_OF_ITEM_AS_DESCRIBED",
    "PROOF_OF_PICKUP",
    "TRACKING_INFORMATION",
    "OTHER",
]


# =============================================================================
# Request Schemas
# =============================================================================


class SyncDisputesRequest(BaseModel):
    """Request to sync disputes from eBay API."""

    days_back: int = Field(
        default=90, ge=1, le=90, description="Days to look back (max 90)"
    )


class SyncDisputeRequest(BaseModel):
    """Request to sync a single dispute."""

    payment_dispute_id: str = Field(
        ..., min_length=1, description="eBay payment dispute ID"
    )


class AcceptDisputeRequest(BaseModel):
    """Request to accept a payment dispute."""

    payment_dispute_id: str = Field(
        ..., min_length=1, description="eBay payment dispute ID"
    )
    return_address: Optional[Dict[str, Any]] = Field(
        default=None, description="Return address if buyer should return item"
    )


class ContestDisputeRequest(BaseModel):
    """Request to contest a payment dispute."""

    payment_dispute_id: str = Field(
        ..., min_length=1, description="eBay payment dispute ID"
    )
    note: Optional[str] = Field(
        default=None, max_length=1000, description="Note to eBay (max 1000 chars)"
    )
    return_address: Optional[Dict[str, Any]] = Field(
        default=None, description="Return address if needed"
    )


class EvidenceFileInfo(BaseModel):
    """Evidence file information."""

    file_id: str = Field(..., description="eBay file ID (from upload)")
    content_type: str = Field(default="application/pdf", description="File MIME type")


class AddEvidenceRequest(BaseModel):
    """Request to add evidence to a dispute."""

    payment_dispute_id: str = Field(
        ..., min_length=1, description="eBay payment dispute ID"
    )
    evidence_type: EvidenceType = Field(..., description="Type of evidence")
    files: Optional[List[EvidenceFileInfo]] = Field(
        default=None, description="Files to attach as evidence"
    )
    line_items: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Line items the evidence applies to"
    )


# =============================================================================
# Response Schemas
# =============================================================================


class EbayPaymentDisputeResponse(BaseModel):
    """Response schema for a single payment dispute."""

    id: int
    payment_dispute_id: str
    order_id: Optional[str] = None

    # Status
    dispute_state: Optional[str] = None
    reason: Optional[str] = None
    reason_for_closure: Optional[str] = None

    # Seller response
    seller_response: Optional[str] = None
    note: Optional[str] = None

    # Amount
    dispute_amount: Optional[float] = None
    dispute_currency: Optional[str] = None

    # Buyer
    buyer_username: Optional[str] = None

    # Revision
    revision: Optional[int] = None

    # Available choices
    available_choices: Optional[List[str]] = None

    # Evidence
    evidence: Optional[List[Dict[str, Any]]] = None
    evidence_requests: Optional[List[Dict[str, Any]]] = None

    # Line items
    line_items: Optional[List[Dict[str, Any]]] = None

    # Resolution
    resolution: Optional[Dict[str, Any]] = None

    # Return address
    return_address: Optional[Dict[str, Any]] = None

    # Dates
    open_date: Optional[datetime] = None
    respond_by_date: Optional[datetime] = None
    closed_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Computed properties
    @computed_field
    @property
    def is_open(self) -> bool:
        """Check if dispute is open."""
        return self.dispute_state in ("OPEN", "ACTION_NEEDED")

    @computed_field
    @property
    def is_closed(self) -> bool:
        """Check if dispute is closed."""
        return self.dispute_state == "CLOSED"

    @computed_field
    @property
    def needs_action(self) -> bool:
        """Check if dispute requires seller action."""
        return self.dispute_state == "ACTION_NEEDED"

    @computed_field
    @property
    def can_contest(self) -> bool:
        """Check if dispute can be contested."""
        if not self.available_choices:
            return False
        return "CONTEST" in self.available_choices

    @computed_field
    @property
    def can_accept(self) -> bool:
        """Check if dispute can be accepted."""
        if not self.available_choices:
            return False
        return "ACCEPT" in self.available_choices

    @computed_field
    @property
    def was_contested(self) -> bool:
        """Check if seller contested the dispute."""
        return self.seller_response == "CONTEST"

    @computed_field
    @property
    def was_accepted(self) -> bool:
        """Check if seller accepted the dispute."""
        return self.seller_response == "ACCEPT"

    @computed_field
    @property
    def is_past_deadline(self) -> bool:
        """Check if respond_by_date has passed."""
        if not self.respond_by_date:
            return False
        return datetime.utcnow() > self.respond_by_date

    @computed_field
    @property
    def days_until_deadline(self) -> Optional[int]:
        """Days until deadline (negative if past)."""
        if not self.respond_by_date:
            return None
        delta = self.respond_by_date - datetime.utcnow()
        return delta.days

    @computed_field
    @property
    def evidence_count(self) -> int:
        """Number of evidence items submitted."""
        return len(self.evidence) if self.evidence else 0

    @computed_field
    @property
    def evidence_requested_count(self) -> int:
        """Number of evidence types requested."""
        return len(self.evidence_requests) if self.evidence_requests else 0

    @computed_field
    @property
    def outcome(self) -> Optional[str]:
        """Get dispute outcome if closed."""
        if not self.resolution:
            return None
        return self.resolution.get("outcome")

    model_config = {"from_attributes": True}


class DisputeListResponse(BaseModel):
    """Paginated list of disputes."""

    items: List[EbayPaymentDisputeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SyncDisputesResponse(BaseModel):
    """Response for sync operation."""

    created: int
    updated: int
    total_fetched: int
    errors: int


class DisputeActionResponse(BaseModel):
    """Response for accept/contest dispute operation."""

    success: bool
    message: Optional[str] = None
    dispute: Optional[EbayPaymentDisputeResponse] = None


class AddEvidenceResponse(BaseModel):
    """Response for add evidence operation."""

    success: bool
    message: Optional[str] = None
    evidence_id: Optional[str] = None


class ReasonStatistics(BaseModel):
    """Statistics by dispute reason."""

    ITEM_NOT_RECEIVED: int = 0
    SIGNIFICANTLY_NOT_AS_DESCRIBED: int = 0
    FRAUD: int = 0
    COUNTERFEIT: int = 0
    DUPLICATE_AMOUNT: int = 0
    INCORRECT_AMOUNT: int = 0
    CANCELLATION: int = 0
    RETURN_REFUND_NOT_PROCESSED: int = 0
    OTHER: int = 0


class DisputeStatisticsResponse(BaseModel):
    """Response for dispute statistics."""

    open: int
    action_needed: int
    closed: int
    past_deadline: int
    total_amount: float
    by_reason: Dict[str, int]


class UrgentDisputeResponse(BaseModel):
    """Response for urgent disputes list."""

    disputes: List[EbayPaymentDisputeResponse]
    count: int


# =============================================================================
# API Constants
# =============================================================================


# Valid dispute states
DISPUTE_STATES = ["OPEN", "ACTION_NEEDED", "CLOSED"]

# Valid dispute reasons
DISPUTE_REASONS = [
    "ITEM_NOT_RECEIVED",
    "SIGNIFICANTLY_NOT_AS_DESCRIBED",
    "FRAUD",
    "COUNTERFEIT",
    "DUPLICATE_AMOUNT",
    "INCORRECT_AMOUNT",
    "CANCELLATION",
    "RETURN_REFUND_NOT_PROCESSED",
    "OTHER",
]

# Valid seller responses
SELLER_RESPONSES = ["CONTEST", "ACCEPT"]

# Valid evidence types
EVIDENCE_TYPES = [
    "PROOF_OF_DELIVERY",
    "PROOF_OF_AUTHENTICITY",
    "PROOF_OF_ITEM_AS_DESCRIBED",
    "PROOF_OF_PICKUP",
    "TRACKING_INFORMATION",
    "OTHER",
]

# Closure reasons
CLOSURE_REASONS = [
    "BUYER_WIN",
    "SELLER_WIN",
    "CANCELLED",
    "EXPIRED",
]
