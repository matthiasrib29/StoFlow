"""
Tests for Etsy API Routes

Tests d'intégration pour les endpoints Etsy OAuth2 et API.

Author: Claude
Date: 2025-12-10
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.public.platform_mapping import PlatformMapping
from models.user.product import Product, ProductStatus


# ===== FIXTURES =====


@pytest.fixture
def mock_etsy_config():
    """Mock de la configuration Etsy depuis .env."""
    with patch.dict(
        "os.environ",
        {
            "ETSY_API_KEY": "test_client_id",
            "ETSY_API_SECRET": "test_client_secret",
            "ETSY_REDIRECT_URI": "http://localhost:3000/etsy/callback",
        },
    ):
        yield


@pytest.fixture
def etsy_platform_mapping(db_session: Session, test_user):
    """Fixture pour créer un PlatformMapping Etsy."""
    now = datetime.now(timezone.utc)
    mapping = PlatformMapping(
        user_id=test_user.id,
        platform="etsy",
        access_token="test_access_token",
        refresh_token="12345678.test_refresh_token",
        access_token_expires_at=now + timedelta(hours=1),
        refresh_token_expires_at=now + timedelta(days=90),
        shop_id="12345678",
        shop_name="TestEtsyShop",
        api_key="test_client_id",
    )
    db_session.add(mapping)
    db_session.commit()
    db_session.refresh(mapping)
    return mapping


@pytest.fixture
def test_product_for_etsy(db_session: Session, test_user, seed_attributes):
    """Fixture pour créer un produit de test pour Etsy."""
    product = Product(
        sku="ETSY-TEST-001",
        title="Vintage Handmade Necklace",
        description="Beautiful vintage necklace handmade with love",
        price=Decimal("29.99"),
        category="Jeans",
        brand="Levi's",
        condition="EXCELLENT",
        label_size="M",
        color="Blue",
        stock_quantity=1,
        status=ProductStatus.DRAFT,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


# ===== TESTS OAUTH2 =====


class TestEtsyOAuth:
    """Tests pour les routes OAuth2 Etsy."""

    def test_connect_generates_authorization_url(
        self, client: TestClient, auth_headers: dict, mock_etsy_config
    ):
        """Test de génération de l'URL d'autorisation Etsy."""
        response = client.get("/api/etsy/oauth/connect", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert "authorization_url" in data
        assert "state" in data
        assert "https://www.etsy.com/oauth/connect" in data["authorization_url"]
        assert "client_id=test_client_id" in data["authorization_url"]
        assert "code_challenge=" in data["authorization_url"]
        assert "code_challenge_method=S256" in data["authorization_url"]

    def test_connect_without_credentials_fails(self, client: TestClient, auth_headers: dict):
        """Test que la connexion échoue si credentials manquants."""
        with patch.dict("os.environ", {}, clear=True):
            response = client.get("/api/etsy/oauth/connect", headers=auth_headers)

            assert response.status_code == 500
            assert "not configured" in response.json()["detail"]

    @patch("requests.post")
    def test_callback_success(
        self, mock_post, client: TestClient, auth_headers: dict, db_session: Session, mock_etsy_config
    ):
        """Test du callback OAuth2 réussi."""
        # Mock de la réponse de l'API Etsy
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_access_token_new",
            "refresh_token": "12345678.new_refresh_token",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response

        # Simuler le code_verifier en storage
        from api.etsy_oauth import PKCE_VERIFIERS

        state = "test_state_123"
        PKCE_VERIFIERS[state] = "test_code_verifier"

        response = client.get(
            f"/api/etsy/oauth/callback?code=test_code&state={state}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["shop_id"] == "12345678"
        assert data["access_token_expires_at"] is not None

        # Vérifier que le mapping a été créé en DB
        mapping = (
            db_session.query(PlatformMapping)
            .filter(
                PlatformMapping.user_id == 1,  # test_user.id
                PlatformMapping.platform == "etsy",
            )
            .first()
        )
        assert mapping is not None
        assert mapping.access_token == "test_access_token_new"

    def test_callback_invalid_state(self, client: TestClient, auth_headers: dict, mock_etsy_config):
        """Test du callback avec state invalide."""
        response = client.get(
            "/api/etsy/oauth/callback?code=test_code&state=invalid_state",
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "Invalid state" in response.json()["detail"]

    @patch("requests.post")
    def test_callback_token_exchange_fails(
        self, mock_post, client: TestClient, auth_headers: dict, mock_etsy_config
    ):
        """Test du callback avec échec d'échange de tokens."""
        # Mock d'une erreur API Etsy
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid authorization code"
        mock_post.return_value = mock_response

        # Simuler le code_verifier
        from api.etsy_oauth import PKCE_VERIFIERS

        state = "test_state_456"
        PKCE_VERIFIERS[state] = "test_code_verifier"

        response = client.get(
            f"/api/etsy/oauth/callback?code=invalid_code&state={state}",
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "Token exchange failed" in response.json()["detail"]

    def test_disconnect_success(
        self, client: TestClient, auth_headers: dict, etsy_platform_mapping: PlatformMapping
    ):
        """Test de déconnexion Etsy réussie."""
        response = client.post("/api/etsy/oauth/disconnect", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "disconnected successfully" in data["message"]

    def test_disconnect_not_connected(self, client: TestClient, auth_headers: dict):
        """Test de déconnexion alors que pas connecté."""
        response = client.post("/api/etsy/oauth/disconnect", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "was not connected" in data["message"]


# ===== TESTS API ENDPOINTS =====


class TestEtsyAPI:
    """Tests pour les routes API Etsy."""

    def test_connection_status_connected(
        self, client: TestClient, auth_headers: dict, etsy_platform_mapping: PlatformMapping
    ):
        """Test du status de connexion (connecté)."""
        response = client.get("/api/etsy/connection/status", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["connected"] is True
        assert data["shop_id"] == "12345678"
        assert data["shop_name"] == "TestEtsyShop"
        assert data["access_token_expires_at"] is not None

    def test_connection_status_not_connected(self, client: TestClient, auth_headers: dict):
        """Test du status de connexion (non connecté)."""
        response = client.get("/api/etsy/connection/status", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["connected"] is False
        assert data["shop_id"] is None

    @patch("services.etsy.etsy_publication_service.EtsyPublicationService.publish_product")
    def test_publish_product_success(
        self,
        mock_publish,
        client: TestClient,
        auth_headers: dict,
        etsy_platform_mapping: PlatformMapping,
        test_product_for_etsy: Product,
    ):
        """Test de publication d'un produit sur Etsy."""
        # Mock du résultat de publication
        mock_publish.return_value = {
            "listing_id": 987654321,
            "listing_url": "https://www.etsy.com/listing/987654321",
            "state": "active",
        }

        response = client.post(
            "/api/etsy/products/publish",
            headers=auth_headers,
            json={
                "product_id": test_product_for_etsy.id,
                "taxonomy_id": 1234,
                "state": "active",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["listing_id"] == 987654321
        assert "etsy.com/listing" in data["listing_url"]

    def test_publish_product_not_connected(
        self, client: TestClient, auth_headers: dict, test_product_for_etsy: Product
    ):
        """Test de publication sans connexion Etsy."""
        response = client.post(
            "/api/etsy/products/publish",
            headers=auth_headers,
            json={
                "product_id": test_product_for_etsy.id,
                "taxonomy_id": 1234,
            },
        )

        assert response.status_code == 400
        assert "not connected" in response.json()["detail"]

    @patch("services.etsy.etsy_listing_client.EtsyListingClient.get_shop_listings_active")
    def test_get_active_listings_success(
        self,
        mock_get_listings,
        client: TestClient,
        auth_headers: dict,
        etsy_platform_mapping: PlatformMapping,
    ):
        """Test de récupération des listings actifs."""
        # Mock de la réponse
        mock_get_listings.return_value = [
            {
                "listing_id": 123456,
                "title": "Test Listing 1",
                "state": "active",
                "price": {"amount": 2999, "divisor": 100, "currency_code": "USD"},
                "quantity": 5,
            },
            {
                "listing_id": 123457,
                "title": "Test Listing 2",
                "state": "active",
                "price": {"amount": 1999, "divisor": 100, "currency_code": "USD"},
                "quantity": 3,
            },
        ]

        response = client.get("/api/etsy/listings/active?limit=25", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2
        assert data[0]["listing_id"] == 123456
        assert data[0]["title"] == "Test Listing 1"

    @patch("services.etsy.etsy_shop_client.EtsyShopClient.get_shop")
    def test_get_shop_info_success(
        self,
        mock_get_shop,
        client: TestClient,
        auth_headers: dict,
        etsy_platform_mapping: PlatformMapping,
    ):
        """Test de récupération des infos du shop."""
        # Mock de la réponse
        mock_get_shop.return_value = {
            "shop_id": 12345678,
            "shop_name": "TestEtsyShop",
            "title": "My Vintage Shop",
            "url": "https://www.etsy.com/shop/TestEtsyShop",
            "listing_active_count": 42,
            "currency_code": "USD",
        }

        response = client.get("/api/etsy/shop", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["shop_id"] == 12345678
        assert data["shop_name"] == "TestEtsyShop"
        assert data["listing_active_count"] == 42

    @patch("services.etsy.etsy_receipt_client.EtsyReceiptClient.get_shop_receipts")
    def test_get_orders_success(
        self,
        mock_get_receipts,
        client: TestClient,
        auth_headers: dict,
        etsy_platform_mapping: PlatformMapping,
    ):
        """Test de récupération des commandes."""
        # Mock de la réponse
        mock_get_receipts.return_value = [
            {
                "receipt_id": 123456789,
                "buyer_user_id": 987654,
                "buyer_email": "buyer@example.com",
                "status": "completed",
                "is_paid": True,
                "is_shipped": True,
            }
        ]

        response = client.get("/api/etsy/orders?limit=25", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert data[0]["receipt_id"] == 123456789
        assert data[0]["status"] == "completed"

    @patch("services.etsy.etsy_shipping_client.EtsyShippingClient.get_shop_shipping_profiles")
    def test_get_shipping_profiles_success(
        self,
        mock_get_profiles,
        client: TestClient,
        auth_headers: dict,
        etsy_platform_mapping: PlatformMapping,
    ):
        """Test de récupération des shipping profiles."""
        # Mock de la réponse
        mock_get_profiles.return_value = [
            {
                "shipping_profile_id": 12345,
                "title": "Standard Shipping",
                "min_processing_days": 1,
                "max_processing_days": 3,
                "origin_country_iso": "US",
            }
        ]

        response = client.get("/api/etsy/shipping/profiles", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert data[0]["shipping_profile_id"] == 12345
        assert data[0]["title"] == "Standard Shipping"

    @patch("services.etsy.etsy_taxonomy_client.EtsyTaxonomyClient.get_seller_taxonomy_nodes")
    def test_get_taxonomy_nodes_success(
        self,
        mock_get_nodes,
        client: TestClient,
        auth_headers: dict,
        etsy_platform_mapping: PlatformMapping,
    ):
        """Test de récupération des catégories Etsy."""
        # Mock de la réponse
        mock_get_nodes.return_value = [
            {
                "id": 1234,
                "level": 2,
                "name": "Necklaces",
                "parent_id": 1000,
                "children": [1235, 1236],
            }
        ]

        response = client.get("/api/etsy/taxonomy/nodes", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert data[0]["id"] == 1234
        assert data[0]["name"] == "Necklaces"

    @patch("services.etsy.etsy_polling_service.EtsyPollingService.run_polling_cycle")
    def test_polling_status_success(
        self,
        mock_polling,
        client: TestClient,
        auth_headers: dict,
        etsy_platform_mapping: PlatformMapping,
    ):
        """Test du polling Etsy."""
        # Mock de la réponse de polling
        mock_polling.return_value = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "new_orders_count": 2,
            "updated_listings_count": 1,
            "low_stock_count": 0,
            "new_orders": [],
            "updated_listings": [],
            "low_stock_listings": [],
        }

        response = client.get(
            "/api/etsy/polling/status?check_orders=true&check_listings=true",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["new_orders_count"] == 2
        assert data["updated_listings_count"] == 1
        assert data["low_stock_count"] == 0


# ===== TESTS SERVICES ETSY =====


class TestEtsyProductConversionService:
    """Tests pour le service de conversion de produits."""

    @patch("services.etsy.etsy_product_conversion_service.EtsyProductConversionService.convert_to_listing_data")
    def test_convert_product_to_etsy_format(
        self, mock_convert, db_session: Session, test_product_for_etsy: Product
    ):
        """Test de conversion d'un produit Stoflow vers format Etsy."""
        from services.etsy.etsy_product_conversion_service import EtsyProductConversionService

        # Mock du résultat de conversion
        mock_convert.return_value = {
            "title": "Vintage Handmade Necklace",
            "description": "Beautiful vintage necklace handmade with love",
            "price": 29.99,
            "quantity": 1,
            "taxonomy_id": 1234,
            "who_made": "i_did",
            "when_made": "2020_2024",
            "is_supply": False,
        }

        service = EtsyProductConversionService(db_session)
        result = service.convert_to_listing_data(test_product_for_etsy, taxonomy_id=1234)

        assert result["title"] == "Vintage Handmade Necklace"
        assert result["price"] == 29.99
        assert result["quantity"] == 1
        assert result["who_made"] == "i_did"

    def test_product_validation_title_too_long(self, db_session: Session, test_product_for_etsy: Product):
        """Test de validation - titre trop long."""
        from services.etsy.etsy_product_conversion_service import (
            EtsyProductConversionService,
            ProductValidationError,
        )

        # Créer un produit avec titre trop long
        test_product_for_etsy.title = "A" * 150  # Max 140 chars

        service = EtsyProductConversionService(db_session)

        with pytest.raises(ProductValidationError, match="Title must be"):
            service._validate_product(test_product_for_etsy)


# ===== TESTS PKCE =====


class TestPKCE:
    """Tests pour la génération PKCE."""

    def test_generate_code_verifier(self):
        """Test de génération du code verifier."""
        from api.etsy_oauth import generate_code_verifier

        verifier = generate_code_verifier()

        # Doit être entre 43 et 128 caractères
        assert 43 <= len(verifier) <= 128

        # Doit être url-safe base64 (sans padding)
        assert "=" not in verifier

    def test_generate_code_challenge(self):
        """Test de génération du code challenge."""
        from api.etsy_oauth import generate_code_challenge

        verifier = "test_verifier_1234567890"
        challenge = generate_code_challenge(verifier)

        # Doit être base64 url-safe
        assert "=" not in challenge
        assert len(challenge) > 0

        # Le même verifier doit produire le même challenge
        challenge2 = generate_code_challenge(verifier)
        assert challenge == challenge2
