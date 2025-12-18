"""
Tests unitaires pour VintedProductValidator.

Couverture:
- Validation pour création (stock, prix, marque, catégorie, genre)
- Validation pour mise à jour
- Validation des attributs mappés
- Validation des images

Author: Claude
Date: 2025-12-10
"""

import pytest
from unittest.mock import Mock

from services.vinted.vinted_product_validator import VintedProductValidator


class TestValidateForCreation:
    """Tests pour la méthode validate_for_creation."""

    # Tests Stock
    def test_stock_missing_attribute(self):
        """Test produit sans attribut stock_quantity."""
        product = Mock(spec=[])

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is False
        assert "Stock non défini" in error

    def test_stock_is_none(self):
        """Test produit avec stock_quantity = None."""
        product = Mock()
        product.stock_quantity = None

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is False
        assert "Stock non défini" in error

    def test_stock_is_zero(self):
        """Test produit avec stock = 0."""
        product = Mock()
        product.stock_quantity = 0
        product.price = 25.0
        product.brand = "TestBrand"
        product.category = "TestCategory"
        product.gender = "M"

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is False
        assert "Stock insuffisant" in error
        assert "0" in error

    def test_stock_negative(self):
        """Test produit avec stock négatif."""
        product = Mock()
        product.stock_quantity = -5
        product.price = 25.0
        product.brand = "TestBrand"
        product.category = "TestCategory"
        product.gender = "M"

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is False
        assert "Stock insuffisant" in error

    # Tests Prix
    def test_price_missing_attribute(self):
        """Test produit sans attribut price."""
        product = Mock(spec=['stock_quantity'])
        product.stock_quantity = 1

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is False
        assert "Prix non défini" in error

    def test_price_is_none(self):
        """Test produit avec price = None."""
        product = Mock()
        product.stock_quantity = 1
        product.price = None

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is False
        assert "Prix non défini" in error

    def test_price_is_zero(self):
        """Test produit avec prix = 0."""
        product = Mock()
        product.stock_quantity = 1
        product.price = 0

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is False
        assert "Prix invalide" in error

    def test_price_negative(self):
        """Test produit avec prix négatif."""
        product = Mock()
        product.stock_quantity = 1
        product.price = -10.0

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is False
        assert "Prix invalide" in error

    def test_price_invalid_format(self):
        """Test produit avec prix au format invalide."""
        product = Mock()
        product.stock_quantity = 1
        product.price = "invalid"

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is False
        assert "Prix invalide" in error

    # Tests Marque
    def test_brand_missing_attribute(self):
        """Test produit sans attribut brand."""
        product = Mock(spec=['stock_quantity', 'price'])
        product.stock_quantity = 1
        product.price = 25.0

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is False
        assert "Marque manquante" in error

    def test_brand_is_none(self):
        """Test produit avec brand = None."""
        product = Mock()
        product.stock_quantity = 1
        product.price = 25.0
        product.brand = None

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is False
        assert "Marque manquante" in error

    def test_brand_is_empty(self):
        """Test produit avec marque vide."""
        product = Mock()
        product.stock_quantity = 1
        product.price = 25.0
        product.brand = ""

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is False
        assert "Marque manquante" in error

    # Tests Catégorie
    def test_category_missing_attribute(self):
        """Test produit sans attribut category."""
        product = Mock(spec=['stock_quantity', 'price', 'brand'])
        product.stock_quantity = 1
        product.price = 25.0
        product.brand = "TestBrand"

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is False
        assert "Catégorie manquante" in error

    def test_category_is_none(self):
        """Test produit avec category = None."""
        product = Mock()
        product.stock_quantity = 1
        product.price = 25.0
        product.brand = "TestBrand"
        product.category = None

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is False
        assert "Catégorie manquante" in error

    def test_category_is_empty(self):
        """Test produit avec catégorie vide."""
        product = Mock()
        product.stock_quantity = 1
        product.price = 25.0
        product.brand = "TestBrand"
        product.category = ""

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is False
        assert "Catégorie manquante" in error

    # Tests Genre
    def test_gender_missing_attribute(self):
        """Test produit sans attribut gender."""
        product = Mock(spec=['stock_quantity', 'price', 'brand', 'category'])
        product.stock_quantity = 1
        product.price = 25.0
        product.brand = "TestBrand"
        product.category = "TestCategory"

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is False
        assert "Genre manquant" in error

    def test_gender_is_none(self):
        """Test produit avec gender = None."""
        product = Mock()
        product.stock_quantity = 1
        product.price = 25.0
        product.brand = "TestBrand"
        product.category = "TestCategory"
        product.gender = None

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is False
        assert "Genre manquant" in error

    def test_gender_is_empty(self):
        """Test produit avec genre vide."""
        product = Mock()
        product.stock_quantity = 1
        product.price = 25.0
        product.brand = "TestBrand"
        product.category = "TestCategory"
        product.gender = ""

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is False
        assert "Genre manquant" in error

    # Tests Produit Valide
    def test_valid_product(self):
        """Test produit valide."""
        product = Mock()
        product.stock_quantity = 1
        product.price = 25.0
        product.brand = "Levi's"
        product.category = "Jeans"
        product.gender = "M"

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is True
        assert error is None

    def test_valid_product_high_values(self):
        """Test produit valide avec valeurs élevées."""
        product = Mock()
        product.stock_quantity = 100
        product.price = 500.00
        product.brand = "Gucci"
        product.category = "Dress"
        product.gender = "F"

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is True
        assert error is None

    def test_valid_product_decimal_price(self):
        """Test produit valide avec prix décimal."""
        product = Mock()
        product.stock_quantity = 1
        product.price = 25.99
        product.brand = "Nike"
        product.category = "Sneakers"
        product.gender = "U"

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is True
        assert error is None


class TestValidateForUpdate:
    """Tests pour la méthode validate_for_update."""

    def test_update_uses_same_validation(self):
        """Test que update utilise les mêmes règles que create."""
        product = Mock()
        product.stock_quantity = 0
        product.price = 25.0
        product.brand = "TestBrand"
        product.category = "TestCategory"
        product.gender = "M"

        is_valid, error = VintedProductValidator.validate_for_update(product)

        # Stock = 0 devrait échouer
        assert is_valid is False
        assert "Stock insuffisant" in error

    def test_update_valid_product(self):
        """Test update produit valide."""
        product = Mock()
        product.stock_quantity = 5
        product.price = 30.0
        product.brand = "Adidas"
        product.category = "T-shirt"
        product.gender = "M"

        is_valid, error = VintedProductValidator.validate_for_update(product)

        assert is_valid is True
        assert error is None


class TestValidateMappedAttributes:
    """Tests pour la méthode validate_mapped_attributes."""

    def test_all_required_attributes_present(self):
        """Test avec tous les attributs requis."""
        mapped = {
            'brand_id': 123,
            'color_id': 12,
            'condition_id': 1,
            'size_id': 207,
        }

        is_valid, error = VintedProductValidator.validate_mapped_attributes(mapped)

        assert is_valid is True
        assert error is None

    def test_missing_brand_id(self):
        """Test sans brand_id."""
        mapped = {
            'brand_id': None,
            'color_id': 12,
            'condition_id': 1,
            'size_id': 207,
        }

        is_valid, error = VintedProductValidator.validate_mapped_attributes(mapped)

        assert is_valid is False
        assert "brand_id" in error

    def test_missing_color_id(self):
        """Test sans color_id."""
        mapped = {
            'brand_id': 123,
            'color_id': None,
            'condition_id': 1,
            'size_id': 207,
        }

        is_valid, error = VintedProductValidator.validate_mapped_attributes(mapped)

        assert is_valid is False
        assert "color_id" in error

    def test_missing_condition_id(self):
        """Test sans condition_id."""
        mapped = {
            'brand_id': 123,
            'color_id': 12,
            'condition_id': None,
            'size_id': 207,
        }

        is_valid, error = VintedProductValidator.validate_mapped_attributes(mapped)

        assert is_valid is False
        assert "condition_id" in error

    def test_missing_size_id(self):
        """Test sans size_id."""
        mapped = {
            'brand_id': 123,
            'color_id': 12,
            'condition_id': 1,
            'size_id': None,
        }

        is_valid, error = VintedProductValidator.validate_mapped_attributes(mapped)

        assert is_valid is False
        assert "size_id" in error

    def test_missing_multiple_attributes(self):
        """Test avec plusieurs attributs manquants."""
        mapped = {
            'brand_id': 123,
            'color_id': None,
            'condition_id': None,
            'size_id': 207,
        }

        is_valid, error = VintedProductValidator.validate_mapped_attributes(mapped)

        assert is_valid is False
        assert "color_id" in error
        assert "condition_id" in error

    def test_size_not_required_for_sunglasses(self):
        """Test que size_id n'est pas requis pour les lunettes (category_id=98)."""
        mapped = {
            'brand_id': 123,
            'color_id': 12,
            'condition_id': 1,
            'category_id': 98,  # Lunettes
            'size_id': None,
        }

        is_valid, error = VintedProductValidator.validate_mapped_attributes(mapped)

        assert is_valid is True
        assert error is None

    def test_with_product_id_for_logging(self):
        """Test avec product_id pour logging."""
        mapped = {
            'brand_id': None,
            'color_id': 12,
            'condition_id': 1,
            'size_id': 207,
        }

        is_valid, error = VintedProductValidator.validate_mapped_attributes(
            mapped, product_id=12345
        )

        assert is_valid is False
        # product_id est juste pour les logs, pas d'impact sur le résultat


class TestValidateImages:
    """Tests pour la méthode validate_images."""

    def test_no_images(self):
        """Test sans images."""
        is_valid, error = VintedProductValidator.validate_images([])

        assert is_valid is False
        assert "Aucune image" in error

    def test_none_images(self):
        """Test avec None."""
        is_valid, error = VintedProductValidator.validate_images(None)

        assert is_valid is False
        assert "Aucune image" in error

    def test_one_image(self):
        """Test avec une image."""
        is_valid, error = VintedProductValidator.validate_images([123])

        assert is_valid is True
        assert error is None

    def test_multiple_images(self):
        """Test avec plusieurs images."""
        is_valid, error = VintedProductValidator.validate_images([123, 456, 789])

        assert is_valid is True
        assert error is None

    def test_max_images(self):
        """Test avec le maximum d'images (20)."""
        is_valid, error = VintedProductValidator.validate_images(list(range(20)))

        assert is_valid is True
        assert error is None

    def test_too_many_images(self):
        """Test avec trop d'images (21)."""
        is_valid, error = VintedProductValidator.validate_images(list(range(21)))

        assert is_valid is False
        assert "Trop d'images" in error
        assert "21" in error
        assert "max 20" in error

    def test_way_too_many_images(self):
        """Test avec beaucoup trop d'images."""
        is_valid, error = VintedProductValidator.validate_images(list(range(100)))

        assert is_valid is False
        assert "Trop d'images" in error


class TestValidationEdgeCases:
    """Tests pour les cas limites."""

    def test_string_price_convertible(self):
        """Test prix sous forme de string convertible."""
        product = Mock()
        product.stock_quantity = 1
        product.price = "25.50"  # String mais convertible
        product.brand = "TestBrand"
        product.category = "TestCategory"
        product.gender = "M"

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is True

    def test_decimal_price(self):
        """Test prix Decimal."""
        from decimal import Decimal
        product = Mock()
        product.stock_quantity = 1
        product.price = Decimal("25.50")
        product.brand = "TestBrand"
        product.category = "TestCategory"
        product.gender = "M"

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is True

    def test_integer_stock(self):
        """Test stock integer."""
        product = Mock()
        product.stock_quantity = 10
        product.price = 25.0
        product.brand = "TestBrand"
        product.category = "TestCategory"
        product.gender = "M"

        is_valid, error = VintedProductValidator.validate_for_creation(product)

        assert is_valid is True
