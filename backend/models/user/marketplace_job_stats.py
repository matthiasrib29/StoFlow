"""
Marketplace Job Stats Model

Daily analytics for marketplace job execution (Vinted, eBay, Etsy).
Tracks success/failure rates, average duration per action type and marketplace.

Author: Claude
Date: 2025-12-19
Updated: 2026-01-15 - Refactored to be marketplace-agnostic
"""

from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class MarketplaceJobStats(Base):
    """
    Daily statistics for marketplace jobs.

    Table: user_{id}.marketplace_job_stats

    Aggregates job execution metrics per action type per marketplace per day.
    Used for analytics and monitoring across all marketplaces (Vinted, eBay, Etsy).
    """

    __tablename__ = "marketplace_job_stats"
    __table_args__ = (
        UniqueConstraint(
            "action_type_id", "marketplace", "date",
            name="uq_marketplace_job_stats_action_marketplace_date"
        ),
        CheckConstraint(
            "marketplace IN ('vinted', 'ebay', 'etsy')",
            name="ck_marketplace_job_stats_marketplace"
        ),
        {"schema": "tenant"},  # Placeholder for schema_translate_map
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Marketplace identifier
    marketplace: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Marketplace: vinted, ebay, or etsy"
    )

    # Action type reference (FK to marketplace-specific action_types table)
    action_type_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="FK to {marketplace}.action_types"
    )

    # Date of statistics
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )

    # Counters
    total_jobs: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    success_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    failure_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # Average duration in milliseconds
    avg_duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True  # Index for queries filtering by marketplace + created_at
    )

    def __repr__(self) -> str:
        return f"<MarketplaceJobStats(marketplace={self.marketplace}, date={self.date}, action_type_id={self.action_type_id}, total={self.total_jobs})>"

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_jobs == 0:
            return 0.0
        return (self.success_count / self.total_jobs) * 100
