"""
Tests for CategoryMappingRepository

Tests the multi-platform category mapping repository.
Uses mocks to avoid database dependency.
"""
import json
import pytest
from unittest.mock import MagicMock, patch

from repositories.category_mapping_repository import CategoryMappingRepository
from models.public.category_platform_mapping import CategoryPlatformMapping


class TestCategoryMappingRepositoryVinted:
    """Tests for Vinted mapping methods."""

    def test_get_vinted_mapping_exact_match(self):
        """Test exact match with category + gender + fit."""
        # Create mock mapping
        mock_mapping = MagicMock(spec=CategoryPlatformMapping)
        mock_mapping.vinted_category_id = 89
        mock_mapping.vinted_category_name = "Jean slim"
        mock_mapping.vinted_category_path = "Hommes > Jeans > Slim"

        # Mock session
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_mapping

        repo = CategoryMappingRepository(mock_session)
        result = repo.get_vinted_mapping("Jeans", "Men", "Slim")

        assert result is not None
        assert result['id'] == 89
        assert result['name'] == "Jean slim"
        assert result['path'] == "Hommes > Jeans > Slim"

    def test_get_vinted_mapping_no_fit_fallback(self):
        """Test fallback to no-fit mapping when exact match not found."""
        mock_mapping = MagicMock(spec=CategoryPlatformMapping)
        mock_mapping.vinted_category_id = 88
        mock_mapping.vinted_category_name = "Jeans"
        mock_mapping.vinted_category_path = "Hommes > Jeans"

        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        # First call (exact match) returns None, second call (no fit) returns mapping
        mock_query.first.side_effect = [None, mock_mapping]

        repo = CategoryMappingRepository(mock_session)
        result = repo.get_vinted_mapping("Jeans", "Men", "Bootcut")

        assert result is not None
        assert result['id'] == 88

    def test_get_vinted_mapping_not_found(self):
        """Test returns None when no mapping found."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        repo = CategoryMappingRepository(mock_session)
        result = repo.get_vinted_mapping("UnknownCategory", "Men")

        assert result is None

    def test_get_vinted_mapping_no_vinted_id(self):
        """Test returns None when mapping exists but no vinted_category_id."""
        mock_mapping = MagicMock(spec=CategoryPlatformMapping)
        mock_mapping.vinted_category_id = None

        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_mapping

        repo = CategoryMappingRepository(mock_session)
        result = repo.get_vinted_mapping("Jeans", "Men")

        assert result is None


class TestCategoryMappingRepositoryEtsy:
    """Tests for Etsy mapping methods."""

    def test_get_etsy_mapping_with_attributes(self):
        """Test Etsy mapping with required attributes JSON."""
        mock_mapping = MagicMock(spec=CategoryPlatformMapping)
        mock_mapping.etsy_taxonomy_id = 1429
        mock_mapping.etsy_category_name = "Jeans"
        mock_mapping.etsy_category_path = "Clothing > Men's Clothing > Jeans"
        mock_mapping.etsy_required_attributes = json.dumps({
            "style": ["casual", "vintage"],
            "fit": ["slim", "regular"]
        })

        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_mapping

        repo = CategoryMappingRepository(mock_session)
        result = repo.get_etsy_mapping("Jeans", "Men")

        assert result is not None
        assert result['taxonomy_id'] == 1429
        assert result['name'] == "Jeans"
        assert result['attributes'] is not None
        assert 'style' in result['attributes']

    def test_get_etsy_mapping_invalid_json_attributes(self):
        """Test Etsy mapping with invalid JSON returns None for attributes."""
        mock_mapping = MagicMock(spec=CategoryPlatformMapping)
        mock_mapping.etsy_taxonomy_id = 1429
        mock_mapping.etsy_category_name = "Jeans"
        mock_mapping.etsy_category_path = "Clothing > Jeans"
        mock_mapping.etsy_required_attributes = "invalid json {"

        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_mapping

        repo = CategoryMappingRepository(mock_session)
        result = repo.get_etsy_mapping("Jeans", "Men")

        assert result is not None
        assert result['taxonomy_id'] == 1429
        assert result['attributes'] is None

    def test_get_etsy_mapping_not_found(self):
        """Test returns None when no Etsy mapping."""
        mock_mapping = MagicMock(spec=CategoryPlatformMapping)
        mock_mapping.etsy_taxonomy_id = None

        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_mapping

        repo = CategoryMappingRepository(mock_session)
        result = repo.get_etsy_mapping("Jeans", "Men")

        assert result is None


class TestCategoryMappingRepositoryEbay:
    """Tests for eBay mapping methods."""

    def test_get_ebay_mapping_fr(self):
        """Test eBay mapping for French marketplace."""
        mock_mapping = MagicMock(spec=CategoryPlatformMapping)
        mock_mapping.ebay_category_id_fr = 11483
        mock_mapping.ebay_category_id_de = 11484
        mock_mapping.ebay_category_id_gb = 11485
        mock_mapping.ebay_category_id_it = None
        mock_mapping.ebay_category_id_es = None
        mock_mapping.ebay_category_name = "Jeans"
        mock_mapping.ebay_item_specifics = json.dumps({
            "Style": "Jeans",
            "Department": "Men"
        })

        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_mapping

        repo = CategoryMappingRepository(mock_session)
        result = repo.get_ebay_mapping("Jeans", "Men", marketplace="EBAY_FR")

        assert result is not None
        assert result['category_id'] == 11483
        assert result['name'] == "Jeans"
        assert result['item_specifics'] is not None

    def test_get_ebay_mapping_de(self):
        """Test eBay mapping for German marketplace."""
        mock_mapping = MagicMock(spec=CategoryPlatformMapping)
        mock_mapping.ebay_category_id_fr = 11483
        mock_mapping.ebay_category_id_de = 11484
        mock_mapping.ebay_category_id_gb = 11485
        mock_mapping.ebay_category_id_it = None
        mock_mapping.ebay_category_id_es = None
        mock_mapping.ebay_category_name = "Jeans"
        mock_mapping.ebay_item_specifics = None

        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_mapping

        repo = CategoryMappingRepository(mock_session)
        result = repo.get_ebay_mapping("Jeans", "Men", marketplace="EBAY_DE")

        assert result is not None
        assert result['category_id'] == 11484

    def test_get_ebay_mapping_marketplace_not_configured(self):
        """Test returns None when marketplace not configured."""
        mock_mapping = MagicMock(spec=CategoryPlatformMapping)
        mock_mapping.ebay_category_id_fr = 11483
        mock_mapping.ebay_category_id_de = None
        mock_mapping.ebay_category_id_gb = None
        mock_mapping.ebay_category_id_it = None
        mock_mapping.ebay_category_id_es = None
        mock_mapping.ebay_category_name = "Jeans"
        mock_mapping.ebay_item_specifics = None

        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_mapping

        repo = CategoryMappingRepository(mock_session)
        result = repo.get_ebay_mapping("Jeans", "Men", marketplace="EBAY_IT")

        assert result is None

    def test_get_ebay_mapping_unknown_marketplace(self):
        """Test returns None for unknown marketplace."""
        mock_mapping = MagicMock(spec=CategoryPlatformMapping)
        mock_mapping.ebay_category_id_fr = 11483

        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_mapping

        repo = CategoryMappingRepository(mock_session)
        result = repo.get_ebay_mapping("Jeans", "Men", marketplace="EBAY_JP")

        assert result is None


class TestCategoryMappingRepositoryAllMappings:
    """Tests for get_all_mappings method."""

    def test_get_all_mappings_full(self):
        """Test getting all platform mappings in single query."""
        mock_mapping = MagicMock(spec=CategoryPlatformMapping)
        mock_mapping.vinted_category_id = 89
        mock_mapping.vinted_category_name = "Jean slim"
        mock_mapping.vinted_category_path = "Hommes > Jeans > Slim"
        mock_mapping.etsy_taxonomy_id = 1429
        mock_mapping.etsy_category_name = "Jeans"
        mock_mapping.etsy_category_path = "Clothing > Jeans"
        mock_mapping.etsy_required_attributes = None
        mock_mapping.ebay_category_id_fr = 11483
        mock_mapping.ebay_category_id_de = 11484
        mock_mapping.ebay_category_id_gb = 11485
        mock_mapping.ebay_category_id_it = None
        mock_mapping.ebay_category_id_es = None
        mock_mapping.ebay_category_name = "Jeans"
        mock_mapping.ebay_item_specifics = None

        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_mapping

        repo = CategoryMappingRepository(mock_session)
        result = repo.get_all_mappings("Jeans", "Men", "Slim")

        assert result['vinted'] is not None
        assert result['vinted']['id'] == 89
        assert result['etsy'] is not None
        assert result['etsy']['taxonomy_id'] == 1429
        assert result['ebay_fr'] is not None
        assert result['ebay_fr']['category_id'] == 11483
        assert result['ebay_de'] is not None
        assert result['ebay_it'] is None
        assert result['ebay_es'] is None

    def test_get_all_mappings_not_found(self):
        """Test get_all_mappings returns all None when no mapping found."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        repo = CategoryMappingRepository(mock_session)
        result = repo.get_all_mappings("Unknown", "Men")

        assert result['vinted'] is None
        assert result['etsy'] is None
        assert result['ebay_fr'] is None
        assert result['ebay_de'] is None
        assert result['ebay_gb'] is None
        assert result['ebay_it'] is None
        assert result['ebay_es'] is None


class TestCategoryMappingRepositoryCRUD:
    """Tests for CRUD operations."""

    def test_create(self):
        """Test creating a new mapping."""
        mock_mapping = MagicMock(spec=CategoryPlatformMapping)
        mock_mapping.id = 1
        mock_mapping.category = "Jeans"
        mock_mapping.gender = "Men"

        mock_session = MagicMock()

        repo = CategoryMappingRepository(mock_session)
        result = repo.create(mock_mapping)

        mock_session.add.assert_called_once_with(mock_mapping)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_mapping)

    def test_get_by_id(self):
        """Test getting mapping by ID."""
        mock_mapping = MagicMock(spec=CategoryPlatformMapping)
        mock_mapping.id = 1

        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_mapping

        repo = CategoryMappingRepository(mock_session)
        result = repo.get_by_id(1)

        assert result is not None
        assert result.id == 1

    def test_get_by_id_not_found(self):
        """Test get_by_id returns None when not found."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        repo = CategoryMappingRepository(mock_session)
        result = repo.get_by_id(999)

        assert result is None

    def test_delete(self):
        """Test deleting a mapping."""
        mock_mapping = MagicMock(spec=CategoryPlatformMapping)
        mock_mapping.id = 1

        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_mapping

        repo = CategoryMappingRepository(mock_session)
        result = repo.delete(1)

        assert result is True
        mock_session.delete.assert_called_once_with(mock_mapping)
        mock_session.commit.assert_called_once()

    def test_delete_not_found(self):
        """Test delete returns False when not found."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        repo = CategoryMappingRepository(mock_session)
        result = repo.delete(999)

        assert result is False
        mock_session.delete.assert_not_called()

    def test_exists_true(self):
        """Test exists returns True when mapping exists."""
        mock_mapping = MagicMock(spec=CategoryPlatformMapping)

        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_mapping

        repo = CategoryMappingRepository(mock_session)
        result = repo.exists("Jeans", "Men", "Slim")

        assert result is True

    def test_exists_false(self):
        """Test exists returns False when mapping doesn't exist."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        repo = CategoryMappingRepository(mock_session)
        result = repo.exists("Unknown", "Men")

        assert result is False
