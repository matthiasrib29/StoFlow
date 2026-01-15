"""
Beta signup routes - Public endpoints for beta program registration.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models.public.beta_signup import BetaSignup
from schemas.beta import (
    BetaSignupCreate,
    BetaSignupSuccessMessage,
    BetaSignupErrorMessage,
)
from shared.database import get_db
from shared.logging_setup import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/beta", tags=["beta"])


@router.post(
    "/signup",
    response_model=BetaSignupSuccessMessage,
    status_code=status.HTTP_201_CREATED,
    summary="Sign up for beta program",
    description="Register for the Stoflow beta program waitlist. Public endpoint, no authentication required.",
)
def create_beta_signup(
    signup_data: BetaSignupCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new beta signup.

    Args:
        signup_data: Email and optional profile information
        db: Database session

    Returns:
        Success message with signup details

    Raises:
        HTTPException 400: If email already registered
        HTTPException 500: If database error occurs
    """
    try:
        # Create new beta signup
        new_signup = BetaSignup(
            email=signup_data.email,
            first_name=signup_data.first_name,
            vendor_type=signup_data.vendor_type,
            monthly_volume=signup_data.monthly_volume,
            status="pending",
        )

        db.add(new_signup)
        db.commit()
        db.refresh(new_signup)

        logger.info(f"New beta signup: {new_signup.email}")

        return BetaSignupSuccessMessage(
            success=True,
            message="Inscription réussie ! Vérifiez votre email.",
            data=new_signup,
        )

    except IntegrityError as e:
        db.rollback()
        logger.warning(f"Duplicate email signup attempt: {signup_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà inscrit à la beta.",
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating beta signup: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur est survenue. Veuillez réessayer.",
        )
