"""
Model

Stores pricing data for specific models within brand×group combinations.
Used by the pricing algorithm to apply model-specific coefficients and feature expectations.

Schema: public
Table: models
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import CheckConstraint, DECIMAL, ForeignKeyConstraint, Index, String, TIMESTAMP, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Model(Base):
    """Model-specific pricing data."""

    __tablename__ = "models"
    __table_args__ = (
        CheckConstraint(
            "coefficient >= 0.5 AND coefficient <= 3.0",
            name="ck_models_coefficient"
        ),
        ForeignKeyConstraint(
            ["brand", "group"],
            ["public.brand_groups.brand", "public.brand_groups.group"],
            name="fk_models_brand_group",
            ondelete="CASCADE"
        ),
        UniqueConstraint("brand", "group", "name", name="uq_models_brand_group_name"),
        Index("idx_models_brand_group", "brand", "group"),
        Index("idx_models_name", "name"),
        Index("idx_models_created_at", "created_at"),
        {"schema": "public"}
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    group: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Pricing data
    coefficient: Mapped[Decimal] = mapped_column(
        DECIMAL(4, 2),
        nullable=False,
        default=Decimal("1.0")
    )

    # Expected features (JSONB list)
    expected_features: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Metadata
    generated_by_ai: Mapped[bool] = mapped_column(default=False, nullable=False)
    ai_confidence: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(3, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Model(brand='{self.brand}', group='{self.group}', name='{self.name}', coefficient={self.coefficient})>"
