"""
eBay Account API Client.

Gère les business policies et programmes eBay du seller.

API Reference:
- https://developer.ebay.com/api-docs/sell/account/resources/methods

Responsabilités:
- Business Policies: fulfillment, payment, return (create, read, update)
- Programs: opt-in, opted-in programs
- Advertising Eligibility: check seller eligibility for Promoted Listings

Author: Claude (porté depuis pythonApiWOO)
Date: 2025-12-10
"""

import json
from typing import Any, Dict, List, Optional

import requests
from sqlalchemy.orm import Session

from services.ebay.ebay_base_client import EbayBaseClient


class EbayAccountClient(EbayBaseClient):
    """
    Client pour eBay Account API.

    Usage:
        >>> client = EbayAccountClient(db, user_id=1, marketplace_id="EBAY_FR")
        >>> 
        >>> # Récupérer les fulfillment policies
        >>> policies = client.get_fulfillment_policies()
        >>> for policy in policies['fulfillmentPolicies']:
        ...     print(f"{policy['fulfillmentPolicyId']}: {policy['name']}")
        >>> 
        >>> # Vérifier éligibilité Promoted Listings
        >>> eligibility = client.get_advertising_eligibility("EBAY_FR")
        >>> for prog in eligibility['advertisingEligibility']:
        ...     print(f"{prog['programType']}: {prog['reason']}")
    """

    # API Endpoints
    FULFILLMENT_POLICY_URL = "/sell/account/v1/fulfillment_policy"
    PAYMENT_POLICY_URL = "/sell/account/v1/payment_policy"
    RETURN_POLICY_URL = "/sell/account/v1/return_policy"
    PROGRAM_URL = "/sell/account/v1/program"
    ADVERTISING_ELIGIBILITY_URL = "/sell/account/v1/advertising_eligibility"

    # ========== FULFILLMENT POLICIES API ==========

    def get_fulfillment_policies(
        self, marketplace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Récupère les fulfillment policies (livraison) du seller.

        Args:
            marketplace_id: Marketplace (ex: "EBAY_FR")
                           Si None, utilise self.marketplace_id

        Returns:
            Dict avec 'fulfillmentPolicies' (liste) et 'total' (int)

        Examples:
            >>> policies = client.get_fulfillment_policies("EBAY_FR")
            >>> for policy in policies['fulfillmentPolicies']:
            ...     print(f"{policy['name']}: {policy['shippingOptions']}")
        """
        params = {
            "marketplace_id": marketplace_id or self.marketplace_id or "EBAY_FR"
        }
        return self.api_call(
            "GET",
            self.FULFILLMENT_POLICY_URL,
            params=params,
            scopes=["sell.account"],
        )

    def get_fulfillment_policy(self, policy_id: str) -> Dict[str, Any]:
        """
        Récupère une fulfillment policy spécifique.

        Args:
            policy_id: ID de la policy

        Returns:
            Dict avec les détails de la policy
        """
        return self.api_call(
            "GET",
            f"{self.FULFILLMENT_POLICY_URL}/{policy_id}",
            scopes=["sell.account"],
        )

    def create_fulfillment_policy(
        self, policy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crée une nouvelle fulfillment policy.

        Args:
            policy_data: Données de la policy (name, description, marketplaceId, shippingOptions, etc.)

        Returns:
            Dict avec 'fulfillmentPolicyId' et détails de la policy créée

        Examples:
            >>> policy_data = {
            ...     "name": "Standard Shipping",
            ...     "marketplaceId": "EBAY_FR",
            ...     "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
            ...     "shippingOptions": [{
            ...         "optionType": "DOMESTIC",
            ...         "shippingServices": [{
            ...             "shippingCarrierCode": "COLISSIMO",
            ...             "shippingServiceCode": "FR_ColiPoste",
            ...             "freeShipping": False,
            ...             "shippingCost": {"value": "5.00", "currency": "EUR"}
            ...         }]
            ...     }],
            ...     "handlingTime": {"value": 2, "unit": "DAY"}
            ... }
            >>> result = client.create_fulfillment_policy(policy_data)
        """
        return self.api_call(
            "POST",
            self.FULFILLMENT_POLICY_URL,
            json_data=policy_data,
            scopes=["sell.account"],
        )

    def delete_fulfillment_policy(self, policy_id: str) -> None:
        """
        Supprime une fulfillment policy.

        Args:
            policy_id: ID de la policy à supprimer

        Returns:
            None (204 No Content)
        """
        return self.api_call(
            "DELETE",
            f"{self.FULFILLMENT_POLICY_URL}/{policy_id}",
            scopes=["sell.account"],
        )

    def update_fulfillment_policy(
        self, policy_id: str, policy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Met à jour une fulfillment policy existante.

        Args:
            policy_id: ID de la policy à mettre à jour
            policy_data: Nouvelles données (même format que create)

        Returns:
            Dict avec les détails de la policy mise à jour
        """
        return self.api_call(
            "PUT",
            f"{self.FULFILLMENT_POLICY_URL}/{policy_id}",
            json_data=policy_data,
            scopes=["sell.account"],
        )

    # ========== PAYMENT POLICIES API ==========

    def get_payment_policies(
        self, marketplace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Récupère les payment policies du seller.

        Args:
            marketplace_id: Marketplace (ex: "EBAY_FR")

        Returns:
            Dict avec 'paymentPolicies' (liste) et 'total' (int)
        """
        params = {
            "marketplace_id": marketplace_id or self.marketplace_id or "EBAY_FR"
        }
        return self.api_call(
            "GET", self.PAYMENT_POLICY_URL, params=params, scopes=["sell.account"]
        )

    def get_payment_policy(self, policy_id: str) -> Dict[str, Any]:
        """Récupère une payment policy spécifique."""
        return self.api_call(
            "GET",
            f"{self.PAYMENT_POLICY_URL}/{policy_id}",
            scopes=["sell.account"],
        )

    def create_payment_policy(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle payment policy.

        Examples:
            >>> policy_data = {
            ...     "name": "PayPal + Carte",
            ...     "marketplaceId": "EBAY_FR",
            ...     "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
            ...     "paymentMethods": [
            ...         {"paymentMethodType": "PAYPAL"},
            ...         {"paymentMethodType": "CREDIT_CARD"}
            ...     ],
            ...     "immediatePay": True
            ... }
            >>> result = client.create_payment_policy(policy_data)
        """
        return self.api_call(
            "POST",
            self.PAYMENT_POLICY_URL,
            json_data=policy_data,
            scopes=["sell.account"],
        )

    def delete_payment_policy(self, policy_id: str) -> None:
        """
        Supprime une payment policy.

        Args:
            policy_id: ID de la policy à supprimer

        Returns:
            None (204 No Content)
        """
        return self.api_call(
            "DELETE",
            f"{self.PAYMENT_POLICY_URL}/{policy_id}",
            scopes=["sell.account"],
        )

    def update_payment_policy(
        self, policy_id: str, policy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Met à jour une payment policy existante.

        Args:
            policy_id: ID de la policy à mettre à jour
            policy_data: Nouvelles données (même format que create)

        Returns:
            Dict avec les détails de la policy mise à jour
        """
        return self.api_call(
            "PUT",
            f"{self.PAYMENT_POLICY_URL}/{policy_id}",
            json_data=policy_data,
            scopes=["sell.account"],
        )

    # ========== RETURN POLICIES API ==========

    def get_return_policies(
        self, marketplace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Récupère les return policies du seller.

        Args:
            marketplace_id: Marketplace (ex: "EBAY_FR")

        Returns:
            Dict avec 'returnPolicies' (liste) et 'total' (int)
        """
        params = {
            "marketplace_id": marketplace_id or self.marketplace_id or "EBAY_FR"
        }
        return self.api_call(
            "GET", self.RETURN_POLICY_URL, params=params, scopes=["sell.account"]
        )

    def get_return_policy(self, policy_id: str) -> Dict[str, Any]:
        """Récupère une return policy spécifique."""
        return self.api_call(
            "GET", f"{self.RETURN_POLICY_URL}/{policy_id}", scopes=["sell.account"]
        )

    def create_return_policy(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle return policy.

        Examples:
            >>> policy_data = {
            ...     "name": "Retours 30 jours",
            ...     "marketplaceId": "EBAY_FR",
            ...     "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
            ...     "returnsAccepted": True,
            ...     "returnPeriod": {"value": 30, "unit": "DAY"},
            ...     "refundMethod": "MONEY_BACK",
            ...     "returnShippingCostPayer": "BUYER"
            ... }
            >>> result = client.create_return_policy(policy_data)
        """
        return self.api_call(
            "POST",
            self.RETURN_POLICY_URL,
            json_data=policy_data,
            scopes=["sell.account"],
        )

    def delete_return_policy(self, policy_id: str) -> None:
        """
        Supprime une return policy.

        Args:
            policy_id: ID de la policy à supprimer

        Returns:
            None (204 No Content)
        """
        return self.api_call(
            "DELETE",
            f"{self.RETURN_POLICY_URL}/{policy_id}",
            scopes=["sell.account"],
        )

    def update_return_policy(
        self, policy_id: str, policy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Met à jour une return policy existante.

        Args:
            policy_id: ID de la policy à mettre à jour
            policy_data: Nouvelles données (même format que create)

        Returns:
            Dict avec les détails de la policy mise à jour
        """
        return self.api_call(
            "PUT",
            f"{self.RETURN_POLICY_URL}/{policy_id}",
            json_data=policy_data,
            scopes=["sell.account"],
        )

    # ========== PROGRAM API ==========

    def get_opted_in_programs(self) -> Dict[str, Any]:
        """
        Récupère la liste des programmes eBay auxquels le seller est inscrit.

        Returns:
            Dict avec 'programs' (liste des programmes actifs)

        Examples:
            >>> result = client.get_opted_in_programs()
            >>> for program in result['programs']:
            ...     print(f"{program['programType']}: {program['status']}")
        """
        return self.api_call(
            "GET", f"{self.PROGRAM_URL}/get_opted_in_programs", scopes=["sell.account"]
        )

    def opt_in_to_program(self, program_type: str) -> Dict[str, Any]:
        """
        Inscrit le seller à un programme eBay.

        Args:
            program_type: Type de programme (ex: "SELLING_POLICY_MANAGEMENT")

        Returns:
            Dict avec status de l'inscription

        Examples:
            >>> result = client.opt_in_to_program("SELLING_POLICY_MANAGEMENT")
        """
        return self.api_call(
            "POST",
            f"{self.PROGRAM_URL}/opt_in",
            json_data={"programType": program_type},
            scopes=["sell.account"],
        )

    # ========== ADVERTISING ELIGIBILITY API ==========

    def get_advertising_eligibility(
        self,
        marketplace_id: str,
        program_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Vérifie l'éligibilité du seller pour les programmes publicitaires eBay.

        Args:
            marketplace_id: ID marketplace (EBAY_FR, EBAY_GB, etc.)
            program_types: Liste des programmes à vérifier:
                          - PROMOTED_LISTINGS_STANDARD
                          - PROMOTED_LISTINGS_ADVANCED
                          - OFFSITE_ADS
                          Si None, vérifie tous les programmes

        Returns:
            Dict avec 'advertisingEligibility' (liste des résultats par programme)

        Examples:
            >>> # Vérifier tous les programmes
            >>> result = client.get_advertising_eligibility("EBAY_FR")
            >>> 
            >>> # Vérifier Promoted Listings uniquement
            >>> result = client.get_advertising_eligibility(
            ...     "EBAY_FR",
            ...     program_types=["PROMOTED_LISTINGS_STANDARD"]
            ... )
            >>> 
            >>> for prog in result['advertisingEligibility']:
            ...     print(f"{prog['programType']}: eligible={prog.get('eligible', False)}")
        """
        url = f"{self.api_base}{self.ADVERTISING_ELIGIBILITY_URL}"
        token = self.get_access_token(scopes=["sell.account.readonly"])

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": marketplace_id,
        }

        params = {}
        if program_types:
            params["program_types"] = ",".join(program_types)

        try:
            resp = requests.get(url, headers=headers, params=params, timeout=30)

            if not resp.ok:
                error_data = resp.text
                try:
                    error_data = resp.json()
                except json.JSONDecodeError:
                    pass
                raise RuntimeError(f"Erreur eBay {resp.status_code}: {error_data}")

            return resp.json()

        except requests.exceptions.Timeout as e:
            raise RuntimeError(f"Timeout advertising_eligibility: {e}") from e
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Erreur réseau advertising_eligibility: {e}") from e
