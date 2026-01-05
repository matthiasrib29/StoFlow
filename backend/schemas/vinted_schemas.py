"""
Vinted Schemas

Schémas Pydantic pour les endpoints API Vinted.

Created: 2024-12-10
Author: Claude
"""

from datetime import date as date_type, datetime
from typing import List, Optional
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


# ===== Connection Schemas =====

class VintedConnectionStatusResponse(BaseModel):
    """Response pour le statut de connexion Vinted."""

    is_connected: bool = Field(..., description="Connexion active")
    vinted_user_id: Optional[int] = Field(None, description="ID Vinted")
    login: Optional[str] = Field(None, description="Username")
    last_sync: Optional[datetime] = Field(None, description="Dernière sync")
    disconnected_at: Optional[datetime] = Field(None, description="Date de déconnexion si déconnecté")

    model_config = ConfigDict(from_attributes=True)


# ===== VintedProduct Schemas =====

class VintedProductResponse(BaseModel):
    """Response schema pour un VintedProduct."""

    vinted_id: int = Field(..., description="ID Vinted (PK)")
    product_id: int = Field(..., description="ID du produit Stoflow")
    status: str = Field(..., description="Statut: pending, published, error, deleted")
    date: Optional[date_type] = Field(None, description="Date de publication")
    title: Optional[str] = Field(None, description="Titre utilisé sur Vinted")
    price: Optional[Decimal] = Field(None, description="Prix de vente sur Vinted")
    url: Optional[str] = Field(None, description="URL du listing Vinted")
    view_count: int = Field(0, description="Nombre de vues")
    favourite_count: int = Field(0, description="Nombre de favoris")
    conversations: int = Field(0, description="Nombre de conversations")
    image_ids: Optional[str] = Field(None, description="IDs images uploadées (CSV)")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: datetime = Field(..., description="Date de dernière modification")

    model_config = ConfigDict(from_attributes=True)


class VintedProductListResponse(BaseModel):
    """Response schema pour une liste de VintedProducts."""

    items: List[VintedProductResponse]
    total: int = Field(..., description="Nombre total de résultats")
    page: int = Field(..., description="Page actuelle (0-indexed)")
    page_size: int = Field(..., description="Nombre d'items par page")
    total_pages: int = Field(..., description="Nombre total de pages")


# ===== Publication Requests =====

class VintedPublishRequest(BaseModel):
    """Request pour publier un produit sur Vinted."""

    product_id: int = Field(..., description="ID du produit Stoflow à publier")


class VintedBatchPublishRequest(BaseModel):
    """Request pour publier plusieurs produits en batch."""

    product_ids: List[int] = Field(..., min_length=1, max_length=100, description="IDs des produits à publier (max 100)")


class VintedPublishResponse(BaseModel):
    """Response après demande de publication."""

    product_id: int = Field(..., description="ID du produit")
    status: str = Field(..., description="Statut de la demande")
    message: str = Field(..., description="Message de confirmation/erreur")
    vinted_product_id: Optional[int] = Field(None, description="ID du VintedProduct créé")


class VintedBatchPublishResponse(BaseModel):
    """Response après publication batch."""

    total: int = Field(..., description="Nombre total de produits")
    success: int = Field(..., description="Nombre de succès")
    failed: int = Field(..., description="Nombre d'échecs")
    results: List[VintedPublishResponse] = Field(..., description="Résultats détaillés")


# ===== Update Requests =====

class VintedUpdateRequest(BaseModel):
    """Request pour mettre à jour un produit Vinted."""

    title: Optional[str] = Field(None, description="Nouveau titre")
    price: Optional[Decimal] = Field(None, description="Nouveau prix")
    description: Optional[str] = Field(None, description="Nouvelle description")


class VintedAnalyticsUpdate(BaseModel):
    """Request pour mettre à jour les analytics d'un produit."""

    view_count: Optional[int] = Field(None, ge=0, description="Nombre de vues")
    favourite_count: Optional[int] = Field(None, ge=0, description="Nombre de favoris")
    conversations: Optional[int] = Field(None, ge=0, description="Nombre de conversations")


# ===== Bordereau Schemas =====

class VintedBordereauDownloadRequest(BaseModel):
    """Request pour télécharger un bordereau."""

    label_url: str = Field(..., description="URL du bordereau Vinted")
    transaction_id: int = Field(..., description="ID de la transaction Vinted")


# Alias pour compatibilité avec api/vinted.py
VintedBordereauRequest = VintedBordereauDownloadRequest


class VintedBordereauBatchRequest(BaseModel):
    """Request pour télécharger plusieurs bordereaux."""

    bordereaux: List[VintedBordereauDownloadRequest] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Liste des bordereaux à télécharger (max 100)"
    )


class VintedBordereauResponse(BaseModel):
    """Response après téléchargement bordereau."""

    transaction_id: int = Field(..., description="ID de la transaction")
    status: str = Field(..., description="Statut: success ou error")
    file_path: Optional[str] = Field(None, description="Chemin du fichier téléchargé")
    error: Optional[str] = Field(None, description="Message d'erreur si échec")


class VintedBordereauBatchResponse(BaseModel):
    """Response après téléchargement batch."""

    total: int = Field(..., description="Nombre total de bordereaux")
    success: int = Field(..., description="Nombre de succès")
    failed: int = Field(..., description="Nombre d'échecs")
    files: List[str] = Field(..., description="Chemins des fichiers téléchargés")
    errors: List[dict] = Field(..., description="Erreurs rencontrées")


class VintedBordereauListItem(BaseModel):
    """Item dans la liste des bordereaux."""

    path: str = Field(..., description="Chemin du fichier")
    transaction_id: Optional[int] = Field(None, description="ID de la transaction")
    filename: str = Field(..., description="Nom du fichier")
    size_bytes: int = Field(..., description="Taille du fichier en octets")
    created_at: datetime = Field(..., description="Date de création")


class VintedBordereauListResponse(BaseModel):
    """Response pour liste des bordereaux."""

    items: List[VintedBordereauListItem]
    total: int = Field(..., description="Nombre total de bordereaux")


# ===== Error Log Schemas =====

class VintedErrorLogResponse(BaseModel):
    """Response schema pour un VintedErrorLog."""

    id: int = Field(..., description="ID du log d'erreur")
    product_id: int = Field(..., description="ID du produit")
    operation: str = Field(..., description="Type d'opération: publish, update, delete")
    error_type: str = Field(..., description="Type d'erreur: mapping_error, api_error, image_error, validation_error")
    error_message: str = Field(..., description="Message d'erreur")
    error_details: Optional[str] = Field(None, description="Détails supplémentaires")
    created_at: datetime = Field(..., description="Date de création")

    model_config = ConfigDict(from_attributes=True)


class VintedErrorLogListResponse(BaseModel):
    """Response pour liste des erreurs."""

    items: List[VintedErrorLogResponse]
    total: int = Field(..., description="Nombre total d'erreurs")
    page: int = Field(..., description="Page actuelle")
    page_size: int = Field(..., description="Taille de page")
    total_pages: int = Field(..., description="Nombre total de pages")


class VintedErrorSummaryResponse(BaseModel):
    """Response pour résumé des erreurs."""

    total_errors: int = Field(..., description="Nombre total d'erreurs")
    by_type: dict = Field(..., description="Comptage par type d'erreur")
    by_operation: dict = Field(..., description="Comptage par opération")
    last_24h: int = Field(..., description="Erreurs dernières 24h")
    last_7d: int = Field(..., description="Erreurs derniers 7 jours")


# ===== Analytics Schemas =====

class VintedAnalyticsSummaryResponse(BaseModel):
    """Response pour résumé analytics."""

    total_views: int = Field(..., description="Total de vues")
    total_favourites: int = Field(..., description="Total de favoris")
    total_conversations: int = Field(..., description="Total de conversations")
    avg_views: float = Field(..., description="Moyenne de vues par produit")
    published_count: int = Field(..., description="Nombre de produits publiés")


# ===== Preparation Schemas =====

class VintedProductPreparationResponse(BaseModel):
    """Response pour préparation d'un produit (génération titre/description/prix)."""

    product_id: int = Field(..., description="ID du produit")
    title: str = Field(..., description="Titre généré")
    description: str = Field(..., description="Description générée")
    price: Decimal = Field(..., description="Prix calculé")
    mapped_attributes: dict = Field(..., description="Attributs mappés vers IDs Vinted")
    validation: dict = Field(..., description="Résultats de validation")
    ready_to_publish: bool = Field(..., description="Prêt à publier ou non")


# ===== Simplified Connection Schemas (NEW) =====

class VintedUserSyncRequest(BaseModel):
    """Request simplifié pour synchroniser l'utilisateur Vinted (userId + login uniquement)."""

    vinted_user_id: int = Field(..., description="ID utilisateur Vinted", gt=0)
    login: str = Field(..., description="Login/username Vinted", min_length=1, max_length=255)


class VintedSimpleConnectionResponse(BaseModel):
    """Response simplifiée avec uniquement les informations de base."""

    is_connected: bool = Field(..., description="Indique si l'utilisateur est connecté à Vinted")
    vinted_user_id: Optional[int] = Field(None, description="ID utilisateur Vinted")
    login: Optional[str] = Field(None, description="Login/username Vinted")
    last_sync: Optional[datetime] = Field(None, description="Date de dernière synchronisation")

    model_config = ConfigDict(from_attributes=True)
