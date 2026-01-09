"""
Unit tests for EtsyListingClient.

Tests the Etsy listing management functionality:
- Get shop listings (active, draft, inactive)
- Get single listing
- Create draft listing
- Update listing
- Delete listing

Author: Claude
Date: 2025-12-22
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from services.etsy.etsy_listing_client import EtsyListingClient


class TestGetShopListingsActive:
    """Tests for get_shop_listings_active method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock EtsyListingClient with mocked dependencies."""
        with patch.object(EtsyListingClient, "__init__", return_value=None):
            client = EtsyListingClient.__new__(EtsyListingClient)
            client.db = MagicMock()
            client.user_id = 1
            client.shop_id = 12345678
            client.api_call = MagicMock()
            return client

    def test_get_shop_listings_active_success(self, mock_client):
        """Test successful retrieval of active listings with default parameters."""
        expected_response = {
            "count": 2,
            "results": [
                {
                    "listing_id": 111111111,
                    "title": "Vintage Necklace",
                    "price": {"amount": 4999, "divisor": 100, "currency_code": "USD"},
                    "state": "active",
                },
                {
                    "listing_id": 222222222,
                    "title": "Handmade Ring",
                    "price": {"amount": 2999, "divisor": 100, "currency_code": "USD"},
                    "state": "active",
                },
            ],
        }
        mock_client.api_call.return_value = expected_response

        result = mock_client.get_shop_listings_active()

        mock_client.api_call.assert_called_once_with(
            "GET",
            "/application/shops/12345678/listings/active",
            params={
                "limit": 25,
                "offset": 0,
                "sort_on": "created",
                "sort_order": "desc",
            },
        )
        assert result["count"] == 2
        assert len(result["results"]) == 2
        assert result["results"][0]["title"] == "Vintage Necklace"

    def test_get_shop_listings_active_with_pagination(self, mock_client):
        """Test retrieval of active listings with custom pagination parameters."""
        expected_response = {
            "count": 100,
            "results": [
                {
                    "listing_id": 333333333,
                    "title": "Earrings Set",
                    "state": "active",
                }
            ],
        }
        mock_client.api_call.return_value = expected_response

        result = mock_client.get_shop_listings_active(
            limit=50, offset=25, sort_on="updated", sort_order="asc"
        )

        mock_client.api_call.assert_called_once_with(
            "GET",
            "/application/shops/12345678/listings/active",
            params={
                "limit": 50,
                "offset": 25,
                "sort_on": "updated",
                "sort_order": "asc",
            },
        )
        assert result["count"] == 100


class TestGetShopListingsDraft:
    """Tests for get_shop_listings_draft method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock EtsyListingClient with mocked dependencies."""
        with patch.object(EtsyListingClient, "__init__", return_value=None):
            client = EtsyListingClient.__new__(EtsyListingClient)
            client.db = MagicMock()
            client.user_id = 1
            client.shop_id = 12345678
            client.api_call = MagicMock()
            return client

    def test_get_shop_listings_draft_success(self, mock_client):
        """Test successful retrieval of draft listings."""
        expected_response = {
            "count": 3,
            "results": [
                {
                    "listing_id": 444444444,
                    "title": "Draft Bracelet",
                    "state": "draft",
                },
                {
                    "listing_id": 555555555,
                    "title": "Draft Pendant",
                    "state": "draft",
                },
                {
                    "listing_id": 666666666,
                    "title": "Draft Anklet",
                    "state": "draft",
                },
            ],
        }
        mock_client.api_call.return_value = expected_response

        result = mock_client.get_shop_listings_draft()

        mock_client.api_call.assert_called_once_with(
            "GET",
            "/application/shops/12345678/listings/draft",
            params={"limit": 25, "offset": 0},
        )
        assert result["count"] == 3
        assert all(item["state"] == "draft" for item in result["results"])


class TestGetShopListingsInactive:
    """Tests for get_shop_listings_inactive method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock EtsyListingClient with mocked dependencies."""
        with patch.object(EtsyListingClient, "__init__", return_value=None):
            client = EtsyListingClient.__new__(EtsyListingClient)
            client.db = MagicMock()
            client.user_id = 1
            client.shop_id = 12345678
            client.api_call = MagicMock()
            return client

    def test_get_shop_listings_inactive_success(self, mock_client):
        """Test successful retrieval of inactive listings."""
        expected_response = {
            "count": 1,
            "results": [
                {
                    "listing_id": 777777777,
                    "title": "Sold Out Brooch",
                    "state": "inactive",
                    "quantity": 0,
                }
            ],
        }
        mock_client.api_call.return_value = expected_response

        result = mock_client.get_shop_listings_inactive()

        mock_client.api_call.assert_called_once_with(
            "GET",
            "/application/shops/12345678/listings/inactive",
            params={"limit": 25, "offset": 0},
        )
        assert result["count"] == 1
        assert result["results"][0]["state"] == "inactive"


class TestGetListing:
    """Tests for get_listing method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock EtsyListingClient with mocked dependencies."""
        with patch.object(EtsyListingClient, "__init__", return_value=None):
            client = EtsyListingClient.__new__(EtsyListingClient)
            client.db = MagicMock()
            client.user_id = 1
            client.shop_id = 12345678
            client.api_call = MagicMock()
            return client

    def test_get_listing_success(self, mock_client):
        """Test successful retrieval of a single listing."""
        listing_id = 123456789
        expected_response = {
            "listing_id": listing_id,
            "title": "Beautiful Vintage Necklace",
            "description": "A stunning handmade vintage necklace.",
            "price": {"amount": 4999, "divisor": 100, "currency_code": "USD"},
            "quantity": 1,
            "state": "active",
            "who_made": "i_did",
            "when_made": "2020_2023",
            "taxonomy_id": 1234,
            "tags": ["vintage", "necklace", "handmade"],
            "materials": ["silver", "beads"],
        }
        mock_client.api_call.return_value = expected_response

        result = mock_client.get_listing(listing_id)

        mock_client.api_call.assert_called_once_with(
            "GET",
            f"/application/listings/{listing_id}",
        )
        assert result["listing_id"] == listing_id
        assert result["title"] == "Beautiful Vintage Necklace"
        assert result["state"] == "active"

    def test_get_listing_not_found(self, mock_client):
        """Test retrieval of a non-existent listing raises an error."""
        from shared.exceptions import EtsyAPIError

        listing_id = 999999999
        mock_client.api_call.side_effect = EtsyAPIError(
            message="Listing not found",
            status_code=404,
            response_body={"error": "Not found"},
        )

        with pytest.raises(EtsyAPIError) as exc_info:
            mock_client.get_listing(listing_id)

        assert exc_info.value.status_code == 404
        mock_client.api_call.assert_called_once_with(
            "GET",
            f"/application/listings/{listing_id}",
        )


class TestCreateDraftListing:
    """Tests for create_draft_listing method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock EtsyListingClient with mocked dependencies."""
        with patch.object(EtsyListingClient, "__init__", return_value=None):
            client = EtsyListingClient.__new__(EtsyListingClient)
            client.db = MagicMock()
            client.user_id = 1
            client.shop_id = 12345678
            client.api_call = MagicMock()
            return client

    def test_create_draft_listing_success(self, mock_client):
        """Test successful creation of a draft listing with required fields."""
        listing_data = {
            "quantity": 1,
            "title": "Handmade Vintage Necklace",
            "description": "Beautiful vintage necklace handcrafted with care.",
            "price": 49.99,
            "who_made": "i_did",
            "when_made": "2020_2023",
            "taxonomy_id": 1234,
        }
        expected_response = {
            "listing_id": 888888888,
            "title": listing_data["title"],
            "state": "draft",
            "quantity": 1,
            "price": {"amount": 4999, "divisor": 100, "currency_code": "USD"},
        }
        mock_client.api_call.return_value = expected_response

        result = mock_client.create_draft_listing(listing_data)

        mock_client.api_call.assert_called_once_with(
            "POST",
            "/application/shops/12345678/listings",
            json_data=listing_data,
        )
        assert result["listing_id"] == 888888888
        assert result["state"] == "draft"
        assert result["title"] == "Handmade Vintage Necklace"

    def test_create_draft_listing_minimal_fields(self, mock_client):
        """Test creation with only the minimum required fields."""
        listing_data = {
            "quantity": 1,
            "title": "Simple Item",
            "description": "Basic description",
            "price": 10.00,
            "who_made": "i_did",
            "when_made": "made_to_order",
            "taxonomy_id": 5678,
        }
        expected_response = {
            "listing_id": 999999999,
            "title": "Simple Item",
            "state": "draft",
        }
        mock_client.api_call.return_value = expected_response

        result = mock_client.create_draft_listing(listing_data)

        mock_client.api_call.assert_called_once_with(
            "POST",
            "/application/shops/12345678/listings",
            json_data=listing_data,
        )
        assert result["listing_id"] == 999999999

    def test_create_draft_listing_all_fields(self, mock_client):
        """Test creation with all optional fields populated."""
        listing_data = {
            # Required fields
            "quantity": 5,
            "title": "Premium Handmade Bracelet",
            "description": "Luxurious bracelet with premium materials.",
            "price": 149.99,
            "who_made": "i_did",
            "when_made": "2020_2023",
            "taxonomy_id": 2345,
            # Optional fields
            "shipping_profile_id": 111,
            "return_policy_id": 222,
            "materials": ["gold", "silver", "gems"],
            "shop_section_id": 333,
            "processing_min": 3,
            "processing_max": 7,
            "tags": ["premium", "bracelet", "handmade", "gift"],
            "styles": ["vintage", "elegant"],
            "item_weight": 0.05,
            "item_length": 20.0,
            "item_width": 2.0,
            "item_height": 0.5,
            "item_weight_unit": "kg",
            "item_dimensions_unit": "cm",
            "is_personalizable": True,
            "personalization_is_required": False,
            "personalization_char_count_max": 50,
            "personalization_instructions": "Enter name to engrave",
            "is_supply": False,
            "is_customizable": True,
            "should_auto_renew": True,
            "is_taxable": True,
            "type": "physical",
        }
        expected_response = {
            "listing_id": 101010101,
            "title": listing_data["title"],
            "state": "draft",
            "is_personalizable": True,
            "tags": listing_data["tags"],
        }
        mock_client.api_call.return_value = expected_response

        result = mock_client.create_draft_listing(listing_data)

        mock_client.api_call.assert_called_once_with(
            "POST",
            "/application/shops/12345678/listings",
            json_data=listing_data,
        )
        assert result["listing_id"] == 101010101
        assert result["is_personalizable"] is True
        assert result["tags"] == listing_data["tags"]


class TestUpdateListing:
    """Tests for update_listing method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock EtsyListingClient with mocked dependencies."""
        with patch.object(EtsyListingClient, "__init__", return_value=None):
            client = EtsyListingClient.__new__(EtsyListingClient)
            client.db = MagicMock()
            client.user_id = 1
            client.shop_id = 12345678
            client.api_call = MagicMock()
            return client

    def test_update_listing_success(self, mock_client):
        """Test successful update of a listing with multiple fields."""
        listing_id = 123456789
        listing_data = {
            "title": "Updated Vintage Necklace",
            "description": "Updated description with more details.",
            "price": 59.99,
            "quantity": 3,
        }
        expected_response = {
            "listing_id": listing_id,
            "title": "Updated Vintage Necklace",
            "description": "Updated description with more details.",
            "price": {"amount": 5999, "divisor": 100, "currency_code": "USD"},
            "quantity": 3,
            "state": "active",
        }
        mock_client.api_call.return_value = expected_response

        result = mock_client.update_listing(listing_id, listing_data)

        mock_client.api_call.assert_called_once_with(
            "PATCH",
            f"/application/shops/12345678/listings/{listing_id}",
            json_data=listing_data,
        )
        assert result["listing_id"] == listing_id
        assert result["title"] == "Updated Vintage Necklace"
        assert result["quantity"] == 3

    def test_update_listing_partial(self, mock_client):
        """Test partial update of a listing with only price change."""
        listing_id = 123456789
        listing_data = {
            "price": 39.99,
        }
        expected_response = {
            "listing_id": listing_id,
            "title": "Existing Title",
            "price": {"amount": 3999, "divisor": 100, "currency_code": "USD"},
            "state": "active",
        }
        mock_client.api_call.return_value = expected_response

        result = mock_client.update_listing(listing_id, listing_data)

        mock_client.api_call.assert_called_once_with(
            "PATCH",
            f"/application/shops/12345678/listings/{listing_id}",
            json_data=listing_data,
        )
        assert result["listing_id"] == listing_id
        assert result["price"]["amount"] == 3999


class TestDeleteListing:
    """Tests for delete_listing method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock EtsyListingClient with mocked dependencies."""
        with patch.object(EtsyListingClient, "__init__", return_value=None):
            client = EtsyListingClient.__new__(EtsyListingClient)
            client.db = MagicMock()
            client.user_id = 1
            client.shop_id = 12345678
            client.api_call = MagicMock()
            return client

    def test_delete_listing_success(self, mock_client):
        """Test successful deletion of a listing."""
        listing_id = 123456789
        mock_client.api_call.return_value = None

        # Should not raise any exception
        mock_client.delete_listing(listing_id)

        mock_client.api_call.assert_called_once_with(
            "DELETE",
            f"/application/shops/12345678/listings/{listing_id}",
        )

    def test_delete_listing_not_found(self, mock_client):
        """Test deletion of a non-existent listing raises an error."""
        from shared.exceptions import EtsyAPIError

        listing_id = 999999999
        mock_client.api_call.side_effect = EtsyAPIError(
            message="Listing not found",
            status_code=404,
            response_body={"error": "Not found"},
        )

        with pytest.raises(EtsyAPIError) as exc_info:
            mock_client.delete_listing(listing_id)

        assert exc_info.value.status_code == 404
        mock_client.api_call.assert_called_once_with(
            "DELETE",
            f"/application/shops/12345678/listings/{listing_id}",
        )


class TestShopIdUsage:
    """Tests verifying shop_id from parent class is properly used."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock EtsyListingClient with mocked dependencies."""
        with patch.object(EtsyListingClient, "__init__", return_value=None):
            client = EtsyListingClient.__new__(EtsyListingClient)
            client.db = MagicMock()
            client.user_id = 1
            client.shop_id = 99999999  # Different shop_id
            client.api_call = MagicMock()
            return client

    def test_shop_id_used_in_active_listings_endpoint(self, mock_client):
        """Test that shop_id is correctly used in the active listings endpoint."""
        mock_client.api_call.return_value = {"count": 0, "results": []}

        mock_client.get_shop_listings_active()

        call_args = mock_client.api_call.call_args
        assert "/shops/99999999/" in call_args[0][1]

    def test_shop_id_used_in_draft_listings_endpoint(self, mock_client):
        """Test that shop_id is correctly used in the draft listings endpoint."""
        mock_client.api_call.return_value = {"count": 0, "results": []}

        mock_client.get_shop_listings_draft()

        call_args = mock_client.api_call.call_args
        assert "/shops/99999999/" in call_args[0][1]

    def test_shop_id_used_in_create_endpoint(self, mock_client):
        """Test that shop_id is correctly used in the create listing endpoint."""
        mock_client.api_call.return_value = {"listing_id": 1, "state": "draft"}
        listing_data = {
            "quantity": 1,
            "title": "Test",
            "description": "Test",
            "price": 10.0,
            "who_made": "i_did",
            "when_made": "2020_2023",
            "taxonomy_id": 1,
        }

        mock_client.create_draft_listing(listing_data)

        call_args = mock_client.api_call.call_args
        assert "/shops/99999999/listings" in call_args[0][1]

    def test_shop_id_used_in_update_endpoint(self, mock_client):
        """Test that shop_id is correctly used in the update listing endpoint."""
        mock_client.api_call.return_value = {"listing_id": 1, "state": "active"}

        mock_client.update_listing(123, {"price": 20.0})

        call_args = mock_client.api_call.call_args
        assert "/shops/99999999/listings/123" in call_args[0][1]

    def test_shop_id_used_in_delete_endpoint(self, mock_client):
        """Test that shop_id is correctly used in the delete listing endpoint."""
        mock_client.api_call.return_value = None

        mock_client.delete_listing(123)

        call_args = mock_client.api_call.call_args
        assert "/shops/99999999/listings/123" in call_args[0][1]

    def test_get_listing_does_not_use_shop_id(self, mock_client):
        """Test that get_listing uses listing_id only (not shop_id)."""
        mock_client.api_call.return_value = {"listing_id": 555, "title": "Test"}

        mock_client.get_listing(555)

        call_args = mock_client.api_call.call_args
        # get_listing endpoint does not include shop_id
        assert "/application/listings/555" in call_args[0][1]
        assert "shops" not in call_args[0][1]
