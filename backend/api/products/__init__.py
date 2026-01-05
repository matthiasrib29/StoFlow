"""
Product Routes Package

Combined router for all product-related endpoints.

Structure:
- crud.py: Basic CRUD operations (create, read, update, delete, status)
- images.py: Image management (upload, delete, reorder)
- ai.py: AI-powered features (description generation, image analysis)

Author: Claude
Date: 2025-12-09
Refactored: 2026-01-05 - Split into multiple modules
"""

from fastapi import APIRouter

from api.products.crud import router as crud_router
from api.products.images import router as images_router
from api.products.ai import router as ai_router

# Main router that combines all sub-routers
router = APIRouter(prefix="/products", tags=["Products"])

# Include all sub-routers
router.include_router(crud_router)
router.include_router(images_router)
router.include_router(ai_router)

__all__ = ["router"]
