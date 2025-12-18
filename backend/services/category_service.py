"""
Category Service

Service pour gérer les catégories avec validation de hiérarchie.

Business Rules (2025-12-05):
- Empêche les références circulaires
- Limite de profondeur hiérarchique
- Validation avant toute insertion/modification
"""

from typing import Optional

from sqlalchemy.orm import Session

from models.public.category import Category


class CategoryService:
    """Service pour les opérations sur les catégories."""

    MAX_HIERARCHY_DEPTH = 5  # Maximum 5 niveaux de profondeur

    @staticmethod
    def validate_parent_category(
        db: Session, category_name: str, parent_name: Optional[str]
    ) -> None:
        """
        Valide qu'un parent category est valide et ne crée pas de cycle.

        Business Rules:
        - Parent doit exister
        - Pas d'auto-référence (déjà protégé par CHECK constraint)
        - Pas de cycle indirect (A > B > C > A)
        - Profondeur maximale respectée

        Args:
            db: Session SQLAlchemy
            category_name: Nom de la catégorie à valider
            parent_name: Nom du parent (None pour catégorie racine)

        Raises:
            ValueError: Si validation échoue
        """
        # Catégorie racine (pas de parent) → OK
        if not parent_name:
            return

        # Auto-référence (normalement empêchée par CHECK mais on vérifie)
        if category_name == parent_name:
            raise ValueError(
                f"Category '{category_name}' cannot be its own parent"
            )

        # Vérifier que le parent existe
        parent = db.query(Category).filter(Category.name_en == parent_name).first()
        if not parent:
            raise ValueError(f"Parent category '{parent_name}' does not exist")

        # Vérifier que le parent n'aurait pas category_name dans SES parents
        # (empêche cycle indirect: A > B, puis B > A)
        try:
            parent_path = parent.get_full_path(max_depth=CategoryService.MAX_HIERARCHY_DEPTH)

            if category_name in parent_path:
                raise ValueError(
                    f"Circular reference detected: '{category_name}' is already "
                    f"an ancestor of '{parent_name}' ({parent_path})"
                )
        except ValueError as e:
            # Si le parent lui-même a un problème de cycle
            raise ValueError(
                f"Cannot set parent '{parent_name}': {str(e)}"
            )

        # Vérifier que la profondeur ne dépasse pas la limite
        try:
            parent_depth = parent.get_depth(max_depth=CategoryService.MAX_HIERARCHY_DEPTH)

            if parent_depth + 1 >= CategoryService.MAX_HIERARCHY_DEPTH:
                raise ValueError(
                    f"Cannot add category: would exceed maximum hierarchy depth "
                    f"({CategoryService.MAX_HIERARCHY_DEPTH} levels). "
                    f"Parent '{parent_name}' is already at depth {parent_depth}."
                )
        except ValueError as e:
            raise ValueError(
                f"Cannot validate parent depth: {str(e)}"
            )

    @staticmethod
    def create_category(
        db: Session,
        name_en: str,
        parent_category: Optional[str] = None,
        name_fr: Optional[str] = None,
        name_de: Optional[str] = None,
        name_it: Optional[str] = None,
        name_es: Optional[str] = None,
    ) -> Category:
        """
        Crée une nouvelle catégorie avec validation de hiérarchie.

        Args:
            db: Session SQLAlchemy
            name_en: Nom en anglais (clé primaire)
            parent_category: Nom du parent (optionnel)
            name_fr: Nom en français (optionnel)
            name_de: Nom en allemand (optionnel)
            name_it: Nom en italien (optionnel)
            name_es: Nom en espagnol (optionnel)

        Returns:
            Category: La catégorie créée

        Raises:
            ValueError: Si validation échoue
        """
        # Valider le parent
        CategoryService.validate_parent_category(db, name_en, parent_category)

        # Créer la catégorie
        category = Category(
            name_en=name_en,
            parent_category=parent_category,
            name_fr=name_fr,
            name_de=name_de,
            name_it=name_it,
            name_es=name_es,
        )

        db.add(category)
        db.commit()
        db.refresh(category)

        return category

    @staticmethod
    def update_category_parent(
        db: Session, category_name: str, new_parent_name: Optional[str]
    ) -> Category:
        """
        Met à jour le parent d'une catégorie avec validation.

        Args:
            db: Session SQLAlchemy
            category_name: Nom de la catégorie à modifier
            new_parent_name: Nouveau parent (None pour catégorie racine)

        Returns:
            Category: La catégorie modifiée

        Raises:
            ValueError: Si validation échoue ou catégorie non trouvée
        """
        category = db.query(Category).filter(Category.name_en == category_name).first()
        if not category:
            raise ValueError(f"Category '{category_name}' not found")

        # Valider le nouveau parent
        CategoryService.validate_parent_category(db, category_name, new_parent_name)

        # Mettre à jour
        category.parent_category = new_parent_name
        db.commit()
        db.refresh(category)

        return category
