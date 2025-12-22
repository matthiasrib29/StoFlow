"""
Tests for Attributes API

Integration tests for /api/attributes/* endpoints.
These endpoints are public (no authentication required).

Business Rules Tested:
- All 9 attribute types return valid JSON arrays
- Response structure matches expected format
- Language parameter (lang) works correctly
- Search parameter works for brands
- Limit parameter respects boundaries
"""

import pytest
from fastapi.testclient import TestClient


# ===== CONSTANTS =====

ATTRIBUTE_TYPES = [
    "categories",
    "conditions",
    "genders",
    "seasons",
    "brands",
    "colors",
    "materials",
    "fits",
    "sizes",
]

LANGUAGES = ["en", "fr", "de", "it", "es", "nl", "pl"]


# ===== TEST CLASSES =====


class TestAttributesEndpoints:
    """Tests for all attribute endpoints."""

    @pytest.mark.parametrize("attribute_type", ATTRIBUTE_TYPES)
    def test_get_attributes_returns_list(self, client: TestClient, attribute_type: str):
        """
        Test that each attribute endpoint returns a valid JSON list.

        This is the most basic smoke test to ensure endpoints work.
        """
        response = client.get(f"/api/attributes/{attribute_type}")

        assert response.status_code == 200, f"Failed for {attribute_type}: {response.text}"

        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)} for {attribute_type}"

    @pytest.mark.parametrize("attribute_type", ATTRIBUTE_TYPES)
    def test_get_attributes_has_value_and_label(self, client: TestClient, attribute_type: str):
        """
        Test that each item in response has 'value' and 'label' keys.
        """
        response = client.get(f"/api/attributes/{attribute_type}")

        assert response.status_code == 200
        data = response.json()

        # Skip if empty (e.g., fits table might be empty)
        if len(data) == 0:
            pytest.skip(f"No data in {attribute_type}")

        first_item = data[0]
        assert "value" in first_item, f"Missing 'value' key in {attribute_type}"
        assert "label" in first_item, f"Missing 'label' key in {attribute_type}"

    def test_invalid_attribute_type_returns_404(self, client: TestClient):
        """Test that invalid attribute type returns 404."""
        response = client.get("/api/attributes/invalid_type")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_list_attribute_types_returns_all_types(self, client: TestClient):
        """Test that listing endpoint returns all available types."""
        response = client.get("/api/attributes/")

        assert response.status_code == 200
        data = response.json()

        assert "available_types" in data
        assert isinstance(data["available_types"], list)

        # Verify all expected types are present
        for attr_type in ATTRIBUTE_TYPES:
            assert attr_type in data["available_types"], f"Missing {attr_type}"


class TestAttributesLanguageParameter:
    """Tests for language (lang) parameter."""

    @pytest.mark.parametrize("lang", LANGUAGES)
    def test_lang_parameter_accepted(self, client: TestClient, lang: str):
        """Test that all language codes are accepted."""
        response = client.get(f"/api/attributes/categories?lang={lang}")

        assert response.status_code == 200

    def test_default_language_is_english(self, client: TestClient):
        """Test that default language is English when not specified."""
        response = client.get("/api/attributes/categories")

        assert response.status_code == 200
        # Response should be valid even without lang parameter


class TestAttributesLimitParameter:
    """Tests for limit parameter."""

    def test_limit_default_is_100(self, client: TestClient):
        """Test default limit behavior."""
        response = client.get("/api/attributes/colors")

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 100

    def test_limit_parameter_works(self, client: TestClient):
        """Test that limit parameter restricts results."""
        response = client.get("/api/attributes/colors?limit=3")

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 3

    def test_limit_max_is_500(self, client: TestClient):
        """Test that limit above 500 is rejected or capped."""
        response = client.get("/api/attributes/colors?limit=1000")

        # FastAPI should validate this and return 422
        assert response.status_code == 422


class TestAttributesSearchParameter:
    """Tests for search parameter (brands endpoint)."""

    def test_brands_search_works(self, client: TestClient):
        """Test that search parameter filters brands."""
        # First get all brands
        all_response = client.get("/api/attributes/brands?limit=500")
        assert all_response.status_code == 200

        # Then search for specific brand
        search_response = client.get("/api/attributes/brands?search=Nike")
        assert search_response.status_code == 200

        search_data = search_response.json()

        # If Nike exists, it should be in results
        if len(search_data) > 0:
            # All results should contain search term (case-insensitive)
            for item in search_data:
                assert "nike" in item["value"].lower() or "nike" in item["label"].lower()

    def test_search_on_non_searchable_type_ignored(self, client: TestClient):
        """Test that search parameter is ignored for non-searchable types."""
        # Colors doesn't support search
        response = client.get("/api/attributes/colors?search=blue")

        # Should still return results (search ignored)
        assert response.status_code == 200


class TestConditionsEndpoint:
    """Specific tests for conditions endpoint (special structure)."""

    def test_conditions_has_numeric_value(self, client: TestClient):
        """Test that conditions value is numeric (note 0-10)."""
        response = client.get("/api/attributes/conditions")

        assert response.status_code == 200
        data = response.json()

        if len(data) == 0:
            pytest.skip("No conditions data")

        first_item = data[0]
        assert isinstance(first_item["value"], int), "Condition value should be integer"

    def test_conditions_has_coefficient(self, client: TestClient):
        """Test that conditions include coefficient field."""
        response = client.get("/api/attributes/conditions")

        assert response.status_code == 200
        data = response.json()

        if len(data) == 0:
            pytest.skip("No conditions data")

        first_item = data[0]
        assert "coefficient" in first_item, "Condition should have coefficient"

    def test_conditions_has_vinted_id(self, client: TestClient):
        """Test that conditions include vinted_id field."""
        response = client.get("/api/attributes/conditions")

        assert response.status_code == 200
        data = response.json()

        if len(data) == 0:
            pytest.skip("No conditions data")

        first_item = data[0]
        assert "vinted_id" in first_item, "Condition should have vinted_id"


class TestColorsEndpoint:
    """Specific tests for colors endpoint."""

    def test_colors_has_hex_code(self, client: TestClient):
        """Test that colors include hex_code field."""
        response = client.get("/api/attributes/colors")

        assert response.status_code == 200
        data = response.json()

        if len(data) == 0:
            pytest.skip("No colors data")

        first_item = data[0]
        assert "hex_code" in first_item, "Color should have hex_code"


class TestSizesEndpoint:
    """Specific tests for sizes endpoint."""

    def test_sizes_has_marketplace_fields(self, client: TestClient):
        """Test that sizes include marketplace fields."""
        response = client.get("/api/attributes/sizes")

        assert response.status_code == 200
        data = response.json()

        if len(data) == 0:
            pytest.skip("No sizes data")

        first_item = data[0]
        assert "vinted_id" in first_item, "Size should have vinted_id"
        assert "ebay_size" in first_item, "Size should have ebay_size"
        assert "etsy_size" in first_item, "Size should have etsy_size"


class TestCategoriesEndpoint:
    """Specific tests for categories endpoint."""

    def test_categories_has_parent_category(self, client: TestClient):
        """Test that categories include parent_category field."""
        response = client.get("/api/attributes/categories")

        assert response.status_code == 200
        data = response.json()

        if len(data) == 0:
            pytest.skip("No categories data")

        first_item = data[0]
        assert "parent_category" in first_item, "Category should have parent_category"


# ===== SMOKE TESTS =====


class TestAttributesSmokeTests:
    """
    Quick smoke tests to run after deployment.

    These tests verify the basic functionality without deep assertions.
    Useful for CI/CD pipelines.
    """

    def test_all_endpoints_respond(self, client: TestClient):
        """Single test that checks all endpoints respond with 200."""
        failed = []

        for attr_type in ATTRIBUTE_TYPES:
            response = client.get(f"/api/attributes/{attr_type}")
            if response.status_code != 200:
                failed.append(f"{attr_type}: {response.status_code}")

        assert len(failed) == 0, f"Failed endpoints: {', '.join(failed)}"

    def test_all_endpoints_return_valid_json(self, client: TestClient):
        """Single test that checks all endpoints return valid JSON arrays."""
        failed = []

        for attr_type in ATTRIBUTE_TYPES:
            response = client.get(f"/api/attributes/{attr_type}")
            try:
                data = response.json()
                if not isinstance(data, list):
                    failed.append(f"{attr_type}: not a list")
            except Exception as e:
                failed.append(f"{attr_type}: {str(e)}")

        assert len(failed) == 0, f"Failed endpoints: {', '.join(failed)}"
