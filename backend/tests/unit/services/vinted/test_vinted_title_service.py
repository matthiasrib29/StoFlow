"""
Tests unitaires pour VintedTitleService.

Couverture:
- Extraction des attributs
- Construction du suffixe (location + ID)
- Construction du titre avec priorité des attributs
- Limite de 100 caractères
- Title Case et normalisation majuscules
- Formatage des décennies
- Mapping des conditions

Author: Claude
Date: 2025-12-10
"""

import pytest
from unittest.mock import Mock, MagicMock

from services.vinted.vinted_title_service import VintedTitleService, MAX_TITLE_LENGTH


class TestConstants:
    """Tests pour les constantes."""

    def test_max_title_length(self):
        """Vérifie la limite de 100 caractères."""
        assert MAX_TITLE_LENGTH == 100

    def test_priority_order_exists(self):
        """Vérifie l'ordre de priorité des attributs."""
        assert 'brand' in VintedTitleService.PRIORITY_ORDER
        assert 'category' in VintedTitleService.PRIORITY_ORDER
        assert 'size' in VintedTitleService.PRIORITY_ORDER
        assert 'condition' in VintedTitleService.PRIORITY_ORDER

    def test_priority_order_brand_first(self):
        """Vérifie que la marque est en première position."""
        assert VintedTitleService.PRIORITY_ORDER[0] == 'brand'

    def test_condition_labels_exist(self):
        """Vérifie les labels de condition."""
        assert 'EXCELLENT' in VintedTitleService.CONDITION_LABELS
        assert 'GOOD' in VintedTitleService.CONDITION_LABELS
        assert 'FAIR' in VintedTitleService.CONDITION_LABELS
        assert 'POOR' in VintedTitleService.CONDITION_LABELS


class TestCleanValue:
    """Tests pour la méthode _clean_value."""

    def test_clean_value_normal(self):
        """Test valeur normale."""
        assert VintedTitleService._clean_value("Test") == "Test"

    def test_clean_value_with_spaces(self):
        """Test valeur avec espaces."""
        assert VintedTitleService._clean_value("  Test  ") == "Test"

    def test_clean_value_none(self):
        """Test valeur None."""
        assert VintedTitleService._clean_value(None) is None

    def test_clean_value_empty(self):
        """Test valeur vide."""
        assert VintedTitleService._clean_value("") is None

    def test_clean_value_whitespace_only(self):
        """Test valeur avec espaces seulement."""
        assert VintedTitleService._clean_value("   ") is None


class TestToTitleCase:
    """Tests pour la méthode _to_title_case."""

    def test_title_case_lowercase(self):
        """Test conversion minuscules."""
        assert VintedTitleService._to_title_case("wrangler") == "Wrangler"

    def test_title_case_uppercase(self):
        """Test conversion majuscules."""
        assert VintedTitleService._to_title_case("LEVI'S") == "Levi'S"

    def test_title_case_multiple_words(self):
        """Test plusieurs mots."""
        assert VintedTitleService._to_title_case("ecko unltd") == "Ecko Unltd"

    def test_title_case_empty(self):
        """Test chaîne vide."""
        assert VintedTitleService._to_title_case("") == ""


class TestNormalizeUppercase:
    """Tests pour la méthode _normalize_uppercase."""

    def test_normalize_long_uppercase_word(self):
        """Test mot long en majuscules."""
        result = VintedTitleService._normalize_uppercase("TEXAS STRETCH")
        assert result == "Texas Stretch"

    def test_normalize_short_acronym_preserved(self):
        """Test acronyme court préservé (USA, XL, etc.)."""
        result = VintedTitleService._normalize_uppercase("USA MADE")
        assert result == "USA Made"

    def test_normalize_preserve_brackets(self):
        """Test préservation des crochets."""
        result = VintedTitleService._normalize_uppercase("TEST [2726]")
        assert "[2726]" in result

    def test_normalize_preserve_parentheses(self):
        """Test préservation des parenthèses."""
        result = VintedTitleService._normalize_uppercase("TEST (A3)")
        assert "(A3)" in result

    def test_normalize_mixed_case_preserved(self):
        """Test casse mixte préservée."""
        result = VintedTitleService._normalize_uppercase("Levi's Jeans")
        assert result == "Levi's Jeans"

    def test_normalize_empty_string(self):
        """Test chaîne vide."""
        assert VintedTitleService._normalize_uppercase("") == ""

    def test_normalize_none(self):
        """Test None."""
        assert VintedTitleService._normalize_uppercase(None) is None


class TestFormatDecade:
    """Tests pour la méthode _format_decade."""

    def test_format_decade_full_year(self):
        """Test année complète (1990s)."""
        result = VintedTitleService._format_decade("1990s")
        assert result == "Vintage 90s"

    def test_format_decade_short_year(self):
        """Test année courte (90s)."""
        result = VintedTitleService._format_decade("90s")
        assert result == "Vintage 90s"

    def test_format_decade_year_only(self):
        """Test année seule (1980)."""
        result = VintedTitleService._format_decade("1980")
        assert result == "Vintage 80s"

    def test_format_decade_80s(self):
        """Test années 80."""
        result = VintedTitleService._format_decade("80s")
        assert result == "Vintage 80s"

    def test_format_decade_none(self):
        """Test valeur None."""
        assert VintedTitleService._format_decade(None) is None

    def test_format_decade_empty(self):
        """Test chaîne vide."""
        assert VintedTitleService._format_decade("") is None

    def test_format_decade_no_digits(self):
        """Test sans chiffres."""
        assert VintedTitleService._format_decade("vintage") is None


class TestBuildSuffix:
    """Tests pour la méthode _build_suffix."""

    def test_suffix_with_location_and_id(self):
        """Test suffixe avec emplacement et ID."""
        product = Mock()
        product.id = 2726
        product.location = "A3"

        result = VintedTitleService._build_suffix(product)
        assert result == "(A3) [2726]"

    def test_suffix_without_location(self):
        """Test suffixe sans emplacement."""
        product = Mock()
        product.id = 1234
        product.location = None

        result = VintedTitleService._build_suffix(product)
        assert result == "[1234]"

    def test_suffix_with_empty_location(self):
        """Test suffixe avec emplacement vide."""
        product = Mock(spec=['id'])
        product.id = 5678

        result = VintedTitleService._build_suffix(product)
        assert result == "[5678]"


class TestExtractAttributes:
    """Tests pour la méthode _extract_attributes."""

    def test_extract_with_brand(self):
        """Test extraction avec marque."""
        product = Mock()
        product.brand = "Levi's"
        product.category = "Jeans"
        product.size_original = "36"
        product.color = "Blue"
        product.condition = 8
        product.fit = None
        product.model = None
        product.decade = None

        attrs = VintedTitleService._extract_attributes(product)
        assert attrs['brand'] == "Levi'S"  # Title case applied

    def test_extract_excludes_unbranded(self):
        """Test exclusion de 'unbranded'."""
        product = Mock()
        product.brand = "unbranded"
        product.category = "Jeans"
        product.size_normalized = None
        product.color = None
        product.condition = None
        product.fit = None
        product.model = None
        product.decade = None
        product.size_original = None

        attrs = VintedTitleService._extract_attributes(product)
        assert attrs['brand'] is None

    def test_extract_with_size(self):
        """Test extraction avec taille."""
        product = Mock()
        product.brand = "TestBrand"
        product.category = "T-shirt"
        product.size_original = "M"
        product.size_normalized = None
        product.color = None
        product.condition = None
        product.fit = None
        product.model = None
        product.decade = None

        attrs = VintedTitleService._extract_attributes(product)
        assert attrs['size'] == "Taille M"

    def test_extract_with_condition_mapping(self):
        """Test extraction avec mapping condition."""
        product = Mock()
        product.brand = "TestBrand"
        product.category = "T-shirt"
        product.size_normalized = None
        product.color = None
        product.condition = 8
        product.fit = None
        product.model = None
        product.decade = None
        product.size_original = None

        attrs = VintedTitleService._extract_attributes(product)
        assert attrs['condition'] == "Très bon état"

    def test_extract_with_decade(self):
        """Test extraction avec décennie."""
        product = Mock()
        product.brand = "TestBrand"
        product.category = "Jeans"
        product.size_normalized = None
        product.color = None
        product.condition = None
        product.fit = None
        product.model = None
        product.decade = "1990s"
        product.size_original = None

        attrs = VintedTitleService._extract_attributes(product)
        assert attrs['decade'] == "Vintage 90s"


class TestBuildTitleWithMaxAttributes:
    """Tests pour la méthode _build_title_with_max_attributes."""

    def test_build_title_all_attributes_fit(self):
        """Test titre avec tous les attributs qui tiennent."""
        attributes = {
            'brand': 'TestBrand',
            'model': '501',
            'category': 'Jeans',
            'fit': 'Slim',
            'size': 'Taille 32',
            'condition': 'Bon état',
            'color': 'Blue',
            'decade': 'Vintage 90s',
        }
        suffix = "[123]"

        result = VintedTitleService._build_title_with_max_attributes(attributes, suffix)
        assert len(result) <= MAX_TITLE_LENGTH
        assert "[123]" in result

    def test_build_title_priority_order(self):
        """Test que l'ordre de priorité est respecté."""
        attributes = {
            'brand': 'Levi\'s',
            'category': 'Jeans',
            'color': 'Blue',
        }
        suffix = "[123]"

        result = VintedTitleService._build_title_with_max_attributes(attributes, suffix)
        # Marque doit être avant catégorie
        assert result.index("Levi's") < result.index("Jeans")

    def test_build_title_truncates_when_too_long(self):
        """Test troncature si titre trop long."""
        attributes = {
            'brand': 'A' * 40,
            'model': 'B' * 30,
            'category': 'C' * 30,
            'fit': 'D' * 30,
            'size': 'E' * 30,
            'condition': 'F' * 30,
            'color': 'G' * 30,
            'decade': 'H' * 30,
        }
        suffix = "[123456789]"

        result = VintedTitleService._build_title_with_max_attributes(attributes, suffix)
        assert len(result) <= MAX_TITLE_LENGTH

    def test_build_title_suffix_always_present(self):
        """Test que le suffixe est toujours présent."""
        attributes = {'brand': 'X' * 95}  # Très long
        suffix = "[999]"

        result = VintedTitleService._build_title_with_max_attributes(attributes, suffix)
        assert "[999]" in result


class TestGenerateTitle:
    """Tests pour la méthode generate_title."""

    def test_generate_title_basic(self):
        """Test génération basique."""
        product = Mock()
        product.id = 2726
        product.brand = "Levi's"
        product.category = "Jeans"
        product.size_original = "36"
        product.color = "Blue"
        product.condition = 8
        product.location = "A3"
        product.fit = None
        product.model = None
        product.decade = None
        product.size_original = None

        title = VintedTitleService.generate_title(product)

        assert len(title) <= MAX_TITLE_LENGTH
        assert "[2726]" in title
        assert "(A3)" in title

    def test_generate_title_max_length(self):
        """Test que le titre ne dépasse jamais 100 caractères."""
        product = Mock()
        product.id = 999999
        product.brand = "SuperLongBrandName" * 3
        product.category = "SuperLongCategory" * 3
        product.size_original = "XXXL"
        product.color = "Rainbow Multicolor"
        product.condition = 8
        product.location = "WAREHOUSE123"
        product.fit = "Extra Slim Fit"
        product.model = "SuperModelName"
        product.decade = "1990s"
        product.size_original = None

        title = VintedTitleService.generate_title(product)
        assert len(title) <= MAX_TITLE_LENGTH

    def test_generate_title_without_location(self):
        """Test génération sans emplacement."""
        product = Mock(spec=['id', 'brand', 'category', 'size', 'color', 'condition'])
        product.id = 1000
        product.brand = "Nike"
        product.category = "Sneakers"
        product.size_original = "42"
        product.color = "White"
        product.condition = 7

        title = VintedTitleService.generate_title(product)

        assert "[1000]" in title
        assert "(" not in title  # Pas de parenthèses si pas de location

    def test_generate_title_normalizes_uppercase(self):
        """Test normalisation des majuscules."""
        product = Mock()
        product.id = 123
        product.brand = "TEXAS"
        product.category = "STRETCH JEANS"
        product.size_normalized = None
        product.color = None
        product.condition = None
        product.location = None
        product.fit = None
        product.model = None
        product.decade = None
        product.size_original = None

        title = VintedTitleService.generate_title(product)

        # Les mots longs en majuscules devraient être convertis en Title Case
        assert "TEXAS" not in title or len("TEXAS") <= 3  # Texas ou préservé si court
