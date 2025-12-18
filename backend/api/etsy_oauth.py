"""
API OAuth2 Routes pour Etsy.

Endpoints pour le flow OAuth2 Etsy (avec PKCE):
1. /connect - Génère authorization URL
2. /callback - Reçoit authorization code et échange contre tokens
3. /disconnect - Déconnecte le compte Etsy

Documentation: https://developer.etsy.com/documentation/essentials/authentication/

Author: Claude
Date: 2025-12-10
"""

import hashlib
import os
import secrets
from base64 import urlsafe_b64encode
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from models.public.platform_mapping import PlatformMapping
from models.public.user import User
from shared.config import settings
from shared.logging_setup import get_logger

router = APIRouter(prefix="/etsy/oauth", tags=["Etsy OAuth"])
logger = get_logger(__name__)

# Etsy OAuth2 URLs
ETSY_AUTHORIZE_URL = "https://www.etsy.com/oauth/connect"
ETSY_TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"

# Temporary storage for PKCE verifiers (in production, use Redis)
# Format: {state: code_verifier}
PKCE_VERIFIERS = {}


# ========== PYDANTIC SCHEMAS ==========


class ConnectResponse(BaseModel):
    """Response avec l'URL d'autorisation Etsy."""

    authorization_url: str
    state: str


class CallbackResponse(BaseModel):
    """Response après callback OAuth2."""

    success: bool
    shop_id: Optional[str] = None
    shop_name: Optional[str] = None
    access_token_expires_at: Optional[str] = None
    error: Optional[str] = None


class DisconnectResponse(BaseModel):
    """Response après déconnexion."""

    success: bool
    message: str


# ========== HELPER FUNCTIONS ==========


def generate_code_verifier() -> str:
    """
    Génère un code verifier pour PKCE.

    Returns:
        Code verifier (43-128 chars, url-safe base64)
    """
    # Generate 32 random bytes
    random_bytes = secrets.token_bytes(32)

    # Encode to url-safe base64 (without padding)
    code_verifier = urlsafe_b64encode(random_bytes).decode("utf-8").rstrip("=")

    return code_verifier


def generate_code_challenge(code_verifier: str) -> str:
    """
    Génère un code challenge à partir du verifier.

    Args:
        code_verifier: Code verifier

    Returns:
        Code challenge (SHA256 hash, url-safe base64)
    """
    # SHA256 hash
    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()

    # Encode to url-safe base64 (without padding)
    code_challenge = urlsafe_b64encode(digest).decode("utf-8").rstrip("=")

    return code_challenge


# ========== ROUTES ==========


@router.get("/connect", response_model=ConnectResponse)
def connect_etsy_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Génère l'URL d'autorisation Etsy OAuth2 avec PKCE.

    **Flow:**
    1. Générer code_verifier et code_challenge (PKCE)
    2. Générer state (CSRF protection)
    3. Stocker code_verifier temporairement
    4. Rediriger user vers Etsy

    **Configuration requise:**
    Dans .env:
    - ETSY_API_KEY (Client ID)
    - ETSY_API_SECRET (Client Secret)
    - ETSY_REDIRECT_URI (ex: http://localhost:3000/etsy/callback)

    Returns:
        URL d'autorisation Etsy + state

    Examples:
        >>> # Frontend:
        >>> response = await fetch('/api/etsy/oauth/connect')
        >>> window.location.href = response.authorization_url
    """
    # Get Etsy credentials from env
    client_id = os.getenv("ETSY_API_KEY")
    redirect_uri = os.getenv("ETSY_REDIRECT_URI")

    if not client_id or not redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Etsy OAuth2 not configured. Please set ETSY_API_KEY and ETSY_REDIRECT_URI in .env",
        )

    # Generate PKCE verifier and challenge
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)

    # Generate state (CSRF protection)
    state = secrets.token_urlsafe(32)

    # Store code_verifier temporarily (keyed by state)
    PKCE_VERIFIERS[state] = code_verifier

    # Build authorization URL
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "listings_r listings_w listings_d transactions_r transactions_w shops_r shops_w email_r",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    authorization_url = f"{ETSY_AUTHORIZE_URL}?{urlencode(params)}"

    logger.info(f"Generated Etsy authorization URL for user {current_user.id}")

    return ConnectResponse(
        authorization_url=authorization_url,
        state=state,
    )


@router.get("/callback", response_model=CallbackResponse)
def etsy_oauth_callback(
    code: str = Query(..., description="Authorization code from Etsy"),
    state: str = Query(..., description="State parameter (CSRF protection)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Callback OAuth2 Etsy - Échange authorization code contre tokens.

    **Flow:**
    1. Vérifier state (CSRF protection)
    2. Récupérer code_verifier depuis storage
    3. Échanger code + code_verifier contre tokens
    4. Sauvegarder tokens en DB
    5. Récupérer shop_id

    Args:
        code: Authorization code from Etsy
        state: State parameter

    Returns:
        Success status + shop info

    Raises:
        HTTPException 400: Si state invalide
        HTTPException 500: Si erreur OAuth2

    Examples:
        >>> # Etsy redirige vers: http://localhost:3000/etsy/callback?code=XXX&state=YYY
        >>> # Frontend call API:
        >>> response = await fetch(`/api/etsy/oauth/callback?code=${code}&state=${state}`)
    """
    # Get Etsy credentials
    client_id = os.getenv("ETSY_API_KEY")
    redirect_uri = os.getenv("ETSY_REDIRECT_URI")

    if not client_id or not redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Etsy OAuth2 not configured",
        )

    # Retrieve code_verifier from temporary storage
    code_verifier = PKCE_VERIFIERS.pop(state, None)

    if not code_verifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter or PKCE verifier expired",
        )

    try:
        # Exchange code for tokens
        token_payload = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "code": code,
            "code_verifier": code_verifier,
        }

        response = requests.post(ETSY_TOKEN_URL, data=token_payload, timeout=30)

        if response.status_code != 200:
            error_text = response.text
            logger.error(f"Etsy token exchange failed: {error_text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Token exchange failed: {error_text}",
            )

        token_data = response.json()

        # Extract tokens
        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]
        expires_in = token_data["expires_in"]  # Seconds (3600)

        # Calculate expiry dates
        now = datetime.now(timezone.utc)
        access_token_expires_at = now + timedelta(seconds=expires_in)
        refresh_token_expires_at = now + timedelta(days=90)

        # Get shop_id from token (user_id is prefixed to refresh_token)
        # Format: {shop_id}.{random_string}
        shop_id = refresh_token.split(".")[0] if "." in refresh_token else None

        # Save or update in DB
        mapping = (
            db.query(PlatformMapping)
            .filter(
                PlatformMapping.user_id == current_user.id,
                PlatformMapping.platform == "etsy",
            )
            .first()
        )

        if mapping:
            # Update existing
            mapping.access_token = access_token
            mapping.refresh_token = refresh_token
            mapping.access_token_expires_at = access_token_expires_at
            mapping.refresh_token_expires_at = refresh_token_expires_at
            mapping.shop_id = shop_id
            mapping.api_key = client_id  # Store client_id for future use
        else:
            # Create new
            mapping = PlatformMapping(
                user_id=current_user.id,
                platform="etsy",
                access_token=access_token,
                refresh_token=refresh_token,
                access_token_expires_at=access_token_expires_at,
                refresh_token_expires_at=refresh_token_expires_at,
                shop_id=shop_id,
                api_key=client_id,
            )
            db.add(mapping)

        db.commit()
        db.refresh(mapping)

        logger.info(f"✅ Etsy account connected for user {current_user.id}, shop_id={shop_id}")

        return CallbackResponse(
            success=True,
            shop_id=shop_id,
            shop_name=mapping.shop_name,
            access_token_expires_at=access_token_expires_at.isoformat(),
            error=None,
        )

    except Exception as e:
        logger.error(f"Error in Etsy OAuth callback: {e}")
        return CallbackResponse(
            success=False,
            shop_id=None,
            shop_name=None,
            access_token_expires_at=None,
            error=str(e),
        )


@router.post("/disconnect", response_model=DisconnectResponse)
def disconnect_etsy_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Déconnecte le compte Etsy de l'utilisateur.

    Supprime les credentials Etsy de la DB.

    Returns:
        Confirmation de déconnexion

    Examples:
        >>> response = await fetch('/api/etsy/oauth/disconnect', {method: 'POST'})
    """
    mapping = (
        db.query(PlatformMapping)
        .filter(
            PlatformMapping.user_id == current_user.id,
            PlatformMapping.platform == "etsy",
        )
        .first()
    )

    if not mapping:
        return DisconnectResponse(
            success=True,
            message="Etsy account was not connected",
        )

    db.delete(mapping)
    db.commit()

    logger.info(f"✅ Etsy account disconnected for user {current_user.id}")

    return DisconnectResponse(
        success=True,
        message="Etsy account disconnected successfully",
    )
