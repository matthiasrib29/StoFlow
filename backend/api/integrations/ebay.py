"""
eBay Integration Routes

Routes for eBay platform integration (test, import).

Business Rules:
- eBay requires OAuth2 (not cookies)
- V1: Stub implementations

Author: Claude
Date: 2025-12-17
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from models.public.user import User
from services.ebay.ebay_adapter import EbayAdapter
from shared.database import get_db

router = APIRouter()


@router.post("/ebay/test-connection", status_code=status.HTTP_200_OK)
async def test_ebay_connection(
    access_token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Teste la connexion à eBay avec OAuth2 token.

    Business Rules:
    - eBay requiert OAuth2 (pas de cookies)
    - V1: Stub qui retourne "not implemented"

    Args:
        access_token: Token OAuth2 eBay
        current_user: Utilisateur authentifié
        db: Session DB

    Returns:
        dict: Résultat du test
    """
    async with EbayAdapter(access_token) as adapter:
        result = await adapter.test_connection()
        return result


@router.post("/ebay/import", status_code=status.HTTP_200_OK)
async def import_ebay_products(
    access_token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Importe des produits depuis eBay.

    Business Rules (Updated: 2025-12-08):
    - V1: Stub non implémenté
    - Requiert configuration OAuth2 eBay Developer Program
    - Isolation: produits importés dans schema user_X de l'utilisateur authentifié

    Args:
        access_token: Token OAuth2 eBay
        db: Session DB
        current_user: Utilisateur authentifié (depuis JWT token)

    Returns:
        dict: Résultat de l'import
    """
    async with EbayAdapter(access_token) as adapter:
        user_id = current_user.id
        result = await adapter.import_all_products(db, user_id)
        return result
