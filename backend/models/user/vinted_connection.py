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
"""

from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index, Enum
from shared.database import Base


class DataDomeStatus(str, PyEnum):
    """Status of the DataDome session."""
    OK = "OK"                    # Last ping successful
    FAILED = "FAILED"            # Last ping failed (after retries)
    UNKNOWN = "UNKNOWN"          # Never pinged or expired


class VintedConnection(Base):
    """
    Table pour stocker la connexion Vinted d'un utilisateur.

    Attributes:
        vinted_user_id: ID utilisateur Vinted (PK)
        login: Username Vinted
        is_connected: True si actuellement connecté
        created_at: Date de première connexion
        last_sync: Dernière synchronisation réussie
        disconnected_at: Date de dernière déconnexion (null si connecté)
    """
    __tablename__ = "vinted_connection"

    # Primary key: l'ID utilisateur Vinted
    vinted_user_id = Column(Integer, primary_key=True, index=True)

    # Login/username Vinted
    login = Column(String(255), nullable=False, index=True)

    # État de connexion
    is_connected = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="True si l'utilisateur est connecté à Vinted"
    )

    # Relation vers l'utilisateur Stoflow (cross-schema reference, no FK constraint)
    # Note: La table users est dans le schema public, vinted_connection dans user_{id}
    # L'intégrité référentielle est gérée au niveau applicatif
    user_id = Column(Integer, nullable=False, index=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Date de première connexion"
    )
    last_sync = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Dernière synchronisation réussie"
    )
    disconnected_at = Column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="Date de dernière déconnexion (null si connecté)"
    )

    # DataDome tracking
    last_datadome_ping = Column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="Timestamp of last successful DataDome ping"
    )
    datadome_status = Column(
        Enum(DataDomeStatus),
        nullable=False,
        default=DataDomeStatus.UNKNOWN,
        comment="Current DataDome session status"
    )

    def __repr__(self):
        status = "connected" if self.is_connected else "disconnected"
        return f"<VintedConnection(vinted_user_id={self.vinted_user_id}, login='{self.login}', {status})>"

    def connect(self) -> None:
        """Marque la connexion comme active."""
        self.is_connected = True
        self.disconnected_at = None
        self.last_sync = datetime.now(timezone.utc)

    def disconnect(self) -> None:
        """Marque la connexion comme inactive."""
        self.is_connected = False
        self.disconnected_at = datetime.now(timezone.utc)

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


# Index pour recherches fréquentes
Index('ix_vinted_connection_user_id', VintedConnection.user_id)
Index('ix_vinted_connection_is_connected', VintedConnection.is_connected)
