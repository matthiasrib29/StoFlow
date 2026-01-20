"""
Etsy Polling Service - Alternative aux Webhooks.

Etsy n'ayant PAS de webhooks natifs, ce service permet de:
- Poller régulièrement l'API Etsy pour détecter changements
- Récupérer nouvelles commandes
- Détecter mises à jour listings
- Détecter changements stock

À utiliser avec un scheduler (ex: APScheduler).

Documentation:
https://developer.etsy.com/documentation/reference/

Note: Etsy rate limit = 10 req/sec, 10 000 req/24h

Author: Claude
Date: 2025-12-10
"""

import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from services.etsy.etsy_listing_client import EtsyListingClient
from services.etsy.etsy_receipt_client import EtsyReceiptClient
from shared.logging import get_logger

logger = get_logger(__name__)


class EtsyPollingService:
    """
    Service de polling pour Etsy (alternative aux webhooks).

    Usage:
        >>> service = EtsyPollingService(db_session, user_id=1)
        >>>
        >>> # Poll for new orders (every 5 minutes)
        >>> new_orders = service.poll_new_receipts(since_minutes=5)
        >>> for order in new_orders:
        ...     print(f"New order: {order['receipt_id']}")
        >>>
        >>> # Poll for updated listings (every 15 minutes)
        >>> updated = service.poll_updated_listings(since_minutes=15)
    """

    def __init__(self, db: Session, user_id: int):
        """
        Initialise le service de polling.

        Args:
            db: Session SQLAlchemy
            user_id: ID utilisateur Stoflow
        """
        self.db = db
        self.user_id = user_id
        self.listing_client = EtsyListingClient(db, user_id)
        self.receipt_client = EtsyReceiptClient(db, user_id)

    def poll_new_receipts(
        self,
        since_minutes: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Polle les nouvelles commandes (receipts) depuis N minutes.

        Args:
            since_minutes: Nombre de minutes en arrière

        Returns:
            Liste des nouveaux receipts

        Examples:
            >>> # Check for new orders in last 5 minutes
            >>> new_orders = service.poll_new_receipts(since_minutes=5)
            >>> for order in new_orders:
            ...     logger.info(f"📦 New order: {order['receipt_id']}")
            ...     # TODO: Notify user, update DB, etc.
        """
        try:
            logger.info(f"Polling new Etsy receipts (last {since_minutes} min)...")

            # Calculate timestamp range
            now = datetime.now(timezone.utc)
            since = now - timedelta(minutes=since_minutes)
            min_created = int(since.timestamp())

            # Get receipts
            result = self.receipt_client.get_shop_receipts(
                min_created=min_created,
                limit=100,
            )

            receipts = result.get("results", [])

            logger.info(f"Found {len(receipts)} receipts in last {since_minutes} min")

            return receipts

        except Exception as e:
            logger.error(f"Error polling receipts: {e}")
            return []

    def poll_updated_listings(
        self,
        since_minutes: int = 15,
    ) -> List[Dict[str, Any]]:
        """
        Polle les listings mis à jour depuis N minutes.

        Note: Etsy API n'a pas de filtre "updated_since" direct.
        On récupère tous les listings actifs et on compare updated_timestamp.

        Args:
            since_minutes: Nombre de minutes en arrière

        Returns:
            Liste des listings mis à jour

        Examples:
            >>> # Check for updated listings in last 15 minutes
            >>> updated = service.poll_updated_listings(since_minutes=15)
            >>> for listing in updated:
            ...     logger.info(f"📝 Updated: {listing['title']}")
        """
        try:
            logger.info(f"Polling updated Etsy listings (last {since_minutes} min)...")

            # Calculate cutoff timestamp
            now = datetime.now(timezone.utc)
            since = now - timedelta(minutes=since_minutes)
            cutoff_timestamp = int(since.timestamp())

            # Get active listings
            result = self.listing_client.get_shop_listings_active(limit=100)
            listings = result.get("results", [])

            # Filter by updated timestamp
            updated_listings = [
                listing
                for listing in listings
                if listing.get("updated_timestamp", 0) >= cutoff_timestamp
            ]

            logger.info(
                f"Found {len(updated_listings)} updated listings in last {since_minutes} min"
            )

            return updated_listings

        except Exception as e:
            logger.error(f"Error polling listings: {e}")
            return []

    def poll_low_stock_listings(
        self,
        threshold: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Polle les listings avec stock faible.

        Args:
            threshold: Seuil de stock (ex: alerte si ≤ 5)

        Returns:
            Liste des listings avec stock faible

        Examples:
            >>> # Check for low stock items
            >>> low_stock = service.poll_low_stock_listings(threshold=5)
            >>> for listing in low_stock:
            ...     logger.warning(f"⚠️  Low stock: {listing['title']} ({listing['quantity']})")
        """
        try:
            logger.info(f"Polling low stock listings (threshold={threshold})...")

            # Get active listings
            result = self.listing_client.get_shop_listings_active(limit=100)
            listings = result.get("results", [])

            # Filter by quantity
            low_stock_listings = [
                listing
                for listing in listings
                if listing.get("quantity", 0) <= threshold
            ]

            logger.info(
                f"Found {len(low_stock_listings)} listings with stock ≤ {threshold}"
            )

            return low_stock_listings

        except Exception as e:
            logger.error(f"Error polling low stock: {e}")
            return []

    def run_polling_cycle(
        self,
        check_orders: bool = True,
        check_listings: bool = True,
        check_stock: bool = True,
        order_interval: int = 5,
        listing_interval: int = 15,
        stock_threshold: int = 5,
    ) -> Dict[str, Any]:
        """
        Exécute un cycle complet de polling.

        Args:
            check_orders: Poller les nouvelles commandes
            check_listings: Poller les listings mis à jour
            check_stock: Poller le stock faible
            order_interval: Intervalle commandes (minutes)
            listing_interval: Intervalle listings (minutes)
            stock_threshold: Seuil stock faible

        Returns:
            Dict avec résultats polling

        Examples:
            >>> # Run full polling cycle
            >>> results = service.run_polling_cycle(
            ...     order_interval=5,
            ...     listing_interval=15,
            ...     stock_threshold=5,
            ... )
            >>> print(f"New orders: {results['new_orders_count']}")
            >>> print(f"Updated listings: {results['updated_listings_count']}")
        """
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "new_orders": [],
            "new_orders_count": 0,
            "updated_listings": [],
            "updated_listings_count": 0,
            "low_stock_listings": [],
            "low_stock_count": 0,
        }

        try:
            # 1. Check for new orders
            if check_orders:
                new_orders = self.poll_new_receipts(since_minutes=order_interval)
                results["new_orders"] = new_orders
                results["new_orders_count"] = len(new_orders)

                # Rate limiting (respect 10 req/sec)
                time.sleep(0.2)

            # 2. Check for updated listings
            if check_listings:
                updated_listings = self.poll_updated_listings(
                    since_minutes=listing_interval
                )
                results["updated_listings"] = updated_listings
                results["updated_listings_count"] = len(updated_listings)

                time.sleep(0.2)

            # 3. Check for low stock
            if check_stock:
                low_stock = self.poll_low_stock_listings(threshold=stock_threshold)
                results["low_stock_listings"] = low_stock
                results["low_stock_count"] = len(low_stock)

            logger.info(f"✅ Polling cycle complete: {results['new_orders_count']} orders, {results['updated_listings_count']} listings, {results['low_stock_count']} low stock")

            return results

        except Exception as e:
            logger.error(f"Error in polling cycle: {e}")
            results["error"] = str(e)
            return results
