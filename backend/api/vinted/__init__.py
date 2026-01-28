"""
Vinted API Routes - Modular Structure

Architecture modulaire pour la gestion Vinted:
- connection.py: Connexion/déconnexion compte Vinted
- products.py: CRUD produits + stats
- publishing.py: Publication, préparation, descriptions (Temporal workflows)
- orders.py: Commandes (Temporal workflows)
- messages.py: Inbox/conversations/messages
- temporal.py: Temporal workflow sync (2026-01-22)

Created: 2024-12-10
Refactored: 2025-12-17 (split into modules)
Updated: 2026-01-27 (removed jobs module, replaced by Temporal workflows)
Author: Claude
"""

from fastapi import APIRouter

from .connection import router as connection_router
from .products import router as products_router
from .publishing import router as publishing_router
from .orders import router as orders_router
from .messages import router as messages_router
from .temporal import router as temporal_router

# Router principal qui agrège tous les sous-routers
router = APIRouter(prefix="/vinted", tags=["Vinted"])

router.include_router(connection_router)
router.include_router(products_router)
router.include_router(publishing_router)
router.include_router(orders_router)
router.include_router(messages_router)
router.include_router(temporal_router)
