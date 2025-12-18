"""
Clothing Price Model

Table pour les prix de base par combinaison brand/category (schema public).

Business Rules (2025-12-08):
- Prix de base utilisé pour calcul automatique
- Formule: prix_final = base_price × coeff_condition × coeff_rarity × coeff_quality
- Prix minimum: 5€, arrondi: 0.50€
- Compatible avec PostEditFlet logic (adjust_price)

Author: Claude
Date: 2025-12-08
"""

import os
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DECIMAL, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class ClothingPrice(Base):
    """
    Modèle pour les prix de base par brand/category.

    Business Rules (2025-12-08):
    - Clé primaire composite: (brand, category)
    - base_price: Prix de base avant application des coefficients
    - Coefficients appliqués depuis d'autres tables (condition, rarity, quality)
    """

    __tablename__ = "clothing_prices"
    __table_args__ = {"schema": "public"}

    # Note: Foreign keys vers product_attributes.brands et product_attributes.categories
    # ont été retirées de la définition SQLAlchemy car ces tables ne sont pas importées
    # dans l'environnement Alembic. Les contraintes existent toujours en base de données.

    # ===== PRIMARY KEY (COMPOSITE) =====
    brand: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
        index=True,
        comment="Marque (FK brands.name)"
    )
    category: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        index=True,
        comment="Catégorie (FK categories.name_en)"
    )

    # ===== PRICING =====
    base_price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
        comment="Prix de base en euros"
    )

    # ===== TIMESTAMP =====
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Date de dernière mise à jour du prix"
    )

    # Note: Les relationships vers Brand et Category ont été retirées car elles causent
    # des problèmes avec Alembic (cross-schema relationships). Les foreign keys restent
    # fonctionnelles pour maintenir l'intégrité référentielle.

    def __repr__(self) -> str:
        return f"<ClothingPrice(brand='{self.brand}', category='{self.category}', base_price={self.base_price})>"
