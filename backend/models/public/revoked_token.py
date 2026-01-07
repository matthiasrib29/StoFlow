"""
Revoked Token Model - Tokens révoqués (logout)

Stocke les tokens révoqués pour empêcher leur réutilisation après logout.
Index sur token_hash pour lookup rapide et sur expires_at pour cleanup.

Architecture:
- token_hash: SHA256 du token (pas le token en clair)
- revoked_at: Timestamp de révocation
- expires_at: Timestamp d'expiration (pour cleanup automatique)

Author: Claude
Date: 2026-01-07
"""

from datetime import datetime
from sqlalchemy import Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base
from shared.datetime_utils import utc_now


class RevokedToken(Base):
    """
    Token révoqué après logout ou refresh.

    Pour la sécurité, on stocke le SHA256 du token (pas le token en clair).
    """

    __tablename__ = "revoked_tokens"
    __table_args__ = (
        Index("idx_revoked_tokens_token_hash", "token_hash"),
        Index("idx_revoked_tokens_expires_at", "expires_at"),
    )

    # Primary key: SHA256 du token
    token_hash: Mapped[str] = mapped_column(primary_key=True, index=True)

    # Timestamps
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        doc="Timestamp de révocation"
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="Timestamp d'expiration du token (pour cleanup)"
    )

    def __repr__(self) -> str:
        return f"<RevokedToken token_hash={self.token_hash[:8]}... revoked_at={self.revoked_at}>"
