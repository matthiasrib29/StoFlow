"""
Tests Unitaires pour VintedPublisher

Tests de la logique de publication de produits sur Vinted.
Utilise des mocks pour les appels HTTP et la base de donnees.

Author: Claude
Date: 2026-01-08
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import httpx


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_cookies():
    """Mock des cookies Vinted valides."""
    return {
        "_csrf_token": "test-csrf-token-12345",
        "anon_id": "anon-id-67890",
        "session_id": "session-123",
    }


@pytest.fixture
def mock_cookies_missing_csrf():
    """Mock des cookies Vinted sans CSRF token."""
    return {
        "session_id": "session-123",
        "other_cookie": "value",
    }


@pytest.fixture
def sample_stoflow_product():
    """Donnees produit Stoflow pour publication."""
    return {
        "title": "Jean Levi's 501 Vintage",
        "description": "Jean vintage en excellent etat. Coupe droite classique.",
        "price": 45.99,
        "brand": "Levi's",
        "category": "Jeans",
        "condition": "EXCELLENT",
        "size_original": "W32L34",
        "color": "Blue",
        "images": [
            "https://stoflow.cdn/img1.jpg",
            "https://stoflow.cdn/img2.jpg",
            "https://stoflow.cdn/img3.jpg",
        ]
    }


@pytest.fixture
def sample_stoflow_product_minimal():
    """Donnees produit Stoflow minimales."""
    return {
        "title": "T-shirt Nike",
        "description": "T-shirt sport",
        "price": 15.00,
        "category": "T-shirt",
        "images": ["https://stoflow.cdn/img1.jpg"],
    }


@pytest.fixture
def mock_httpx_client():
    """Mock du client httpx."""
    client = MagicMock(spec=httpx.Client)
    return client


# =============================================================================
# TESTS - CSRF TOKEN
# =============================================================================


class TestGetCsrfToken:
    """Tests pour la recuperation du CSRF token."""

    @pytest.mark.asyncio
    async def test_get_csrf_token_from_csrf_cookie_success(self, mock_cookies):
        """Test recuperation CSRF token depuis cookie _csrf_token."""
        from services.vinted.vinted_publisher import VintedPublisher

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.csrf_token = None

            token = await publisher.get_csrf_token()

            assert token == "test-csrf-token-12345"
            assert publisher.csrf_token == "test-csrf-token-12345"

    @pytest.mark.asyncio
    async def test_get_csrf_token_from_anon_id_fallback(self, mock_cookies_missing_csrf):
        """Test recuperation CSRF token depuis anon_id en fallback."""
        from services.vinted.vinted_publisher import VintedPublisher

        cookies_with_anon = {**mock_cookies_missing_csrf, "anon_id": "anon-fallback-token"}

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = cookies_with_anon
            publisher.csrf_token = None

            token = await publisher.get_csrf_token()

            assert token == "anon-fallback-token"

    @pytest.mark.asyncio
    async def test_get_csrf_token_missing_raises_error(self, mock_cookies_missing_csrf):
        """Test erreur si aucun CSRF token disponible."""
        from services.vinted.vinted_publisher import VintedPublisher

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies_missing_csrf
            publisher.csrf_token = None

            with pytest.raises(ValueError, match="CSRF token not found"):
                await publisher.get_csrf_token()


# =============================================================================
# TESTS - UPLOAD PHOTO
# =============================================================================


class TestUploadPhoto:
    """Tests pour l'upload de photos."""

    @pytest.mark.asyncio
    async def test_upload_photo_success(self, mock_cookies):
        """Test upload photo avec succes."""
        from services.vinted.vinted_publisher import VintedPublisher

        mock_client = MagicMock(spec=httpx.Client)

        # Mock response pour /photos
        mock_photos_response = MagicMock()
        mock_photos_response.json.return_value = {
            "photo_id": 12345,
            "upload_url": "https://vinted.s3.amazonaws.com/upload/12345"
        }
        mock_photos_response.raise_for_status = MagicMock()

        mock_client.post.return_value = mock_photos_response

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.csrf_token = None
            publisher.client = mock_client

            # Mock httpx.put pour l'upload S3
            with patch('httpx.put') as mock_put:
                mock_put_response = MagicMock()
                mock_put_response.raise_for_status = MagicMock()
                mock_put.return_value = mock_put_response

                result = await publisher.upload_photo(b"fake_image_bytes")

                assert result["photo_id"] == 12345
                assert result["upload_url"] == "https://vinted.s3.amazonaws.com/upload/12345"
                mock_client.post.assert_called_once()
                mock_put.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_photo_api_error_raises_exception(self, mock_cookies):
        """Test erreur API lors de l'upload photo."""
        from services.vinted.vinted_publisher import VintedPublisher

        mock_client = MagicMock(spec=httpx.Client)
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error",
            request=MagicMock(),
            response=MagicMock(status_code=500)
        )
        mock_client.post.return_value = mock_response

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.csrf_token = None
            publisher.client = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                await publisher.upload_photo(b"fake_image_bytes")


# =============================================================================
# TESTS - UPLOAD PHOTOS (MULTIPLE)
# =============================================================================


class TestUploadPhotos:
    """Tests pour l'upload de plusieurs photos."""

    @pytest.mark.asyncio
    async def test_upload_photos_success(self, mock_cookies):
        """Test upload multiple photos avec succes."""
        from services.vinted.vinted_publisher import VintedPublisher

        image_urls = [
            "https://stoflow.cdn/img1.jpg",
            "https://stoflow.cdn/img2.jpg",
        ]

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.csrf_token = None

            # Mock upload_photo pour retourner des IDs differents
            async def mock_upload(image_bytes):
                return {"photo_id": hash(image_bytes) % 10000, "upload_url": "https://s3.com/upload"}

            publisher.upload_photo = AsyncMock(side_effect=[
                {"photo_id": 1001, "upload_url": "https://s3.com/1"},
                {"photo_id": 1002, "upload_url": "https://s3.com/2"},
            ])

            # Mock httpx.get pour telecharger les images
            with patch('httpx.get') as mock_get:
                mock_response = MagicMock()
                mock_response.content = b"fake_image_data"
                mock_response.raise_for_status = MagicMock()
                mock_get.return_value = mock_response

                photo_ids = await publisher.upload_photos(image_urls)

                assert len(photo_ids) == 2
                assert 1001 in photo_ids
                assert 1002 in photo_ids

    @pytest.mark.asyncio
    async def test_upload_photos_max_20_images(self, mock_cookies):
        """Test limite de 20 images maximum."""
        from services.vinted.vinted_publisher import VintedPublisher

        # 25 images (depasse la limite)
        image_urls = [f"https://stoflow.cdn/img{i}.jpg" for i in range(25)]

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.csrf_token = None

            upload_count = 0

            async def mock_upload(image_bytes):
                nonlocal upload_count
                upload_count += 1
                return {"photo_id": upload_count, "upload_url": "https://s3.com/upload"}

            publisher.upload_photo = AsyncMock(side_effect=mock_upload)

            with patch('httpx.get') as mock_get:
                mock_response = MagicMock()
                mock_response.content = b"fake_image_data"
                mock_response.raise_for_status = MagicMock()
                mock_get.return_value = mock_response

                photo_ids = await publisher.upload_photos(image_urls)

                # Doit limiter a 20 images
                assert len(photo_ids) <= 20

    @pytest.mark.asyncio
    async def test_upload_photos_no_images_raises_error(self, mock_cookies):
        """Test erreur si aucune image uploadee avec succes."""
        from services.vinted.vinted_publisher import VintedPublisher

        image_urls = ["https://stoflow.cdn/img1.jpg"]

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.csrf_token = None

            # Mock echec du telechargement
            with patch('httpx.get') as mock_get:
                mock_get.side_effect = Exception("Network error")

                with pytest.raises(ValueError, match="No images uploaded"):
                    await publisher.upload_photos(image_urls)

    @pytest.mark.asyncio
    async def test_upload_photos_partial_failure_continues(self, mock_cookies):
        """Test que l'upload continue malgre des echecs partiels."""
        from services.vinted.vinted_publisher import VintedPublisher

        image_urls = [
            "https://stoflow.cdn/img1.jpg",
            "https://stoflow.cdn/img2.jpg",
            "https://stoflow.cdn/img3.jpg",
        ]

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.csrf_token = None

            call_count = 0

            async def mock_upload(image_bytes):
                nonlocal call_count
                call_count += 1
                if call_count == 2:
                    raise Exception("Upload failed")
                return {"photo_id": 1000 + call_count, "upload_url": "https://s3.com/upload"}

            publisher.upload_photo = AsyncMock(side_effect=mock_upload)

            with patch('httpx.get') as mock_get:
                mock_response = MagicMock()
                mock_response.content = b"fake_image_data"
                mock_response.raise_for_status = MagicMock()
                mock_get.return_value = mock_response

                photo_ids = await publisher.upload_photos(image_urls)

                # 2 images sur 3 doivent avoir reussi
                assert len(photo_ids) == 2


# =============================================================================
# TESTS - SEARCH BRAND
# =============================================================================


class TestSearchBrand:
    """Tests pour la recherche de marques."""

    @pytest.mark.asyncio
    async def test_search_brand_exact_match_success(self, mock_cookies):
        """Test recherche marque avec correspondance exacte."""
        from services.vinted.vinted_publisher import VintedPublisher

        mock_client = MagicMock(spec=httpx.Client)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "brands": [
                {"id": 100, "title": "Levi's"},
                {"id": 101, "title": "Levi Strauss"},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.client = mock_client

            brand_id = await publisher.search_brand("Levi's")

            assert brand_id == 100

    @pytest.mark.asyncio
    async def test_search_brand_case_insensitive(self, mock_cookies):
        """Test recherche marque insensible a la casse."""
        from services.vinted.vinted_publisher import VintedPublisher

        mock_client = MagicMock(spec=httpx.Client)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "brands": [
                {"id": 200, "title": "Nike"},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.client = mock_client

            brand_id = await publisher.search_brand("NIKE")

            assert brand_id == 200

    @pytest.mark.asyncio
    async def test_search_brand_no_exact_match_returns_first(self, mock_cookies):
        """Test retourne premiere marque si pas de correspondance exacte."""
        from services.vinted.vinted_publisher import VintedPublisher

        mock_client = MagicMock(spec=httpx.Client)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "brands": [
                {"id": 300, "title": "Adidas Original"},
                {"id": 301, "title": "Adidas Sport"},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.client = mock_client

            brand_id = await publisher.search_brand("Adidas")

            assert brand_id == 300  # Premier resultat

    @pytest.mark.asyncio
    async def test_search_brand_not_found_returns_none(self, mock_cookies):
        """Test retourne None si marque non trouvee."""
        from services.vinted.vinted_publisher import VintedPublisher

        mock_client = MagicMock(spec=httpx.Client)
        mock_response = MagicMock()
        mock_response.json.return_value = {"brands": []}
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.client = mock_client

            brand_id = await publisher.search_brand("UnknownBrand")

            assert brand_id is None

    @pytest.mark.asyncio
    async def test_search_brand_api_error_returns_none(self, mock_cookies):
        """Test retourne None en cas d'erreur API."""
        from services.vinted.vinted_publisher import VintedPublisher

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.side_effect = Exception("Network error")

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.client = mock_client

            brand_id = await publisher.search_brand("Nike")

            assert brand_id is None


# =============================================================================
# TESTS - SEARCH SIZE
# =============================================================================


class TestSearchSize:
    """Tests pour la recherche de tailles."""

    @pytest.mark.asyncio
    async def test_search_size_exact_match_success(self, mock_cookies):
        """Test recherche taille avec correspondance exacte."""
        from services.vinted.vinted_publisher import VintedPublisher

        mock_client = MagicMock(spec=httpx.Client)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "sizes": [
                {"id": 50, "title": "M"},
                {"id": 51, "title": "L"},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.client = mock_client

            size_id = await publisher.search_size("M", catalog_id=1193)

            assert size_id == 50

    @pytest.mark.asyncio
    async def test_search_size_not_found_returns_none(self, mock_cookies):
        """Test retourne None si taille non trouvee."""
        from services.vinted.vinted_publisher import VintedPublisher

        mock_client = MagicMock(spec=httpx.Client)
        mock_response = MagicMock()
        mock_response.json.return_value = {"sizes": []}
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.client = mock_client

            size_id = await publisher.search_size("XXL", catalog_id=1193)

            assert size_id is None


# =============================================================================
# TESTS - SEARCH COLOR
# =============================================================================


class TestSearchColor:
    """Tests pour la recherche de couleurs."""

    @pytest.mark.asyncio
    async def test_search_color_exact_match_success(self, mock_cookies):
        """Test recherche couleur avec correspondance exacte."""
        from services.vinted.vinted_publisher import VintedPublisher

        mock_client = MagicMock(spec=httpx.Client)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "colors": [
                {"id": 10, "title": "Blue"},
                {"id": 11, "title": "Red"},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.client = mock_client

            color_id = await publisher.search_color("Blue")

            assert color_id == 10

    @pytest.mark.asyncio
    async def test_search_color_not_found_returns_none(self, mock_cookies):
        """Test retourne None si couleur non trouvee."""
        from services.vinted.vinted_publisher import VintedPublisher

        mock_client = MagicMock(spec=httpx.Client)
        mock_response = MagicMock()
        mock_response.json.return_value = {"colors": []}
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.client = mock_client

            color_id = await publisher.search_color("UnknownColor")

            assert color_id is None


# =============================================================================
# TESTS - CREATE LISTING
# =============================================================================


class TestCreateListing:
    """Tests pour la creation de listings."""

    @pytest.mark.asyncio
    async def test_create_listing_success(self, mock_cookies, sample_stoflow_product):
        """Test creation listing avec succes."""
        from services.vinted.vinted_publisher import VintedPublisher

        mock_client = MagicMock(spec=httpx.Client)

        # Mock response creation listing
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "item": {
                "id": 99999,
                "url": "https://www.vinted.fr/items/99999",
                "status": "active"
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.csrf_token = None
            publisher.client = mock_client

            # Mock les methodes auxiliaires
            publisher.get_csrf_token = AsyncMock(return_value="csrf-token")
            publisher.upload_photos = AsyncMock(return_value=[1001, 1002, 1003])
            publisher.search_brand = AsyncMock(return_value=100)
            publisher.search_size = AsyncMock(return_value=50)
            publisher.search_color = AsyncMock(return_value=10)

            # Mock VintedMapper
            with patch('services.vinted.vinted_publisher.VintedMapper') as mock_mapper:
                mock_mapper.stoflow_to_vinted.return_value = {
                    "title": "Jean Levi's 501 Vintage",
                    "description": "Jean vintage...",
                    "price": 45.99,
                    "catalog_id": 1193,
                    "status_id": 2,
                }

                result = await publisher.create_listing(sample_stoflow_product)

                assert result["item_id"] == 99999
                assert result["url"] == "https://www.vinted.fr/items/99999"
                assert result["status"] == "active"

    @pytest.mark.asyncio
    async def test_create_listing_without_optional_fields(
        self, mock_cookies, sample_stoflow_product_minimal
    ):
        """Test creation listing sans champs optionnels."""
        from services.vinted.vinted_publisher import VintedPublisher

        mock_client = MagicMock(spec=httpx.Client)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "item": {"id": 88888, "url": "https://vinted.fr/items/88888"}
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.csrf_token = None
            publisher.client = mock_client

            publisher.get_csrf_token = AsyncMock(return_value="csrf-token")
            publisher.upload_photos = AsyncMock(return_value=[1001])
            publisher.search_brand = AsyncMock(return_value=None)
            publisher.search_size = AsyncMock(return_value=None)
            publisher.search_color = AsyncMock(return_value=None)

            with patch('services.vinted.vinted_publisher.VintedMapper') as mock_mapper:
                mock_mapper.stoflow_to_vinted.return_value = {
                    "title": "T-shirt Nike",
                    "description": "T-shirt sport",
                    "price": 15.00,
                    "catalog_id": 1203,
                    "status_id": 3,
                }

                result = await publisher.create_listing(sample_stoflow_product_minimal)

                assert result["item_id"] == 88888

    @pytest.mark.asyncio
    async def test_create_listing_api_error_raises_exception(
        self, mock_cookies, sample_stoflow_product
    ):
        """Test erreur API lors de la creation."""
        from services.vinted.vinted_publisher import VintedPublisher

        mock_client = MagicMock(spec=httpx.Client)
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Forbidden", request=MagicMock(), response=MagicMock(status_code=403)
        )
        mock_client.post.return_value = mock_response

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.csrf_token = None
            publisher.client = mock_client

            publisher.get_csrf_token = AsyncMock(return_value="csrf-token")
            publisher.upload_photos = AsyncMock(return_value=[1001])
            publisher.search_brand = AsyncMock(return_value=None)
            publisher.search_size = AsyncMock(return_value=None)
            publisher.search_color = AsyncMock(return_value=None)

            with patch('services.vinted.vinted_publisher.VintedMapper') as mock_mapper:
                mock_mapper.stoflow_to_vinted.return_value = {"title": "Test", "catalog_id": 1193}

                with pytest.raises(httpx.HTTPStatusError):
                    await publisher.create_listing(sample_stoflow_product)


# =============================================================================
# TESTS - UPDATE LISTING
# =============================================================================


class TestUpdateListing:
    """Tests pour la mise a jour de listings."""

    @pytest.mark.asyncio
    async def test_update_listing_success(self, mock_cookies, sample_stoflow_product):
        """Test mise a jour listing avec succes."""
        from services.vinted.vinted_publisher import VintedPublisher

        mock_client = MagicMock(spec=httpx.Client)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "item": {
                "id": 99999,
                "title": "Updated Title",
                "price": 39.99,
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.put.return_value = mock_response

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.csrf_token = None
            publisher.client = mock_client

            publisher.get_csrf_token = AsyncMock(return_value="csrf-token")

            with patch('services.vinted.vinted_publisher.VintedMapper') as mock_mapper:
                mock_mapper.stoflow_to_vinted.return_value = {
                    "title": "Updated Title",
                    "price": 39.99,
                }

                result = await publisher.update_listing(99999, sample_stoflow_product)

                assert result["id"] == 99999
                mock_client.put.assert_called_once()


# =============================================================================
# TESTS - DELETE LISTING
# =============================================================================


class TestDeleteListing:
    """Tests pour la suppression de listings."""

    @pytest.mark.asyncio
    async def test_delete_listing_success_200(self, mock_cookies):
        """Test suppression listing avec status 200."""
        from services.vinted.vinted_publisher import VintedPublisher

        mock_client = MagicMock(spec=httpx.Client)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.delete.return_value = mock_response

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.csrf_token = None
            publisher.client = mock_client

            publisher.get_csrf_token = AsyncMock(return_value="csrf-token")

            result = await publisher.delete_listing(99999)

            assert result is True

    @pytest.mark.asyncio
    async def test_delete_listing_success_204(self, mock_cookies):
        """Test suppression listing avec status 204 (No Content)."""
        from services.vinted.vinted_publisher import VintedPublisher

        mock_client = MagicMock(spec=httpx.Client)
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_client.delete.return_value = mock_response

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.csrf_token = None
            publisher.client = mock_client

            publisher.get_csrf_token = AsyncMock(return_value="csrf-token")

            result = await publisher.delete_listing(99999)

            assert result is True

    @pytest.mark.asyncio
    async def test_delete_listing_failure_returns_false(self, mock_cookies):
        """Test suppression listing echouee retourne False."""
        from services.vinted.vinted_publisher import VintedPublisher

        mock_client = MagicMock(spec=httpx.Client)
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client.delete.return_value = mock_response

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.csrf_token = None
            publisher.client = mock_client

            publisher.get_csrf_token = AsyncMock(return_value="csrf-token")

            result = await publisher.delete_listing(99999)

            assert result is False


# =============================================================================
# TESTS - CONTEXT MANAGER
# =============================================================================


class TestContextManager:
    """Tests pour le context manager."""

    @pytest.mark.asyncio
    async def test_context_manager_closes_client(self, mock_cookies):
        """Test que le context manager ferme le client."""
        from services.vinted.vinted_publisher import VintedPublisher

        mock_client = MagicMock(spec=httpx.Client)

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.client = mock_client

            async with publisher:
                pass

            mock_client.close.assert_called_once()

    def test_close_method_closes_client(self, mock_cookies):
        """Test que close() ferme le client."""
        from services.vinted.vinted_publisher import VintedPublisher

        mock_client = MagicMock(spec=httpx.Client)

        with patch.object(VintedPublisher, '__init__', lambda x, y: None):
            publisher = VintedPublisher.__new__(VintedPublisher)
            publisher.cookies = mock_cookies
            publisher.client = mock_client

            publisher.close()

            mock_client.close.assert_called_once()
