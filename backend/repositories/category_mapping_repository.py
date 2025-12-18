"""
Category Mapping Repository

Repository pour la gestion des mappings categories -> plateformes (Vinted, Etsy, eBay).
Responsabilite: Acces donnees pour category_platform_mappings (schema public).

Architecture:
- Repository pattern pour isolation DB
- Fallback strategy: exact match -> sans fit -> premier trouve
- Methodes specifiques par plateforme

Created: 2025-12-17
Author: Claude
"""

import json
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from models.public.category_platform_mapping import CategoryPlatformMapping


class CategoryMappingRepository:
    """
    Repository pour la gestion des CategoryPlatformMapping.

    Fournit des methodes de lookup par plateforme avec fallback strategy:
    1. Match exact (category + gender + fit)
    2. Match sans fit (category + gender + fit=NULL)
    3. Premier trouve (category + gender, n'importe quel fit)
    """

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy session
        """
        self.db = db

    def _find_mapping(
        self,
        category: str,
        gender: str,
        fit: Optional[str] = None
    ) -> Optional[CategoryPlatformMapping]:
        """
        Find mapping with fallback strategy.

        Strategy:
        1. Exact match (category + gender + fit)
        2. No-fit match (category + gender + fit=NULL)
        3. Any fit match (category + gender, first found)

        Args:
            category: Category name (EN)
            gender: Gender name (EN)
            fit: Fit name (EN), optional

        Returns:
            CategoryPlatformMapping if found, None otherwise
        """
        # 1. Exact match (with fit)
        if fit:
            mapping = self.db.query(CategoryPlatformMapping).filter(
                and_(
                    CategoryPlatformMapping.category == category,
                    CategoryPlatformMapping.gender == gender,
                    CategoryPlatformMapping.fit == fit
                )
            ).first()
            if mapping:
                return mapping

        # 2. No-fit match (fit is NULL)
        mapping = self.db.query(CategoryPlatformMapping).filter(
            and_(
                CategoryPlatformMapping.category == category,
                CategoryPlatformMapping.gender == gender,
                CategoryPlatformMapping.fit.is_(None)
            )
        ).first()
        if mapping:
            return mapping

        # 3. Any fit match (first found)
        mapping = self.db.query(CategoryPlatformMapping).filter(
            and_(
                CategoryPlatformMapping.category == category,
                CategoryPlatformMapping.gender == gender
            )
        ).first()
        return mapping

    # ===== VINTED =====

    def get_vinted_mapping(
        self,
        category: str,
        gender: str,
        fit: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get Vinted category mapping.

        Args:
            category: Category name (EN), e.g. "Jeans"
            gender: Gender name (EN), e.g. "Men"
            fit: Fit name (EN), e.g. "Slim" (optional)

        Returns:
            Dict with Vinted mapping if found:
            {
                'id': int,          # Vinted catalog_id
                'name': str,        # Vinted category name
                'path': str         # Vinted category path
            }
            None if not found

        Example:
            >>> repo = CategoryMappingRepository(db)
            >>> mapping = repo.get_vinted_mapping("Jeans", "Men", "Slim")
            >>> print(mapping)
            {'id': 89, 'name': 'Jean slim', 'path': 'Hommes > Jeans > Slim'}
        """
        mapping = self._find_mapping(category, gender, fit)
        if not mapping or not mapping.vinted_category_id:
            return None

        return {
            'id': mapping.vinted_category_id,
            'name': mapping.vinted_category_name,
            'path': mapping.vinted_category_path
        }

    # ===== ETSY =====

    def get_etsy_mapping(
        self,
        category: str,
        gender: str,
        fit: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get Etsy taxonomy mapping.

        Args:
            category: Category name (EN)
            gender: Gender name (EN)
            fit: Fit name (EN), optional

        Returns:
            Dict with Etsy mapping if found:
            {
                'taxonomy_id': int,     # Etsy taxonomy ID
                'name': str,            # Etsy category name
                'path': str,            # Etsy category path
                'attributes': dict      # Required attributes (parsed JSON)
            }
            None if not found

        Example:
            >>> repo = CategoryMappingRepository(db)
            >>> mapping = repo.get_etsy_mapping("Jeans", "Men")
            >>> print(mapping['taxonomy_id'])
            1429
        """
        mapping = self._find_mapping(category, gender, fit)
        if not mapping or not mapping.etsy_taxonomy_id:
            return None

        # Parse JSON attributes if present
        attributes = None
        if mapping.etsy_required_attributes:
            try:
                attributes = json.loads(mapping.etsy_required_attributes)
            except json.JSONDecodeError:
                attributes = None

        return {
            'taxonomy_id': mapping.etsy_taxonomy_id,
            'name': mapping.etsy_category_name,
            'path': mapping.etsy_category_path,
            'attributes': attributes
        }

    # ===== EBAY =====

    def get_ebay_mapping(
        self,
        category: str,
        gender: str,
        fit: Optional[str] = None,
        marketplace: str = "EBAY_FR"
    ) -> Optional[Dict[str, Any]]:
        """
        Get eBay category mapping for a specific marketplace.

        Args:
            category: Category name (EN)
            gender: Gender name (EN)
            fit: Fit name (EN), optional
            marketplace: eBay marketplace ("EBAY_FR", "EBAY_DE", "EBAY_GB", "EBAY_IT", "EBAY_ES")

        Returns:
            Dict with eBay mapping if found:
            {
                'category_id': int,         # eBay category ID for marketplace
                'name': str,                # eBay category name
                'item_specifics': dict      # Required item specifics (parsed JSON)
            }
            None if not found

        Example:
            >>> repo = CategoryMappingRepository(db)
            >>> mapping = repo.get_ebay_mapping("Jeans", "Men", marketplace="EBAY_FR")
            >>> print(mapping['category_id'])
            11483
        """
        mapping = self._find_mapping(category, gender, fit)
        if not mapping:
            return None

        # Get category ID for specific marketplace
        marketplace_column_map = {
            "EBAY_FR": mapping.ebay_category_id_fr,
            "EBAY_DE": mapping.ebay_category_id_de,
            "EBAY_GB": mapping.ebay_category_id_gb,
            "EBAY_IT": mapping.ebay_category_id_it,
            "EBAY_ES": mapping.ebay_category_id_es,
        }

        category_id = marketplace_column_map.get(marketplace.upper())
        if not category_id:
            return None

        # Parse JSON item specifics if present
        item_specifics = None
        if mapping.ebay_item_specifics:
            try:
                item_specifics = json.loads(mapping.ebay_item_specifics)
            except json.JSONDecodeError:
                item_specifics = None

        return {
            'category_id': category_id,
            'name': mapping.ebay_category_name,
            'item_specifics': item_specifics
        }

    # ===== ALL PLATFORMS =====

    def get_all_mappings(
        self,
        category: str,
        gender: str,
        fit: Optional[str] = None
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Get mappings for all platforms in a single query.

        Args:
            category: Category name (EN)
            gender: Gender name (EN)
            fit: Fit name (EN), optional

        Returns:
            Dict with mappings for each platform:
            {
                'vinted': {...} or None,
                'etsy': {...} or None,
                'ebay_fr': {...} or None,
                'ebay_de': {...} or None,
                'ebay_gb': {...} or None,
                'ebay_it': {...} or None,
                'ebay_es': {...} or None
            }

        Example:
            >>> repo = CategoryMappingRepository(db)
            >>> all_mappings = repo.get_all_mappings("Jeans", "Men", "Slim")
            >>> print(all_mappings['vinted']['id'])
            89
        """
        mapping = self._find_mapping(category, gender, fit)

        result = {
            'vinted': None,
            'etsy': None,
            'ebay_fr': None,
            'ebay_de': None,
            'ebay_gb': None,
            'ebay_it': None,
            'ebay_es': None
        }

        if not mapping:
            return result

        # Vinted
        if mapping.vinted_category_id:
            result['vinted'] = {
                'id': mapping.vinted_category_id,
                'name': mapping.vinted_category_name,
                'path': mapping.vinted_category_path
            }

        # Etsy
        if mapping.etsy_taxonomy_id:
            attributes = None
            if mapping.etsy_required_attributes:
                try:
                    attributes = json.loads(mapping.etsy_required_attributes)
                except json.JSONDecodeError:
                    pass
            result['etsy'] = {
                'taxonomy_id': mapping.etsy_taxonomy_id,
                'name': mapping.etsy_category_name,
                'path': mapping.etsy_category_path,
                'attributes': attributes
            }

        # eBay (all marketplaces)
        item_specifics = None
        if mapping.ebay_item_specifics:
            try:
                item_specifics = json.loads(mapping.ebay_item_specifics)
            except json.JSONDecodeError:
                pass

        ebay_base = {
            'name': mapping.ebay_category_name,
            'item_specifics': item_specifics
        }

        if mapping.ebay_category_id_fr:
            result['ebay_fr'] = {**ebay_base, 'category_id': mapping.ebay_category_id_fr}
        if mapping.ebay_category_id_de:
            result['ebay_de'] = {**ebay_base, 'category_id': mapping.ebay_category_id_de}
        if mapping.ebay_category_id_gb:
            result['ebay_gb'] = {**ebay_base, 'category_id': mapping.ebay_category_id_gb}
        if mapping.ebay_category_id_it:
            result['ebay_it'] = {**ebay_base, 'category_id': mapping.ebay_category_id_it}
        if mapping.ebay_category_id_es:
            result['ebay_es'] = {**ebay_base, 'category_id': mapping.ebay_category_id_es}

        return result

    # ===== CRUD =====

    def create(self, mapping: CategoryPlatformMapping) -> CategoryPlatformMapping:
        """
        Create a new category platform mapping.

        Args:
            mapping: CategoryPlatformMapping instance

        Returns:
            Created CategoryPlatformMapping with ID
        """
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        return mapping

    def get_by_id(self, mapping_id: int) -> Optional[CategoryPlatformMapping]:
        """
        Get mapping by ID.

        Args:
            mapping_id: Mapping ID

        Returns:
            CategoryPlatformMapping if found, None otherwise
        """
        return self.db.query(CategoryPlatformMapping).filter(
            CategoryPlatformMapping.id == mapping_id
        ).first()

    def get_all(self, limit: int = 1000) -> List[CategoryPlatformMapping]:
        """
        Get all mappings.

        Args:
            limit: Maximum number of results

        Returns:
            List of CategoryPlatformMapping
        """
        return self.db.query(CategoryPlatformMapping).limit(limit).all()

    def update(self, mapping: CategoryPlatformMapping) -> CategoryPlatformMapping:
        """
        Update an existing mapping.

        Args:
            mapping: CategoryPlatformMapping with changes

        Returns:
            Updated CategoryPlatformMapping
        """
        self.db.commit()
        self.db.refresh(mapping)
        return mapping

    def delete(self, mapping_id: int) -> bool:
        """
        Delete a mapping.

        Args:
            mapping_id: Mapping ID to delete

        Returns:
            True if deleted, False if not found
        """
        mapping = self.get_by_id(mapping_id)
        if not mapping:
            return False

        self.db.delete(mapping)
        self.db.commit()
        return True

    def exists(self, category: str, gender: str, fit: Optional[str] = None) -> bool:
        """
        Check if a mapping exists for the given composite key.

        Args:
            category: Category name (EN)
            gender: Gender name (EN)
            fit: Fit name (EN), optional

        Returns:
            True if mapping exists, False otherwise
        """
        query = self.db.query(CategoryPlatformMapping).filter(
            and_(
                CategoryPlatformMapping.category == category,
                CategoryPlatformMapping.gender == gender
            )
        )

        if fit:
            query = query.filter(CategoryPlatformMapping.fit == fit)
        else:
            query = query.filter(CategoryPlatformMapping.fit.is_(None))

        return query.first() is not None
