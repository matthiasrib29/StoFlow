"""
Integrations API Routes

Routes pour les intégrations avec plateformes externes (Vinted, eBay, Etsy).

Business Rules (2025-12-06):
- Cookies fournis par le plugin browser
- Stockage sécurisé des cookies (encrypted)
- Test connexion avant import/publish

TEMPORARILY DISABLED (2025-12-24):
- Etsy: PlatformMapping model missing (not yet implemented)

Author: Claude
Date: 2025-12-17
Updated: 2026-01-03 - Re-enabled eBay
"""

from fastapi import APIRouter

# eBay router (re-enabled 2026-01-03)
from .ebay import router as ebay_router
# TEMPORARILY DISABLED - Etsy uses PlatformMapping model (not yet implemented)
# from .etsy import router as etsy_router
from .status import router as status_router
# Vinted router removed (2026-01-05) - Use /api/vinted/* endpoints instead

router = APIRouter(prefix="/integrations", tags=["Integrations"])

# Include sub-routers
router.include_router(status_router)
router.include_router(ebay_router)
# TEMPORARILY DISABLED - Etsy uses PlatformMapping model (not yet implemented)
# router.include_router(etsy_router)

__all__ = ["router"]
