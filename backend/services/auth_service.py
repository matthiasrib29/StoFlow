"""
Authentication Service (Simplified - No Tenant)

Ce service gère l'authentification des utilisateurs avec JWT.

Business Rules (Updated: 2026-01-05):
- Access token: durée configurable via JWT_ACCESS_TOKEN_EXPIRE_MINUTES (défaut: 1440 = 24h)
- Refresh token: durée configurable via JWT_REFRESH_TOKEN_EXPIRE_DAYS (défaut: 7 jours)
- Les mots de passe doivent être hashés avec bcrypt
- Email globalement unique (un email = un seul user)
- Un utilisateur inactif (is_active=False) ne peut pas se connecter
- Chaque user a son propre schema PostgreSQL (user_{id})
- Vérification email obligatoire pour certaines actions
- Blocage après 5 tentatives de login échouées
"""

import secrets
from datetime import timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from models.public.user import User
from repositories.user_repository import UserRepository
from shared.config import settings
from shared.datetime_utils import utc_now
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class AuthService:
    """Service d'authentification avec JWT."""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash un mot de passe avec bcrypt.

        Args:
            password: Mot de passe en clair

        Returns:
            Hash du mot de passe
        """
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Vérifie qu'un mot de passe correspond au hash.

        Args:
            plain_password: Mot de passe en clair
            hashed_password: Hash à vérifier

        Returns:
            True si le mot de passe est correct, False sinon
        """
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)

    @staticmethod
    def create_access_token(user_id: int, role: str) -> str:
        """
        Crée un access token JWT.

        La durée de validité est configurée via JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        (défaut: 1440 minutes = 24 heures).

        Args:
            user_id: ID de l'utilisateur
            role: Rôle de l'utilisateur (admin ou user)

        Returns:
            Access token JWT
        """
        expire = utc_now() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
        payload = {
            "user_id": user_id,
            "role": role,
            "type": "access",
            "exp": expire,
            "iat": utc_now(),
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    @staticmethod
    def create_refresh_token(user_id: int) -> str:
        """
        Crée un refresh token JWT.

        La durée de validité est configurée via JWT_REFRESH_TOKEN_EXPIRE_DAYS
        (défaut: 7 jours).

        Args:
            user_id: ID de l'utilisateur

        Returns:
            Refresh token JWT
        """
        expire = utc_now() + timedelta(days=settings.jwt_refresh_token_expire_days)
        payload = {
            "user_id": user_id,
            "type": "refresh",
            "exp": expire,
            "iat": utc_now(),
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
        """
        Vérifie et décode un token JWT.

        Supporte la rotation de secrets JWT:
        - Essaie d'abord avec le secret actuel (jwt_secret_key)
        - Si échec et qu'un ancien secret est configuré (jwt_secret_key_previous),
          essaie avec l'ancien secret (période de grâce)

        Args:
            token: Token JWT à vérifier
            token_type: Type attendu ("access" ou "refresh")

        Returns:
            Payload du token si valide, None sinon
        """
        # Liste des secrets à essayer (actuel en premier, puis ancien si configuré)
        secrets_to_try = [settings.jwt_secret_key]
        if settings.jwt_secret_key_previous:
            secrets_to_try.append(settings.jwt_secret_key_previous)

        last_error = None
        for i, secret in enumerate(secrets_to_try):
            try:
                payload = jwt.decode(token, secret, algorithms=[settings.jwt_algorithm])

                # Vérifier que le type de token correspond
                if payload.get("type") != token_type:
                    return None

                # Log si token validé avec ancien secret (utile pour monitoring)
                if i > 0:
                    logger.debug(
                        f"Token validé avec ancien secret (rotation en cours). "
                        f"user_id={payload.get('user_id')}, type={token_type}"
                    )

                return payload
            except JWTError as e:
                last_error = e
                continue

        # Tous les secrets ont échoué
        if last_error:
            logger.debug(f"Token verification failed: {last_error}")
        return None

    # Configuration blocage compte (nombre d'échecs avant blocage et durée)
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str, source: str = "web") -> Optional[User]:
        """
        Authentifie un utilisateur.

        Business Rules (Updated: 2025-12-18):
        - L'email est globalement unique
        - Vérifie que l'utilisateur existe et est actif (is_active=True)
        - Vérifie que le compte n'est pas verrouillé (locked_until)
        - Vérifie le mot de passe
        - Incrémente failed_login_attempts en cas d'échec
        - Verrouille le compte après MAX_FAILED_ATTEMPTS échecs
        - Reset le compteur en cas de succès
        - Met à jour last_login en cas de succès
        - Accepte un paramètre 'source' optionnel pour tracking (web, plugin, mobile)

        Args:
            db: Session SQLAlchemy
            email: Email de l'utilisateur (globalement unique)
            password: Mot de passe en clair
            source: Source de la connexion (web, plugin, mobile) - défaut: "web"

        Returns:
            Utilisateur si authentification réussie, None sinon
        """
        # Chercher l'utilisateur par email (globalement unique)
        user = UserRepository.get_by_email(db, email)

        # Vérifier que l'utilisateur existe
        if not user:
            logger.warning(f"Login failed: email={email}, reason=user_not_found")
            return None

        # Vérifier que l'utilisateur est actif
        if not user.is_active:
            logger.warning(f"Login failed: email={email}, user_id={user.id}, reason=account_inactive")
            return None

        # Vérifier si le compte est verrouillé
        if user.locked_until and user.locked_until > utc_now():
            remaining = (user.locked_until - utc_now()).total_seconds() / 60
            logger.warning(
                f"Login failed: email={email}, user_id={user.id}, "
                f"reason=account_locked, remaining_minutes={remaining:.1f}"
            )
            return None

        # Log si le compte était verrouillé et vient d'être déverrouillé automatiquement
        if user.locked_until and user.locked_until <= utc_now():
            logger.info(
                f"Account auto-unlocked: user_id={user.id}, "
                f"was_locked_until={user.locked_until}"
            )

        # Vérifier le mot de passe
        if not AuthService.verify_password(password, user.hashed_password):
            # Incrémenter le compteur d'échecs
            UserRepository.increment_failed_login(db, user)

            logger.warning(
                f"Login failed: email={email}, user_id={user.id}, "
                f"reason=wrong_password, attempts={user.failed_login_attempts}"
            )

            # Verrouiller si trop d'échecs
            if user.failed_login_attempts >= AuthService.MAX_FAILED_ATTEMPTS:
                lock_until = utc_now() + timedelta(minutes=AuthService.LOCKOUT_DURATION_MINUTES)
                UserRepository.lock_account(db, user, lock_until)
                logger.warning(
                    f"Account locked: user_id={user.id}, email={email}, "
                    f"attempts={user.failed_login_attempts}, locked_for={AuthService.LOCKOUT_DURATION_MINUTES}min"
                )

            db.commit()
            return None

        # Authentification réussie - reset le compteur et déverrouiller
        UserRepository.reset_login_failures(db, user)
        UserRepository.update_login_stats(db, user, last_login=utc_now())
        db.commit()

        # Log de la connexion avec source pour tracking
        logger.info(f"User authenticated: user_id={user.id}, schema={user.schema_name}, source={source}")

        return user

    @staticmethod
    def get_user_from_token(db: Session, token: str) -> Optional[User]:
        """
        Récupère un utilisateur à partir d'un access token.

        Args:
            db: Session SQLAlchemy
            token: Access token JWT

        Returns:
            Utilisateur si token valide, None sinon
        """
        payload = AuthService.verify_token(token, token_type="access")
        if not payload:
            return None

        user_id = payload.get("user_id")
        if not user_id:
            return None

        user = UserRepository.get_by_id(db, user_id)

        # Vérifier que l'utilisateur est actif
        if not user or not user.is_active:
            return None

        return user

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> Optional[dict]:
        """
        Génère un nouveau access token à partir d'un refresh token.

        Args:
            db: Session SQLAlchemy
            refresh_token: Refresh token JWT

        Returns:
            Dict avec nouveau access token si valide, None sinon
            Format: {"access_token": "...", "token_type": "bearer"}
        """
        payload = AuthService.verify_token(refresh_token, token_type="refresh")
        if not payload:
            return None

        user_id = payload.get("user_id")

        if not user_id:
            return None

        # Vérifier que l'utilisateur est toujours actif
        user = UserRepository.get_by_id(db, user_id)
        if not user or not user.is_active:
            return None

        # Générer un nouveau access token
        access_token = AuthService.create_access_token(
            user_id=user.id,
            role=user.role.value,
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }

    # Configuration vérification email
    EMAIL_VERIFICATION_EXPIRES_HOURS = 24

    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash a token using SHA-256 for secure storage."""
        import hashlib
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def generate_email_verification_token(user: User, db: Session) -> str:
        """
        Génère un token de vérification email pour un utilisateur.

        Security: Le token est hashé (SHA-256) avant stockage en DB.
        Seul le hash est stocké, pas le token en clair.

        Args:
            user: Utilisateur pour lequel générer le token
            db: Session SQLAlchemy

        Returns:
            Token de vérification (32 bytes en URL-safe base64) - envoyé par email
        """
        # Générer un token aléatoire fort
        token = secrets.token_urlsafe(32)

        # Stocker le HASH du token (pas le token en clair)
        token_hash = AuthService._hash_token(token)
        user.email_verification_token = token_hash
        user.email_verification_expires = utc_now() + timedelta(
            hours=AuthService.EMAIL_VERIFICATION_EXPIRES_HOURS
        )
        db.commit()

        logger.info(f"Email verification token generated: user_id={user.id}")
        return token  # Retourner le token original (envoyé par email)

    @staticmethod
    def verify_email_token(db: Session, token: str) -> Optional[User]:
        """
        Vérifie un token de vérification email et marque l'email comme vérifié.

        Security: Le token fourni est hashé puis comparé au hash stocké en DB.

        Args:
            db: Session SQLAlchemy
            token: Token de vérification (reçu par email)

        Returns:
            User si token valide, None sinon
        """
        # Hasher le token fourni pour comparaison
        token_hash = AuthService._hash_token(token)

        user = db.query(User).filter(
            User.email_verification_token == token_hash
        ).first()

        if not user:
            logger.warning("Email verification failed: token_not_found")
            return None

        # Vérifier que l'email n'est pas déjà vérifié (token déjà utilisé)
        if user.email_verified:
            logger.warning(f"Email verification failed: already_verified, user_id={user.id}")
            return None

        # Vérifier expiration
        if user.email_verification_expires and user.email_verification_expires < utc_now():
            logger.warning(f"Email verification failed: token_expired, user_id={user.id}")
            return None

        # Marquer comme vérifié
        user.email_verified = True
        user.email_verification_token = None
        user.email_verification_expires = None
        db.commit()

        logger.info(f"Email verified: user_id={user.id}")
        return user

    @staticmethod
    def is_email_verified(user: User) -> bool:
        """
        Vérifie si l'email de l'utilisateur est vérifié.

        Args:
            user: Utilisateur à vérifier

        Returns:
            True si email vérifié, False sinon
        """
        return user.email_verified is True

    # NOTE (2025-12-12): get_subscription_limits() SUPPRIMÉE
    # Les limites d'abonnement sont maintenant définies en base de données
    # dans la table subscription_quotas et accessibles via:
    # - user.subscription_quota.max_products
    # - user.subscription_quota.max_platforms
    # - user.subscription_quota.ai_credits_monthly
    # Voir: shared/subscription_limits.py et models/public/subscription_quota.py
