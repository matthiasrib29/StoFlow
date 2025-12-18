"""
eBay OAuth Configuration.

Centralise la configuration OAuth eBay (URLs, Scopes, Credentials).

Author: Claude
Date: 2025-12-12
"""

import os
from dataclasses import dataclass
from typing import List, Tuple

from fastapi import HTTPException, status


# ========== OAUTH URLS ==========

# Production
EBAY_OAUTH_BASE_URL = "https://auth.ebay.com/oauth2/authorize"
EBAY_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"

# Sandbox (pour tests)
EBAY_SANDBOX_OAUTH_BASE_URL = "https://auth.sandbox.ebay.com/oauth2/authorize"
EBAY_SANDBOX_TOKEN_URL = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"


# ========== SCOPES ==========

EBAY_SCOPES: List[str] = [
    "https://api.ebay.com/oauth/api_scope",  # Trading API (accès de base)
    "https://api.ebay.com/oauth/api_scope/sell.inventory",  # Inventory API
    "https://api.ebay.com/oauth/api_scope/sell.marketing",  # Marketing API
    "https://api.ebay.com/oauth/api_scope/sell.account",  # Account API
    "https://api.ebay.com/oauth/api_scope/sell.fulfillment",  # Fulfillment API
    "https://api.ebay.com/oauth/api_scope/sell.analytics.readonly",  # Analytics API
    "https://api.ebay.com/oauth/api_scope/commerce.identity.readonly",  # Identity API
]


# ========== CREDENTIALS ==========

@dataclass
class EbayOAuthCredentials:
    """eBay OAuth credentials."""
    client_id: str
    client_secret: str
    redirect_uri: str


def get_ebay_credentials(sandbox: bool = False) -> EbayOAuthCredentials:
    """
    Récupère les credentials eBay depuis environment variables.

    Args:
        sandbox: Si True, utilise les credentials sandbox

    Returns:
        EbayOAuthCredentials with client_id, client_secret, redirect_uri

    Raises:
        HTTPException: Si credentials manquants
    """
    if sandbox:
        client_id = os.getenv("EBAY_SANDBOX_CLIENT_ID")
        client_secret = os.getenv("EBAY_SANDBOX_CLIENT_SECRET")
        redirect_uri = os.getenv("EBAY_SANDBOX_REDIRECT_URI")
        env_prefix = "EBAY_SANDBOX_"
    else:
        client_id = os.getenv("EBAY_CLIENT_ID")
        client_secret = os.getenv("EBAY_CLIENT_SECRET")
        redirect_uri = os.getenv("EBAY_REDIRECT_URI")
        env_prefix = "EBAY_"

    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{env_prefix}CLIENT_ID not configured in environment",
        )

    if not client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{env_prefix}CLIENT_SECRET not configured in environment",
        )

    if not redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{env_prefix}REDIRECT_URI not configured in environment",
        )

    return EbayOAuthCredentials(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    )


def get_oauth_urls(sandbox: bool = False) -> Tuple[str, str]:
    """
    Retourne les URLs OAuth selon l'environnement.

    Args:
        sandbox: Si True, retourne URLs sandbox

    Returns:
        Tuple (auth_url, token_url)
    """
    if sandbox:
        return EBAY_SANDBOX_OAUTH_BASE_URL, EBAY_SANDBOX_TOKEN_URL
    return EBAY_OAUTH_BASE_URL, EBAY_TOKEN_URL


__all__ = [
    "EBAY_SCOPES",
    "EbayOAuthCredentials",
    "get_ebay_credentials",
    "get_oauth_urls",
]
