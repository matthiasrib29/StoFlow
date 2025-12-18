"""
Vinted API Routes - Modular Structure

Architecture modulaire pour la gestion Vinted:
- connection.py: Connexion/déconnexion compte Vinted
- products.py: CRUD produits + stats
- publishing.py: Publication, préparation, descriptions
- orders.py: Commandes et étiquettes

Created: 2024-12-10
Refactored: 2025-12-17 (split into modules)
Author: Claude
"""

from fastapi import APIRouter

from .connection import router as connection_router
from .products import router as products_router
from .publishing import router as publishing_router
from .orders import router as orders_router

# Router principal qui agrège tous les sous-routers
router = APIRouter(prefix="/vinted", tags=["Vinted"])

router.include_router(connection_router)
router.include_router(products_router)
router.include_router(publishing_router)
router.include_router(orders_router)
