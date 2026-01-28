"""
Stripe Webhook Handlers

Strategy pattern for handling different Stripe webhook events.
"""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from models.public.user import User, SubscriptionTier
from models.public.subscription_quota import SubscriptionQuota

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

        # Add purchased credits directly to user
        user.ai_credits_purchased += credits

        db.commit()
        logger.info(f"User {user_id} purchased {credits} AI credits")

    return {"status": "success"}


def handle_subscription_updated(data: dict, db: Session) -> dict:
    """
    Handle customer.subscription.updated event.

    Issue #18 - Business Logic Audit: Grace period for downgrades.
    If cancel_at_period_end is true, the user has scheduled cancellation
    but should keep their current tier until the billing period ends.
    Only downgrade on immediate cancellation (status=canceled).
    """
    subscription = data
    customer_id = subscription["customer"]

    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if not user:
        logger.error(f"User not found for customer {customer_id}")
        return {"status": "error", "message": "User not found"}

    # Grace period: if user scheduled cancellation at period end,
    # keep current tier until the period actually ends (Issue #18)
    if subscription.get("cancel_at_period_end"):
        logger.info(
            f"User {user.id} scheduled cancellation at period end - "
            f"keeping current tier until billing period expires"
        )
        return {"status": "success", "grace_period": True}

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


def handle_charge_refunded(data: dict, db: Session) -> dict:
    """
    Handle charge.refunded event.

    Reverses credits if the refunded charge was a credits purchase.
    Issue #19 - Business Logic Audit.

    Args:
        data: Stripe charge object with refund info.
        db: Database session.

    Returns:
        Dict with status.
    """
    charge = data
    customer_id = charge.get("customer")

    if not customer_id:
        logger.warning(f"Charge refund without customer_id: {charge.get('id')}")
        return {"status": "skipped", "message": "No customer_id"}

    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if not user:
        logger.error(f"User not found for customer {customer_id} (charge refund)")
        return {"status": "error", "message": "User not found"}

    # Check if this was a credits purchase (metadata from checkout session)
    metadata = charge.get("metadata", {})
    payment_type = metadata.get("payment_type")

    if payment_type == "credits":
        refunded_credits = int(metadata.get("credits", 0))
        if refunded_credits > 0:
            previous = user.ai_credits_purchased
            user.ai_credits_purchased = max(0, user.ai_credits_purchased - refunded_credits)
            db.commit()
            logger.info(
                f"Refund: reversed {refunded_credits} credits for user {user.id} "
                f"(was {previous}, now {user.ai_credits_purchased})"
            )
            return {"status": "success", "credits_reversed": refunded_credits}

    logger.info(f"Charge refunded for user {user.id} (non-credits payment)")
    return {"status": "success"}


# Strategy pattern: map event types to handlers
WEBHOOK_HANDLERS = {
    "checkout.session.completed": handle_checkout_completed,
    "customer.subscription.updated": handle_subscription_updated,
    "customer.subscription.deleted": handle_subscription_deleted,
    "invoice.payment_failed": handle_payment_failed,
    "invoice.payment_succeeded": handle_payment_succeeded,
    "charge.refunded": handle_charge_refunded,
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
