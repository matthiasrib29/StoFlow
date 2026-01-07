"""
Product Attribute Repository

Repository pour la gestion des attributs produits (schema product_attributes).
Centralise l'accès aux tables d'attributs partagés.

Tables gérées:
- brands
- categories
- colors
- conditions
- fits
- genders
- materials
- seasons
- sizes

Created: 2026-01-06
Author: Claude
"""

from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.public.brand import Brand
from models.public.category import Category
from models.public.color import Color
from models.public.condition import Condition
from models.public.fit import Fit
from models.public.gender import Gender
from models.public.material import Material
from models.public.season import Season
from models.public.size_normalized import SizeNormalized
from models.public.stretch import Stretch
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class ProductAttributeRepository:
    """
    Repository pour la gestion des attributs produits.

    Fournit des méthodes pour accéder aux tables d'attributs partagés
    (brands, colors, sizes, etc.) dans le schema product_attributes.
    """

    # =========================================================================
    # BRAND
    # =========================================================================

    @staticmethod
    def get_brand_by_name(db: Session, name: str) -> Optional[Brand]:
        """
        Récupère une Brand par son nom.

        Args:
            db: Session SQLAlchemy
            name: Nom de la marque

        Returns:
            Brand si trouvée, None sinon
        """
        return db.query(Brand).filter(Brand.name == name).first()

    @staticmethod
    def get_brand_by_id(db: Session, brand_id: int) -> Optional[Brand]:
        """
        Récupère une Brand par son ID.

        Args:
            db: Session SQLAlchemy
            brand_id: ID de la marque

        Returns:
            Brand si trouvée, None sinon
        """
        return db.query(Brand).filter(Brand.id == brand_id).first()

    @staticmethod
    def get_or_create_brand(db: Session, name: str) -> Brand:
        """
        Récupère ou crée une Brand.

        Args:
            db: Session SQLAlchemy
            name: Nom de la marque

        Returns:
            Brand existante ou nouvellement créée
        """
        brand = ProductAttributeRepository.get_brand_by_name(db, name)
        if not brand:
            brand = Brand(name=name)
            db.add(brand)
            db.flush()
            logger.info(f"[ProductAttributeRepository] Brand created: {name}")
        return brand

    @staticmethod
    def list_brands(db: Session, limit: int = 500) -> List[Brand]:
        """
        Liste toutes les marques.

        Args:
            db: Session SQLAlchemy
            limit: Nombre max de résultats

        Returns:
            Liste de Brand
        """
        return db.query(Brand).order_by(Brand.name).limit(limit).all()

    @staticmethod
    def search_brands(db: Session, query: str, limit: int = 50) -> List[Brand]:
        """
        Recherche des marques par nom.

        Args:
            db: Session SQLAlchemy
            query: Terme de recherche
            limit: Nombre max de résultats

        Returns:
            Liste de Brand correspondantes
        """
        return (
            db.query(Brand)
            .filter(Brand.name.ilike(f"%{query}%"))
            .order_by(Brand.name)
            .limit(limit)
            .all()
        )

    # =========================================================================
    # SIZE NORMALIZED
    # =========================================================================

    @staticmethod
    def get_size_normalized_by_name(db: Session, name_en: str) -> Optional[SizeNormalized]:
        """
        Récupère une SizeNormalized par son nom anglais.

        Args:
            db: Session SQLAlchemy
            name_en: Nom anglais de la taille

        Returns:
            SizeNormalized si trouvée, None sinon
        """
        return db.query(SizeNormalized).filter(SizeNormalized.name_en == name_en).first()

    @staticmethod
    def list_sizes_normalized(db: Session, limit: int = 200) -> List[SizeNormalized]:
        """
        Liste toutes les tailles normalisées.

        Args:
            db: Session SQLAlchemy
            limit: Nombre max de résultats

        Returns:
            Liste de SizeNormalized
        """
        return db.query(SizeNormalized).order_by(SizeNormalized.name_en).limit(limit).all()

    # =========================================================================
    # COLOR
    # =========================================================================

    @staticmethod
    def get_color_by_name(db: Session, name_en: str) -> Optional[Color]:
        """
        Récupère une Color par son nom anglais.

        Args:
            db: Session SQLAlchemy
            name_en: Nom anglais de la couleur

        Returns:
            Color si trouvée, None sinon
        """
        return db.query(Color).filter(Color.name_en == name_en).first()

    @staticmethod
    def list_colors(db: Session, limit: int = 100) -> List[Color]:
        """
        Liste toutes les couleurs.

        Args:
            db: Session SQLAlchemy
            limit: Nombre max de résultats

        Returns:
            Liste de Color
        """
        return db.query(Color).order_by(Color.name_en).limit(limit).all()

    # =========================================================================
    # CONDITION
    # =========================================================================

    @staticmethod
    def get_condition_by_name(db: Session, name_en: str) -> Optional[Condition]:
        """
        Récupère une Condition par son nom anglais.

        Args:
            db: Session SQLAlchemy
            name_en: Nom anglais de la condition

        Returns:
            Condition si trouvée, None sinon
        """
        return db.query(Condition).filter(Condition.name_en == name_en).first()

    @staticmethod
    def list_conditions(db: Session) -> List[Condition]:
        """
        Liste toutes les conditions.

        Args:
            db: Session SQLAlchemy

        Returns:
            Liste de Condition
        """
        return db.query(Condition).order_by(Condition.name_en).all()

    # =========================================================================
    # MATERIAL
    # =========================================================================

    @staticmethod
    def get_material_by_name(db: Session, name_en: str) -> Optional[Material]:
        """
        Récupère un Material par son nom anglais.

        Args:
            db: Session SQLAlchemy
            name_en: Nom anglais du matériau

        Returns:
            Material si trouvé, None sinon
        """
        return db.query(Material).filter(Material.name_en == name_en).first()

    @staticmethod
    def list_materials(db: Session, limit: int = 200) -> List[Material]:
        """
        Liste tous les matériaux.

        Args:
            db: Session SQLAlchemy
            limit: Nombre max de résultats

        Returns:
            Liste de Material
        """
        return db.query(Material).order_by(Material.name_en).limit(limit).all()

    # =========================================================================
    # CATEGORY
    # =========================================================================

    @staticmethod
    def get_category_by_name(db: Session, name_en: str) -> Optional[Category]:
        """
        Récupère une Category par son nom anglais.

        Args:
            db: Session SQLAlchemy
            name_en: Nom anglais de la catégorie

        Returns:
            Category si trouvée, None sinon
        """
        return db.query(Category).filter(Category.name_en == name_en).first()

    @staticmethod
    def list_categories(db: Session, limit: int = 500) -> List[Category]:
        """
        Liste toutes les catégories.

        Args:
            db: Session SQLAlchemy
            limit: Nombre max de résultats

        Returns:
            Liste de Category
        """
        return db.query(Category).order_by(Category.name_en).limit(limit).all()

    @staticmethod
    def search_categories(db: Session, query: str, limit: int = 50) -> List[Category]:
        """
        Recherche des catégories par nom.

        Args:
            db: Session SQLAlchemy
            query: Terme de recherche
            limit: Nombre max de résultats

        Returns:
            Liste de Category correspondantes
        """
        return (
            db.query(Category)
            .filter(Category.name_en.ilike(f"%{query}%"))
            .order_by(Category.name_en)
            .limit(limit)
            .all()
        )

    # =========================================================================
    # FIT
    # =========================================================================

    @staticmethod
    def get_fit_by_name(db: Session, name_en: str) -> Optional[Fit]:
        """
        Récupère un Fit par son nom anglais.

        Args:
            db: Session SQLAlchemy
            name_en: Nom anglais du fit

        Returns:
            Fit si trouvé, None sinon
        """
        return db.query(Fit).filter(Fit.name_en == name_en).first()

    @staticmethod
    def list_fits(db: Session) -> List[Fit]:
        """
        Liste tous les fits.

        Args:
            db: Session SQLAlchemy

        Returns:
            Liste de Fit
        """
        return db.query(Fit).order_by(Fit.name_en).all()

    # =========================================================================
    # GENDER
    # =========================================================================

    @staticmethod
    def get_gender_by_name(db: Session, name_en: str) -> Optional[Gender]:
        """
        Récupère un Gender par son nom anglais.

        Args:
            db: Session SQLAlchemy
            name_en: Nom anglais du genre

        Returns:
            Gender si trouvé, None sinon
        """
        return db.query(Gender).filter(Gender.name_en == name_en).first()

    @staticmethod
    def list_genders(db: Session) -> List[Gender]:
        """
        Liste tous les genres.

        Args:
            db: Session SQLAlchemy

        Returns:
            Liste de Gender
        """
        return db.query(Gender).order_by(Gender.name_en).all()

    # =========================================================================
    # SEASON
    # =========================================================================

    @staticmethod
    def get_season_by_name(db: Session, name_en: str) -> Optional[Season]:
        """
        Récupère une Season par son nom anglais.

        Args:
            db: Session SQLAlchemy
            name_en: Nom anglais de la saison

        Returns:
            Season si trouvée, None sinon
        """
        return db.query(Season).filter(Season.name_en == name_en).first()

    @staticmethod
    def list_seasons(db: Session) -> List[Season]:
        """
        Liste toutes les saisons.

        Args:
            db: Session SQLAlchemy

        Returns:
            Liste de Season
        """
        return db.query(Season).order_by(Season.name_en).all()

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    @staticmethod
    def get_attributes(
        db: Session,
        brand: Optional[str] = None,
        color: Optional[str] = None,
        condition: Optional[str] = None,
        material: Optional[str] = None,
        size: Optional[str] = None,
        category: Optional[str] = None,
        fit: Optional[str] = None,
        gender: Optional[str] = None,
        season: Optional[str] = None,
    ) -> dict:
        """
        Récupère plusieurs attributs en une seule requête.

        Args:
            db: Session SQLAlchemy
            brand: Nom de la marque
            color: Nom de la couleur
            condition: Nom de la condition
            material: Nom du matériau
            size: Nom de la taille
            category: Nom de la catégorie
            fit: Nom du fit
            gender: Nom du genre
            season: Nom de la saison

        Returns:
            dict: {attr_name: attr_object or None}
        """
        result = {}

        if brand:
            result["brand"] = ProductAttributeRepository.get_brand_by_name(db, brand)
        if color:
            result["color"] = ProductAttributeRepository.get_color_by_name(db, color)
        if condition:
            result["condition"] = ProductAttributeRepository.get_condition_by_name(
                db, condition
            )
        if material:
            result["material"] = ProductAttributeRepository.get_material_by_name(
                db, material
            )
        if size:
            result["size"] = ProductAttributeRepository.get_size_normalized_by_name(db, size)
        if category:
            result["category"] = ProductAttributeRepository.get_category_by_name(
                db, category
            )
        if fit:
            result["fit"] = ProductAttributeRepository.get_fit_by_name(db, fit)
        if gender:
            result["gender"] = ProductAttributeRepository.get_gender_by_name(db, gender)
        if season:
            result["season"] = ProductAttributeRepository.get_season_by_name(db, season)

        return result

    # =========================================================================
    # STRETCH
    # =========================================================================

    @staticmethod
    def get_stretch_by_name(db: Session, name_en: str) -> Optional[Stretch]:
        """
        Récupère un Stretch par son nom anglais.

        Args:
            db: Session SQLAlchemy
            name_en: Nom anglais du stretch

        Returns:
            Stretch si trouvé, None sinon
        """
        return db.query(Stretch).filter(Stretch.name_en == name_en).first()

    @staticmethod
    def list_stretches(db: Session, limit: int = 100) -> List[Stretch]:
        """
        Liste tous les stretches.

        Args:
            db: Session SQLAlchemy
            limit: Nombre maximum de résultats

        Returns:
            Liste des Stretch objects
        """
        return db.query(Stretch).order_by(Stretch.name_en).limit(limit).all()

    # =========================================================================
    # UTILITIES
    # =========================================================================

    @staticmethod
    def attribute_exists(db: Session, attr_type: str, value: str) -> bool:
        """
        Vérifie si un attribut existe.

        Args:
            db: Session SQLAlchemy
            attr_type: Type d'attribut (brand, color, condition, etc.)
            value: Valeur à vérifier

        Returns:
            bool: True si l'attribut existe
        """
        attr_getters = {
            "brand": ProductAttributeRepository.get_brand_by_name,
            "color": ProductAttributeRepository.get_color_by_name,
            "condition": ProductAttributeRepository.get_condition_by_name,
            "material": ProductAttributeRepository.get_material_by_name,
            "size": ProductAttributeRepository.get_size_normalized_by_name,
            "category": ProductAttributeRepository.get_category_by_name,
            "fit": ProductAttributeRepository.get_fit_by_name,
            "gender": ProductAttributeRepository.get_gender_by_name,
            "season": ProductAttributeRepository.get_season_by_name,
        }

        getter = attr_getters.get(attr_type.lower())
        if not getter:
            return False

        return getter(db, value) is not None


__all__ = ["ProductAttributeRepository"]
