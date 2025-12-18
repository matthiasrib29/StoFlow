"""
Plugin Schemas

Pydantic schemas for plugin API requests and responses.

Author: Claude
Date: 2025-12-17
"""

from datetime import datetime

from pydantic import BaseModel, Field


# ===== SYNC SCHEMAS =====


class PlatformCookies(BaseModel):
    """Cookies d'une plateforme."""

    platform: str = Field(..., description="Nom de la plateforme (vinted, ebay, etsy)")
    cookies: dict[str, str] = Field(..., description="Dictionnaire des cookies")
    user_agent: str | None = Field(None, description="User agent du browser")


class PluginSyncRequest(BaseModel):
    """Requête de synchronisation depuis le plugin."""

    platforms: list[PlatformCookies] = Field(
        ..., description="Liste des plateformes avec leurs cookies"
    )
    plugin_version: str = Field(..., description="Version du plugin")
    browser: str = Field(..., description="Browser (chrome, firefox)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "platforms": [
                    {
                        "platform": "vinted",
                        "cookies": {"v_sid": "abc123...", "anon_id": "xyz789..."},
                        "user_agent": "Mozilla/5.0...",
                    }
                ],
                "plugin_version": "1.0.0",
                "browser": "chrome",
            }
        }
    }


class PlatformStatus(BaseModel):
    """Status de connexion d'une plateforme."""

    platform: str
    connected: bool
    user: dict | None = None
    error: str | None = None
    last_sync: datetime | None = None


class PluginSyncResponse(BaseModel):
    """Réponse de synchronisation."""

    success: bool
    platforms_synced: int
    platforms_status: list[PlatformStatus]
    message: str


# ===== TASK QUEUE SCHEMAS =====


class PluginTaskResponse(BaseModel):
    """
    Tache a executer par le plugin.

    Architecture simplifiée (2025-12-12):
    - Le backend orchestre step-by-step avec async/await
    - path contient l'URL complète (ex: https://www.vinted.fr/api/v2/items/123)
    - params contient les query parameters (ex: { "page": 1, "per_page": 20 })
    - payload contient le body pour POST/PUT

    Rate Limiting (2025-12-18):
    - execute_delay_ms indique au plugin d'attendre AVANT d'exécuter la tâche
    - Évite le flood des APIs externes (Vinted, eBay, etc.)
    """

    id: int
    platform: str = Field(..., description="Plateforme cible (vinted, ebay, etsy)")
    http_method: str | None = Field(
        None, description="Méthode HTTP (POST, PUT, DELETE, GET) - Optionnel pour tasks spéciales"
    )
    path: str | None = Field(
        None,
        description="URL complète (ex: https://www.vinted.fr/api/v2/items) - Optionnel pour tasks spéciales",
    )
    params: dict | None = Field(
        None, description="Query parameters (ex: {page: 1, per_page: 20})"
    )
    payload: dict = Field(
        ..., description="Body de la requête (POST/PUT) ou données additionnelles"
    )

    # Pour tâches spéciales non-HTTP
    task_type: str | None = Field(
        None, description="Type de tâche spéciale (get_vinted_user_info, etc.)"
    )

    # Rate limiting (2025-12-18)
    execute_delay_ms: int = Field(
        0,
        description="Délai en ms que le plugin doit attendre AVANT d'exécuter cette tâche. "
                    "CRITIQUE: Le plugin DOIT respecter ce délai pour éviter le ban Vinted."
    )

    created_at: datetime

    model_config = {"from_attributes": True}


class TaskResultRequest(BaseModel):
    """Resultat d'execution d'une tache."""

    success: bool
    result: dict | None = Field(None, description="Resultat si succes")
    error_message: str | None = Field(None, description="Message d'erreur si echec")
    error_details: dict | None = Field(None, description="Details de l'erreur")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "result": {
                    "vinted_id": 987654,
                    "url": "https://vinted.fr/items/987654",
                },
            }
        }
    }


class PendingTasksResponse(BaseModel):
    """
    Réponse du polling avec intervalle adaptatif.

    Le backend contrôle l'intervalle de polling selon l'activité:
    - Tâches présentes → polling rapide (5s)
    - Aucune tâche → backoff progressif (jusqu'à 60s)
    """

    tasks: list[PluginTaskResponse] = Field(default_factory=list)
    next_poll_interval_ms: int = Field(
        5000, description="Intervalle recommandé avant le prochain poll (en ms)"
    )
    has_pending_tasks: bool = Field(
        False, description="Indique si des tâches sont en attente"
    )
