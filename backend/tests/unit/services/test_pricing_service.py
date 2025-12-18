"""
Tests unitaires pour PricingService.

Couverture:
- Calcul de prix avec tous les paramètres
- Coefficients de rareté
- Coefficients de qualité
- Prix minimum
- Arrondi à 0.50€
- Cas limites

Author: Claude
Date: 2025-12-10
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch

from services.pricing_service import PricingService


class TestPricingServiceCoefficients:
    """Tests pour les constantes et coefficients."""

    def test_rarity_coefficients_exist(self):
        """Vérifie que les coefficients de rareté sont définis."""
        assert "Rare" in PricingService.RARITY_COEFFICIENTS
        assert "Vintage" in PricingService.RARITY_COEFFICIENTS
        assert "Common" in PricingService.RARITY_COEFFICIENTS
        assert "Standard" in PricingService.RARITY_COEFFICIENTS

    def test_rarity_coefficients_values(self):
        """Vérifie les valeurs des coefficients de rareté."""
        assert PricingService.RARITY_COEFFICIENTS["Rare"] == 1.3
        assert PricingService.RARITY_COEFFICIENTS["Vintage"] == 1.2
        assert PricingService.RARITY_COEFFICIENTS["Common"] == 1.0
        assert PricingService.RARITY_COEFFICIENTS["Standard"] == 1.0

    def test_quality_coefficients_exist(self):
        """Vérifie que les coefficients de qualité sont définis."""
        assert "Premium" in PricingService.QUALITY_COEFFICIENTS
        assert "Good" in PricingService.QUALITY_COEFFICIENTS
        assert "Average" in PricingService.QUALITY_COEFFICIENTS
        assert "Standard" in PricingService.QUALITY_COEFFICIENTS

    def test_quality_coefficients_values(self):
        """Vérifie les valeurs des coefficients de qualité."""
        assert PricingService.QUALITY_COEFFICIENTS["Premium"] == 1.2
        assert PricingService.QUALITY_COEFFICIENTS["Good"] == 1.0
        assert PricingService.QUALITY_COEFFICIENTS["Average"] == 0.8
        assert PricingService.QUALITY_COEFFICIENTS["Standard"] == 1.0

    def test_constants(self):
        """Vérifie les constantes."""
        assert PricingService.DEFAULT_BASE_PRICE == Decimal("30.00")
        assert PricingService.MIN_PRICE == Decimal("5.00")
        assert PricingService.ROUND_TO == Decimal("0.50")


class TestRoundToNearest:
    """Tests pour la méthode _round_to_nearest."""

    def test_round_up_to_050(self):
        """Test arrondi vers 0.50."""
        result = PricingService._round_to_nearest(Decimal("24.30"), Decimal("0.50"))
        assert result == Decimal("24.50")

    def test_round_to_nearest_050(self):
        """Test arrondi vers 0.50 le plus proche (banker's rounding)."""
        # 24.70 / 0.50 = 49.4 -> rounds to 49 -> 49 * 0.50 = 24.50
        result = PricingService._round_to_nearest(Decimal("24.70"), Decimal("0.50"))
        assert result == Decimal("24.50")

    def test_round_exact_050(self):
        """Test valeur exacte 0.50."""
        result = PricingService._round_to_nearest(Decimal("24.50"), Decimal("0.50"))
        assert result == Decimal("24.50")

    def test_round_exact_100(self):
        """Test valeur exacte entière."""
        result = PricingService._round_to_nearest(Decimal("25.00"), Decimal("0.50"))
        assert result == Decimal("25.00")

    def test_round_small_value(self):
        """Test arrondi petite valeur."""
        result = PricingService._round_to_nearest(Decimal("0.10"), Decimal("0.50"))
        assert result == Decimal("0.00")

    def test_round_large_value(self):
        """Test arrondi grande valeur."""
        result = PricingService._round_to_nearest(Decimal("999.99"), Decimal("0.50"))
        assert result == Decimal("1000.00")


class TestGetBasePrice:
    """Tests pour la méthode _get_base_price."""

    def test_returns_default_when_no_brand(self):
        """Retourne prix par défaut si pas de marque."""
        mock_db = Mock()
        result = PricingService._get_base_price(mock_db, None, "Jeans")
        assert result == PricingService.DEFAULT_BASE_PRICE

    def test_returns_default_when_not_found(self):
        """Retourne prix par défaut si non trouvé en DB."""
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = PricingService._get_base_price(mock_db, "UnknownBrand", "Jeans")
        assert result == PricingService.DEFAULT_BASE_PRICE

    def test_returns_db_price_when_found(self):
        """Retourne prix DB si trouvé."""
        mock_db = Mock()
        mock_query = Mock()
        mock_clothing_price = Mock()
        mock_clothing_price.base_price = Decimal("45.00")

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_clothing_price

        result = PricingService._get_base_price(mock_db, "Levi's", "Jeans")
        assert result == Decimal("45.00")


class TestGetConditionCoefficient:
    """Tests pour la méthode _get_condition_coefficient."""

    def test_returns_coefficient_from_db(self):
        """Retourne coefficient depuis DB."""
        mock_db = Mock()
        mock_query = Mock()
        mock_condition = Mock()
        mock_condition.coefficient = 0.9

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_condition

        result = PricingService._get_condition_coefficient(mock_db, "GOOD")
        assert result == 0.9

    def test_returns_default_when_not_found(self):
        """Retourne 1.0 si condition non trouvée."""
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = PricingService._get_condition_coefficient(mock_db, "UNKNOWN")
        assert result == 1.0

    def test_returns_default_when_no_coefficient(self):
        """Retourne 1.0 si coefficient None."""
        mock_db = Mock()
        mock_query = Mock()
        mock_condition = Mock()
        mock_condition.coefficient = None

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_condition

        result = PricingService._get_condition_coefficient(mock_db, "GOOD")
        assert result == 1.0


class TestCalculatePrice:
    """Tests pour la méthode calculate_price."""

    @patch.object(PricingService, '_get_base_price')
    @patch.object(PricingService, '_get_condition_coefficient')
    def test_basic_calculation(self, mock_condition, mock_base):
        """Test calcul basique sans rareté ni qualité."""
        mock_db = Mock()
        mock_base.return_value = Decimal("30.00")
        mock_condition.return_value = 1.0

        result = PricingService.calculate_price(
            db=mock_db,
            brand="TestBrand",
            category="Jeans",
            condition="EXCELLENT"
        )

        # 30 * 1.0 * 1.0 * 1.0 = 30 → arrondi 30.00
        assert result == Decimal("30.00")

    @patch.object(PricingService, '_get_base_price')
    @patch.object(PricingService, '_get_condition_coefficient')
    def test_calculation_with_rarity_rare(self, mock_condition, mock_base):
        """Test calcul avec rareté Rare (+30%)."""
        mock_db = Mock()
        mock_base.return_value = Decimal("30.00")
        mock_condition.return_value = 1.0

        result = PricingService.calculate_price(
            db=mock_db,
            brand="TestBrand",
            category="Jeans",
            condition="EXCELLENT",
            rarity="Rare"
        )

        # 30 * 1.0 * 1.3 * 1.0 = 39 → arrondi 39.00
        assert result == Decimal("39.00")

    @patch.object(PricingService, '_get_base_price')
    @patch.object(PricingService, '_get_condition_coefficient')
    def test_calculation_with_rarity_vintage(self, mock_condition, mock_base):
        """Test calcul avec rareté Vintage (+20%)."""
        mock_db = Mock()
        mock_base.return_value = Decimal("30.00")
        mock_condition.return_value = 1.0

        result = PricingService.calculate_price(
            db=mock_db,
            brand="TestBrand",
            category="Jeans",
            condition="EXCELLENT",
            rarity="Vintage"
        )

        # 30 * 1.0 * 1.2 * 1.0 = 36 → arrondi 36.00
        assert result == Decimal("36.00")

    @patch.object(PricingService, '_get_base_price')
    @patch.object(PricingService, '_get_condition_coefficient')
    def test_calculation_with_quality_premium(self, mock_condition, mock_base):
        """Test calcul avec qualité Premium (+20%)."""
        mock_db = Mock()
        mock_base.return_value = Decimal("30.00")
        mock_condition.return_value = 1.0

        result = PricingService.calculate_price(
            db=mock_db,
            brand="TestBrand",
            category="Jeans",
            condition="EXCELLENT",
            quality="Premium"
        )

        # 30 * 1.0 * 1.0 * 1.2 = 36 → arrondi 36.00
        assert result == Decimal("36.00")

    @patch.object(PricingService, '_get_base_price')
    @patch.object(PricingService, '_get_condition_coefficient')
    def test_calculation_with_quality_average(self, mock_condition, mock_base):
        """Test calcul avec qualité Average (-20%)."""
        mock_db = Mock()
        mock_base.return_value = Decimal("30.00")
        mock_condition.return_value = 1.0

        result = PricingService.calculate_price(
            db=mock_db,
            brand="TestBrand",
            category="Jeans",
            condition="EXCELLENT",
            quality="Average"
        )

        # 30 * 1.0 * 1.0 * 0.8 = 24 → arrondi 24.00
        assert result == Decimal("24.00")

    @patch.object(PricingService, '_get_base_price')
    @patch.object(PricingService, '_get_condition_coefficient')
    def test_calculation_with_all_factors(self, mock_condition, mock_base):
        """Test calcul avec tous les facteurs."""
        mock_db = Mock()
        mock_base.return_value = Decimal("80.00")
        mock_condition.return_value = 0.9

        result = PricingService.calculate_price(
            db=mock_db,
            brand="Diesel",
            category="Jeans",
            condition="GOOD",
            rarity="Vintage",
            quality="Premium"
        )

        # 80 * 0.9 * 1.2 * 1.2 = 103.68 / 0.50 = 207.36 → rounds to 207 → 103.50
        assert result == Decimal("103.50")

    @patch.object(PricingService, '_get_base_price')
    @patch.object(PricingService, '_get_condition_coefficient')
    def test_minimum_price_enforcement(self, mock_condition, mock_base):
        """Test que le prix minimum est appliqué."""
        mock_db = Mock()
        mock_base.return_value = Decimal("2.00")
        mock_condition.return_value = 0.5

        result = PricingService.calculate_price(
            db=mock_db,
            brand="CheapBrand",
            category="T-shirt",
            condition="POOR",
            quality="Average"
        )

        # 2 * 0.5 * 1.0 * 0.8 = 0.80 → min 5.00
        assert result == Decimal("5.00")

    @patch.object(PricingService, '_get_base_price')
    @patch.object(PricingService, '_get_condition_coefficient')
    def test_rounding_to_half_euro(self, mock_condition, mock_base):
        """Test arrondi à 0.50€."""
        mock_db = Mock()
        mock_base.return_value = Decimal("27.00")
        mock_condition.return_value = 1.0

        result = PricingService.calculate_price(
            db=mock_db,
            brand="TestBrand",
            category="Jeans",
            condition="EXCELLENT"
        )

        # 27 * 1.0 * 1.0 * 1.0 = 27 → arrondi 27.00
        assert result == Decimal("27.00")

    @patch.object(PricingService, '_get_base_price')
    @patch.object(PricingService, '_get_condition_coefficient')
    def test_unknown_rarity_defaults_to_standard(self, mock_condition, mock_base):
        """Test rareté inconnue utilise Standard (1.0)."""
        mock_db = Mock()
        mock_base.return_value = Decimal("30.00")
        mock_condition.return_value = 1.0

        result = PricingService.calculate_price(
            db=mock_db,
            brand="TestBrand",
            category="Jeans",
            condition="EXCELLENT",
            rarity="UnknownRarity"
        )

        # 30 * 1.0 * 1.0 * 1.0 = 30 → arrondi 30.00
        assert result == Decimal("30.00")

    @patch.object(PricingService, '_get_base_price')
    @patch.object(PricingService, '_get_condition_coefficient')
    def test_unknown_quality_defaults_to_standard(self, mock_condition, mock_base):
        """Test qualité inconnue utilise Standard (1.0)."""
        mock_db = Mock()
        mock_base.return_value = Decimal("30.00")
        mock_condition.return_value = 1.0

        result = PricingService.calculate_price(
            db=mock_db,
            brand="TestBrand",
            category="Jeans",
            condition="EXCELLENT",
            quality="UnknownQuality"
        )

        # 30 * 1.0 * 1.0 * 1.0 = 30 → arrondi 30.00
        assert result == Decimal("30.00")
