"""
Etsy Connection Routes

Endpoints for connection status.

Author: Claude
Date: 2025-12-17
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from models.public.platform_mapping import PlatformMapping
from models.public.user import User

from .schemas import EtsyConnectionStatusResponse

router = APIRouter()


@router.get("/connection/status", response_model=EtsyConnectionStatusResponse)
def get_etsy_connection_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recupere le status de la connexion Etsy de l'utilisateur.

    Returns:
        Status de connexion avec infos shop si connecte
    """
    mapping = (
        db.query(PlatformMapping)
        .filter(
            PlatformMapping.user_id == current_user.id,
            PlatformMapping.platform == "etsy",
        )
        .first()
    )

    if not mapping or not mapping.access_token:
        return EtsyConnectionStatusResponse(connected=False)

    return EtsyConnectionStatusResponse(
        connected=True,
        shop_id=mapping.shop_id,
        shop_name=mapping.shop_name,
        access_token_expires_at=(
            mapping.access_token_expires_at.isoformat()
            if mapping.access_token_expires_at
            else None
        ),
        refresh_token_expires_at=(
            mapping.refresh_token_expires_at.isoformat()
            if mapping.refresh_token_expires_at
            else None
        ),
    )
