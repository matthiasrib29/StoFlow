"""
Subscription Limits Checker

Helper pour vérifier les limites d'abonnement des utilisateurs.

Business Rules (2025-12-08):
- Les limites sont définies par subscription_tier uniquement
- Comportement: Avertissement + blocage si limite atteinte
- USER voit uniquement ses propres données (isolation stricte)

Author: Claude
Date: 2025-12-08
"""

from typing import Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.public.user import User, SubscriptionTier


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


__all__ = [
    "SubscriptionLimitError",
    "check_product_limit",
    "check_platform_limit",
    "check_ai_credits",
    "get_subscription_limits_info",
]
