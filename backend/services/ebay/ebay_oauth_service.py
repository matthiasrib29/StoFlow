"""
eBay OAuth Service.

Gère la logique OAuth eBay (token exchange, refresh, validation).

Author: Claude
Date: 2025-12-12
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests
from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from models.user.ebay_credentials import EbayCredentials
from services.ebay.ebay_oauth_config import (
    EBAY_SCOPES,
    get_ebay_credentials,
    get_oauth_urls,
)
from services.ebay.ebay_account_parser import update_ebay_credentials_from_seller_info
from shared.logging_setup import get_logger

logger = get_logger(__name__)


# ========== STATE MANAGEMENT ==========


def generate_state(user_id: int) -> str:
    """
    Génère un state pour CSRF protection.

    Format: {user_id}:{random_token}

    Args:
        user_id: ID du user

    Returns:
        str: State token
    """
    random_token = secrets.token_urlsafe(32)
    return f"{user_id}:{random_token}"


def validate_state(state: str, expected_user_id: int) -> bool:
    """
    Valide le state reçu dans le callback.

    Args:
        state: State token reçu
        expected_user_id: User ID attendu

    Returns:
        bool: True si valide
    """
    try:
        user_id_str, _ = state.split(":", 1)
        return int(user_id_str) == expected_user_id
    except (ValueError, TypeError):
        return False


def extract_user_id_from_state(state: str) -> int:
    """
    Extrait le user_id depuis le state token.

    Args:
        state: State token format "user_id:random_token"

    Returns:
        int: User ID

    Raises:
        HTTPException: Si format invalide
    """
    try:
        user_id_str, _ = state.split(":", 1)
        return int(user_id_str)
    except (ValueError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter format",
        )


# ========== AUTH URL GENERATION ==========


def generate_auth_url(user_id: int, sandbox: bool = False) -> Dict[str, str]:
    """
    Génère l'URL d'autorisation eBay OAuth2.

    Args:
        user_id: ID utilisateur Stoflow
        sandbox: Si True, utilise eBay Sandbox

    Returns:
        Dict avec auth_url et state
    """
    credentials = get_ebay_credentials(sandbox=sandbox)
    oauth_base_url, _ = get_oauth_urls(sandbox=sandbox)
    state = generate_state(user_id)

    params = {
        "client_id": credentials.client_id,
        "redirect_uri": credentials.redirect_uri,
        "response_type": "code",
        "scope": " ".join(EBAY_SCOPES),
        "state": state,
    }

    auth_url = f"{oauth_base_url}?{urlencode(params)}"

    logger.info(f"eBay OAuth URL generated for user {user_id}, sandbox={sandbox}")

    return {"auth_url": auth_url, "state": state}


# ========== TOKEN EXCHANGE ==========


def exchange_code_for_tokens(
    code: str,
    sandbox: bool = False,
) -> Dict[str, Any]:
    """
    Échange le code d'autorisation contre access_token + refresh_token.

    Args:
        code: Authorization code from eBay
        sandbox: Si True, utilise sandbox

    Returns:
        Dict avec tokens et expiration

    Raises:
        HTTPException: Si échange échoue
    """
    credentials = get_ebay_credentials(sandbox=sandbox)
    _, token_url = get_oauth_urls(sandbox=sandbox)

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": credentials.redirect_uri,
    }

    try:
        response = requests.post(
            token_url,
            auth=(credentials.client_id, credentials.client_secret),
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )

        if not response.ok:
            error_data = response.text
            try:
                error_data = response.json()
            except (ValueError, requests.exceptions.JSONDecodeError):
                pass

            logger.error(f"eBay token exchange failed: {error_data}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"eBay token exchange failed: {error_data}",
            )

        token_data = response.json()

        # Calculate expiration timestamps
        now = datetime.now(timezone.utc)
        expires_in = token_data["expires_in"]  # seconds (7200 = 2h)
        refresh_token_expires_in = token_data.get("refresh_token_expires_in", 47304000)  # 18 mois

        return {
            "access_token": token_data["access_token"],
            "refresh_token": token_data["refresh_token"],
            "access_token_expires_at": now + timedelta(seconds=expires_in),
            "refresh_token_expires_at": now + timedelta(seconds=refresh_token_expires_in),
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during token exchange: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Network error during token exchange: {str(e)}",
        )


# ========== CREDENTIALS STORAGE ==========


def save_tokens_to_db(
    db: Session,
    tokens: Dict[str, Any],
    sandbox: bool,
) -> EbayCredentials:
    """
    Sauvegarde les tokens OAuth dans ebay_credentials.

    Args:
        db: Session DB (avec search_path déjà configuré)
        tokens: Dict avec access_token, refresh_token, expiration dates
        sandbox: Mode sandbox

    Returns:
        EbayCredentials mis à jour
    """
    ebay_creds = db.query(EbayCredentials).first()

    if not ebay_creds:
        ebay_creds = EbayCredentials(
            sandbox_mode=sandbox,
            is_connected=True,
        )
        # Use secure setters for tokens (Security 2026-01-12)
        ebay_creds.set_access_token(tokens["access_token"])
        ebay_creds.set_refresh_token(tokens["refresh_token"])
        ebay_creds.access_token_expires_at = tokens["access_token_expires_at"]
        ebay_creds.refresh_token_expires_at = tokens["refresh_token_expires_at"]
        db.add(ebay_creds)
    else:
        # Use secure setters for tokens (Security 2026-01-12)
        ebay_creds.set_access_token(tokens["access_token"])
        ebay_creds.set_refresh_token(tokens["refresh_token"])
        ebay_creds.access_token_expires_at = tokens["access_token_expires_at"]
        ebay_creds.refresh_token_expires_at = tokens["refresh_token_expires_at"]
        ebay_creds.sandbox_mode = sandbox
        ebay_creds.is_connected = True

    db.commit()
    db.refresh(ebay_creds)

    logger.info("eBay tokens saved to database")

    return ebay_creds


# ========== ACCOUNT INFO FETCHING ==========


def fetch_and_save_account_info(
    db: Session,
    user_id: int,
    ebay_creds: EbayCredentials,
    schema_name: Optional[str] = None,
) -> None:
    """
    Récupère et sauvegarde les infos du compte eBay.

    Combine Commerce Identity API et Trading API.

    Args:
        db: Session DB
        user_id: User ID
        ebay_creds: Credentials à mettre à jour
        schema_name: Schema name pour search_path
    """
    try:
        from services.ebay.ebay_identity_client import EbayIdentityClient
        from services.ebay.ebay_trading_client import EbayTradingClient

        # Set schema for multi-tenant isolation (survives commit/rollback)
        db = db.execution_options(
            schema_translate_map={"tenant": f"user_{user_id}"}
        )

        seller_info = {}

        # 1. Commerce Identity API
        try:
            identity_client = EbayIdentityClient(db, user_id=user_id)
            identity_info = identity_client.get_user_safe()
            if identity_info:
                seller_info.update(identity_info)
        except Exception as e:
            logger.warning(f"Commerce Identity API failed: {type(e).__name__}: {e}")

        # 2. Trading API
        try:
            trading_client = EbayTradingClient(db, user_id=user_id)
            trading_info = trading_client.get_user_safe()
            if trading_info:
                seller_info.update(trading_info)
        except Exception as e:
            logger.warning(f"Trading API failed: {type(e).__name__}: {e}")

        # 3. Update credentials
        if seller_info:
            update_ebay_credentials_from_seller_info(seller_info, ebay_creds)
            db.commit()
            logger.info(f"eBay account info saved for user {user_id}")

    except Exception as e:
        logger.warning(f"Failed to fetch eBay account info: {type(e).__name__}: {e}")


# ========== MAIN OAUTH CALLBACK PROCESSING ==========


def process_oauth_callback(
    code: str,
    state: str,
    user_id: int,
    sandbox: bool,
    db: Session,
    schema_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Traite le callback OAuth eBay complet.

    1. Valide le state (CSRF)
    2. Échange code contre tokens
    3. Sauvegarde tokens en DB
    4. Récupère infos compte

    Args:
        code: Authorization code from eBay
        state: State token pour validation
        user_id: User ID
        sandbox: Mode sandbox
        db: Session DB
        schema_name: Schema name pour search_path

    Returns:
        Dict avec success, message, expiration dates

    Raises:
        HTTPException: Si validation ou échange échoue
    """
    # Set schema for multi-tenant isolation (survives commit/rollback)
    db = db.execution_options(
        schema_translate_map={"tenant": f"user_{user_id}"}
    )

    # Validate state (CSRF protection)
    if not validate_state(state, user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter (CSRF protection)",
        )

    # Exchange code for tokens
    tokens = exchange_code_for_tokens(code, sandbox=sandbox)

    # Save tokens to DB
    ebay_creds = save_tokens_to_db(db, tokens, sandbox)

    # Fetch and save account info (non-blocking)
    # Note: execution_options already applied, fetch_and_save_account_info will reapply
    fetch_and_save_account_info(db, user_id, ebay_creds, schema_name)

    return {
        "success": True,
        "message": "eBay account connected successfully",
        "access_token_expires_at": tokens["access_token_expires_at"].isoformat(),
        "refresh_token_expires_at": tokens["refresh_token_expires_at"].isoformat(),
    }


__all__ = [
    "generate_state",
    "validate_state",
    "extract_user_id_from_state",
    "generate_auth_url",
    "exchange_code_for_tokens",
    "save_tokens_to_db",
    "fetch_and_save_account_info",
    "process_oauth_callback",
]
