"""
Etsy Shipping Client - Shipping Templates & Profiles API.

Client pour gérer les shipping profiles Etsy:
- Get shipping profiles
- Create/Update shipping profiles
- Get shipping templates

Scopes requis: shops_r, shops_w

Documentation: https://developer.etsy.com/documentation/reference/

Author: Claude
Date: 2025-12-10
"""

from typing import Any, Dict, List

from services.etsy.etsy_base_client import EtsyBaseClient


class EtsyShippingClient(EtsyBaseClient):
    """Client Etsy Shipping Management API."""

    def get_shop_shipping_profiles(self) -> List[Dict[str, Any]]:
        """
        Récupère les shipping profiles du shop.

        Returns:
            Liste des shipping profiles
        """
        result = self.api_call(
            "GET",
            f"/application/shops/{self.shop_id}/shipping-profiles",
        )
        return result.get("results", [])

    def get_shop_shipping_profile(self, profile_id: int) -> Dict[str, Any]:
        """Récupère un shipping profile spécifique."""
        return self.api_call(
            "GET",
            f"/application/shops/{self.shop_id}/shipping-profiles/{profile_id}",
        )

    def create_shop_shipping_profile(
        self,
        title: str,
        origin_country_iso: str = "US",
        primary_cost: float = 5.0,
        secondary_cost: float = 2.0,
        processing_min: int = 1,
        processing_max: int = 3,
    ) -> Dict[str, Any]:
        """
        Crée un nouveau shipping profile.

        Args:
            title: Nom du profile
            origin_country_iso: Code pays origine (US, FR, etc.)
            primary_cost: Coût shipping premier item
            secondary_cost: Coût shipping items supplémentaires
            processing_min: Jours processing min
            processing_max: Jours processing max

        Returns:
            Shipping profile créé
        """
        return self.api_call(
            "POST",
            f"/application/shops/{self.shop_id}/shipping-profiles",
            json_data={
                "title": title,
                "origin_country_iso": origin_country_iso,
                "primary_cost": primary_cost,
                "secondary_cost": secondary_cost,
                "min_processing_days": processing_min,
                "max_processing_days": processing_max,
            },
        )
