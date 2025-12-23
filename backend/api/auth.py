"""
Authentication Routes (Simplified - No Tenant)

Routes API pour l'authentification des utilisateurs.
"""

import asyncio
import random

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.public.user import User, UserRole, SubscriptionTier, AccountType, BusinessType, EstimatedProducts
from schemas.auth_schemas import LoginRequest, RefreshRequest, RefreshResponse, RegisterRequest, TokenResponse
from services.auth_service import AuthService
from services.email_service import EmailService
from services.user_schema_service import UserSchemaService
from shared.database import get_db
from shared.logging_setup import get_logger
from shared.security_utils import redact_email, redact_password

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
    source: str = "web",
) -> TokenResponse:
    """
    Authentifie un utilisateur et retourne les tokens JWT.

    Business Rules (Updated: 2025-12-07):
    - L'email est globalement unique
    - L'utilisateur doit être actif (is_active=True)
    - Le mot de passe doit être correct
    - Retourne un access token (1h) et un refresh token (7 jours)
    - Supporte le paramètre optionnel 'source' pour tracking (web, plugin, mobile)

    Args:
        credentials: Email et mot de passe uniquement
        db: Session SQLAlchemy
        source: Source de la connexion (web, plugin, mobile) - défaut: "web"

    Returns:
        TokenResponse avec access_token et refresh_token

    Raises:
        HTTPException: 401 si authentification échouée
    """
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

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user_id=user.id,
        role=user.role.value,
        subscription_tier=user.subscription_tier.value,
    )


@router.post("/refresh", response_model=RefreshResponse, status_code=status.HTTP_200_OK)
def refresh_token(
    request: RefreshRequest,
    db: Session = Depends(get_db),
) -> RefreshResponse:
    """
    Génère un nouveau access token à partir d'un refresh token.

    Business Rules:
    - Le refresh token doit être valide (pas expiré, signature correcte)
    - L'utilisateur et le tenant doivent toujours être actifs
    - Retourne un nouveau access token (1h)

    Args:
        request: Refresh token JWT
        db: Session SQLAlchemy

    Returns:
        RefreshResponse avec nouveau access_token

    Raises:
        HTTPException: 401 si refresh token invalide ou compte inactif
    """
    result = AuthService.refresh_access_token(db, request.refresh_token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalide ou expiré, ou compte inactif",
        )

    return RefreshResponse(**result)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
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
        from models.public.subscription_quota import SubscriptionQuota

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
def verify_email(
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
