"""
Etsy Connection Routes

Endpoints for connection status.

Author: Claude
Date: 2025-12-17
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from models.user.etsy_credentials import EtsyCredentials
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
    credentials = db.query(EtsyCredentials).first()

    if not credentials or not credentials.access_token:
        return EtsyConnectionStatusResponse(connected=False)

    return EtsyConnectionStatusResponse(
        connected=True,
        shop_id=credentials.shop_id,
        shop_name=credentials.shop_name,
        access_token_expires_at=(
            credentials.access_token_expires_at.isoformat()
            if credentials.access_token_expires_at
            else None
        ),
        refresh_token_expires_at=(
            credentials.refresh_token_expires_at.isoformat()
            if credentials.refresh_token_expires_at
            else None
        ),
    )
