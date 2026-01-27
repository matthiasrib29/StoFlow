"""
eBay Dashboard Service

Provides unified statistics and alerts across all eBay post-sale domains:
- Returns
- Cancellations
- Refunds
- Payment Disputes
- INR Inquiries

Created: 2026-01-14
Author: Claude
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from repositories import (
    EbayInquiryRepository,
)
from repositories.ebay_return_repository import EbayReturnRepository
from repositories.ebay_cancellation_repository import EbayCancellationRepository
from repositories.ebay_refund_repository import EbayRefundRepository
from repositories.ebay_payment_dispute_repository import EbayPaymentDisputeRepository
from shared.logging import setup_logging

logger = setup_logging()


class EbayDashboardService:
    """
    Service for aggregating eBay post-sale statistics and alerts.

    Provides:
    - Unified statistics across all domains
    - Urgent items requiring seller action
    - Timeline of recent activity
    """

    def __init__(self, db: Session):
        """
        Initialize the dashboard service.

        Args:
            db: Database session with user schema set
        """
        self.db = db

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_unified_statistics(self) -> Dict[str, Any]:
        """
        Get unified statistics across all post-sale domains.

        Returns:
            Dictionary with statistics for each domain and totals
        """
        logger.debug("Fetching unified eBay dashboard statistics")

        # Fetch statistics from each domain
        returns_stats = self._get_returns_statistics()
        cancellations_stats = self._get_cancellations_statistics()
        refunds_stats = self._get_refunds_statistics()
        disputes_stats = self._get_disputes_statistics()
        inquiries_stats = self._get_inquiries_statistics()

        # Calculate totals
        total_open = (
            returns_stats.get("open", 0) +
            cancellations_stats.get("pending", 0) +
            disputes_stats.get("open", 0) +
            inquiries_stats.get("open", 0)
        )

        total_needs_action = (
            returns_stats.get("needs_action", 0) +
            cancellations_stats.get("needs_action", 0) +
            disputes_stats.get("action_needed", 0) +
            inquiries_stats.get("needs_action", 0)
        )

        total_past_deadline = (
            returns_stats.get("past_deadline", 0) +
            cancellations_stats.get("past_due", 0) +
            inquiries_stats.get("past_deadline", 0)
        )

        return {
            "returns": returns_stats,
            "cancellations": cancellations_stats,
            "refunds": refunds_stats,
            "payment_disputes": disputes_stats,
            "inquiries": inquiries_stats,
            "totals": {
                "open": total_open,
                "needs_action": total_needs_action,
                "past_deadline": total_past_deadline,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _get_returns_statistics(self) -> Dict[str, int]:
        """Get return statistics."""
        try:
            open_count = EbayReturnRepository.count_by_state(self.db, "OPEN")
            closed_count = EbayReturnRepository.count_by_state(self.db, "CLOSED")
            needs_action = EbayReturnRepository.count_needs_action(self.db)
            past_deadline = EbayReturnRepository.count_past_deadline(self.db)

            return {
                "open": open_count,
                "closed": closed_count,
                "needs_action": needs_action,
                "past_deadline": past_deadline,
            }
        except Exception as e:
            logger.warning(f"Failed to get return statistics: {e}", exc_info=True)
            return {"open": 0, "closed": 0, "needs_action": 0, "past_deadline": 0}

    def _get_cancellations_statistics(self) -> Dict[str, int]:
        """Get cancellation statistics."""
        try:
            pending = EbayCancellationRepository.count_pending(self.db)
            closed = EbayCancellationRepository.count_closed(self.db)
            needs_action = EbayCancellationRepository.count_needs_action(self.db)
            past_due = EbayCancellationRepository.count_past_due(self.db)

            return {
                "pending": pending,
                "closed": closed,
                "needs_action": needs_action,
                "past_due": past_due,
            }
        except Exception as e:
            logger.warning(f"Failed to get cancellation statistics: {e}", exc_info=True)
            return {"pending": 0, "closed": 0, "needs_action": 0, "past_due": 0}

    def _get_refunds_statistics(self) -> Dict[str, Any]:
        """Get refund statistics."""
        try:
            pending = EbayRefundRepository.count_by_status(self.db, "PENDING")
            completed = EbayRefundRepository.count_by_status(self.db, "REFUNDED")
            failed = EbayRefundRepository.count_by_status(self.db, "FAILED")
            total_refunded = EbayRefundRepository.sum_refunded_amount(self.db)

            return {
                "pending": pending,
                "completed": completed,
                "failed": failed,
                "total_refunded": total_refunded or 0.0,
            }
        except Exception as e:
            logger.warning(f"Failed to get refund statistics: {e}", exc_info=True)
            return {"pending": 0, "completed": 0, "failed": 0, "total_refunded": 0.0}

    def _get_disputes_statistics(self) -> Dict[str, Any]:
        """Get payment dispute statistics."""
        try:
            open_count = EbayPaymentDisputeRepository.count_by_state(self.db, "OPEN")
            action_needed = EbayPaymentDisputeRepository.count_by_state(
                self.db, "ACTION_NEEDED"
            )
            closed = EbayPaymentDisputeRepository.count_by_state(self.db, "CLOSED")
            total_disputed = EbayPaymentDisputeRepository.sum_disputed_amount(self.db)

            return {
                "open": open_count,
                "action_needed": action_needed,
                "closed": closed,
                "total_disputed": total_disputed or 0.0,
            }
        except Exception as e:
            logger.warning(f"Failed to get dispute statistics: {e}", exc_info=True)
            return {"open": 0, "action_needed": 0, "closed": 0, "total_disputed": 0.0}

    def _get_inquiries_statistics(self) -> Dict[str, int]:
        """Get INR inquiry statistics."""
        try:
            open_count = EbayInquiryRepository.count_by_state(self.db, "OPEN")
            closed = EbayInquiryRepository.count_by_state(self.db, "CLOSED")
            needs_action = EbayInquiryRepository.count_needs_action(self.db)
            past_deadline = EbayInquiryRepository.count_past_deadline(self.db)

            return {
                "open": open_count,
                "closed": closed,
                "needs_action": needs_action,
                "past_deadline": past_deadline,
            }
        except Exception as e:
            logger.warning(f"Failed to get inquiry statistics: {e}", exc_info=True)
            return {"open": 0, "closed": 0, "needs_action": 0, "past_deadline": 0}

    # =========================================================================
    # ALERTS / URGENT ITEMS
    # =========================================================================

    def get_urgent_items(self, limit: int = 20) -> Dict[str, Any]:
        """
        Get all items requiring urgent seller action.

        Args:
            limit: Maximum number of items per category

        Returns:
            Dictionary with urgent items from each domain
        """
        logger.debug(f"Fetching urgent items with limit={limit}")

        urgent_returns = self._get_urgent_returns(limit)
        urgent_cancellations = self._get_urgent_cancellations(limit)
        urgent_disputes = self._get_urgent_disputes(limit)
        urgent_inquiries = self._get_urgent_inquiries(limit)

        total_urgent = (
            len(urgent_returns) +
            len(urgent_cancellations) +
            len(urgent_disputes) +
            len(urgent_inquiries)
        )

        return {
            "returns": urgent_returns,
            "cancellations": urgent_cancellations,
            "payment_disputes": urgent_disputes,
            "inquiries": urgent_inquiries,
            "total_count": total_urgent,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _get_urgent_returns(self, limit: int) -> List[Dict[str, Any]]:
        """Get urgent returns needing action."""
        try:
            # Get returns needing action
            returns = EbayReturnRepository.list_needs_action(self.db, limit)
            # Also get past deadline returns
            past_deadline = EbayReturnRepository.list_past_deadline(self.db, limit)

            # Combine and deduplicate
            seen_ids = set()
            urgent = []

            for ret in list(returns) + list(past_deadline):
                if ret.id not in seen_ids:
                    seen_ids.add(ret.id)
                    urgent.append({
                        "id": ret.id,
                        "return_id": ret.return_id,
                        "order_id": ret.order_id,
                        "status": ret.status,
                        "reason": ret.reason,
                        "refund_amount": ret.refund_amount,
                        "refund_currency": ret.refund_currency,
                        "buyer_username": ret.buyer_username,
                        "deadline_date": ret.deadline_date.isoformat() if ret.deadline_date else None,
                        "is_past_deadline": ret.is_past_deadline,
                        "type": "return",
                        "urgency": "critical" if ret.is_past_deadline else "high",
                    })

            return urgent[:limit]
        except Exception as e:
            logger.warning(f"Failed to get urgent returns: {e}", exc_info=True)
            return []

    def _get_urgent_cancellations(self, limit: int) -> List[Dict[str, Any]]:
        """Get urgent cancellations needing action."""
        try:
            cancellations = EbayCancellationRepository.list_needs_action(self.db, limit)

            urgent = []
            for cancel in cancellations:
                urgent.append({
                    "id": cancel.id,
                    "cancel_id": cancel.cancel_id,
                    "order_id": cancel.order_id,
                    "status": cancel.cancel_status,
                    "reason": cancel.cancel_reason,
                    "requestor_role": cancel.requestor_role,
                    "refund_amount": cancel.refund_amount,
                    "refund_currency": cancel.refund_currency,
                    "buyer_username": cancel.buyer_username,
                    "response_due_date": cancel.response_due_date.isoformat() if cancel.response_due_date else None,
                    "is_past_due": cancel.is_past_response_due,
                    "type": "cancellation",
                    "urgency": "critical" if cancel.is_past_response_due else "high",
                })

            return urgent[:limit]
        except Exception as e:
            logger.warning(f"Failed to get urgent cancellations: {e}", exc_info=True)
            return []

    def _get_urgent_disputes(self, limit: int) -> List[Dict[str, Any]]:
        """Get urgent payment disputes needing action."""
        try:
            disputes = EbayPaymentDisputeRepository.list_urgent(self.db, limit)

            urgent = []
            for dispute in disputes:
                urgent.append({
                    "id": dispute.id,
                    "dispute_id": dispute.dispute_id,
                    "order_id": dispute.order_id,
                    "state": dispute.dispute_state,
                    "reason": dispute.dispute_reason,
                    "dispute_amount": dispute.dispute_amount,
                    "dispute_currency": dispute.dispute_currency,
                    "buyer_username": dispute.buyer_username,
                    "response_due_date": dispute.response_due_date.isoformat() if dispute.response_due_date else None,
                    "is_past_due": dispute.is_past_due,
                    "type": "payment_dispute",
                    "urgency": "critical" if dispute.is_past_due else "high",
                })

            return urgent[:limit]
        except Exception as e:
            logger.warning(f"Failed to get urgent disputes: {e}", exc_info=True)
            return []

    def _get_urgent_inquiries(self, limit: int) -> List[Dict[str, Any]]:
        """Get urgent INR inquiries needing action."""
        try:
            # Get inquiries needing action
            inquiries = EbayInquiryRepository.list_needs_action(self.db, limit)
            # Also get past deadline inquiries
            past_deadline = EbayInquiryRepository.list_past_deadline(self.db, limit)

            # Combine and deduplicate
            seen_ids = set()
            urgent = []

            for inq in list(inquiries) + list(past_deadline):
                if inq.id not in seen_ids:
                    seen_ids.add(inq.id)
                    urgent.append({
                        "id": inq.id,
                        "inquiry_id": inq.inquiry_id,
                        "order_id": inq.order_id,
                        "status": inq.inquiry_status,
                        "claim_amount": inq.claim_amount,
                        "claim_currency": inq.claim_currency,
                        "buyer_username": inq.buyer_username,
                        "item_title": inq.item_title,
                        "respond_by_date": inq.respond_by_date.isoformat() if inq.respond_by_date else None,
                        "is_past_due": inq.is_past_due,
                        "is_escalated": inq.is_escalated,
                        "type": "inquiry",
                        "urgency": "critical" if inq.is_past_due or inq.is_escalated else "high",
                    })

            return urgent[:limit]
        except Exception as e:
            logger.warning(f"Failed to get urgent inquiries: {e}", exc_info=True)
            return []

    # =========================================================================
    # RECENT ACTIVITY
    # =========================================================================

    def get_recent_activity(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent activity across all domains.

        Args:
            limit: Maximum number of items to return

        Returns:
            List of recent activity items sorted by date
        """
        logger.debug(f"Fetching recent activity with limit={limit}")

        activities = []

        # Get recent returns
        try:
            returns = EbayReturnRepository.list_returns(
                self.db, limit=limit, offset=0
            )
            for ret in returns:
                activities.append({
                    "type": "return",
                    "id": ret.id,
                    "external_id": ret.return_id,
                    "order_id": ret.order_id,
                    "status": ret.status,
                    "amount": ret.refund_amount,
                    "currency": ret.refund_currency,
                    "buyer_username": ret.buyer_username,
                    "date": ret.creation_date or ret.created_at,
                    "updated_at": ret.updated_at,
                })
        except Exception as e:
            logger.warning(f"Failed to get recent returns: {e}", exc_info=True)

        # Get recent cancellations
        try:
            cancellations = EbayCancellationRepository.list_cancellations(
                self.db, limit=limit, offset=0
            )
            for cancel in cancellations:
                activities.append({
                    "type": "cancellation",
                    "id": cancel.id,
                    "external_id": cancel.cancel_id,
                    "order_id": cancel.order_id,
                    "status": cancel.cancel_status,
                    "amount": cancel.refund_amount,
                    "currency": cancel.refund_currency,
                    "buyer_username": cancel.buyer_username,
                    "date": cancel.creation_date or cancel.created_at,
                    "updated_at": cancel.updated_at,
                })
        except Exception as e:
            logger.warning(f"Failed to get recent cancellations: {e}", exc_info=True)

        # Get recent refunds
        try:
            refunds = EbayRefundRepository.list_refunds(
                self.db, limit=limit, offset=0
            )
            for refund in refunds:
                activities.append({
                    "type": "refund",
                    "id": refund.id,
                    "external_id": refund.refund_id,
                    "order_id": refund.order_id,
                    "status": refund.refund_status,
                    "amount": refund.refund_amount,
                    "currency": refund.refund_currency,
                    "buyer_username": refund.buyer_username,
                    "date": refund.refund_date or refund.created_at,
                    "updated_at": refund.updated_at,
                })
        except Exception as e:
            logger.warning(f"Failed to get recent refunds: {e}", exc_info=True)

        # Get recent payment disputes
        try:
            disputes = EbayPaymentDisputeRepository.list_payment_disputes(
                self.db, limit=limit, offset=0
            )
            for dispute in disputes:
                activities.append({
                    "type": "payment_dispute",
                    "id": dispute.id,
                    "external_id": dispute.dispute_id,
                    "order_id": dispute.order_id,
                    "status": dispute.dispute_state,
                    "amount": dispute.dispute_amount,
                    "currency": dispute.dispute_currency,
                    "buyer_username": dispute.buyer_username,
                    "date": dispute.creation_date or dispute.created_at,
                    "updated_at": dispute.updated_at,
                })
        except Exception as e:
            logger.warning(f"Failed to get recent disputes: {e}", exc_info=True)

        # Get recent inquiries
        try:
            inquiries = EbayInquiryRepository.list_inquiries(
                self.db, limit=limit, offset=0
            )
            for inq in inquiries:
                activities.append({
                    "type": "inquiry",
                    "id": inq.id,
                    "external_id": inq.inquiry_id,
                    "order_id": inq.order_id,
                    "status": inq.inquiry_status,
                    "amount": inq.claim_amount,
                    "currency": inq.claim_currency,
                    "buyer_username": inq.buyer_username,
                    "date": inq.creation_date or inq.created_at,
                    "updated_at": inq.updated_at,
                })
        except Exception as e:
            logger.warning(f"Failed to get recent inquiries: {e}", exc_info=True)

        # Sort by updated_at descending and limit
        activities.sort(key=lambda x: x.get("updated_at") or x.get("date"), reverse=True)

        return activities[:limit]
