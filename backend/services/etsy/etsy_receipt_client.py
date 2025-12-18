"""
Etsy Receipt Client - Order/Receipt Management API.

Client pour gérer les commandes (receipts) Etsy:
- Get receipts (orders)
- Update receipt shipment info
- Get transactions

Scopes requis: transactions_r, transactions_w

Documentation: https://developer.etsy.com/documentation/reference/

Author: Claude
Date: 2025-12-10
"""

from typing import Any, Dict, List, Optional

from services.etsy.etsy_base_client import EtsyBaseClient


class EtsyReceiptClient(EtsyBaseClient):
    """Client Etsy Receipt/Order Management API."""

    def get_shop_receipts(
        self,
        status: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
        min_created: Optional[int] = None,
        max_created: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Récupère les receipts (commandes) du shop.

        Args:
            status: Filtre par statut (open, completed, canceled)
            limit: Nombre de résultats
            offset: Pagination offset
            min_created: Timestamp min (epoch seconds)
            max_created: Timestamp max (epoch seconds)

        Returns:
            Dict avec receipts
        """
        params = {"limit": limit, "offset": offset}

        if status:
            params["was_paid"] = True if status == "completed" else None
        if min_created:
            params["min_created"] = min_created
        if max_created:
            params["max_created"] = max_created

        return self.api_call(
            "GET",
            f"/application/shops/{self.shop_id}/receipts",
            params=params,
        )

    def get_shop_receipt(self, receipt_id: int) -> Dict[str, Any]:
        """Récupère un receipt spécifique."""
        return self.api_call(
            "GET",
            f"/application/shops/{self.shop_id}/receipts/{receipt_id}",
        )

    def update_shop_receipt(
        self,
        receipt_id: int,
        was_shipped: Optional[bool] = None,
        tracking_code: Optional[str] = None,
        carrier_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Met à jour un receipt (marquer comme expédié, ajouter tracking).

        Args:
            receipt_id: ID du receipt
            was_shipped: Marquer comme expédié
            tracking_code: Code de suivi
            carrier_name: Transporteur

        Returns:
            Receipt mis à jour
        """
        update_data = {}

        if was_shipped is not None:
            update_data["was_shipped"] = was_shipped
        if tracking_code:
            update_data["tracking_code"] = tracking_code
        if carrier_name:
            update_data["carrier_name"] = carrier_name

        return self.api_call(
            "PUT",
            f"/application/shops/{self.shop_id}/receipts/{receipt_id}",
            json_data=update_data,
        )

    def get_shop_receipt_transactions(self, receipt_id: int) -> List[Dict[str, Any]]:
        """Récupère les transactions d'un receipt."""
        result = self.api_call(
            "GET",
            f"/application/shops/{self.shop_id}/receipts/{receipt_id}/transactions",
        )
        return result.get("results", [])
