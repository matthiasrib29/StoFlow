"""
eBay Trading API Client.

API XML legacy d'eBay pour récupérer les informations du seller.
Utilisée car l'API Commerce Identity nécessite une approbation spéciale.

API Reference:
- https://developer.ebay.com/devzone/xml/docs/reference/ebay/GetUser.html

Responsabilités:
- Récupérer les informations du user/seller via Trading API
- Parser les réponses XML
- Mapper vers un format JSON simple

Author: Claude
Date: 2025-12-11
"""

import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional

import requests
from sqlalchemy.orm import Session

from services.ebay.ebay_base_client import EbayBaseClient


class EbayTradingClient(EbayBaseClient):
    """
    Client pour eBay Trading API (XML).

    Usage:
        >>> client = EbayTradingClient(db, user_id=1)
        >>> user_info = client.get_user()
        >>> print(f"Username: {user_info['username']}")
    """

    # API Endpoints Trading
    TRADING_API_URL_PRODUCTION = "https://api.ebay.com/ws/api.dll"
    TRADING_API_URL_SANDBOX = "https://api.sandbox.ebay.com/ws/api.dll"

    def get_user(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Récupère les informations d'un user via Trading API GetUser.

        Args:
            user_id: ID eBay du user (optionnel, si None = user authentifié)

        Returns:
            Dict avec les informations du user:
            - user_id: ID unique eBay
            - username: Nom d'utilisateur eBay
            - email: Email
            - registration_date: Date d'inscription
            - site: Site eBay (ex: US, FR, etc.)
            - status: Statut du compte
            - feedback_score: Score de feedback
            - positive_feedback_percent: Pourcentage feedback positif

        Raises:
            RuntimeError: Si l'appel API échoue
        """
        # Construire requête XML
        xml_request = self._build_get_user_request(user_id)

        # Faire l'appel
        url = self.TRADING_API_URL_SANDBOX if self.sandbox else self.TRADING_API_URL_PRODUCTION
        token = self.get_access_token()

        headers = {
            "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
            "X-EBAY-API-CALL-NAME": "GetUser",
            "X-EBAY-API-SITEID": "0",  # 0 = US, 71 = FR
            "X-EBAY-API-IAF-TOKEN": token,
            "Content-Type": "text/xml",
        }

        response = requests.post(url, data=xml_request, headers=headers, timeout=30)

        if not response.ok:
            raise RuntimeError(f"Trading API error: {response.status_code} - {response.text}")

        # Parser XML response
        return self._parse_get_user_response(response.text)

    def _build_get_user_request(self, user_id: Optional[str] = None) -> str:
        """
        Construit la requête XML pour GetUser.

        Args:
            user_id: ID du user (si None, récupère le user authentifié)

        Returns:
            str: Requête XML
        """
        user_id_xml = f"<UserID>{user_id}</UserID>" if user_id else ""

        return f"""<?xml version="1.0" encoding="utf-8"?>
<GetUserRequest xmlns="urn:ebay:apis:eBLBaseComponents">
    <RequesterCredentials>
        <eBayAuthToken><!-- Token géré par header --></eBayAuthToken>
    </RequesterCredentials>
    {user_id_xml}
    <DetailLevel>ReturnAll</DetailLevel>
</GetUserRequest>"""

    def _parse_get_user_response(self, xml_response: str) -> Dict[str, Any]:
        """
        Parse la réponse XML de GetUser.

        Args:
            xml_response: Réponse XML brute

        Returns:
            Dict avec les infos du user

        Raises:
            RuntimeError: Si erreur dans la réponse
        """
        # Parser XML
        root = ET.fromstring(xml_response)

        # Namespace eBay
        ns = {"ns": "urn:ebay:apis:eBLBaseComponents"}

        # Vérifier erreurs
        ack = root.find(".//ns:Ack", ns)
        if ack is not None and ack.text not in ["Success", "Warning"]:
            errors = root.findall(".//ns:Errors", ns)
            error_msgs = []
            for error in errors:
                short_msg = error.find("ns:ShortMessage", ns)
                long_msg = error.find("ns:LongMessage", ns)
                if short_msg is not None:
                    error_msgs.append(short_msg.text)
                elif long_msg is not None:
                    error_msgs.append(long_msg.text)
            raise RuntimeError(f"GetUser failed: {', '.join(error_msgs)}")

        # Extraire données User
        user_elem = root.find(".//ns:User", ns)
        if user_elem is None:
            raise RuntimeError("No User element in GetUser response")

        # Helper pour extraire texte
        def get_text(elem, path: str, default: str = "") -> str:
            found = elem.find(path, ns)
            return found.text if found is not None and found.text else default

        # Builder le dict de retour
        result = {
            "user_id": get_text(user_elem, "ns:UserID"),
            "username": get_text(user_elem, "ns:UserID"),  # UserID = username sur eBay
            "email": get_text(user_elem, "ns:Email"),
            "registration_date": get_text(user_elem, "ns:RegistrationDate"),
            "site": get_text(user_elem, "ns:Site"),
            "status": get_text(user_elem, "ns:Status"),
            "feedback_score": int(get_text(user_elem, "ns:FeedbackScore", "0")),
            "positive_feedback_percent": float(
                get_text(user_elem, "ns:PositiveFeedbackPercent", "0")
            ),
        }

        # Infos supplémentaires si disponibles
        seller_info = user_elem.find("ns:SellerInfo", ns)
        if seller_info is not None:
            result["seller_level"] = get_text(seller_info, "ns:SellerLevel", "standard")
            result["top_rated_seller"] = get_text(seller_info, "ns:TopRatedSeller") == "true"

        return result

    def get_user_safe(self) -> Optional[Dict[str, Any]]:
        """
        Version safe qui retourne None en cas d'erreur.

        Returns:
            Dict avec infos user ou None si erreur
        """
        try:
            return self.get_user()
        except Exception:
            return None
