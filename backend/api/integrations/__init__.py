"""
Integrations API Routes

Routes pour les intégrations avec plateformes externes (Vinted, eBay, Etsy).

Business Rules (2025-12-06):
- Cookies fournis par le plugin browser
- Stockage sécurisé des cookies (encrypted)
- Test connexion avant import/publish

Author: Claude
Date: 2025-12-17
"""

from fastapi import APIRouter

from .ebay import router as ebay_router
from .etsy import router as etsy_router
from .status import router as status_router
from .vinted import router as vinted_router

router = APIRouter(prefix="/integrations", tags=["Integrations"])

# Include sub-routers
router.include_router(status_router)
router.include_router(vinted_router)
router.include_router(ebay_router)
router.include_router(etsy_router)

__all__ = ["router"]
