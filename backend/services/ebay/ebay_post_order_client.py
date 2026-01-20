"""
eBay Post-Order API Base Client.

Client for Post-Order API v2 (cancellations, returns, inquiries).
Inherits from EbayBaseClient for OAuth handling.

Post-Order API is an eBay "traditional API" that uses the same OAuth tokens
but different base URL: https://api.ebay.com/post-order/v2/

The api_scope OAuth scope provides access to traditional APIs including Post-Order.
No additional scopes are required.

Documentation:
https://developer.ebay.com/devzone/post-order/index.html

Author: Claude
Date: 2026-01-13
"""

from typing import Any, Dict, Optional

import requests
from sqlalchemy.orm import Session

from services.ebay.ebay_base_client import EbayBaseClient
from shared.exceptions import (
    EbayAPIError,
    EbayError,
    EbayOAuthError,
    MarketplaceRateLimitError,
)
from shared.http_client import RateLimiter
from shared.logging import get_logger

logger = get_logger(__name__)


class EbayPostOrderClient(EbayBaseClient):
    """
    Base client for eBay Post-Order API v2.

    Provides api_call_post_order() method for Post-Order endpoints.
    Subclasses will implement specific domain methods:
    - EbayCancellationClient (cancellations)
    - EbayReturnClient (returns)
    - EbayInquiryClient (INR inquiries)

    Usage:
        >>> client = EbayPostOrderClient(db_session, user_id=1)
        >>> # Search cancellations
        >>> data = client.api_call_post_order("GET", "/cancellation/search", params={...})
        >>> # Get return details
        >>> data = client.api_call_post_order("GET", "/return/123456")
    """

    # Post-Order API Base URLs (different from standard API)
    POST_ORDER_BASE_SANDBOX = "https://api.sandbox.ebay.com/post-order/v2"
    POST_ORDER_BASE_PRODUCTION = "https://api.ebay.com/post-order/v2"

    def __init__(
        self,
        db: Session,
        user_id: int,
        marketplace_id: Optional[str] = None,
        sandbox: bool = False,
    ):
        """
        Initialize Post-Order API client.

        Args:
            db: SQLAlchemy session
            user_id: User ID for credentials lookup
            marketplace_id: Optional marketplace (EBAY_FR, EBAY_DE, etc.)
            sandbox: Use sandbox environment
        """
        super().__init__(db, user_id, marketplace_id, sandbox)
        self.post_order_base = (
            self.POST_ORDER_BASE_SANDBOX
            if self.sandbox
            else self.POST_ORDER_BASE_PRODUCTION
        )

    def api_call_post_order(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        API call specific to Post-Order API v2.

        Uses Post-Order base URL instead of standard API base URL.
        The OAuth token is the same (inherited from EbayBaseClient).

        Args:
            method: HTTP method (GET, POST, PUT)
            path: Endpoint path (e.g., "/cancellation/search", "/return/123")
            params: Query parameters
            json_data: Request body JSON

        Returns:
            Response JSON or None for 204 responses

        Raises:
            EbayAPIError: For API errors (4xx, 5xx)
            EbayOAuthError: For authentication errors (401, 403)
            MarketplaceRateLimitError: For rate limiting (429)
            EbayError: For network/timeout errors

        Examples:
            >>> # Search cancellations
            >>> result = client.api_call_post_order(
            ...     "GET",
            ...     "/cancellation/search",
            ...     params={"order_id": "12-34567-89012"}
            ... )
            >>>
            >>> # Approve cancellation
            >>> result = client.api_call_post_order(
            ...     "POST",
            ...     "/cancellation/ABC123/approve"
            ... )
        """
        # Build full URL with Post-Order base
        url = f"{self.post_order_base}{path}"

        # Get OAuth token (same as RESTful APIs - api_scope covers traditional APIs)
        token = self.get_access_token()

        # Determine marketplace ID for header
        marketplace_id = self.marketplace_id or "EBAY_FR"

        # Headers for Post-Order API
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": marketplace_id,
        }

        # Rate limiting (reuse from base client)
        if not hasattr(self, "_post_order_rate_limiter"):
            self._post_order_rate_limiter = RateLimiter(min_delay=0.3, max_delay=0.8)
        self._post_order_rate_limiter.wait()

        logger.debug(f"eBay Post-Order API {method} {path}")

        try:
            resp = requests.request(
                method.upper(),
                url,
                headers=headers,
                params=params,
                json=json_data,
                timeout=30,
            )

            # Handle errors
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
                        message=f"Post-Order API auth failed ({resp.status_code})",
                        status_code=resp.status_code,
                        response_body=error_data,
                    )

                # Other API errors
                raise EbayAPIError(
                    message=f"Post-Order API error {resp.status_code} on {method} {path}",
                    status_code=resp.status_code,
                    response_body=error_data,
                )

            # Success without content
            if resp.status_code == 204 or not resp.text:
                return None

            # Success with JSON content
            try:
                return resp.json()
            except (ValueError, requests.exceptions.JSONDecodeError):
                return None

        except requests.exceptions.Timeout as e:
            raise EbayError(
                message=f"Timeout on Post-Order {method} {path}: {e}",
                operation=method.lower(),
            ) from e
        except requests.exceptions.RequestException as e:
            raise EbayError(
                message=f"Network error on Post-Order {method} {path}: {e}",
                operation=method.lower(),
            ) from e
