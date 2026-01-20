"""
API Routes eBay OAuth.

Gère le flow OAuth2 pour connecter un compte eBay user.

Flow:
1. GET /connect → génère auth URL et redirige user vers eBay
2. User autorise l'application sur eBay
3. eBay redirige vers GET /callback avec code
4. Backend échange code contre access_token + refresh_token
5. Stocke tokens dans ebay_credentials

Author: Claude
Date: 2025-12-10
Refactored: 2025-12-12
"""

from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db, get_user_db
from api.dependencies.ebay_oauth_dependencies import get_ebay_policies
from models.public.user import User
from models.user.ebay_credentials import EbayCredentials
from shared.exceptions import EbayError
from shared.html_templates import build_oauth_success_html, build_oauth_error_html
from services.ebay.ebay_oauth_service import (
    extract_user_id_from_state,
    generate_auth_url,
    process_oauth_callback,
)

router = APIRouter(prefix="/ebay", tags=["eBay OAuth"])


# ========== PYDANTIC SCHEMAS ==========


class EbayOAuthUrlResponse(BaseModel):
    """Response avec l'URL d'autorisation eBay."""

    auth_url: str
    state: str


class EbayOAuthCallbackResponse(BaseModel):
    """Response après callback OAuth."""

    success: bool
    message: str
    access_token_expires_at: Optional[str] = None
    refresh_token_expires_at: Optional[str] = None


class EbayManualCodeSubmission(BaseModel):
    """Request body pour soumettre manuellement le code OAuth."""

    code: str
    state: str
    sandbox: bool = False


# ========== ROUTES ==========


@router.get("/connect", response_model=EbayOAuthUrlResponse)
def connect_ebay(
    sandbox: bool = Query(False, description="Utiliser eBay Sandbox pour tests"),
    current_user: User = Depends(get_current_user),
):
    """
    Genere l'URL d'autorisation eBay OAuth2.

    Args:
        sandbox: Si True, utilise eBay Sandbox
        current_user: User authentifie

    Returns:
        EbayOAuthUrlResponse: URL d'autorisation + state
    """
    result = generate_auth_url(current_user.id, sandbox=sandbox)
    return EbayOAuthUrlResponse(**result)


@router.post("/submit-code", response_model=EbayOAuthCallbackResponse)
def submit_manual_code(
    data: EbayManualCodeSubmission,
    db_user: tuple[Session, User] = Depends(get_user_db),
):
    """
    Soumet manuellement le code d'autorisation eBay.

    Utilise quand le redirect URI est configure avec les URLs par defaut eBay.

    Args:
        data: Code et state depuis l'URL eBay
        db_user: Tuple (Session DB, User authentifie)

    Returns:
        EbayOAuthCallbackResponse: Success status + token expiration
    """
    db, current_user = db_user
    result = process_oauth_callback(
        code=data.code,
        state=data.state,
        user_id=current_user.id,
        sandbox=data.sandbox,
        db=db,
        schema_name=current_user.schema_name,
    )
    return EbayOAuthCallbackResponse(**result)


@router.get("/callback")
def ebay_callback(
    code: str = Query(..., description="Authorization code from eBay"),
    state: str = Query(..., description="State token for CSRF protection"),
    sandbox: bool = Query(False, description="Whether using sandbox"),
    db: Session = Depends(get_db),
):
    """
    Callback OAuth2 eBay.

    Note: Cette route ne necessite PAS d'authentification JWT car
    eBay fait une simple redirection GET sans headers.

    Args:
        code: Authorization code from eBay
        state: State token contenant user_id
        sandbox: Si True, utilise sandbox
        db: Session DB

    Returns:
        HTMLResponse: Page qui ferme la popup et notifie le parent
    """
    try:
        # Extract user_id from state
        user_id = extract_user_id_from_state(state)

        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Set schema for multi-tenant isolation (survives commit/rollback)
        from shared.schema import configure_schema_translate_map
        configure_schema_translate_map(db, f"user_{user_id}")

        # Define schema_name for multi-tenant isolation
        schema_name = user.schema_name

        # Process OAuth callback
        result = process_oauth_callback(
            code=code,
            state=state,
            user_id=user_id,
            sandbox=sandbox,
            db=db,
            schema_name=schema_name,
        )

        return HTMLResponse(content=build_oauth_success_html(result, "eBay"))

    except HTTPException:
        raise
    except Exception as e:
        return HTMLResponse(
            content=build_oauth_error_html(str(e), "eBay"),
            status_code=500,
        )


@router.post("/disconnect")
def disconnect_ebay(
    db_user: tuple[Session, User] = Depends(get_user_db),
):
    """
    Deconnecte le compte eBay du user.

    Args:
        db_user: Tuple (Session DB, User authentifie)

    Returns:
        dict: Success status
    """
    db, _ = db_user
    ebay_creds = db.query(EbayCredentials).first()

    if not ebay_creds:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="eBay account not connected",
        )

    # Clear tokens (using secure setters)
    ebay_creds.set_access_token(None)
    ebay_creds.set_refresh_token(None)
    ebay_creds.access_token_expires_at = None
    ebay_creds.refresh_token_expires_at = None
    ebay_creds.is_connected = False

    db.commit()

    return {"success": True, "message": "eBay account disconnected successfully"}


@router.get("/status")
def ebay_connection_status(
    db_user: tuple[Session, User] = Depends(get_user_db),
):
    """
    Verifie si le user a connecte son compte eBay.

    Args:
        db_user: Tuple (Session DB, User authentifie)

    Returns:
        dict: Connection status + expiration info
    """
    db, _ = db_user
    ebay_creds = db.query(EbayCredentials).first()

    if not ebay_creds or not ebay_creds.get_access_token():
        return {"is_connected": False, "message": "eBay account not connected"}

    now = datetime.now(timezone.utc)

    access_token_valid = (
        ebay_creds.access_token_expires_at
        and ebay_creds.access_token_expires_at > now
    )
    refresh_token_valid = (
        ebay_creds.refresh_token_expires_at
        and ebay_creds.refresh_token_expires_at > now
    )

    return {
        "is_connected": True,
        "access_token_valid": access_token_valid,
        "refresh_token_valid": refresh_token_valid,
        "access_token_expires_at": (
            ebay_creds.access_token_expires_at.isoformat()
            if ebay_creds.access_token_expires_at
            else None
        ),
        "refresh_token_expires_at": (
            ebay_creds.refresh_token_expires_at.isoformat()
            if ebay_creds.refresh_token_expires_at
            else None
        ),
        "ebay_user_id": ebay_creds.ebay_user_id,
        "sandbox_mode": ebay_creds.sandbox_mode,
        "account_info": {
            "userId": ebay_creds.ebay_user_id,
            "username": ebay_creds.username,
            "email": ebay_creds.email,
            "accountType": ebay_creds.account_type,
            "marketplace": ebay_creds.marketplace,
            "businessName": ebay_creds.business_name,
            "firstName": ebay_creds.first_name,
            "lastName": ebay_creds.last_name,
            "phone": ebay_creds.phone,
            "address": ebay_creds.address,
            "feedbackScore": ebay_creds.feedback_score or 0,
            "feedbackPercentage": ebay_creds.feedback_percentage or 0.0,
            "sellerLevel": ebay_creds.seller_level,
            "registrationDate": ebay_creds.registration_date,
        },
    }


@router.get("/account-info")
def get_ebay_account_info(
    db_user: tuple[Session, User] = Depends(get_user_db),
):
    """
    Recupere les informations du compte eBay connecte.

    Retourne les programmes eBay auxquels le seller est inscrit.

    Args:
        db_user: Tuple (Session DB, User authentifie)

    Returns:
        dict: Account information from eBay API
    """
    from services.ebay.ebay_account_client import EbayAccountClient
    from services.ebay.ebay_identity_client import EbayIdentityClient
    from services.ebay.ebay_trading_client import EbayTradingClient
    from shared.logging import get_logger

    logger = get_logger(__name__)

    db, current_user = db_user
    ebay_creds = db.query(EbayCredentials).first()

    if not ebay_creds or not ebay_creds.get_access_token():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="eBay account not connected. Please connect first.",
        )

    # Check token validity
    now = datetime.now(timezone.utc)
    if ebay_creds.access_token_expires_at and ebay_creds.access_token_expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="eBay access token expired. Please reconnect your account.",
        )

    try:
        account_client = EbayAccountClient(db, user_id=current_user.id)
        identity_client = EbayIdentityClient(db, user_id=current_user.id)
        seller_info = {}

        # 1. Commerce Identity API
        try:
            identity_info = identity_client.get_user_safe()
            if identity_info:
                seller_info.update(identity_info)
        except Exception as e:
            logger.warning(f"Commerce Identity API failed: {type(e).__name__}: {e}")

        # 2. Trading API
        try:
            trading_client = EbayTradingClient(db, user_id=current_user.id)
            trading_info = trading_client.get_user_safe()
            if trading_info:
                seller_info.update(trading_info)
        except Exception as e:
            logger.warning(f"Trading API failed: {type(e).__name__}: {e}")

        if not seller_info:
            seller_info = None

        # Get programs
        programs = account_client.get_opted_in_programs()

        # Get fulfillment policies count
        try:
            fulfillment_policies = account_client.get_fulfillment_policies()
            fulfillment_count = fulfillment_policies.get("total", 0)
        except (EbayError, ValueError):
            fulfillment_count = None

        return {
            "success": True,
            "ebay_user_id": ebay_creds.ebay_user_id,
            "sandbox_mode": ebay_creds.sandbox_mode,
            "seller_info": seller_info,
            "programs": programs.get("programs", []),
            "fulfillment_policies_count": fulfillment_count,
            "access_token_expires_at": (
                ebay_creds.access_token_expires_at.isoformat()
                if ebay_creds.access_token_expires_at
                else None
            ),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch eBay account info: {str(e)}",
        )


@router.get("/policies/{policy_type}")
def get_policies(
    policy_type: Literal["shipping", "return", "payment"] = Path(..., description="Policy type"),
    marketplace_id: str = Query("EBAY_FR", description="Marketplace ID"),
    db_user: tuple[Session, User] = Depends(get_user_db),
):
    """
    Recupere les policies eBay par type.

    Args:
        policy_type: Type de policy (shipping, return, payment)
        marketplace_id: Marketplace ID (EBAY_FR, EBAY_DE, etc.)

    Returns:
        List of policies
    """
    db, current_user = db_user
    return get_ebay_policies(db, current_user.id, policy_type, marketplace_id)


@router.get("/stats")
def get_ebay_stats(
    db_user: tuple[Session, User] = Depends(get_user_db),
):
    """
    Recupere les statistiques eBay (stub).
    """
    db, _ = db_user
    ebay_creds = db.query(EbayCredentials).first()

    if not ebay_creds or not ebay_creds.get_access_token():
        return {
            "activeLis": 0,
            "totalViews": 0,
            "totalSales": 0,
            "totalRevenue": 0,
            "conversionRate": 0,
            "impressions": 0,
            "totalWatchers": 0,
            "averagePrice": 0,
        }

    # Return mock stats for now - can be enhanced later with real API calls
    return {
        "activeLis": 0,
        "totalViews": 0,
        "totalSales": 0,
        "totalRevenue": 0,
        "conversionRate": 0,
        "impressions": 0,
        "totalWatchers": 0,
        "averagePrice": 0,
    }
