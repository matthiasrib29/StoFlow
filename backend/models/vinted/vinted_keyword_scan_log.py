"""
Vinted Keyword Scan Log Model

Tracks which keywords have been scanned and up to which page,
allowing subsequent scans to resume from the last page instead
of re-scanning already-visited pages.

Author: Claude
Date: 2026-01-27
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class VintedKeywordScanLog(Base):
    """
    Log of scanned keywords for Vinted pro seller discovery.

    Each row tracks how far a keyword has been scanned (last page),
    how many pro sellers were found, and whether the search is exhausted
    (no more results available on Vinted for that keyword).

    Table: vinted.vinted_keyword_scan_logs
    """

    __tablename__ = "vinted_keyword_scan_logs"
    __table_args__ = (
        Index(
            "idx_vinted_kw_scan_keyword_mp",
            "keyword", "marketplace",
            unique=True,
        ),
        {"schema": "vinted"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    keyword: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Search keyword used"
    )
    marketplace: Mapped[str] = mapped_column(
        String(50), nullable=False, default="vinted_fr", comment="Marketplace identifier"
    )
    last_page_scanned: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Last page number successfully scanned"
    )
    total_pro_sellers_found: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Cumulative pro sellers found for this keyword"
    )
    exhausted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="True if Vinted returned no more results for this keyword"
    )
    last_scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
    )
