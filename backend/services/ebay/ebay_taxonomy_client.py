"""
eBay Taxonomy API Client.

Client pour récupérer les catégories eBay et obtenir des suggestions
automatiques basées sur le titre du produit.

Permet de:
- Récupérer l'arbre des catégories par marketplace
- Obtenir suggestions de catégories basées sur keywords
- Récupérer aspects (attributs) requis par catégorie

Endpoints implémentés:
- GET /commerce/taxonomy/v1/category_tree/{category_tree_id} - Arbre catégories
- GET /commerce/taxonomy/v1/category_tree/{category_tree_id}/get_category_suggestions - Suggestions
- GET /commerce/taxonomy/v1/category_tree/{category_tree_id}/get_category_subtree - Sous-arbre

Documentation officielle:
https://developer.ebay.com/api-docs/commerce/taxonomy/overview.html

Author: Claude
Date: 2025-12-10
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from services.ebay.ebay_base_client import EbayBaseClient


# Category Tree IDs par marketplace
CATEGORY_TREE_IDS = {
    "EBAY_FR": "3",  # France
    "EBAY_GB": "3",  # UK
    "EBAY_DE": "77",  # Germany
    "EBAY_ES": "186",  # Spain
    "EBAY_IT": "101",  # Italy
    "EBAY_NL": "146",  # Netherlands
    "EBAY_BE": "23",  # Belgium (French)
    "EBAY_PL": "212",  # Poland
    "EBAY_US": "0",  # USA
}


class EbayTaxonomyClient(EbayBaseClient):
    """
    Client eBay Taxonomy API.

    Usage:
        >>> client = EbayTaxonomyClient(db_session, user_id=1, marketplace_id="EBAY_FR")
        >>>
        >>> # Suggérer catégories basées sur titre produit
        >>> suggestions = client.get_category_suggestions("T-shirt Nike vintage")
        >>>
        >>> for suggestion in suggestions:
        ...     print(f"Catégorie: {suggestion['categoryName']} (ID: {suggestion['categoryId']})")
        ...     print(f"Relevance: {suggestion['relevancy']}")
    """

    def __init__(
        self,
        db: Session,
        user_id: int,
        marketplace_id: Optional[str] = None,
        sandbox: bool = False,
    ):
        """
        Initialise le client Taxonomy.

        Args:
            db: Session SQLAlchemy
            user_id: ID du user
            marketplace_id: Marketplace (EBAY_FR, EBAY_GB, etc.)
            sandbox: Utiliser sandbox
        """
        super().__init__(db, user_id, marketplace_id, sandbox)

        # Récupérer category_tree_id pour ce marketplace
        self.category_tree_id = CATEGORY_TREE_IDS.get(
            marketplace_id or "EBAY_FR", "3"
        )

    def get_category_suggestions(
        self,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Obtient des suggestions de catégories basées sur un query (titre produit).

        Args:
            query: Texte de recherche (titre produit, keywords)
            limit: Nombre max de suggestions (défaut 10)

        Returns:
            Liste de suggestions triées par pertinence:
            [
                {
                    "categoryId": "11450",
                    "categoryName": "T-Shirts",
                    "categoryTreeNodeLevel": 3,
                    "categoryTreeNodeAncestors": [
                        {"categoryId": "11450", "categoryName": "Clothing"}
                    ],
                    "relevancy": "100"
                }
            ]

        Examples:
            >>> # Suggestions pour un T-shirt
            >>> suggestions = client.get_category_suggestions("T-shirt Nike homme")
            >>> best_match = suggestions[0]
            >>> print(f"Meilleure catégorie: {best_match['categoryName']}")
            >>> print(f"ID: {best_match['categoryId']}")
            >>>
            >>> # Suggestions pour un jean
            >>> suggestions = client.get_category_suggestions("Jean Levi's 501 vintage")
            >>> for s in suggestions[:3]:
            ...     print(f"{s['categoryName']} - Relevance: {s['relevancy']}%")
        """
        params = {
            "q": query,
        }

        # Note: Taxonomy API utilise scope commerce.catalog.readonly
        scopes = ["commerce.catalog.readonly"]

        result = self.api_call(
            "GET",
            f"/commerce/taxonomy/v1/category_tree/{self.category_tree_id}/get_category_suggestions",
            params=params,
            scopes=scopes,
        )

        suggestions = result.get("categorySuggestions", []) if result else []

        # Limiter résultats
        return suggestions[:limit]

    def get_best_category(
        self,
        query: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Obtient la meilleure suggestion de catégorie pour un produit.

        Helper method qui retourne la suggestion la plus pertinente.

        Args:
            query: Titre ou description du produit

        Returns:
            Meilleure suggestion ou None si aucune trouvée

        Examples:
            >>> # Obtenir meilleure catégorie
            >>> category = client.get_best_category("Robe Zara noire taille M")
            >>> if category:
            ...     print(f"Catégorie suggérée: {category['categoryName']}")
            ...     print(f"ID à utiliser: {category['categoryId']}")
            ...     # Utiliser pour publication
            ...     offer_data = service.create_offer_data(
            ...         product, sku, marketplace_id="EBAY_FR",
            ...         category_id=category['categoryId'],  # Auto-détecté
            ...         ...
            ...     )
        """
        suggestions = self.get_category_suggestions(query, limit=1)
        return suggestions[0] if suggestions else None

    def get_category_tree(
        self,
        category_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Récupère l'arbre des catégories (ou sous-arbre).

        Args:
            category_id: ID catégorie pour sous-arbre (optionnel)
                        Si None, retourne arbre complet

        Returns:
            Arbre ou sous-arbre de catégories

        Examples:
            >>> # Récupérer arbre complet
            >>> tree = client.get_category_tree()
            >>> print(f"Catégories disponibles: {tree['categoryTreeVersion']}")
            >>>
            >>> # Récupérer sous-arbre "Vêtements Homme"
            >>> subtree = client.get_category_tree(category_id="1059")
            >>> for child in subtree.get('childCategoryTreeNodes', []):
            ...     print(f"  - {child['category']['categoryName']}")
        """
        scopes = ["commerce.catalog.readonly"]

        if category_id:
            # Sous-arbre
            result = self.api_call(
                "GET",
                f"/commerce/taxonomy/v1/category_tree/{self.category_tree_id}/get_category_subtree",
                params={"category_id": category_id},
                scopes=scopes,
            )
        else:
            # Arbre complet
            result = self.api_call(
                "GET",
                f"/commerce/taxonomy/v1/category_tree/{self.category_tree_id}",
                scopes=scopes,
            )

        return result or {}

    def get_category_aspects(
        self,
        category_id: str,
    ) -> Dict[str, Any]:
        """
        Récupère les aspects (attributs) d'une catégorie.

        Retourne les aspects requis et recommandés pour une catégorie donnée.

        Args:
            category_id: ID de la catégorie eBay

        Returns:
            Aspects de la catégorie:
            {
                "categoryId": "11450",
                "aspects": [
                    {
                        "aspectConstraint": {
                            "aspectRequired": true,
                            "aspectDataType": "STRING",
                            "aspectMode": "SELECTION_ONLY"
                        },
                        "localizedAspectName": "Brand",
                        "aspectValues": [...]
                    }
                ]
            }

        Examples:
            >>> # Récupérer aspects requis pour T-shirts
            >>> aspects = client.get_category_aspects(category_id="11450")
            >>>
            >>> for aspect in aspects.get('aspects', []):
            ...     name = aspect['localizedAspectName']
            ...     required = aspect['aspectConstraint']['aspectRequired']
            ...     print(f"Aspect: {name} - Requis: {required}")
        """
        params = {
            "category_ids": category_id,
        }

        scopes = ["commerce.catalog.readonly"]

        result = self.api_call(
            "GET",
            f"/commerce/taxonomy/v1/category_tree/{self.category_tree_id}/get_item_aspects_for_category",
            params=params,
            scopes=scopes,
        )

        # Retourner aspects de la catégorie
        categories = result.get("categoryTreeNode", {}).get("categoryAspects", []) if result else []
        return categories[0] if categories else {}

    def search_categories(
        self,
        keyword: str,
    ) -> List[Dict[str, Any]]:
        """
        Recherche catégories par mot-clé.

        Alias pour get_category_suggestions avec limite étendue.

        Args:
            keyword: Mot-clé de recherche

        Returns:
            Liste de catégories correspondantes

        Examples:
            >>> # Rechercher catégories liées à "sneakers"
            >>> categories = client.search_categories("sneakers")
            >>> for cat in categories:
            ...     print(f"{cat['categoryName']} (ID: {cat['categoryId']})")
        """
        return self.get_category_suggestions(keyword, limit=20)
