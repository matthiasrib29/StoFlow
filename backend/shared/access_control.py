"""
Access Control

Utilities for security checks, access control, and resource ownership.

Defense-in-depth helpers for multi-tenant schema isolation.
Role-based access control for USER, ADMIN, and SUPPORT roles.

Created: 2026-01-08
Updated: 2026-01-20 - Merged ownership.py functions
"""

from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from models.public.user import User, UserRole
from shared.logging import get_logger

logger = get_logger(__name__)


def verify_schema_isolation(db: Session, expected_user_id: int) -> bool:
    """
    Verify that the database session is using the correct user schema.

    Defense-in-depth check: Ensures that the session's search_path
    matches the expected user schema.

    Args:
        db: SQLAlchemy session
        expected_user_id: User ID that should own this session

    Returns:
        True if schema isolation is correct

    Raises:
        HTTPException: 500 if schema mismatch detected (security violation)
    """
    try:
        # Get current search_path
        result = db.execute(text("SHOW search_path")).fetchone()
        current_path = result[0] if result else ""

        expected_schema = f"user_{expected_user_id}"

        # Check if user schema is first in search_path
        if not current_path.startswith(expected_schema):
            logger.error(
                f"[SecurityViolation] Schema mismatch detected! "
                f"Expected: {expected_schema}, Got: {current_path}, "
                f"User ID: {expected_user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Security violation detected"
            )

        return True

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SecurityCheck] Failed to verify schema: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Security check failed"
        )


def ensure_resource_ownership(
    resource: Optional[object],
    resource_name: str,
    identifier: int | str,
    user_id: int
) -> object:
    """
    Ensure a resource exists and belongs to the current user.

    For models WITH user_id field: Checks user_id matches.
    For models WITHOUT user_id field: Relies on schema isolation (already verified by get_user_db).

    Args:
        resource: Database object (or None if not found)
        resource_name: Type of resource for error message (e.g., "Product", "Order")
        identifier: Resource identifier for error message
        user_id: Current user ID (for logging)

    Returns:
        The resource object if valid

    Raises:
        HTTPException: 404 if resource not found
        HTTPException: 403 if resource belongs to different user
    """
    if resource is None:
        logger.warning(
            f"[AccessDenied] {resource_name} {identifier} not found "
            f"(user_id: {user_id})"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_name} not found"
        )

    # If resource has user_id field, verify ownership
    if hasattr(resource, "user_id"):
        if resource.user_id != user_id:
            logger.error(
                f"[SecurityViolation] User {user_id} attempted to access "
                f"{resource_name} {identifier} owned by user {resource.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

    # Note: For resources without user_id, ownership is enforced by schema isolation
    # (the query wouldn't find the resource if it's in a different user's schema)

    return resource


def require_permission(user_role: str, required_roles: list[str]) -> bool:
    """
    Check if user has required role/permission.

    Args:
        user_role: Current user's role (e.g., "user", "admin")
        required_roles: List of allowed roles (e.g., ["admin", "moderator"])

    Returns:
        True if user has permission

    Raises:
        HTTPException: 403 if user lacks required permission
    """
    if user_role not in required_roles:
        logger.warning(
            f"[AccessDenied] User with role '{user_role}' attempted to access "
            f"resource requiring roles: {required_roles}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    return True


def is_admin(user_role: str) -> bool:
    """
    Check if user is admin.

    Args:
        user_role: User's role

    Returns:
        True if admin

    Raises:
        HTTPException: 403 if not admin
    """
    return require_permission(user_role, ["admin"])


# =============================================================================
# ROLE-BASED ACCESS CONTROL (merged from ownership.py)
# =============================================================================


def check_resource_ownership(
    user: User,
    resource_user_id: int,
    resource_type: str = "ressource",
    allow_admin: bool = True,
    allow_support: bool = False,
) -> None:
    """
    Vérifie que l'utilisateur a le droit d'accéder à une ressource.

    Business Rules:
    - USER: Peut uniquement accéder à ses propres ressources
    - ADMIN: Peut accéder à toutes les ressources (si allow_admin=True)
    - SUPPORT: Peut accéder à toutes les ressources en lecture (si allow_support=True)

    Args:
        user: Utilisateur qui tente d'accéder
        resource_user_id: ID du propriétaire de la ressource
        resource_type: Type de ressource (pour message d'erreur)
        allow_admin: Si True, ADMIN peut accéder (défaut: True)
        allow_support: Si True, SUPPORT peut accéder (défaut: False)

    Raises:
        HTTPException: 403 si l'utilisateur n'a pas le droit d'accéder
    """
    # ADMIN a accès à tout (si autorisé)
    if allow_admin and user.role == UserRole.ADMIN:
        return

    # SUPPORT a accès en lecture (si autorisé)
    if allow_support and user.role == UserRole.SUPPORT:
        return

    # USER ne peut accéder qu'à ses propres ressources
    if user.id != resource_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Vous n'avez pas accès à cette {resource_type}."
        )


def ensure_user_owns_resource(
    user: User,
    resource: Any,
    resource_type: str = "ressource",
    allow_support: bool = True  # Par défaut, SUPPORT peut lire
) -> None:
    """
    Vérifie que l'utilisateur est propriétaire d'une ressource.

    Raccourci pour check_resource_ownership qui extrait automatiquement
    le user_id de la ressource.

    Business Rules:
    - Si la ressource a un attribut user_id: vérifie l'ownership classique
    - Si pas de user_id: assume que l'isolation est faite par schema (multi-tenant)
      → Dans ce cas, ADMIN et SUPPORT (si allow_support=True) peuvent accéder

    Args:
        user: Utilisateur qui tente d'accéder
        resource: Objet ressource (peut avoir ou non un attribut user_id)
        resource_type: Type de ressource (pour message d'erreur)
        allow_support: Si True, SUPPORT peut accéder en lecture (défaut: True)

    Raises:
        HTTPException: 403 si l'utilisateur n'est pas propriétaire
    """
    # Si la ressource a un user_id, on fait la vérification classique
    if hasattr(resource, 'user_id'):
        check_resource_ownership(
            user=user,
            resource_user_id=resource.user_id,
            resource_type=resource_type,
            allow_admin=True,
            allow_support=allow_support,
        )
    else:
        # Pas de user_id = isolation par schema utilisateur
        # ADMIN et SUPPORT (si autorisé) peuvent accéder à tous les schemas
        if user.role == UserRole.ADMIN:
            return  # ADMIN peut tout voir
        if allow_support and user.role == UserRole.SUPPORT:
            return  # SUPPORT peut tout voir en lecture seule
        # Pour USER: si la ressource existe dans le search_path actuel,
        # c'est qu'elle appartient bien à l'utilisateur (isolation par schema)
        return


def ensure_can_modify(user: User, resource_type: str = "ressource") -> None:
    """
    Vérifie que l'utilisateur peut modifier une ressource.

    Business Rules:
    - SUPPORT ne peut JAMAIS modifier (lecture seule)
    - ADMIN et USER peuvent modifier (sous réserve d'ownership)

    Args:
        user: Utilisateur qui tente de modifier
        resource_type: Type de ressource (pour message d'erreur)

    Raises:
        HTTPException: 403 si SUPPORT essaie de modifier
    """
    if user.role == UserRole.SUPPORT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Le rôle SUPPORT ne peut pas modifier de {resource_type}. Accès en lecture seule uniquement."
        )


def can_modify_resource(user: User, resource_user_id: int) -> bool:
    """
    Vérifie si l'utilisateur peut modifier une ressource.

    Business Rules:
    - USER: Peut uniquement modifier ses propres ressources
    - ADMIN: Peut modifier toutes les ressources
    - SUPPORT: Ne peut rien modifier (lecture seule)

    Args:
        user: Utilisateur
        resource_user_id: ID du propriétaire de la ressource

    Returns:
        bool: True si l'utilisateur peut modifier, False sinon
    """
    # ADMIN peut tout modifier
    if user.role == UserRole.ADMIN:
        return True

    # SUPPORT ne peut rien modifier
    if user.role == UserRole.SUPPORT:
        return False

    # USER peut modifier ses propres ressources
    return user.id == resource_user_id


def can_view_resource(user: User, resource_user_id: int) -> bool:
    """
    Vérifie si l'utilisateur peut consulter une ressource.

    Business Rules:
    - USER: Peut uniquement consulter ses propres ressources
    - ADMIN: Peut consulter toutes les ressources
    - SUPPORT: Peut consulter toutes les ressources

    Args:
        user: Utilisateur
        resource_user_id: ID du propriétaire de la ressource

    Returns:
        bool: True si l'utilisateur peut consulter, False sinon
    """
    # ADMIN et SUPPORT peuvent tout consulter
    if user.role in [UserRole.ADMIN, UserRole.SUPPORT]:
        return True

    # USER peut consulter ses propres ressources
    return user.id == resource_user_id


__all__ = [
    # Schema isolation
    "verify_schema_isolation",
    # Resource ownership (simple)
    "ensure_resource_ownership",
    # Permission checks
    "require_permission",
    "is_admin",
    # Role-based access control
    "check_resource_ownership",
    "ensure_user_owns_resource",
    "ensure_can_modify",
    "can_modify_resource",
    "can_view_resource",
]
