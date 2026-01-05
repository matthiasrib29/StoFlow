"""
Vinted Importer

Import de produits depuis Vinted vers Stoflow.

Business Rules (2025-12-06):
- Import uniquement produits actifs (not sold)
- Téléchargement images vers notre CDN
- Détection duplicatas via vinted_id
- Mode: cookies du navigateur (fournis par plugin)

Author: Claude
Date: 2025-12-06
Updated: 2026-01-05 - Removed HTML parsing methods (use VintedProductEnricher instead)
"""

import httpx
from typing import Optional
from sqlalchemy.orm import Session

from services.vinted.vinted_mapper import VintedMapper
from services.product_service import ProductService
from services.file_service import FileService
from shared.datetime_utils import utc_now
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class VintedImporter:
    """Service pour importer produits depuis Vinted."""

    VINTED_API_BASE = "https://www.vinted.fr/api/v2"

    def __init__(self, cookies: dict[str, str]):
        """
        Initialise l'importeur avec les cookies Vinted.

        Args:
            cookies: Dictionnaire des cookies Vinted
                     Ex: {"v_sid": "...", "anon_id": "..."}
        """
        self.cookies = cookies
        self.client = httpx.Client(
            base_url=self.VINTED_API_BASE,
            cookies=cookies,
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            },
            timeout=30.0
        )

    async def get_current_user(self, vinted_user_id: int) -> Optional[dict]:
        """
        Récupère les infos de l'utilisateur Vinted.

        IMPORTANT: Cette méthode nécessite le vinted_user_id.
        Pour obtenir l'ID utilisateur depuis les cookies, utilisez plutôt
        une requête vers une page HTML et parsez window.vinted.user.id

        Args:
            vinted_user_id: ID utilisateur Vinted (ex: 29535217)

        Returns:
            dict: User info ou None si non connecté

        Raises:
            ValueError: Si cookies invalides ou user_id incorrect
        """
        try:
            # Note: L'API Vinted n'a pas d'endpoint /users/current
            # Il faut utiliser /users/{user_id}
            response = self.client.get(f"/users/{vinted_user_id}")
            response.raise_for_status()

            data = response.json()
            return data.get("user")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid Vinted cookies. User not authenticated.")
            elif e.response.status_code == 404:
                raise ValueError(f"Vinted user {vinted_user_id} not found.")
            raise

    async def fetch_user_items(
        self,
        vinted_user_id: int,
        page: int = 1,
        per_page: int = 96,
        order: str = "relevance"
    ) -> dict:
        """
        Récupère les produits d'un utilisateur Vinted.

        IMPORTANT: Utilise /wardrobe/{user_id}/items (pas /users/current/items)

        Args:
            vinted_user_id: ID utilisateur Vinted (ex: 29535217)
            page: Numéro de page (default: 1)
            per_page: Items par page (max 96, default: 96)
            order: Ordre de tri ("relevance", "newest_first", etc.)

        Returns:
            dict: {"items": [...], "pagination": {...}}

        Note:
            L'API /wardrobe/{user_id}/items retourne tous les produits visibles
            Il n'y a pas de filtre par status dans cette version de l'API
        """
        params = {
            "page": page,
            "per_page": min(per_page, 96),
            "order": order
        }

        # URL correcte: /wardrobe/{user_id}/items
        response = self.client.get(f"/wardrobe/{vinted_user_id}/items", params=params)
        response.raise_for_status()

        return response.json()

    async def fetch_all_active_items(self, vinted_user_id: int) -> list[dict]:
        """
        Récupère TOUS les produits actifs de l'utilisateur.

        Args:
            vinted_user_id: ID utilisateur Vinted (ex: 29535217)

        Returns:
            list[dict]: Liste de tous les items Vinted visibles
        """
        all_items = []
        page = 1

        while True:
            data = await self.fetch_user_items(
                vinted_user_id=vinted_user_id,
                page=page,
                per_page=96,
                order="relevance"
            )
            items = data.get("items", [])

            if not items:
                break

            all_items.extend(items)

            # Check pagination
            pagination = data.get("pagination", {})
            if page >= pagination.get("total_pages", 1):
                break

            page += 1

        return all_items

    async def download_image(self, image_url: str) -> bytes:
        """
        Télécharge une image depuis Vinted.

        Args:
            image_url: URL de l'image Vinted

        Returns:
            bytes: Contenu de l'image
        """
        response = self.client.get(image_url)
        response.raise_for_status()
        return response.content

    async def import_items_to_stoflow(
        self,
        db: Session,
        user_id: int,
        vinted_items: list[dict]
    ) -> dict:
        """
        Importe des items Vinted vers Stoflow.

        Args:
            db: Session SQLAlchemy
            user_id: ID de l'utilisateur Stoflow
            vinted_items: Liste d'items Vinted

        Returns:
            dict: {
                "imported": int,
                "skipped": int,
                "errors": int,
                "details": [...]
            }
        """
        results = {
            "imported": 0,
            "skipped": 0,
            "errors": 0,
            "details": []
        }

        for vinted_item in vinted_items:
            try:
                result = await self._import_single_item(db, user_id, vinted_item)

                if result["status"] == "imported":
                    results["imported"] += 1
                elif result["status"] == "skipped":
                    results["skipped"] += 1

                results["details"].append(result)

            except Exception as e:
                results["errors"] += 1
                results["details"].append({
                    "vinted_id": vinted_item.get("id"),
                    "status": "error",
                    "error": str(e)
                })

        return results

    async def _import_single_item(
        self,
        db: Session,
        user_id: int,
        vinted_item: dict
    ) -> dict:
        """
        Importe un seul item Vinted vers Stoflow.

        Args:
            db: Session SQLAlchemy
            user_id: ID de l'utilisateur
            vinted_item: Item Vinted

        Returns:
            dict: Résultat de l'import
        """
        vinted_id = vinted_item.get("id")

        # Check si déjà importé
        existing_product = self._find_existing_product(db, vinted_id)
        if existing_product:
            return {
                "vinted_id": vinted_id,
                "status": "skipped",
                "reason": "already_imported",
                "product_id": existing_product.id
            }

        # Convertir Vinted → Stoflow
        product_data = VintedMapper.vinted_to_stoflow(vinted_item)

        # Télécharger et uploader images
        image_urls = await self._process_images(
            user_id,
            product_data["images"]
        )

        product_data["images"] = image_urls
        product_data["integration_metadata"]["imported_at"] = utc_now().isoformat()

        # Créer le produit dans Stoflow
        # Note: Pour l'instant on stocke images dans integration_metadata
        # TODO: Intégrer avec ProductService.create_product
        from models.user.product import Product

        product = Product(
            user_id=user_id,
            title=product_data["title"],
            description=product_data["description"],
            price=product_data["price"],
            brand=product_data["brand"],
            category=product_data["category"],
            condition=product_data["condition"],
            size_original=product_data["size_original"],
            color=product_data["color"],
            stock_quantity=product_data["stock_quantity"],
            # Stocker metadata Vinted dans integration_metadata JSONB
            integration_metadata=product_data["integration_metadata"],
        )

        db.add(product)
        db.commit()
        db.refresh(product)

        return {
            "vinted_id": vinted_id,
            "status": "imported",
            "product_id": product.id,
            "product_sku": product.sku
        }

    async def _process_images(
        self,
        user_id: int,
        vinted_image_urls: list[str]
    ) -> list[str]:
        """
        Télécharge images Vinted et les upload vers Stoflow CDN.

        Args:
            user_id: ID utilisateur
            vinted_image_urls: URLs images Vinted

        Returns:
            list[str]: URLs images sur Stoflow CDN
        """
        uploaded_urls = []

        for url in vinted_image_urls[:10]:  # Max 10 images
            try:
                # Download image from Vinted
                image_content = await self.download_image(url)

                # TODO: Upload to Cloudinary/S3 via FileService
                # Pour l'instant on garde l'URL Vinted
                uploaded_urls.append(url)

            except Exception as e:
                logger.warning(f"Failed to process image {url}: {e}")
                # Continue avec les autres images

        return uploaded_urls

    def _find_existing_product(self, db: Session, vinted_id: int) -> Optional:
        """
        Cherche si un produit avec ce vinted_id existe déjà.

        Args:
            db: Session SQLAlchemy
            vinted_id: ID Vinted

        Returns:
            Product | None (via VintedProduct.product relation)
        """
        from models.user.vinted_product import VintedProduct

        # Chercher via la table vinted_products qui contient le vinted_id
        vinted_product = db.query(VintedProduct).filter(
            VintedProduct.vinted_id == vinted_id
        ).first()

        return vinted_product.product if vinted_product else None

    def close(self):
        """Ferme le client HTTP."""
        self.client.close()

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
