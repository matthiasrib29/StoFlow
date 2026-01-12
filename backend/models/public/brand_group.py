"""
BrandGroup Model

Stores pricing data for brand×group combinations.
Used by the pricing algorithm to determine base prices and expectations.

Schema: public
Table: brand_groups
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import CheckConstraint, DECIMAL, Index, String, TIMESTAMP, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class BrandGroup(Base):
    """Brand×Group pricing data model."""

    __tablename__ = "brand_groups"
    __table_args__ = (
        CheckConstraint(
            "base_price >= 5.00 AND base_price <= 500.00",
            name="ck_brand_groups_base_price"
        ),
        CheckConstraint(
            "condition_sensitivity >= 0.5 AND condition_sensitivity <= 1.5",
            name="ck_brand_groups_sensitivity"
        ),
        UniqueConstraint("brand", "group", name="uq_brand_groups_brand_group"),
        Index("idx_brand_groups_brand", "brand"),
        Index("idx_brand_groups_group", "group"),
        Index("idx_brand_groups_created_at", "created_at"),
        {"schema": "public"}
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    group: Mapped[str] = mapped_column(String(100), nullable=False)

    # Pricing data
    base_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    condition_sensitivity: Mapped[Decimal] = mapped_column(
        DECIMAL(3, 2),
        nullable=False,
        default=Decimal("1.0")
    )

    # Expectations (JSONB lists)
    expected_origins: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    expected_decades: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    expected_trends: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Metadata
    generated_by_ai: Mapped[bool] = mapped_column(default=False, nullable=False)
    ai_confidence: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(3, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<BrandGroup(brand='{self.brand}', group='{self.group}', base_price={self.base_price})>"
