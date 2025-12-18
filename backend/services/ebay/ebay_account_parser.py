"""
eBay Account Info Parser.

Parse les informations de compte eBay depuis les APIs Identity et Trading.

Author: Claude
Date: 2025-12-12
"""

from typing import Any, Dict, Optional

from models.user.ebay_credentials import EbayCredentials
from shared.logging_setup import get_logger

logger = get_logger(__name__)


def parse_phone_number(phone_data: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Parse un numéro de téléphone depuis le format eBay.

    Args:
        phone_data: Dict avec countryCode et number

    Returns:
        Numéro formaté ou None
    """
    if not phone_data:
        return None

    country_code = phone_data.get("countryCode", "")
    number = phone_data.get("number", "")

    if country_code or number:
        return f"+{country_code} {number}".strip()
    return None


def parse_address(address_data: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Parse une adresse depuis le format eBay.

    Args:
        address_data: Dict avec addressLine1, addressLine2, postalCode, city, country

    Returns:
        Adresse formatée ou None
    """
    if not address_data:
        return None

    address_parts = [
        address_data.get("addressLine1"),
        address_data.get("addressLine2"),
        f"{address_data.get('postalCode', '')} {address_data.get('city', '')}".strip(),
        address_data.get("country"),
    ]

    filtered_parts = [p for p in address_parts if p]
    if filtered_parts:
        return ", ".join(filtered_parts)
    return None


def parse_business_account(
    business_data: Dict[str, Any],
    ebay_creds: EbayCredentials,
) -> None:
    """
    Parse les données d'un compte Business eBay.

    Args:
        business_data: Données du businessAccount
        ebay_creds: Credentials à mettre à jour (in-place)
    """
    ebay_creds.business_name = business_data.get("name")
    ebay_creds.email = ebay_creds.email or business_data.get("email")

    # Téléphone
    phone = parse_phone_number(business_data.get("primaryPhone"))
    if phone:
        ebay_creds.phone = phone

    # Adresse
    address = parse_address(business_data.get("address"))
    if address:
        ebay_creds.address = address

    # Contact principal
    primary_contact = business_data.get("primaryContact")
    if primary_contact:
        ebay_creds.first_name = primary_contact.get("firstName")
        ebay_creds.last_name = primary_contact.get("lastName")


def parse_individual_account(
    individual_data: Dict[str, Any],
    ebay_creds: EbayCredentials,
) -> None:
    """
    Parse les données d'un compte Individual eBay.

    Args:
        individual_data: Données du individualAccount
        ebay_creds: Credentials à mettre à jour (in-place)
    """
    ebay_creds.first_name = individual_data.get("firstName")
    ebay_creds.last_name = individual_data.get("lastName")
    ebay_creds.email = ebay_creds.email or individual_data.get("email")

    # Téléphone
    phone = parse_phone_number(individual_data.get("primaryPhone"))
    if phone:
        ebay_creds.phone = phone

    # Adresse
    address = parse_address(individual_data.get("registrationAddress"))
    if address:
        ebay_creds.address = address


def parse_trading_api_info(
    trading_info: Dict[str, Any],
    ebay_creds: EbayCredentials,
) -> None:
    """
    Parse les données de réputation depuis Trading API.

    Args:
        trading_info: Données Trading API
        ebay_creds: Credentials à mettre à jour (in-place)
    """
    if "feedback_score" in trading_info:
        ebay_creds.feedback_score = trading_info.get("feedback_score", 0)

    if "positive_feedback_percent" in trading_info:
        ebay_creds.feedback_percentage = trading_info.get("positive_feedback_percent", 0.0)

    if "registration_date" in trading_info:
        ebay_creds.registration_date = trading_info.get("registration_date")

    if "top_rated_seller" in trading_info:
        ebay_creds.seller_level = (
            "top_rated" if trading_info.get("top_rated_seller") else "standard"
        )


def update_ebay_credentials_from_seller_info(
    seller_info: Dict[str, Any],
    ebay_creds: EbayCredentials,
) -> None:
    """
    Met à jour les credentials eBay depuis les infos seller combinées.

    Combine les données de Commerce Identity API et Trading API.

    Args:
        seller_info: Données combinées Identity + Trading
        ebay_creds: Credentials à mettre à jour (in-place)
    """
    if not seller_info:
        return

    # Données de base
    ebay_creds.ebay_user_id = seller_info.get("userId", ebay_creds.ebay_user_id)
    ebay_creds.username = seller_info.get("username")
    ebay_creds.email = seller_info.get("email")
    ebay_creds.account_type = seller_info.get("accountType")
    ebay_creds.marketplace = seller_info.get("registrationMarketplaceId")

    # Business Account
    if seller_info.get("businessAccount"):
        parse_business_account(seller_info["businessAccount"], ebay_creds)

    # Individual Account
    elif seller_info.get("individualAccount"):
        parse_individual_account(seller_info["individualAccount"], ebay_creds)

    # Réputation vendeur (depuis Trading API)
    parse_trading_api_info(seller_info, ebay_creds)

    logger.debug(f"Updated eBay credentials for user_id={ebay_creds.ebay_user_id}")


__all__ = [
    "parse_phone_number",
    "parse_address",
    "parse_business_account",
    "parse_individual_account",
    "parse_trading_api_info",
    "update_ebay_credentials_from_seller_info",
]
