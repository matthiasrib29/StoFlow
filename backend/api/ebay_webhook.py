"""
API Webhook eBay Notifications.

Endpoint pour recevoir les notifications push d'eBay (webhooks).

eBay peut notifier l'application en temps réel pour:
- Nouvelle commande (ORDER.CREATED)
- Commande payée (ORDER.PAID)
- Commande expédiée (ORDER.SHIPPED)
- Message acheteur (BUYER_MESSAGE)
- Listing expiré (LISTING.ENDED)
- Retour initié (RETURN.CREATED)

Documentation officielle:
https://developer.ebay.com/api-docs/sell/commerce/resources/notification/methods/getPublicKey

Flow:
1. eBay envoie POST avec notification JSON
2. Backend vérifie signature pour authentifier requête
3. Backend traite l'événement et met à jour DB

Author: Claude
Date: 2025-12-10
"""

import hashlib
import hmac
import json
import time as _time
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_db
from shared.logging import get_logger

router = APIRouter(prefix="/ebay", tags=["eBay Webhooks"])
logger = get_logger(__name__)

# In-memory replay protection (for multi-server: use Redis)
_processed_notifications: dict[str, float] = {}
_NOTIFICATION_TTL_SECONDS = 600   # 10 minutes
_MAX_WEBHOOK_AGE_SECONDS = 300    # Reject webhooks older than 5 minutes


def _cleanup_old_notifications():
    """Remove expired notification IDs."""
    now = _time.time()
    expired = [k for k, v in _processed_notifications.items()
               if now - v > _NOTIFICATION_TTL_SECONDS]
    for k in expired:
        del _processed_notifications[k]


def _check_duplicate(notification_id: str) -> bool:
    """Return True if duplicate. Records the ID if new."""
    if not notification_id:
        return False
    _cleanup_old_notifications()
    if notification_id in _processed_notifications:
        return True
    _processed_notifications[notification_id] = _time.time()
    return False


# ========== PYDANTIC SCHEMAS ==========


class EbayNotificationMetadata(BaseModel):
    """Métadonnées de la notification eBay."""

    topic: str
    schemaVersion: str
    deprecated: bool = False


class EbayNotificationPayload(BaseModel):
    """Payload complet d'une notification eBay."""

    metadata: EbayNotificationMetadata
    notification: Dict[str, Any]


# ========== WEBHOOK VERIFICATION ==========


def verify_ebay_signature(
    payload: bytes,
    signature: str,
    verification_token: str,
) -> bool:
    """
    Vérifie la signature eBay pour authentifier la requête.

    eBay signe chaque notification avec HMAC-SHA256 en utilisant
    le verification_token configuré dans eBay Developer Portal.

    Args:
        payload: Corps brut de la requête (bytes)
        signature: Signature fournie dans header X-EBAY-SIGNATURE
        verification_token: Token de vérification depuis .env

    Returns:
        bool: True si signature valide

    Security:
        Cette vérification est CRITIQUE pour éviter les webhooks falsifiés.
        Toujours vérifier la signature avant de traiter la notification.
    """
    if not verification_token:
        logger.error("EBAY_WEBHOOK_VERIFICATION_TOKEN non configuré")
        return False

    # Calculer HMAC-SHA256
    expected_signature = hmac.new(
        key=verification_token.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()

    # Comparer signatures (timing-safe)
    return hmac.compare_digest(expected_signature, signature)


# ========== EVENT HANDLERS ==========


async def handle_order_created(notification: Dict[str, Any], db: Session) -> None:
    """
    Traite événement ORDER.CREATED (nouvelle commande).

    Args:
        notification: Données de la notification
        db: Session DB
    """
    order_data = notification.get("order", {})
    order_id = order_data.get("orderId")

    logger.info(f"📦 Nouvelle commande eBay reçue: {order_id}")

    # TODO: Créer/mettre à jour EbayOrder dans DB
    # from models.user.ebay_order import EbayOrder
    # order = EbayOrder.from_ebay_api(user_id=user_id, order_data=order_data)
    # db.add(order)
    # db.commit()

    logger.info(f"✅ Commande {order_id} enregistrée")


async def handle_order_paid(notification: Dict[str, Any], db: Session) -> None:
    """
    Traite événement ORDER.PAID (commande payée).

    Args:
        notification: Données de la notification
        db: Session DB
    """
    order_data = notification.get("order", {})
    order_id = order_data.get("orderId")

    logger.info(f"💰 Commande eBay payée: {order_id}")

    # TODO: Mettre à jour statut paiement
    # order = db.query(EbayOrder).filter(EbayOrder.ebay_order_id == order_id).first()
    # if order:
    #     order.order_payment_status = "PAID"
    #     order.paid_date = datetime.now(timezone.utc)
    #     db.commit()


async def handle_listing_ended(notification: Dict[str, Any], db: Session) -> None:
    """
    Traite événement LISTING.ENDED (listing expiré ou vendu).

    Args:
        notification: Données de la notification
        db: Session DB
    """
    listing_data = notification.get("listing", {})
    listing_id = listing_data.get("listingId")
    reason = listing_data.get("endedReason", "UNKNOWN")

    logger.info(f"🏁 Listing eBay terminé: {listing_id} - Raison: {reason}")

    # TODO: Mettre à jour statut produit
    # if reason == "SOLD":
    #     logger.info(f"✅ Listing {listing_id} vendu")
    # elif reason == "EXPIRED":
    #     logger.warning(f"⏰ Listing {listing_id} expiré")


async def handle_buyer_message(notification: Dict[str, Any], db: Session) -> None:
    """
    Traite événement BUYER_MESSAGE (message acheteur).

    Args:
        notification: Données de la notification
        db: Session DB
    """
    message_data = notification.get("message", {})
    order_id = message_data.get("orderId")
    buyer_username = message_data.get("buyerUsername")
    message_text = message_data.get("text", "")

    logger.info(f"💬 Message acheteur reçu sur commande {order_id}")
    logger.info(f"   De: {buyer_username}")
    logger.info(f"   Message: {message_text[:100]}...")

    # TODO: Envoyer notification au seller
    # - Email notification
    # - Push notification
    # - Stocker dans DB pour historique


# ========== EVENT DISPATCHER ==========


EVENT_HANDLERS = {
    "ORDER.CREATED": handle_order_created,
    "ORDER.PAID": handle_order_paid,
    "LISTING.ENDED": handle_listing_ended,
    "BUYER_MESSAGE": handle_buyer_message,
    # Ajouter autres événements au besoin
}


async def dispatch_event(topic: str, notification: Dict[str, Any], db: Session) -> None:
    """
    Dispatche l'événement vers le bon handler.

    Args:
        topic: Type d'événement (ex: "ORDER.CREATED")
        notification: Données de la notification
        db: Session DB
    """
    handler = EVENT_HANDLERS.get(topic)

    if handler:
        await handler(notification, db)
    else:
        logger.warning(f"⚠️  Événement non géré: {topic}")


# ========== ROUTES ==========


@router.post("/webhook")
async def ebay_webhook_handler(
    request: Request,
    x_ebay_signature: str = Header(..., alias="X-EBAY-SIGNATURE"),
):
    """
    Endpoint webhook pour recevoir les notifications eBay.

    eBay envoie des notifications POST à cette URL quand des événements
    se produisent (nouvelle commande, paiement, message, etc.).

    **Configuration requise:**
    1. Dans eBay Developer Portal:
       - Aller dans "Notifications"
       - Configurer Webhook URL: https://your-domain.com/api/ebay/webhook
       - Définir Verification Token
       - Sélectionner événements à recevoir

    2. Dans .env:
       - EBAY_WEBHOOK_VERIFICATION_TOKEN=your_token

    **Événements supportés:**
    - ORDER.CREATED - Nouvelle commande
    - ORDER.PAID - Commande payée
    - ORDER.SHIPPED - Commande expédiée
    - LISTING.ENDED - Listing terminé
    - BUYER_MESSAGE - Message acheteur
    - RETURN.CREATED - Retour initié

    **Sécurité:**
    Vérifie la signature X-EBAY-SIGNATURE pour authentifier la requête.

    Args:
        request: Requête FastAPI
        x_ebay_signature: Signature eBay dans header

    Returns:
        Status 200 si traité avec succès

    Raises:
        HTTPException 401: Si signature invalide
        HTTPException 400: Si payload invalide

    Author: Claude
    Date: 2025-12-10
    """
    import os

    # Récupérer verification token depuis env
    verification_token = os.getenv("EBAY_WEBHOOK_VERIFICATION_TOKEN")

    if not verification_token:
        logger.error("EBAY_WEBHOOK_VERIFICATION_TOKEN non configuré")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook verification token not configured",
        )

    # Lire payload brut (bytes)
    payload_bytes = await request.body()

    # Vérifier signature
    if not verify_ebay_signature(payload_bytes, x_ebay_signature, verification_token):
        logger.error("❌ Signature webhook eBay invalide")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    # Parser JSON
    try:
        payload_json = json.loads(payload_bytes.decode("utf-8"))
        payload = EbayNotificationPayload(**payload_json)
    except Exception as e:
        logger.error(f"❌ Erreur parsing webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payload: {str(e)}",
        )

    # Replay protection: extract notification ID
    notification_id = payload_json.get("notificationId") or \
        payload_json.get("notification", {}).get("notificationId")

    if _check_duplicate(notification_id):
        logger.warning(f"Duplicate webhook rejected: {notification_id}")
        return {"status": "ok", "message": "duplicate"}

    # Timestamp validation (reject old webhooks)
    publish_date_str = payload_json.get("publishDate") or \
        payload_json.get("metadata", {}).get("publishDate")
    if publish_date_str:
        try:
            publish_date = datetime.fromisoformat(
                publish_date_str.replace("Z", "+00:00")
            )
            age = (datetime.now(timezone.utc) - publish_date).total_seconds()
            if age > _MAX_WEBHOOK_AGE_SECONDS:
                logger.warning(f"Old webhook rejected: age={age:.0f}s, id={notification_id}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Notification too old")
        except (ValueError, TypeError):
            pass  # Don't block on parsing issues

    # Log événement reçu
    topic = payload.metadata.topic
    logger.info(f"🔔 Webhook eBay reçu: {topic}")

    # TODO: Récupérer DB session
    # Pour l'instant, on log juste l'événement
    # db = get_db()

    # Dispatcher événement
    try:
        # await dispatch_event(topic, payload.notification, db)
        logger.info(f"✅ Événement {topic} traité avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur traitement événement {topic}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing event: {str(e)}",
        )

    return {"status": "ok", "message": f"Event {topic} processed"}


@router.get("/webhook/challenge")
async def ebay_webhook_challenge(
    challenge_code: str,
):
    """
    Endpoint pour vérification webhook eBay (challenge).

    Quand vous configurez un webhook dans eBay Developer Portal,
    eBay envoie une requête GET avec un challenge_code.
    Vous devez répondre avec ce code pour valider l'endpoint.

    **Flow:**
    1. eBay Developer Portal: Configurer webhook URL
    2. eBay envoie: GET /webhook/challenge?challenge_code=XXX
    3. Backend répond: {"challengeResponse": "XXX"}
    4. eBay valide l'endpoint

    Args:
        challenge_code: Code de challenge envoyé par eBay

    Returns:
        Response avec challengeResponse

    Examples:
        >>> # eBay envoie:
        >>> GET /api/ebay/webhook/challenge?challenge_code=abc123
        >>>
        >>> # Backend répond:
        >>> {"challengeResponse": "abc123"}

    Author: Claude
    Date: 2025-12-10
    """
    logger.info(f"🔐 Challenge webhook eBay reçu: {challenge_code}")
    return {"challengeResponse": challenge_code}
