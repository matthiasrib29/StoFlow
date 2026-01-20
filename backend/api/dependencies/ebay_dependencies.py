"""
eBay Service Dependencies

FastAPI dependencies for injecting eBay services into route handlers.
Uses factory pattern to create services with proper DB session and user context.

Benefits:
- Reduces boilerplate in route handlers (no manual service instantiation)
- Consistent service initialization across endpoints
- Easy to test (mock at dependency level)

Usage:
    @router.get("/payment-disputes")
    def list_disputes(
        service: EbayPaymentDisputeService = Depends(get_payment_dispute_service)
    ):
        return service.list_disputes()

Created: 2026-01-20
Author: Claude
"""

from typing import Tuple

from fastapi import Depends
from sqlalchemy.orm import Session

from api.dependencies import get_user_db
from models.public.user import User
from services.ebay.ebay_cancellation_service import EbayCancellationService
from services.ebay.ebay_inquiry_service import EbayInquiryService
from services.ebay.ebay_payment_dispute_service import EbayPaymentDisputeService
from services.ebay.ebay_refund_service import EbayRefundService
from services.ebay.ebay_return_service import EbayReturnService
from services.ebay.ebay_importer import EbayImporter
from services.ebay.ebay_link_service import EbayLinkService


def get_payment_dispute_service(
    db_user: Tuple[Session, User] = Depends(get_user_db),
) -> EbayPaymentDisputeService:
    """
    Factory for EbayPaymentDisputeService.

    Returns:
        Configured EbayPaymentDisputeService instance
    """
    db, user = db_user
    return EbayPaymentDisputeService(db, user.id)


def get_return_service(
    db_user: Tuple[Session, User] = Depends(get_user_db),
) -> EbayReturnService:
    """
    Factory for EbayReturnService.

    Returns:
        Configured EbayReturnService instance
    """
    db, user = db_user
    return EbayReturnService(db, user.id)


def get_cancellation_service(
    db_user: Tuple[Session, User] = Depends(get_user_db),
) -> EbayCancellationService:
    """
    Factory for EbayCancellationService.

    Returns:
        Configured EbayCancellationService instance
    """
    db, user = db_user
    return EbayCancellationService(db, user.id)


def get_inquiry_service(
    db_user: Tuple[Session, User] = Depends(get_user_db),
) -> EbayInquiryService:
    """
    Factory for EbayInquiryService.

    Returns:
        Configured EbayInquiryService instance
    """
    db, user = db_user
    return EbayInquiryService(db, user.id)


def get_refund_service(
    db_user: Tuple[Session, User] = Depends(get_user_db),
) -> EbayRefundService:
    """
    Factory for EbayRefundService.

    Returns:
        Configured EbayRefundService instance
    """
    db, user = db_user
    return EbayRefundService(db, user.id)


def get_ebay_importer(
    db_user: Tuple[Session, User] = Depends(get_user_db),
) -> EbayImporter:
    """
    Factory for EbayImporter.

    Returns:
        Configured EbayImporter instance
    """
    db, user = db_user
    return EbayImporter(db)


def get_ebay_link_service(
    db_user: Tuple[Session, User] = Depends(get_user_db),
) -> EbayLinkService:
    """
    Factory for EbayLinkService.

    Returns:
        Configured EbayLinkService instance
    """
    db, user = db_user
    return EbayLinkService(db, user.id)


# Export user context separately when needed
def get_db_and_user(
    db_user: Tuple[Session, User] = Depends(get_user_db),
) -> Tuple[Session, User]:
    """
    Get DB session and user for endpoints that need both.

    Use this when you need raw DB access alongside a service,
    or when the endpoint doesn't use a specific service.

    Returns:
        Tuple of (Session, User)
    """
    return db_user
