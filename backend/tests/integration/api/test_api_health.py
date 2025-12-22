"""
Tests for API Health and Core Endpoints

Smoke tests to verify the API is running and core endpoints work.
These tests should be run after every deployment.

Endpoints Tested:
- GET / (root)
- GET /health
- GET /api/attributes/* (all attribute types)
- Basic auth endpoints (register, login structure)
"""

import pytest
from fastapi.testclient import TestClient


class TestAPIHealth:
    """Tests for API health endpoints."""

    def test_root_endpoint(self, client: TestClient):
        """Test that root endpoint returns welcome message."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "status" in data

    def test_health_endpoint(self, client: TestClient):
        """Test that health endpoint returns OK status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy" or "ok" in str(data).lower()


class TestAPIDocumentation:
    """Tests for API documentation endpoints."""

    def test_openapi_schema_available(self, client: TestClient):
        """Test that OpenAPI schema is available."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data

    def test_docs_endpoint_available(self, client: TestClient):
        """Test that Swagger UI docs are available."""
        response = client.get("/docs")

        # Should return HTML or redirect
        assert response.status_code in [200, 307]

    def test_redoc_endpoint_available(self, client: TestClient):
        """Test that ReDoc docs are available."""
        response = client.get("/redoc")

        # Should return HTML or redirect
        assert response.status_code in [200, 307]


class TestAuthEndpointsStructure:
    """Tests for auth endpoints structure (not functionality)."""

    def test_register_endpoint_exists(self, client: TestClient):
        """Test that register endpoint exists and accepts POST."""
        # Send empty body to check endpoint exists
        response = client.post("/api/auth/register", json={})

        # Should return 422 (validation error) not 404
        assert response.status_code != 404, "Register endpoint should exist"
        assert response.status_code == 422  # Validation error expected

    def test_login_endpoint_exists(self, client: TestClient):
        """Test that login endpoint exists and accepts POST."""
        response = client.post("/api/auth/login", json={})

        # Should return 422 (validation error) not 404
        assert response.status_code != 404, "Login endpoint should exist"
        assert response.status_code == 422  # Validation error expected

    def test_protected_endpoint_requires_auth(self, client: TestClient):
        """Test that protected endpoints require authentication."""
        # Products endpoint requires auth
        response = client.get("/api/products")

        # Should return 401 (unauthorized)
        assert response.status_code == 401


class TestProductEndpointsStructure:
    """Tests for product endpoints structure."""

    def test_products_list_requires_auth(self, client: TestClient):
        """Test that products list requires authentication."""
        response = client.get("/api/products")

        assert response.status_code == 401

    def test_products_create_requires_auth(self, client: TestClient):
        """Test that product creation requires authentication."""
        response = client.post("/api/products", json={})

        assert response.status_code == 401


class TestAttributeEndpointsComplete:
    """Complete tests for all attribute endpoints."""

    ATTRIBUTE_ENDPOINTS = [
        "/api/attributes/",
        "/api/attributes/categories",
        "/api/attributes/conditions",
        "/api/attributes/genders",
        "/api/attributes/seasons",
        "/api/attributes/brands",
        "/api/attributes/colors",
        "/api/attributes/materials",
        "/api/attributes/fits",
        "/api/attributes/sizes",
    ]

    @pytest.mark.parametrize("endpoint", ATTRIBUTE_ENDPOINTS)
    def test_attribute_endpoint_returns_200(self, client: TestClient, endpoint: str):
        """Test that each attribute endpoint returns 200."""
        response = client.get(endpoint)

        assert response.status_code == 200, f"{endpoint} should return 200"

    @pytest.mark.parametrize("endpoint", ATTRIBUTE_ENDPOINTS[1:])  # Skip list endpoint
    def test_attribute_endpoint_returns_list(self, client: TestClient, endpoint: str):
        """Test that attribute data endpoints return lists."""
        response = client.get(endpoint)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), f"{endpoint} should return a list"


class TestCORSHeaders:
    """Tests for CORS headers."""

    def test_cors_headers_present(self, client: TestClient):
        """Test that CORS headers are present in responses."""
        response = client.options(
            "/api/attributes/categories",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )

        # CORS preflight should succeed
        assert response.status_code in [200, 204]


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_for_unknown_endpoint(self, client: TestClient):
        """Test that unknown endpoints return 404."""
        response = client.get("/api/this-endpoint-does-not-exist")

        assert response.status_code == 404

    def test_405_for_wrong_method(self, client: TestClient):
        """Test that wrong HTTP method returns 405."""
        # Attributes endpoint only accepts GET, not DELETE
        response = client.delete("/api/attributes/categories")

        assert response.status_code == 405

    def test_422_for_invalid_query_params(self, client: TestClient):
        """Test that invalid query params return 422."""
        # limit must be between 1 and 500
        response = client.get("/api/attributes/categories?limit=9999")

        assert response.status_code == 422


class TestAPIVersioning:
    """Tests for API versioning and structure."""

    def test_api_prefix_required(self, client: TestClient):
        """Test that /api prefix is used for API routes."""
        # Direct access without /api should not work for API endpoints
        response = client.get("/attributes/categories")

        # Should be 404 (endpoint doesn't exist without /api)
        assert response.status_code == 404


# ===== DEPLOYMENT SMOKE TEST =====


class TestDeploymentSmokeTest:
    """
    Single comprehensive test for post-deployment verification.

    Run this test after every deployment to verify basic functionality.
    """

    def test_deployment_health_check(self, client: TestClient):
        """
        Comprehensive health check for deployment.

        Verifies:
        1. API is responding
        2. Database connection works (via attributes)
        3. All attribute types are queryable
        4. Auth endpoints exist
        """
        errors = []

        # 1. Check root endpoint
        response = client.get("/")
        if response.status_code != 200:
            errors.append(f"Root endpoint failed: {response.status_code}")

        # 2. Check health endpoint
        response = client.get("/health")
        if response.status_code != 200:
            errors.append(f"Health endpoint failed: {response.status_code}")

        # 3. Check all attribute endpoints
        attribute_types = [
            "categories", "conditions", "genders", "seasons",
            "brands", "colors", "materials", "fits", "sizes"
        ]
        for attr_type in attribute_types:
            response = client.get(f"/api/attributes/{attr_type}")
            if response.status_code != 200:
                errors.append(f"Attributes/{attr_type} failed: {response.status_code}")
            else:
                try:
                    data = response.json()
                    if not isinstance(data, list):
                        errors.append(f"Attributes/{attr_type} didn't return list")
                except Exception as e:
                    errors.append(f"Attributes/{attr_type} JSON error: {e}")

        # 4. Check auth endpoints exist
        response = client.post("/api/auth/register", json={})
        if response.status_code == 404:
            errors.append("Auth register endpoint missing")

        response = client.post("/api/auth/login", json={})
        if response.status_code == 404:
            errors.append("Auth login endpoint missing")

        # Report all errors
        assert len(errors) == 0, f"Deployment issues: {'; '.join(errors)}"
