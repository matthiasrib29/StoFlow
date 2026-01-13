"""
Modèle pour la connexion Vinted.

Source de vérité unique pour l'état de connexion Vinted d'un utilisateur.
Les colonnes User.vinted_* ont été supprimées au profit de ce modèle.

Business Rules:
- Un user Stoflow = un compte Vinted max (UniqueConstraint sur user_id)
- is_connected = True si l'utilisateur est connecté à Vinted
- Le plugin détecte les connexions/déconnexions et notifie le backend
- Le frontend peut vérifier via /check-connection (task plugin)

Author: Claude
Date: 2025-12-17
Updated: 2026-01-12 (refactored schema: id as PK, username, last_synced_at)
"""

from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Boolean, Text, Float, Enum
from shared.database import Base


class DataDomeStatus(str, PyEnum):
    """Status of the DataDome session."""
    UNKNOWN = "UNKNOWN"              # Never checked or expired
    OK = "OK"                        # Session is valid (legacy)
    VALID = "VALID"                  # Session is valid
    EXPIRED = "EXPIRED"              # Session has expired
    BLOCKED = "BLOCKED"              # IP/session is blocked
    CAPTCHA_REQUIRED = "CAPTCHA_REQUIRED"  # Captcha needs solving
    FAILED = "FAILED"                # Last check failed


class VintedConnection(Base):
    """
    Table pour stocker la connexion Vinted d'un utilisateur.

    Note: Cette table est dans le schema utilisateur (user_X), pas public.
    Elle est créée à partir de template_tenant lors de la création de l'utilisateur.

    Attributes:
        id: Auto-increment primary key
        user_id: FK vers public.users.id (UNIQUE - 1 connexion par user)
        is_connected: True si actuellement connecté
        vinted_user_id: ID utilisateur Vinted (nullable)
        username: Login/username Vinted
        session_id: Session ID Vinted
        csrf_token: CSRF token pour les requêtes
        datadome_cookie: Cookie DataDome
        datadome_status: Status de la session DataDome
        last_datadome_ping: Dernière vérification DataDome
        created_at: Date de création
        updated_at: Date de mise à jour
        last_synced_at: Dernière synchronisation réussie
    """
    __tablename__ = "vinted_connection"
    __table_args__ = {"schema": "tenant"}  # Placeholder for schema_translate_map

    # Primary key: auto-increment ID
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key vers public.users.id (UNIQUE - 1 connexion par user max)
    user_id = Column(Integer, nullable=False, unique=True, index=True)

    # Connection state
    is_connected = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="True si l'utilisateur est connecté à Vinted"
    )

    # Vinted user info
    vinted_user_id = Column(
        BigInteger,
        nullable=True,
        index=True,
        comment="ID utilisateur sur Vinted"
    )
    username = Column(
        String(255),
        nullable=True,
        index=True,
        comment="Login/username Vinted"
    )

    # Session credentials (managed by plugin)
    session_id = Column(Text, nullable=True, comment="Session ID Vinted")
    csrf_token = Column(Text, nullable=True, comment="CSRF token pour les requêtes")
    datadome_cookie = Column(Text, nullable=True, comment="Cookie DataDome")

    # DataDome tracking
    datadome_status = Column(
        Enum(DataDomeStatus),
        nullable=False,
        default=DataDomeStatus.UNKNOWN,
        comment="Current DataDome session status"
    )
    last_datadome_ping = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last DataDome check"
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

    # Timestamps
    last_synced_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Dernière synchronisation réussie"
    )
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
        comment="Date de mise à jour"
    )

    def __repr__(self):
        status = "connected" if self.is_connected else "disconnected"
        return f"<VintedConnection(id={self.id}, username='{self.username}', {status})>"

    def connect(self, vinted_user_id: int = None, username: str = None) -> None:
        """Marque la connexion comme active."""
        self.is_connected = True
        if vinted_user_id is not None:
            self.vinted_user_id = vinted_user_id
        if username is not None:
            self.username = username
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
