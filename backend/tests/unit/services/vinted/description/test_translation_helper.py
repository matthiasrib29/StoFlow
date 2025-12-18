"""
Tests for TranslationHelper

Tests the translation functionality for Vinted descriptions.
"""
import pytest
from services.vinted.description.translation_helper import TranslationHelper


class TestTranslateCategory:
    """Tests for category translation."""

    def test_translate_known_categories(self):
        """Test translation of known categories."""
        translations = {
            "Jeans": "Jean",
            "Jacket": "Veste",
            "Coat": "Manteau",
            "Shirt": "Chemise",
            "T-shirt": "T-shirt",
            "Sweatshirt": "Sweat",
            "Pants": "Pantalon",
            "Shorts": "Short",
            "Skirt": "Jupe",
            "Dress": "Robe",
            "Sweater": "Pull",
            "Shoes": "Chaussures",
            "Bag": "Sac",
            "Sunglasses": "Lunettes de soleil",
        }

        for english, french in translations.items():
            assert TranslationHelper.translate_category(english) == french

    def test_unknown_category_returns_original(self):
        """Test that unknown category returns the original string."""
        assert TranslationHelper.translate_category("UnknownCategory") == "UnknownCategory"


class TestTranslateColor:
    """Tests for color translation."""

    def test_translate_known_colors(self):
        """Test translation of known colors."""
        translations = {
            "Blue": "Bleu",
            "Red": "Rouge",
            "Green": "Vert",
            "Black": "Noir",
            "White": "Blanc",
            "Grey": "Gris",
            "Gray": "Gris",
            "Brown": "Marron",
            "Yellow": "Jaune",
            "Pink": "Rose",
            "Purple": "Violet",
            "Navy": "Bleu marine",
            "Burgundy": "Bordeaux",
        }

        for english, french in translations.items():
            assert TranslationHelper.translate_color(english) == french

    def test_unknown_color_returns_original(self):
        """Test that unknown color returns the original string."""
        assert TranslationHelper.translate_color("Turquoise") == "Turquoise"


class TestConditionText:
    """Tests for condition text methods."""

    def test_get_condition_text(self):
        """Test getting condition display text."""
        conditions = {
            "EXCELLENT": "Très bon état",
            "GOOD": "Bon état",
            "FAIR": "État correct",
            "POOR": "À rénover",
            "NEW": "Neuf",
        }

        for condition, expected_text in conditions.items():
            assert TranslationHelper.get_condition_text(condition) == expected_text

    def test_get_condition_text_case_insensitive(self):
        """Test that condition text is case insensitive."""
        assert TranslationHelper.get_condition_text("excellent") == "Très bon état"
        assert TranslationHelper.get_condition_text("EXCELLENT") == "Très bon état"
        assert TranslationHelper.get_condition_text("Excellent") == "Très bon état"

    def test_get_condition_default_text(self):
        """Test getting default condition description."""
        assert "Très peu porté" in TranslationHelper.get_condition_default_text("EXCELLENT")
        assert "signes d'usure" in TranslationHelper.get_condition_default_text("GOOD")
        assert "réparations" in TranslationHelper.get_condition_default_text("POOR")

    def test_get_condition_default_text_returns_none_for_unknown(self):
        """Test that unknown condition returns None for default text."""
        assert TranslationHelper.get_condition_default_text("UNKNOWN") is None


class TestDecadeFormatting:
    """Tests for decade formatting methods."""

    def test_format_decade_fr_full_year(self):
        """Test formatting full year decades."""
        assert TranslationHelper.format_decade_fr("1990s") == "Vintage 90s"
        assert TranslationHelper.format_decade_fr("1980s") == "Vintage 80s"
        assert TranslationHelper.format_decade_fr("1970s") == "Vintage 70s"

    def test_format_decade_fr_short_year(self):
        """Test formatting short year decades."""
        assert TranslationHelper.format_decade_fr("90s") == "Vintage 90s"
        assert TranslationHelper.format_decade_fr("80s") == "Vintage 80s"

    def test_format_decade_fr_year_only(self):
        """Test formatting year only (no 's')."""
        assert TranslationHelper.format_decade_fr("1990") == "Vintage 90s"
        assert TranslationHelper.format_decade_fr("1985") == "Vintage 85s"  # Takes last 2 digits

    def test_format_decade_fr_returns_none_for_invalid(self):
        """Test that invalid decade returns None."""
        assert TranslationHelper.format_decade_fr("") is None
        assert TranslationHelper.format_decade_fr(None) is None
        assert TranslationHelper.format_decade_fr("invalid") is None

    def test_normalize_decade(self):
        """Test decade normalization for hashtag matching."""
        assert TranslationHelper.normalize_decade("1990s") == "90s"
        assert TranslationHelper.normalize_decade("90s") == "90s"
        assert TranslationHelper.normalize_decade("1980") == "80s"

    def test_normalize_decade_returns_empty_for_invalid(self):
        """Test that invalid input returns empty string."""
        assert TranslationHelper.normalize_decade("") == ""
        assert TranslationHelper.normalize_decade(None) == ""
        assert TranslationHelper.normalize_decade("no-numbers") == ""
