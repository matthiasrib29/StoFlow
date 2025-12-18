"""
Etsy Taxonomy Client - Category/Taxonomy API.

Client pour naviguer la taxonomie Etsy (catégories):
- Get seller taxonomy (categories)
- Get taxonomy properties (attributes requis par catégorie)

Documentation: https://developer.etsy.com/documentation/reference/

Author: Claude
Date: 2025-12-10
"""

from typing import Any, Dict, List, Optional

from services.etsy.etsy_base_client import EtsyBaseClient


class EtsyTaxonomyClient(EtsyBaseClient):
    """Client Etsy Taxonomy API."""

    def get_seller_taxonomy_nodes(self) -> List[Dict[str, Any]]:
        """
        Récupère toutes les catégories Etsy disponibles pour les sellers.

        Returns:
            Liste de nodes taxonomy (catégories)

        Examples:
            >>> nodes = client.get_seller_taxonomy_nodes()
            >>> for node in nodes:
            ...     print(f"{node['id']}: {node['name']} (level {node['level']})")
        """
        result = self.api_call("GET", "/application/seller-taxonomy/nodes")
        return result.get("results", [])

    def get_properties_by_taxonomy_id(
        self,
        taxonomy_id: int,
    ) -> List[Dict[str, Any]]:
        """
        Récupère les propriétés requises pour une catégorie.

        Args:
            taxonomy_id: ID de la catégorie Etsy

        Returns:
            Liste des propriétés (attributes) requis

        Examples:
            >>> props = client.get_properties_by_taxonomy_id(1234)
            >>> for prop in props:
            ...     required = "✓" if prop.get("is_required") else ""
            ...     print(f"{required} {prop['name']}: {prop['display_name']}")
        """
        result = self.api_call(
            "GET",
            f"/application/seller-taxonomy/nodes/{taxonomy_id}/properties",
        )
        return result.get("results", [])

    def search_taxonomy(self, query: str) -> List[Dict[str, Any]]:
        """
        Recherche une catégorie par mot-clé.

        Args:
            query: Mot-clé de recherche

        Returns:
            Liste de catégories correspondantes

        Examples:
            >>> categories = client.search_taxonomy("necklace")
            >>> for cat in categories:
            ...     print(f"{cat['id']}: {cat['name']}")
        """
        # Note: Etsy API n'a pas d'endpoint de recherche direct
        # On récupère toutes les catégories et filtre localement
        all_nodes = self.get_seller_taxonomy_nodes()

        query_lower = query.lower()
        matching = [
            node
            for node in all_nodes
            if query_lower in node.get("name", "").lower()
        ]

        return matching

    def get_category_by_id(self, taxonomy_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère une catégorie spécifique par son ID.

        Args:
            taxonomy_id: ID de la catégorie

        Returns:
            Category details ou None
        """
        all_nodes = self.get_seller_taxonomy_nodes()

        for node in all_nodes:
            if node.get("id") == taxonomy_id:
                return node

        return None
