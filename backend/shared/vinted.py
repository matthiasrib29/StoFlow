"""
Vinted Configuration and Constants

Headers, endpoints, and payload builders for Vinted API integration.

This module consolidates all Vinted-related configuration:
- HTTP headers for API requests
- API endpoint URLs
- Enums for condition/package size
- Payload builders for create/update operations

Architecture Stoflow:
- Le backend cree des PluginTask avec http_method + path
- Le plugin execute les requetes avec les cookies/tokens du navigateur
- Le backend recoit les reponses brutes

Author: Claude
Date: 2025-12-11
Updated: 2026-01-20 - Merged vinted_config.py and vinted_constants.py
"""

import uuid

# =============================================================================
# HTTP HEADERS (from vinted_config.py)
# =============================================================================

VINTED_HEADERS_BASE = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fr",
    "Content-Type": "application/json",
    "Priority": "u=3",
}

VINTED_HEADERS_CONDITIONAL = {
    # Upload / Edit articles
    "upload_item": {
        "X-Upload-Form": "true",
        "X-Enable-Multiple-Size-Groups": "true",
    },
    "edit_item": {
        "X-Upload-Form": "true",
        "X-Enable-Multiple-Size-Groups": "true",
    },
    "edit_draft": {
        "X-Upload-Form": "true",
        "X-Enable-Multiple-Size-Groups": "true",
    },
    "delete_item": {
        "X-Upload-Form": "true",
    },

    # Transactions / Orders
    "transactions": {
        "X-Money-Object": "true",
    },
    "orders": {
        "X-Money-Object": "true",
    },

    # Auth
    "auth": {
        "X-Browser-Compat": "2",
    },

    # Brand
    "brand": {
        "Mda-Brand": "true",
    },
}

VINTED_URL_PATTERNS = {
    "upload_item": ["/item_upload", "/items", "/photos"],
    "edit_item": ["/items/", "/edit"],
    "edit_draft": ["/draft"],
    "delete_item": ["/items/", "/delete"],
    "transactions": ["/transactions"],
    "orders": ["/orders", "/help_center/recent"],
    "auth": ["/web/api/auth", "/auth/refresh"],
    "brand": ["/brand"],
}

# =============================================================================
# BASE URL
# =============================================================================

VINTED_BASE_URL = "https://www.vinted.fr"


# =============================================================================
# API ENDPOINTS
# =============================================================================

class VintedProductAPI:
    """URLs pour les operations produits"""

    # Liste des produits d'un shop (pagination)
    @staticmethod
    def get_shop_items(shop_id: int, page: int = 1, per_page: int = 96) -> str:
        """GET - Recupere les produits d'un shop"""
        return f"{VINTED_BASE_URL}/api/v2/wardrobe/{shop_id}/items?page={page}&per_page={per_page}&order=relevance"

    # Creation de produit
    CREATE = f"{VINTED_BASE_URL}/api/v2/item_upload/items"

    # Mise a jour de produit
    @staticmethod
    def update(item_id: int) -> str:
        """PUT - Met a jour un produit"""
        return f"{VINTED_BASE_URL}/api/v2/item_upload/items/{item_id}"

    # Suppression de produit
    @staticmethod
    def delete(item_id: int) -> str:
        """POST - Supprime un produit"""
        return f"{VINTED_BASE_URL}/api/v2/items/{item_id}/delete"

    # Statut d'un produit
    @staticmethod
    def get_status(item_id: int) -> str:
        """GET - Recupere le statut d'un produit"""
        return f"{VINTED_BASE_URL}/api/v2/items/{item_id}/status"


class VintedDraftAPI:
    """URLs pour les brouillons"""

    # Creation de brouillon
    CREATE = f"{VINTED_BASE_URL}/api/v2/item_upload/drafts"

    # Suppression de brouillon
    @staticmethod
    def delete(draft_id: int) -> str:
        """DELETE - Supprime un brouillon"""
        return f"{VINTED_BASE_URL}/api/v2/item_upload/drafts/{draft_id}"


class VintedImageAPI:
    """URLs pour les images"""

    # Upload d'image (multipart/form-data)
    UPLOAD = f"{VINTED_BASE_URL}/api/v2/photos"


class VintedOrderAPI:
    """URLs pour les commandes"""

    # Liste des commandes
    @staticmethod
    def get_orders(
        order_type: str = "sold",
        status: str = "all",
        page: int = 1,
        per_page: int = 100
    ) -> str:
        """
        GET - Recupere les commandes (ventes ou achats).

        Args:
            order_type: Type de commande ("sold" = ventes, "purchased" = achats)
            status: Filtre de statut (all = tout)
            page: Numero de page
            per_page: Nombre de resultats par page (max 100)

        Returns:
            URL de l'API /my_orders
        """
        return f"{VINTED_BASE_URL}/api/v2/my_orders?type={order_type}&status={status}&per_page={per_page}&page={page}"

    # Details d'une transaction
    @staticmethod
    def get_transaction(transaction_id: int) -> str:
        """GET - Details d'une transaction"""
        return f"{VINTED_BASE_URL}/api/v2/transactions/{transaction_id}"

    # URL du bordereau d'expedition
    @staticmethod
    def get_shipment_label(shipment_id: int) -> str:
        """GET - URL du bordereau PDF"""
        return f"{VINTED_BASE_URL}/api/v2/shipments/{shipment_id}/label_url"

    # Factures/transactions par mois (wallet invoices)
    @staticmethod
    def get_wallet_invoices(year: int, month: int, page: int = 1) -> str:
        """
        GET - Recupere les factures/transactions d'un mois specifique.

        Retourne les ventes, achats, transferts, remboursements du mois.
        Utile pour synchro par mois au lieu de tout l'historique.

        Args:
            year: Annee (ex: 2025)
            month: Mois (1-12)
            page: Page de pagination

        Returns:
            URL de l'endpoint wallet/invoices
        """
        return f"{VINTED_BASE_URL}/api/v2/wallet/invoices/{year}/{month}?page={page}"


class VintedConversationAPI:
    """URLs pour les conversations et la messagerie"""

    @staticmethod
    def get_inbox(page: int = 1, per_page: int = 20) -> str:
        """
        GET - Recupere la liste des conversations (inbox).

        Returns conversations with:
        - id, description (last message preview), unread, updated_at
        - opposite_user (id, login, photo)
        - item_photos (photos des articles concernes)

        Args:
            page: Page number (1-indexed)
            per_page: Items per page (default 20)

        Returns:
            URL de l'endpoint inbox
        """
        return f"{VINTED_BASE_URL}/api/v2/inbox?page={page}&per_page={per_page}"

    @staticmethod
    def get_conversation(conversation_id: int) -> str:
        """
        GET - Recupere les details d'une conversation avec messages.

        Returns conversation with:
        - messages[] (entity_type: message, offer_request_message, status_message, action_message)
        - transaction (id, status, buyer_id, seller_id, item details)
        - opposite_user (full profile info)

        Args:
            conversation_id: ID de la conversation Vinted

        Returns:
            URL de l'endpoint conversation
        """
        return f"{VINTED_BASE_URL}/api/v2/conversations/{conversation_id}"


class VintedReferers:
    """URLs de reference pour les headers Referer"""

    @staticmethod
    def member(user_id: int) -> str:
        """Page profil membre"""
        return f"{VINTED_BASE_URL}/member/{user_id}"

    NEW_ITEM = f"{VINTED_BASE_URL}/items/new"

    @staticmethod
    def edit_item(item_id: int) -> str:
        """Page edition produit"""
        return f"{VINTED_BASE_URL}/items/{item_id}/edit"

    ORDERS_SOLD = f"{VINTED_BASE_URL}/my_orders/sold"

    # Inbox / Messages
    INBOX = f"{VINTED_BASE_URL}/inbox"

    @staticmethod
    def inbox_conversation(conversation_id: int) -> str:
        """Page conversation specifique"""
        return f"{VINTED_BASE_URL}/inbox/{conversation_id}"


# =============================================================================
# ENUMS
# =============================================================================

class VintedCondition:
    """IDs des etats/conditions Vinted"""
    NEW_WITH_TAGS = 6      # Neuf avec etiquette
    NEW_WITHOUT_TAGS = 1   # Neuf sans etiquette
    VERY_GOOD = 2          # Tres bon etat
    GOOD = 3               # Bon etat
    SATISFACTORY = 4       # Satisfaisant


class VintedPackageSize:
    """IDs des tailles de colis"""
    SMALL = 1      # Petit colis (< 1kg)
    MEDIUM = 2     # Moyen colis (1-2kg)
    LARGE = 3      # Grand colis (2-5kg)
    EXTRA_LARGE = 5  # Tres grand colis (> 5kg)


# =============================================================================
# PAYLOAD BUILDERS
# =============================================================================

def build_create_payload(
    title: str,
    description: str,
    price: float,
    brand_id: int | None,
    brand_name: str,
    size_id: int | None,
    catalog_id: int,
    status_id: int,
    color_ids: list[int],
    photo_ids: list[int],
    measurement_width: int | None = None,
    measurement_length: int | None = None,
    is_unisex: bool = False,
    package_size_id: int = VintedPackageSize.SMALL,
    temp_uuid: str | None = None,
    upload_session_id: str | None = None
) -> dict:
    """
    Construit le payload pour creer un produit Vinted.

    Args:
        title: Titre du produit (max 100 chars, inclure [SKU])
        description: Description (max 2000 chars)
        price: Prix en EUR (format xx.90 recommande)
        brand_id: ID Vinted de la marque (None si non mappee)
        brand_name: Nom de la marque (utilise si brand_id=None)
        size_id: ID Vinted de la taille
        catalog_id: ID Vinted de la categorie
        status_id: ID de l'etat (VintedCondition)
        color_ids: Liste des IDs couleurs
        photo_ids: Liste des IDs photos uploadees
        measurement_width: Largeur en cm (optionnel)
        measurement_length: Longueur en cm (optionnel)
        is_unisex: True si produit unisexe (lunettes)
        package_size_id: Taille du colis (VintedPackageSize)
        temp_uuid: UUID temporaire (auto-genere si None)
        upload_session_id: ID session upload (auto-genere si None)

    Returns:
        dict: Payload pret pour POST /api/v2/item_upload/items
    """
    if temp_uuid is None:
        temp_uuid = str(uuid.uuid4())
    if upload_session_id is None:
        upload_session_id = str(uuid.uuid4())

    return {
        "item": {
            "id": None,
            "currency": "EUR",
            "temp_uuid": temp_uuid,
            "title": title,
            "description": description,
            "brand_id": brand_id,
            "brand": brand_name if not brand_id else "",
            "size_id": size_id,
            "catalog_id": catalog_id,
            "isbn": None,
            "is_unisex": is_unisex,
            "status_id": status_id,
            "video_game_rating_id": None,
            "price": price,
            "package_size_id": package_size_id,
            "shipment_prices": {
                "domestic": None,
                "international": None
            },
            "color_ids": color_ids,
            "assigned_photos": [
                {"id": photo_id, "orientation": 0}
                for photo_id in photo_ids
            ],
            "measurement_length": measurement_length,
            "measurement_width": measurement_width,
            "item_attributes": [],
            "manufacturer": None,
            "manufacturer_labelling": None
        },
        "feedback_id": None,
        "push_up": False,
        "parcel": None,
        "upload_session_id": upload_session_id
    }


def build_update_payload(
    vinted_id: int,
    title: str,
    description: str,
    price: float,
    brand_id: int | None,
    brand_name: str,
    size_id: int | None,
    catalog_id: int,
    status_id: int,
    color_ids: list[int],
    photo_ids: list[int],
    measurement_width: int | None = None,
    measurement_length: int | None = None,
    is_unisex: bool = False,
    package_size_id: int = VintedPackageSize.SMALL
) -> dict:
    """
    Construit le payload pour mettre a jour un produit Vinted.

    Args:
        vinted_id: ID Vinted du produit existant
        ... (memes args que build_create_payload)

    Returns:
        dict: Payload pret pour PUT /api/v2/item_upload/items/{vinted_id}
    """
    return {
        "feedback_id": None,
        "item": {
            "id": vinted_id,
            "currency": "EUR",
            "temp_uuid": str(uuid.uuid4()),
            "title": title,
            "description": description,
            "brand_id": brand_id,
            "brand": brand_name,  # Toujours inclure pour update
            "size_id": size_id,
            "catalog_id": catalog_id,
            "isbn": None,
            "is_unisex": is_unisex,
            "status_id": status_id,
            "video_game_rating_id": None,
            "price": price,
            "package_size_id": package_size_id,
            "shipment_prices": {
                "domestic": None,
                "international": None
            },
            "color_ids": color_ids,
            "assigned_photos": [
                {"id": photo_id, "orientation": 0}
                for photo_id in photo_ids
            ],
            "measurement_length": measurement_length,
            "measurement_width": measurement_width,
            "item_attributes": [],
            "manufacturer": None,
            "manufacturer_labelling": "Article complet avec etiquetage, conseils d'entretien et certifications pour une utilisation en toute securite."
        },
        "push_up": False,
        "parcel": None,
        "upload_session_id": str(uuid.uuid4())
    }


def build_image_upload_form(image_data: bytes, filename: str) -> dict:
    """
    Construit les donnees pour upload d'image multipart.

    Args:
        image_data: Contenu binaire de l'image
        filename: Nom du fichier

    Returns:
        dict: Donnees pour multipart/form-data
            {
                'fields': {'photo[type]': 'item', 'photo[temp_uuid]': ''},
                'file_field': 'photo[file]',
                'filename': str,
                'content': bytes,
                'content_type': 'image/jpeg'
            }
    """
    return {
        'fields': {
            'photo[type]': 'item',
            'photo[temp_uuid]': ''
        },
        'file_field': 'photo[file]',
        'filename': filename,
        'content': image_data,
        'content_type': 'image/jpeg'
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Headers
    "VINTED_HEADERS_BASE",
    "VINTED_HEADERS_CONDITIONAL",
    "VINTED_URL_PATTERNS",
    # Base URL
    "VINTED_BASE_URL",
    # API Classes
    "VintedProductAPI",
    "VintedDraftAPI",
    "VintedImageAPI",
    "VintedOrderAPI",
    "VintedConversationAPI",
    "VintedReferers",
    # Enums
    "VintedCondition",
    "VintedPackageSize",
    # Payload builders
    "build_create_payload",
    "build_update_payload",
    "build_image_upload_form",
]
