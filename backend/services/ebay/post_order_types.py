"""
eBay Post-Order API Shared Types and Enums.

Enumerations for returns, cancellations, inquiries, and payment disputes statuses.
Used by models, services, and API schemas.

Based on eBay Post-Order API v2 and Fulfillment API documentation.

Author: Claude
Date: 2026-01-13
"""

from enum import Enum


# ========== CANCELLATION TYPES ==========


class CancellationStatus(str, Enum):
    """
    Cancellation request status.

    From: https://developer.ebay.com/devzone/post-order/types/CancelStatusEnum.html
    """

    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    CANCEL_PENDING = "CANCEL_PENDING"
    CANCEL_CLOSED_NO_REFUND = "CANCEL_CLOSED_NO_REFUND"
    CANCEL_CLOSED_WITH_REFUND = "CANCEL_CLOSED_WITH_REFUND"
    CANCEL_CLOSED_UNKNOWN_REFUND = "CANCEL_CLOSED_UNKNOWN_REFUND"
    CANCEL_CLOSED_FOR_COMMITMENT = "CANCEL_CLOSED_FOR_COMMITMENT"


class CancellationReason(str, Enum):
    """
    Reason for cancellation.

    From: https://developer.ebay.com/devzone/post-order/types/CancelReasonEnum.html
    """

    BUYER_ASKED_CANCEL = "BUYER_ASKED_CANCEL"
    BUYER_NO_SHOW = "BUYER_NO_SHOW"
    BUYER_CANCEL = "BUYER_CANCEL"
    ORDER_UNPAID = "ORDER_UNPAID"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    SELLER_CANCEL = "SELLER_CANCEL"
    ADDRESS_ISSUES = "ADDRESS_ISSUES"
    PRICE_ERROR = "PRICE_ERROR"
    OTHER = "OTHER"


class CancellationInitiator(str, Enum):
    """Who initiated the cancellation."""

    BUYER = "BUYER"
    SELLER = "SELLER"
    UNKNOWN = "UNKNOWN"


# ========== RETURN TYPES ==========


class ReturnStatus(str, Enum):
    """
    Return request status.

    From: https://developer.ebay.com/devzone/post-order/types/ReturnStatusEnum.html
    """

    RETURN_REQUESTED = "RETURN_REQUESTED"
    RETURN_WAITING_FOR_RMA = "RETURN_WAITING_FOR_RMA"
    RETURN_WAITING_FOR_SHIPPING_LABEL = "RETURN_WAITING_FOR_SHIPPING_LABEL"
    RETURN_SHIPPING_LABEL_CREATED = "RETURN_SHIPPING_LABEL_CREATED"
    RETURN_ITEM_SHIPPED = "RETURN_ITEM_SHIPPED"
    RETURN_ITEM_DELIVERED = "RETURN_ITEM_DELIVERED"
    RETURN_CLOSED = "RETURN_CLOSED"
    PARTIAL_REFUND_REQUESTED = "PARTIAL_REFUND_REQUESTED"
    PARTIAL_REFUND_DECLINED = "PARTIAL_REFUND_DECLINED"
    PARTIAL_REFUND_FAILED = "PARTIAL_REFUND_FAILED"
    REFUND_INITIATED = "REFUND_INITIATED"


class ReturnReason(str, Enum):
    """
    Reason for return.

    From: https://developer.ebay.com/devzone/post-order/types/ReturnReasonEnum.html
    """

    ARRIVED_DAMAGED = "ARRIVED_DAMAGED"
    ARRIVED_LATE = "ARRIVED_LATE"
    BUYER_CANCEL = "BUYER_CANCEL"
    BUYER_REMORSE = "BUYER_REMORSE"
    DEFECTIVE_ITEM = "DEFECTIVE_ITEM"
    DIFFERENT_FROM_LISTING = "DIFFERENT_FROM_LISTING"
    MISSING_PARTS = "MISSING_PARTS"
    NOT_AS_DESCRIBED = "NOT_AS_DESCRIBED"
    WRONG_ITEM = "WRONG_ITEM"
    OTHER = "OTHER"


class ReturnType(str, Enum):
    """Type of return request."""

    RETURN = "RETURN"
    REPLACEMENT = "REPLACEMENT"
    REFUND_ONLY = "REFUND_ONLY"


class ReturnState(str, Enum):
    """
    High-level return state for filtering.

    Used in search queries.
    """

    OPEN = "OPEN"
    CLOSED = "CLOSED"


# ========== INQUIRY TYPES (INR - Item Not Received) ==========


class InquiryStatus(str, Enum):
    """
    INR Inquiry status.

    From: https://developer.ebay.com/devzone/post-order/types/InquiryStatusEnum.html
    """

    OPEN = "OPEN"
    CLOSED = "CLOSED"
    ON_HOLD = "ON_HOLD"
    ESCALATED = "ESCALATED"


class InquiryType(str, Enum):
    """Type of inquiry."""

    INR = "INR"  # Item Not Received


class InquiryCloseReason(str, Enum):
    """Reason for closing an inquiry."""

    BUYER_RECEIVED_ITEM = "BUYER_RECEIVED_ITEM"
    BUYER_REQUESTED_CLOSE = "BUYER_REQUESTED_CLOSE"
    SELLER_PROVIDED_REFUND = "SELLER_PROVIDED_REFUND"
    SELLER_PROVIDED_TRACKING = "SELLER_PROVIDED_TRACKING"
    ESCALATED_TO_CASE = "ESCALATED_TO_CASE"
    OTHER = "OTHER"


# ========== PAYMENT DISPUTE TYPES ==========


class PaymentDisputeStatus(str, Enum):
    """
    Payment dispute status.

    From: https://developer.ebay.com/api-docs/sell/fulfillment/types/api:PaymentDisputeStatusEnum
    """

    OPEN = "OPEN"
    WAITING_FOR_SELLER = "WAITING_FOR_SELLER"
    ACTION_NEEDED = "ACTION_NEEDED"
    CLOSED = "CLOSED"
    PROCESSING = "PROCESSING"


class PaymentDisputeReason(str, Enum):
    """
    Reason for payment dispute.

    From: https://developer.ebay.com/api-docs/sell/fulfillment/types/api:PaymentDisputeReasonEnum
    """

    ITEM_NOT_RECEIVED = "ITEM_NOT_RECEIVED"
    SIGNIFICANTLY_NOT_AS_DESCRIBED = "SIGNIFICANTLY_NOT_AS_DESCRIBED"
    UNAUTHORIZED = "UNAUTHORIZED"
    DEFECTIVE = "DEFECTIVE"
    DUPLICATE_CHARGE = "DUPLICATE_CHARGE"
    INCORRECT_AMOUNT = "INCORRECT_AMOUNT"
    CREDIT_NOT_PROCESSED = "CREDIT_NOT_PROCESSED"
    CANCELLED = "CANCELLED"


class PaymentDisputeOutcome(str, Enum):
    """Outcome of a payment dispute."""

    SELLER_WINS = "SELLER_WINS"
    BUYER_WINS = "BUYER_WINS"
    UNKNOWN = "UNKNOWN"


# ========== REFUND TYPES ==========


class RefundStatus(str, Enum):
    """Refund status."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class RefundType(str, Enum):
    """Type of refund."""

    FULL = "FULL"
    PARTIAL = "PARTIAL"


class RefundReason(str, Enum):
    """Reason for issuing a refund."""

    RETURN_RECEIVED = "RETURN_RECEIVED"
    CANCELLATION_APPROVED = "CANCELLATION_APPROVED"
    PAYMENT_DISPUTE = "PAYMENT_DISPUTE"
    SELLER_INITIATED = "SELLER_INITIATED"
    ORDER_PROBLEM = "ORDER_PROBLEM"
    OTHER = "OTHER"


# ========== ACTION URGENCY ==========


class ActionUrgency(str, Enum):
    """
    Urgency level for seller actions.

    Used in AlertService to prioritize notifications.
    """

    CRITICAL = "CRITICAL"  # Must act within 24h
    HIGH = "HIGH"  # Must act within 48h
    MEDIUM = "MEDIUM"  # Must act within 3-5 days
    LOW = "LOW"  # No immediate action required


__all__ = [
    # Cancellation
    "CancellationStatus",
    "CancellationReason",
    "CancellationInitiator",
    # Return
    "ReturnStatus",
    "ReturnReason",
    "ReturnType",
    "ReturnState",
    # Inquiry
    "InquiryStatus",
    "InquiryType",
    "InquiryCloseReason",
    # Payment Dispute
    "PaymentDisputeStatus",
    "PaymentDisputeReason",
    "PaymentDisputeOutcome",
    # Refund
    "RefundStatus",
    "RefundType",
    "RefundReason",
    # Utility
    "ActionUrgency",
]
