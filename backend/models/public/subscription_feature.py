"""
Subscription Feature Model

Table for storing the features displayed for each subscription plan.

Business Rules (2024-12-24):
- Each subscription tier has multiple features displayed on pricing page
- Features are ordered by display_order
- Feature text is displayed as-is (e.g., "Produits illimités")

Author: Claude
Date: 2024-12-24
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from shared.database import Base


class SubscriptionFeature(Base):
    """
    Model for subscription plan features.

    Stores the list of features displayed for each pricing plan.
    """
    __tablename__ = "subscription_features"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)
    subscription_quota_id = Column(
        Integer,
        ForeignKey("public.subscription_quotas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK to subscription_quotas"
    )
    feature_text = Column(
        String(200),
        nullable=False,
        comment="Feature text displayed on pricing page"
    )
    display_order = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Order of display (lower = first)"
    )

    # Relationship
    subscription_quota = relationship(
        "SubscriptionQuota",
        back_populates="features"
    )

    def __repr__(self):
        return f"<SubscriptionFeature(id={self.id}, text='{self.feature_text[:30]}...')>"

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "feature_text": self.feature_text,
            "display_order": self.display_order,
        }
