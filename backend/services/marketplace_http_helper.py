"""
Marketplace HTTP Helper - Direct HTTP calls pour eBay/Etsy

Provides utility functions for making direct HTTP requests to marketplace APIs.
Used by eBay and Etsy handlers (not Vinted, which uses WebSocket).

Author: Claude
Date: 2026-01-09
"""

import httpx
from typing import Any, Optional

from shared.logging import get_logger

logger = get_logger(__name__)


class MarketplaceHttpHelper:
    """
    Helper for direct HTTP calls to marketplace APIs.

    Used by eBay and Etsy handlers (not Vinted, which uses WebSocket).

    Usage:
        result = await MarketplaceHttpHelper.call_api(
            base_url="https://api.ebay.com",
            http_method="POST",
            path="/sell/inventory/v1/inventory_item",
            headers={"Authorization": f"Bearer {token}"},
            payload={"sku": "123", "product": {...}}
        )
    """

    @staticmethod
    async def call_api(
        base_url: str,
        http_method: str,
        path: str,
        headers: dict,
        payload: Optional[dict] = None,
        params: Optional[dict] = None,
        timeout: int = 60,
        description: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Execute direct HTTP call to marketplace API.

        Args:
            base_url: API base URL (e.g., 'https://api.ebay.com')
            http_method: GET, POST, PUT, DELETE
            path: API path (e.g., '/sell/inventory/v1/inventory_item')
            headers: HTTP headers (auth, content-type)
            payload: Request body (will be serialized to JSON)
            params: Query parameters
            timeout: Timeout in seconds
            description: Description for logs

        Returns:
            dict: API response (parsed JSON)

        Raises:
            httpx.HTTPStatusError: If request fails (4xx, 5xx)
            httpx.TimeoutException: If request times out
            httpx.RequestError: If request cannot be sent
        """
        url = f"{base_url}{path}"

        log_desc = description or f"{http_method} {path}"
        logger.debug(f"[HTTP] {log_desc}")

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=http_method.upper(),
                    url=url,
                    headers=headers,
                    json=payload if payload else None,
                    params=params
                )

                # Log response status
                logger.debug(f"[HTTP] {log_desc} → {response.status_code}")

                # Raise for 4xx/5xx errors
                response.raise_for_status()

                # Parse JSON response (or return empty dict if no content)
                if response.content:
                    return response.json()
                else:
                    return {}

        except httpx.HTTPStatusError as e:
            # HTTP error (4xx, 5xx)
            error_detail = ""
            try:
                error_detail = e.response.json()
            except (ValueError, TypeError):
                # JSON parsing failed, fallback to raw text
                error_detail = e.response.text

            logger.error(
                f"[HTTP] {log_desc} failed: {e.response.status_code} - {error_detail}",
                exc_info=True,
            )
            raise

        except httpx.TimeoutException as e:
            logger.error(f"[HTTP] {log_desc} timeout after {timeout}s", exc_info=True)
            raise

        except httpx.RequestError as e:
            logger.error(f"[HTTP] {log_desc} request error: {e}", exc_info=True)
            raise
