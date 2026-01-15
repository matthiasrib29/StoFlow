"""
BetaSignup model for beta waitlist collection.
Stores email leads for beta program signup.
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class BetaSignup(Base):
    """
    Beta program signup model.

    Stores information about users who signed up for the beta program.
    Used for waitlist management and pre-launch marketing.
    """

    __tablename__ = "beta_signups"
    __table_args__ = {"schema": "public"}

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Contact info
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Business info
    vendor_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    monthly_volume: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="NOW()"
    )

    def __repr__(self) -> str:
        return f"<BetaSignup(id={self.id}, email={self.email}, status={self.status})>"
