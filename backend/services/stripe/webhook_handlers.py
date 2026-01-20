"""
Stripe Webhook Handlers

Strategy pattern for handling different Stripe webhook events.
"""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from models.public.user import User, SubscriptionTier
from models.public.subscription_quota import SubscriptionQuota
from models.public.ai_credit import AICredit

logger = logging.getLogger(__name__)


def handle_checkout_completed(data: dict, db: Session) -> dict:
    """Handle checkout.session.completed event."""
    session = data
    user_id = int(session["metadata"]["user_id"])
    payment_type = session["metadata"]["payment_type"]

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.error(f"User {user_id} not found for checkout session {session['id']}")
        return {"status": "error", "message": "User not found"}

    # SUBSCRIPTION
    if payment_type == "subscription":
        tier_value = session["metadata"]["tier"]
        new_tier = SubscriptionTier(tier_value)

        quota = db.query(SubscriptionQuota).filter(
            SubscriptionQuota.tier == new_tier
        ).first()

        if quota:
            user.subscription_tier = new_tier
            user.subscription_tier_id = quota.id

            if "subscription" in session:
                user.stripe_subscription_id = session["subscription"]

            db.commit()
            logger.info(f"User {user_id} upgraded to {new_tier.value}")

    # CREDITS
    elif payment_type == "credits":
        credits = int(session["metadata"]["credits"])

        ai_credit = db.query(AICredit).filter(AICredit.user_id == user_id).first()

        if not ai_credit:
            ai_credit = AICredit(
                user_id=user_id,
                ai_credits_purchased=credits,
                ai_credits_used_this_month=0,
                last_reset_date=datetime.now()
            )
            db.add(ai_credit)
        else:
            ai_credit.ai_credits_purchased += credits

        db.commit()
        logger.info(f"User {user_id} purchased {credits} AI credits")

    return {"status": "success"}


def handle_subscription_updated(data: dict, db: Session) -> dict:
    """Handle customer.subscription.updated event."""
    subscription = data
    customer_id = subscription["customer"]

    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if not user:
        logger.error(f"User not found for customer {customer_id}")
        return {"status": "error", "message": "User not found"}

    if subscription["status"] in ["active", "trialing"]:
        logger.info(f"Subscription active for user {user.id}")
    elif subscription["status"] in ["past_due", "unpaid"]:
        logger.warning(f"Subscription past_due for user {user.id} - grace period active")
    elif subscription["status"] in ["canceled", "incomplete_expired"]:
        _downgrade_to_free(user, db)
        logger.info(f"User {user.id} downgraded to FREE (subscription canceled)")

    return {"status": "success"}


def handle_subscription_deleted(data: dict, db: Session) -> dict:
    """Handle customer.subscription.deleted event."""
    subscription = data
    customer_id = subscription["customer"]

    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if not user:
        logger.error(f"User not found for customer {customer_id}")
        return {"status": "error", "message": "User not found"}

    _downgrade_to_free(user, db)
    user.stripe_subscription_id = None
    db.commit()
    logger.info(f"User {user.id} downgraded to FREE (subscription deleted)")

    return {"status": "success"}


def handle_payment_failed(data: dict, db: Session) -> dict:
    """Handle invoice.payment_failed event."""
    invoice = data
    customer_id = invoice["customer"]

    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if not user:
        logger.error(f"User not found for customer {customer_id}")
        return {"status": "error", "message": "User not found"}

    logger.warning(f"Payment failed for user {user.id} - grace period of 3 days")
    return {"status": "success"}


def handle_payment_succeeded(data: dict, db: Session) -> dict:
    """Handle invoice.payment_succeeded event."""
    invoice = data
    customer_id = invoice["customer"]

    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if user:
        logger.info(f"Payment succeeded for user {user.id}")

    return {"status": "success"}


def _downgrade_to_free(user: User, db: Session) -> None:
    """Helper to downgrade user to FREE tier."""
    free_quota = db.query(SubscriptionQuota).filter(
        SubscriptionQuota.tier == SubscriptionTier.FREE
    ).first()
    if free_quota:
        user.subscription_tier = SubscriptionTier.FREE
        user.subscription_tier_id = free_quota.id
        db.commit()


# Strategy pattern: map event types to handlers
WEBHOOK_HANDLERS = {
    "checkout.session.completed": handle_checkout_completed,
    "customer.subscription.updated": handle_subscription_updated,
    "customer.subscription.deleted": handle_subscription_deleted,
    "invoice.payment_failed": handle_payment_failed,
    "invoice.payment_succeeded": handle_payment_succeeded,
}


def handle_webhook_event(event_type: str, event_data: dict, db: Session) -> dict:
    """
    Handle a Stripe webhook event.

    Args:
        event_type: Type of Stripe event
        event_data: Event data from Stripe
        db: Database session

    Returns:
        Dict with status and optional message
    """
    handler = WEBHOOK_HANDLERS.get(event_type)
    if handler:
        return handler(event_data, db)
    return {"status": "unhandled"}
