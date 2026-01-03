"""
Tests unitaires pour VintedMappingService

Tests pour le mapping des attributs Product → IDs Vinted.

Business Rules Tested:
- Brand: mapping via brand.vinted_id
- Color: mapping via color.vinted_id
- Condition: mapping via condition.vinted_id
- Size: mapping selon genre (woman, man_top, man_bottom)
- Material: mapping via material.vinted_id (NEW)
- Category: mapping via CategoryMappingRepository

Author: Claude
Date: 2025-12-18
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from services.vinted.vinted_mapping_service import VintedMappingService


class TestMapBrand:
    """Tests pour map_brand."""

    def test_map_brand_found(self):
        """Test mapping marque existante."""
        mock_db = Mock()
        mock_brand = Mock()
        mock_brand.vinted_id = 53
        mock_db.query.return_value.filter.return_value.first.return_value = mock_brand

        result = VintedMappingService.map_brand(mock_db, "Levi's")

        assert result == 53

    def test_map_brand_not_found(self):
        """Test mapping marque inexistante."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = VintedMappingService.map_brand(mock_db, "UnknownBrand")

        assert result is None

    def test_map_brand_no_vinted_id(self):
        """Test marque sans vinted_id."""
        mock_db = Mock()
        mock_brand = Mock()
        mock_brand.vinted_id = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_brand

        result = VintedMappingService.map_brand(mock_db, "Levi's")

        assert result is None

    def test_map_brand_none_input(self):
        """Test avec brand_name None."""
        mock_db = Mock()

        result = VintedMappingService.map_brand(mock_db, None)

        assert result is None
        mock_db.query.assert_not_called()

    def test_map_brand_empty_string(self):
        """Test avec brand_name vide."""
        mock_db = Mock()

        result = VintedMappingService.map_brand(mock_db, "")

        assert result is None


class TestMapColor:
    """Tests pour map_color."""

    def test_map_color_found(self):
        """Test mapping couleur existante."""
        mock_db = Mock()
        mock_color = Mock()
        mock_color.vinted_id = 12
        mock_db.query.return_value.filter.return_value.first.return_value = mock_color

        result = VintedMappingService.map_color(mock_db, "Blue")

        assert result == 12

    def test_map_color_not_found(self):
        """Test mapping couleur inexistante."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = VintedMappingService.map_color(mock_db, "Rainbow")

        assert result is None

    def test_map_color_none_input(self):
        """Test avec color_name None."""
        mock_db = Mock()

        result = VintedMappingService.map_color(mock_db, None)

        assert result is None


class TestMapCondition:
    """Tests pour map_condition."""

    def test_map_condition_found(self):
        """Test mapping condition existante."""
        mock_db = Mock()
        mock_condition = Mock()
        mock_condition.vinted_id = 2
        mock_db.query.return_value.filter.return_value.first.return_value = mock_condition

        result = VintedMappingService.map_condition(mock_db, "EXCELLENT")

        assert result == 2

    def test_map_condition_not_found(self):
        """Test mapping condition inexistante."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = VintedMappingService.map_condition(mock_db, "UNKNOWN")

        assert result is None

    def test_map_condition_none_input(self):
        """Test avec condition_name None."""
        mock_db = Mock()

        result = VintedMappingService.map_condition(mock_db, None)

        assert result is None


class TestMapMaterial:
    """Tests pour map_material (NEW)."""

    def test_map_material_found(self):
        """Test mapping matériau existant."""
        mock_db = Mock()
        mock_material = Mock()
        mock_material.vinted_id = 44
        mock_db.query.return_value.filter.return_value.first.return_value = mock_material

        result = VintedMappingService.map_material(mock_db, "Cotton")

        assert result == 44

    def test_map_material_denim(self):
        """Test mapping Denim → 303."""
        mock_db = Mock()
        mock_material = Mock()
        mock_material.vinted_id = 303
        mock_db.query.return_value.filter.return_value.first.return_value = mock_material

        result = VintedMappingService.map_material(mock_db, "Denim")

        assert result == 303

    def test_map_material_not_found(self):
        """Test mapping matériau inexistant."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = VintedMappingService.map_material(mock_db, "Unobtainium")

        assert result is None

    def test_map_material_no_vinted_id(self):
        """Test matériau sans vinted_id."""
        mock_db = Mock()
        mock_material = Mock()
        mock_material.vinted_id = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_material

        result = VintedMappingService.map_material(mock_db, "Hemp")

        assert result is None

    def test_map_material_none_input(self):
        """Test avec material_name None."""
        mock_db = Mock()

        result = VintedMappingService.map_material(mock_db, None)

        assert result is None


class TestMapMaterials:
    """Tests pour map_materials (liste de matériaux)."""

    def test_map_materials_single(self):
        """Test mapping d'un seul matériau."""
        mock_db = Mock()
        mock_material = Mock()
        mock_material.vinted_id = 44
        mock_db.query.return_value.filter.return_value.first.return_value = mock_material

        result = VintedMappingService.map_materials(mock_db, ["Cotton"])

        assert result == [44]

    def test_map_materials_multiple(self):
        """Test mapping de plusieurs matériaux."""
        mock_db = Mock()

        # Setup mock to return different vinted_ids
        def mock_filter_side_effect(*args, **kwargs):
            mock_result = Mock()
            # Simulate different materials
            filter_call = mock_db.query.return_value.filter.call_args
            if filter_call:
                # Return different mock based on call count
                call_count = mock_db.query.return_value.filter.call_count
                if call_count == 1:
                    mock_mat = Mock()
                    mock_mat.vinted_id = 44  # Cotton
                    mock_result.first.return_value = mock_mat
                elif call_count == 2:
                    mock_mat = Mock()
                    mock_mat.vinted_id = 45  # Polyester
                    mock_result.first.return_value = mock_mat
            return mock_result

        mock_db.query.return_value.filter.side_effect = mock_filter_side_effect

        result = VintedMappingService.map_materials(mock_db, ["Cotton", "Polyester"])

        assert len(result) == 2
        assert 44 in result
        assert 45 in result

    def test_map_materials_max_three(self):
        """Test limite de 3 matériaux (règle Vinted)."""
        mock_db = Mock()
        mock_material = Mock()
        mock_material.vinted_id = 44
        mock_db.query.return_value.filter.return_value.first.return_value = mock_material

        # Pass 5 materials, should only process 3
        result = VintedMappingService.map_materials(
            mock_db, ["Cotton", "Polyester", "Wool", "Silk", "Linen"]
        )

        # Only 3 calls should have been made
        assert mock_db.query.call_count == 3

    def test_map_materials_empty_list(self):
        """Test avec liste vide."""
        mock_db = Mock()

        result = VintedMappingService.map_materials(mock_db, [])

        assert result == []

    def test_map_materials_none_input(self):
        """Test avec None."""
        mock_db = Mock()

        result = VintedMappingService.map_materials(mock_db, None)

        assert result == []

    def test_map_materials_deduplication(self):
        """Test déduplication des IDs."""
        mock_db = Mock()
        mock_material = Mock()
        mock_material.vinted_id = 44  # Same ID for all
        mock_db.query.return_value.filter.return_value.first.return_value = mock_material

        result = VintedMappingService.map_materials(mock_db, ["Cotton", "Cotton", "Cotton"])

        # Should only have one 44, not three
        assert result == [44]


class TestMapSize:
    """Tests pour map_size."""

    def test_map_size_woman(self):
        """Test mapping taille femme."""
        mock_db = Mock()
        mock_size = Mock()
        mock_size.vinted_woman_id = 206
        mock_size.vinted_man_top_id = None
        mock_size.vinted_man_bottom_id = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_size

        result = VintedMappingService.map_size(mock_db, "M", "female", "T-shirt")

        assert result == 206

    def test_map_size_man_top(self):
        """Test mapping taille homme haut."""
        mock_db = Mock()
        mock_size = Mock()
        mock_size.vinted_woman_id = None
        mock_size.vinted_man_top_id = 210
        mock_size.vinted_man_bottom_id = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_size

        result = VintedMappingService.map_size(mock_db, "L", "male", "Sweater")

        assert result == 210

    def test_map_size_man_bottom(self):
        """Test mapping taille homme bas."""
        mock_db = Mock()
        mock_size = Mock()
        mock_size.vinted_woman_id = None
        mock_size.vinted_man_top_id = None
        mock_size.vinted_man_bottom_id = 207
        mock_db.query.return_value.filter.return_value.first.return_value = mock_size

        result = VintedMappingService.map_size(mock_db, "32", "male", "Jeans")

        assert result == 207

    def test_map_size_none_input(self):
        """Test avec size_name None."""
        mock_db = Mock()

        result = VintedMappingService.map_size(mock_db, None, "male", "Jeans")

        assert result is None


class TestIsBottomCategory:
    """Tests pour _is_bottom_category."""

    def test_is_bottom_jeans(self):
        """Test Jeans = bottom."""
        assert VintedMappingService._is_bottom_category("Jeans") is True

    def test_is_bottom_pants(self):
        """Test Pants = bottom."""
        assert VintedMappingService._is_bottom_category("Pants") is True

    def test_is_bottom_shorts(self):
        """Test Shorts = bottom."""
        assert VintedMappingService._is_bottom_category("Shorts") is True

    def test_is_bottom_skirt(self):
        """Test Skirt = bottom."""
        assert VintedMappingService._is_bottom_category("Skirt") is True

    def test_is_not_bottom_tshirt(self):
        """Test T-shirt = NOT bottom."""
        assert VintedMappingService._is_bottom_category("T-shirt") is False

    def test_is_not_bottom_jacket(self):
        """Test Jacket = NOT bottom."""
        assert VintedMappingService._is_bottom_category("Jacket") is False

    def test_is_not_bottom_sweater(self):
        """Test Sweater = NOT bottom."""
        assert VintedMappingService._is_bottom_category("Sweater") is False


class TestNormalizeGender:
    """Tests pour _normalize_gender."""

    def test_normalize_male(self):
        """Test normalisation male → Men."""
        assert VintedMappingService._normalize_gender("male") == "Men"

    def test_normalize_man(self):
        """Test normalisation man → Men."""
        assert VintedMappingService._normalize_gender("man") == "Men"

    def test_normalize_homme(self):
        """Test normalisation homme → Men."""
        assert VintedMappingService._normalize_gender("homme") == "Men"

    def test_normalize_female(self):
        """Test normalisation female → Women."""
        assert VintedMappingService._normalize_gender("female") == "Women"

    def test_normalize_woman(self):
        """Test normalisation woman → Women."""
        assert VintedMappingService._normalize_gender("woman") == "Women"

    def test_normalize_femme(self):
        """Test normalisation femme → Women."""
        assert VintedMappingService._normalize_gender("femme") == "Women"

    def test_normalize_unisex_defaults_to_men(self):
        """Test normalisation unisex → Men (default)."""
        assert VintedMappingService._normalize_gender("unisex") == "Men"

    def test_normalize_case_insensitive(self):
        """Test normalisation case insensitive."""
        assert VintedMappingService._normalize_gender("MALE") == "Men"
        assert VintedMappingService._normalize_gender("Female") == "Women"


class TestMapAllAttributes:
    """Tests pour map_all_attributes."""

    @patch.object(VintedMappingService, 'map_brand')
    @patch.object(VintedMappingService, 'map_color')
    @patch.object(VintedMappingService, 'map_condition')
    @patch.object(VintedMappingService, 'map_size')
    @patch.object(VintedMappingService, 'map_category')
    @patch.object(VintedMappingService, 'map_material')
    def test_map_all_attributes_complete(
        self, mock_material, mock_category, mock_size,
        mock_condition, mock_color, mock_brand
    ):
        """Test mapping complet de tous les attributs."""
        mock_db = Mock()

        # Setup mocks
        mock_brand.return_value = 53
        mock_color.return_value = 12
        mock_condition.return_value = 2
        mock_size.return_value = 207
        mock_category.return_value = (1193, "Jean slim", "Hommes > Jeans > Slim")
        mock_material.return_value = 303

        # Create mock product
        mock_product = Mock()
        mock_product.brand = "Levi's"
        mock_product.color = "Blue"
        mock_product.condition = 8
        mock_product.size = "32"
        mock_product.category = "Jeans"
        mock_product.gender = "male"
        mock_product.fit = "Slim"
        mock_product.material = "Denim"

        result = VintedMappingService.map_all_attributes(mock_db, mock_product)

        assert result['brand_id'] == 53
        assert result['color_id'] == 12
        assert result['condition_id'] == 2
        assert result['size_id'] == 207
        assert result['category_id'] == 1193
        assert result['category_name'] == "Jean slim"
        assert result['category_path'] == "Hommes > Jeans > Slim"
        assert result['gender'] == "male"
        assert result['is_bottom'] is True
        assert result['material_ids'] == [303]

    @patch.object(VintedMappingService, 'map_brand')
    @patch.object(VintedMappingService, 'map_color')
    @patch.object(VintedMappingService, 'map_condition')
    @patch.object(VintedMappingService, 'map_size')
    @patch.object(VintedMappingService, 'map_category')
    @patch.object(VintedMappingService, 'map_material')
    def test_map_all_attributes_no_material(
        self, mock_material, mock_category, mock_size,
        mock_condition, mock_color, mock_brand
    ):
        """Test mapping sans matériau."""
        mock_db = Mock()

        mock_brand.return_value = 53
        mock_color.return_value = 12
        mock_condition.return_value = 2
        mock_size.return_value = 207
        mock_category.return_value = (1193, "Jean", "Hommes > Jeans")
        mock_material.return_value = None

        mock_product = Mock()
        mock_product.brand = "Levi's"
        mock_product.color = "Blue"
        mock_product.condition = 8
        mock_product.size = "32"
        mock_product.category = "Jeans"
        mock_product.gender = "male"
        mock_product.fit = None
        mock_product.material = None

        result = VintedMappingService.map_all_attributes(mock_db, mock_product)

        assert result['material_ids'] == []

    @patch.object(VintedMappingService, 'map_brand')
    @patch.object(VintedMappingService, 'map_color')
    @patch.object(VintedMappingService, 'map_condition')
    @patch.object(VintedMappingService, 'map_size')
    @patch.object(VintedMappingService, 'map_category')
    @patch.object(VintedMappingService, 'map_materials')
    def test_map_all_attributes_material_list(
        self, mock_materials, mock_category, mock_size,
        mock_condition, mock_color, mock_brand
    ):
        """Test mapping avec liste de matériaux."""
        mock_db = Mock()

        mock_brand.return_value = 53
        mock_color.return_value = 12
        mock_condition.return_value = 2
        mock_size.return_value = 210
        mock_category.return_value = (1203, "T-shirt", "Hommes > T-shirts")
        mock_materials.return_value = [44, 45]  # Cotton + Polyester

        mock_product = Mock()
        mock_product.brand = "Nike"
        mock_product.color = "White"
        mock_product.condition = 7
        mock_product.size = "L"
        mock_product.category = "T-shirt"
        mock_product.gender = "male"
        mock_product.fit = None
        mock_product.material = ["Cotton", "Polyester"]

        result = VintedMappingService.map_all_attributes(mock_db, mock_product)

        assert result['material_ids'] == [44, 45]
