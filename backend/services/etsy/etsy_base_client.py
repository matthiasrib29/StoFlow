"""
Etsy Base Client - OAuth2 + API Call Handler.

Client de base pour toutes les API Etsy v3 avec:
- OAuth2 token management (access + refresh tokens)
- Token refresh automatique
- Rate limiting Etsy (10 req/sec)
- Error handling

Documentation officielle:
https://developer.etsy.com/documentation/

Etsy OAuth2 Flow:
1. Authorization Code → Access Token + Refresh Token
2. Access Token expire après 3600s (1h)
3. Refresh Token expire après 90 jours
4. Utiliser refresh token pour renouveler access token

Author: Claude
Date: 2025-12-10
"""

import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import requests
from sqlalchemy.orm import Session

from models.user.etsy_credentials import EtsyCredentials
from shared.exceptions import (
    EtsyAPIError,
    EtsyError,
    EtsyOAuthError,
    MarketplaceRateLimitError,
)
from shared.http_client import RateLimiter
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class EtsyBaseClient:
    """
    Client de base pour Etsy API v3 (OAuth2).

    Gère:
    - OAuth2 tokens (access + refresh)
    - Token refresh automatique
    - Rate limiting (10 req/sec)
    - Error handling

    Usage:
        >>> client = EtsyBaseClient(db_session, user_id=1)
        >>> result = client.api_call(
        ...     "GET",
        ...     "/application/shops/12345678/listings/active",
        ... )
    """

    BASE_URL = "https://openapi.etsy.com/v3"
    TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"

    # Rate limiting: Etsy limite à 10 req/sec
    RATE_LIMIT_DELAY = 0.1  # 100ms entre requêtes

    def __init__(self, db: Session, user_id: int):
        """
        Initialise le client Etsy.

        Args:
            db: Session SQLAlchemy
            user_id: ID utilisateur Stoflow

        Raises:
            ValueError: Si credentials Etsy non trouvés
        """
        self.db = db
        self.user_id = user_id
        self.last_request_time = 0

        # Charger credentials depuis DB
        self._load_credentials()

    def _load_credentials(self) -> None:
        """
        Charge les credentials Etsy depuis etsy_credentials.

        Raises:
            ValueError: Si credentials non trouvés
        """
        credentials = self.db.query(EtsyCredentials).first()

        if not credentials:
            raise ValueError(
                f"Etsy credentials not found for user {self.user_id}. "
                "Please connect Etsy account first."
            )

        # OAuth2 credentials
        import os
        self.api_key = os.getenv("ETSY_API_KEY")  # Client ID Etsy
        self.api_secret = os.getenv("ETSY_API_SECRET")  # Client Secret Etsy
        self.access_token = credentials.access_token
        self.refresh_token = credentials.refresh_token
        self.shop_id = credentials.shop_id  # Etsy shop_id

        # Token expiry dates
        self.access_token_expires_at = credentials.access_token_expires_at
        self.refresh_token_expires_at = credentials.refresh_token_expires_at

        logger.info(
            f"Etsy credentials loaded for user {self.user_id}, shop_id={self.shop_id}"
        )

    def _check_refresh_token_expiry(self) -> None:
        """
        Vérifie si le refresh token est expiré.

        Etsy refresh tokens expirent après 90 jours.

        Raises:
            RuntimeError: Si refresh token expiré
        """
        if self.refresh_token_expires_at is None:
            return

        now = datetime.now(timezone.utc)
        if now >= self.refresh_token_expires_at:
            raise RuntimeError(
                f"Etsy refresh token expired for user {self.user_id}. "
                "Please reconnect your Etsy account via /api/etsy/connect"
            )

    def _refresh_access_token(self) -> str:
        """
        Renouvelle l'access token Etsy en utilisant le refresh token.

        Etsy access tokens expirent après 3600s (1h).

        Returns:
            str: Nouvel access token

        Raises:
            RuntimeError: Si refresh échoue
        """
        self._check_refresh_token_expiry()

        logger.info(f"Refreshing Etsy access token for user {self.user_id}...")

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.api_key,
        }

        try:
            response = requests.post(
                self.TOKEN_URL,
                data=payload,
                timeout=30,
            )

            if response.status_code != 200:
                error_text = response.text
                logger.error(
                    f"Etsy token refresh failed: {response.status_code} - {error_text}"
                )
                raise RuntimeError(
                    f"Failed to refresh Etsy access token: {error_text}"
                )

            token_data = response.json()

            # Extract tokens
            new_access_token = token_data["access_token"]
            new_refresh_token = token_data["refresh_token"]
            expires_in = token_data["expires_in"]  # Seconds (3600)

            # Calculate expiry dates
            now = datetime.now(timezone.utc)
            access_token_expires_at = now + timedelta(seconds=expires_in)
            refresh_token_expires_at = now + timedelta(days=90)

            # Update in DB
            self._update_tokens_in_db(
                new_access_token,
                new_refresh_token,
                access_token_expires_at,
                refresh_token_expires_at,
            )

            # Update instance
            self.access_token = new_access_token
            self.refresh_token = new_refresh_token
            self.access_token_expires_at = access_token_expires_at
            self.refresh_token_expires_at = refresh_token_expires_at

            logger.info(f"✅ Etsy access token refreshed for user {self.user_id}")

            return new_access_token

        except Exception as e:
            logger.error(f"Error refreshing Etsy token: {e}")
            raise RuntimeError(f"Failed to refresh Etsy access token: {str(e)}")

    def _update_tokens_in_db(
        self,
        new_access_token: str,
        new_refresh_token: str,
        access_token_expires_at: datetime,
        refresh_token_expires_at: datetime,
    ) -> None:
        """
        Met à jour les tokens dans la DB.

        Args:
            new_access_token: Nouveau access token
            new_refresh_token: Nouveau refresh token
            access_token_expires_at: Date expiration access token
            refresh_token_expires_at: Date expiration refresh token
        """
        credentials = self.db.query(EtsyCredentials).first()

        if credentials:
            credentials.access_token = new_access_token
            credentials.refresh_token = new_refresh_token
            credentials.access_token_expires_at = access_token_expires_at
            credentials.refresh_token_expires_at = refresh_token_expires_at
            self.db.commit()
            logger.info(f"Etsy tokens updated in DB for user {self.user_id}")

    def get_access_token(self) -> str:
        """
        Retourne un access token valide (refresh si nécessaire).

        Returns:
            str: Access token valide
        """
        # Check if token expired or expires soon (< 5 min)
        if self.access_token_expires_at:
            now = datetime.now(timezone.utc)
            expires_soon = now + timedelta(minutes=5)

            if now >= self.access_token_expires_at or expires_soon >= self.access_token_expires_at:
                logger.info("Etsy access token expired or expires soon, refreshing...")
                return self._refresh_access_token()

        return self.access_token

    def _rate_limit(self) -> None:
        """
        Rate limiting pour respecter limite Etsy (10 req/sec).

        Attend au minimum 100ms entre chaque requête.
        """
        now = time.time()
        elapsed = now - self.last_request_time

        if elapsed < self.RATE_LIMIT_DELAY:
            sleep_time = self.RATE_LIMIT_DELAY - elapsed
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def api_call(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Effectue un appel API Etsy v3.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            endpoint: API endpoint (ex: "/application/shops/123/listings/active")
            json_data: Données JSON (pour POST/PUT/PATCH)
            params: Query parameters

        Returns:
            Response JSON

        Raises:
            requests.exceptions.HTTPError: Si erreur API

        Examples:
            >>> # GET listings
            >>> result = client.api_call(
            ...     "GET",
            ...     "/application/shops/12345678/listings/active",
            ...     params={"limit": 25}
            ... )
            >>>
            >>> # Create listing
            >>> result = client.api_call(
            ...     "POST",
            ...     "/application/shops/12345678/listings",
            ...     json_data={
            ...         "quantity": 1,
            ...         "title": "Product Title",
            ...         "price": 29.99,
            ...         # ...
            ...     }
            ... )
        """
        # Rate limiting (utilise RateLimiter partagé)
        if not hasattr(self, '_rate_limiter'):
            self._rate_limiter = RateLimiter(min_delay=0.1, max_delay=0.15)  # 10 req/sec
        self._rate_limiter.wait()

        # Get valid token
        access_token = self.get_access_token()

        # Build URL
        url = f"{self.BASE_URL}{endpoint}"

        # Headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
        }

        # Log request
        logger.debug(f"Etsy API {method} {endpoint}")

        try:
            # Make request
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data,
                params=params,
                timeout=30,
            )

            # Handle errors with standardized exceptions
            if response.status_code >= 400:
                error_data = None
                try:
                    error_data = response.json()
                except json.JSONDecodeError:
                    error_data = {"raw_text": response.text[:500] if response.text else None}

                logger.error(f"Etsy API error: {response.status_code} - {error_data}")

                # Rate limit
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    raise MarketplaceRateLimitError(
                        platform="etsy",
                        retry_after=int(retry_after) if retry_after else None,
                        operation=method.lower(),
                    )

                # Auth errors
                if response.status_code in (401, 403):
                    raise EtsyOAuthError(
                        message=f"Authentification Etsy échouée ({response.status_code})",
                        status_code=response.status_code,
                        response_body=error_data,
                    )

                # Other API errors
                raise EtsyAPIError(
                    message=f"Erreur Etsy {response.status_code} sur {method} {endpoint}",
                    status_code=response.status_code,
                    response_body=error_data,
                )

            # Return JSON (or empty dict for 204 No Content)
            if response.status_code == 204:
                return {}

            return response.json()

        except requests.exceptions.Timeout as e:
            raise EtsyError(
                message=f"Timeout sur {method} {endpoint}: {e}",
                operation=method.lower(),
            ) from e
        except requests.exceptions.RequestException as e:
            raise EtsyError(
                message=f"Erreur réseau sur {method} {endpoint}: {e}",
                operation=method.lower(),
            ) from e
