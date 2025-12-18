"""
Tests unitaires pour VintedProductConverter

Tests pour la construction des payloads API Vinted.

Business Rules Tested:
- Payload structure conforme à l'API Vinted
- item_attributes avec materials
- Dimensions pour hauts uniquement
- Format des photos assignées

Author: Claude
Date: 2025-12-18
"""

import pytest
from unittest.mock import Mock, patch
import uuid

from services.vinted.vinted_product_converter import VintedProductConverter


class TestBuildItemAttributes:
    """Tests pour _build_item_attributes."""

    def test_build_item_attributes_empty(self):
        """Test avec aucun attribut."""
        attrs = {}
        result = VintedProductConverter._build_item_attributes(attrs)
        assert result == []

    def test_build_item_attributes_no_materials(self):
        """Test avec material_ids vide."""
        attrs = {'material_ids': []}
        result = VintedProductConverter._build_item_attributes(attrs)
        assert result == []

    def test_build_item_attributes_single_material(self):
        """Test avec un seul matériau."""
        attrs = {'material_ids': [44]}
        result = VintedProductConverter._build_item_attributes(attrs)

        assert len(result) == 1
        assert result[0]['code'] == 'material'
        assert result[0]['ids'] == [44]

    def test_build_item_attributes_multiple_materials(self):
        """Test avec plusieurs matériaux."""
        attrs = {'material_ids': [44, 45, 303]}
        result = VintedProductConverter._build_item_attributes(attrs)

        assert len(result) == 1
        assert result[0]['code'] == 'material'
        assert result[0]['ids'] == [44, 45, 303]

    def test_build_item_attributes_format_matches_vinted(self):
        """Test que le format correspond exactement à Vinted."""
        attrs = {'material_ids': [468]}
        result = VintedProductConverter._build_item_attributes(attrs)

        # Format attendu par Vinted: [{"code": "material", "ids": [468]}]
        expected = [{"code": "material", "ids": [468]}]
        assert result == expected

    def test_build_item_attributes_ignores_other_keys(self):
        """Test que les autres clés sont ignorées."""
        attrs = {
            'material_ids': [44],
            'brand_id': 53,
            'color_id': 12,
            'random_key': 'value'
        }
        result = VintedProductConverter._build_item_attributes(attrs)

        assert len(result) == 1
        assert result[0]['code'] == 'material'


class TestGetDimensions:
    """Tests pour _get_dimensions."""

    def test_get_dimensions_for_tshirt(self):
        """Test dimensions pour T-shirt."""
        mock_product = Mock()
        mock_product.category = "T-shirt"
        mock_product.dim1 = 52
        mock_product.dim2 = 70

        width, length = VintedProductConverter._get_dimensions(mock_product, is_bottom=False)

        assert width == 52
        assert length == 70

    def test_get_dimensions_for_sweater(self):
        """Test dimensions pour Sweater."""
        mock_product = Mock()
        mock_product.category = "Sweater"
        mock_product.dim1 = 55
        mock_product.dim2 = 68

        width, length = VintedProductConverter._get_dimensions(mock_product, is_bottom=False)

        assert width == 55
        assert length == 68

    def test_no_dimensions_for_bottom(self):
        """Test pas de dimensions pour bas."""
        mock_product = Mock()
        mock_product.category = "Jeans"
        mock_product.dim1 = 80
        mock_product.dim2 = 100

        width, length = VintedProductConverter._get_dimensions(mock_product, is_bottom=True)

        assert width is None
        assert length is None

    def test_no_dimensions_for_jacket(self):
        """Test pas de dimensions pour veste (pas dans liste)."""
        mock_product = Mock()
        mock_product.category = "Jacket"
        mock_product.dim1 = 60
        mock_product.dim2 = 75

        width, length = VintedProductConverter._get_dimensions(mock_product, is_bottom=False)

        assert width is None
        assert length is None

    def test_dimensions_none_values(self):
        """Test avec dimensions None."""
        mock_product = Mock()
        mock_product.category = "T-shirt"
        mock_product.dim1 = None
        mock_product.dim2 = None

        width, length = VintedProductConverter._get_dimensions(mock_product, is_bottom=False)

        assert width is None
        assert length is None

    def test_dimensions_converted_to_int(self):
        """Test conversion en entier."""
        mock_product = Mock()
        mock_product.category = "T-shirt"
        mock_product.dim1 = 52.5
        mock_product.dim2 = 70.8

        width, length = VintedProductConverter._get_dimensions(mock_product, is_bottom=False)

        assert width == 52
        assert length == 70
        assert isinstance(width, int)
        assert isinstance(length, int)


class TestBuildCreatePayload:
    """Tests pour build_create_payload."""

    def test_build_create_payload_basic(self):
        """Test construction payload basique."""
        mock_product = Mock()
        mock_product.brand = "Levi's"
        mock_product.category = "Jeans"
        mock_product.dim1 = None
        mock_product.dim2 = None

        photo_ids = [123, 456]
        mapped_attrs = {
            'brand_id': 53,
            'color_id': 12,
            'condition_id': 2,
            'size_id': 207,
            'category_id': 1193,
            'is_bottom': True,
            'material_ids': [303]
        }

        payload = VintedProductConverter.build_create_payload(
            product=mock_product,
            photo_ids=photo_ids,
            mapped_attrs=mapped_attrs,
            prix_vinted=45.90,
            title="Levi's 501 Jean",
            description="Jean vintage"
        )

        # Verify structure
        assert 'item' in payload
        assert 'feedback_id' in payload
        assert 'push_up' in payload
        assert 'upload_session_id' in payload

        item = payload['item']
        assert item['title'] == "Levi's 501 Jean"
        assert item['description'] == "Jean vintage"
        assert item['brand_id'] == 53
        assert item['size_id'] == 207
        assert item['catalog_id'] == 1193
        assert item['status_id'] == 2
        assert item['color_ids'] == [12]
        assert item['price'] == 45.90
        assert item['currency'] == "EUR"

    def test_build_create_payload_with_materials(self):
        """Test payload avec item_attributes materials."""
        mock_product = Mock()
        mock_product.brand = "Nike"
        mock_product.category = "T-shirt"
        mock_product.dim1 = 52
        mock_product.dim2 = 70

        mapped_attrs = {
            'brand_id': 100,
            'color_id': 5,
            'condition_id': 3,
            'size_id': 210,
            'category_id': 1203,
            'is_bottom': False,
            'material_ids': [44, 45]  # Cotton + Polyester
        }

        payload = VintedProductConverter.build_create_payload(
            product=mock_product,
            photo_ids=[789],
            mapped_attrs=mapped_attrs,
            prix_vinted=25.90,
            title="Nike T-shirt",
            description="T-shirt sport"
        )

        item = payload['item']

        # Verify item_attributes contains materials
        assert item['item_attributes'] == [{"code": "material", "ids": [44, 45]}]

    def test_build_create_payload_empty_materials(self):
        """Test payload sans materials."""
        mock_product = Mock()
        mock_product.brand = "Nike"
        mock_product.category = "T-shirt"
        mock_product.dim1 = None
        mock_product.dim2 = None

        mapped_attrs = {
            'brand_id': 100,
            'color_id': 5,
            'condition_id': 3,
            'size_id': 210,
            'category_id': 1203,
            'is_bottom': False,
            'material_ids': []
        }

        payload = VintedProductConverter.build_create_payload(
            product=mock_product,
            photo_ids=[789],
            mapped_attrs=mapped_attrs,
            prix_vinted=25.90,
            title="Nike T-shirt",
            description="T-shirt sport"
        )

        item = payload['item']
        assert item['item_attributes'] == []

    def test_build_create_payload_photos_format(self):
        """Test format des photos assignées."""
        mock_product = Mock()
        mock_product.brand = None
        mock_product.category = "Jeans"
        mock_product.dim1 = None
        mock_product.dim2 = None

        photo_ids = [111, 222, 333]
        mapped_attrs = {
            'category_id': 1193,
            'is_bottom': True,
            'material_ids': []
        }

        payload = VintedProductConverter.build_create_payload(
            product=mock_product,
            photo_ids=photo_ids,
            mapped_attrs=mapped_attrs,
            prix_vinted=30.00,
            title="Jean",
            description="Description"
        )

        assigned_photos = payload['item']['assigned_photos']

        assert len(assigned_photos) == 3
        assert assigned_photos[0] == {"id": 111, "orientation": 0}
        assert assigned_photos[1] == {"id": 222, "orientation": 0}
        assert assigned_photos[2] == {"id": 333, "orientation": 0}

    def test_build_create_payload_with_dimensions(self):
        """Test payload avec dimensions pour haut."""
        mock_product = Mock()
        mock_product.brand = "Nike"
        mock_product.category = "T-shirt"
        mock_product.dim1 = 52
        mock_product.dim2 = 70

        mapped_attrs = {
            'brand_id': 100,
            'category_id': 1203,
            'is_bottom': False,
            'material_ids': []
        }

        payload = VintedProductConverter.build_create_payload(
            product=mock_product,
            photo_ids=[789],
            mapped_attrs=mapped_attrs,
            prix_vinted=25.90,
            title="Nike T-shirt",
            description="T-shirt sport"
        )

        item = payload['item']
        assert item['measurement_width'] == 52
        assert item['measurement_length'] == 70

    def test_build_create_payload_no_dimensions_for_bottom(self):
        """Test pas de dimensions pour bas."""
        mock_product = Mock()
        mock_product.brand = "Levi's"
        mock_product.category = "Jeans"
        mock_product.dim1 = 80
        mock_product.dim2 = 100

        mapped_attrs = {
            'brand_id': 53,
            'category_id': 1193,
            'is_bottom': True,
            'material_ids': []
        }

        payload = VintedProductConverter.build_create_payload(
            product=mock_product,
            photo_ids=[123],
            mapped_attrs=mapped_attrs,
            prix_vinted=45.90,
            title="Levi's Jean",
            description="Jean"
        )

        item = payload['item']
        assert item['measurement_width'] is None
        assert item['measurement_length'] is None

    def test_build_create_payload_unisex_detection(self):
        """Test détection is_unisex pour lunettes (category_id=98)."""
        mock_product = Mock()
        mock_product.brand = "Ray-Ban"
        mock_product.category = "Sunglasses"
        mock_product.dim1 = None
        mock_product.dim2 = None

        mapped_attrs = {
            'brand_id': 200,
            'category_id': 98,  # Lunettes = unisex
            'is_bottom': False,
            'material_ids': []
        }

        payload = VintedProductConverter.build_create_payload(
            product=mock_product,
            photo_ids=[123],
            mapped_attrs=mapped_attrs,
            prix_vinted=89.90,
            title="Ray-Ban Aviator",
            description="Lunettes"
        )

        assert payload['item']['is_unisex'] is True

    def test_build_create_payload_not_unisex(self):
        """Test is_unisex=False pour autres catégories."""
        mock_product = Mock()
        mock_product.brand = "Nike"
        mock_product.category = "T-shirt"
        mock_product.dim1 = None
        mock_product.dim2 = None

        mapped_attrs = {
            'category_id': 1203,
            'is_bottom': False,
            'material_ids': []
        }

        payload = VintedProductConverter.build_create_payload(
            product=mock_product,
            photo_ids=[123],
            mapped_attrs=mapped_attrs,
            prix_vinted=25.90,
            title="Nike T-shirt",
            description="T-shirt"
        )

        assert payload['item']['is_unisex'] is False

    def test_build_create_payload_price_rounded(self):
        """Test arrondi du prix à 2 décimales."""
        mock_product = Mock()
        mock_product.brand = None
        mock_product.category = "Jeans"
        mock_product.dim1 = None
        mock_product.dim2 = None

        mapped_attrs = {
            'category_id': 1193,
            'is_bottom': True,
            'material_ids': []
        }

        payload = VintedProductConverter.build_create_payload(
            product=mock_product,
            photo_ids=[123],
            mapped_attrs=mapped_attrs,
            prix_vinted=45.999,  # Should round to 46.00
            title="Jean",
            description="Description"
        )

        assert payload['item']['price'] == 46.0

    def test_build_create_payload_missing_category_raises(self):
        """Test erreur si category_id manquant."""
        mock_product = Mock()
        mock_product.brand = None
        mock_product.category = "Unknown"
        mock_product.dim1 = None
        mock_product.dim2 = None

        mapped_attrs = {
            'category_id': None,
            'is_bottom': False,
            'material_ids': []
        }

        with pytest.raises(ValueError) as exc_info:
            VintedProductConverter.build_create_payload(
                product=mock_product,
                photo_ids=[123],
                mapped_attrs=mapped_attrs,
                prix_vinted=25.90,
                title="Product",
                description="Description"
            )

        assert "category_id" in str(exc_info.value)

    def test_build_create_payload_uuid_format(self):
        """Test que temp_uuid et upload_session_id sont des UUIDs valides."""
        mock_product = Mock()
        mock_product.brand = None
        mock_product.category = "Jeans"
        mock_product.dim1 = None
        mock_product.dim2 = None

        mapped_attrs = {
            'category_id': 1193,
            'is_bottom': True,
            'material_ids': []
        }

        payload = VintedProductConverter.build_create_payload(
            product=mock_product,
            photo_ids=[123],
            mapped_attrs=mapped_attrs,
            prix_vinted=30.00,
            title="Jean",
            description="Description"
        )

        # Verify UUIDs are valid
        temp_uuid = payload['item']['temp_uuid']
        upload_session_id = payload['upload_session_id']

        # Should not raise
        uuid.UUID(temp_uuid)
        uuid.UUID(upload_session_id)


class TestBuildUpdatePayload:
    """Tests pour build_update_payload."""

    def test_build_update_payload_includes_id(self):
        """Test que le payload update inclut l'ID Vinted."""
        mock_product = Mock()
        mock_product.brand = "Levi's"
        mock_product.category = "Jeans"
        mock_product.dim1 = None
        mock_product.dim2 = None

        mock_vinted_product = Mock()
        mock_vinted_product.vinted_id = 999888777
        mock_vinted_product.image_ids_list = [123, 456]

        mapped_attrs = {
            'brand_id': 53,
            'category_id': 1193,
            'is_bottom': True,
            'material_ids': [303]
        }

        payload = VintedProductConverter.build_update_payload(
            product=mock_product,
            vinted_product=mock_vinted_product,
            mapped_attrs=mapped_attrs,
            prix_vinted=49.90,
            title="Levi's 501 Updated",
            description="Updated description"
        )

        assert payload['item']['id'] == 999888777

    def test_build_update_payload_with_materials(self):
        """Test que le payload update inclut les materials."""
        mock_product = Mock()
        mock_product.brand = "Nike"
        mock_product.category = "T-shirt"
        mock_product.dim1 = 52
        mock_product.dim2 = 70

        mock_vinted_product = Mock()
        mock_vinted_product.vinted_id = 123456
        mock_vinted_product.image_ids_list = [789]

        mapped_attrs = {
            'brand_id': 100,
            'category_id': 1203,
            'is_bottom': False,
            'material_ids': [44, 45]
        }

        payload = VintedProductConverter.build_update_payload(
            product=mock_product,
            vinted_product=mock_vinted_product,
            mapped_attrs=mapped_attrs,
            prix_vinted=25.90,
            title="Nike T-shirt",
            description="Description"
        )

        assert payload['item']['item_attributes'] == [{"code": "material", "ids": [44, 45]}]

    def test_build_update_payload_missing_vinted_id_raises(self):
        """Test erreur si vinted_id manquant."""
        mock_product = Mock()
        mock_product.brand = None
        mock_product.category = "Jeans"
        mock_product.dim1 = None
        mock_product.dim2 = None

        mock_vinted_product = Mock()
        mock_vinted_product.vinted_id = None

        mapped_attrs = {
            'category_id': 1193,
            'is_bottom': True,
            'material_ids': []
        }

        with pytest.raises(ValueError) as exc_info:
            VintedProductConverter.build_update_payload(
                product=mock_product,
                vinted_product=mock_vinted_product,
                mapped_attrs=mapped_attrs,
                prix_vinted=30.00,
                title="Jean",
                description="Description"
            )

        assert "vinted_id" in str(exc_info.value)


class TestBuildPriceUpdatePayload:
    """Tests pour build_price_update_payload."""

    def test_build_price_update_payload(self):
        """Test construction payload mise à jour prix."""
        payload = VintedProductConverter.build_price_update_payload(
            vinted_id=123456,
            new_price=35.90
        )

        assert payload['item']['id'] == 123456
        assert payload['item']['price'] == 35.90

    def test_build_price_update_payload_rounded(self):
        """Test arrondi du prix."""
        payload = VintedProductConverter.build_price_update_payload(
            vinted_id=123456,
            new_price=35.999
        )

        assert payload['item']['price'] == 36.0
