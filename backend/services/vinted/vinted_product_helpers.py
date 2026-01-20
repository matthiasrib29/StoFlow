"""
Vinted Product Helpers - Fonctions utilitaires pour les produits Vinted

Helpers internes pour la gestion des produits Vinted:
- Upload d'images
- Sauvegarde de nouveaux produits
- Verification des conditions de suppression

Author: Claude
Date: 2025-12-17
"""

from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from models.user.product import Product
from models.user.vinted_product import VintedProduct
from services.plugin_websocket_helper import PluginWebSocketHelper  # WebSocket architecture (2026-01-12)
from services.vinted.vinted_product_converter import VintedProductConverter
from shared.vinted import VintedImageAPI
from shared.logging import get_logger
from shared.config import settings

logger = get_logger(__name__)


async def upload_product_images(
    db: Session,
    product: Product,
    user_id: int,
    job_id: int | None = None
) -> list[int]:
    """
    Upload les images d'un produit sur Vinted.

    Args:
        db: Session SQLAlchemy
        product: Instance Product
        user_id: ID utilisateur (requis pour WebSocket) (2026-01-12)
        job_id: ID du job parent (optionnel, pour tracking)

    Returns:
        Liste des IDs photos uploadees
    """
    photo_ids = []

    # Recuperer les URLs images depuis product
    image_urls = []
    if hasattr(product, 'images') and product.images:
        if isinstance(product.images, list):
            for img in product.images:
                if isinstance(img, dict) and img.get('url'):
                    image_urls.append(img['url'])
                elif hasattr(img, 'url'):
                    image_urls.append(img.url)
        elif isinstance(product.images, str):
            image_urls = [
                url.strip() for url in product.images.split(',') if url.strip()
            ]

    if not image_urls:
        logger.warning(f"  Aucune image trouvee pour produit #{product.id}")
        return []

    for idx, image_url in enumerate(image_urls, 1):
        try:
            logger.debug(f"    Upload image {idx}/{len(image_urls)}...")

            payload = VintedProductConverter.build_image_upload_payload(
                image_url=image_url
            )

            # WebSocket architecture (2026-01-12)
            result = await PluginWebSocketHelper.call_plugin_http(
                db=db,
                user_id=user_id,
                http_method="POST",
                path=VintedImageAPI.UPLOAD,
                payload={"body": payload, "image_url": image_url},
                timeout=settings.plugin_timeout_upload,
                description=f"Upload image {idx}"
            )

            photo_id = result.get('id')
            if photo_id:
                photo_ids.append(photo_id)
                logger.debug(f"    Image {idx} -> id={photo_id}")

        except Exception as e:
            logger.warning(f"    Erreur image {idx}: {e}")

    return photo_ids


def save_new_vinted_product(
    db: Session,
    product_id: int,
    response_data: dict,
    prix_vinted: float,
    image_ids: list[int],
    title: str
):
    """
    Sauvegarde un nouveau VintedProduct apres creation.

    Args:
        db: Session SQLAlchemy
        product_id: ID du produit local
        response_data: Reponse de l'API Vinted
        prix_vinted: Prix calcule
        image_ids: IDs des images uploadees
        title: Titre genere
    """
    item_data = response_data.get('item', response_data)

    vinted_product = VintedProduct(
        product_id=product_id,
        vinted_id=item_data.get('id'),
        status='published',
        date=date.today(),
        view_count=0,
        favourite_count=0,
        price=Decimal(str(prix_vinted)),
        title=item_data.get('title', title),
        url=item_data.get('url')
    )

    if image_ids:
        vinted_product.set_image_ids(image_ids)

    db.add(vinted_product)


def should_delete_product(
    vinted_product: VintedProduct,
    threshold_days: int = 90,
    no_favs_days: int = 30
) -> bool:
    """
    Verifie si un produit doit etre supprime.

    Args:
        vinted_product: Instance VintedProduct
        threshold_days: Seuil general en jours
        no_favs_days: Seuil si 0 favoris

    Returns:
        True si eligible a la suppression
    """
    if not vinted_product.date:
        return False

    days_active = (date.today() - vinted_product.date).days

    # Si 0 favoris, seuil reduit
    if vinted_product.favourite_count == 0:
        return days_active >= no_favs_days

    return days_active >= threshold_days
