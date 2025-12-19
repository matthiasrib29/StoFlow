"""
Subscription Limits Checker

Helper pour vérifier les limites d'abonnement des utilisateurs.

Business Rules (2025-12-08, Updated 2025-12-19):
- Les limites sont définies par subscription_tier uniquement
- Comportement: Avertissement à 80% + blocage à 100%
- USER voit uniquement ses propres données (isolation stricte)

Author: Claude
Date: 2025-12-08
Updated: 2025-12-19 - Added quota warnings at 80%
"""

from enum import Enum
from typing import Tuple, Optional
from dataclasses import dataclass
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.public.user import User, SubscriptionTier


class QuotaStatus(str, Enum):
    """Status of quota usage."""
    OK = "ok"              # < 80% - All good
    WARNING = "warning"    # 80-99% - Approaching limit
    BLOCKED = "blocked"    # 100% - Limit reached


@dataclass
class QuotaCheckResult:
    """Result of a quota check."""
    status: QuotaStatus
    current: int
    max_allowed: int
    percentage: float
    message: Optional[str] = None

    @property
    def is_warning(self) -> bool:
        return self.status == QuotaStatus.WARNING

    @property
    def is_blocked(self) -> bool:
        return self.status == QuotaStatus.BLOCKED

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "current": self.current,
            "max_allowed": self.max_allowed,
            "percentage": round(self.percentage, 1),
            "message": self.message,
        }


# Warning threshold (80%)
WARNING_THRESHOLD = 0.8


class SubscriptionLimitError(HTTPException):
    """Exception levée quand une limite d'abonnement est atteinte."""

    def __init__(self, message: str, limit_type: str, current: int, max_allowed: int):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "subscription_limit_reached",
                "message": message,
                "limit_type": limit_type,
                "current": current,
                "max_allowed": max_allowed,
            }
        )


def check_product_limit(user: User, db: Session) -> Tuple[int, int]:
    """
    Vérifie si l'utilisateur peut créer un nouveau produit.

    Business Rules (2025-12-09):
    - Compte le nombre de produits actifs (non supprimés) dans le schema de l'utilisateur
    - Compare avec max_products défini dans subscription_quota
    - Lève SubscriptionLimitError si limite atteinte
    - Note: Pas besoin de filter sur user_id car l'isolation est faite par search_path (schema)

    Args:
        user: Utilisateur à vérifier
        db: Session SQLAlchemy (avec search_path déjà configuré)

    Returns:
        Tuple[current_count, max_allowed]: Nombre actuel et limite

    Raises:
        SubscriptionLimitError: Si la limite est atteinte
    """
    from models.user.product import Product

    # Compter les produits actifs (non supprimés) dans le schema de l'utilisateur
    # Note: Le search_path est déjà configuré par l'endpoint, donc on compte simplement
    current_count = (
        db.query(Product)
        .filter(Product.deleted_at.is_(None))
        .count()
    )

    # Récupérer la limite depuis subscription_quota (nouvelle table)
    # En mode test, subscription_quota peut être None, utiliser limite par défaut
    if user.subscription_quota:
        max_allowed = user.subscription_quota.max_products
    else:
        # Mode test: limite généreuse pour ne pas bloquer les tests
        max_allowed = 9999

    if current_count >= max_allowed:
        raise SubscriptionLimitError(
            message=f"Limite de produits atteinte ({max_allowed}). Passez à un abonnement supérieur pour en créer plus.",
            limit_type="products",
            current=current_count,
            max_allowed=max_allowed,
        )

    return current_count, max_allowed


def check_platform_limit(user: User, db: Session) -> Tuple[int, int]:
    """
    Vérifie si l'utilisateur peut connecter une nouvelle plateforme.

    Business Rules (2025-12-09):
    - Compte le nombre de plateformes connectées (intégrations actives)
    - Compare avec max_platforms défini dans subscription_quota
    - Lève SubscriptionLimitError si limite atteinte

    Args:
        user: Utilisateur à vérifier
        db: Session SQLAlchemy

    Returns:
        Tuple[current_count, max_allowed]: Nombre actuel et limite

    Raises:
        SubscriptionLimitError: Si la limite est atteinte
    """
    from models.public.platform_mapping import PlatformMapping

    # Compter les plateformes connectées (avec credentials)
    current_count = (
        db.query(PlatformMapping)
        .filter(
            PlatformMapping.user_id == user.id,
            PlatformMapping.credentials.isnot(None),
        )
        .count()
    )

    # Récupérer la limite depuis subscription_quota (nouvelle table)
    # En mode test, subscription_quota peut être None, utiliser limite par défaut
    if user.subscription_quota:
        max_allowed = user.subscription_quota.max_platforms
    else:
        # Mode test: limite généreuse pour ne pas bloquer les tests
        max_allowed = 99

    if current_count >= max_allowed:
        raise SubscriptionLimitError(
            message=f"Limite de plateformes atteinte ({max_allowed}). Passez à un abonnement supérieur pour en connecter plus.",
            limit_type="platforms",
            current=current_count,
            max_allowed=max_allowed,
        )

    return current_count, max_allowed


def check_ai_credits(user: User, db: Session, credits_needed: int = 1) -> Tuple[int, int]:
    """
    Vérifie si l'utilisateur a assez de crédits IA.

    Business Rules (2025-12-09):
    - Compte les crédits IA utilisés ce mois
    - Compare avec ai_credits_monthly défini dans subscription_quota
    - Lève SubscriptionLimitError si limite atteinte

    Args:
        user: Utilisateur à vérifier
        db: Session SQLAlchemy
        credits_needed: Nombre de crédits nécessaires (défaut: 1)

    Returns:
        Tuple[credits_used, credits_total]: Crédits utilisés et total mensuel

    Raises:
        SubscriptionLimitError: Si pas assez de crédits
    """
    from models.user.ai_generation_log import AIGenerationLog
    from sqlalchemy import func, extract
    from shared.datetime_utils import utc_now

    # Compter les générations IA ce mois
    now = utc_now()
    current_month = now.month
    current_year = now.year

    credits_used = (
        db.query(func.count(AIGenerationLog.id))
        .filter(
            AIGenerationLog.user_id == user.id,
            extract('month', AIGenerationLog.created_at) == current_month,
            extract('year', AIGenerationLog.created_at) == current_year,
        )
        .scalar() or 0
    )

    # Récupérer la limite depuis subscription_quota (nouvelle table)
    credits_total = user.subscription_quota.ai_credits_monthly

    if credits_used + credits_needed > credits_total:
        raise SubscriptionLimitError(
            message=f"Crédits IA épuisés pour ce mois ({credits_used}/{credits_total}). Passez à un abonnement supérieur.",
            limit_type="ai_credits",
            current=credits_used,
            max_allowed=credits_total,
        )

    return credits_used, credits_total


def get_subscription_limits_info(user: User) -> dict:
    """
    Retourne les informations de limites d'abonnement pour un utilisateur.

    Business Rules (2025-12-09):
    - Utilise les limites définies dans subscription_quota
    - Retourne aussi le tier actuel

    Args:
        user: Utilisateur

    Returns:
        Dict avec les limites: max_products, max_platforms, ai_credits_monthly
    """
    return {
        "subscription_tier": user.subscription_tier.value if user.subscription_tier else None,
        "max_products": user.subscription_quota.max_products,
        "max_platforms": user.subscription_quota.max_platforms,
        "ai_credits_monthly": user.subscription_quota.ai_credits_monthly,
    }


# ============================================================================
# New quota check functions with warning system (2025-12-19)
# ============================================================================

def _calculate_quota_status(current: int, max_allowed: int, limit_type: str) -> QuotaCheckResult:
    """
    Calculate quota status with warning at 80%.

    Args:
        current: Current usage
        max_allowed: Maximum allowed
        limit_type: Type of limit (for message)

    Returns:
        QuotaCheckResult with status, percentage, and message
    """
    if max_allowed <= 0:
        # Unlimited (enterprise)
        return QuotaCheckResult(
            status=QuotaStatus.OK,
            current=current,
            max_allowed=max_allowed,
            percentage=0.0,
            message=None
        )

    percentage = current / max_allowed

    if percentage >= 1.0:
        return QuotaCheckResult(
            status=QuotaStatus.BLOCKED,
            current=current,
            max_allowed=max_allowed,
            percentage=percentage * 100,
            message=f"Limite de {limit_type} atteinte ({current}/{max_allowed}). Passez à un abonnement supérieur."
        )
    elif percentage >= WARNING_THRESHOLD:
        remaining = max_allowed - current
        return QuotaCheckResult(
            status=QuotaStatus.WARNING,
            current=current,
            max_allowed=max_allowed,
            percentage=percentage * 100,
            message=f"Attention: {int(percentage * 100)}% de votre quota {limit_type} utilisé. Il vous reste {remaining} {limit_type}."
        )
    else:
        return QuotaCheckResult(
            status=QuotaStatus.OK,
            current=current,
            max_allowed=max_allowed,
            percentage=percentage * 100,
            message=None
        )


def get_product_quota_status(user: User, db: Session) -> QuotaCheckResult:
    """
    Get product quota status with warning.

    Business Rules (2025-12-19):
    - Returns OK if < 80% used
    - Returns WARNING if 80-99% used
    - Returns BLOCKED if >= 100% used

    Args:
        user: User to check
        db: SQLAlchemy session (with search_path configured)

    Returns:
        QuotaCheckResult with status and message
    """
    from models.user.product import Product

    current_count = (
        db.query(Product)
        .filter(Product.deleted_at.is_(None))
        .count()
    )

    if user.subscription_quota:
        max_allowed = user.subscription_quota.max_products
    else:
        max_allowed = 9999

    return _calculate_quota_status(current_count, max_allowed, "produits")


def get_platform_quota_status(user: User, db: Session) -> QuotaCheckResult:
    """
    Get platform quota status with warning.

    Business Rules (2025-12-19):
    - Returns OK if < 80% used
    - Returns WARNING if 80-99% used
    - Returns BLOCKED if >= 100% used

    Args:
        user: User to check
        db: SQLAlchemy session

    Returns:
        QuotaCheckResult with status and message
    """
    from models.public.platform_mapping import PlatformMapping

    current_count = (
        db.query(PlatformMapping)
        .filter(
            PlatformMapping.user_id == user.id,
            PlatformMapping.credentials.isnot(None),
        )
        .count()
    )

    if user.subscription_quota:
        max_allowed = user.subscription_quota.max_platforms
    else:
        max_allowed = 99

    return _calculate_quota_status(current_count, max_allowed, "plateformes")


def get_ai_credits_quota_status(user: User, db: Session) -> QuotaCheckResult:
    """
    Get AI credits quota status with warning.

    Business Rules (2025-12-19):
    - Returns OK if < 80% used
    - Returns WARNING if 80-99% used
    - Returns BLOCKED if >= 100% used

    Args:
        user: User to check
        db: SQLAlchemy session

    Returns:
        QuotaCheckResult with status and message
    """
    from models.user.ai_generation_log import AIGenerationLog
    from sqlalchemy import func, extract
    from shared.datetime_utils import utc_now

    now = utc_now()
    current_month = now.month
    current_year = now.year

    credits_used = (
        db.query(func.count(AIGenerationLog.id))
        .filter(
            AIGenerationLog.user_id == user.id,
            extract('month', AIGenerationLog.created_at) == current_month,
            extract('year', AIGenerationLog.created_at) == current_year,
        )
        .scalar() or 0
    )

    if user.subscription_quota:
        credits_total = user.subscription_quota.ai_credits_monthly
    else:
        credits_total = 9999

    return _calculate_quota_status(credits_used, credits_total, "crédits IA")


def get_all_quotas_status(user: User, db: Session) -> dict:
    """
    Get all quotas status for a user.

    Business Rules (2025-12-19):
    - Returns status for all quota types
    - Useful for dashboard display

    Args:
        user: User to check
        db: SQLAlchemy session (with search_path configured for products)

    Returns:
        Dict with all quota statuses
    """
    products = get_product_quota_status(user, db)
    platforms = get_platform_quota_status(user, db)
    ai_credits = get_ai_credits_quota_status(user, db)

    return {
        "subscription_tier": user.subscription_tier.value if user.subscription_tier else None,
        "products": products.to_dict(),
        "platforms": platforms.to_dict(),
        "ai_credits": ai_credits.to_dict(),
        "has_warnings": any([products.is_warning, platforms.is_warning, ai_credits.is_warning]),
        "has_blocked": any([products.is_blocked, platforms.is_blocked, ai_credits.is_blocked]),
    }


def check_and_warn_product_limit(user: User, db: Session) -> QuotaCheckResult:
    """
    Check product limit and raise error if blocked.

    Business Rules (2025-12-19):
    - Returns QuotaCheckResult (can be OK or WARNING)
    - Raises SubscriptionLimitError if BLOCKED

    Args:
        user: User to check
        db: SQLAlchemy session

    Returns:
        QuotaCheckResult (OK or WARNING)

    Raises:
        SubscriptionLimitError: If quota is BLOCKED
    """
    result = get_product_quota_status(user, db)

    if result.is_blocked:
        raise SubscriptionLimitError(
            message=result.message,
            limit_type="products",
            current=result.current,
            max_allowed=result.max_allowed,
        )

    return result


def check_and_warn_platform_limit(user: User, db: Session) -> QuotaCheckResult:
    """
    Check platform limit and raise error if blocked.

    Business Rules (2025-12-19):
    - Returns QuotaCheckResult (can be OK or WARNING)
    - Raises SubscriptionLimitError if BLOCKED

    Args:
        user: User to check
        db: SQLAlchemy session

    Returns:
        QuotaCheckResult (OK or WARNING)

    Raises:
        SubscriptionLimitError: If quota is BLOCKED
    """
    result = get_platform_quota_status(user, db)

    if result.is_blocked:
        raise SubscriptionLimitError(
            message=result.message,
            limit_type="platforms",
            current=result.current,
            max_allowed=result.max_allowed,
        )

    return result


def check_and_warn_ai_credits(user: User, db: Session) -> QuotaCheckResult:
    """
    Check AI credits limit and raise error if blocked.

    Business Rules (2025-12-19):
    - Returns QuotaCheckResult (can be OK or WARNING)
    - Raises SubscriptionLimitError if BLOCKED

    Args:
        user: User to check
        db: SQLAlchemy session

    Returns:
        QuotaCheckResult (OK or WARNING)

    Raises:
        SubscriptionLimitError: If quota is BLOCKED
    """
    result = get_ai_credits_quota_status(user, db)

    if result.is_blocked:
        raise SubscriptionLimitError(
            message=result.message,
            limit_type="ai_credits",
            current=result.current,
            max_allowed=result.max_allowed,
        )

    return result


__all__ = [
    # Original functions (backward compatible)
    "SubscriptionLimitError",
    "check_product_limit",
    "check_platform_limit",
    "check_ai_credits",
    "get_subscription_limits_info",
    # New quota status classes
    "QuotaStatus",
    "QuotaCheckResult",
    "WARNING_THRESHOLD",
    # New functions with warning system
    "get_product_quota_status",
    "get_platform_quota_status",
    "get_ai_credits_quota_status",
    "get_all_quotas_status",
    "check_and_warn_product_limit",
    "check_and_warn_platform_limit",
    "check_and_warn_ai_credits",
]
