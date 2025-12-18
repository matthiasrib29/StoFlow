"""
Integrations Schemas

Pydantic schemas for integrations API requests and responses.

Author: Claude
Date: 2025-12-17
"""

from pydantic import BaseModel


class VintedCookiesRequest(BaseModel):
    """Schema pour fournir les cookies Vinted."""

    cookies: dict[str, str]  # Ex: {"v_sid": "...", "anon_id": "..."}


class VintedConnectionResponse(BaseModel):
    """Résultat du test de connexion Vinted."""

    connected: bool
    user: dict | None = None
    error: str | None = None


class VintedImportRequest(BaseModel):
    """Requête d'import Vinted."""

    cookies: dict[str, str]
    vinted_ids: list[int] | None = None  # Si None → import ALL


class VintedImportResponse(BaseModel):
    """Résultat de l'import Vinted."""

    total_vinted: int
    imported: int
    skipped: int
    errors: int
    details: list[dict] = []


class VintedPublishRequest(BaseModel):
    """Requête de publication sur Vinted."""

    cookies: dict[str, str]
    product_id: int  # ID produit Stoflow


class VintedPublishResponse(BaseModel):
    """Résultat de la publication Vinted."""

    success: bool
    item_id: int | None = None
    url: str | None = None
    error: str | None = None


class IntegrationStatusItem(BaseModel):
    """Statut d'une intégration."""

    platform: str
    name: str
    is_connected: bool
    last_sync: str | None = None
    total_publications: int = 0
    active_publications: int = 0


class IntegrationsStatusResponse(BaseModel):
    """Statut global de toutes les intégrations."""

    integrations: list[IntegrationStatusItem]
