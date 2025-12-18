"""
eBay Adapter

Adaptateur pour intégration eBay (OAuth2 requis).

Business Rules (2025-12-06):
- eBay utilise OAuth2 (pas de cookies comme Vinted)
- Requiert configuration app eBay Developer Program
- Pour V1: Structure de base, implémentation complète ultérieure

Author: Claude
Date: 2025-12-06
"""

from typing import Optional


class EbayAdapter:
    """
    Adaptateur pour intégration eBay.
    
    Note: eBay requiert OAuth2. Pour V1, cette classe fournit 
    la structure de base. L'implémentation complète nécessite:
    - App enregistrée sur eBay Developer Program
    - Client ID / Client Secret
    - Flux OAuth2 pour obtenir access_token
    """

    def __init__(self, access_token: str):
        """
        Initialise l'adapter avec un access token OAuth2.
        
        Args:
            access_token: Token OAuth2 eBay
        """
        self.access_token = access_token
        self.base_url = "https://api.ebay.com"

    async def test_connection(self) -> dict:
        """
        Teste la connexion eBay.
        
        Returns:
            dict: {
                "connected": bool,
                "user": {...} | None,
                "error": str | None
            }
        """
        # TODO: Implémenter avec vraie API eBay
        return {
            "connected": False,
            "user": None,
            "error": "eBay integration requires OAuth2 setup. Not implemented in V1."
        }

    async def import_all_products(self, db, user_id: int) -> dict:
        """
        Importe tous les produits eBay.
        
        Note: Non implémenté en V1.
        """
        return {
            "total_ebay": 0,
            "imported": 0,
            "skipped": 0,
            "errors": 0,
            "details": [{
                "status": "error",
                "error": "eBay OAuth2 integration not implemented in V1"
            }]
        }

    async def publish_product(self, stoflow_product: dict) -> dict:
        """
        Publie un produit sur eBay.
        
        Note: Non implémenté en V1.
        """
        return {
            "success": False,
            "item_id": None,
            "url": None,
            "error": "eBay OAuth2 integration not implemented in V1. "
                    "Requires eBay Developer Program app registration."
        }

    def close(self):
        """Cleanup ressources."""
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.close()
