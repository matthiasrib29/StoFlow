"""
Vinted Publisher

Publication de produits Stoflow vers Vinted.

Business Rules (2025-12-06):
- Upload images vers Vinted avant création listing
- Récupération brand_id, size_id depuis API Vinted
- CSRF token requis pour toutes les mutations
- Mode: cookies du navigateur (fournis par plugin)

Author: Claude
Date: 2025-12-06
"""

import httpx
from typing import Optional
from io import BytesIO

from services.vinted.vinted_mapper import VintedMapper
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class VintedPublisher:
    """Service pour publier produits sur Vinted."""

    VINTED_API_BASE = "https://www.vinted.fr/api/v2"

    def __init__(self, cookies: dict[str, str]):
        """
        Initialise le publisher avec les cookies Vinted.

        Args:
            cookies: Dictionnaire des cookies Vinted
        """
        self.cookies = cookies
        self.client = httpx.Client(
            base_url=self.VINTED_API_BASE,
            cookies=cookies,
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            },
            timeout=60.0  # Upload images peut être long
        )
        self.csrf_token: Optional[str] = None

    async def get_csrf_token(self) -> str:
        """
        Récupère le CSRF token depuis les cookies Vinted.

        Returns:
            str: CSRF token

        Raises:
            ValueError: Si token non trouvé
        """
        # Le CSRF token est généralement dans le cookie 'anon_id' ou '_csrf_token'
        csrf_token = self.cookies.get("_csrf_token") or self.cookies.get("anon_id")

        if not csrf_token:
            raise ValueError("CSRF token not found in cookies")

        self.csrf_token = csrf_token
        return csrf_token

    async def upload_photo(self, image_bytes: bytes) -> dict:
        """
        Upload une photo vers Vinted et retourne le photo_id.

        Args:
            image_bytes: Contenu de l'image

        Returns:
            dict: {"photo_id": int, "upload_url": str}

        Raises:
            httpx.HTTPError: Si upload échoue
        """
        # Step 1: Demander upload URL à Vinted
        csrf_token = await self.get_csrf_token()

        response = self.client.post(
            "/photos",
            headers={"X-CSRF-Token": csrf_token}
        )
        response.raise_for_status()

        data = response.json()
        upload_url = data.get("upload_url")
        photo_id = data.get("photo_id")

        # Step 2: Upload l'image vers l'URL fournie
        files = {"file": ("image.jpg", BytesIO(image_bytes), "image/jpeg")}

        upload_response = httpx.put(upload_url, files=files, timeout=60.0)
        upload_response.raise_for_status()

        return {
            "photo_id": photo_id,
            "upload_url": upload_url
        }

    async def upload_photos(self, image_urls: list[str]) -> list[int]:
        """
        Upload plusieurs photos vers Vinted.

        Args:
            image_urls: Liste d'URLs images Stoflow CDN

        Returns:
            list[int]: Liste des photo_ids Vinted

        Raises:
            Exception: Si upload échoue pour une image
        """
        photo_ids = []

        for url in image_urls[:20]:  # Max 20 images Vinted
            try:
                # Download image from Stoflow CDN
                image_response = httpx.get(url, timeout=30.0)
                image_response.raise_for_status()

                # Upload to Vinted
                result = await self.upload_photo(image_response.content)
                photo_ids.append(result["photo_id"])

            except Exception as e:
                logger.warning(f"Failed to upload image {url}: {e}")
                # Continue avec les autres images

        if not photo_ids:
            raise ValueError("No images uploaded successfully")

        return photo_ids

    async def search_brand(self, brand_name: str) -> Optional[int]:
        """
        Cherche un brand_id Vinted par nom.

        Args:
            brand_name: Nom de la marque (ex: "Levi's")

        Returns:
            int | None: Brand ID ou None si non trouvé
        """
        try:
            response = self.client.get(
                "/brands",
                params={"search_text": brand_name}
            )
            response.raise_for_status()

            brands = response.json().get("brands", [])

            # Chercher correspondance exacte
            for brand in brands:
                if brand.get("title", "").lower() == brand_name.lower():
                    return brand.get("id")

            # Si pas de correspondance exacte, prendre le premier
            if brands:
                return brands[0].get("id")

        except Exception as e:
            logger.warning(f"Failed to search brand {brand_name}: {e}")

        return None

    async def search_size(self, size_title: str, catalog_id: int) -> Optional[int]:
        """
        Cherche un size_id Vinted par nom et catégorie.

        Args:
            size_title: Taille (ex: "M", "W32L34")
            catalog_id: ID catalogue Vinted

        Returns:
            int | None: Size ID ou None si non trouvé
        """
        try:
            response = self.client.get(
                f"/catalog/{catalog_id}/sizes",
                params={"search_text": size_title}
            )
            response.raise_for_status()

            sizes = response.json().get("sizes", [])

            # Chercher correspondance exacte
            for size in sizes:
                if size.get("title", "").lower() == size_title.lower():
                    return size.get("id")

        except Exception as e:
            logger.warning(f"Failed to search size {size_title}: {e}")

        return None

    async def search_color(self, color_name: str) -> Optional[int]:
        """
        Cherche un color_id Vinted par nom.

        Args:
            color_name: Nom couleur (ex: "Blue", "Red")

        Returns:
            int | None: Color ID ou None
        """
        try:
            response = self.client.get("/colors")
            response.raise_for_status()

            colors = response.json().get("colors", [])

            for color in colors:
                if color.get("title", "").lower() == color_name.lower():
                    return color.get("id")

        except Exception as e:
            logger.warning(f"Failed to search color {color_name}: {e}")

        return None

    async def create_listing(self, stoflow_product: dict) -> dict:
        """
        Crée un listing Vinted depuis un produit Stoflow.

        Args:
            stoflow_product: Données produit Stoflow
            {
                "title": str,
                "description": str,
                "price": float,
                "brand": str,
                "category": str,
                "condition": str,
                "size_original": str,
                "color": str,
                "images": [str, ...]  # URLs Stoflow CDN
            }

        Returns:
            dict: {
                "item_id": int,
                "url": str,
                "status": "active"
            }

        Raises:
            ValueError: Si données invalides
            httpx.HTTPError: Si API Vinted échoue
        """
        # 1. Convertir Stoflow → Vinted format
        vinted_payload = VintedMapper.stoflow_to_vinted(stoflow_product)

        # 2. Upload images
        photo_ids = await self.upload_photos(stoflow_product.get("images", []))
        vinted_payload["photo_ids"] = photo_ids

        # 3. Résoudre brand_id (optionnel)
        if stoflow_product.get("brand"):
            brand_id = await self.search_brand(stoflow_product["brand"])
            if brand_id:
                vinted_payload["brand_id"] = brand_id

        # 4. Résoudre size_id (optionnel)
        if stoflow_product.get("size_original"):
            size_id = await self.search_size(
                stoflow_product["size_original"],
                vinted_payload["catalog_id"]
            )
            if size_id:
                vinted_payload["size_id"] = size_id

        # 5. Résoudre color_id (optionnel)
        if stoflow_product.get("color"):
            color_id = await self.search_color(stoflow_product["color"])
            if color_id:
                vinted_payload["color_ids"] = [color_id]

        # 6. Créer le listing
        csrf_token = await self.get_csrf_token()

        response = self.client.post(
            "/items",
            headers={
                "X-CSRF-Token": csrf_token,
                "Content-Type": "application/json"
            },
            json=vinted_payload
        )
        response.raise_for_status()

        result = response.json()
        item = result.get("item", {})

        return {
            "item_id": item.get("id"),
            "url": item.get("url"),
            "status": "active"
        }

    async def update_listing(
        self,
        item_id: int,
        stoflow_product: dict
    ) -> dict:
        """
        Met à jour un listing Vinted existant.

        Args:
            item_id: ID du listing Vinted
            stoflow_product: Nouvelles données produit

        Returns:
            dict: Listing mis à jour
        """
        # Convertir données
        vinted_payload = VintedMapper.stoflow_to_vinted(stoflow_product)

        csrf_token = await self.get_csrf_token()

        response = self.client.put(
            f"/items/{item_id}",
            headers={
                "X-CSRF-Token": csrf_token,
                "Content-Type": "application/json"
            },
            json=vinted_payload
        )
        response.raise_for_status()

        return response.json().get("item", {})

    async def delete_listing(self, item_id: int) -> bool:
        """
        Supprime (cache) un listing Vinted.

        Args:
            item_id: ID du listing Vinted

        Returns:
            bool: True si succès
        """
        csrf_token = await self.get_csrf_token()

        response = self.client.delete(
            f"/items/{item_id}",
            headers={"X-CSRF-Token": csrf_token}
        )

        return response.status_code in [200, 204]

    def close(self):
        """Ferme le client HTTP."""
        self.client.close()

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
