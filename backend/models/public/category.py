"""
Category Model

Table pour les catégories de produits avec hiérarchie parent-enfant (schema public, multilingue).
"""

from typing import List
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class Category(Base):
    """
    Modèle pour les catégories de produits avec hiérarchie.

    Business Rules (2025-12-04, Updated 2025-12-17):
    - Catégories partagées entre tous les tenants (schema public)
    - Nom en anglais (name_en) est la clé primaire
    - Hiérarchie parent-enfant (self-referencing FK)
    - Traductions optionnelles (FR, DE, IT, ES)
    - genders: Liste des genres disponibles (men, women, boys, girls)
    - Ex: Clothing (parent) -> Jeans (child)
    """

    __tablename__ = "categories"
    __table_args__ = {"schema": "product_attributes"}

    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Nom de la catégorie (EN)"
    )
    parent_category: Mapped[str | None] = mapped_column(
        String(100),
        ForeignKey(
            "product_attributes.categories.name_en",
            onupdate="CASCADE",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True,
        comment="Catégorie parente (self-reference)"
    )
    name_fr: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Nom de la catégorie (FR)"
    )
    name_de: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Nom de la catégorie (DE)"
    )
    name_it: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Nom de la catégorie (IT)"
    )
    name_es: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Nom de la catégorie (ES)"
    )
    genders: Mapped[List[str] | None] = mapped_column(
        ARRAY(String(20)),
        nullable=True,
        comment="Available genders for this category (men, women, boys, girls)"
    )

    # Relationships
    parent: Mapped["Category | None"] = relationship(
        "Category",
        remote_side=[name_en],
        back_populates="children",
        foreign_keys=[parent_category]
    )
    children: Mapped[list["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan"
    )

    def is_parent(self) -> bool:
        """Vérifie si cette catégorie est une catégorie parente (pas de parent)."""
        return self.parent_category is None

    def is_child(self) -> bool:
        """Vérifie si cette catégorie est une catégorie enfant (a un parent)."""
        return self.parent_category is not None

    def get_full_path(self, max_depth: int = 10) -> str:
        """
        Retourne le chemin complet de la catégorie avec protection contre boucles.

        Business Rules (2025-12-05):
        - Protection contre références circulaires
        - Limite de profondeur configurable (défaut: 10 niveaux)
        - Format: "Parent > Enfant > Petit-enfant"

        Args:
            max_depth: Profondeur maximale de la hiérarchie (défaut: 10)

        Returns:
            str: Chemin complet de la catégorie

        Raises:
            ValueError: Si boucle circulaire détectée

        Example:
            >>> category = Category(name_en="Skinny Jeans")
            >>> category.get_full_path()
            "Clothing > Jeans > Skinny Jeans"
        """
        path = [self.name_en]
        current = self
        visited = {self.name_en}  # Track visited nodes to detect cycles

        depth = 0
        while current.parent_category and depth < max_depth:
            # Circular reference detection
            if current.parent_category in visited:
                raise ValueError(
                    f"Circular reference detected in category hierarchy: "
                    f"{' > '.join(path)} > {current.parent_category}"
                )

            visited.add(current.parent_category)
            path.append(current.parent_category)
            current = current.parent
            depth += 1

        if depth >= max_depth:
            raise ValueError(
                f"Category hierarchy too deep (>{max_depth} levels): "
                f"{' > '.join(path)}"
            )

        return " > ".join(reversed(path))

    def get_depth(self, max_depth: int = 10) -> int:
        """
        Retourne la profondeur de la catégorie dans la hiérarchie.

        Args:
            max_depth: Profondeur maximale autorisée (protection contre boucles)

        Returns:
            int: Profondeur (0 = racine, 1 = niveau 1, etc.)

        Raises:
            ValueError: Si boucle circulaire détectée ou profondeur excessive

        Example:
            >>> root = Category(name_en="Clothing", parent_category=None)
            >>> root.get_depth()
            0
            >>> child = Category(name_en="Jeans", parent_category="Clothing")
            >>> child.get_depth()
            1
        """
        depth = 0
        current = self
        visited = {self.name_en}

        while current.parent_category and depth < max_depth:
            if current.parent_category in visited:
                raise ValueError(
                    f"Circular reference detected at depth {depth}"
                )

            visited.add(current.parent_category)
            current = current.parent
            depth += 1

        if depth >= max_depth:
            raise ValueError(f"Category hierarchy exceeds max depth: {max_depth}")

        return depth

    def is_gender_available(self, gender: str) -> bool:
        """
        Check if a gender is available for this category.

        Args:
            gender: Gender to check (men, women, boys, girls)

        Returns:
            bool: True if gender is available, False otherwise

        Example:
            >>> category = Category(name_en="skirt", genders=["women", "girls"])
            >>> category.is_gender_available("women")
            True
            >>> category.is_gender_available("men")
            False
        """
        if not self.genders:
            return True  # If no genders specified, assume all are available
        return gender.lower() in [g.lower() for g in self.genders]

    def __repr__(self) -> str:
        return f"<Category(name_en='{self.name_en}', parent='{self.parent_category}', genders={self.genders})>"
