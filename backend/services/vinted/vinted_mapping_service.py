"""
Vinted Mapping Service

Service de mapping des attributs Product → IDs Vinted.
Responsabilité: Traduction attributs internes vers IDs marketplace Vinted.

Business Rules (2024-12-10, Updated 2025-12-18):
- Brand: mapping via brand.vinted_id
- Color: mapping via color.vinted_id
- Condition: mapping via condition.vinted_id
- Size: mapping via size.vinted_{woman|man_top|man_bottom}_id selon genre et catégorie
- Category: mapping via CategoryMappingRepository (table category_platform_mappings)
- Material: mapping via material.vinted_id (for item_attributes)

Architecture:
- Accès direct aux tables product_attributes (shared entre tenants)
- CategoryMappingRepository pour le mapping catégorie multi-plateformes
- Logs d'erreurs si attribut non mappé
- Gestion spécifique du genre (woman vs man) pour les tailles

Created: 2024-12-10
Updated: 2025-12-18 - Ajout map_material pour item_attributes
Author: Claude
"""

from typing import Optional, Dict, Any, Tuple, List
from sqlalchemy.orm import Session

from models.public.brand import Brand
from models.public.color import Color
from models.public.condition import Condition
from models.public.material import Material
from models.public.size import Size
from repositories.category_mapping_repository import CategoryMappingRepository


class VintedMappingService:
    """
    Service de mapping attributs → IDs Vinted.
    
    Mappe les attributs internes du produit vers les IDs requis par l'API Vinted.
    """

    @staticmethod
    def map_brand(db: Session, brand_name: Optional[str]) -> Optional[int]:
        """
        Mappe une marque vers son ID Vinted.

        Args:
            db: Session SQLAlchemy
            brand_name: Nom de la marque (ex: "Levi's")

        Returns:
            ID Vinted de la marque, ou None si non trouvée

        Examples:
            >>> brand_id = VintedMappingService.map_brand(db, "Levi's")
            >>> print(brand_id)  # Ex: 53
            53
        """
        if not brand_name:
            return None

        brand = db.query(Brand).filter(Brand.name == brand_name).first()

        if brand and brand.vinted_id:
            return int(brand.vinted_id)

        return None

    @staticmethod
    def map_color(db: Session, color_name: Optional[str]) -> Optional[int]:
        """
        Mappe une couleur vers son ID Vinted.

        Args:
            db: Session SQLAlchemy
            color_name: Nom de la couleur en anglais (ex: "Blue")

        Returns:
            ID Vinted de la couleur, ou None si non trouvée

        Examples:
            >>> color_id = VintedMappingService.map_color(db, "Blue")
            >>> print(color_id)  # Ex: 12
            12
        """
        if not color_name:
            return None

        color = db.query(Color).filter(Color.name_en == color_name).first()

        if color and color.vinted_id:
            return int(color.vinted_id)

        return None

    @staticmethod
    def map_condition(db: Session, condition_name: Optional[str]) -> Optional[int]:
        """
        Mappe un état/condition vers son ID Vinted.

        Args:
            db: Session SQLAlchemy
            condition_name: Nom de la condition (ex: "EXCELLENT", "GOOD")

        Returns:
            ID Vinted de la condition, ou None si non trouvée

        Examples:
            >>> condition_id = VintedMappingService.map_condition(db, "EXCELLENT")
            >>> print(condition_id)  # Ex: 1 (NEW)
            1
        """
        if not condition_name:
            return None

        condition = db.query(Condition).filter(Condition.name == condition_name).first()

        if condition and condition.vinted_id:
            return int(condition.vinted_id)

        return None

    @staticmethod
    def map_material(db: Session, material_name: Optional[str]) -> Optional[int]:
        """
        Mappe une matière vers son ID Vinted.

        Args:
            db: Session SQLAlchemy
            material_name: Nom de la matière en anglais (ex: "Cotton", "Denim")

        Returns:
            ID Vinted de la matière, ou None si non trouvée

        Examples:
            >>> material_id = VintedMappingService.map_material(db, "Cotton")
            >>> print(material_id)  # Ex: 44
            44
        """
        if not material_name:
            return None

        material = db.query(Material).filter(Material.name_en == material_name).first()

        if material and material.vinted_id:
            return int(material.vinted_id)

        return None

    @staticmethod
    def map_materials(db: Session, material_names: List[str]) -> List[int]:
        """
        Mappe une liste de matières vers leurs IDs Vinted.

        Vinted supporte jusqu'à 3 matières par produit.

        Args:
            db: Session SQLAlchemy
            material_names: Liste de noms de matières

        Returns:
            Liste d'IDs Vinted (max 3, dédupliqués)

        Examples:
            >>> material_ids = VintedMappingService.map_materials(db, ["Cotton", "Polyester"])
            >>> print(material_ids)  # Ex: [44, 45]
            [44, 45]
        """
        if not material_names:
            return []

        material_ids = []
        for name in material_names[:3]:  # Vinted limit: 3 materials
            material_id = VintedMappingService.map_material(db, name)
            if material_id and material_id not in material_ids:
                material_ids.append(material_id)

        return material_ids

    @staticmethod
    def map_size(
        db: Session,
        size_name: Optional[str],
        gender: str,
        parent_category: str
    ) -> Optional[int]:
        """
        Mappe une taille vers son ID Vinted selon le genre et le type.

        Business Rules:
        - Femme: utilise vinted_woman_id
        - Homme Bottom (Jeans, Pants, Shorts): utilise vinted_man_bottom_id
        - Homme Top (autres): utilise vinted_man_top_id

        Args:
            db: Session SQLAlchemy
            size_name: Nom de la taille (ex: "M", "32", "L")
            gender: Genre du produit (ex: "male", "female")
            parent_category: Catégorie parente (ex: "Jeans", "Jacket")

        Returns:
            ID Vinted de la taille, ou None si non trouvée

        Examples:
            >>> size_id = VintedMappingService.map_size(db, "32", "male", "Jeans")
            >>> print(size_id)  # Ex: 207 (W32 men bottom)
            207

            >>> size_id = VintedMappingService.map_size(db, "M", "female", "T-shirt")
            >>> print(size_id)  # Ex: 206 (M women)
            206
        """
        if not size_name:
            return None

        size = db.query(Size).filter(Size.name == size_name).first()

        if not size:
            return None

        # Déterminer si c'est un produit femme
        is_woman = gender.lower() in ['female', 'woman', 'femme', 'women']

        if is_woman:
            # Femme: utiliser vinted_woman_id
            if size.vinted_woman_id:
                return int(size.vinted_woman_id)
        else:
            # Homme: déterminer si c'est un bas (bottom) ou haut (top)
            is_bottom = VintedMappingService._is_bottom_category(parent_category)

            if is_bottom:
                # Bas homme: pantalon, jean, short
                if size.vinted_man_bottom_id:
                    return int(size.vinted_man_bottom_id)
            else:
                # Haut homme: veste, t-shirt, sweat, etc.
                if size.vinted_man_top_id:
                    return int(size.vinted_man_top_id)

        return None

    @staticmethod
    def map_category(
        db: Session,
        category: str,
        gender: str,
        fit: Optional[str] = None
    ) -> Tuple[Optional[int], Optional[str], Optional[str]]:
        """
        Mappe une catégorie vers son ID Vinted via CategoryMappingRepository.

        Uses fallback strategy:
        1. Exact match (category + gender + fit)
        2. No-fit match (category + gender + fit=NULL)
        3. Any fit match (category + gender, first found)

        Args:
            db: Session SQLAlchemy
            category: Nom de la catégorie (EN), ex: "Jeans"
            gender: Genre du produit, ex: "Men", "Women"
            fit: Coupe du produit (optionnel), ex: "Slim", "Regular"

        Returns:
            Tuple (category_id, category_name, category_path):
            - category_id: ID Vinted catalog_id, ou None si non trouvé
            - category_name: Nom de la catégorie Vinted
            - category_path: Chemin de la catégorie (ex: "Hommes > Jeans > Slim")

        Examples:
            >>> cat_id, name, path = VintedMappingService.map_category(db, "Jeans", "Men", "Slim")
            >>> print(cat_id)  # Ex: 89
            89
            >>> print(path)
            'Hommes > Jeans > Slim'
        """
        repo = CategoryMappingRepository(db)

        # Normalize gender to match DB values
        gender_normalized = VintedMappingService._normalize_gender(gender)

        mapping = repo.get_vinted_mapping(category, gender_normalized, fit)

        if mapping:
            return mapping['id'], mapping['name'], mapping['path']

        return None, None, None

    @staticmethod
    def _normalize_gender(gender: str) -> str:
        """
        Normalize gender string to match DB values.

        Args:
            gender: Input gender string

        Returns:
            Normalized gender: "Men" or "Women"

        Examples:
            >>> VintedMappingService._normalize_gender("male")
            'Men'
            >>> VintedMappingService._normalize_gender("female")
            'Women'
        """
        gender_lower = gender.lower() if gender else ''

        if gender_lower in ['male', 'man', 'men', 'homme', 'hommes', 'boy', 'boys']:
            return 'Men'
        elif gender_lower in ['female', 'woman', 'women', 'femme', 'femmes', 'girl', 'girls']:
            return 'Women'
        else:
            # Default to Men for unisex or unknown
            return 'Men'

    @staticmethod
    def _is_bottom_category(parent_category: str) -> bool:
        """
        Détermine si une catégorie parente est un bas (pantalon, jupe, etc.).

        Args:
            parent_category: Nom de la catégorie parente (en anglais)

        Returns:
            True si c'est un bas, False sinon

        Examples:
            >>> VintedMappingService._is_bottom_category("Jeans")
            True

            >>> VintedMappingService._is_bottom_category("Jacket")
            False
        """
        bottom_categories = ['Pants', 'Shorts', 'Skirt', 'Jeans']
        return parent_category in bottom_categories

    @staticmethod
    def map_all_attributes(db: Session, product) -> Dict[str, Any]:
        """
        Mappe tous les attributs d'un produit vers leurs IDs Vinted.

        Args:
            db: Session SQLAlchemy
            product: Instance de Product

        Returns:
            Dictionnaire avec tous les attributs mappés:
            {
                'brand_id': int | None,
                'color_id': int | None,
                'condition_id': int | None,
                'size_id': int | None,
                'category_id': int | None,
                'category_name': str | None,
                'category_path': str | None,
                'gender': str,
                'is_bottom': bool,
                'material_ids': list[int]  # For item_attributes
            }

        Examples:
            >>> mapped = VintedMappingService.map_all_attributes(db, product)
            >>> print(mapped)
            {
                'brand_id': 53,
                'color_id': 12,
                'condition_id': 1,
                'size_id': 207,
                'category_id': 89,
                'category_name': 'Jean slim',
                'category_path': 'Hommes > Jeans > Slim',
                'gender': 'male',
                'is_bottom': True,
                'material_ids': [303]  # Denim
            }
        """
        # Déterminer genre et catégorie parente
        gender = product.gender or 'unisex'
        parent_category = product.category.parent_category if hasattr(product, 'category') and hasattr(product.category, 'parent_category') else product.category

        # Mapping catégorie via CategoryMappingRepository
        category_name = product.category if isinstance(product.category, str) else (product.category.name_en if hasattr(product.category, 'name_en') else str(product.category))
        fit = getattr(product, 'fit', None)

        category_id, vinted_category_name, category_path = VintedMappingService.map_category(
            db,
            category_name,
            gender,
            fit
        )

        # Mapping taille
        size_id = VintedMappingService.map_size(
            db,
            product.size,
            gender,
            parent_category
        )

        # Mapping material(s) - support single string or list
        material = getattr(product, 'material', None)
        material_ids = []
        if material:
            if isinstance(material, list):
                material_ids = VintedMappingService.map_materials(db, material)
            else:
                material_id = VintedMappingService.map_material(db, material)
                if material_id:
                    material_ids = [material_id]

        return {
            'brand_id': VintedMappingService.map_brand(db, product.brand),
            'color_id': VintedMappingService.map_color(db, product.color),
            'condition_id': VintedMappingService.map_condition(db, product.condition),
            'size_id': size_id,
            'category_id': category_id,
            'category_name': vinted_category_name,
            'category_path': category_path,
            'gender': gender,
            'is_bottom': VintedMappingService._is_bottom_category(parent_category),
            'material_ids': material_ids
        }
