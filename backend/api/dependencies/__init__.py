"""
API Dependencies

Dependencies FastAPI reusables pour l'authentification et l'autorisation.

Author: Claude
Date: 2025-12-08
"""

import logging
import os
import re
from typing import Callable, Optional, Tuple

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.orm import Session

from models.public.user import User, UserRole
from services.auth_service import AuthService
from shared.config import settings
from shared.database import get_db

logger = logging.getLogger(__name__)

# Regex pour validation stricte du schema_name (protection SQL injection)
SCHEMA_NAME_PATTERN = re.compile(r'^user_\d+$')


def _validate_schema_name(schema_name: str) -> str:
    """
    Valide strictement le nom du schema PostgreSQL.

    Security (2025-12-18):
    - Vérifie que le schema_name correspond au pattern attendu (user_<id>)
    - Protection contre SQL injection dans SET search_path
    - Defense-in-depth même si schema_name vient d'une source de confiance

    Args:
        schema_name: Nom du schema à valider

    Returns:
        schema_name si valide

    Raises:
        HTTPException: 500 si schema_name invalide (ne devrait jamais arriver)
    """
    if not SCHEMA_NAME_PATTERN.match(schema_name):
        logger.critical(
            f"🚨 SECURITY: Invalid schema_name detected! "
            f"schema_name={schema_name}, pattern={SCHEMA_NAME_PATTERN.pattern}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne de sécurité"
        )
    return schema_name

# Security scheme pour JWT Bearer (auto_error=False pour permettre le bypass dev)
security = HTTPBearer(auto_error=False)

# Mode bypass pour développement - BLOQUÉ EN PRODUCTION
_dev_auth_bypass_env = os.getenv("DEV_AUTH_BYPASS", "false").lower() == "true"
DEV_DEFAULT_USER_ID = int(os.getenv("DEV_DEFAULT_USER_ID", "2"))

# Sécurité: DEV_AUTH_BYPASS ne peut JAMAIS être activé en production
if _dev_auth_bypass_env and settings.is_production:
    logger.critical(
        "🚨 SECURITY: DEV_AUTH_BYPASS=true détecté en PRODUCTION! "
        "Cette option est DÉSACTIVÉE pour des raisons de sécurité."
    )
    DEV_AUTH_BYPASS = False
else:
    DEV_AUTH_BYPASS = _dev_auth_bypass_env
    if DEV_AUTH_BYPASS:
        logger.warning(
            "⚠️ DEV_AUTH_BYPASS activé - Mode développement uniquement. "
            "Ne JAMAIS utiliser en production!"
        )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
    x_dev_user_id: Optional[str] = Header(None, alias="X-Dev-User-Id"),
) -> User:
    """
    Recupere l'utilisateur actuel depuis le JWT token.

    Business Rules (Updated: 2025-12-12):
    - Le token doit etre valide (pas expire, signature correcte)
    - L'utilisateur doit etre actif
    - Architecture simplifiee: pas de tenant, seulement user
    - MODE DEV: Si DEV_AUTH_BYPASS=true, permet de bypasser l'auth via X-Dev-User-Id header

    Args:
        credentials: Bearer token depuis header Authorization
        db: Session SQLAlchemy
        x_dev_user_id: Header optionnel pour bypass en mode dev

    Returns:
        User: Utilisateur authentifie

    Raises:
        HTTPException: 401 si token invalide ou utilisateur inactif
    """
    # Mode bypass pour développement (via Swagger UI)
    if DEV_AUTH_BYPASS:
        # Utiliser X-Dev-User-Id header si fourni, sinon DEV_DEFAULT_USER_ID
        if x_dev_user_id:
            user_id = int(x_dev_user_id)
        elif not credentials:
            # Pas de token et pas de header = utiliser l'user par défaut
            user_id = DEV_DEFAULT_USER_ID
        else:
            # Token fourni = utiliser le flow normal
            user_id = None

        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.is_active:
                logger.debug(
                    f"🔓 DEV_AUTH_BYPASS: Authentification bypassée pour user_id={user_id} "
                    f"(email={user.email})"
                )
                return user

    # Flow normal avec JWT
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token manquant",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Verifier et decoder le JWT token
    payload = AuthService.verify_token(token, token_type="access")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expire",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token malformed",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Recuperer l'utilisateur
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Compte desactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_role(*allowed_roles: UserRole) -> Callable:
    """
    Factory pour créer une dependency qui vérifie le rôle de l'utilisateur.

    Business Rules (2025-12-08):
    - Vérifie que l'utilisateur a un des rôles autorisés
    - Lève une 403 Forbidden si le rôle n'est pas autorisé

    Args:
        *allowed_roles: Liste des rôles autorisés (ex: UserRole.ADMIN, UserRole.SUPPORT)

    Returns:
        Dependency FastAPI qui vérifie le rôle

    Example:
        @app.get("/admin/users")
        async def list_users(current_user: User = Depends(require_role(UserRole.ADMIN))):
            # ...
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Accès refusé. Rôle requis: {', '.join([r.value for r in allowed_roles])}"
            )
        return current_user
    return role_checker


# Shortcuts pour les rôles courants
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency qui vérifie que l'utilisateur est ADMIN.

    Business Rules (2025-12-08):
    - Seuls les ADMIN peuvent accéder
    - Utilisé pour: gestion utilisateurs, modification abonnements, config

    Returns:
        User avec role ADMIN

    Raises:
        HTTPException: 403 si pas ADMIN
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Rôle ADMIN requis."
        )
    return current_user


def require_admin_or_support(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency qui vérifie que l'utilisateur est ADMIN ou SUPPORT.

    Business Rules (2025-12-08):
    - ADMIN et SUPPORT peuvent accéder
    - Utilisé pour: consultation des données utilisateurs, support client

    Returns:
        User avec role ADMIN ou SUPPORT

    Raises:
        HTTPException: 403 si ni ADMIN ni SUPPORT
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPPORT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Rôle ADMIN ou SUPPORT requis."
        )
    return current_user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Alias pour get_current_user (pour compatibilité).
    Tous les utilisateurs retournés par get_current_user sont déjà actifs.
    """
    return current_user


def get_user_db(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Tuple[Session, User]:
    """
    Dependency qui retourne une session DB avec isolation user automatique.

    Cette dependency:
    1. Authentifie l'utilisateur via JWT
    2. Configure automatiquement le search_path PostgreSQL vers le schema de l'utilisateur
    3. Vérifie et garantit que le search_path est correctement appliqué
    4. Retourne la session et l'utilisateur

    Business Rules (2025-12-11):
    - Élimine la duplication du SET search_path dans chaque route
    - Garantit que l'isolation est toujours appliquée
    - Vérifie le search_path après application (fix connection pooling issues)
    - Simplifie le code des routes

    Usage:
        @router.get("/products")
        def list_products(db_user: Tuple[Session, User] = Depends(get_user_db)):
            db, current_user = db_user
            # db est déjà configuré pour le schema user_{id}
            products = db.query(Product).all()

    Returns:
        Tuple[Session, User]: (session DB isolée, utilisateur authentifié)
    """
    # Valider strictement le schema_name (defense-in-depth contre SQL injection)
    schema_name = _validate_schema_name(current_user.schema_name)

    # Use SET LOCAL to ensure search_path persists within the transaction
    # SET LOCAL is transaction-scoped and won't be affected by connection pooling
    db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))

    # Verify search_path was applied
    result = db.execute(text("SHOW search_path"))
    actual_path = result.scalar()

    logger.debug(f"[get_user_db] User {current_user.id}, schema={schema_name}, search_path={actual_path}")

    # Double-check schema is in path
    if schema_name not in actual_path:
        logger.warning(f"[get_user_db] search_path mismatch! Expected {schema_name}, got {actual_path}")
        # Force re-apply
        db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))

    return db, current_user


__all__ = [
    "get_current_user",
    "get_current_active_user",
    "get_user_db",
    "require_role",
    "require_admin",
    "require_admin_or_support",
]
