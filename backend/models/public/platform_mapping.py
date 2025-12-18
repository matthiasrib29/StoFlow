"""
PlatformMapping Model - Schema Public

Ce modèle contient les mappings de catégories/attributs entre Stoflow et les plateformes externes.
C'est une table de référence commune à tous les utilisateurs.

Business Rules:
- Table de référence partagée (pas de user_id)
- Platforms supportées: vinted, ebay, etsy
- Utilisée pour mapper les catégories Stoflow vers les catégories des plateformes
- Un mapping peut être actif ou inactif (is_active)
"""

import os
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Platform(str, Enum):
    """Plateformes supportées."""
    VINTED = "vinted"
    EBAY = "ebay"
    ETSY = "etsy"


class PlatformMapping(Base):
    """
    Modèle PlatformMapping - Mappings de catégories/attributs vers plateformes externes.

    Attributes:
        id: Identifiant unique du mapping
        platform: Plateforme cible (vinted, ebay, etsy)
        stoflow_category: Catégorie interne Stoflow
        platform_category: Catégorie de la plateforme externe
        platform_category_id: ID de la catégorie sur la plateforme (si applicable)
        attributes_mapping: JSON avec mappings d'attributs spécifiques
        is_active: Active ou inactive
        created_at: Date de création
        updated_at: Date de dernière modification
    """

    __tablename__ = "platform_mappings"
    __table_args__ = (
        UniqueConstraint("platform", "stoflow_category", name="uq_platform_stoflow_category"),
        {"schema": "public"}
    )

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Business Fields
    platform: Mapped[Platform] = mapped_column(
        SQLEnum(Platform, name="platform_type", create_type=True),
        nullable=False,
        index=True
    )
    stoflow_category: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    platform_category: Mapped[str] = mapped_column(String(255), nullable=False)
    platform_category_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # JSON pour attributs spécifiques (ex: tailles, couleurs, matières)
    attributes_mapping: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

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
            f"<PlatformMapping(id={self.id}, platform={self.platform}, "
            f"stoflow_category='{self.stoflow_category}', "
            f"platform_category='{self.platform_category}')>"
        )
