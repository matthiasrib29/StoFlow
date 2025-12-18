"""
eBay Commerce Identity API Client.

Récupère les informations du seller authentifié (nom, email, adresse, etc.).

API Reference:
- https://developer.ebay.com/api-docs/commerce/identity/overview.html

Responsabilités:
- Récupérer les informations du user authentifié
- Gérer les différents types de comptes (INDIVIDUAL vs BUSINESS)

Author: Claude
Date: 2025-12-11
"""

from typing import Any, Dict, Optional

import requests
from sqlalchemy.orm import Session

from services.ebay.ebay_base_client import EbayBaseClient


class EbayIdentityClient(EbayBaseClient):
    """
    Client pour eBay Commerce Identity API.

    Usage:
        >>> client = EbayIdentityClient(db, user_id=1)
        >>> user_info = client.get_user()
        >>> print(f"Username: {user_info['username']}")
        >>> print(f"Email: {user_info.get('email')}")
    """

    # API Endpoints (IMPORTANT: slash final requis par l'API eBay)
    USER_ENDPOINT = "/commerce/identity/v1/user/"

    def get_user(self) -> Dict[str, Any]:
        """
        Récupère les informations du user authentifié.

        Nécessite les scopes Commerce Identity (tous inclus pour info complètes):
        - commerce.identity.readonly (base)
        - commerce.identity.name.readonly (nom complet)
        - commerce.identity.email.readonly (email)
        - commerce.identity.phone.readonly (téléphone)
        - commerce.identity.address.readonly (adresse)

        Returns:
            Dict avec les informations du user:
            - userId: ID unique eBay
            - username: Nom d'utilisateur public
            - accountType: "INDIVIDUAL" ou "BUSINESS"
            - registrationMarketplaceId: Marketplace d'inscription
            - email: Email (si scope activé)
            - individualAccount: Détails compte individuel (nom, adresse, etc.)
            - businessAccount: Détails compte business (nom entreprise, etc.)

        Examples:
            >>> user_info = client.get_user()
            >>> if user_info['accountType'] == 'BUSINESS':
            ...     print(f"Business: {user_info['businessAccount']['name']}")
            ... else:
            ...     print(f"User: {user_info['individualAccount']['firstName']}")

        Raises:
            RuntimeError: Si l'appel API échoue ou si le scope n'est pas autorisé
        """
        # Utiliser seulement le scope de base (les autres nécessitent approbation spéciale)
        return self.api_call(
            "GET",
            self.USER_ENDPOINT,
            scopes=["commerce.identity.readonly"],
        )

    def get_user_safe(self) -> Optional[Dict[str, Any]]:
        """
        Version "safe" de get_user qui retourne None en cas d'erreur.

        Utile pour récupérer les infos user sans bloquer si le scope
        n'est pas configuré ou si l'API est temporairement indisponible.

        Returns:
            Dict avec les infos user, ou None si erreur
        """
        try:
            return self.get_user()
        except Exception:
            return None

    def format_user_info(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formate les données user de manière plus lisible.

        Args:
            user_data: Réponse brute de l'API get_user()

        Returns:
            Dict formaté avec les champs principaux
        """
        formatted = {
            "user_id": user_data.get("userId"),
            "username": user_data.get("username"),
            "account_type": user_data.get("accountType"),
            "marketplace": user_data.get("registrationMarketplaceId"),
        }

        # Ajouter les infos spécifiques au type de compte
        if user_data.get("accountType") == "BUSINESS":
            business = user_data.get("businessAccount", {})
            formatted.update({
                "business_name": business.get("name"),
                "email": business.get("email"),
                "phone": business.get("primaryPhone", {}).get("phoneNumber"),
                "address": self._format_address(business.get("address")),
            })
        else:
            individual = user_data.get("individualAccount", {})
            formatted.update({
                "first_name": individual.get("firstName"),
                "last_name": individual.get("lastName"),
                "email": individual.get("email"),
                "phone": individual.get("primaryPhone", {}).get("phoneNumber"),
                "address": self._format_address(individual.get("registrationAddress")),
            })

        return formatted

    def _format_address(self, address: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Formate une adresse en string lisible.

        Args:
            address: Objet adresse de l'API eBay

        Returns:
            Adresse formatée ou None
        """
        if not address:
            return None

        parts = []
        if address.get("addressLine1"):
            parts.append(address["addressLine1"])
        if address.get("addressLine2"):
            parts.append(address["addressLine2"])
        if address.get("city"):
            parts.append(address["city"])
        if address.get("stateOrProvince"):
            parts.append(address["stateOrProvince"])
        if address.get("postalCode"):
            parts.append(address["postalCode"])
        if address.get("country"):
            parts.append(address["country"])

        return ", ".join(parts) if parts else None
