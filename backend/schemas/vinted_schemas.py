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
    last_synced_at: Optional[datetime] = Field(None, description="Dernière sync")

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


class VintedProductDetailResponse(BaseModel):
    """Response schema détaillé pour un VintedProduct (GET /products/{vinted_id})."""

    vinted_id: int = Field(..., description="ID Vinted (PK)")
    product_id: Optional[int] = Field(None, description="ID du produit Stoflow lié")
    title: Optional[str] = Field(None, description="Titre du produit")
    description: Optional[str] = Field(None, description="Description")
    price: Optional[float] = Field(None, description="Prix de vente")
    total_price: Optional[float] = Field(None, description="Prix total (avec frais)")
    currency: Optional[str] = Field(None, description="Devise (EUR)")
    url: Optional[str] = Field(None, description="URL du listing Vinted")
    status: Optional[str] = Field(None, description="Statut")
    condition: Optional[str] = Field(None, description="État du produit")
    status_id: Optional[int] = Field(None, description="ID du statut")
    view_count: int = Field(0, description="Nombre de vues")
    favourite_count: int = Field(0, description="Nombre de favoris")
    brand: Optional[str] = Field(None, description="Nom de la marque")
    brand_id: Optional[int] = Field(None, description="ID de la marque")
    size: Optional[str] = Field(None, description="Taille")
    size_id: Optional[int] = Field(None, description="ID de la taille")
    color1: Optional[str] = Field(None, description="Couleur principale")
    catalog_id: Optional[int] = Field(None, description="ID du catalogue Vinted")
    measurement_width: Optional[int] = Field(None, description="Largeur (cm)")
    measurement_length: Optional[int] = Field(None, description="Longueur (cm)")
    manufacturer_labelling: Optional[str] = Field(None, description="Étiquette fabricant")
    image_url: Optional[str] = Field(None, description="URL de l'image principale")
    is_draft: Optional[bool] = Field(None, description="Est un brouillon")
    is_closed: Optional[bool] = Field(None, description="Est fermé")
    is_reserved: Optional[bool] = Field(None, description="Est réservé")
    is_hidden: Optional[bool] = Field(None, description="Est caché")
    seller_id: Optional[int] = Field(None, description="ID du vendeur")
    seller_login: Optional[str] = Field(None, description="Login du vendeur")
    service_fee: Optional[float] = Field(None, description="Frais de service Vinted")
    published_at: Optional[str] = Field(None, description="Date de publication (ISO)")
    created_at: Optional[str] = Field(None, description="Date de création (ISO)")
    updated_at: Optional[str] = Field(None, description="Date de modification (ISO)")


class VintedProductsListResponse(BaseModel):
    """Response schema pour liste de produits Vinted avec pagination offset/limit."""

    products: List[VintedProductDetailResponse] = Field(..., description="Liste des produits")
    total: int = Field(..., description="Nombre total de produits")
    limit: int = Field(..., description="Limite par page")
    offset: int = Field(..., description="Offset de pagination")


class VintedStatsResponse(BaseModel):
    """Response schema pour les statistiques Vinted."""

    activePublications: int = Field(..., description="Nombre de publications actives")
    totalViews: int = Field(..., description="Total de vues")
    totalFavourites: int = Field(..., description="Total de favoris")
    potentialRevenue: float = Field(..., description="Revenu potentiel (EUR)")
    totalProducts: int = Field(..., description="Nombre total de produits")


class VintedJobResponse(BaseModel):
    """Response schema pour opérations avec job (sync, update, etc.)."""

    job_id: int = Field(..., description="ID du job MarketplaceJob")
    status: str = Field(..., description="Statut du job (pending, running, completed, failed)")
    result: Optional[dict] = Field(None, description="Résultat de l'exécution si process_now=True")


class VintedDeleteResponse(BaseModel):
    """Response schema pour suppression de produit."""

    success: bool = Field(..., description="Succès de l'opération")
    vinted_id: int = Field(..., description="ID Vinted du produit supprimé")


class VintedLinkResponse(BaseModel):
    """Response schema pour liaison/création de Product depuis VintedProduct."""

    success: bool = Field(..., description="Succès de l'opération")
    vinted_id: int = Field(..., description="ID Vinted")
    product_id: int = Field(..., description="ID du Product Stoflow")
    created: bool = Field(..., description="True si Product créé, False si lié à existant")
    images_copied: Optional[int] = Field(None, description="Nombre d'images copiées (si créé)")
    product: Optional[dict] = Field(None, description="Détails du Product créé")


class VintedUnlinkResponse(BaseModel):
    """Response schema pour déliaison de Product."""

    success: bool = Field(..., description="Succès de l'opération")
    vinted_id: int = Field(..., description="ID Vinted")


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

    title: Optional[str] = Field(None, max_length=500, description="Nouveau titre")
    price: Optional[Decimal] = Field(None, description="Nouveau prix")
    description: Optional[str] = Field(None, max_length=5000, description="Nouvelle description")


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
    last_synced_at: Optional[datetime] = Field(None, description="Date de dernière synchronisation")

    model_config = ConfigDict(from_attributes=True)
