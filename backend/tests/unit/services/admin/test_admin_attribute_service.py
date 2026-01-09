"""
Unit tests for AdminAttributeService.

Coverage:
- get_model, get_pk_field, get_name_field: configuration access
- list_attributes: pagination, search, unknown type
- get_attribute: found, not found, unknown type
- create_attribute: success, duplicate, unknown type
- update_attribute: success, not found, pk not modified
- delete_attribute: success, not found, foreign key constraint
- attribute_to_dict: all attribute types

Author: Claude
Date: 2026-01-08
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from services.admin_attribute_service import AdminAttributeService
from models.public.brand import Brand
from models.public.category import Category
from models.public.color import Color
from models.public.material import Material


class TestGetModel:
    """Tests for AdminAttributeService.get_model method."""

    def test_get_model_brands(self):
        """Test get_model returns Brand model for 'brands'."""
        model = AdminAttributeService.get_model("brands")
        assert model == Brand

    def test_get_model_categories(self):
        """Test get_model returns Category model for 'categories'."""
        model = AdminAttributeService.get_model("categories")
        assert model == Category

    def test_get_model_colors(self):
        """Test get_model returns Color model for 'colors'."""
        model = AdminAttributeService.get_model("colors")
        assert model == Color

    def test_get_model_materials(self):
        """Test get_model returns Material model for 'materials'."""
        model = AdminAttributeService.get_model("materials")
        assert model == Material

    def test_get_model_unknown_type_raises_error(self):
        """Test get_model raises ValueError for unknown attribute type."""
        with pytest.raises(ValueError, match="Unknown attribute type"):
            AdminAttributeService.get_model("unknown")


class TestGetPkField:
    """Tests for AdminAttributeService.get_pk_field method."""

    def test_get_pk_field_brands(self):
        """Test get_pk_field returns 'name' for brands."""
        pk_field = AdminAttributeService.get_pk_field("brands")
        assert pk_field == "name"

    def test_get_pk_field_categories(self):
        """Test get_pk_field returns 'name_en' for categories."""
        pk_field = AdminAttributeService.get_pk_field("categories")
        assert pk_field == "name_en"

    def test_get_pk_field_colors(self):
        """Test get_pk_field returns 'name_en' for colors."""
        pk_field = AdminAttributeService.get_pk_field("colors")
        assert pk_field == "name_en"

    def test_get_pk_field_materials(self):
        """Test get_pk_field returns 'name_en' for materials."""
        pk_field = AdminAttributeService.get_pk_field("materials")
        assert pk_field == "name_en"

    def test_get_pk_field_unknown_type_raises_error(self):
        """Test get_pk_field raises ValueError for unknown attribute type."""
        with pytest.raises(ValueError, match="Unknown attribute type"):
            AdminAttributeService.get_pk_field("unknown")


class TestGetNameField:
    """Tests for AdminAttributeService.get_name_field method."""

    def test_get_name_field_brands(self):
        """Test get_name_field returns 'name' for brands."""
        name_field = AdminAttributeService.get_name_field("brands")
        assert name_field == "name"

    def test_get_name_field_categories(self):
        """Test get_name_field returns 'name_en' for categories."""
        name_field = AdminAttributeService.get_name_field("categories")
        assert name_field == "name_en"

    def test_get_name_field_unknown_type_raises_error(self):
        """Test get_name_field raises ValueError for unknown attribute type."""
        with pytest.raises(ValueError, match="Unknown attribute type"):
            AdminAttributeService.get_name_field("unknown")


class TestListAttributes:
    """Tests for AdminAttributeService.list_attributes method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock(spec=Session)

    def test_list_attributes_returns_items_and_count(self, mock_db):
        """Test list_attributes returns tuple of items and total count."""
        mock_brand1 = Mock(spec=Brand)
        mock_brand2 = Mock(spec=Brand)

        mock_query = MagicMock()
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            mock_brand1, mock_brand2
        ]
        mock_db.query.return_value = mock_query

        items, total = AdminAttributeService.list_attributes(mock_db, "brands")

        assert total == 2
        assert len(items) == 2
        mock_db.query.assert_called_once_with(Brand)

    def test_list_attributes_with_pagination(self, mock_db):
        """Test list_attributes with skip and limit parameters."""
        mock_query = MagicMock()
        mock_query.count.return_value = 100
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        AdminAttributeService.list_attributes(mock_db, "brands", skip=10, limit=5)

        mock_query.order_by.return_value.offset.assert_called_once_with(10)
        mock_query.order_by.return_value.offset.return_value.limit.assert_called_once_with(5)

    def test_list_attributes_with_search(self, mock_db):
        """Test list_attributes with search filter."""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        AdminAttributeService.list_attributes(mock_db, "brands", search="nike")

        mock_query.filter.assert_called_once()

    def test_list_attributes_empty_result(self, mock_db):
        """Test list_attributes returns empty list when no items found."""
        mock_query = MagicMock()
        mock_query.count.return_value = 0
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        items, total = AdminAttributeService.list_attributes(mock_db, "colors")

        assert total == 0
        assert items == []

    def test_list_attributes_unknown_type_raises_error(self, mock_db):
        """Test list_attributes raises ValueError for unknown type."""
        with pytest.raises(ValueError, match="Unknown attribute type"):
            AdminAttributeService.list_attributes(mock_db, "unknown")


class TestGetAttribute:
    """Tests for AdminAttributeService.get_attribute method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock(spec=Session)

    def test_get_attribute_found(self, mock_db):
        """Test get_attribute returns item when found."""
        mock_brand = Mock(spec=Brand)
        mock_brand.name = "Nike"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_brand

        result = AdminAttributeService.get_attribute(mock_db, "brands", "Nike")

        assert result is not None
        assert result.name == "Nike"

    def test_get_attribute_not_found(self, mock_db):
        """Test get_attribute returns None when not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = AdminAttributeService.get_attribute(mock_db, "brands", "NonExistent")

        assert result is None

    def test_get_attribute_unknown_type_raises_error(self, mock_db):
        """Test get_attribute raises ValueError for unknown type."""
        with pytest.raises(ValueError, match="Unknown attribute type"):
            AdminAttributeService.get_attribute(mock_db, "unknown", "test")


class TestCreateAttribute:
    """Tests for AdminAttributeService.create_attribute method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=Session)
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        return db

    def test_create_attribute_success(self, mock_db):
        """Test successful attribute creation."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        data = {"name": "NewBrand", "name_fr": "NouvelleMarge"}

        result = AdminAttributeService.create_attribute(mock_db, "brands", data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_attribute_duplicate_raises_error(self, mock_db):
        """Test create_attribute raises ValueError for duplicate."""
        mock_existing = Mock(spec=Brand)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_existing

        data = {"name": "ExistingBrand"}

        with pytest.raises(ValueError, match="already exists"):
            AdminAttributeService.create_attribute(mock_db, "brands", data)

    def test_create_attribute_unknown_type_raises_error(self, mock_db):
        """Test create_attribute raises ValueError for unknown type."""
        with pytest.raises(ValueError, match="Unknown attribute type"):
            AdminAttributeService.create_attribute(mock_db, "unknown", {"name": "test"})

    def test_create_attribute_without_pk_value(self, mock_db):
        """Test create_attribute works without pk in data (model handles default)."""
        data = {"name_fr": "Rouge"}  # No name_en for color

        result = AdminAttributeService.create_attribute(mock_db, "colors", data)

        mock_db.add.assert_called_once()


class TestUpdateAttribute:
    """Tests for AdminAttributeService.update_attribute method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=Session)
        db.commit = Mock()
        db.refresh = Mock()
        return db

    @pytest.fixture
    def mock_brand(self):
        """Create mock brand."""
        brand = Mock(spec=Brand)
        brand.name = "Nike"
        brand.name_fr = "Nike"
        brand.description = "Sports brand"
        return brand

    def test_update_attribute_success(self, mock_db, mock_brand):
        """Test successful attribute update."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_brand

        result = AdminAttributeService.update_attribute(
            mock_db,
            "brands",
            "Nike",
            {"name_fr": "Nike FR", "description": "Updated description"}
        )

        assert result is not None
        assert mock_brand.name_fr == "Nike FR"
        assert mock_brand.description == "Updated description"
        mock_db.commit.assert_called_once()

    def test_update_attribute_not_found(self, mock_db):
        """Test update_attribute returns None when not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = AdminAttributeService.update_attribute(
            mock_db,
            "brands",
            "NonExistent",
            {"name_fr": "Test"}
        )

        assert result is None

    def test_update_attribute_pk_not_modified(self, mock_db, mock_brand):
        """Test update_attribute does not modify primary key field."""
        original_name = mock_brand.name
        mock_db.query.return_value.filter.return_value.first.return_value = mock_brand

        AdminAttributeService.update_attribute(
            mock_db,
            "brands",
            "Nike",
            {"name": "DifferentName", "description": "New desc"}  # Try to change PK
        )

        # Primary key should not be changed
        assert mock_brand.name == original_name

    def test_update_attribute_ignores_none_values(self, mock_db, mock_brand):
        """Test update_attribute ignores None values."""
        original_description = mock_brand.description
        mock_db.query.return_value.filter.return_value.first.return_value = mock_brand

        AdminAttributeService.update_attribute(
            mock_db,
            "brands",
            "Nike",
            {"description": None}
        )

        # None values should be ignored
        assert mock_brand.description == original_description


class TestDeleteAttribute:
    """Tests for AdminAttributeService.delete_attribute method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=Session)
        db.delete = Mock()
        db.commit = Mock()
        db.rollback = Mock()
        return db

    def test_delete_attribute_success(self, mock_db):
        """Test successful attribute deletion."""
        mock_brand = Mock(spec=Brand)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_brand

        result = AdminAttributeService.delete_attribute(mock_db, "brands", "Nike")

        assert result is True
        mock_db.delete.assert_called_once_with(mock_brand)
        mock_db.commit.assert_called_once()

    def test_delete_attribute_not_found(self, mock_db):
        """Test delete_attribute returns False when not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = AdminAttributeService.delete_attribute(mock_db, "brands", "NonExistent")

        assert result is False
        mock_db.delete.assert_not_called()

    def test_delete_attribute_foreign_key_constraint_raises_error(self, mock_db):
        """Test delete_attribute raises ValueError when FK constraint violated."""
        mock_brand = Mock(spec=Brand)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_brand
        mock_db.delete.side_effect = Exception("foreign key constraint")

        with pytest.raises(ValueError, match="Cannot delete"):
            AdminAttributeService.delete_attribute(mock_db, "brands", "Nike")

        mock_db.rollback.assert_called_once()

    def test_delete_attribute_other_error_propagates(self, mock_db):
        """Test delete_attribute propagates non-FK errors."""
        mock_brand = Mock(spec=Brand)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_brand
        mock_db.delete.side_effect = Exception("Some other error")

        with pytest.raises(Exception, match="Some other error"):
            AdminAttributeService.delete_attribute(mock_db, "brands", "Nike")


class TestAttributeToDict:
    """Tests for AdminAttributeService.attribute_to_dict method."""

    def test_attribute_to_dict_brand(self):
        """Test attribute_to_dict for brand."""
        mock_brand = Mock()
        mock_brand.name = "Nike"
        mock_brand.name_fr = "Nike"
        mock_brand.description = "Sports brand"
        mock_brand.vinted_id = 123
        mock_brand.monitoring = True
        mock_brand.sector_jeans = False
        mock_brand.sector_jacket = True

        result = AdminAttributeService.attribute_to_dict(mock_brand, "brands")

        assert result["pk"] == "Nike"
        assert result["name"] == "Nike"
        assert result["name_fr"] == "Nike"
        assert result["description"] == "Sports brand"
        assert result["vinted_id"] == 123
        assert result["monitoring"] is True

    def test_attribute_to_dict_category(self):
        """Test attribute_to_dict for category."""
        mock_category = Mock()
        mock_category.name_en = "Shoes"
        mock_category.name_fr = "Chaussures"
        mock_category.name_de = "Schuhe"
        mock_category.name_it = "Scarpe"
        mock_category.name_es = "Zapatos"
        mock_category.parent_category = "Fashion"
        mock_category.genders = ["men", "women"]

        result = AdminAttributeService.attribute_to_dict(mock_category, "categories")

        assert result["pk"] == "Shoes"
        assert result["name_en"] == "Shoes"
        assert result["name_fr"] == "Chaussures"
        assert result["parent_category"] == "Fashion"

    def test_attribute_to_dict_color(self):
        """Test attribute_to_dict for color."""
        mock_color = Mock()
        mock_color.name_en = "Red"
        mock_color.name_fr = "Rouge"
        mock_color.name_de = "Rot"
        mock_color.name_it = "Rosso"
        mock_color.name_es = "Rojo"
        mock_color.name_nl = "Rood"
        mock_color.name_pl = "Czerwony"
        mock_color.hex_code = "#FF0000"

        result = AdminAttributeService.attribute_to_dict(mock_color, "colors")

        assert result["pk"] == "Red"
        assert result["name_en"] == "Red"
        assert result["hex_code"] == "#FF0000"

    def test_attribute_to_dict_material(self):
        """Test attribute_to_dict for material."""
        mock_material = Mock()
        mock_material.name_en = "Cotton"
        mock_material.name_fr = "Coton"
        mock_material.name_de = "Baumwolle"
        mock_material.name_it = "Cotone"
        mock_material.name_es = "Algodon"
        mock_material.name_nl = "Katoen"
        mock_material.name_pl = "Bawelna"
        mock_material.vinted_id = 456

        result = AdminAttributeService.attribute_to_dict(mock_material, "materials")

        assert result["pk"] == "Cotton"
        assert result["name_en"] == "Cotton"
        assert result["vinted_id"] == 456

    def test_attribute_to_dict_unknown_type_raises_error(self):
        """Test attribute_to_dict raises ValueError for unknown type."""
        mock_item = Mock()

        with pytest.raises(ValueError, match="Unknown attribute type"):
            AdminAttributeService.attribute_to_dict(mock_item, "unknown")
