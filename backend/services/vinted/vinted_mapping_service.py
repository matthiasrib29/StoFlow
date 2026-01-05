"""
Vinted Mapping Service

Service de mapping des attributs Product → IDs Vinted.
Responsabilité: Traduction attributs internes vers IDs marketplace Vinted.

Business Rules (Updated 2026-01-05):
- Brand: mapping via brand.vinted_id
- Color: mapping via color.vinted_id
- Condition: mapping via condition.vinted_id (PK = note integer)
- Size: mapping via size.vinted_women_id / size.vinted_men_id (gender-specific)
- Category: mapping via vinted.mapping table + get_vinted_category() function
- Material: mapping via material.vinted_id

Architecture:
- Accès direct aux tables product_attributes (shared entre tenants)
- Category mapping via VintedMappingRepository (calls PostgreSQL function)

Created: 2024-12-10
Updated: 2026-01-05 - Category mapping restored via VintedMappingRepository
Author: Claude
"""

from typing import Optional, Dict, Any, Tuple, List
from sqlalchemy.orm import Session

from models.public.brand import Brand
from models.public.color import Color
from models.public.condition import Condition
from models.public.material import Material
from models.public.size import Size


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
        Map a color to its Vinted ID.

        Args:
            db: Session SQLAlchemy
            color_name: Color name in English (e.g., "blue", "black")

        Returns:
            Vinted color ID, or None if not found

        Examples:
            >>> VintedMappingService.map_color(db, "black")
            1
            >>> VintedMappingService.map_color(db, "blue")
            9
        """
        if not color_name:
            return None

        color = db.query(Color).filter(Color.name_en == color_name).first()

        if color and color.vinted_id:
            return int(color.vinted_id)

        return None

    @staticmethod
    def map_condition(db: Session, condition_note: Optional[int]) -> Optional[int]:
        """
        Mappe un état/condition Stoflow vers son ID Vinted.

        Args:
            db: Session SQLAlchemy
            condition_note: Note de condition Stoflow (0-10)

        Returns:
            ID Vinted de la condition, ou None si non trouvée

        Examples:
            >>> condition_id = VintedMappingService.map_condition(db, 2)
            >>> print(condition_id)  # Ex: 1 (Vinted ID pour très bon état)
            1
        """
        if condition_note is None:
            return None

        # condition_note is an integer (note 0-10)
        condition = db.query(Condition).filter(Condition.note == condition_note).first()

        if condition and condition.vinted_id:
            return int(condition.vinted_id)

        return None

    @staticmethod
    def reverse_map_condition(db: Session, vinted_condition_id: Optional[int]) -> Optional[int]:
        """
        Mappe un ID condition Vinted vers une note Stoflow (reverse lookup).

        Args:
            db: Session SQLAlchemy
            vinted_condition_id: ID Vinted de la condition (1-5)

        Returns:
            Note Stoflow (0-10), ou None si non trouvée

        Examples:
            >>> note = VintedMappingService.reverse_map_condition(db, 2)
            >>> print(note)  # Ex: 2 (très bon état)
            2
        """
        if vinted_condition_id is None:
            return None

        condition = db.query(Condition).filter(
            Condition.vinted_id == vinted_condition_id
        ).first()

        if condition:
            return condition.note

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
        Map a size to its Vinted ID based on gender.

        Vinted uses different size IDs for women vs men. This method
        returns the appropriate ID based on the product's gender.

        Args:
            db: Session SQLAlchemy
            size_name: Size name (e.g., "M", "W32/L30", "L")
            gender: Product gender (e.g., "men", "women", "male", "female")
            parent_category: Parent category (not used currently)

        Returns:
            Vinted size ID, or None if not found

        Examples:
            >>> VintedMappingService.map_size(db, "M", "women", "t-shirt")
            4  # Women's M
            >>> VintedMappingService.map_size(db, "M", "men", "t-shirt")
            208  # Men's M
        """
        if not size_name:
            return None

        size = db.query(Size).filter(Size.name_en == size_name).first()

        if not size:
            return None

        # Determine which vinted_id to use based on gender
        gender_lower = gender.lower() if gender else ''
        is_women = gender_lower in ['women', 'woman', 'female', 'femme', 'girl', 'girls']

        if is_women:
            if size.vinted_women_id:
                return int(size.vinted_women_id)
        else:
            # Default to men for male, unisex, or unknown gender
            if size.vinted_men_id:
                return int(size.vinted_men_id)

        # Fallback: try the other gender's ID if the preferred one is missing
        if size.vinted_women_id:
            return int(size.vinted_women_id)
        if size.vinted_men_id:
            return int(size.vinted_men_id)

        return None

    @staticmethod
    def map_category(
        db: Session,
        category: str,
        gender: str,
        fit: Optional[str] = None,
        length: Optional[str] = None,
        rise: Optional[str] = None,
        material: Optional[str] = None,
        pattern: Optional[str] = None,
        neckline: Optional[str] = None,
        sleeve_length: Optional[str] = None
    ) -> Tuple[Optional[int], Optional[str], Optional[str]]:
        """
        Map Stoflow category to Vinted category using vinted.mapping table.

        Uses VintedMappingRepository which calls the PostgreSQL function
        get_vinted_category() for intelligent matching with attribute scoring.

        Args:
            db: Session SQLAlchemy
            category: Category name (EN), e.g. "jeans", "t-shirt"
            gender: Product gender, e.g. "men", "women"
            fit: Optional fit, e.g. "slim", "regular"
            length: Optional length, e.g. "short", "long"
            rise: Optional rise (for pants), e.g. "high", "mid", "low"
            material: Optional material, e.g. "cotton", "denim"
            pattern: Optional pattern, e.g. "solid", "striped"
            neckline: Optional neckline, e.g. "crew", "v-neck"
            sleeve_length: Optional sleeve length, e.g. "short", "long"

        Returns:
            Tuple (vinted_id, vinted_title, vinted_path) or (None, None, None)

        Examples:
            >>> vinted_id, title, path = VintedMappingService.map_category(
            ...     db, "jeans", "women", fit="skinny"
            ... )
            >>> print(vinted_id, title)  # Ex: 1844, "Jeans skinny"
        """
        from repositories.vinted_mapping_repository import VintedMappingRepository

        repo = VintedMappingRepository(db)
        details = repo.get_vinted_category_with_details(
            category=category,
            gender=gender,
            fit=fit,
            length=length,
            rise=rise,
            material=material,
            pattern=pattern,
            neckline=neckline,
            sleeve_length=sleeve_length
        )

        return (
            details.get("vinted_id"),
            details.get("title"),
            details.get("path")
        )

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

        # Extract category name
        category_name = product.category if isinstance(product.category, str) else (product.category.name_en if hasattr(product.category, 'name_en') else str(product.category))

        # Extract all optional attributes for intelligent matching
        fit = getattr(product, 'fit', None)
        length = getattr(product, 'length', None)
        rise = getattr(product, 'rise', None)
        pattern = getattr(product, 'pattern', None)
        neckline = getattr(product, 'neckline', None)
        sleeve_length = getattr(product, 'sleeve_length', None)

        # Get material name for category matching
        material = getattr(product, 'material', None)
        material_name_for_category = None
        if material:
            if isinstance(material, list) and len(material) > 0:
                material_name_for_category = material[0]
            elif isinstance(material, str):
                material_name_for_category = material

        # Map category using all available attributes for best match
        category_id, vinted_category_name, category_path = VintedMappingService.map_category(
            db,
            category_name,
            gender,
            fit=fit,
            length=length,
            rise=rise,
            material=material_name_for_category,
            pattern=pattern,
            neckline=neckline,
            sleeve_length=sleeve_length
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
