"""
Vinted Adapter

Adaptateur principal pour toutes les opérations Vinted.
Orchestre l'import, publication, et synchronisation.

Business Rules (2025-12-06):
- Point d'entrée unique pour toutes opérations Vinted
- Gestion connexion via cookies (fournis par plugin browser)
- Retry automatique sur erreurs temporaires

Author: Claude
Date: 2025-12-06
"""

from typing import Optional
from sqlalchemy.orm import Session

from services.vinted.vinted_importer import VintedImporter
from services.vinted.vinted_publisher import VintedPublisher
from services.vinted.vinted_mapper import VintedMapper


class VintedAdapter:
    """
    Adaptateur principal pour opérations Vinted.

    Usage:
        cookies = {"v_sid": "...", "anon_id": "..."}

        async with VintedAdapter(cookies) as adapter:
            # Test connexion
            user = await adapter.test_connection()

            # Import produits
            result = await adapter.import_all_products(db, user_id)

            # Publier produit
            listing = await adapter.publish_product(stoflow_product)
    """

    def __init__(self, cookies: dict[str, str]):
        """
        Initialise l'adapter avec les cookies Vinted.

        Args:
            cookies: Dictionnaire des cookies Vinted
                     Requis: "v_sid" (session ID) au minimum
        """
        self.cookies = cookies
        self.importer = VintedImporter(cookies)
        self.publisher = VintedPublisher(cookies)

    async def test_connection(self) -> dict:
        """
        Teste la connexion Vinted avec les cookies fournis.

        Returns:
            dict: {
                "connected": bool,
                "user": {...} | None,
                "error": str | None
            }
        """
        try:
            user = await self.importer.get_current_user()

            if user:
                return {
                    "connected": True,
                    "user": {
                        "id": user.get("id"),
                        "login": user.get("login"),
                        "email": user.get("email")
                    },
                    "error": None
                }
            else:
                return {
                    "connected": False,
                    "user": None,
                    "error": "No user found"
                }

        except Exception as e:
            return {
                "connected": False,
                "user": None,
                "error": str(e)
            }

    async def import_all_products(
        self,
        db: Session,
        user_id: int
    ) -> dict:
        """
        Importe TOUS les produits actifs Vinted vers Stoflow.

        Args:
            db: Session SQLAlchemy
            user_id: ID de l'utilisateur Stoflow

        Returns:
            dict: {
                "total_vinted": int,
                "imported": int,
                "skipped": int,
                "errors": int,
                "details": [...]
            }
        """
        # Fetch tous les items actifs depuis Vinted
        vinted_items = await self.importer.fetch_all_active_items()

        # Import vers Stoflow
        result = await self.importer.import_items_to_stoflow(
            db,
            user_id,
            vinted_items
        )

        result["total_vinted"] = len(vinted_items)

        return result

    async def import_specific_products(
        self,
        db: Session,
        user_id: int,
        vinted_ids: list[int]
    ) -> dict:
        """
        Importe des produits Vinted spécifiques.

        Args:
            db: Session SQLAlchemy
            user_id: ID de l'utilisateur
            vinted_ids: Liste d'IDs Vinted à importer

        Returns:
            dict: Résultat de l'import
        """
        # TODO: Implémenter fetch items spécifiques
        # Pour l'instant: fetch all et filter
        all_items = await self.importer.fetch_all_active_items()

        specific_items = [
            item for item in all_items
            if item.get("id") in vinted_ids
        ]

        return await self.importer.import_items_to_stoflow(
            db,
            user_id,
            specific_items
        )

    async def publish_product(self, stoflow_product: dict) -> dict:
        """
        Publie un produit Stoflow sur Vinted.

        Args:
            stoflow_product: Données produit Stoflow

        Returns:
            dict: {
                "success": bool,
                "item_id": int | None,
                "url": str | None,
                "error": str | None
            }
        """
        try:
            # Vérifier que la catégorie est supportée
            category = stoflow_product.get("category", "")
            if not VintedMapper.is_category_supported(category):
                return {
                    "success": False,
                    "item_id": None,
                    "url": None,
                    "error": f"Category '{category}' not supported for Vinted. "
                            f"Supported: {VintedMapper.get_supported_categories()}"
                }

            # Créer le listing
            result = await self.publisher.create_listing(stoflow_product)

            return {
                "success": True,
                "item_id": result["item_id"],
                "url": result["url"],
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "item_id": None,
                "url": None,
                "error": str(e)
            }

    async def update_product(
        self,
        vinted_item_id: int,
        stoflow_product: dict
    ) -> dict:
        """
        Met à jour un produit Vinted existant.

        Args:
            vinted_item_id: ID du listing Vinted
            stoflow_product: Nouvelles données

        Returns:
            dict: {
                "success": bool,
                "error": str | None
            }
        """
        try:
            await self.publisher.update_listing(vinted_item_id, stoflow_product)

            return {
                "success": True,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def delete_product(self, vinted_item_id: int) -> dict:
        """
        Supprime (cache) un produit Vinted.

        Args:
            vinted_item_id: ID du listing Vinted

        Returns:
            dict: {
                "success": bool,
                "error": str | None
            }
        """
        try:
            success = await self.publisher.delete_listing(vinted_item_id)

            return {
                "success": success,
                "error": None if success else "Failed to delete"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_user_stats(self) -> dict:
        """
        Récupère les stats de l'utilisateur Vinted.

        Returns:
            dict: {
                "total_items": int,
                "visible_items": int,
                "sold_items": int
            }
        """
        try:
            # Fetch première page pour avoir pagination info
            visible_data = await self.importer.fetch_user_items(status="visible", page=1)
            sold_data = await self.importer.fetch_user_items(status="sold", page=1)

            visible_pagination = visible_data.get("pagination", {})
            sold_pagination = sold_data.get("pagination", {})

            return {
                "total_items": visible_pagination.get("total_entries", 0) + sold_pagination.get("total_entries", 0),
                "visible_items": visible_pagination.get("total_entries", 0),
                "sold_items": sold_pagination.get("total_entries", 0)
            }

        except Exception as e:
            return {
                "total_items": 0,
                "visible_items": 0,
                "sold_items": 0,
                "error": str(e)
            }

    def close(self):
        """Ferme toutes les connexions."""
        self.importer.close()
        self.publisher.close()

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# ===== Helper Functions =====

def validate_vinted_cookies(cookies: dict[str, str]) -> bool:
    """
    Valide que les cookies Vinted ont les champs requis.

    Args:
        cookies: Dictionnaire cookies

    Returns:
        bool: True si valide
    """
    required_keys = ["v_sid"]  # Session ID minimum requis

    return all(key in cookies for key in required_keys)


async def test_vinted_connection(cookies: dict[str, str]) -> dict:
    """
    Teste rapidement une connexion Vinted.

    Args:
        cookies: Cookies Vinted

    Returns:
        dict: Résultat du test
    """
    if not validate_vinted_cookies(cookies):
        return {
            "connected": False,
            "error": "Missing required cookies: v_sid"
        }

    async with VintedAdapter(cookies) as adapter:
        return await adapter.test_connection()
