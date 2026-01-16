"""
Beta signup routes - Public endpoints for beta program registration.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from models.beta_signup import BetaSignup, BetaSignupStatus
from schemas.beta_signup import BetaSignupCreate, BetaSignupResponse
from services.email_service import EmailService
from shared.database import get_db
from shared.logger import logger

router = APIRouter(prefix="/beta", tags=["beta"])


@router.post(
    "/signup",
    response_model=BetaSignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Sign up for beta program",
    description="Register for the Stoflow beta program waitlist. Public endpoint, no authentication required.",
)
async def create_beta_signup(
    signup_data: BetaSignupCreate,
    db: Session = Depends(get_db),
) -> BetaSignupResponse:
    """
    Create a new beta signup.

    Args:
        signup_data: Email and profile information
        db: Database session

    Returns:
        Created beta signup

    Raises:
        HTTPException 409: If email already registered
        HTTPException 500: If database error occurs
    """
    try:
        # Check if email already exists (case-insensitive)
        existing_signup = db.query(BetaSignup).filter(
            func.lower(BetaSignup.email) == func.lower(signup_data.email)
        ).first()

        if existing_signup:
            logger.warning(f"Beta signup attempt with existing email: {signup_data.email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cette adresse email est déjà inscrite à la beta."
            )

        # Create new beta signup
        new_signup = BetaSignup(
            email=signup_data.email.lower(),
            name=signup_data.name,
            vendor_type=signup_data.vendor_type,
            monthly_volume=signup_data.monthly_volume,
            status=BetaSignupStatus.PENDING
        )

        db.add(new_signup)
        db.commit()
        db.refresh(new_signup)

        logger.info(f"Beta signup created: {new_signup.id} ({new_signup.email})")

        # Send confirmation email (don't fail signup if email fails)
        try:
            await EmailService.send_beta_confirmation_email(
                to_email=new_signup.email,
                to_name=new_signup.name,
                vendor_type=new_signup.vendor_type,
                monthly_volume=new_signup.monthly_volume
            )
            logger.info(f"Beta confirmation email sent to {new_signup.email}")
        except Exception as email_error:
            logger.error(f"Failed to send beta confirmation email: {email_error}")

        return BetaSignupResponse.model_validate(new_signup)

    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        logger.warning(f"Duplicate email signup attempt: {signup_data.email}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cette adresse email est déjà inscrite à la beta."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating beta signup: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur est survenue lors de l'inscription."
        )
