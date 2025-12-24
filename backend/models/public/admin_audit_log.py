"""
Admin Audit Log Model

Tracks all admin actions for auditing and security purposes.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class AdminAuditLog(Base):
    """
    Admin audit log entry.

    Tracks admin actions on resources (users, brands, categories, etc.).
    Used for security auditing and accountability.
    """

    __tablename__ = "admin_audit_logs"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Who performed the action
    admin_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("public.users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # What action was performed
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Action type: CREATE, UPDATE, DELETE, TOGGLE_ACTIVE, UNLOCK"
    )

    # On which resource
    resource_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Resource type: user, brand, category, color, material"
    )

    resource_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Primary key of the affected resource"
    )

    resource_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Human-readable name of the resource"
    )

    # What changed
    details: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Changed fields, before/after values"
    )

    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="IP address of the admin"
    )

    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="User agent of the admin browser"
    )

    # When
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )

    # Relationship to admin user
    admin = relationship("User", foreign_keys=[admin_id])

    def __repr__(self) -> str:
        return (
            f"<AdminAuditLog(id={self.id}, action={self.action}, "
            f"resource_type={self.resource_type}, resource_id={self.resource_id})>"
        )
