"""
BetaDiscountService - Gestion des réductions beta -50% à vie

Ce service gère:
- Vérification de l'éligibilité au coupon beta
- Application du coupon lors du checkout Stripe

Note: Les fonctionnalités avancées (conversion tracking, revocation) seront
ajoutées après le déploiement initial de la landing page, une fois la migration
des colonnes supplémentaires appliquée.

Author: Claude
Date: 2026-01-20 (simplified 2026-01-21)
"""

import logging

import stripe
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.beta_signup import BetaSignup
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

    Note: This is a simplified version for the beta landing page.
    Advanced features (conversion tracking, admin revocation) require
    additional database columns that will be added later.
    """

    @staticmethod
    def is_beta_tester(db: Session, email: str) -> BetaSignup | None:
        """
        Check if an email belongs to an eligible beta tester.

        Eligibility criteria:
        - Must have a beta_signup record
        - Status must be 'pending' (not cancelled)

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

        # Eligible if status is pending (waiting for conversion)
        # Once they subscribe, they'll get the discount
        if beta_signup.status not in ("pending", "converted"):
            logger.info(f"Beta signup {beta_signup.id} not eligible (status={beta_signup.status})")
            return None

        return beta_signup

    @staticmethod
    def get_beta_stats(db: Session) -> dict:
        """
        Get statistics about the beta program.

        Returns:
            Dictionary with counts by status
        """
        total = db.query(func.count(BetaSignup.id)).scalar()
        pending = db.query(func.count(BetaSignup.id)).filter(
            BetaSignup.status == "pending"
        ).scalar()
        converted = db.query(func.count(BetaSignup.id)).filter(
            BetaSignup.status == "converted"
        ).scalar()
        cancelled = db.query(func.count(BetaSignup.id)).filter(
            BetaSignup.status == "cancelled"
        ).scalar()

        return {
            "total_signups": total or 0,
            "pending": pending or 0,
            "converted": converted or 0,
            "revoked": 0,  # Not implemented yet
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

    # ========================================
    # ADVANCED FEATURES (disabled for now)
    # ========================================
    # The following methods require additional database columns:
    # - user_id
    # - discount_applied_at
    # - discount_revoked_at
    # - discount_revoked_by
    # - revocation_reason
    #
    # These will be enabled after the migration is applied.

    @staticmethod
    def mark_as_converted(
        db: Session,
        beta_signup_id: int,
        user_id: int
    ) -> BetaSignup | None:
        """
        Mark a beta signup as converted.

        NOTE: Simplified version - only updates status, does not track user_id.
        Full tracking will be enabled after migration adds required columns.
        """
        beta_signup = (
            db.query(BetaSignup)
            .filter(BetaSignup.id == beta_signup_id)
            .with_for_update()
            .first()
        )

        if not beta_signup:
            logger.warning(f"Beta signup {beta_signup_id} not found for conversion")
            return None

        # Already converted - idempotent
        if beta_signup.status == "converted":
            logger.info(f"Beta signup {beta_signup_id} already converted, skipping")
            return beta_signup

        # Mark as converted (simple status change only)
        beta_signup.status = "converted"
        db.commit()
        db.refresh(beta_signup)

        logger.info(
            f"Beta signup {beta_signup_id} marked as converted "
            f"(email={beta_signup.email})"
        )

        return beta_signup

    @staticmethod
    def revoke_discount(
        db: Session,
        beta_signup_id: int,
        admin_id: int,
        reason: str
    ) -> None:
        """
        Revoke the beta discount for a user.

        NOTE: This feature is disabled until the required database columns
        are added via migration.

        Raises:
            BetaDiscountError: Always - feature not yet available
        """
        raise BetaDiscountError(
            "La révocation des réductions beta n'est pas encore disponible. "
            "Cette fonctionnalité sera activée après la migration de la base de données."
        )
