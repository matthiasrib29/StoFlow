"""
Vinted API Constants - Extracted from reverse engineering

Ces constantes sont utilisées pour construire les PluginTask
qui seront exécutées par le plugin navigateur.

Architecture Stoflow:
- Le backend crée des PluginTask avec http_method + path
- Le plugin exécute les requêtes avec les cookies/tokens du navigateur
- Le backend reçoit les réponses brutes

Author: Claude
Date: 2025-12-12
Source: pythonApiWOO reverse engineering
"""

# =============================================================================
# BASE URLS
# =============================================================================

VINTED_BASE_URL = "https://www.vinted.fr"


# =============================================================================
# PRODUCT ENDPOINTS
# =============================================================================

class VintedProductAPI:
    """URLs pour les opérations produits"""

    # Liste des produits d'un shop (pagination)
    @staticmethod
    def get_shop_items(shop_id: int, page: int = 1, per_page: int = 96) -> str:
        """GET - Récupère les produits d'un shop"""
        return f"{VINTED_BASE_URL}/api/v2/wardrobe/{shop_id}/items?page={page}&per_page={per_page}&order=relevance"

    # Création de produit
    CREATE = f"{VINTED_BASE_URL}/api/v2/item_upload/items"

    # Mise à jour de produit
    @staticmethod
    def update(item_id: int) -> str:
        """PUT - Met à jour un produit"""
        return f"{VINTED_BASE_URL}/api/v2/item_upload/items/{item_id}"

    # Suppression de produit
    @staticmethod
    def delete(item_id: int) -> str:
        """POST - Supprime un produit"""
        return f"{VINTED_BASE_URL}/api/v2/items/{item_id}/delete"

    # Statut d'un produit
    @staticmethod
    def get_status(item_id: int) -> str:
        """GET - Récupère le statut d'un produit"""
        return f"{VINTED_BASE_URL}/api/v2/items/{item_id}/status"


# =============================================================================
# DRAFT ENDPOINTS
# =============================================================================

class VintedDraftAPI:
    """URLs pour les brouillons"""

    # Création de brouillon
    CREATE = f"{VINTED_BASE_URL}/api/v2/item_upload/drafts"

    # Suppression de brouillon
    @staticmethod
    def delete(draft_id: int) -> str:
        """DELETE - Supprime un brouillon"""
        return f"{VINTED_BASE_URL}/api/v2/item_upload/drafts/{draft_id}"


# =============================================================================
# IMAGE ENDPOINTS
# =============================================================================

class VintedImageAPI:
    """URLs pour les images"""

    # Upload d'image (multipart/form-data)
    UPLOAD = f"{VINTED_BASE_URL}/api/v2/photos"


# =============================================================================
# ORDER ENDPOINTS
# =============================================================================

class VintedOrderAPI:
    """URLs pour les commandes"""

    # Liste des commandes
    @staticmethod
    def get_orders(
        order_type: str = "sold",
        status: str = "completed",
        page: int = 1,
        per_page: int = 20
    ) -> str:
        """GET - Récupère les commandes"""
        return f"{VINTED_BASE_URL}/api/v2/my_orders?type={order_type}&status={status}&page={page}&per_page={per_page}"

    # Détails d'une transaction
    @staticmethod
    def get_transaction(transaction_id: int) -> str:
        """GET - Détails d'une transaction"""
        return f"{VINTED_BASE_URL}/api/v2/transactions/{transaction_id}"

    # URL du bordereau d'expédition
    @staticmethod
    def get_shipment_label(shipment_id: int) -> str:
        """GET - URL du bordereau PDF"""
        return f"{VINTED_BASE_URL}/api/v2/shipments/{shipment_id}/label_url"

    # Factures/transactions par mois (wallet invoices)
    @staticmethod
    def get_wallet_invoices(year: int, month: int, page: int = 1) -> str:
        """
        GET - Récupère les factures/transactions d'un mois spécifique.

        Retourne les ventes, achats, transferts, remboursements du mois.
        Utile pour synchro par mois au lieu de tout l'historique.

        Args:
            year: Année (ex: 2025)
            month: Mois (1-12)
            page: Page de pagination

        Returns:
            URL de l'endpoint wallet/invoices
        """
        return f"{VINTED_BASE_URL}/api/v2/wallet/invoices/{year}/{month}?page={page}"


# =============================================================================
# CONVERSATION / INBOX ENDPOINTS
# =============================================================================

class VintedConversationAPI:
    """URLs pour les conversations et la messagerie"""

    @staticmethod
    def get_inbox(page: int = 1, per_page: int = 20) -> str:
        """
        GET - Récupère la liste des conversations (inbox).

        Returns conversations with:
        - id, description (last message preview), unread, updated_at
        - opposite_user (id, login, photo)
        - item_photos (photos des articles concernés)

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
        GET - Récupère les détails d'une conversation avec messages.

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


# =============================================================================
# REFERER URLS (pour contexte plugin)
# =============================================================================

class VintedReferers:
    """URLs de référence pour les headers Referer"""

    @staticmethod
    def member(user_id: int) -> str:
        """Page profil membre"""
        return f"{VINTED_BASE_URL}/member/{user_id}"

    NEW_ITEM = f"{VINTED_BASE_URL}/items/new"

    @staticmethod
    def edit_item(item_id: int) -> str:
        """Page édition produit"""
        return f"{VINTED_BASE_URL}/items/{item_id}/edit"

    ORDERS_SOLD = f"{VINTED_BASE_URL}/my_orders/sold"

    # Inbox / Messages
    INBOX = f"{VINTED_BASE_URL}/inbox"

    @staticmethod
    def inbox_conversation(conversation_id: int) -> str:
        """Page conversation spécifique"""
        return f"{VINTED_BASE_URL}/inbox/{conversation_id}"


# =============================================================================
# CONDITION IDS (status_id)
# =============================================================================

class VintedCondition:
    """IDs des états/conditions Vinted"""
    NEW_WITH_TAGS = 6      # Neuf avec étiquette
    NEW_WITHOUT_TAGS = 1   # Neuf sans étiquette
    VERY_GOOD = 2          # Très bon état
    GOOD = 3               # Bon état
    SATISFACTORY = 4       # Satisfaisant


# =============================================================================
# PACKAGE SIZE IDS (package_size_id)
# =============================================================================

class VintedPackageSize:
    """IDs des tailles de colis"""
    SMALL = 1      # Petit colis (< 1kg)
    MEDIUM = 2     # Moyen colis (1-2kg)
    LARGE = 3      # Grand colis (2-5kg)
    EXTRA_LARGE = 5  # Très grand colis (> 5kg)


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
    Construit le payload pour créer un produit Vinted.

    Args:
        title: Titre du produit (max 100 chars, inclure [SKU])
        description: Description (max 2000 chars)
        price: Prix en EUR (format xx.90 recommandé)
        brand_id: ID Vinted de la marque (None si non mappée)
        brand_name: Nom de la marque (utilisé si brand_id=None)
        size_id: ID Vinted de la taille
        catalog_id: ID Vinted de la catégorie
        status_id: ID de l'état (VintedCondition)
        color_ids: Liste des IDs couleurs
        photo_ids: Liste des IDs photos uploadées
        measurement_width: Largeur en cm (optionnel)
        measurement_length: Longueur en cm (optionnel)
        is_unisex: True si produit unisexe (lunettes)
        package_size_id: Taille du colis (VintedPackageSize)
        temp_uuid: UUID temporaire (auto-généré si None)
        upload_session_id: ID session upload (auto-généré si None)

    Returns:
        dict: Payload prêt pour POST /api/v2/item_upload/items
    """
    import uuid

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
    Construit le payload pour mettre à jour un produit Vinted.

    Args:
        vinted_id: ID Vinted du produit existant
        ... (mêmes args que build_create_payload)

    Returns:
        dict: Payload prêt pour PUT /api/v2/item_upload/items/{vinted_id}
    """
    import uuid

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
            "manufacturer_labelling": "Article complet avec étiquetage, conseils d'entretien et certifications pour une utilisation en toute sécurité."
        },
        "push_up": False,
        "parcel": None,
        "upload_session_id": str(uuid.uuid4())
    }


def build_image_upload_form(image_data: bytes, filename: str) -> dict:
    """
    Construit les données pour upload d'image multipart.

    Args:
        image_data: Contenu binaire de l'image
        filename: Nom du fichier

    Returns:
        dict: Données pour multipart/form-data
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
