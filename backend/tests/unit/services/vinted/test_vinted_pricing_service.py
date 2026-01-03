"""
Tests unitaires pour VintedPricingService.

Couverture:
- Coefficient Vinted (+10%)
- Arrondi psychologique x.90
- Prix minimum 1.00€
- Calcul complet avec PricingService
- Calcul direct (sans PricingService)

Author: Claude
Date: 2025-12-10
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch

from services.vinted.vinted_pricing_service import VintedPricingService


class TestConstants:
    """Tests pour les constantes."""

    def test_vinted_markup(self):
        """Vérifie le coefficient +10%."""
        assert VintedPricingService.VINTED_MARKUP == Decimal("1.10")

    def test_min_vinted_price(self):
        """Vérifie le prix minimum 1.00€."""
        assert VintedPricingService.MIN_VINTED_PRICE == Decimal("1.00")


class TestRoundToPsychological:
    """Tests pour la méthode _round_to_psychological."""

    def test_round_normal_price(self):
        """Test arrondi prix normal."""
        result = VintedPricingService._round_to_psychological(Decimal("27.83"))
        assert result == Decimal("27.90")

    def test_round_half_price(self):
        """Test arrondi prix avec .50."""
        result = VintedPricingService._round_to_psychological(Decimal("49.50"))
        assert result == Decimal("49.90")

    def test_round_integer_price(self):
        """Test arrondi prix entier."""
        result = VintedPricingService._round_to_psychological(Decimal("20.00"))
        assert result == Decimal("20.90")

    def test_round_high_decimals(self):
        """Test arrondi avec beaucoup de décimales."""
        result = VintedPricingService._round_to_psychological(Decimal("35.999"))
        assert result == Decimal("35.90")

    def test_round_low_price(self):
        """Test arrondi petit prix."""
        result = VintedPricingService._round_to_psychological(Decimal("1.25"))
        assert result == Decimal("1.90")

    def test_round_very_low_price(self):
        """Test arrondi très petit prix."""
        result = VintedPricingService._round_to_psychological(Decimal("0.55"))
        assert result == Decimal("0.90")

    def test_round_large_price(self):
        """Test arrondi grand prix."""
        result = VintedPricingService._round_to_psychological(Decimal("199.99"))
        assert result == Decimal("199.90")

    def test_round_already_90(self):
        """Test prix déjà à .90."""
        result = VintedPricingService._round_to_psychological(Decimal("25.90"))
        assert result == Decimal("25.90")


class TestCalculatePriceWithoutBase:
    """Tests pour la méthode calculate_price_without_base."""

    def test_basic_calculation(self):
        """Test calcul basique (25.00 → 27.90)."""
        result = VintedPricingService.calculate_price_without_base(Decimal("25.00"))
        # 25.00 * 1.10 = 27.50 → 27.90
        assert result == Decimal("27.90")

    def test_calculation_50_euros(self):
        """Test calcul 50€ (50.00 → 55.90)."""
        result = VintedPricingService.calculate_price_without_base(Decimal("50.00"))
        # 50.00 * 1.10 = 55.00 → 55.90
        assert result == Decimal("55.90")

    def test_calculation_100_euros(self):
        """Test calcul 100€."""
        result = VintedPricingService.calculate_price_without_base(Decimal("100.00"))
        # 100.00 * 1.10 = 110.00 → 110.90
        assert result == Decimal("110.90")

    def test_calculation_small_price(self):
        """Test calcul petit prix."""
        result = VintedPricingService.calculate_price_without_base(Decimal("5.00"))
        # 5.00 * 1.10 = 5.50 → 5.90
        assert result == Decimal("5.90")

    def test_calculation_with_decimals(self):
        """Test calcul avec décimales."""
        result = VintedPricingService.calculate_price_without_base(Decimal("45.50"))
        # 45.50 * 1.10 = 50.05 → 50.90
        assert result == Decimal("50.90")


class TestCalculateVintedPrice:
    """Tests pour la méthode calculate_vinted_price."""

    @patch('services.vinted.vinted_pricing_service.PricingService')
    def test_full_calculation(self, mock_pricing_service):
        """Test calcul complet avec PricingService."""
        mock_db = Mock()
        mock_product = Mock()
        mock_product.brand = "Levi's"
        mock_product.category = "Jeans"
        mock_product.condition = 8
        mock_product.rarity = None
        mock_product.quality = None

        # PricingService retourne 30.00€
        mock_pricing_service.calculate_price.return_value = Decimal("30.00")

        result = VintedPricingService.calculate_vinted_price(mock_db, mock_product)

        # 30.00 * 1.10 = 33.00 → 33.90
        assert result == Decimal("33.90")

    @patch('services.vinted.vinted_pricing_service.PricingService')
    def test_calculation_with_rarity(self, mock_pricing_service):
        """Test calcul avec rareté."""
        mock_db = Mock()
        mock_product = Mock()
        mock_product.brand = "Diesel"
        mock_product.category = "Jeans"
        mock_product.condition = 7
        mock_product.rarity = "Vintage"
        mock_product.quality = None

        # PricingService retourne 50.00€ (avec coefficient rareté)
        mock_pricing_service.calculate_price.return_value = Decimal("50.00")

        result = VintedPricingService.calculate_vinted_price(mock_db, mock_product)

        # 50.00 * 1.10 = 55.00 → 55.90
        assert result == Decimal("55.90")

    @patch('services.vinted.vinted_pricing_service.PricingService')
    def test_minimum_price_enforced(self, mock_pricing_service):
        """Test que le prix minimum est appliqué."""
        mock_db = Mock()
        mock_product = Mock()
        mock_product.brand = "NoName"
        mock_product.category = "T-shirt"
        mock_product.condition = 5
        mock_product.rarity = None
        mock_product.quality = None

        # PricingService retourne 0.50€ (très bas)
        mock_pricing_service.calculate_price.return_value = Decimal("0.50")

        # Doit lever une ValueError car 0.50 * 1.10 = 0.55 → 0.90 < 1.00
        with pytest.raises(ValueError) as exc_info:
            VintedPricingService.calculate_vinted_price(mock_db, mock_product)

        assert "minimum Vinted" in str(exc_info.value)
        assert "1.00€" in str(exc_info.value)

    @patch('services.vinted.vinted_pricing_service.PricingService')
    def test_minimum_price_edge_case(self, mock_pricing_service):
        """Test cas limite prix minimum."""
        mock_db = Mock()
        mock_product = Mock()
        mock_product.brand = "Budget"
        mock_product.category = "T-shirt"
        mock_product.condition = 6
        mock_product.rarity = None
        mock_product.quality = None

        # PricingService retourne 1.00€
        mock_pricing_service.calculate_price.return_value = Decimal("1.00")

        result = VintedPricingService.calculate_vinted_price(mock_db, mock_product)

        # 1.00 * 1.10 = 1.10 → 1.90 >= 1.00 OK
        assert result == Decimal("1.90")

    @patch('services.vinted.vinted_pricing_service.PricingService')
    def test_pricing_service_called_correctly(self, mock_pricing_service):
        """Test que PricingService est appelé avec les bons paramètres."""
        mock_db = Mock()
        mock_product = Mock()
        mock_product.brand = "TestBrand"
        mock_product.category = "TestCategory"
        mock_product.condition = 8
        mock_product.rarity = "Rare"
        mock_product.quality = "Premium"

        mock_pricing_service.calculate_price.return_value = Decimal("100.00")

        VintedPricingService.calculate_vinted_price(mock_db, mock_product)

        mock_pricing_service.calculate_price.assert_called_once_with(
            db=mock_db,
            brand="TestBrand",
            category="TestCategory",
            condition=8,
            rarity="Rare",
            quality="Premium"
        )


class TestCalculateVintedPriceWithExamples:
    """Tests avec les exemples de la documentation."""

    @patch('services.vinted.vinted_pricing_service.PricingService')
    def test_example_45_euros_base(self, mock_pricing_service):
        """Test exemple: 45.00€ base → 49.90€."""
        mock_db = Mock()
        mock_product = Mock()
        mock_product.brand = "Levi's"
        mock_product.category = "Jeans"
        mock_product.condition = 8
        mock_product.rarity = None
        mock_product.quality = None

        mock_pricing_service.calculate_price.return_value = Decimal("45.00")

        result = VintedPricingService.calculate_vinted_price(mock_db, mock_product)

        # 45.00 * 1.10 = 49.50 → 49.90
        assert result == Decimal("49.90")

    @patch('services.vinted.vinted_pricing_service.PricingService')
    def test_multiple_price_points(self, mock_pricing_service):
        """Test plusieurs points de prix."""
        mock_db = Mock()
        mock_product = Mock()
        mock_product.brand = "Test"
        mock_product.category = "Test"
        mock_product.condition = 7
        mock_product.rarity = None
        mock_product.quality = None

        test_cases = [
            (Decimal("10.00"), Decimal("11.90")),   # 10*1.1=11 → 11.90
            (Decimal("20.00"), Decimal("22.90")),   # 20*1.1=22 → 22.90
            (Decimal("35.00"), Decimal("38.90")),   # 35*1.1=38.5 → 38.90
            (Decimal("75.00"), Decimal("82.90")),   # 75*1.1=82.5 → 82.90
            (Decimal("150.00"), Decimal("165.90")), # 150*1.1=165 → 165.90
        ]

        for base_price, expected in test_cases:
            mock_pricing_service.calculate_price.return_value = base_price
            result = VintedPricingService.calculate_vinted_price(mock_db, mock_product)
            assert result == expected, f"Base {base_price} should give {expected}, got {result}"
