"""
Base HTTP Client for OAuth-authenticated APIs.

Ce module fournit une classe de base pour les clients HTTP OAuth
utilisés par les intégrations marketplace (eBay, Etsy, etc.).

Features:
- Gestion automatique des headers d'authentification
- Rate limiting configurable
- Retry avec backoff exponentiel
- Gestion unifiée des erreurs
- Logging standardisé

Author: Claude
Date: 2025-12-12
"""

import random
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import requests

from shared.exceptions import (
    MarketplaceAuthError,
    MarketplaceError,
    MarketplaceRateLimitError,
)
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Rate limiter simple avec délai configurable.

    Attributes:
        min_delay: Délai minimum entre requêtes (secondes)
        max_delay: Délai maximum entre requêtes (secondes)
        last_request_time: Timestamp de la dernière requête
    """

    def __init__(self, min_delay: float = 0.3, max_delay: float = 0.8):
        """
        Initialise le rate limiter.

        Args:
            min_delay: Délai minimum entre requêtes (défaut: 0.3s)
            max_delay: Délai maximum entre requêtes (défaut: 0.8s)
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = 0.0

    def wait(self) -> None:
        """Attend le délai nécessaire avant la prochaine requête."""
        now = time.time()
        elapsed = now - self.last_request_time

        if elapsed < self.min_delay:
            delay = random.uniform(self.min_delay, self.max_delay)
            time.sleep(delay)

        self.last_request_time = time.time()


class BaseOAuthHttpClient(ABC):
    """
    Classe de base pour les clients HTTP OAuth.

    Cette classe fournit la logique commune pour :
    - Construction des headers avec token OAuth
    - Rate limiting
    - Retry avec backoff
    - Gestion des erreurs HTTP

    Les sous-classes doivent implémenter:
    - get_access_token(): Récupère le token OAuth valide
    - PLATFORM_NAME: Nom de la plateforme pour les logs/erreurs

    Example:
        >>> class EbayClient(BaseOAuthHttpClient):
        ...     PLATFORM_NAME = "ebay"
        ...
        ...     def get_access_token(self) -> str:
        ...         return self._load_token_from_db()
        ...
        >>> client = EbayClient(base_url="https://api.ebay.com")
        >>> result = client.api_call("GET", "/sell/inventory/v1/item/SKU-123")
    """

    PLATFORM_NAME: str = "unknown"

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limiter: Optional[RateLimiter] = None,
    ):
        """
        Initialise le client HTTP.

        Args:
            base_url: URL de base de l'API (ex: "https://api.ebay.com")
            timeout: Timeout en secondes pour les requêtes (défaut: 30)
            max_retries: Nombre maximum de retries (défaut: 3)
            rate_limiter: Rate limiter custom (optionnel)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limiter = rate_limiter or RateLimiter()

    @abstractmethod
    def get_access_token(self) -> str:
        """
        Récupère le token OAuth valide.

        Cette méthode doit être implémentée par les sous-classes.
        Elle devrait:
        - Retourner un token valide depuis le cache
        - Ou refresh le token si expiré
        - Ou lever une exception si impossible

        Returns:
            str: Token OAuth valide

        Raises:
            MarketplaceAuthError: Si impossible d'obtenir un token
        """
        pass

    def _build_headers(
        self,
        access_token: str,
        content_type: str = "application/json",
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """
        Construit les headers HTTP standard.

        Args:
            access_token: Token OAuth
            content_type: Content-Type header (défaut: application/json)
            extra_headers: Headers supplémentaires à fusionner

        Returns:
            Dict des headers
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": content_type,
        }

        if extra_headers:
            headers.update(extra_headers)

        return headers

    def _handle_error_response(
        self,
        response: requests.Response,
        method: str,
        path: str,
    ) -> None:
        """
        Gère les réponses d'erreur HTTP.

        Args:
            response: Réponse HTTP
            method: Méthode HTTP utilisée
            path: Chemin de l'endpoint

        Raises:
            MarketplaceRateLimitError: Si 429 Too Many Requests
            MarketplaceAuthError: Si 401/403
            MarketplaceAPIError: Pour les autres erreurs
        """
        status_code = response.status_code

        # Essayer de parser le body d'erreur
        error_body = None
        try:
            error_body = response.json()
        except (ValueError, requests.exceptions.JSONDecodeError):
            error_body = {"raw_text": response.text[:500] if response.text else None}

        # Rate limit
        if status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise MarketplaceRateLimitError(
                platform=self.PLATFORM_NAME,
                retry_after=int(retry_after) if retry_after else None,
                operation=method.lower(),
            )

        # Auth errors
        if status_code in (401, 403):
            raise MarketplaceAuthError(
                platform=self.PLATFORM_NAME,
                message=f"Authentification {self.PLATFORM_NAME} échouée ({status_code})",
                status_code=status_code,
                response_body=error_body,
            )

        # Other errors
        error_message = f"Erreur {self.PLATFORM_NAME} {status_code} sur {method} {path}"
        if error_body and isinstance(error_body, dict):
            # Extraire message d'erreur de la réponse si disponible
            api_message = error_body.get("message") or error_body.get("error") or error_body.get("errors")
            if api_message:
                error_message = f"{error_message}: {api_message}"

        raise MarketplaceError(
            message=error_message,
            platform=self.PLATFORM_NAME,
            operation=method.lower(),
            status_code=status_code,
            response_body=error_body,
        )

    def api_call(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        skip_rate_limit: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Effectue un appel API avec gestion automatique des erreurs.

        Args:
            method: Méthode HTTP (GET, POST, PUT, DELETE, PATCH)
            path: Chemin de l'endpoint (ex: "/sell/inventory/v1/item")
            params: Query parameters (optionnel)
            json_data: Corps JSON de la requête (optionnel)
            extra_headers: Headers supplémentaires (optionnel)
            skip_rate_limit: Ignorer le rate limiting (défaut: False)

        Returns:
            Dict: Réponse JSON désérialisée, ou None pour 204 No Content

        Raises:
            MarketplaceRateLimitError: Si rate limit atteint
            MarketplaceAuthError: Si erreur d'authentification
            MarketplaceAPIError: Si erreur API
            RuntimeError: Si erreur réseau/timeout après retries
        """
        # Rate limiting
        if not skip_rate_limit:
            self.rate_limiter.wait()

        # Build URL
        url = f"{self.base_url}{path}"

        # Get token
        access_token = self.get_access_token()

        # Build headers
        headers = self._build_headers(access_token, extra_headers=extra_headers)

        # Log request
        logger.debug(f"{self.PLATFORM_NAME} API {method} {path}")

        # Make request with retry
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                response = requests.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    timeout=self.timeout,
                )

                # Handle errors
                if not response.ok:
                    self._handle_error_response(response, method, path)

                # Success - No Content
                if response.status_code == 204:
                    return None

                # Success - With Content
                if response.status_code in (200, 201):
                    try:
                        return response.json()
                    except (ValueError, requests.exceptions.JSONDecodeError):
                        # Si parse JSON échoue mais status 2xx, retourner None
                        return None

                return None

            except MarketplaceRateLimitError:
                # Ne pas retry les rate limits, propager directement
                raise

            except MarketplaceAuthError:
                # Ne pas retry les erreurs d'auth, propager directement
                raise

            except MarketplaceError:
                # Ne pas retry les erreurs API (4xx), propager directement
                raise

            except requests.exceptions.Timeout as e:
                last_exception = e
                logger.warning(
                    f"{self.PLATFORM_NAME} timeout on {method} {path} "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                if attempt < self.max_retries - 1:
                    # Backoff exponentiel
                    time.sleep(2 ** attempt)

            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.warning(
                    f"{self.PLATFORM_NAME} network error on {method} {path}: {e} "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)

        # All retries exhausted
        raise RuntimeError(
            f"Erreur réseau sur {method} {path} après {self.max_retries} tentatives: {last_exception}"
        ) from last_exception


__all__ = [
    "BaseOAuthHttpClient",
    "RateLimiter",
]
