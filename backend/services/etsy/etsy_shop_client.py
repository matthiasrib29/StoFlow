"""
Etsy Shop Client - Shop Management API.

Client pour gérer le shop Etsy:
- Get shop info
- Get/Create/Update shop sections
- Get shop policies (shipping, return, payment)

Scopes requis: shops_r, shops_w

Documentation: https://developer.etsy.com/documentation/tutorials/shopmanagement/

Author: Claude
Date: 2025-12-10
"""

from typing import Any, Dict, List, Optional

from services.etsy.etsy_base_client import EtsyBaseClient


class EtsyShopClient(EtsyBaseClient):
    """Client Etsy Shop Management API."""

    def get_shop(self) -> Dict[str, Any]:
        """
        Récupère les infos du shop.

        Returns:
            Shop details
        """
        return self.api_call("GET", f"/application/shops/{self.shop_id}")

    def get_shop_sections(self) -> List[Dict[str, Any]]:
        """Récupère les sections du shop (catégories internes)."""
        result = self.api_call("GET", f"/application/shops/{self.shop_id}/sections")
        return result.get("results", [])

    def create_shop_section(self, title: str) -> Dict[str, Any]:
        """Crée une section de shop."""
        return self.api_call(
            "POST",
            f"/application/shops/{self.shop_id}/sections",
            json_data={"title": title},
        )

    def update_shop_section(self, section_id: int, title: str) -> Dict[str, Any]:
        """Met à jour une section de shop."""
        return self.api_call(
            "PUT",
            f"/application/shops/{self.shop_id}/sections/{section_id}",
            json_data={"title": title},
        )

    def delete_shop_section(self, section_id: int) -> None:
        """Supprime une section de shop."""
        self.api_call(
            "DELETE",
            f"/application/shops/{self.shop_id}/sections/{section_id}",
        )
