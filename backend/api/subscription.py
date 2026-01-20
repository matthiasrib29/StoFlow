"""
Subscription API Routes

Routes pour la gestion des abonnements utilisateur.

Business Rules (2025-12-10):
- USER peut changer son propre abonnement (upgrade/downgrade)
- ADMIN peut changer l'abonnement de n'importe quel utilisateur
- SUPPORT peut uniquement consulter (lecture seule)
- Changement de tier = mise à jour de subscription_tier_id
- Paiement simulé avec délai de 2s (MVP)
- Crédits IA = mensuels (abonnement) + achetés - utilisés ce mois

Author: Claude
Date: 2025-12-10
"""

import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from models.public.user import User, UserRole, SubscriptionTier
from models.public.subscription_quota import SubscriptionQuota
from models.public.ai_credit import AICredit
from models.public.ai_credit_pack import AiCreditPack
from shared.database import get_db
from shared.access_control import ensure_can_modify

router = APIRouter(prefix="/subscription", tags=["Subscription"])


# ===== SCHEMAS =====

class SubscriptionUpgradeRequest(BaseModel):
    """Requête de changement d'abonnement."""
    new_tier: SubscriptionTier

    model_config = {
        "json_schema_extra": {
            "example": {
                "new_tier": "pro"
            }
        }
    }


class SubscriptionInfoResponse(BaseModel):
    """Informations sur l'abonnement actuel."""
    user_id: int
    current_tier: str
    price: float

    # Quotas
    max_products: int
    max_platforms: int
    ai_credits_monthly: int

    # Usage counters (Added: 2025-12-10)
    current_products_count: int
    current_platforms_count: int

    # AI Credits (Added: 2025-12-10)
    ai_credits_purchased: int
    ai_credits_used_this_month: int
    ai_credits_remaining: int

    model_config = {"from_attributes": True}


class CreditPurchaseRequest(BaseModel):
    """Requête d'achat de crédits IA."""
    credits: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "credits": 500
            }
        }
    }


class PaymentSimulationRequest(BaseModel):
    """Requête de simulation de paiement pour upgrade."""
    new_tier: SubscriptionTier

    model_config = {
        "json_schema_extra": {
            "example": {
                "new_tier": "pro"
            }
        }
    }


# ===== ROUTES =====

@router.get(
    "/info",
    response_model=SubscriptionInfoResponse,
    status_code=status.HTTP_200_OK
)
def get_subscription_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retourne les informations d'abonnement de l'utilisateur connecté.

    Business Rules (2025-12-10):
    - USER voit son propre abonnement
    - ADMIN et SUPPORT voient leur propre abonnement (pas celui des autres)
    - Inclut les compteurs d'utilisation et crédits IA restants

    Args:
        current_user: Utilisateur authentifié
        db: Session DB

    Returns:
        SubscriptionInfoResponse: Info abonnement complète
    """
    # Récupérer ou créer l'enregistrement AI credits
    ai_credit = db.query(AICredit).filter(AICredit.user_id == current_user.id).first()

    if not ai_credit:
        # Créer un enregistrement AI credits si il n'existe pas
        ai_credit = AICredit(
            user_id=current_user.id,
            ai_credits_purchased=0,
            ai_credits_used_this_month=0,
            last_reset_date=datetime.now()
        )
        db.add(ai_credit)
        db.commit()
        db.refresh(ai_credit)

    # Calculer les crédits restants
    ai_credits_remaining = ai_credit.get_remaining_credits(
        current_user.subscription_quota.ai_credits_monthly
    )

    return SubscriptionInfoResponse(
        user_id=current_user.id,
        current_tier=current_user.subscription_tier.value,
        price=float(current_user.subscription_quota.price),
        max_products=current_user.subscription_quota.max_products,
        max_platforms=current_user.subscription_quota.max_platforms,
        ai_credits_monthly=current_user.subscription_quota.ai_credits_monthly,
        current_products_count=current_user.current_products_count,
        current_platforms_count=current_user.current_platforms_count,
        ai_credits_purchased=ai_credit.ai_credits_purchased,
        ai_credits_used_this_month=ai_credit.ai_credits_used_this_month,
        ai_credits_remaining=ai_credits_remaining,
    )


@router.post(
    "/upgrade",
    response_model=SubscriptionInfoResponse,
    status_code=status.HTTP_200_OK
)
def upgrade_subscription(
    request: SubscriptionUpgradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change le tier d'abonnement de l'utilisateur.

    Business Rules (2025-12-09):
    - USER peut changer son propre abonnement
    - ADMIN peut changer son propre abonnement
    - SUPPORT ne peut PAS modifier (lecture seule)
    - Le changement est immédiat (pas de paiement dans V1)

    Args:
        request: Nouveau tier
        current_user: Utilisateur authentifié
        db: Session DB

    Returns:
        SubscriptionInfoResponse: Nouvel abonnement

    Raises:
        HTTPException: 403 si SUPPORT essaie de modifier
        HTTPException: 404 si le tier n'existe pas
    """
    # SUPPORT ne peut pas modifier
    ensure_can_modify(current_user, "abonnement")

    # Vérifier que le nouveau tier existe
    new_quota = (
        db.query(SubscriptionQuota)
        .filter(SubscriptionQuota.tier == request.new_tier)
        .first()
    )

    if not new_quota:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription tier '{request.new_tier.value}' not found"
        )

    # Mettre à jour le tier de l'utilisateur
    current_user.subscription_tier = request.new_tier
    current_user.subscription_tier_id = new_quota.id

    db.commit()
    db.refresh(current_user)

    return SubscriptionInfoResponse(
        user_id=current_user.id,
        current_tier=current_user.subscription_tier.value,
        max_products=current_user.subscription_quota.max_products,
        max_platforms=current_user.subscription_quota.max_platforms,
        ai_credits_monthly=current_user.subscription_quota.ai_credits_monthly,
    )


@router.get(
    "/tiers",
    status_code=status.HTTP_200_OK
)
def get_available_tiers(
    db: Session = Depends(get_db)
):
    """
    Retourne la liste des tiers d'abonnement disponibles.

    Business Rules (2025-12-10):
    - Endpoint PUBLIC (pas d'authentification requise)
    - Utilisé pour la page pricing et le choix d'abonnement
    - Retourne les quotas, prix et features de chaque tier

    Args:
        db: Session DB

    Returns:
        dict: Liste des tiers avec leurs quotas, prix et features
    """
    from sqlalchemy.orm import joinedload

    quotas = (
        db.query(SubscriptionQuota)
        .options(joinedload(SubscriptionQuota.features))
        .order_by(SubscriptionQuota.display_order)
        .all()
    )

    return {
        "tiers": [
            {
                "tier": quota.tier.value,
                "display_name": quota.display_name,
                "description": quota.description,
                "price": float(quota.price) if quota.price else 0,
                "annual_discount_percent": quota.annual_discount_percent,
                "is_popular": quota.is_popular,
                "cta_text": quota.cta_text,
                "max_products": quota.max_products,
                "max_platforms": quota.max_platforms,
                "ai_credits_monthly": quota.ai_credits_monthly,
                "features": [
                    {"feature_text": f.feature_text, "display_order": f.display_order}
                    for f in sorted(quota.features, key=lambda x: x.display_order)
                ]
            }
            for quota in quotas
        ]
    }


@router.get(
    "/credit-packs",
    status_code=status.HTTP_200_OK
)
def get_credit_packs(
    db: Session = Depends(get_db)
):
    """
    Retourne les packs de crédits IA disponibles à l'achat.

    Business Rules (2026-01-14):
    - Endpoint PUBLIC (pas d'authentification requise)
    - Utilisé pour la page crédits
    - Retourne uniquement les packs actifs
    - Triés par display_order

    Args:
        db: Session DB

    Returns:
        dict: Liste des packs avec prix et détails
    """
    packs = (
        db.query(AiCreditPack)
        .filter(AiCreditPack.is_active == True)
        .order_by(AiCreditPack.display_order)
        .all()
    )

    return {
        "packs": [pack.to_dict() for pack in packs]
    }


@router.post(
    "/payment/simulate-upgrade",
    response_model=SubscriptionInfoResponse,
    status_code=status.HTTP_200_OK
)
async def simulate_upgrade_payment(
    request: PaymentSimulationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Simule le paiement et effectue l'upgrade d'abonnement.

    Business Rules (2025-12-10):
    - Simulation: délai de 2 secondes pour simuler le traitement du paiement
    - L'upgrade est effectué après le "paiement"
    - Retourne les nouvelles informations d'abonnement

    Args:
        request: Nouveau tier souhaité
        current_user: Utilisateur authentifié
        db: Session DB

    Returns:
        SubscriptionInfoResponse: Nouvelles informations d'abonnement

    Raises:
        HTTPException: 403 si SUPPORT essaie de modifier
        HTTPException: 404 si le tier n'existe pas
    """
    # SUPPORT ne peut pas modifier
    ensure_can_modify(current_user, "abonnement")

    # Vérifier que le nouveau tier existe
    new_quota = (
        db.query(SubscriptionQuota)
        .filter(SubscriptionQuota.tier == request.new_tier)
        .first()
    )

    if not new_quota:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription tier '{request.new_tier.value}' not found"
        )

    # Simuler le délai de traitement du paiement (2 secondes)
    await asyncio.sleep(2)

    # Mettre à jour le tier de l'utilisateur
    current_user.subscription_tier = request.new_tier
    current_user.subscription_tier_id = new_quota.id

    db.commit()
    db.refresh(current_user)

    # Récupérer les infos complètes avec get_subscription_info
    return get_subscription_info(current_user, db)


@router.post(
    "/credits/purchase",
    response_model=SubscriptionInfoResponse,
    status_code=status.HTTP_200_OK
)
async def purchase_credits(
    request: CreditPurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Simule l'achat de crédits IA et les ajoute au compte.

    Business Rules (2025-12-10):
    - Simulation: délai de 2 secondes pour simuler le traitement du paiement
    - Les crédits achetés sont ajoutés à ai_credits_purchased
    - Les crédits achetés ne s'épuisent jamais
    - Retourne les nouvelles informations d'abonnement

    Args:
        request: Nombre de crédits à acheter
        current_user: Utilisateur authentifié
        db: Session DB

    Returns:
        SubscriptionInfoResponse: Informations d'abonnement avec nouveaux crédits

    Raises:
        HTTPException: 403 si SUPPORT essaie de modifier
        HTTPException: 400 si le nombre de crédits est invalide
    """
    # SUPPORT ne peut pas modifier
    ensure_can_modify(current_user, "crédits IA")

    # Valider le nombre de crédits
    if request.credits <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nombre de crédits doit être positif"
        )

    # Simuler le délai de traitement du paiement (2 secondes)
    await asyncio.sleep(2)

    # Récupérer ou créer l'enregistrement AI credits
    ai_credit = db.query(AICredit).filter(AICredit.user_id == current_user.id).first()

    if not ai_credit:
        ai_credit = AICredit(
            user_id=current_user.id,
            ai_credits_purchased=request.credits,
            ai_credits_used_this_month=0,
            last_reset_date=datetime.now()
        )
        db.add(ai_credit)
    else:
        # Ajouter les crédits achetés
        ai_credit.ai_credits_purchased += request.credits

    db.commit()
    db.refresh(current_user)

    # Récupérer les infos complètes avec get_subscription_info
    return get_subscription_info(current_user, db)
