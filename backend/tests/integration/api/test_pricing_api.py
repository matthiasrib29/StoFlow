"""
Integration Tests for Pricing API

Tests the full request/response flow for POST /api/pricing/calculate endpoint.
Validates authentication, input validation, service integration, and error handling.

Architecture:
- Real database (Docker postgres test container)
- Real PricingService, repositories, calculators
- Mock only external LLM calls when necessary
- Full end-to-end flow testing

Created: 2026-01-12
Author: Claude
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.public.brand_group import BrandGroup
from models.product_attributes.model import Model


# ===== TEST CLASSES =====


class TestPricingCalculateAuthentication:
    """Test authentication requirements for the pricing endpoint."""

    def test_without_auth_token_returns_403(self, client: TestClient):
        """Without auth token should return 403 Forbidden (FastAPI behavior)."""
        response = client.post(
            "/api/pricing/calculate",
            json={
                "brand": "Nike",
                "category": "jacket",
                "materials": ["leather"],
                "condition_score": 4,
                "supplements": [],
                "condition_sensitivity": 1.0,
                "actual_origin": "China",
                "expected_origins": ["China"],
                "actual_decade": "2020s",
                "expected_decades": ["2020s"],
                "actual_trends": [],
                "expected_trends": [],
                "actual_features": [],
                "expected_features": []
            }
        )

        assert response.status_code == 403
        assert "detail" in response.json()

    def test_with_invalid_token_returns_401(self, client: TestClient):
        """With invalid token should return 401 Unauthorized."""
        response = client.post(
            "/api/pricing/calculate",
            json={
                "brand": "Nike",
                "category": "jacket",
                "materials": ["leather"],
                "condition_score": 4,
                "supplements": [],
                "condition_sensitivity": 1.0,
                "actual_origin": "China",
                "expected_origins": ["China"],
                "actual_decade": "2020s",
                "expected_decades": ["2020s"],
                "actual_trends": [],
                "expected_trends": [],
                "actual_features": [],
                "expected_features": []
            },
            headers={"Authorization": "Bearer invalid_token_12345"}
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_with_valid_token_returns_200(self, client: TestClient, auth_headers, db_session):
        """With valid token should return 200 OK (baseline test)."""
        # Mock LLM generation to avoid external API calls
        with patch('services.pricing.pricing_generation_service.PricingGenerationService.generate_brand_group') as mock_gen:
            mock_gen.return_value = BrandGroup(
                brand="Nike",
                group="jacket_leather",
                base_price=Decimal("120.00")
            )

            response = client.post(
                "/api/pricing/calculate",
                json={
                    "brand": "Nike",
                    "category": "jacket",
                    "materials": ["leather"],
                    "condition_score": 4,
                    "supplements": [],
                    "condition_sensitivity": 1.0,
                    "actual_origin": "China",
                    "expected_origins": ["China"],
                    "actual_decade": "2020s",
                    "expected_decades": ["2020s"],
                    "actual_trends": [],
                    "expected_trends": [],
                    "actual_features": [],
                    "expected_features": []
                },
                headers=auth_headers
            )

            assert response.status_code == 200


class TestPricingCalculateValidation:
    """Test input validation for the pricing endpoint."""

    def test_missing_required_fields_returns_422(self, client: TestClient, auth_headers):
        """Missing required fields should return 422 Unprocessable Entity."""
        response = client.post(
            "/api/pricing/calculate",
            json={
                "brand": "Nike",
                # Missing category
                "materials": ["leather"]
            },
            headers=auth_headers
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_invalid_condition_score_returns_422(self, client: TestClient, auth_headers):
        """Invalid condition_score (out of range 0-10) should return 422."""
        response = client.post(
            "/api/pricing/calculate",
            json={
                "brand": "Nike",
                "category": "jacket",
                "materials": ["leather"],
                "condition_score": 11,  # Invalid: must be 0-10
                "supplements": [],
                "condition_sensitivity": 1.0,
                "actual_origin": "China",
                "expected_origins": ["China"],
                "actual_decade": "2020s",
                "expected_decades": ["2020s"],
                "actual_trends": [],
                "expected_trends": [],
                "actual_features": [],
                "expected_features": []
            },
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_invalid_condition_sensitivity_returns_422(self, client: TestClient, auth_headers):
        """Invalid condition_sensitivity (out of range 0.5-1.5) should return 422."""
        response = client.post(
            "/api/pricing/calculate",
            json={
                "brand": "Nike",
                "category": "jacket",
                "materials": ["leather"],
                "condition_score": 4,
                "supplements": [],
                "condition_sensitivity": 2.0,  # Invalid: must be 0.5-1.5
                "actual_origin": "China",
                "expected_origins": ["China"],
                "actual_decade": "2020s",
                "expected_decades": ["2020s"],
                "actual_trends": [],
                "expected_trends": [],
                "actual_features": [],
                "expected_features": []
            },
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_valid_minimal_input_returns_200(self, client: TestClient, auth_headers, db_session):
        """Valid minimal input should return 200 OK."""
        # Mock LLM generation
        with patch('services.pricing.pricing_generation_service.PricingGenerationService.generate_brand_group') as mock_gen:
            mock_gen.return_value = BrandGroup(
                brand="Nike",
                group="jacket_leather",
                base_price=Decimal("120.00")
            )

            response = client.post(
                "/api/pricing/calculate",
                json={
                    "brand": "Nike",
                    "category": "jacket",
                    "materials": ["leather"],
                    "condition_score": 3,
                    "supplements": [],
                    "condition_sensitivity": 1.0,
                    "actual_origin": "China",
                    "expected_origins": [],
                    "actual_decade": "2020s",
                    "expected_decades": [],
                    "actual_trends": [],
                    "expected_trends": [],
                    "actual_features": [],
                    "expected_features": []
                },
                headers=auth_headers
            )

            if response.status_code != 200:
                print(f"RESPONSE STATUS: {response.status_code}")
                print(f"RESPONSE BODY: {response.json()}")
            assert response.status_code == 200

    def test_valid_full_input_returns_200(self, client: TestClient, auth_headers, db_session):
        """Valid full input with all fields should return 200 OK."""
        # Mock LLM generation
        with patch('services.pricing.pricing_generation_service.PricingGenerationService.generate_brand_group') as mock_gen:
            mock_gen.return_value = BrandGroup(
                brand="Nike",
                group="jacket_leather",
                base_price=Decimal("120.00")
            )

            response = client.post(
                "/api/pricing/calculate",
                json={
                    "brand": "Nike",
                    "category": "jacket",
                    "materials": ["leather", "rubber"],
                    "model_name": "Air Max 90",
                    "condition_score": 5,
                    "supplements": ["original_box", "tags"],
                    "condition_sensitivity": 1.2,
                    "actual_origin": "Vietnam",
                    "expected_origins": ["China", "Vietnam"],
                    "actual_decade": "2020s",
                    "expected_decades": ["2020s", "2010s"],
                    "actual_trends": ["streetwear", "retro"],
                    "expected_trends": ["streetwear"],
                    "actual_features": ["deadstock"],
                    "expected_features": ["deadstock"]
                },
                headers=auth_headers
            )

            assert response.status_code == 200


class TestPricingCalculateFlow:
    """Test the full pricing calculation flow with database interactions."""

    def test_with_existing_brand_group_fetches_from_db(self, client: TestClient, auth_headers, db_session):
        """When BrandGroup exists in DB, should fetch only (no generation)."""
        # Given: BrandGroup exists in DB
        brand_group = BrandGroup(
            brand="Nike",
            group="jacket_leather",
            base_price=Decimal("120.00")
        )
        db_session.add(brand_group)
        db_session.commit()

        # When: Calculate price
        response = client.post(
            "/api/pricing/calculate",
            json={
                "brand": "Nike",
                "category": "jacket",
                "materials": ["leather"],
                "condition_score": 4,
                "supplements": [],
                "condition_sensitivity": 1.0,
                "actual_origin": "China",
                "expected_origins": ["China"],
                "actual_decade": "2020s",
                "expected_decades": ["2020s"],
                "actual_trends": [],
                "expected_trends": [],
                "actual_features": [],
                "expected_features": []
            },
            headers=auth_headers
        )

        # Then: Success with correct structure
        assert response.status_code == 200
        data = response.json()
        assert "quick_price" in data
        assert "standard_price" in data
        assert "premium_price" in data
        assert data["base_price"] == "120.00"
        assert Decimal(data["quick_price"]) < Decimal(data["standard_price"]) < Decimal(data["premium_price"])

    def test_with_missing_brand_group_generates_via_llm(self, client: TestClient, auth_headers, db_session):
        """When BrandGroup missing, should generate via LLM and save to DB."""
        # determine_group("jacket", ["cotton"]) -> "jacket_natural"
        # Mock LLM generation (async method needs AsyncMock)
        # Must patch where the class is used (api.pricing), not where defined
        mock_brand_group = BrandGroup(
            brand="Adidas",
            group="jacket_natural",  # Matches determine_group output for cotton
            base_price=Decimal("100.00")
        )
        with patch('api.pricing.PricingGenerationService.generate_brand_group', new_callable=AsyncMock, return_value=mock_brand_group):

            # When: Calculate price (BrandGroup doesn't exist)
            response = client.post(
                "/api/pricing/calculate",
                json={
                    "brand": "Adidas",
                    "category": "jacket",
                    "materials": ["cotton"],  # Cotton -> natural -> jacket_natural
                    "condition_score": 3,
                    "supplements": [],
                    "condition_sensitivity": 1.0,
                    "actual_origin": "China",
                    "expected_origins": ["China"],
                    "actual_decade": "2020s",
                    "expected_decades": ["2020s"],
                    "actual_trends": [],
                    "expected_trends": [],
                    "actual_features": [],
                    "expected_features": []
                },
                headers=auth_headers
            )

            # Then: Success and BrandGroup saved to DB
            assert response.status_code == 200
            data = response.json()
            assert data["brand"] == "Adidas"
            assert data["group"] == "jacket_natural"
            assert data["base_price"] == "100.00"

            # Verify BrandGroup was saved to DB
            saved_bg = db_session.query(BrandGroup).filter_by(
                brand="Adidas",
                group="jacket_natural"
            ).first()
            assert saved_bg is not None
            assert saved_bg.base_price == Decimal("100.00")

    def test_with_existing_model_fetches_from_db(self, client: TestClient, auth_headers, db_session):
        """When Model exists in DB, should fetch only (no generation)."""
        # Given: BrandGroup and Model exist in DB
        brand_group = BrandGroup(
            brand="Nike",
            group="jacket_leather",
            base_price=Decimal("120.00")
        )
        db_session.add(brand_group)
        db_session.commit()

        model = Model(
            brand="Nike",
            group="jacket_leather",
            name="Air Max 90",
            coefficient=Decimal("1.5")
        )
        db_session.add(model)
        db_session.commit()

        # When: Calculate price with model_name
        response = client.post(
            "/api/pricing/calculate",
            json={
                "brand": "Nike",
                "category": "jacket",
                "materials": ["leather"],
                "model_name": "Air Max 90",
                "condition_score": 4,
                "supplements": [],
                "condition_sensitivity": 1.0,
                "actual_origin": "China",
                "expected_origins": ["China"],
                "actual_decade": "2020s",
                "expected_decades": ["2020s"],
                "actual_trends": [],
                "expected_trends": [],
                "actual_features": [],
                "expected_features": []
            },
            headers=auth_headers
        )

        # Then: Success with model coefficient applied
        assert response.status_code == 200
        data = response.json()
        assert data["model_coefficient"] == "1.50"
        assert data["model_name"] == "Air Max 90"

    def test_with_missing_model_generates_via_llm(self, client: TestClient, auth_headers, db_session):
        """When Model missing, should generate via LLM and save to DB."""
        # Given: BrandGroup exists
        brand_group = BrandGroup(
            brand="Nike",
            group="jacket_leather",
            base_price=Decimal("120.00")
        )
        db_session.add(brand_group)
        db_session.commit()

        # Mock LLM model generation (async method needs AsyncMock)
        mock_model = Model(
            brand="Nike",
            group="jacket_leather",
            name="Cortez",
            coefficient=Decimal("1.2")
        )
        with patch('services.pricing.pricing_generation_service.PricingGenerationService.generate_model', new_callable=AsyncMock, return_value=mock_model):

            # When: Calculate price with new model_name
            response = client.post(
                "/api/pricing/calculate",
                json={
                    "brand": "Nike",
                    "category": "jacket",
                    "materials": ["leather"],
                    "model_name": "Cortez",
                    "condition_score": 4,
                    "supplements": [],
                    "condition_sensitivity": 1.0,
                    "actual_origin": "China",
                    "expected_origins": ["China"],
                    "actual_decade": "2020s",
                    "expected_decades": ["2020s"],
                    "actual_trends": [],
                    "expected_trends": [],
                    "actual_features": [],
                    "expected_features": []
                },
                headers=auth_headers
            )

            # Then: Success and Model saved to DB
            assert response.status_code == 200
            data = response.json()
            assert data["model_coefficient"] == "1.20"
            assert data["model_name"] == "Cortez"

            # Verify Model was saved to DB
            saved_model = db_session.query(Model).filter_by(
                brand="Nike",
                name="Cortez"
            ).first()
            assert saved_model is not None
            assert saved_model.coefficient == Decimal("1.2")

    def test_without_model_name_uses_default_coefficient(self, client: TestClient, auth_headers, db_session):
        """When model_name not provided, should use model_coeff = 1.0."""
        # Given: BrandGroup exists
        brand_group = BrandGroup(
            brand="Nike",
            group="jacket_leather",
            base_price=Decimal("120.00")
        )
        db_session.add(brand_group)
        db_session.commit()

        # When: Calculate price without model_name
        response = client.post(
            "/api/pricing/calculate",
            json={
                "brand": "Nike",
                "category": "jacket",
                "materials": ["leather"],
                "condition_score": 4,
                "supplements": [],
                "condition_sensitivity": 1.0,
                "actual_origin": "China",
                "expected_origins": ["China"],
                "actual_decade": "2020s",
                "expected_decades": ["2020s"],
                "actual_trends": [],
                "expected_trends": [],
                "actual_features": [],
                "expected_features": []
            },
            headers=auth_headers
        )

        # Then: Success with model_coefficient = 1.0
        assert response.status_code == 200
        data = response.json()
        # Accept both "1.0" and "1.00" formats
        assert Decimal(data["model_coefficient"]) == Decimal("1.0")
        assert data["model_name"] is None

    def test_with_all_positive_adjustments(self, client: TestClient, auth_headers, db_session):
        """With all positive adjustments, premium > standard > quick."""
        # Given: BrandGroup exists
        brand_group = BrandGroup(
            brand="Nike",
            group="jacket_leather",
            base_price=Decimal("100.00")
        )
        db_session.add(brand_group)
        db_session.commit()

        # When: Calculate price with positive adjustments
        # Formula: (score - 5) * 0.06 * sensitivity + supplements
        # With score=10: (10-5) * 0.06 * 1.0 = 0.30 + original_box(0.05) = 0.35 → capped at 0.30
        response = client.post(
            "/api/pricing/calculate",
            json={
                "brand": "Nike",
                "category": "jacket",
                "materials": ["leather"],
                "condition_score": 10,  # (10-5) * 0.06 = +0.30 base
                "supplements": ["original_box"],  # +0.05 bonus
                "condition_sensitivity": 1.0,
                "actual_origin": "Italy",  # +0.15 (premium origin)
                "expected_origins": ["China"],
                "actual_decade": "1990s",  # +0.20 (vintage)
                "expected_decades": ["2020s"],
                "actual_trends": ["y2k"],  # +0.20
                "expected_trends": [],
                "actual_features": ["deadstock"],  # +0.30
                "expected_features": []
            },
            headers=auth_headers
        )

        # Then: Success with prices in correct order
        assert response.status_code == 200
        data = response.json()
        quick = Decimal(data["quick_price"])
        standard = Decimal(data["standard_price"])
        premium = Decimal(data["premium_price"])

        assert quick < standard < premium
        assert data["adjustments"]["condition"] == "0.30"  # Max cap (0.30 + 0.05 capped to 0.30)
        assert Decimal(data["adjustments"]["total"]) > 0  # Net positive

    def test_response_structure_complete(self, client: TestClient, auth_headers, db_session):
        """Response should have all required fields."""
        # Given: BrandGroup exists
        brand_group = BrandGroup(
            brand="Nike",
            group="jacket_leather",
            base_price=Decimal("120.00")
        )
        db_session.add(brand_group)
        db_session.commit()

        # When: Calculate price
        response = client.post(
            "/api/pricing/calculate",
            json={
                "brand": "Nike",
                "category": "jacket",
                "materials": ["leather"],
                "condition_score": 4,
                "supplements": [],
                "condition_sensitivity": 1.0,
                "actual_origin": "China",
                "expected_origins": ["China"],
                "actual_decade": "2020s",
                "expected_decades": ["2020s"],
                "actual_trends": [],
                "expected_trends": [],
                "actual_features": [],
                "expected_features": []
            },
            headers=auth_headers
        )

        # Then: All fields present
        assert response.status_code == 200
        data = response.json()

        # Price levels
        assert "quick_price" in data
        assert "standard_price" in data
        assert "premium_price" in data

        # Calculation breakdown
        assert "base_price" in data
        assert "model_coefficient" in data
        assert "adjustments" in data

        # Adjustment breakdown
        adjustments = data["adjustments"]
        assert "condition" in adjustments
        assert "origin" in adjustments
        assert "decade" in adjustments
        assert "trend" in adjustments
        assert "feature" in adjustments
        assert "total" in adjustments

        # Metadata
        assert "brand" in data
        assert "group" in data
        assert "model_name" in data

    def test_price_ratios_correct(self, client: TestClient, auth_headers, db_session):
        """Price ratios: quick = standard × 0.75, premium = standard × 1.30."""
        # Given: BrandGroup exists
        brand_group = BrandGroup(
            brand="Nike",
            group="jacket_leather",
            base_price=Decimal("100.00")
        )
        db_session.add(brand_group)
        db_session.commit()

        # When: Calculate price
        response = client.post(
            "/api/pricing/calculate",
            json={
                "brand": "Nike",
                "category": "jacket",
                "materials": ["leather"],
                "condition_score": 3,
                "supplements": [],
                "condition_sensitivity": 1.0,
                "actual_origin": "China",
                "expected_origins": ["China"],
                "actual_decade": "2020s",
                "expected_decades": ["2020s"],
                "actual_trends": [],
                "expected_trends": [],
                "actual_features": [],
                "expected_features": []
            },
            headers=auth_headers
        )

        # Then: Ratios are correct
        assert response.status_code == 200
        data = response.json()
        quick = Decimal(data["quick_price"])
        standard = Decimal(data["standard_price"])
        premium = Decimal(data["premium_price"])

        # Verify ratios (with small tolerance for rounding)
        expected_quick = (standard * Decimal("0.75")).quantize(Decimal("0.01"))
        expected_premium = (standard * Decimal("1.30")).quantize(Decimal("0.01"))

        assert abs(quick - expected_quick) < Decimal("0.02")
        assert abs(premium - expected_premium) < Decimal("0.02")


class TestPricingCalculateErrors:
    """Test error handling for the pricing endpoint."""

    def test_invalid_category_returns_400(self, client: TestClient, auth_headers, db_session):
        """Invalid category (group determination fails) should return 400."""
        response = client.post(
            "/api/pricing/calculate",
            json={
                "brand": "Nike",
                "category": "invalid_category_xyz",
                "materials": ["leather"],
                "condition_score": 4,
                "supplements": [],
                "condition_sensitivity": 1.0,
                "actual_origin": "China",
                "expected_origins": ["China"],
                "actual_decade": "2020s",
                "expected_decades": ["2020s"],
                "actual_trends": [],
                "expected_trends": [],
                "actual_features": [],
                "expected_features": []
            },
            headers=auth_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_llm_generation_failure_returns_504(self, client: TestClient, auth_headers, db_session):
        """LLM generation failure should return 504 Gateway Timeout."""
        # Mock LLM to raise ServiceError (async method needs AsyncMock)
        from shared.exceptions import ServiceError

        with patch(
            'services.pricing.pricing_generation_service.PricingGenerationService.generate_brand_group',
            new_callable=AsyncMock,
            side_effect=ServiceError("LLM API timeout")
        ):
            response = client.post(
                "/api/pricing/calculate",
                json={
                    "brand": "Nike",
                    "category": "jacket",
                    "materials": ["leather"],
                    "condition_score": 4,
                    "supplements": [],
                    "condition_sensitivity": 1.0,
                    "actual_origin": "China",
                    "expected_origins": ["China"],
                    "actual_decade": "2020s",
                    "expected_decades": ["2020s"],
                    "actual_trends": [],
                    "expected_trends": [],
                    "actual_features": [],
                    "expected_features": []
                },
                headers=auth_headers
            )

            assert response.status_code == 504
            data = response.json()
            assert "detail" in data
            # Message can be "failed", "generation", or "timed out"
            detail_lower = data["detail"].lower()
            assert any(keyword in detail_lower for keyword in ["failed", "generation", "timed out", "timeout"])

    def test_error_messages_clear(self, client: TestClient, auth_headers, db_session):
        """Error responses should include clear messages."""
        response = client.post(
            "/api/pricing/calculate",
            json={
                "brand": "Nike",
                "category": "invalid_xyz",
                "materials": ["leather"],
                "condition_score": 4,
                "supplements": [],
                "condition_sensitivity": 1.0,
                "actual_origin": "China",
                "expected_origins": ["China"],
                "actual_decade": "2020s",
                "expected_decades": ["2020s"],
                "actual_trends": [],
                "expected_trends": [],
                "actual_features": [],
                "expected_features": []
            },
            headers=auth_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)
        assert len(data["detail"]) > 0
