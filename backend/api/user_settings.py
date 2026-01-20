"""
User Settings API

Endpoints for managing user preferences (text generator settings).
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from models.public.user import User
from schemas.user_settings import TextGeneratorSettings, TextGeneratorSettingsUpdate
from shared.database import get_db
from shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/users/me/settings", tags=["User Settings"])


@router.get("/text-generator", response_model=TextGeneratorSettings)
async def get_text_generator_settings(
    current_user: User = Depends(get_current_user),
) -> TextGeneratorSettings:
    """
    Get user's text generator preferences.

    Returns the user's default title format and description style preferences.
    Values are 1-3 or None (no preference).

    Returns:
        TextGeneratorSettings: Current text generator preferences
    """
    logger.debug(f"Getting text generator settings for user_id={current_user.id}")

    return TextGeneratorSettings(
        default_title_format=current_user.default_title_format,
        default_description_style=current_user.default_description_style,
    )


@router.patch("/text-generator", response_model=TextGeneratorSettings)
async def update_text_generator_settings(
    settings: TextGeneratorSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TextGeneratorSettings:
    """
    Update user's text generator preferences.

    Only provided fields will be updated. To clear a preference, explicitly set it to null.

    Args:
        settings: Fields to update (title_format, description_style)

    Returns:
        TextGeneratorSettings: Updated text generator preferences
    """
    # Update only provided fields
    update_data = settings.model_dump(exclude_unset=True)

    if "default_title_format" in update_data:
        current_user.default_title_format = update_data["default_title_format"]
    if "default_description_style" in update_data:
        current_user.default_description_style = update_data["default_description_style"]

    db.commit()
    db.refresh(current_user)

    logger.info(
        f"Updated text generator settings for user_id={current_user.id}: "
        f"title_format={current_user.default_title_format}, "
        f"description_style={current_user.default_description_style}"
    )

    return TextGeneratorSettings(
        default_title_format=current_user.default_title_format,
        default_description_style=current_user.default_description_style,
    )
