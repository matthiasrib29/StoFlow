"""
Stripe API Routes

Routes pour la gestion des paiements via Stripe.

Business Rules (2025-12-10):
- Checkout Sessions pour subscriptions (abonnements récurrents)
- Checkout Sessions pour one-time payments (crédits IA)
- Webhooks pour synchroniser les paiements
- Customer Portal pour gérer les abonnements
- Grace period de 3 jours pour échecs de paiement

Author: Claude
Date: 2025-12-10
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
import stripe
from typing import Literal

from api.dependencies import get_current_user
from models.public.user import User, SubscriptionTier
from models.public.subscription_quota import SubscriptionQuota
from models.public.ai_credit import AICredit
from shared.database import get_db
from shared.stripe_config import (
    STRIPE_SUCCESS_URL,
    STRIPE_CANCEL_URL,
    STRIPE_WEBHOOK_SECRET,
    validate_stripe_config,
)
from repositories.ai_credit_pack_repository import AiCreditPackRepository
from services.ai_credit_pack_service import AiCreditPackService
from services.stripe.webhook_handlers import handle_webhook_event

router = APIRouter(prefix="/stripe", tags=["Stripe"])


# ===== DEPENDENCIES =====

def get_credit_pack_service(db: Session = Depends(get_db)) -> AiCreditPackService:
    """Dependency injection for AiCreditPackService."""
    repository = AiCreditPackRepository()
    return AiCreditPackService(db, repository)


# ===== SCHEMAS =====

class CheckoutSessionRequest(BaseModel):
    """Requête pour créer une session Stripe Checkout."""
    payment_type: Literal["subscription", "credits"]
    tier: SubscriptionTier | None = None  # Pour subscriptions
    credits: int | None = None  # Pour achats de crédits

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "payment_type": "subscription",
                    "tier": "pro"
                },
                {
                    "payment_type": "credits",
                    "credits": 500
                }
            ]
        }
    }


class CheckoutSessionResponse(BaseModel):
    """Réponse avec l'URL de la session Checkout."""
    session_id: str
    url: str


class CustomerPortalResponse(BaseModel):
    """Réponse avec l'URL du Customer Portal."""
    url: str


# ===== ROUTES =====

@router.post(
    "/create-checkout-session",
    response_model=CheckoutSessionResponse,
    status_code=status.HTTP_200_OK
)
def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    credit_pack_service: AiCreditPackService = Depends(get_credit_pack_service)
):
    """
    Crée une session Stripe Checkout pour un abonnement ou un achat de crédits.

    Business Rules (2025-12-10):
    - payment_type='subscription': Créer une subscription Stripe récurrente
    - payment_type='credits': Créer un paiement one-time pour crédits IA
    - Utilise les prix depuis la DB (subscriptions) ou config (crédits)
    - Stocke user_id et metadata dans la session pour le webhook

    Args:
        request: Type de paiement et détails
        current_user: Utilisateur authentifié
        db: Session DB

    Returns:
        CheckoutSessionResponse: URL de la session Checkout

    Raises:
        HTTPException: 400 si paramètres invalides
        HTTPException: 500 si erreur Stripe
    """
    try:
        # Valider la configuration Stripe
        validate_stripe_config()

        # Créer ou récupérer le Stripe Customer
        if not current_user.stripe_customer_id:
            # Créer un nouveau customer Stripe
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={
                    "user_id": str(current_user.id),
                    "username": current_user.username,
                }
            )
            current_user.stripe_customer_id = customer.id
            db.commit()
        else:
            customer_id = current_user.stripe_customer_id

        # Paramètres communs
        checkout_params = {
            "customer": current_user.stripe_customer_id,
            "mode": None,  # Sera défini selon le type
            "success_url": STRIPE_SUCCESS_URL,
            "cancel_url": STRIPE_CANCEL_URL,
            "metadata": {
                "user_id": str(current_user.id),
                "payment_type": request.payment_type,
            }
        }

        # === SUBSCRIPTION ===
        if request.payment_type == "subscription":
            if not request.tier:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Le paramètre 'tier' est requis pour un abonnement"
                )

            # Récupérer le quota pour ce tier
            quota = db.query(SubscriptionQuota).filter(
                SubscriptionQuota.tier == request.tier
            ).first()

            if not quota:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tier '{request.tier.value}' non trouvé"
                )

            # Vérifier que ce n'est pas le tier FREE
            if request.tier == SubscriptionTier.FREE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Impossible de créer une session Checkout pour le tier FREE"
                )

            # Créer le line item pour l'abonnement
            checkout_params["mode"] = "subscription"
            checkout_params["line_items"] = [
                {
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": f"Abonnement Stoflow {request.tier.value.upper()}",
                            "description": (
                                f"{quota.max_products} produits, "
                                f"{quota.max_platforms} plateformes, "
                                f"{quota.ai_credits_monthly} crédits IA/mois"
                            ),
                        },
                        "unit_amount": int(quota.price * 100),  # Convertir en centimes
                        "recurring": {
                            "interval": "month",
                        },
                    },
                    "quantity": 1,
                }
            ]
            checkout_params["metadata"]["tier"] = request.tier.value

        # === CREDITS ===
        elif request.payment_type == "credits":
            if not request.credits:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Le paramètre 'credits' est requis pour un achat de crédits"
                )

            # Récupérer le pack depuis la DB via le service (avec cache)
            pack_entity = credit_pack_service.get_pack_by_credits(request.credits)

            if not pack_entity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Pack de {request.credits} crédits non disponible"
                )

            # Créer le line item pour les crédits (prix depuis DB)
            checkout_params["mode"] = "payment"
            checkout_params["line_items"] = [
                {
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": pack_entity.name,
                            "description": pack_entity.description,
                        },
                        "unit_amount": int(pack_entity.price * 100),  # Convertir en centimes
                    },
                    "quantity": 1,
                }
            ]
            checkout_params["metadata"]["credits"] = str(request.credits)

        # Créer la session Checkout
        session = stripe.checkout.Session.create(**checkout_params)

        return CheckoutSessionResponse(
            session_id=session.id,
            url=session.url
        )

    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur Stripe: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de la session: {str(e)}"
        )


@router.post(
    "/customer-portal",
    response_model=CustomerPortalResponse,
    status_code=status.HTTP_200_OK
)
def create_customer_portal_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crée une session Customer Portal pour gérer l'abonnement.

    Le Customer Portal permet à l'utilisateur de:
    - Mettre à jour son moyen de paiement
    - Annuler son abonnement
    - Voir l'historique des factures

    Args:
        current_user: Utilisateur authentifié
        db: Session DB

    Returns:
        CustomerPortalResponse: URL du Customer Portal

    Raises:
        HTTPException: 400 si pas de Stripe Customer ID
        HTTPException: 500 si erreur Stripe
    """
    try:
        if not current_user.stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucun abonnement Stripe trouvé"
            )

        # Créer une session Customer Portal
        session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=f"{STRIPE_SUCCESS_URL.split('?')[0].replace('/success', '')}",
        )

        return CustomerPortalResponse(url=session.url)

    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur Stripe: {str(e)}"
        )


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    include_in_schema=False  # Ne pas afficher dans la doc Swagger
)
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Webhook pour recevoir les événements Stripe.

    Business Rules (2025-12-10):
    - checkout.session.completed: Marquer le paiement comme réussi
    - customer.subscription.updated: Mettre à jour le tier si changement
    - customer.subscription.deleted: Rétrograder au tier FREE
    - invoice.payment_failed: Gérer les échecs (grace period de 3 jours)

    Args:
        request: Requête HTTP brute (pour signature)
        db: Session DB

    Returns:
        dict: {"status": "success"}

    Raises:
        HTTPException: 400 si signature invalide
    """
    import logging

    logger = logging.getLogger(__name__)

    # Récupérer le payload brut et la signature
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        # Vérifier la signature du webhook
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    logger.info(f"Received Stripe event: {event['type']} - {event['id']}")

    try:
        result = handle_webhook_event(event["type"], event["data"]["object"], db)
        return result
    except Exception as e:
        logger.error(f"Error processing webhook {event['type']}: {e}")
        # Retourner 200 pour éviter que Stripe ne retry indéfiniment
        return {"status": "error", "message": str(e)}
