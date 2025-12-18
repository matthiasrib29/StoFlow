"""
Schemas Package

Ce package contient tous les schemas Pydantic pour la validation des requêtes/réponses.
"""

from schemas.auth_schemas import (
    LoginRequest,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    TokenResponse,
)
from schemas.product_schemas import (
    ProductCreate,
    ProductImageCreate,
    ProductImageResponse,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)

__all__ = [
    "LoginRequest",
    "TokenResponse",
    "RefreshRequest",
    "RefreshResponse",
    "RegisterRequest",
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "ProductListResponse",
    "ProductImageCreate",
    "ProductImageResponse",
]
