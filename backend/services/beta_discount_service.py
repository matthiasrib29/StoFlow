"""
BetaDiscountService - Gestion des réductions beta -50% à vie

Ce service gère:
- Vérification de l'éligibilité au coupon beta
- Marquage des conversions beta → paid
- Révocation des réductions par admin

Business Rules:
- Seuls les beta testers avec status != REVOKED/CANCELLED sont éligibles
- Le coupon STOFLOW_BETA_50 est appliqué automatiquement lors du checkout
- La révocation supprime le coupon de l'abonnement Stripe actif

Author: Claude
Date: 2026-01-20
"""

import logging
from datetime import datetime

import stripe
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.beta_signup import BetaSignup, BetaSignupStatus
from models.public.user import User
from shared.exceptions import StoflowError

logger = logging.getLogger(__name__)

# Stripe coupon ID - must be created manually in Stripe Dashboard
BETA_COUPON_CODE = "STOFLOW_BETA_50"


class BetaDiscountError(StoflowError):
    """Exception for beta discount operations."""
    pass


class BetaDiscountService:
    """
    Service for managing beta tester discounts.

    All methods are static to allow easy use without instantiation.
    """

    @staticmethod
    def is_beta_tester(db: Session, email: str) -> BetaSignup | None:
        """
        Check if an email belongs to an eligible beta tester.

        Args:
            db: Database session
            email: Email address to check

        Returns:
            BetaSignup if eligible, None otherwise
        """
        beta_signup = db.query(BetaSignup).filter(
            func.lower(BetaSignup.email) == func.lower(email)
        ).first()

        if not beta_signup:
            return None

        if not beta_signup.is_eligible_for_discount():
            logger.info(f"Beta signup {beta_signup.id} not eligible (status={beta_signup.status})")
            return None

        return beta_signup

    @staticmethod
    def mark_as_converted(
        db: Session,
        beta_signup_id: int,
        user_id: int
    ) -> BetaSignup | None:
        """
        Mark a beta signup as converted (user created account and subscribed).

        Uses pessimistic locking (SELECT FOR UPDATE) to prevent race conditions
        when multiple webhooks arrive simultaneously for the same user.

        Security Fix 2026-01-20: Added FOR UPDATE lock and idempotency check.

        Args:
            db: Database session
            beta_signup_id: ID of the BetaSignup to update
            user_id: ID of the converted user

        Returns:
            Updated BetaSignup record, or None if already converted
        """
        # Acquire row lock to prevent race conditions
        beta_signup = (
            db.query(BetaSignup)
            .filter(BetaSignup.id == beta_signup_id)
            .with_for_update()
            .first()
        )

        if not beta_signup:
            logger.warning(f"Beta signup {beta_signup_id} not found for conversion")
            return None

        # Idempotency check: already converted
        if beta_signup.status == BetaSignupStatus.CONVERTED:
            logger.info(
                f"Beta signup {beta_signup_id} already converted "
                f"(user_id={beta_signup.user_id}), skipping"
            )
            return beta_signup  # Return existing, no duplicate

        # Check if this user_id was already used for another beta signup
        existing_for_user = db.query(BetaSignup).filter(
            BetaSignup.user_id == user_id,
            BetaSignup.status == BetaSignupStatus.CONVERTED,
            BetaSignup.id != beta_signup_id
        ).first()

        if existing_for_user:
            logger.warning(
                f"User {user_id} already has a converted beta signup "
                f"(id={existing_for_user.id}), rejecting duplicate conversion"
            )
            return None

        beta_signup.status = BetaSignupStatus.CONVERTED
        beta_signup.user_id = user_id
        beta_signup.discount_applied_at = datetime.now()

        db.commit()
        db.refresh(beta_signup)

        logger.info(
            f"Beta signup {beta_signup.id} marked as converted "
            f"(user_id={user_id}, email={beta_signup.email})"
        )

        return beta_signup

    @staticmethod
    def revoke_discount(
        db: Session,
        beta_signup_id: int,
        admin_id: int,
        reason: str
    ) -> BetaSignup:
        """
        Revoke the beta discount for a user.

        This will:
        1. Update the beta_signup status to REVOKED
        2. Remove the coupon from the user's Stripe subscription (if active)

        Args:
            db: Database session
            beta_signup_id: ID of the beta signup to revoke
            admin_id: ID of the admin performing the revocation
            reason: Reason for revocation (min 10 chars)

        Returns:
            Updated BetaSignup record

        Raises:
            BetaDiscountError: If beta signup not found or already revoked
        """
        beta_signup = db.query(BetaSignup).filter(BetaSignup.id == beta_signup_id).first()

        if not beta_signup:
            raise BetaDiscountError(f"Beta signup {beta_signup_id} not found")

        if beta_signup.status == BetaSignupStatus.REVOKED:
            raise BetaDiscountError(f"Beta signup {beta_signup_id} already revoked")

        # If user has an active subscription, remove the coupon
        if beta_signup.user_id:
            user = db.query(User).filter(User.id == beta_signup.user_id).first()
            if user and user.stripe_subscription_id:
                try:
                    BetaDiscountService._remove_coupon_from_subscription(
                        user.stripe_subscription_id
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to remove coupon from subscription "
                        f"{user.stripe_subscription_id}: {e}"
                    )
                    # Continue with revocation even if Stripe fails

        # Update beta signup
        beta_signup.status = BetaSignupStatus.REVOKED
        beta_signup.discount_revoked_at = datetime.now()
        beta_signup.discount_revoked_by = admin_id
        beta_signup.revocation_reason = reason

        db.commit()
        db.refresh(beta_signup)

        logger.info(
            f"Beta discount revoked for signup {beta_signup_id} "
            f"by admin {admin_id}: {reason}"
        )

        return beta_signup

    @staticmethod
    def _remove_coupon_from_subscription(subscription_id: str) -> None:
        """
        Remove the beta coupon from a Stripe subscription.

        This updates the subscription to have no discount.

        Args:
            subscription_id: Stripe subscription ID
        """
        try:
            # Remove all discounts from the subscription
            stripe.Subscription.modify(
                subscription_id,
                discounts=[]  # Empty array removes all discounts
            )
            logger.info(f"Removed coupon from subscription {subscription_id}")
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error removing coupon: {e}")
            raise BetaDiscountError(f"Failed to remove coupon: {str(e)}")

    @staticmethod
    def get_beta_stats(db: Session) -> dict:
        """
        Get statistics about the beta program.

        Returns:
            Dictionary with counts by status
        """
        total = db.query(func.count(BetaSignup.id)).scalar()
        pending = db.query(func.count(BetaSignup.id)).filter(
            BetaSignup.status == BetaSignupStatus.PENDING
        ).scalar()
        converted = db.query(func.count(BetaSignup.id)).filter(
            BetaSignup.status == BetaSignupStatus.CONVERTED
        ).scalar()
        revoked = db.query(func.count(BetaSignup.id)).filter(
            BetaSignup.status == BetaSignupStatus.REVOKED
        ).scalar()
        cancelled = db.query(func.count(BetaSignup.id)).filter(
            BetaSignup.status == BetaSignupStatus.CANCELLED
        ).scalar()

        return {
            "total_signups": total or 0,
            "pending": pending or 0,
            "converted": converted or 0,
            "revoked": revoked or 0,
            "cancelled": cancelled or 0,
        }

    @staticmethod
    def verify_coupon_exists() -> bool:
        """
        Verify that the STOFLOW_BETA_50 coupon exists in Stripe.

        Returns:
            True if coupon exists, False otherwise
        """
        try:
            stripe.Coupon.retrieve(BETA_COUPON_CODE)
            return True
        except stripe.error.InvalidRequestError:
            logger.warning(f"Stripe coupon {BETA_COUPON_CODE} not found")
            return False
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error checking coupon: {e}")
            return False
