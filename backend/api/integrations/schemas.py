"""
Integrations Schemas

Pydantic schemas for integrations API requests and responses.

Author: Claude
Date: 2025-12-17
Updated: 2026-01-05 - Removed Vinted schemas (use /api/vinted/* endpoints)
"""

from pydantic import BaseModel


# Vinted schemas removed (2026-01-05)
# Use /api/vinted/* endpoints with schemas defined in api/vinted/*.py


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
