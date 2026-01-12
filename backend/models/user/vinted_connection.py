"""
Modèle pour la connexion Vinted.

Source de vérité unique pour l'état de connexion Vinted d'un utilisateur.
Les colonnes User.vinted_* ont été supprimées au profit de ce modèle.

Business Rules:
- Un user Stoflow = un compte Vinted max
- is_connected = True si l'utilisateur est connecté à Vinted
- Le plugin détecte les connexions/déconnexions et notifie le backend
- Le frontend peut vérifier via /check-connection (task plugin)

Author: Claude
Date: 2025-12-17
Updated: 2026-01-12 - Aligned with actual DB schema
"""

from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, Boolean, Float, Enum
from shared.database import Base


class DataDomeStatus(str, PyEnum):
    """Status of the DataDome session."""
    OK = "OK"
    VALID = "VALID"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    BLOCKED = "BLOCKED"
    CAPTCHA_REQUIRED = "CAPTCHA_REQUIRED"
    UNKNOWN = "UNKNOWN"


class VintedConnection(Base):
    """
    Table pour stocker la connexion Vinted d'un utilisateur.

    Attributes:
        id: Primary key
        vinted_user_id: ID utilisateur Vinted
        username: Username Vinted
        is_connected: True si actuellement connecté
        user_id: FK vers l'utilisateur Stoflow
        session_id: Session Vinted
        csrf_token: CSRF token pour les requêtes
        datadome_cookie: Cookie DataDome
    """
    __tablename__ = "vinted_connection"

    # Primary key
    id = Column(Integer, primary_key=True)

    # Vinted user info
    vinted_user_id = Column(BigInteger, nullable=True, index=True)
    username = Column(String(255), nullable=True, index=True)

    # Connection state
    is_connected = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="True si l'utilisateur est connecté à Vinted"
    )

    # Relation vers l'utilisateur Stoflow
    user_id = Column(Integer, nullable=False, unique=True, index=True)

    # Session data
    session_id = Column(Text, nullable=True)
    csrf_token = Column(Text, nullable=True)
    datadome_cookie = Column(Text, nullable=True)

    # DataDome tracking
    datadome_status = Column(
        Enum(DataDomeStatus, name='datadomestatus', create_type=False),
        nullable=True,
        default=DataDomeStatus.UNKNOWN,
        comment="Current DataDome session status"
    )
    last_datadome_ping = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last successful DataDome ping"
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
        comment="Date de création"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Dernière mise à jour"
    )
    last_synced_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Dernière synchronisation réussie"
    )

    # Seller statistics (from /api/v2/users/current)
    item_count = Column(Integer, nullable=True, comment="Number of items currently for sale")
    total_items_count = Column(Integer, nullable=True, comment="Total items count (including sold)")
    given_item_count = Column(Integer, nullable=True, comment="Number of items sold")
    taken_item_count = Column(Integer, nullable=True, comment="Number of items bought")
    followers_count = Column(Integer, nullable=True, comment="Number of followers")
    feedback_count = Column(Integer, nullable=True, comment="Total feedback/reviews count")
    feedback_reputation = Column(Float, nullable=True, comment="Reputation score (0.0 to 1.0)")
    positive_feedback_count = Column(Integer, nullable=True, comment="Number of positive reviews")
    negative_feedback_count = Column(Integer, nullable=True, comment="Number of negative reviews")
    is_business = Column(Boolean, nullable=True, comment="True if business/pro account")
    is_on_holiday = Column(Boolean, nullable=True, comment="True if holiday mode is enabled")
    stats_updated_at = Column(DateTime(timezone=True), nullable=True, comment="Timestamp of last stats update")

    def __repr__(self):
        status = "connected" if self.is_connected else "disconnected"
        return f"<VintedConnection(id={self.id}, username='{self.username}', {status})>"

    def connect(self) -> None:
        """Marque la connexion comme active."""
        self.is_connected = True
        self.last_synced_at = datetime.now(timezone.utc)

    def disconnect(self) -> None:
        """Marque la connexion comme inactive."""
        self.is_connected = False

    def update_datadome_status(self, success: bool) -> None:
        """Update DataDome ping status."""
        if success:
            self.last_datadome_ping = datetime.now(timezone.utc)
            self.datadome_status = DataDomeStatus.OK
        else:
            self.datadome_status = DataDomeStatus.FAILED

    def needs_datadome_ping(self, interval_seconds: int = 300) -> bool:
        """Check if DataDome needs to be pinged (default: 5 minutes)."""
        if self.last_datadome_ping is None:
            return True
        elapsed = (datetime.now(timezone.utc) - self.last_datadome_ping).total_seconds()
        return elapsed >= interval_seconds

    def update_seller_stats(self, stats: dict) -> None:
        """
        Update seller statistics from Vinted API /api/v2/users/current response.

        Args:
            stats: Dictionary with stats from Vinted API user object
        """
        self.item_count = stats.get("item_count")
        self.total_items_count = stats.get("total_items_count")
        self.given_item_count = stats.get("given_item_count")
        self.taken_item_count = stats.get("taken_item_count")
        self.followers_count = stats.get("followers_count")
        self.feedback_count = stats.get("feedback_count")
        self.feedback_reputation = stats.get("feedback_reputation")
        self.positive_feedback_count = stats.get("positive_feedback_count")
        self.negative_feedback_count = stats.get("negative_feedback_count")
        self.is_business = stats.get("business")
        self.is_on_holiday = stats.get("is_on_holiday")
        self.stats_updated_at = datetime.now(timezone.utc)
