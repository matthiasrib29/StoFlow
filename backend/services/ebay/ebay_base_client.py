"""
eBay Base Client avec OAuth2 et appels API génériques.

Client de base multi-tenant pour toutes les interactions avec l'API eBay.

Responsabilités:
- Authentification OAuth2 avec refresh token par user
- Cache du token en mémoire
- Méthode api_call() générique pour tous les endpoints
- Gestion du rate limiting
- AUCUNE logique métier

Architecture multi-tenant:
- Credentials récupérés depuis ebay_credentials (user schema)
- Client ID/Secret depuis .env
- Token caché par user_id
- Support marketplace_id pour Content-Language automatique

Author: Claude (porté depuis pythonApiWOO)
Date: 2025-12-10
"""

import base64
import os
import time
from typing import Any, Dict, Optional

import requests
from sqlalchemy.orm import Session

from models.public.ebay_marketplace_config import MarketplaceConfig
from models.user.ebay_credentials import EbayCredentials
from shared.exceptions import (
    EbayAPIError,
    EbayError,
    EbayOAuthError,
    MarketplaceRateLimitError,
)
from shared.http_client import RateLimiter
from shared.logging import get_logger
from shared.timing import timed_operation, measure_operation

logger = get_logger(__name__)


class EbayBaseClient:
    """
    Client de base eBay multi-tenant avec OAuth2.

    Usage:
        >>> client = EbayBaseClient(db_session, user_id=1)
        >>> data = client.api_call("GET", "/sell/inventory/v1/inventory_item/SKU-123")
        >>> # Avec marketplace spécifique
        >>> client_fr = EbayBaseClient(db_session, user_id=1, marketplace_id="EBAY_FR")
        >>> data = client_fr.api_call("POST", "/sell/inventory/v1/inventory_item", json_data={...})
    """

    # API Base URL
    API_BASE_SANDBOX = "https://api.sandbox.ebay.com"
    API_BASE_PRODUCTION = "https://api.ebay.com"

    # Commerce API Base URL (différent ! utilise 'apiz' au lieu de 'api')
    COMMERCE_API_BASE_SANDBOX = "https://apiz.sandbox.ebay.com"
    COMMERCE_API_BASE_PRODUCTION = "https://apiz.ebay.com"

    # Token cache (partagé entre instances) - Format: {user_id: (token, timestamp)}
    # NOTE: Scopes are inherited from refresh token, no need to cache by scope
    _token_cache: Dict[int, tuple[str, float]] = {}
    _token_max_age: int = 7000  # 1h56min (eBay tokens expirent à 2h)

    # OAuth Scopes
    SCOPES = {
        "api_scope": "https://api.ebay.com/oauth/api_scope",
        "sell.inventory": "https://api.ebay.com/oauth/api_scope/sell.inventory",
        "sell.account": "https://api.ebay.com/oauth/api_scope/sell.account",
        "sell.account.readonly": "https://api.ebay.com/oauth/api_scope/sell.account.readonly",
        "sell.fulfillment": "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
        "sell.fulfillment.readonly": "https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly",
        "sell.analytics": "https://api.ebay.com/oauth/api_scope/sell.analytics",
        "sell.analytics.readonly": "https://api.ebay.com/oauth/api_scope/sell.analytics.readonly",
        "sell.compliance": "https://api.ebay.com/oauth/api_scope/sell.compliance",
        "sell.marketing": "https://api.ebay.com/oauth/api_scope/sell.marketing",
        "sell.marketing.readonly": "https://api.ebay.com/oauth/api_scope/sell.marketing.readonly",
        "commerce.catalog.readonly": "https://api.ebay.com/oauth/api_scope/commerce.catalog.readonly",
    }

    def __init__(
        self,
        db: Session,
        user_id: int,
        marketplace_id: Optional[str] = None,
        sandbox: bool = False,
    ):
        """
        Initialise le client eBay pour un user spécifique.

        Args:
            db: Session SQLAlchemy
            user_id: ID du user (pour récupérer credentials)
            marketplace_id: Marketplace optionnelle (EBAY_FR, EBAY_GB, etc.)
                           Si fournie, Content-Language sera automatiquement défini
            sandbox: Utiliser l'environnement sandbox (défaut: production)
        """
        self.db = db
        self.user_id = user_id
        self.marketplace_id = marketplace_id
        self.sandbox = sandbox or os.getenv("EBAY_SANDBOX", "false").lower() == "true"

        # API Base URL
        self.api_base = self.API_BASE_SANDBOX if self.sandbox else self.API_BASE_PRODUCTION

        # Load credentials depuis ebay_credentials
        self._load_credentials()

        # Load marketplace config si marketplace_id fourni
        self.marketplace_config: Optional[MarketplaceConfig] = None
        if marketplace_id:
            self.marketplace_config = (
                db.query(MarketplaceConfig)
                .filter(MarketplaceConfig.marketplace_id == marketplace_id)
                .first()
            )
            if not self.marketplace_config:
                raise ValueError(f"Marketplace inconnue: {marketplace_id}")

    def _load_credentials(self) -> None:
        """
        Charge les credentials eBay depuis ebay_credentials (user schema).

        Raises:
            ValueError: Si le user n'a pas de credentials eBay configurés
        """
        # Récupérer credentials depuis ebay_credentials (user schema)
        ebay_creds = self.db.query(EbayCredentials).first()

        if not ebay_creds:
            raise ValueError(
                f"User {self.user_id} n'a pas de compte eBay configuré. "
                "Merci de configurer les credentials via /api/ebay/connect"
            )

        # Récupérer client_id et client_secret depuis .env
        self.client_id = os.getenv("EBAY_CLIENT_ID")
        self.client_secret = os.getenv("EBAY_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Credentials eBay incomplets. "
                "Veuillez configurer EBAY_CLIENT_ID et EBAY_CLIENT_SECRET dans .env"
            )

        # Vérifier refresh token
        if not ebay_creds.refresh_token:
            raise ValueError(
                f"Refresh token manquant pour user {self.user_id}. "
                "Veuillez compléter le OAuth flow."
            )

        # Stocker les credentials
        self.refresh_token = ebay_creds.refresh_token
        self.refresh_token_expires_at = ebay_creds.refresh_token_expires_at
        self.ebay_credentials = ebay_creds  # Garder référence pour updates

    def _check_refresh_token_expiry(self) -> None:
        """
        Vérifie si le refresh token est expiré.

        Raises:
            RuntimeError: Si le refresh token est expiré (user doit se reconnecter)
        """
        if self.refresh_token_expires_at is None:
            # Pas de date d'expiration = refresh token permanent (legacy)
            return

        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        if now >= self.refresh_token_expires_at:
            raise RuntimeError(
                f"eBay refresh token expired for user {self.user_id}. "
                "Please reconnect your eBay account via /api/ebay/connect"
            )

    def _refresh_access_token(self) -> str:
        """
        Renouvelle l'access token eBay en utilisant le refresh token.

        Cette méthode est appelée automatiquement par get_access_token()
        quand le token en cache expire.

        IMPORTANT: Les scopes ne sont PAS envoyés lors du refresh.
        Ils sont hérités de l'autorisation initiale et ne peuvent pas être modifiés.

        Returns:
            str: Nouveau access token

        Raises:
            RuntimeError: Si le refresh échoue ou si le refresh token est expiré
        """
        # Vérifier que refresh token n'est pas expiré
        self._check_refresh_token_expiry()

        token_url = f"{self.api_base}/identity/v1/oauth2/token"
        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_b64 = base64.b64encode(auth_str.encode()).decode()

        # NOTE: scope parameter is NOT included in refresh token requests
        # Scopes are inherited from the original authorization
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            resp = requests.post(
                token_url, data=payload, headers=headers, timeout=30
            )
            resp.raise_for_status()
            token_data = resp.json()
            access_token = token_data["access_token"]

            # eBay peut retourner un nouveau refresh_token (token rotation)
            # Si présent, on le met à jour dans la DB
            new_refresh_token = token_data.get("refresh_token")
            if new_refresh_token and new_refresh_token != self.refresh_token:
                self._update_refresh_token_in_db(new_refresh_token, token_data)

            return access_token

        except requests.exceptions.HTTPError as e:
            error_msg = f"Erreur OAuth HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg += f": {error_data}"
            except (ValueError, requests.exceptions.JSONDecodeError):
                error_msg += f": {e.response.text}"
            raise RuntimeError(error_msg) from e

        except Exception as e:
            raise RuntimeError(f"Échec OAuth eBay: {e}") from e

    def _update_refresh_token_in_db(
        self, new_refresh_token: str, token_data: dict
    ) -> None:
        """
        Met à jour le refresh token dans la DB (token rotation eBay).

        Args:
            new_refresh_token: Nouveau refresh token
            token_data: Réponse complète du token endpoint
        """
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)

        # Calculer expiration du nouveau refresh token (18 mois par défaut)
        refresh_token_expires_in = token_data.get("refresh_token_expires_in", 47304000)
        new_refresh_token_expires_at = now + timedelta(seconds=refresh_token_expires_in)

        # Mettre à jour en DB
        self.ebay_credentials.refresh_token = new_refresh_token
        self.ebay_credentials.refresh_token_expires_at = new_refresh_token_expires_at

        self.db.commit()

        # Mettre à jour instance locale
        self.refresh_token = new_refresh_token
        self.refresh_token_expires_at = new_refresh_token_expires_at

    def _normalize_scopes(self, scopes: Optional[list[str] | str]) -> str:
        """
        Normalise les scopes en URLs complètes.

        Args:
            scopes: Liste de scopes ou scope unique (ou None pour api_scope par défaut)

        Returns:
            str: Scopes séparés par espace

        Examples:
            >>> client._normalize_scopes(["sell.inventory", "sell.account"])
            "https://api.ebay.com/oauth/api_scope/sell.inventory https://api.ebay.com/oauth/api_scope/sell.account"
        """
        if scopes is None:
            scopes = ["api_scope"]
        if isinstance(scopes, str):
            scopes = [scopes]

        resolved = []
        for item in scopes:
            s = item.strip()
            # Si déjà une URL complète, garder tel quel
            if s.startswith("http"):
                resolved.append(s)
            else:
                # Chercher dans le mapping
                url = self.SCOPES.get(s)
                if url:
                    resolved.append(url)

        # Retourner scopes uniques séparés par espace
        return " ".join(sorted(set(resolved)))

    def get_access_token(self, scopes: Optional[list[str] | str] = None) -> str:
        """
        Récupère un access token OAuth2 avec cache et refresh automatique.

        Cache le token par user_id pour éviter les appels répétés.
        Les tokens eBay expirent après 2h, on les rafraîchit après 1h56.

        Si le token en cache expire, cette méthode appelle automatiquement
        _refresh_access_token() pour obtenir un nouveau token.

        NOTE: Le paramètre scopes est conservé pour compatibilité API mais n'est pas utilisé.
        Les scopes sont hérités du refresh token et ne peuvent pas être modifiés.

        Args:
            scopes: (Ignoré) Scopes OAuth - hérités de l'autorisation initiale

        Returns:
            str: Access token valide

        Raises:
            RuntimeError: Si l'authentification échoue ou si le refresh token est expiré

        Author: Claude
        Date: 2025-12-10
        Updated: 2026-01-07 - Scopes hérités, pas de paramètre scope lors du refresh
        """
        # Vérifier cache (par user_id uniquement, les scopes sont fixes)
        if self.user_id in self._token_cache:
            cached_token, timestamp = self._token_cache[self.user_id]
            token_age = time.time() - timestamp
            if token_age < self._token_max_age:
                return cached_token

        # Token expiré ou non présent → refresh automatique
        access_token = self._refresh_access_token()

        # Mettre en cache (clé simple: user_id)
        self._token_cache[self.user_id] = (access_token, time.time())

        return access_token

    def api_call(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        scopes: Optional[list[str] | str] = None,
        content_language: Optional[str] = None,
    ) -> Any:
        """
        Appel API générique eBay.

        Args:
            method: Méthode HTTP (GET, POST, PUT, DELETE)
            path: Chemin de l'endpoint (ex: /sell/inventory/v1/inventory_item/SKU-123)
            params: Paramètres query string
            json_data: Corps de la requête JSON
            scopes: Scopes OAuth requis (défaut: api_scope)
            content_language: Content-Language header (ex: fr-FR)
                             Si None et marketplace_id défini, auto-détecté

        Returns:
            Dict ou None: Réponse JSON désérialisée (None pour 204/201 sans contenu)

        Raises:
            RuntimeError: Si la requête échoue

        Examples:
            >>> # GET simple
            >>> client.api_call("GET", "/sell/inventory/v1/inventory_item/SKU-123")
            {'sku': 'SKU-123', 'product': {...}}

            >>> # POST avec Content-Language auto
            >>> client_fr = EbayBaseClient(db, user_id=1, marketplace_id="EBAY_FR")
            >>> client_fr.api_call("POST", "/sell/inventory/v1/inventory_item", json_data={...})
            # Content-Language: fr-FR sera automatiquement ajouté
        """
        # Utiliser Commerce API base URL pour les endpoints /commerce/*
        # Exception: Taxonomy API uses standard api.ebay.com, not apiz.ebay.com
        if path.startswith("/commerce/") and not path.startswith("/commerce/taxonomy/"):
            api_base = self.COMMERCE_API_BASE_SANDBOX if self.sandbox else self.COMMERCE_API_BASE_PRODUCTION
        else:
            api_base = self.api_base

        url = f"{api_base}{path}"
        token = self.get_access_token(scopes)

        # Déterminer Content-Language
        if content_language is None and self.marketplace_config:
            content_language = self.marketplace_config.get_content_language()
        if content_language is None:
            content_language = "en-US"  # Fallback

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Content-Language": content_language,
        }

        # Rate limiting (utilise le RateLimiter partagé)
        if not hasattr(self, '_rate_limiter'):
            self._rate_limiter = RateLimiter(min_delay=0.3, max_delay=0.8)
        self._rate_limiter.wait()

        logger.debug(f"eBay API {method} {path}")

        try:
            resp = requests.request(
                method.upper(),
                url,
                headers=headers,
                params=params,
                json=json_data,
                timeout=30,
            )

            # Gestion des erreurs avec exceptions standardisées
            if not resp.ok:
                error_data = None
                try:
                    error_data = resp.json()
                except (ValueError, requests.exceptions.JSONDecodeError):
                    error_data = {"raw_text": resp.text[:500] if resp.text else None}

                # Rate limit
                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    raise MarketplaceRateLimitError(
                        platform="ebay",
                        retry_after=int(retry_after) if retry_after else None,
                        operation=method.lower(),
                    )

                # Auth errors
                if resp.status_code in (401, 403):
                    raise EbayOAuthError(
                        message=f"Authentification eBay échouée ({resp.status_code})",
                        status_code=resp.status_code,
                        response_body=error_data,
                    )

                # Other API errors
                raise EbayAPIError(
                    message=f"Erreur eBay {resp.status_code} sur {method} {path}",
                    status_code=resp.status_code,
                    response_body=error_data,
                )

            # Success sans contenu
            if resp.status_code in (204, 201) and not resp.text:
                return None

            # Success avec contenu JSON
            if resp.status_code in (200, 201):
                try:
                    return resp.json()
                except (ValueError, requests.exceptions.JSONDecodeError):
                    # Si parse JSON échoue mais status 2xx, retourner None
                    return None

            return None

        except requests.exceptions.Timeout as e:
            raise EbayError(
                message=f"Timeout sur {method} {path}: {e}",
                operation=method.lower(),
            ) from e
        except requests.exceptions.RequestException as e:
            raise EbayError(
                message=f"Erreur réseau sur {method} {path}: {e}",
                operation=method.lower(),
            ) from e
