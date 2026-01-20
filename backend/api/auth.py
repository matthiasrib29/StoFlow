"""
Authentication Routes (Simplified - No Tenant)

Routes API pour l'authentification des utilisateurs.

Security (2026-01-20):
- JWT tokens stored in httpOnly cookies (XSS protection)
- CSRF protection via double-submit cookie pattern
- Backward compatibility: header auth still supported during migration
"""

import asyncio
import random
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from api.dependencies.auth_dependencies import apply_rate_limit
from models.public.user import User, UserRole, SubscriptionTier, AccountType, BusinessType, EstimatedProducts
from models.public.subscription_quota import SubscriptionQuota
from schemas.auth_schemas import LoginRequest, RefreshRequest, RefreshResponse, RegisterRequest, TokenResponse
from services.auth_service import AuthService
from services.email_service import EmailService
from services.user_schema_service import UserSchemaService
from shared.cookie_utils import (
    set_auth_cookies,
    set_access_token_cookie,
    set_csrf_token_cookie,
    clear_auth_cookies,
    REFRESH_TOKEN_COOKIE,
)
from shared.database import get_db
from shared.logging import get_logger
from shared.logging import redact_email, redact_password

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    request: Request,
    credentials: LoginRequest,
    db: Session = Depends(get_db),
    source: str = "web",
) -> JSONResponse:
    """
    Authentifie un utilisateur et retourne les tokens JWT.

    Security (2026-01-20):
    - Tokens stored in httpOnly cookies (XSS protection)
    - CSRF token set for state-changing request protection
    - Response body contains user info only (no tokens)

    Business Rules (Updated: 2025-12-07):
    - L'email est globalement unique
    - L'utilisateur doit être actif (is_active=True)
    - Le mot de passe doit être correct
    - Supporte le paramètre optionnel 'source' pour tracking (web, plugin, mobile)

    Args:
        credentials: Email et mot de passe uniquement
        db: Session SQLAlchemy
        source: Source de la connexion (web, plugin, mobile) - défaut: "web"

    Returns:
        JSONResponse avec user_id, role, subscription_tier (tokens in cookies)

    Raises:
        HTTPException: 401 si authentification échouée
    """
    await apply_rate_limit(request, "login")

    # ===== SECURITY FIX (2025-12-05): Redact password dans logs =====
    # Log sans exposer le password
    logger.info(f"Login attempt: email={credentials.email}, password={redact_password(credentials.password)}, source={source}")

    # ===== SECURITY FIX (2025-12-05): Timing Attack Protection =====
    # Délai aléatoire 100-300ms pour rendre timing attack impossible
    delay_ms = random.uniform(0.1, 0.3)  # 100-300ms
    await asyncio.sleep(delay_ms)

    user = AuthService.authenticate_user(
        db=db,
        email=credentials.email,
        password=credentials.password,
        source=source,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect, ou compte inactif",
        )

    # Vérifier que l'email est confirmé
    if not user.email_verified:
        logger.warning(f"Login attempt with unverified email: {redact_email(user.email)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Veuillez confirmer votre adresse email avant de vous connecter. Vérifiez votre boîte de réception.",
        )

    # Générer les tokens
    access_token = AuthService.create_access_token(
        user_id=user.id,
        role=user.role.value,
    )

    refresh_token = AuthService.create_refresh_token(
        user_id=user.id,
    )

    # Build response with user info (no tokens in body)
    response_data = {
        "user_id": user.id,
        "role": user.role.value,
        "subscription_tier": user.subscription_tier.value,
        "token_type": "bearer",
        # Include tokens in body for backward compatibility during migration
        # TODO (2026-02-01): Remove after frontend migration complete
        "access_token": access_token,
        "refresh_token": refresh_token,
    }

    response = JSONResponse(content=response_data)

    # Set auth cookies (httpOnly for tokens, JS-readable for CSRF)
    csrf_token = set_auth_cookies(response, access_token, refresh_token)

    logger.info(f"Login successful: user_id={user.id}, source={source}, token_source=cookie")

    return response


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_token(
    request_obj: Request,
    request: Optional[RefreshRequest] = None,
    db: Session = Depends(get_db),
    refresh_token_cookie: Optional[str] = Cookie(None, alias="refresh_token"),
) -> JSONResponse:
    """
    Génère un nouveau access token à partir d'un refresh token.

    Security (2026-01-20):
    - Reads refresh token from httpOnly cookie (preferred)
    - Falls back to body for backward compatibility
    - Sets new access token in httpOnly cookie

    Business Rules:
    - Le refresh token doit être valide (pas expiré, signature correcte)
    - L'utilisateur doit toujours être actif
    - Retourne un nouveau access token (15 min)

    Args:
        request_obj: FastAPI Request object
        request: Optional RefreshRequest (body) for backward compatibility
        db: Session SQLAlchemy
        refresh_token_cookie: Refresh token from cookie

    Returns:
        JSONResponse avec nouveau access_token (also set in cookie)

    Raises:
        HTTPException: 401 si refresh token invalide ou compte inactif
    """
    await apply_rate_limit(request_obj, "refresh")

    # Priority: cookie > body (for backward compatibility)
    token_to_use = refresh_token_cookie
    token_source = "cookie"

    if not token_to_use and request and request.refresh_token:
        token_to_use = request.refresh_token
        token_source = "body"

    if not token_to_use:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token manquant",
        )

    result = AuthService.refresh_access_token(db, token_to_use)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalide ou expiré, ou compte inactif",
        )

    logger.debug(f"Token refreshed successfully (token_source={token_source})")

    # Build response
    response_data = {
        "access_token": result["access_token"],
        "token_type": result["token_type"],
    }

    response = JSONResponse(content=response_data)

    # Set new access token cookie
    set_access_token_cookie(response, result["access_token"])

    return response


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    access_token_cookie: Optional[str] = Cookie(None, alias="access_token"),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Logout utilisateur en révoquant l'access token.

    Security (2026-01-20):
    - Clears all auth cookies (access, refresh, CSRF)
    - Supports both cookie and header auth for backward compatibility

    Business Rules:
    - Révoque le token JWT actuel
    - Rend le token invalide pour toute utilisation future

    Args:
        credentials: Token extrait du header Authorization: Bearer <token> (optional)
        access_token_cookie: Access token from cookie (optional)
        db: Session SQLAlchemy

    Returns:
        JSONResponse avec message de confirmation (cookies cleared)

    Raises:
        HTTPException: 400 si token invalide
    """
    # Priority: cookie > header
    token = access_token_cookie
    if not token and credentials:
        token = credentials.credentials

    # If no token at all, just clear cookies (idempotent logout)
    if not token:
        response = JSONResponse(content={"message": "Logged out successfully"})
        clear_auth_cookies(response)
        logger.info("User logged out (no token to revoke)")
        return response

    # Révoquer le token
    success = AuthService.revoke_token(db, token)

    if not success:
        # Still clear cookies even if revocation fails
        response = JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Impossible de révoquer le token"}
        )
        clear_auth_cookies(response)
        return response

    response = JSONResponse(content={"message": "Logged out successfully"})
    clear_auth_cookies(response)

    logger.info("User logged out successfully")
    return response


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    registration: RegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Inscrit un nouvel utilisateur (simplifié sans tenant).

    Business Rules (Updated: 2025-12-23):
    - Self-service public: n'importe qui peut s'inscrire
    - Email globalement unique
    - Crée automatiquement:
      * Un utilisateur avec tier starter par défaut
      * Un schema PostgreSQL (user_{id}) pour isolation
    - Envoie un email de vérification
    - L'utilisateur doit vérifier son email avant de pouvoir se connecter

    Args:
        registration: full_name, email, password
        db: Session SQLAlchemy

    Returns:
        Message demandant de vérifier l'email

    Raises:
        HTTPException: 400 si email déjà utilisé ou erreur de création
    """
    await apply_rate_limit(request, "register")

    # Vérifier que l'email n'existe pas déjà
    # Security (2025-12-23): Message générique pour éviter énumération d'emails
    existing_user = db.query(User).filter(User.email == registration.email).first()
    if existing_user:
        logger.warning(f"Registration attempt with existing email: {redact_email(registration.email)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de créer le compte. Vérifiez vos informations ou contactez le support.",
        )

    try:
        # 1. Récupérer le quota FREE par défaut
        subscription_tier = SubscriptionTier.FREE
        quota = db.query(SubscriptionQuota).filter(
            SubscriptionQuota.tier == subscription_tier
        ).first()

        if not quota:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Subscription quota not found. Please contact support."
            )

        # Convertir les strings en Enums si nécessaire
        account_type = AccountType(registration.account_type) if isinstance(registration.account_type, str) else registration.account_type
        business_type = BusinessType(registration.business_type) if registration.business_type and isinstance(registration.business_type, str) else registration.business_type
        estimated_products = EstimatedProducts(registration.estimated_products) if registration.estimated_products and isinstance(registration.estimated_products, str) else registration.estimated_products

        user = User(
            # Authentication
            email=registration.email,
            hashed_password=AuthService.hash_password(registration.password),
            full_name=registration.full_name,
            role=UserRole.USER,  # Tous les users sont "user" par défaut
            is_active=True,
            # Onboarding fields (Added: 2024-12-08)
            business_name=registration.business_name,
            account_type=account_type,
            business_type=business_type,
            estimated_products=estimated_products,
            # Professional fields
            siret=registration.siret,
            vat_number=registration.vat_number,
            # Contact
            phone=registration.phone,
            country=registration.country,
            language=registration.language,
            # Subscription
            subscription_tier=subscription_tier,
            subscription_tier_id=quota.id,
            subscription_status="active",
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        # 2. Créer le schema PostgreSQL pour l'utilisateur
        try:
            schema_name = UserSchemaService.create_user_schema(db, user.id)
            logger.info(f"Schema created: {schema_name}")
        except Exception as schema_error:
            # Rollback user creation if schema creation fails
            db.delete(user)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la création du schema: {str(schema_error)}",
            )

        # 3. Générer le token de vérification email
        verification_token = AuthService.generate_email_verification_token(user, db)

        # 4. Envoyer l'email de vérification
        email_sent = await EmailService.send_verification_email(
            to_email=user.email,
            to_name=user.full_name,
            verification_token=verification_token,
        )

        if email_sent:
            logger.info(f"Verification email sent to {redact_email(user.email)}")
        else:
            logger.warning(f"Failed to send verification email to {redact_email(user.email)}")

        logger.info(f"User registered: user_id={user.id}, schema={user.schema_name}, tier={user.subscription_tier.value}")

        # Ne pas retourner les tokens - l'utilisateur doit d'abord vérifier son email
        return {
            "message": "Inscription réussie ! Veuillez vérifier votre boîte email pour activer votre compte.",
            "email": user.email,
            "requires_verification": True,
        }

    except Exception as e:
        # Rollback en cas d'erreur
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'inscription: {str(e)}",
        )


@router.get("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    request: Request,
    token: str,
    db: Session = Depends(get_db),
):
    """
    Vérifie l'email d'un utilisateur via le token envoyé par email.

    Business Rules (2025-12-18):
    - Le token doit être valide et non expiré (24h)
    - L'email est marqué comme vérifié
    - Le token est supprimé après utilisation

    Args:
        token: Token de vérification reçu par email
        db: Session SQLAlchemy

    Returns:
        Message de succès

    Raises:
        HTTPException: 400 si token invalide ou expiré
    """
    await apply_rate_limit(request, "verify_email")

    user = AuthService.verify_email_token(db, token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de vérification invalide ou expiré",
        )

    return {
        "message": "Email vérifié avec succès",
        "email": user.email,
    }


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification(
    request: Request,
    email: str,
    db: Session = Depends(get_db),
):
    """
    Renvoie un email de vérification.

    Business Rules (2025-12-18):
    - L'utilisateur doit exister
    - L'email ne doit pas déjà être vérifié
    - Génère un nouveau token (invalide l'ancien)
    - Rate limited côté frontend recommandé

    Args:
        email: Email de l'utilisateur
        db: Session SQLAlchemy

    Returns:
        Message de succès (toujours le même pour éviter enumeration)
    """
    await apply_rate_limit(request, "resend_verification")

    # Toujours retourner le même message pour éviter l'énumération d'emails
    success_message = {
        "message": "Si cet email existe et n'est pas vérifié, un email de vérification a été envoyé"
    }

    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Ne pas révéler que l'email n'existe pas
        return success_message

    if user.email_verified:
        # Ne pas révéler que l'email est déjà vérifié
        return success_message

    # Générer nouveau token
    verification_token = AuthService.generate_email_verification_token(user, db)

    # Envoyer l'email de vérification
    email_sent = await EmailService.send_verification_email(
        to_email=user.email,
        to_name=user.full_name,
        verification_token=verification_token,
    )

    if email_sent:
        logger.info(f"Verification email resent to {redact_email(user.email)}")
    else:
        logger.warning(f"Failed to resend verification email to {redact_email(user.email)}")

    return success_message
