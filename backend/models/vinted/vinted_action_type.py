"""
Vinted Action Type Model

Reference table for Vinted action types with their configuration.
Shared across all tenants (vinted schema).

Author: Claude
Date: 2025-12-19
Updated: 2025-12-24 - Moved to vinted schema
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class VintedActionType(Base):
    """
    Reference table for Vinted action types.

    Defines the different types of actions that can be performed on Vinted,
    along with their priority, rate limiting, and retry configuration.

    Table: vinted.vinted_action_types
    """

    __tablename__ = "vinted_action_types"
    __table_args__ = {"schema": "vinted"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="Unique code: publish, sync, orders, message, update, delete"
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Display name"
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
        comment="1=CRITICAL, 2=HIGH, 3=NORMAL, 4=LOW"
    )

    is_batch: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True if action processes multiple items"
    )

    rate_limit_ms: Mapped[int] = mapped_column(
        Integer,
        default=2000,
        nullable=False,
        comment="Delay between requests in ms"
    )

    max_retries: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False
    )

    timeout_seconds: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<VintedActionType(code={self.code}, priority={self.priority})>"
