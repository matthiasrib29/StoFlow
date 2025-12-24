"""
Vinted Mapping Repository

Repository pour accéder à la table vinted_mapping et la fonction get_vinted_category.
Gère le mapping bidirectionnel entre catégories Stoflow et catégories Vinted.

Business Rules (2025-12-18):
- Stoflow → Vinted: utilise get_vinted_category() avec matching d'attributs
- Vinted → Stoflow: lookup inverse dans vinted_mapping (vinted_id → my_category)
- Fallback via is_default si pas de match exact

Architecture:
- Accès direct à la table vinted.mapping
- Appelle la fonction PostgreSQL get_vinted_category pour le matching intelligent
- Gère les attributs optionnels (fit, length, rise, material, etc.)

Author: Claude
Date: 2025-12-18
"""

from typing import Any, Dict, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session

from shared.logging_setup import get_logger

logger = get_logger(__name__)


class VintedMappingRepository:
    """
    Repository pour le mapping bidirectionnel Stoflow ↔ Vinted.

    Utilise la table vinted_mapping et la fonction get_vinted_category.
    """

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy session
        """
        self.db = db

    # =========================================================================
    # STOFLOW → VINTED (Publication)
    # =========================================================================

    def get_vinted_category_id(
        self,
        category: str,
        gender: str,
        fit: Optional[str] = None,
        length: Optional[str] = None,
        rise: Optional[str] = None,
        material: Optional[str] = None,
        pattern: Optional[str] = None,
        neckline: Optional[str] = None,
        sleeve_length: Optional[str] = None
    ) -> Optional[int]:
        """
        Get Vinted category ID from Stoflow category using get_vinted_category function.

        Uses the PostgreSQL function which performs intelligent matching:
        1. Best match with attributes (weighted scoring)
        2. Fallback to is_default=true mapping

        Args:
            category: Stoflow category name (EN), e.g. "jeans", "t-shirt"
            gender: Gender, e.g. "men", "women"
            fit: Optional fit, e.g. "slim", "regular"
            length: Optional length, e.g. "short", "long"
            rise: Optional rise (for pants), e.g. "high", "mid", "low"
            material: Optional material, e.g. "cotton", "denim"
            pattern: Optional pattern, e.g. "solid", "striped"
            neckline: Optional neckline, e.g. "crew", "v-neck"
            sleeve_length: Optional sleeve length, e.g. "short", "long"

        Returns:
            Vinted category ID (catalog_id) or None if not found

        Example:
            >>> repo = VintedMappingRepository(db)
            >>> vinted_id = repo.get_vinted_category_id("jeans", "men", fit="slim")
            >>> print(vinted_id)  # Ex: 1193
        """
        try:
            result = self.db.execute(
                text("""
                    SELECT public.get_vinted_category(
                        :category,
                        :gender,
                        :fit,
                        :length,
                        :rise,
                        :material,
                        :pattern,
                        :neckline,
                        :sleeve_length
                    )
                """),
                {
                    "category": category.lower() if category else None,
                    "gender": gender.lower() if gender else None,
                    "fit": fit.lower() if fit else None,
                    "length": length.lower() if length else None,
                    "rise": rise.lower() if rise else None,
                    "material": material.lower() if material else None,
                    "pattern": pattern.lower() if pattern else None,
                    "neckline": neckline.lower() if neckline else None,
                    "sleeve_length": sleeve_length.lower() if sleeve_length else None,
                }
            )
            vinted_id = result.scalar()

            if vinted_id:
                logger.debug(
                    f"Mapped {category}/{gender} (fit={fit}) → Vinted ID {vinted_id}"
                )
            else:
                logger.warning(
                    f"No Vinted mapping found for {category}/{gender} (fit={fit})"
                )

            return vinted_id

        except Exception as e:
            logger.error(f"Error getting Vinted category: {e}")
            return None

    def get_vinted_category_with_details(
        self,
        category: str,
        gender: str,
        **attributes
    ) -> Dict[str, Any]:
        """
        Get Vinted category ID with full details (name, path).

        Args:
            category: Stoflow category name
            gender: Gender
            **attributes: Optional attributes (fit, length, rise, etc.)

        Returns:
            Dict with vinted_id, title, path, gender or empty values if not found
        """
        vinted_id = self.get_vinted_category_id(
            category=category,
            gender=gender,
            **attributes
        )

        if not vinted_id:
            return {
                "vinted_id": None,
                "title": None,
                "path": None,
                "gender": gender
            }

        # Get category details from vinted_categories
        result = self.db.execute(
            text("""
                SELECT id, title, path, gender
                FROM vinted.categories
                WHERE id = :vinted_id
            """),
            {"vinted_id": vinted_id}
        ).fetchone()

        if result:
            return {
                "vinted_id": result.id,
                "title": result.title,
                "path": result.path,
                "gender": result.gender
            }

        return {
            "vinted_id": vinted_id,
            "title": None,
            "path": None,
            "gender": gender
        }

    # =========================================================================
    # VINTED → STOFLOW (Import)
    # =========================================================================

    def get_stoflow_category(
        self,
        vinted_id: int
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Get Stoflow category from Vinted category ID (reverse lookup).

        Performs lookup in vinted_mapping table.
        Returns the first match with is_default=true priority.

        Args:
            vinted_id: Vinted category ID (catalog_id)

        Returns:
            Tuple (my_category, my_gender) or (None, None) if not found

        Example:
            >>> repo = VintedMappingRepository(db)
            >>> category, gender = repo.get_stoflow_category(1193)
            >>> print(category, gender)  # "jeans", "men"
        """
        try:
            result = self.db.execute(
                text("""
                    SELECT my_category, my_gender
                    FROM vinted.mapping
                    WHERE vinted_id = :vinted_id
                    ORDER BY is_default DESC
                    LIMIT 1
                """),
                {"vinted_id": vinted_id}
            ).fetchone()

            if result:
                logger.debug(
                    f"Reverse mapped Vinted ID {vinted_id} → {result.my_category}/{result.my_gender}"
                )
                return result.my_category, result.my_gender

            logger.warning(f"No reverse mapping found for Vinted ID {vinted_id}")
            return None, None

        except Exception as e:
            logger.error(f"Error getting Stoflow category from Vinted ID {vinted_id}: {e}")
            return None, None

    def get_stoflow_category_with_details(
        self,
        vinted_id: int
    ) -> Dict[str, Any]:
        """
        Get Stoflow category with full mapping details.

        Args:
            vinted_id: Vinted category ID

        Returns:
            Dict with my_category, my_gender, my_fit, etc.
        """
        try:
            result = self.db.execute(
                text("""
                    SELECT
                        my_category,
                        my_gender,
                        my_fit,
                        my_length,
                        my_rise,
                        my_material,
                        my_pattern,
                        my_neckline,
                        my_sleeve_length,
                        is_default
                    FROM vinted.mapping
                    WHERE vinted_id = :vinted_id
                    ORDER BY is_default DESC
                    LIMIT 1
                """),
                {"vinted_id": vinted_id}
            ).fetchone()

            if result:
                return {
                    "category": result.my_category,
                    "gender": result.my_gender,
                    "fit": result.my_fit,
                    "length": result.my_length,
                    "rise": result.my_rise,
                    "material": result.my_material,
                    "pattern": result.my_pattern,
                    "neckline": result.my_neckline,
                    "sleeve_length": result.my_sleeve_length,
                    "is_default": result.is_default
                }

            return {
                "category": None,
                "gender": None,
                "fit": None,
                "length": None,
                "rise": None,
                "material": None,
                "pattern": None,
                "neckline": None,
                "sleeve_length": None,
                "is_default": False
            }

        except Exception as e:
            logger.error(f"Error getting Stoflow category details: {e}")
            return {"category": None, "gender": None}

    # =========================================================================
    # VALIDATION & UTILITIES
    # =========================================================================

    def has_mapping(self, category: str, gender: str) -> bool:
        """
        Check if a mapping exists for category/gender combination.

        Args:
            category: Stoflow category name
            gender: Gender

        Returns:
            True if at least one mapping exists
        """
        result = self.db.execute(
            text("""
                SELECT EXISTS (
                    SELECT 1 FROM vinted.mapping
                    WHERE my_category = :category
                    AND my_gender = :gender
                )
            """),
            {"category": category.lower(), "gender": gender.lower()}
        )
        return result.scalar()

    def has_default_mapping(self, category: str, gender: str) -> bool:
        """
        Check if a default mapping exists for category/gender.

        Args:
            category: Stoflow category name
            gender: Gender

        Returns:
            True if a default mapping exists
        """
        result = self.db.execute(
            text("""
                SELECT EXISTS (
                    SELECT 1 FROM vinted.mapping
                    WHERE my_category = :category
                    AND my_gender = :gender
                    AND is_default = true
                )
            """),
            {"category": category.lower(), "gender": gender.lower()}
        )
        return result.scalar()

    def get_all_mappings_for_category(
        self,
        category: str,
        gender: str
    ) -> list[Dict[str, Any]]:
        """
        Get all mappings for a category/gender combination.

        Useful for debugging or showing available options.

        Args:
            category: Stoflow category name
            gender: Gender

        Returns:
            List of mapping dicts with vinted_id, attributes, etc.
        """
        results = self.db.execute(
            text("""
                SELECT
                    vm.id,
                    vm.vinted_id,
                    vc.title as vinted_title,
                    vc.path as vinted_path,
                    vm.my_fit,
                    vm.my_length,
                    vm.my_rise,
                    vm.is_default
                FROM vinted.mapping vm
                JOIN vinted.categories vc ON vm.vinted_id = vc.id
                WHERE vm.my_category = :category
                AND vm.my_gender = :gender
                ORDER BY vm.is_default DESC
            """),
            {"category": category.lower(), "gender": gender.lower()}
        ).fetchall()

        return [
            {
                "id": r.id,
                "vinted_id": r.vinted_id,
                "vinted_title": r.vinted_title,
                "vinted_path": r.vinted_path,
                "fit": r.my_fit,
                "length": r.my_length,
                "rise": r.my_rise,
                "is_default": r.is_default
            }
            for r in results
        ]

    def get_mapping_issues(self) -> list[Dict[str, Any]]:
        """
        Get current mapping validation issues from mapping_validation view.

        Returns:
            List of issues (VINTED_NOT_MAPPED, NO_DEFAULT, COUPLE_NOT_MAPPED)
        """
        results = self.db.execute(
            text("""
                SELECT issue, vinted_id, vinted_title, vinted_gender, my_category, my_gender
                FROM vinted.mapping_validation
                ORDER BY issue, my_category, my_gender
            """)
        ).fetchall()

        return [
            {
                "issue": r.issue,
                "vinted_id": r.vinted_id,
                "vinted_title": r.vinted_title,
                "vinted_gender": r.vinted_gender,
                "my_category": r.my_category,
                "my_gender": r.my_gender
            }
            for r in results
        ]


__all__ = ["VintedMappingRepository"]
