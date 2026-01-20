"""
Vinted Statistics Service

Service layer for Vinted statistics calculations.
Extracts business logic from routes for testability and reusability.

Created: 2026-01-08
Author: Claude
"""

from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.user.vinted_product import VintedProduct
from shared.logging import get_logger

logger = get_logger(__name__)


class VintedStatsService:
    """Service for calculating Vinted statistics."""

    def __init__(self, db: Session):
        """
        Initialize Vinted Stats Service.

        Args:
            db: SQLAlchemy session (schema already set via get_user_db)
        """
        self.db = db

    def get_publication_stats(self) -> dict:
        """
        Calculate aggregate statistics for Vinted publications.

        Returns:
            dict: Stats including:
                - activePublications: Number of published products
                - totalViews: Sum of all view counts
                - totalFavourites: Sum of all favourite counts
                - potentialRevenue: Sum of prices for published products (EUR)
                - totalProducts: Total number of products (all statuses)

        Raises:
            Exception: On database errors
        """
        try:
            # Active publications (status='published')
            active_count = (
                self.db.query(func.count(VintedProduct.vinted_id))
                .filter(VintedProduct.status == "published")
                .scalar() or 0
            )

            # Total views across all products
            total_views = self.db.query(func.sum(VintedProduct.view_count)).scalar() or 0

            # Total favourites across all products
            total_favourites = self.db.query(func.sum(VintedProduct.favourite_count)).scalar() or 0

            # Potential revenue from published products
            potential_revenue = (
                self.db.query(func.sum(VintedProduct.price))
                .filter(VintedProduct.status == "published")
                .scalar() or Decimal("0")
            )

            # Total products (all statuses)
            total_products = self.db.query(func.count(VintedProduct.vinted_id)).scalar() or 0

            logger.debug(
                f"[VintedStatsService] Calculated stats: active={active_count}, "
                f"views={total_views}, favourites={total_favourites}, "
                f"revenue={potential_revenue}, total={total_products}"
            )

            return {
                "activePublications": active_count,
                "totalViews": int(total_views),
                "totalFavourites": int(total_favourites),
                "potentialRevenue": float(potential_revenue),
                "totalProducts": total_products,
            }

        except Exception as e:
            logger.error(f"[VintedStatsService] Error calculating stats: {e}", exc_info=True)
            raise

    def get_product_count_by_status(self) -> dict[str, int]:
        """
        Get count of products grouped by status.

        Returns:
            dict: Mapping of status -> count
                Example: {"published": 10, "pending": 5, "sold": 3}
        """
        try:
            results = (
                self.db.query(VintedProduct.status, func.count(VintedProduct.vinted_id))
                .group_by(VintedProduct.status)
                .all()
            )

            status_counts = {status: count for status, count in results}

            logger.debug(f"[VintedStatsService] Product counts by status: {status_counts}")

            return status_counts

        except Exception as e:
            logger.error(f"[VintedStatsService] Error getting status counts: {e}", exc_info=True)
            raise

    def get_top_performing_products(self, limit: int = 10) -> list[dict]:
        """
        Get top performing products by view count.

        Args:
            limit: Maximum number of products to return

        Returns:
            list[dict]: Top products with vinted_id, title, view_count, favourite_count, price
        """
        try:
            products = (
                self.db.query(VintedProduct)
                .filter(VintedProduct.status == "published")
                .order_by(VintedProduct.view_count.desc())
                .limit(limit)
                .all()
            )

            result = [
                {
                    "vinted_id": p.vinted_id,
                    "title": p.title,
                    "view_count": p.view_count,
                    "favourite_count": p.favourite_count,
                    "price": float(p.price) if p.price else None,
                    "url": p.url,
                }
                for p in products
            ]

            logger.debug(f"[VintedStatsService] Retrieved top {len(result)} performing products")

            return result

        except Exception as e:
            logger.error(f"[VintedStatsService] Error getting top products: {e}", exc_info=True)
            raise
