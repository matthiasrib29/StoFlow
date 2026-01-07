"""
eBay Order Schemas

Pydantic schemas pour les commandes eBay (request/response).

Schemas:
- Request: SyncOrdersRequest, UpdateFulfillmentRequest, AddTrackingRequest
- Response: EbayOrderProductResponse, EbayOrderDetailResponse, SyncOrdersResponse,
            OrderListResponse, AddTrackingResponse

Created: 2026-01-07
Author: Claude
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, computed_field


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================


class SyncOrdersRequest(BaseModel):
    """
    Request pour synchroniser les commandes eBay.

    Attributes:
        hours: Nombre d'heures à remonter dans l'historique (0=toutes, 1-720=période spécifique)
        status_filter: Filtre optionnel par statut fulfillment
    """

    hours: int = Field(
        default=24,
        ge=0,  # Allow 0 for fetching ALL orders (no date filter)
        le=720,
        description="Nombre d'heures à remonter (0=toutes, 1-720=période spécifique)",
    )
    status_filter: Optional[str] = Field(
        default=None,
        description="Filtre par statut: NOT_STARTED, IN_PROGRESS, FULFILLED",
    )


class UpdateFulfillmentRequest(BaseModel):
    """
    Request pour mettre à jour le statut de fulfillment.

    Attributes:
        new_status: Nouveau statut (NOT_STARTED, IN_PROGRESS, FULFILLED)
    """

    new_status: str = Field(
        ...,
        pattern="^(NOT_STARTED|IN_PROGRESS|FULFILLED)$",
        description="Nouveau statut de fulfillment",
    )


class AddTrackingRequest(BaseModel):
    """
    Request pour ajouter un numéro de suivi.

    Attributes:
        tracking_number: Numéro de suivi (alphanumériques uniquement)
        carrier_code: Code transporteur (COLISSIMO, CHRONOPOST, UPS, etc.)
        shipped_date: Date d'expédition (optionnel, défaut: maintenant)
    """

    tracking_number: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Numéro de suivi (alphanumériques uniquement)",
    )
    carrier_code: str = Field(
        ..., min_length=1, max_length=100, description="Code transporteur"
    )
    shipped_date: Optional[datetime] = Field(
        default=None, description="Date d'expédition (défaut: maintenant)"
    )


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================


class EbayOrderProductResponse(BaseModel):
    """
    Response pour un produit de commande eBay (line item).

    Attributes:
        id: ID interne
        order_id: ID commande eBay
        line_item_id: ID line item eBay
        sku: SKU dérivé (ex: "12345-FR")
        sku_original: SKU original (ex: "12345")
        title: Titre du produit
        quantity: Quantité
        unit_price: Prix unitaire
        total_price: Prix total ligne
        currency: Devise
        legacy_item_id: ID item legacy eBay (pour linking)
    """

    id: int
    order_id: str
    line_item_id: Optional[str] = None
    sku: Optional[str] = None
    sku_original: Optional[str] = None
    title: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    currency: Optional[str] = None
    legacy_item_id: Optional[str] = None

    model_config = {"from_attributes": True}


class EbayOrderDetailResponse(BaseModel):
    """
    Response détaillée pour une commande eBay.

    Attributes:
        id: ID interne
        order_id: ID commande eBay (ex: "12-34567-89012")
        marketplace_id: Marketplace (EBAY_FR, EBAY_GB, etc.)
        buyer_username: Username acheteur
        buyer_email: Email acheteur
        shipping_name: Nom destinataire
        shipping_address: Adresse livraison
        shipping_city: Ville
        shipping_postal_code: Code postal
        shipping_country: Code pays
        total_price: Prix total
        currency: Devise
        shipping_cost: Frais de port
        order_fulfillment_status: Statut fulfillment
        order_payment_status: Statut paiement
        creation_date: Date création
        paid_date: Date paiement
        tracking_number: Numéro de suivi
        shipping_carrier: Transporteur
        created_at: Date création en DB
        updated_at: Date mise à jour en DB
        products: Liste des produits (line items)
    """

    id: int
    order_id: str
    marketplace_id: Optional[str] = None
    buyer_username: Optional[str] = None
    buyer_email: Optional[str] = None
    shipping_name: Optional[str] = None
    shipping_address: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_postal_code: Optional[str] = None
    shipping_country: Optional[str] = None
    total_price: Optional[float] = None
    currency: Optional[str] = None
    shipping_cost: Optional[float] = None
    order_fulfillment_status: Optional[str] = None
    order_payment_status: Optional[str] = None
    creation_date: Optional[datetime] = None
    paid_date: Optional[datetime] = None
    tracking_number: Optional[str] = None
    shipping_carrier: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Nested products (line items)
    products: List[EbayOrderProductResponse] = Field(default_factory=list)

    @computed_field
    @property
    def items_count(self) -> int:
        """Total number of line items in the order."""
        return len(self.products)

    model_config = {"from_attributes": True}


class SyncOrdersResponse(BaseModel):
    """
    Response pour l'opération de synchronisation.

    Attributes:
        created: Nombre de commandes créées
        updated: Nombre de commandes mises à jour
        skipped: Nombre de commandes ignorées
        errors: Nombre d'erreurs
        total_fetched: Total de commandes récupérées depuis eBay
        details: Détails par commande (order_id, action, error)
    """

    created: int = Field(..., ge=0, description="Nombre de commandes créées")
    updated: int = Field(..., ge=0, description="Nombre de commandes mises à jour")
    skipped: int = Field(..., ge=0, description="Nombre de commandes ignorées")
    errors: int = Field(..., ge=0, description="Nombre d'erreurs")
    total_fetched: int = Field(
        ..., ge=0, description="Total commandes récupérées depuis eBay"
    )
    details: List[dict] = Field(
        default_factory=list,
        description="Détails par commande (order_id, action, error)",
    )


class OrderListResponse(BaseModel):
    """
    Response paginée pour liste de commandes.

    Attributes:
        items: Liste des commandes
        total: Nombre total de commandes (tous les résultats)
        page: Page actuelle (1-indexed)
        page_size: Taille de page
        total_pages: Nombre total de pages
    """

    items: List[EbayOrderDetailResponse]
    total: int = Field(..., ge=0, description="Nombre total de commandes")
    page: int = Field(..., ge=1, description="Page actuelle")
    page_size: int = Field(..., ge=1, description="Taille de page")
    total_pages: int = Field(..., ge=0, description="Nombre total de pages")


class AddTrackingResponse(BaseModel):
    """
    Response après ajout de tracking.

    Attributes:
        success: Succès de l'opération
        fulfillment_id: ID fulfillment eBay
        order_id: ID commande eBay
        tracking_number: Numéro de suivi ajouté
    """

    success: bool
    fulfillment_id: str = Field(..., description="ID fulfillment eBay")
    order_id: str = Field(..., description="ID commande eBay")
    tracking_number: str = Field(..., description="Numéro de suivi ajouté")
