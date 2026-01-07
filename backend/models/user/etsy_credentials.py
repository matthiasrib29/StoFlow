"""
EtsyCredentials Model - Schema user_{id}

Stocke les credentials OAuth2 et informations du compte Etsy de l'utilisateur.

Business Rules:
- Un user = un compte Etsy
- OAuth2 avec access_token (expire 1h) et refresh_token (expire 90 jours)
- Le backend gère le refresh automatique des tokens
- Tokens stockés de manière sécurisée dans le schema utilisateur

Author: Claude
Date: 2026-01-07
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class EtsyCredentials(Base):
    """
    Modèle EtsyCredentials - Credentials OAuth2 et informations du compte Etsy.

    Attributes:
        # Identifiants
        id: Identifiant unique (PK)

        # OAuth2 Tokens
        access_token: Token d'accès OAuth2 (expire 1h)
        refresh_token: Token de rafraîchissement OAuth2 (expire 90 jours)
        access_token_expires_at: Date d'expiration du access_token
        refresh_token_expires_at: Date d'expiration du refresh_token

        # Etsy Shop Info
        shop_id: ID du shop Etsy
        shop_name: Nom du shop
        shop_url: URL du shop sur Etsy

        # Account Info
        user_id_etsy: ID utilisateur Etsy (préfixe du token)
        email: Email du compte Etsy

        # Status
        is_connected: True si les credentials sont valides
        last_sync: Dernière synchronisation réussie

        # Timestamps
        created_at: Date de création
        updated_at: Date de dernière modification
    """

    __tablename__ = "etsy_credentials"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # OAuth2 Tokens
    access_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="OAuth2 Access Token (expire 1h)"
    )
    refresh_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="OAuth2 Refresh Token (expire 90 jours)"
    )

    # Token Expiration
    access_token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date d'expiration du access_token"
    )
    refresh_token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date d'expiration du refresh_token"
    )

    # Etsy Shop Info
    shop_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="ID du shop Etsy"
    )
    shop_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Nom du shop Etsy"
    )
    shop_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="URL du shop sur Etsy"
    )

    # Account Info
    user_id_etsy: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="ID utilisateur Etsy (préfixe du token)"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Email du compte Etsy"
    )

    # Status
    is_connected: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True si les credentials sont valides"
    )
    last_sync: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Dernière synchronisation réussie"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<EtsyCredentials(id={self.id}, "
            f"shop_id='{self.shop_id}', "
            f"is_connected={self.is_connected})>"
        )

    @property
    def has_valid_tokens(self) -> bool:
        """Vérifie si les tokens OAuth2 sont présents."""
        return bool(self.access_token and self.refresh_token)

    @property
    def is_access_token_expired(self) -> bool:
        """Vérifie si l'access_token est expiré."""
        if not self.access_token_expires_at:
            return True
        return datetime.now(self.access_token_expires_at.tzinfo) > self.access_token_expires_at

    @property
    def is_refresh_token_expired(self) -> bool:
        """Vérifie si le refresh_token est expiré."""
        if not self.refresh_token_expires_at:
            return True
        return datetime.now(self.refresh_token_expires_at.tzinfo) > self.refresh_token_expires_at

    @property
    def needs_refresh(self) -> bool:
        """Vérifie si l'access_token doit être rafraîchi."""
        return self.has_valid_tokens and self.is_access_token_expired and not self.is_refresh_token_expired
