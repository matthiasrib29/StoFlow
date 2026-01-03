"""
Tests unitaires pour VintedMapper

Tests pour la conversion bidirectionnelle Stoflow ↔ Vinted.

Business Rules Tested:
- Stoflow → Vinted: get_vinted_category_id_from_db avec attributs
- Vinted → Stoflow: get_stoflow_category_from_db (lookup inverse)
- Dimensions: dim1=width, dim2=length pour hauts uniquement
- Fallback statique si pas de DB

Author: Claude
Date: 2025-12-18
"""

import pytest
from unittest.mock import Mock, patch

from services.vinted.vinted_mapper import VintedMapper


class TestVintedMapperStatic:
    """Tests pour les méthodes statiques (fallback sans DB)."""

    def test_condition_map_values(self):
        """Test que les conditions Vinted sont bien mappées vers integers Stoflow."""
        # Vinted status_id → Stoflow condition (Integer 0-10)
        assert VintedMapper.CONDITION_MAP[1] == 10  # Neuf avec étiquette → 10
        assert VintedMapper.CONDITION_MAP[2] == 8   # Très bon état → 8
        assert VintedMapper.CONDITION_MAP[3] == 7   # Bon état → 7
        assert VintedMapper.CONDITION_MAP[4] == 6   # Satisfaisant → 6
        assert VintedMapper.CONDITION_MAP[5] == 5   # Utilisé → 5

    def test_reverse_condition_map_lowercase(self):
        """Test reverse mapping des conditions en minuscules."""
        assert VintedMapper.REVERSE_CONDITION_MAP["new"] == 1
        assert VintedMapper.REVERSE_CONDITION_MAP["excellent"] == 2
        assert VintedMapper.REVERSE_CONDITION_MAP["good"] == 3

    def test_reverse_condition_map_uppercase(self):
        """Test reverse mapping des conditions en majuscules."""
        assert VintedMapper.REVERSE_CONDITION_MAP["NEW"] == 1
        assert VintedMapper.REVERSE_CONDITION_MAP["EXCELLENT"] == 2
        assert VintedMapper.REVERSE_CONDITION_MAP["GOOD"] == 3

    def test_category_map_fallback(self):
        """Test fallback mapping statique des catégories."""
        assert VintedMapper.CATEGORY_MAP_FALLBACK[1193] == "jeans"
        assert VintedMapper.CATEGORY_MAP_FALLBACK[1203] == "t-shirt"
        assert VintedMapper.CATEGORY_MAP_FALLBACK[1199] == "sweater"

    def test_platform_to_stoflow_basic(self):
        """Test conversion Vinted → Stoflow basique."""
        vinted_item = {
            "id": 123456,
            "title": "Jean Levi's 501",
            "description": "Jean vintage en bon état",
            "price": "45.00",
            "brand_title": "Levi's",
            "size_title": "W32L34",
            "status_id": 2,
            "catalog_id": 1193,
            "color": "Blue",
            "photos": [
                {"full_size_url": "https://example.com/photo1.jpg"},
                {"full_size_url": "https://example.com/photo2.jpg"}
            ],
            "user_id": 789,
            "url": "https://vinted.fr/items/123456"
        }

        result = VintedMapper.platform_to_stoflow(vinted_item)

        assert result["title"] == "Jean Levi's 501"
        assert result["description"] == "Jean vintage en bon état"
        assert result["price"] == 45.0
        assert result["brand"] == "Levi's"
        assert result["condition"] == 8  # status_id=2 → Très bon état
        assert result["size_original"] == "W32L34"
        assert result["color"] == "Blue"
        assert result["stock_quantity"] == 1
        assert len(result["images"]) == 2

    def test_platform_to_stoflow_missing_fields(self):
        """Test conversion avec champs manquants."""
        vinted_item = {
            "id": 123,
            "title": "Product",
            "price": "10.00"
        }

        result = VintedMapper.platform_to_stoflow(vinted_item)

        assert result["title"] == "Product"
        assert result["price"] == 10.0
        assert result["brand"] is None
        assert result["condition"] == 7  # Default (status_id=3 → Bon état)
        assert result["images"] == []

    def test_stoflow_to_platform_basic(self):
        """Test conversion Stoflow → Vinted basique."""
        stoflow_product = {
            "title": "Jean Levi's 501",
            "description": "Jean vintage",
            "price": 45.99,
            "brand": "Levi's",
            "category": "jeans",
            "condition": 8,  # 8 = Très bon état
            "size_original": "W32",
            "color": "Blue"
        }

        result = VintedMapper.stoflow_to_platform(stoflow_product)

        assert result["title"] == "Jean Levi's 501"
        assert result["price"] == 45.99
        assert result["currency"] == "EUR"
        assert result["status_id"] == 2  # EXCELLENT
        assert result["is_for_sell"] is True

    def test_is_top_category_true(self):
        """Test détection des catégories hauts."""
        assert VintedMapper._is_top_category("t-shirt") is True
        assert VintedMapper._is_top_category("sweater") is True
        assert VintedMapper._is_top_category("Sweatshirt") is True
        assert VintedMapper._is_top_category("HOODIE") is True
        assert VintedMapper._is_top_category("shirt") is True
        assert VintedMapper._is_top_category("polo") is True

    def test_is_top_category_false(self):
        """Test détection des catégories non-hauts."""
        assert VintedMapper._is_top_category("jeans") is False
        assert VintedMapper._is_top_category("pants") is False
        assert VintedMapper._is_top_category("shorts") is False
        assert VintedMapper._is_top_category("dress") is False
        assert VintedMapper._is_top_category("jacket") is False


class TestVintedMapperWithDB:
    """Tests pour les méthodes utilisant la DB."""

    def test_instantiation_without_db(self):
        """Test instantiation sans DB."""
        mapper = VintedMapper()
        assert mapper.db is None
        assert mapper._repo is None

    def test_instantiation_with_db(self):
        """Test instantiation avec DB mock."""
        mock_db = Mock()
        mapper = VintedMapper(db=mock_db)
        assert mapper.db == mock_db
        assert mapper._repo is not None

    def test_with_db_class_method(self):
        """Test factory method with_db."""
        mock_db = Mock()
        mapper = VintedMapper.with_db(mock_db)
        assert mapper.db == mock_db

    def test_get_vinted_category_id_from_db_fallback(self):
        """Test fallback vers mapping statique si pas de DB."""
        mapper = VintedMapper()

        # Sans DB, utilise le fallback statique
        # Note: "jeans" apparaît 2x (homme=1193, femme=1211), reverse map garde le dernier
        result = mapper.get_vinted_category_id_from_db("t-shirt", "men")
        assert result == 1203  # De REVERSE_CATEGORY_MAP (t-shirt unique)

    def test_get_stoflow_category_from_db_fallback(self):
        """Test fallback vers mapping statique si pas de DB."""
        mapper = VintedMapper()

        # Sans DB, utilise le fallback statique
        category, gender = mapper.get_stoflow_category_from_db(1193)
        assert category == "jeans"
        assert gender is None  # Pas de genre en fallback

    @patch('services.vinted.vinted_mapper.VintedMappingRepository')
    def test_get_vinted_category_id_from_db_with_repo(self, MockRepo):
        """Test appel au repository pour le mapping."""
        mock_db = Mock()
        mock_repo = Mock()
        mock_repo.get_vinted_category_id.return_value = 1234
        MockRepo.return_value = mock_repo

        mapper = VintedMapper(db=mock_db)
        result = mapper.get_vinted_category_id_from_db(
            category="jeans",
            gender="men",
            fit="slim"
        )

        assert result == 1234
        mock_repo.get_vinted_category_id.assert_called_once_with(
            category="jeans",
            gender="men",
            fit="slim",
            length=None,
            rise=None,
            material=None,
            pattern=None,
            neckline=None,
            sleeve_length=None
        )

    @patch('services.vinted.vinted_mapper.VintedMappingRepository')
    def test_get_stoflow_category_from_db_with_repo(self, MockRepo):
        """Test appel au repository pour le reverse mapping."""
        mock_db = Mock()
        mock_repo = Mock()
        mock_repo.get_stoflow_category.return_value = ("jeans", "men")
        MockRepo.return_value = mock_repo

        mapper = VintedMapper(db=mock_db)
        category, gender = mapper.get_stoflow_category_from_db(1193)

        assert category == "jeans"
        assert gender == "men"
        mock_repo.get_stoflow_category.assert_called_once_with(1193)


class TestVintedMapperDimensions:
    """Tests pour le mapping des dimensions."""

    def test_vinted_to_stoflow_with_dimensions(self):
        """Test extraction des dimensions Vinted vers dim1/dim2."""
        mapper = VintedMapper()
        vinted_item = {
            "id": 123,
            "title": "T-shirt",
            "price": "20.00",
            "catalog_id": 1203,
            "measurement_width": 52,
            "measurement_length": 70
        }

        result = mapper.vinted_to_stoflow_with_db(vinted_item)

        assert result["dim1"] == 52
        assert result["dim2"] == 70

    def test_stoflow_to_vinted_with_dimensions_for_top(self):
        """Test inclusion dimensions pour hauts."""
        mapper = VintedMapper()
        stoflow_product = {
            "title": "T-shirt Nike",
            "description": "T-shirt sport",
            "price": 25.0,
            "category": "t-shirt",
            "gender": "men",
            "condition": 7,
            "dim1": 52,
            "dim2": 70
        }

        result = mapper.stoflow_to_vinted_with_db(stoflow_product)

        assert result["measurement_width"] == 52
        assert result["measurement_length"] == 70

    def test_stoflow_to_vinted_no_dimensions_for_pants(self):
        """Test pas de dimensions pour pantalons."""
        mapper = VintedMapper()
        stoflow_product = {
            "title": "Jean Levi's",
            "description": "Jean slim",
            "price": 45.0,
            "category": "jeans",
            "gender": "men",
            "condition": 7,
            "dim1": 80,  # Taille
            "dim2": 100  # Longueur
        }

        result = mapper.stoflow_to_vinted_with_db(stoflow_product)

        # Pas de dimensions pour jeans (pas un haut)
        assert "measurement_width" not in result
        assert "measurement_length" not in result


class TestVintedMapperAliases:
    """Tests pour les alias de rétrocompatibilité."""

    def test_vinted_to_stoflow_alias(self):
        """Test alias vinted_to_stoflow."""
        vinted_item = {"id": 1, "title": "Test", "price": "10.00"}
        result = VintedMapper.vinted_to_stoflow(vinted_item)
        assert result["title"] == "Test"

    def test_stoflow_to_vinted_alias(self):
        """Test alias stoflow_to_vinted."""
        stoflow = {"title": "Test", "price": 10, "category": "jeans", "condition": 7}
        result = VintedMapper.stoflow_to_vinted(stoflow)
        assert result["title"] == "Test"

    def test_get_vinted_catalog_id_alias(self):
        """Test alias get_vinted_catalog_id."""
        # Note: "jeans" apparaît 2x dans le map, utiliser "t-shirt" qui est unique
        result = VintedMapper.get_vinted_catalog_id("t-shirt")
        assert result == 1203
