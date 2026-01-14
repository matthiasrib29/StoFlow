"""
AI Credit Pack Model

Table for purchasable AI credit packs displayed on the credits page.

Business Rules (2026-01-14):
- Packs defined in database (easy to update without redeploy)
- Order by display_order for consistent presentation
- is_popular flag for highlighting recommended pack
- is_active flag to disable packs without deleting

Author: Claude
Date: 2026-01-14
"""

from sqlalchemy import Column, Integer, Boolean, DECIMAL
from decimal import Decimal

from shared.database import Base


class AiCreditPack(Base):
    """
    Model for AI credit packs available for purchase.

    Each pack defines a number of credits and a price.
    """
    __tablename__ = "ai_credit_packs"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)
    credits = Column(
        Integer,
        nullable=False,
        comment="Number of AI credits in this pack"
    )
    price = Column(
        DECIMAL(10, 2),
        nullable=False,
        comment="Price in euros"
    )
    is_popular = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Show as popular/recommended"
    )
    display_order = Column(
        Integer,
        nullable=False,
        default=0,
        index=True,
        comment="Order of display (lower = first)"
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Pack is available for purchase"
    )

    def __repr__(self):
        return (
            f"<AiCreditPack(id={self.id}, "
            f"credits={self.credits}, "
            f"price={self.price})>"
        )

    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "credits": self.credits,
            "price": float(self.price),
            "price_per_credit": round(float(self.price) / self.credits, 2),
            "is_popular": self.is_popular,
            "display_order": self.display_order,
        }
