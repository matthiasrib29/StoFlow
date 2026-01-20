"""
eBay OAuth Dependencies

Helpers and factories for eBay OAuth routes.
"""

from typing import Optional, Tuple

from fastapi import Depends
from sqlalchemy.orm import Session

from api.dependencies import get_user_db
from models.public.user import User
from models.user.ebay_credentials import EbayCredentials
from services.ebay.ebay_account_client import EbayAccountClient
from shared.exceptions import EbayError


def get_ebay_policies(
    db: Session,
    user_id: int,
    policy_type: str,
    marketplace_id: str = "EBAY_FR",
) -> list:
    """
    Get eBay policies by type.

    Args:
        db: Database session
        user_id: User ID
        policy_type: Policy type (shipping, return, payment)
        marketplace_id: eBay marketplace ID

    Returns:
        List of policies or empty list if not connected
    """
    ebay_creds = db.query(EbayCredentials).first()

    if not ebay_creds or not ebay_creds.get_access_token():
        return []

    try:
        client = EbayAccountClient(db, user_id=user_id, marketplace_id=marketplace_id)

        if policy_type == "shipping":
            policies = client.get_fulfillment_policies()
            return policies.get("fulfillmentPolicies", [])
        elif policy_type == "return":
            policies = client.get_return_policies()
            return policies.get("returnPolicies", [])
        elif policy_type == "payment":
            policies = client.get_payment_policies()
            return policies.get("paymentPolicies", [])
        else:
            return []

    except (EbayError, ValueError):
        return []
