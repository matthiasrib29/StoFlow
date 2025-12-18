"""
Etsy API Routes

Endpoints pour l'integration Etsy API v3.

Fonctionnalites:
- Connection status
- Publication produits
- Gestion listings
- Gestion orders
- Shop management
- Polling status

Author: Claude
Date: 2025-12-17
"""

from fastapi import APIRouter

from .connection import router as connection_router
from .products import router as products_router
from .shop import router as shop_router
from .taxonomy import router as taxonomy_router

router = APIRouter(prefix="/etsy", tags=["Etsy"])

# Include sub-routers
router.include_router(connection_router)
router.include_router(products_router)
router.include_router(shop_router)
router.include_router(taxonomy_router)

__all__ = ["router"]
