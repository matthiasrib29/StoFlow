"""
Unit tests for AIVisionService.

Tests the AI image analysis functionality with mocked Gemini API calls to avoid costs.
Tests credit checking, consumption, logging, and error handling.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from decimal import Decimal
from datetime import datetime

from services.ai.vision_service import AIVisionService
from models.public.ai_credit import AICredit
from models.user.ai_generation_log import AIGenerationLog
from models.public.user import User, SubscriptionTier
from models.public.subscription_quota import SubscriptionQuota
from schemas.ai_schemas import VisionExtractedAttributes
from shared.exceptions import AIQuotaExceededError, AIGenerationError


class TestAIVisionServiceCredits:
    """Test credit checking and consumption logic."""

    def test_check_credits_sufficient(self, db_session, test_user):
        """Test credit check passes when user has sufficient credits."""
        # Extract user from tuple
        user, _ = test_user

        # Arrange: Create AI credit record with credits
        ai_credit = AICredit(
            user_id=user.id,
            ai_credits_purchased=5,
            ai_credits_used_this_month=2
        )
        db_session.add(ai_credit)

        # Set monthly credits from subscription
        quota = SubscriptionQuota(
            tier=SubscriptionTier.FREE,
            ai_credits_monthly=10
        )
        db_session.add(quota)
        user.subscription_tier = SubscriptionTier.FREE
        user.subscription_quota = quota
        db_session.commit()

        # Act & Assert: Should not raise
        AIVisionService._check_credits(db_session, user.id, monthly_credits=10)

    def test_check_credits_insufficient_raises_error(self, db_session, test_user):
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

    def test_check_credits_creates_record_if_missing(self, db_session, test_user):
        """Test credit check creates AICredit record if it doesn't exist."""
        # Extract user from tuple
        user, _ = test_user

        # Arrange: No AI credit record
        assert db_session.query(AICredit).filter_by(user_id=user.id).first() is None

        # Act
        AIVisionService._check_credits(db_session, user.id, monthly_credits=10)
        db_session.flush()

        # Assert: Record created
        ai_credit = db_session.query(AICredit).filter_by(user_id=user.id).first()
        assert ai_credit is not None
        assert ai_credit.ai_credits_purchased == 0
        assert ai_credit.ai_credits_used_this_month == 0

    def test_consume_credit_increments_usage(self, db_session, test_user):
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

    def test_consume_credit_handles_missing_record(self, db_session, test_user):
        """Test consume_credit doesn't crash if AICredit record doesn't exist."""
        # Extract user from tuple
        user, _ = test_user

        # Arrange: No AI credit record
        assert db_session.query(AICredit).filter_by(user_id=user.id).first() is None

        # Act & Assert: Should not raise
        AIVisionService._consume_credit(db_session, user.id)


class TestAIVisionServicePrompt:
    """Test prompt generation with database attributes."""

    @patch('services.ai.vision_service.Brand')
    @patch('services.ai.vision_service.Category')
    @patch('services.ai.vision_service.Color')
    def test_fetch_product_attributes(self, mock_color, mock_category, mock_brand, db_session):
        """Test fetching product attributes from database."""
        # Arrange: Mock query results
        mock_brand.name = "name"
        mock_category.name = "name"
        mock_color.name = "name"

        db_session.query = Mock(return_value=Mock(
            order_by=Mock(return_value=Mock(
                limit=Mock(return_value=Mock(
                    all=Mock(return_value=[Mock(name="Nike"), Mock(name="Adidas")])
                ))
            ))
        ))

        # Act
        attributes = AIVisionService._fetch_product_attributes(db_session)

        # Assert
        assert "brands" in attributes
        assert "categories" in attributes
        assert "colors" in attributes
        assert len(attributes["brands"]) == 2

    def test_build_prompt_contains_english(self):
        """Test that the prompt is in English."""
        # Arrange
        attributes = {
            "brands": ["Nike", "Adidas"],
            "categories": ["T-shirt", "Jeans"],
            "colors": ["Blue", "Red"]
        }

        # Act
        prompt = AIVisionService._build_prompt(attributes)

        # Assert
        assert "You are an expert" in prompt
        assert "CRITICAL RULES" in prompt
        assert "VALID ATTRIBUTE VALUES" in prompt
        assert "Categories:" in prompt
        assert "Brands:" in prompt
        assert "Colors:" in prompt

    def test_build_prompt_injects_attributes(self):
        """Test that the prompt injects attribute values."""
        # Arrange
        attributes = {
            "brands": ["Nike", "Adidas", "Zara"],
            "categories": ["T-shirt", "Jeans"],
            "colors": ["Blue", "Red", "Black"]
        }

        # Act
        prompt = AIVisionService._build_prompt(attributes)

        # Assert
        assert "Nike" in prompt
        assert "Adidas" in prompt
        assert "T-shirt" in prompt
        assert "Blue" in prompt


class TestAIVisionServiceLogging:
    """Test AI generation logging."""

    def test_log_generation_creates_record(self, db_session, test_user):
        """Test that log_generation creates an AIGenerationLog record."""
        # Arrange
        user_schema = f"user_{test_user.id}"
        extracted_attrs = VisionExtractedAttributes(
            title="Nike Air Max",
            description="Great shoes",
            brand="Nike",
            color="Blue"
        )

        # Act
        AIVisionService._log_generation(
            db=db_session,
            user_id=test_user.id,
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
        log = db_session.execute(
            f"SELECT * FROM {user_schema}.ai_generation_logs ORDER BY created_at DESC LIMIT 1"
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
        test_product
    ):
        """Test successful image analysis with mocked Gemini."""
        # Extract user from tuple
        user, _ = test_user

        # Arrange: Setup user credits
        quota = SubscriptionQuota(
            tier=SubscriptionTier.FREE,
            ai_credits_monthly=10
        )
        db_session.add(quota)
        user.subscription_tier = SubscriptionTier.FREE
        user.subscription_quota = quota

        ai_credit = AICredit(
            user_id=user.id,
            ai_credits_purchased=5,
            ai_credits_used_this_month=0
        )
        db_session.add(ai_credit)
        db_session.commit()

        # Mock attributes
        mock_fetch_attrs.return_value = {
            "brands": ["Nike", "Adidas"],
            "categories": ["T-shirt"],
            "colors": ["Blue", "Red"]
        }

        # Mock httpx image download
        mock_http_client = AsyncMock()
        mock_http_response = AsyncMock()
        mock_http_response.content = b"fake_image_data"
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

        assert attrs.title == "Nike Air Max"
        assert attrs.brand == "Nike"
        assert attrs.color == "Blue"
        assert tokens == 250
        assert cost > 0
        assert images_analyzed == 2

        # Check credit was consumed
        db_session.refresh(ai_credit)
        assert ai_credit.ai_credits_used_this_month == 1

    @pytest.mark.asyncio
    async def test_analyze_images_no_credits_raises_error(self, db_session, test_user, test_product):
        """Test analyze_images raises error when no credits available."""
        # Extract user from tuple
        user, _ = test_user

        # Arrange: User with no credits
        quota = SubscriptionQuota(
            tier=SubscriptionTier.FREE,
            ai_credits_monthly=10
        )
        db_session.add(quota)
        user.subscription_tier = SubscriptionTier.FREE
        user.subscription_quota = quota

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
    async def test_analyze_images_no_images_raises_error(self, db_session, test_user, test_product):
        """Test analyze_images raises error when product has no images."""
        # Extract user from tuple
        user, _ = test_user

        # Arrange: Product with no images
        quota = SubscriptionQuota(
            tier=SubscriptionTier.FREE,
            ai_credits_monthly=10
        )
        db_session.add(quota)
        user.subscription_tier = SubscriptionTier.FREE
        user.subscription_quota = quota

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
        test_product
    ):
        """Test that analyze_images respects the max_images setting."""
        # Extract user from tuple
        user, _ = test_user

        # Arrange: 10 images but max_images=3
        quota = SubscriptionQuota(
            tier=SubscriptionTier.FREE,
            ai_credits_monthly=10
        )
        db_session.add(quota)
        user.subscription_tier = SubscriptionTier.FREE
        user.subscription_quota = quota

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
            "brands": ["Nike"],
            "categories": ["T-shirt"],
            "colors": ["Blue"]
        }

        # Mock httpx
        mock_http_client = AsyncMock()
        mock_http_response = AsyncMock()
        mock_http_response.content = b"fake_image_data"
        mock_http_client.get = AsyncMock(return_value=mock_http_response)
        mock_httpx.return_value.__aenter__.return_value = mock_http_client

        # Mock Gemini response
        mock_response = MagicMock()
        mock_response.text = '{"title": "Test", "description": "Test", "confidence": 0.9}'
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
            mock_settings.gemini_max_images = 3  # Limit to 3

            result = await AIVisionService.analyze_images(
                db=db_session,
                product=test_product,
                user_id=user.id
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
        test_user
    ):
        """Test direct image analysis with base64 images."""
        # Extract user from tuple
        user, _ = test_user

        # Arrange: Setup user credits
        quota = SubscriptionQuota(
            tier=SubscriptionTier.FREE,
            ai_credits_monthly=10
        )
        db_session.add(quota)
        user.subscription_tier = SubscriptionTier.FREE
        user.subscription_quota = quota

        ai_credit = AICredit(
            user_id=user.id,
            ai_credits_purchased=10,
            ai_credits_used_this_month=0
        )
        db_session.add(ai_credit)
        db_session.commit()

        mock_fetch_attrs.return_value = {
            "brands": ["Nike"],
            "categories": ["T-shirt"],
            "colors": ["Blue"]
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
        base64_images = [
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        ]

        with patch('services.ai.vision_service.settings') as mock_settings:
            mock_settings.gemini_api_key = "test_key"
            mock_settings.gemini_model = "gemini-3-flash"
            mock_settings.gemini_max_images = 5

            result = await AIVisionService.analyze_images_direct(
                db=db_session,
                user_id=user.id,
                images=base64_images
            )

        # Assert
        attrs, tokens, cost, images_analyzed = result
        assert attrs.title == "Test Product"
        assert attrs.brand == "Nike"
        assert tokens == 150
        assert images_analyzed == 2

        # Check credit was consumed
        db_session.refresh(ai_credit)
        assert ai_credit.ai_credits_used_this_month == 1
