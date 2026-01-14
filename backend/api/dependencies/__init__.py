"""
API Dependencies

Dependencies FastAPI reusables pour l'authentification et l'autorisation.

Author: Claude
Date: 2025-12-08
"""

import logging
import re
from typing import Callable, Generator, Optional, Tuple

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload

from models.public.user import User, UserRole
from models.public.permission import Permission, RolePermission
from services.auth_service import AuthService
from shared.config import settings
from shared.database import get_db

logger = logging.getLogger(__name__)

# Regex pour validation stricte du schema_name (protection SQL injection)
SCHEMA_NAME_PATTERN = re.compile(r'^user_\d+$')


def _validate_schema_name(schema_name: str, db: Session = None) -> str:
    """
    Valide strictement le nom du schema PostgreSQL.

    Security (2025-12-23):
    - Vérifie que le schema_name correspond au pattern attendu (user_<id>)
    - Si db fourni, vérifie que le schema existe réellement (defense-in-depth)
    - Protection contre SQL injection dans SET search_path

    Args:
        schema_name: Nom du schema à valider
        db: Session SQLAlchemy optionnelle pour vérification d'existence

    Returns:
        schema_name si valide

    Raises:
        HTTPException: 500 si schema_name invalide (ne devrait jamais arriver)
    """
    # Step 1: Regex validation (fast, first line of defense)
    if not SCHEMA_NAME_PATTERN.match(schema_name):
        logger.critical(
            f"🚨 SECURITY: Invalid schema_name pattern! "
            f"schema_name={schema_name}, pattern={SCHEMA_NAME_PATTERN.pattern}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne de sécurité"
        )

    # Step 2: Database existence check (defense-in-depth)
    if db is not None:
        result = db.execute(
            text("SELECT 1 FROM information_schema.schemata WHERE schema_name = :schema"),
            {"schema": schema_name}
        ).scalar()

        if not result:
            logger.critical(
                f"🚨 SECURITY: Schema does not exist! "
                f"schema_name={schema_name} (passed regex but not in database)"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur interne de sécurité"
            )

    return schema_name

# Security scheme pour JWT Bearer
security = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Recupere l'utilisateur actuel depuis le JWT token.

    Business Rules (Updated: 2026-01-14):
    - Le token doit etre valide (pas expire, signature correcte)
    - L'utilisateur doit etre actif
    - Architecture simplifiee: pas de tenant, seulement user
    - Eager loading de subscription_quota pour éviter DetachedInstanceError

    Performance (2026-01-14):
    - Uses joinedload() to eagerly fetch subscription_quota
    - Prevents N+1 queries and DetachedInstanceError in endpoints
    - Single JOIN adds ~5-7 columns to the query (minimal overhead)

    Security (2025-12-23):
    - All requests MUST have a valid JWT token
    - No authentication bypass is allowed

    Args:
        credentials: Bearer token depuis header Authorization
        db: Session SQLAlchemy

    Returns:
        User: Utilisateur authentifie avec subscription_quota precharge

    Raises:
        HTTPException: 401 si token invalide ou utilisateur inactif
    """
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
    user = (
        db.query(User)
        .options(joinedload(User.subscription_quota))
        .filter(User.id == user_id)
        .first()
    )

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


# Cache pour les permissions (évite les requêtes répétitives)
_permissions_cache: dict = {}


def _get_role_permissions(db: Session, role: UserRole) -> set:
    """
    Récupère les permissions d'un rôle depuis la BDD (avec cache).

    Args:
        db: Session SQLAlchemy
        role: Rôle utilisateur

    Returns:
        Set des codes de permissions pour ce rôle
    """
    cache_key = f"role_{role.value}"

    if cache_key not in _permissions_cache:
        permissions = (
            db.query(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .filter(
                RolePermission.role == role,
                Permission.is_active == True
            )
            .all()
        )
        _permissions_cache[cache_key] = {p.code for p in permissions}
        logger.debug(f"Permissions loaded for role {role.value}: {_permissions_cache[cache_key]}")

    return _permissions_cache[cache_key]


def clear_permissions_cache():
    """Vide le cache des permissions (à appeler après modification des permissions)."""
    _permissions_cache.clear()
    logger.info("Permissions cache cleared")


def has_permission(user: User, permission_code: str, db: Session) -> bool:
    """
    Vérifie si un utilisateur a une permission spécifique.

    Business Rules (2025-12-19):
    - Les permissions sont stockées en BDD
    - Vérification basée sur le rôle de l'utilisateur
    - Résultat mis en cache pour performance

    Args:
        user: Utilisateur à vérifier
        permission_code: Code de la permission (ex: "products:create")
        db: Session SQLAlchemy

    Returns:
        True si l'utilisateur a la permission, False sinon
    """
    role_permissions = _get_role_permissions(db, user.role)
    return permission_code in role_permissions


def require_permission(permission_code: str) -> Callable:
    """
    Factory pour créer une dependency qui vérifie une permission spécifique.

    Business Rules (2025-12-19):
    - Vérifie que l'utilisateur a la permission requise
    - Permissions stockées en BDD (modifiables sans redéploiement)
    - Lève 403 Forbidden si permission manquante

    Args:
        permission_code: Code de la permission requise (ex: "products:create")

    Returns:
        Dependency FastAPI qui vérifie la permission

    Example:
        @router.delete("/products/{id}")
        def delete_product(
            product_id: int,
            current_user: User = Depends(require_permission("products:delete"))
        ):
            ...
    """
    def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        if not has_permission(current_user, permission_code, db):
            logger.warning(
                f"Permission denied: user={current_user.id}, role={current_user.role.value}, "
                f"permission={permission_code}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission requise: {permission_code}"
            )
        return current_user

    return permission_checker


def require_any_permission(*permission_codes: str) -> Callable:
    """
    Factory pour créer une dependency qui vérifie au moins une permission parmi plusieurs.

    Args:
        *permission_codes: Codes des permissions (au moins une requise)

    Returns:
        Dependency FastAPI

    Example:
        @router.get("/integrations")
        def list_integrations(
            current_user: User = Depends(require_any_permission(
                "integrations:vinted:connect",
                "integrations:ebay:connect"
            ))
        ):
            ...
    """
    def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        role_permissions = _get_role_permissions(db, current_user.role)

        if not any(code in role_permissions for code in permission_codes):
            logger.warning(
                f"Permission denied: user={current_user.id}, role={current_user.role.value}, "
                f"required_any={permission_codes}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Une permission requise parmi: {', '.join(permission_codes)}"
            )
        return current_user

    return permission_checker


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Alias pour get_current_user (pour compatibilité).
    Tous les utilisateurs retournés par get_current_user sont déjà actifs.
    """
    return current_user


def get_user_db(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Generator[Tuple[Session, User], None, None]:
    """
    Dependency qui retourne une session DB avec isolation user automatique.

    Cette dependency:
    1. Authentifie l'utilisateur via JWT
    2. Crée une nouvelle session avec schema_translate_map configuré
    3. Vérifie que schema_translate_map est correctement appliqué
    4. Retourne la session et l'utilisateur

    Technical Details (2026-01-13):
    - Uses schema_translate_map instead of SET LOCAL search_path
    - schema_translate_map survives COMMIT and ROLLBACK (unlike SET LOCAL)
    - Models with schema="tenant" are remapped to actual user schema at query time
    - Creates a new session with configured engine bind (Session.connection() doesn't persist options)

    Usage:
        @router.get("/products")
        def list_products(db_user: Tuple[Session, User] = Depends(get_user_db)):
            db, current_user = db_user
            # db est déjà configuré pour le schema user_{id}
            products = db.query(Product).all()

    Yields:
        Tuple[Session, User]: (session DB isolée, utilisateur authentifié)
    """
    from sqlalchemy.exc import SQLAlchemyError
    from shared.database import engine

    # Valider strictement le schema_name (defense-in-depth contre SQL injection)
    # Passe db pour vérifier que le schema existe réellement
    schema_name = _validate_schema_name(current_user.schema_name, db)

    # Close the original session - we'll create a new one with configured bind
    # This releases the connection back to the pool
    db.close()

    # Create engine with schema_translate_map
    # engine.execution_options() returns a NEW engine with the options set
    configured_engine = engine.execution_options(
        schema_translate_map={"tenant": schema_name}
    )

    # Create new session with the configured engine
    configured_db = Session(bind=configured_engine)

    try:
        # Verify schema_translate_map was applied
        schema_map = configured_db.get_bind().get_execution_options().get("schema_translate_map", {})
        configured_schema = schema_map.get("tenant")

        logger.debug(
            f"[get_user_db] User {current_user.id}, "
            f"schema_translate_map={{'tenant': '{schema_name}'}}"
        )

        # Double-check schema_translate_map is set (CRITICAL SECURITY CHECK)
        if configured_schema != schema_name:
            logger.critical(
                f"🚨 SCHEMA_TRANSLATE_MAP FAILURE: Expected '{schema_name}' but got '{configured_schema}'. "
                f"User {current_user.id} isolation compromised."
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database isolation error. Please retry your request."
            )

        yield configured_db, current_user
        configured_db.commit()
    except SQLAlchemyError:
        configured_db.rollback()
        raise
    finally:
        configured_db.close()


__all__ = [
    "get_current_user",
    "get_current_active_user",
    "get_user_db",
    "require_role",
    "require_admin",
    "require_admin_or_support",
    "require_permission",
    "require_any_permission",
    "has_permission",
    "clear_permissions_cache",
]
