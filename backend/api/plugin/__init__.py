"""
Plugin Browser API Routes

Routes pour communication avec le plugin browser (Chrome/Firefox).

Business Rules (Updated: 2025-12-06):
- Le plugin envoie les cookies des plateformes (Vinted, eBay, Etsy)
- Authentification via JWT token Stoflow (Bearer)
- Les cookies restent UNIQUEMENT sur la machine de l'utilisateur (chrome.storage)
- Le backend NE STOCKE PAS les cookies (test uniquement)
- Test de connexion automatique lors de la sync
- Auto-refresh token si expiration < 24h

Author: Claude
Date: 2025-12-17
"""

from fastapi import APIRouter

from .sync import router as sync_router
from .tasks import router as tasks_router

router = APIRouter(prefix="/plugin", tags=["Plugin"])

# Include sub-routers
router.include_router(sync_router)
router.include_router(tasks_router)

__all__ = ["router"]
