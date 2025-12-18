"""
Tests unitaires pour VintedMappingRepository

Tests pour l'accès à la table vinted_mapping et la fonction get_vinted_category.

Business Rules Tested:
- Stoflow → Vinted: utilise get_vinted_category() avec matching d'attributs
- Vinted → Stoflow: lookup inverse dans vinted_mapping (vinted_id → my_category)
- Fallback via is_default si pas de match exact

Author: Claude
Date: 2025-12-18
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from repositories.vinted_mapping_repository import VintedMappingRepository


class TestGetVintedCategoryId:
    """Tests pour get_vinted_category_id."""

    def test_get_vinted_category_id_basic(self):
        """Test mapping basique category + gender."""
        mock_db = Mock()
        mock_result = Mock()
        mock_result.scalar.return_value = 1193

        mock_db.execute.return_value = mock_result

        repo = VintedMappingRepository(mock_db)
        result = repo.get_vinted_category_id("jeans", "men")

        assert result == 1193

    def test_get_vinted_category_id_with_fit(self):
        """Test mapping avec fit."""
        mock_db = Mock()
        mock_result = Mock()
        mock_result.scalar.return_value = 1818

        mock_db.execute.return_value = mock_result

        repo = VintedMappingRepository(mock_db)
        result = repo.get_vinted_category_id("jeans", "men", fit="slim")

        assert result == 1818

    def test_get_vinted_category_id_not_found(self):
        """Test mapping non trouvé."""
        mock_db = Mock()
        mock_result = Mock()
        mock_result.scalar.return_value = None

        mock_db.execute.return_value = mock_result

        repo = VintedMappingRepository(mock_db)
        result = repo.get_vinted_category_id("unknown", "men")

        assert result is None

    def test_get_vinted_category_id_normalizes_case(self):
        """Test normalisation de la casse."""
        mock_db = Mock()
        mock_result = Mock()
        mock_result.scalar.return_value = 1193

        mock_db.execute.return_value = mock_result

        repo = VintedMappingRepository(mock_db)

        # Call with uppercase
        repo.get_vinted_category_id("JEANS", "MEN", fit="SLIM")

        # Verify the parameters were lowercased
        call_args = mock_db.execute.call_args
        params = call_args[0][1]  # Second positional arg is the params dict

        assert params['category'] == 'jeans'
        assert params['gender'] == 'men'
        assert params['fit'] == 'slim'

    def test_get_vinted_category_id_handles_none_attributes(self):
        """Test avec attributs None."""
        mock_db = Mock()
        mock_result = Mock()
        mock_result.scalar.return_value = 1193

        mock_db.execute.return_value = mock_result

        repo = VintedMappingRepository(mock_db)
        result = repo.get_vinted_category_id(
            "jeans", "men",
            fit=None,
            length=None,
            rise=None
        )

        assert result == 1193

    def test_get_vinted_category_id_exception_handling(self):
        """Test gestion des exceptions."""
        mock_db = Mock()
        mock_db.execute.side_effect = Exception("DB Error")

        repo = VintedMappingRepository(mock_db)
        result = repo.get_vinted_category_id("jeans", "men")

        assert result is None


class TestGetStoflowCategory:
    """Tests pour get_stoflow_category (reverse lookup)."""

    def test_get_stoflow_category_found(self):
        """Test reverse lookup trouvé."""
        mock_db = Mock()
        mock_result = Mock()
        mock_result.my_category = "jeans"
        mock_result.my_gender = "men"

        mock_db.execute.return_value.fetchone.return_value = mock_result

        repo = VintedMappingRepository(mock_db)
        category, gender = repo.get_stoflow_category(1193)

        assert category == "jeans"
        assert gender == "men"

    def test_get_stoflow_category_not_found(self):
        """Test reverse lookup non trouvé."""
        mock_db = Mock()
        mock_db.execute.return_value.fetchone.return_value = None

        repo = VintedMappingRepository(mock_db)
        category, gender = repo.get_stoflow_category(99999)

        assert category is None
        assert gender is None

    def test_get_stoflow_category_exception_handling(self):
        """Test gestion des exceptions."""
        mock_db = Mock()
        mock_db.execute.side_effect = Exception("DB Error")

        repo = VintedMappingRepository(mock_db)
        category, gender = repo.get_stoflow_category(1193)

        assert category is None
        assert gender is None


class TestGetVintedCategoryWithDetails:
    """Tests pour get_vinted_category_with_details."""

    def test_get_vinted_category_with_details_found(self):
        """Test récupération avec détails."""
        mock_db = Mock()

        # Mock get_vinted_category_id
        mock_result1 = Mock()
        mock_result1.scalar.return_value = 1193

        # Mock vinted_categories lookup
        mock_result2 = Mock()
        mock_result2.id = 1193
        mock_result2.title = "Jean slim"
        mock_result2.path = "Hommes > Jeans > Slim"
        mock_result2.gender = "men"

        mock_db.execute.side_effect = [mock_result1, Mock(fetchone=Mock(return_value=mock_result2))]

        repo = VintedMappingRepository(mock_db)
        result = repo.get_vinted_category_with_details("jeans", "men")

        assert result['vinted_id'] == 1193
        assert result['title'] == "Jean slim"
        assert result['path'] == "Hommes > Jeans > Slim"

    def test_get_vinted_category_with_details_not_found(self):
        """Test quand aucun mapping trouvé."""
        mock_db = Mock()
        mock_result = Mock()
        mock_result.scalar.return_value = None

        mock_db.execute.return_value = mock_result

        repo = VintedMappingRepository(mock_db)
        result = repo.get_vinted_category_with_details("unknown", "men")

        assert result['vinted_id'] is None
        assert result['title'] is None


class TestGetStoflowCategoryWithDetails:
    """Tests pour get_stoflow_category_with_details."""

    def test_get_stoflow_category_with_details_found(self):
        """Test récupération détails complets."""
        mock_db = Mock()
        mock_result = Mock()
        mock_result.my_category = "jeans"
        mock_result.my_gender = "men"
        mock_result.my_fit = "slim"
        mock_result.my_length = None
        mock_result.my_rise = None
        mock_result.my_material = "denim"
        mock_result.my_pattern = None
        mock_result.my_neckline = None
        mock_result.my_sleeve_length = None
        mock_result.is_default = True

        mock_db.execute.return_value.fetchone.return_value = mock_result

        repo = VintedMappingRepository(mock_db)
        result = repo.get_stoflow_category_with_details(1193)

        assert result['category'] == "jeans"
        assert result['gender'] == "men"
        assert result['fit'] == "slim"
        assert result['material'] == "denim"
        assert result['is_default'] is True

    def test_get_stoflow_category_with_details_not_found(self):
        """Test quand aucun mapping trouvé."""
        mock_db = Mock()
        mock_db.execute.return_value.fetchone.return_value = None

        repo = VintedMappingRepository(mock_db)
        result = repo.get_stoflow_category_with_details(99999)

        assert result['category'] is None
        assert result['gender'] is None
        assert result['is_default'] is False


class TestHasMapping:
    """Tests pour has_mapping."""

    def test_has_mapping_true(self):
        """Test mapping existant."""
        mock_db = Mock()
        mock_db.execute.return_value.scalar.return_value = True

        repo = VintedMappingRepository(mock_db)
        result = repo.has_mapping("jeans", "men")

        assert result is True

    def test_has_mapping_false(self):
        """Test mapping inexistant."""
        mock_db = Mock()
        mock_db.execute.return_value.scalar.return_value = False

        repo = VintedMappingRepository(mock_db)
        result = repo.has_mapping("unknown", "men")

        assert result is False


class TestHasDefaultMapping:
    """Tests pour has_default_mapping."""

    def test_has_default_mapping_true(self):
        """Test default mapping existant."""
        mock_db = Mock()
        mock_db.execute.return_value.scalar.return_value = True

        repo = VintedMappingRepository(mock_db)
        result = repo.has_default_mapping("jeans", "men")

        assert result is True

    def test_has_default_mapping_false(self):
        """Test default mapping inexistant."""
        mock_db = Mock()
        mock_db.execute.return_value.scalar.return_value = False

        repo = VintedMappingRepository(mock_db)
        result = repo.has_default_mapping("jeans", "men")

        assert result is False


class TestGetAllMappingsForCategory:
    """Tests pour get_all_mappings_for_category."""

    def test_get_all_mappings_for_category(self):
        """Test récupération de tous les mappings."""
        mock_db = Mock()

        # Create mock results
        mock_row1 = Mock()
        mock_row1.id = 1
        mock_row1.vinted_id = 1193
        mock_row1.vinted_title = "Jean"
        mock_row1.vinted_path = "Hommes > Jeans"
        mock_row1.my_fit = None
        mock_row1.my_length = None
        mock_row1.my_rise = None
        mock_row1.is_default = True

        mock_row2 = Mock()
        mock_row2.id = 2
        mock_row2.vinted_id = 1818
        mock_row2.vinted_title = "Jean slim"
        mock_row2.vinted_path = "Hommes > Jeans > Slim"
        mock_row2.my_fit = "slim"
        mock_row2.my_length = None
        mock_row2.my_rise = None
        mock_row2.is_default = False

        mock_db.execute.return_value.fetchall.return_value = [mock_row1, mock_row2]

        repo = VintedMappingRepository(mock_db)
        results = repo.get_all_mappings_for_category("jeans", "men")

        assert len(results) == 2
        assert results[0]['vinted_id'] == 1193
        assert results[0]['is_default'] is True
        assert results[1]['vinted_id'] == 1818
        assert results[1]['fit'] == "slim"


class TestGetMappingIssues:
    """Tests pour get_mapping_issues."""

    def test_get_mapping_issues_empty(self):
        """Test aucun problème de mapping."""
        mock_db = Mock()
        mock_db.execute.return_value.fetchall.return_value = []

        repo = VintedMappingRepository(mock_db)
        results = repo.get_mapping_issues()

        assert results == []

    def test_get_mapping_issues_found(self):
        """Test problèmes de mapping trouvés."""
        mock_db = Mock()

        mock_row = Mock()
        mock_row.issue = "NO_DEFAULT"
        mock_row.vinted_id = None
        mock_row.vinted_title = None
        mock_row.vinted_gender = None
        mock_row.my_category = "new-category"
        mock_row.my_gender = "men"

        mock_db.execute.return_value.fetchall.return_value = [mock_row]

        repo = VintedMappingRepository(mock_db)
        results = repo.get_mapping_issues()

        assert len(results) == 1
        assert results[0]['issue'] == "NO_DEFAULT"
        assert results[0]['my_category'] == "new-category"
