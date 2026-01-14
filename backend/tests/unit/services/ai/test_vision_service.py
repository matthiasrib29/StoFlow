"""
Unit tests for AIVisionService.

Tests the AI image analysis functionality with mocked Gemini API calls to avoid costs.
Tests credit checking, consumption, logging, and error handling.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from decimal import Decimal
from datetime import datetime

from sqlalchemy import select

from services.ai.vision_service import AIVisionService
from models.public.ai_credit import AICredit
from models.user.ai_generation_log import AIGenerationLog
from models.public.user import User, SubscriptionTier
from models.public.subscription_quota import SubscriptionQuota
from schemas.ai_schemas import VisionExtractedAttributes
from shared.exceptions import AIQuotaExceededError, AIGenerationError


class TestAIVisionServiceCredits:
    """Test credit checking and consumption logic."""

    def test_check_credits_sufficient(self, db_session, test_user, free_quota):
        """Test credit check passes when user has sufficient credits."""
        # Extract user from tuple
        user, _ = test_user

        # Arrange: Create AI credit record with credits
        # User already has FREE tier set from fixture
        ai_credit = AICredit(
            user_id=user.id,
            ai_credits_purchased=5,
            ai_credits_used_this_month=2
        )
        db_session.add(ai_credit)
        db_session.commit()

        # Act & Assert: Should not raise
        AIVisionService._check_credits(db_session, user.id, monthly_credits=10)

    def test_check_credits_insufficient_raises_error(self, db_session, test_user, free_quota):
        """Test credit check raises error when credits exhausted."""
        # Extract user from tuple
        user, _ = test_user

        # Arrange: User with no credits left
        ai_credit = AICredit(
            user_id=user.id,
            ai_credits_purchased=0,
            ai_credits_used_this_month=10
        )
        db_session.add(ai_credit)
        db_session.commit()

        # Act & Assert
        with pytest.raises(AIQuotaExceededError) as exc_info:
            AIVisionService._check_credits(db_session, user.id, monthly_credits=10)

        assert "Crédits IA insuffisants" in str(exc_info.value)

    def test_check_credits_creates_record_if_missing(self, db_session, test_user, free_quota):
        """Test credit check creates AICredit record if it doesn't exist."""
        # Extract user from tuple
        user, _ = test_user

        # Arrange: No AI credit record
        stmt = select(AICredit).where(AICredit.user_id == user.id)
        assert db_session.execute(stmt).scalar_one_or_none() is None

        # Act
        AIVisionService._check_credits(db_session, user.id, monthly_credits=10)
        db_session.flush()

        # Assert: Record created
        stmt = select(AICredit).where(AICredit.user_id == user.id)
        ai_credit = db_session.execute(stmt).scalar_one_or_none()
        assert ai_credit is not None
        assert ai_credit.ai_credits_purchased == 0
        assert ai_credit.ai_credits_used_this_month == 0

    def test_consume_credit_increments_usage(self, db_session, test_user, free_quota):
        """Test consuming a credit increments the used_this_month counter."""
        # Extract user from tuple
        user, _ = test_user

        # Arrange
        ai_credit = AICredit(
            user_id=user.id,
            ai_credits_purchased=10,
            ai_credits_used_this_month=5
        )
        db_session.add(ai_credit)
        db_session.commit()

        # Act
        AIVisionService._consume_credit(db_session, user.id)
        db_session.commit()

        # Assert
        db_session.refresh(ai_credit)
        assert ai_credit.ai_credits_used_this_month == 6

    def test_consume_credit_handles_missing_record(self, db_session, test_user, free_quota):
        """Test consume_credit doesn't crash if AICredit record doesn't exist."""
        # Extract user from tuple
        user, _ = test_user

        # Arrange: No AI credit record
        stmt = select(AICredit).where(AICredit.user_id == user.id)
        assert db_session.execute(stmt).scalar_one_or_none() is None

        # Act & Assert: Should not raise
        AIVisionService._consume_credit(db_session, user.id)


class TestAIVisionServicePrompt:
    """Test prompt generation with database attributes."""

    def test_fetch_product_attributes_returns_expected_keys(self, db_session):
        """Test _fetch_product_attributes returns expected attribute keys.

        Note: This test uses the real database because the method does
        local imports and complex queries. It verifies structure, not content.
        """
        # Act
        attributes = AIVisionService._fetch_product_attributes(db_session)

        # Assert: Check expected keys are present
        expected_keys = [
            "categories", "colors", "conditions", "fits", "genders",
            "lengths", "materials", "necklines", "patterns", "seasons",
            "sports", "closures", "rises", "sleeve_lengths", "stretches",
            "linings", "decades", "origins", "trends", "condition_sups",
            "unique_features"
        ]
        for key in expected_keys:
            assert key in attributes, f"Missing key: {key}"

        # Brands are NOT in attributes (not sent to AI anymore)
        assert "brands" not in attributes

    def test_build_prompt_contains_english(self):
        """Test that the prompt is in English."""
        # Arrange - Note: brands are not included anymore
        attributes = {
            "categories": ["T-shirt", "Jeans"],
            "colors": ["Blue", "Red"],
            "conditions": [],
            "materials": [],
            "fits": [],
            "genders": [],
            "seasons": [],
            "patterns": [],
            "lengths": [],
            "necklines": [],
            "sports": [],
            "closures": [],
            "rises": [],
            "sleeve_lengths": [],
            "stretches": [],
            "linings": [],
            "decades": [],
            "origins": [],
            "trends": [],
            "condition_sups": [],
            "unique_features": []
        }

        # Act
        prompt = AIVisionService._build_prompt(attributes)

        # Assert
        assert "You are an expert" in prompt
        assert "CRITICAL RULES" in prompt
        assert "VALID ATTRIBUTE VALUES" in prompt
        assert "**Categories:**" in prompt
        assert "**Colors:**" in prompt
        # Note: Brands are NOT sent to AI anymore
        assert "**Brands:**" not in prompt

    def test_build_prompt_injects_attributes(self):
        """Test that the prompt injects attribute values."""
        # Arrange - Note: brands are not included anymore
        attributes = {
            "categories": ["T-shirt", "Jeans"],
            "colors": ["Blue", "Red", "Black"],
            "conditions": ["New", "Used"],
            "materials": ["Cotton", "Polyester"],
            "fits": ["Regular", "Slim"],
            "genders": [],
            "seasons": [],
            "patterns": [],
            "lengths": [],
            "necklines": [],
            "sports": [],
            "closures": [],
            "rises": [],
            "sleeve_lengths": [],
            "stretches": [],
            "linings": [],
            "decades": [],
            "origins": [],
            "trends": [],
            "condition_sups": [],
            "unique_features": []
        }

        # Act
        prompt = AIVisionService._build_prompt(attributes)

        # Assert: Categories and colors are injected
        assert "T-shirt" in prompt
        assert "Jeans" in prompt
        assert "Blue" in prompt
        assert "Cotton" in prompt


class TestAIVisionServiceLogging:
    """Test AI generation logging."""

    @pytest.mark.skip(reason="Method _log_generation was removed - logging is now done inline in analyze_images")
    def test_log_generation_creates_record(self, db_session, test_user, free_quota):
        """Test that log_generation creates an AIGenerationLog record."""
        # Extract user from tuple
        user, _ = test_user
        user_schema = f"user_{user.id}"

        extracted_attrs = VisionExtractedAttributes(
            title="Nike Air Max",
            description="Great shoes",
            brand="Nike",
            color=["Blue"]  # color is now a list
        )

        # Act
        AIVisionService._log_generation(
            db=db_session,
            user_id=user.id,
            model="gemini-3-flash",
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            cost=0.05,
            processing_time_ms=1500,
            input_data={"images": 2},
            output_data=extracted_attrs.model_dump()
        )
        db_session.commit()

        # Assert
        from sqlalchemy import text
        log = db_session.execute(
            text(f"SELECT * FROM {user_schema}.ai_generation_logs ORDER BY created_at DESC LIMIT 1")
        ).fetchone()

        assert log is not None
        # Column indices may vary, check key values exist
        values = list(log)
        assert "gemini-3-flash" in values
        assert 300 in values  # total_tokens
        assert Decimal("0.05") in values or 0.05 in values  # cost


class TestAIVisionServiceAnalyzeImages:
    """Test the full analyze_images flow with mocked Gemini."""

    @pytest.mark.asyncio
    @patch('services.ai.vision_service.httpx.AsyncClient')
    @patch('services.ai.vision_service.genai.Client')
    @patch('services.ai.vision_service.AIVisionService._fetch_product_attributes')
    async def test_analyze_images_success(
        self,
        mock_fetch_attrs,
        mock_genai_client,
        mock_httpx,
        db_session,
        test_user,
        test_product,
        free_quota
    ):
        """Test successful image analysis with mocked Gemini."""
        # Extract user from tuple
        user, _ = test_user

        # Arrange: Setup user credits
        # User already has FREE tier configured from fixture

        ai_credit = AICredit(
            user_id=user.id,
            ai_credits_purchased=5,
            ai_credits_used_this_month=0
        )
        db_session.add(ai_credit)
        db_session.commit()

        # Mock attributes - Note: brands are not included anymore
        mock_fetch_attrs.return_value = {
            "categories": ["T-shirt"],
            "colors": ["Blue", "Red"],
            "conditions": [],
            "materials": [],
            "fits": [],
            "genders": [],
            "seasons": [],
            "patterns": [],
            "lengths": [],
            "necklines": [],
            "sports": [],
            "closures": [],
            "rises": [],
            "sleeve_lengths": [],
            "stretches": [],
            "linings": [],
            "decades": [],
            "origins": [],
            "trends": [],
            "condition_sups": [],
            "unique_features": []
        }

        # Mock httpx image download
        mock_http_client = AsyncMock()
        mock_http_response = MagicMock()  # Use MagicMock since .content is an attribute, not async
        mock_http_response.content = b"fake_image_data"
        mock_http_response.raise_for_status = MagicMock()  # Sync method
        mock_http_response.headers = MagicMock()
        mock_http_response.headers.get = MagicMock(return_value="image/jpeg")
        mock_http_client.get = AsyncMock(return_value=mock_http_response)
        mock_httpx.return_value.__aenter__.return_value = mock_http_client

        # Mock Gemini response
        mock_response = MagicMock()
        mock_response.text = """{
            "title": "Nike Air Max",
            "description": "Great running shoes",
            "brand": "Nike",
            "color": "Blue",
            "category": "T-shirt",
            "confidence": 0.95
        }"""
        mock_response.usage_metadata = MagicMock()
        mock_response.usage_metadata.prompt_token_count = 150
        mock_response.usage_metadata.candidates_token_count = 100
        mock_response.usage_metadata.total_token_count = 250

        mock_client_instance = MagicMock()
        mock_client_instance.models.generate_content.return_value = mock_response
        mock_genai_client.return_value = mock_client_instance

        # Mock image URLs
        test_product.images = [
            {"url": "https://example.com/img1.jpg", "order": 0},
            {"url": "https://example.com/img2.jpg", "order": 1}
        ]
        db_session.commit()

        # Act
        with patch('services.ai.vision_service.settings') as mock_settings:
            mock_settings.gemini_api_key = "test_key"
            mock_settings.gemini_model = "gemini-3-flash"
            mock_settings.gemini_max_images = 5

            result = await AIVisionService.analyze_images(
                db=db_session,
                product=test_product,
                user_id=user.id
            )

        # Assert
        attrs, tokens, cost, images_analyzed = result

        # VisionExtractedAttributes doesn't have title/description, check available fields
        assert attrs.brand == "Nike"
        # Note: color is validated/cleaned by the service, may be list or normalized
        assert tokens == 250
        assert cost > 0
        assert images_analyzed == 2

        # Check credit was consumed
        db_session.refresh(ai_credit)
        assert ai_credit.ai_credits_used_this_month == 1

    @pytest.mark.asyncio
    async def test_analyze_images_no_credits_raises_error(self, db_session, test_user, test_product, free_quota):
        """Test analyze_images raises error when no credits available."""
        # Extract user from tuple
        user, _ = test_user

        # Arrange: User with no credits
        # User already has FREE tier configured from fixture

        ai_credit = AICredit(
            user_id=user.id,
            ai_credits_purchased=0,
            ai_credits_used_this_month=10  # All used
        )
        db_session.add(ai_credit)
        db_session.commit()

        # Act & Assert
        with pytest.raises(AIQuotaExceededError):
            await AIVisionService.analyze_images(
                db=db_session,
                product=test_product,
                user_id=user.id
            )

    @pytest.mark.asyncio
    async def test_analyze_images_no_images_raises_error(self, db_session, test_user, test_product, free_quota):
        """Test analyze_images raises error when product has no images."""
        # Extract user from tuple
        user, _ = test_user

        # Arrange: Product with no images
        # User already has FREE tier configured from fixture

        ai_credit = AICredit(
            user_id=user.id,
            ai_credits_purchased=10,
            ai_credits_used_this_month=0
        )
        db_session.add(ai_credit)

        test_product.images = []
        db_session.commit()

        # Act & Assert
        with pytest.raises(AIGenerationError) as exc_info:
            await AIVisionService.analyze_images(
                db=db_session,
                product=test_product,
                user_id=user.id
            )

        assert "pas d'images" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    @patch('services.ai.vision_service.httpx.AsyncClient')
    @patch('services.ai.vision_service.genai.Client')
    @patch('services.ai.vision_service.AIVisionService._fetch_product_attributes')
    async def test_analyze_images_respects_max_images_limit(
        self,
        mock_fetch_attrs,
        mock_genai_client,
        mock_httpx,
        db_session,
        test_user,
        test_product,
        free_quota
    ):
        """Test that analyze_images respects the max_images setting."""
        # Extract user from tuple
        user, _ = test_user

        # Arrange: 10 images but max_images=3
        # User already has FREE tier configured from fixture

        ai_credit = AICredit(
            user_id=user.id,
            ai_credits_purchased=10,
            ai_credits_used_this_month=0
        )
        db_session.add(ai_credit)

        # Create 10 images
        test_product.images = [
            {"url": f"https://example.com/img{i}.jpg", "order": i}
            for i in range(10)
        ]
        db_session.commit()

        mock_fetch_attrs.return_value = {
            "categories": ["T-shirt"],
            "colors": ["Blue"],
            "conditions": [],
            "materials": [],
            "fits": [],
            "genders": [],
            "seasons": [],
            "patterns": [],
            "lengths": [],
            "necklines": [],
            "sports": [],
            "closures": [],
            "rises": [],
            "sleeve_lengths": [],
            "stretches": [],
            "linings": [],
            "decades": [],
            "origins": [],
            "trends": [],
            "condition_sups": [],
            "unique_features": []
        }

        # Mock httpx
        mock_http_client = AsyncMock()
        mock_http_response = MagicMock()  # Use MagicMock since .content is an attribute, not async
        mock_http_response.content = b"fake_image_data"
        mock_http_response.raise_for_status = MagicMock()  # Sync method
        mock_http_response.headers = MagicMock()
        mock_http_response.headers.get = MagicMock(return_value="image/jpeg")
        mock_http_client.get = AsyncMock(return_value=mock_http_response)
        mock_httpx.return_value.__aenter__.return_value = mock_http_client

        # Mock Gemini response
        mock_response = MagicMock()
        mock_response.text = '{"brand": "Test", "category": "T-shirt", "confidence": 0.9}'
        mock_response.usage_metadata = MagicMock()
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50
        mock_response.usage_metadata.total_token_count = 150

        mock_client_instance = MagicMock()
        mock_client_instance.models.generate_content.return_value = mock_response
        mock_genai_client.return_value = mock_client_instance

        # Act
        with patch('services.ai.vision_service.settings') as mock_settings:
            mock_settings.gemini_api_key = "test_key"
            mock_settings.gemini_model = "gemini-3-flash"

            result = await AIVisionService.analyze_images(
                db=db_session,
                product=test_product,
                user_id=user.id,
                max_images=3  # Limit to 3 images
            )

        # Assert: Only 3 images analyzed
        attrs, tokens, cost, images_analyzed = result
        assert images_analyzed == 3


class TestAIVisionServiceAnalyzeImagesDirect:
    """Test the analyze_images_direct flow."""

    @pytest.mark.asyncio
    @patch('services.ai.vision_service.genai.Client')
    @patch('services.ai.vision_service.AIVisionService._fetch_product_attributes')
    async def test_analyze_images_direct_success(
        self,
        mock_fetch_attrs,
        mock_genai_client,
        db_session,
        test_user,
        free_quota
    ):
        """Test direct image analysis with base64 images."""
        # Extract user from tuple
        user, _ = test_user

        # Arrange: Setup user credits
        # User already has FREE tier configured from fixture

        ai_credit = AICredit(
            user_id=user.id,
            ai_credits_purchased=10,
            ai_credits_used_this_month=0
        )
        db_session.add(ai_credit)
        db_session.commit()

        mock_fetch_attrs.return_value = {
            "categories": ["T-shirt"],
            "colors": ["Blue"],
            "conditions": [],
            "materials": [],
            "fits": [],
            "genders": [],
            "seasons": [],
            "patterns": [],
            "lengths": [],
            "necklines": [],
            "sports": [],
            "closures": [],
            "rises": [],
            "sleeve_lengths": [],
            "stretches": [],
            "linings": [],
            "decades": [],
            "origins": [],
            "trends": [],
            "condition_sups": [],
            "unique_features": []
        }

        # Mock Gemini response
        mock_response = MagicMock()
        mock_response.text = '{"title": "Test Product", "description": "Test", "brand": "Nike", "color": "Blue"}'
        mock_response.usage_metadata = MagicMock()
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50
        mock_response.usage_metadata.total_token_count = 150

        mock_client_instance = MagicMock()
        mock_client_instance.models.generate_content.return_value = mock_response
        mock_genai_client.return_value = mock_client_instance

        # Act
        # image_files format is list[tuple[bytes, str]] - (image_bytes, mime_type)
        image_files = [
            (b"fake_image_data_1", "image/png"),
            (b"fake_image_data_2", "image/png")
        ]

        with patch('services.ai.vision_service.settings') as mock_settings:
            mock_settings.gemini_api_key = "test_key"
            mock_settings.gemini_model = "gemini-3-flash"
            mock_settings.gemini_max_images = 5

            result = await AIVisionService.analyze_images_direct(
                db=db_session,
                image_files=image_files,
                user_id=user.id
            )

        # Assert
        attrs, tokens, cost, images_analyzed = result
        # VisionExtractedAttributes doesn't have title/description, check available fields
        assert attrs.brand == "Nike"
        assert attrs.color == ["Blue"]
        assert tokens == 150
        assert images_analyzed == 2

        # Check credit was consumed
        db_session.refresh(ai_credit)
        assert ai_credit.ai_credits_used_this_month == 1
