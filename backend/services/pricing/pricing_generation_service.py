"""
Pricing Generation Service

Service for generating pricing data using Google Gemini LLM.
Handles BrandGroup and Model data generation with validation and fallback logic.

Business Rules:
- Generate BrandGroup: base_price (5-500€), condition_sensitivity (0.5-1.5)
- Generate Model: coefficient (0.5-3.0), expected_features list
- Graceful degradation: use fallback values on LLM failure
- No external database calls: service generates, repository saves
"""

import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

import httpx
from google import genai
from google.genai import types

from models.public.brand_group import BrandGroup
from models.product_attributes.model import Model
from shared.config import settings
from shared.exceptions import AIGenerationError
from shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class GenerationResult:
    """Result of a pricing generation with token usage info."""
    brand_group: BrandGroup
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    is_fallback: bool = False


class PricingGenerationService:
    """Service for generating pricing data via Gemini LLM."""

    # Gemini pricing (USD per million tokens) - Jan 2026
    MODEL_PRICING = {
        "gemini-3-flash-preview": {"input": 0.10, "output": 0.40},
        "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
    }

    @staticmethod
    async def generate_brand_group(brand: str, group: str) -> GenerationResult:
        """
        Generate BrandGroup pricing data using Gemini LLM.

        Args:
            brand: Brand name (e.g., "Levi's", "Nike")
            group: Pricing group (e.g., "jeans", "sneakers")

        Returns:
            GenerationResult with BrandGroup and token usage info

        Raises:
            AIGenerationError: On unrecoverable API errors (after fallback attempted)
        """
        logger.info(f"Generating BrandGroup for {brand} + {group}")

        try:
            # Initialize Gemini client with timeout
            client = genai.Client(
                api_key=settings.gemini_api_key,
                http_options=types.HttpOptions(timeout=settings.gemini_timeout_seconds * 1000),
            )

            # Build prompt
            prompt = PricingGenerationService._build_brand_group_prompt(brand, group)

            # Call Gemini API with structured output
            response = client.models.generate_content(
                model="gemini-3-flash-preview",  # Latest flash model
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7,  # Balanced creativity for pricing
                ),
            )

            # Extract token usage and calculate cost
            input_tokens = 0
            output_tokens = 0
            cost_usd = 0.0
            if response.usage_metadata:
                input_tokens = response.usage_metadata.prompt_token_count or 0
                output_tokens = response.usage_metadata.candidates_token_count or 0
                # Calculate cost (price per million tokens)
                pricing = PricingGenerationService.MODEL_PRICING.get("gemini-3-flash-preview", {"input": 0.10, "output": 0.40})
                cost_usd = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000

            # Parse JSON response
            response_data = json.loads(response.text)

            # Validate response
            is_valid, sanitized_data = PricingGenerationService._validate_brand_group_response(
                response_data, brand, group
            )

            if not is_valid:
                logger.warning(
                    f"LLM response validation failed for {brand} + {group}, using fallback"
                )
                return GenerationResult(
                    brand_group=PricingGenerationService._get_fallback_brand_group(brand, group),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=cost_usd,
                    is_fallback=True,
                )

            # Create BrandGroup from validated data
            brand_group = BrandGroup(
                brand=brand,
                group=group,
                base_price=Decimal(str(sanitized_data["base_price"])),
                expected_origins=sanitized_data["expected_origins"],
                expected_decades=sanitized_data["expected_decades"],
                expected_trends=sanitized_data["expected_trends"],
                condition_sensitivity=Decimal(str(sanitized_data["condition_sensitivity"])),
                generated_by_ai=True,
                ai_confidence=Decimal(str(sanitized_data["confidence"])),
                generation_cost=Decimal(str(round(cost_usd, 6))) if cost_usd > 0 else None,
            )

            logger.info(
                f"Generated BrandGroup for {brand} + {group}: "
                f"base_price={brand_group.base_price}, "
                f"sensitivity={brand_group.condition_sensitivity}, "
                f"confidence={brand_group.ai_confidence}"
            )

            return GenerationResult(
                brand_group=brand_group,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
                is_fallback=False,
            )

        except genai.errors.ClientError as e:
            logger.error(f"Gemini client error for {brand} + {group}: {e}")
            logger.info(f"Using fallback values for {brand} + {group}")
            return GenerationResult(
                brand_group=PricingGenerationService._get_fallback_brand_group(brand, group),
                is_fallback=True,
            )

        except genai.errors.ServerError as e:
            logger.error(f"Gemini server error for {brand} + {group}: {e}")
            logger.info(f"Using fallback values for {brand} + {group}")
            return GenerationResult(
                brand_group=PricingGenerationService._get_fallback_brand_group(brand, group),
                is_fallback=True,
            )

        except genai.errors.APIError as e:
            logger.error(f"Gemini API error for {brand} + {group}: {e}")
            logger.info(f"Using fallback values for {brand} + {group}")
            return GenerationResult(
                brand_group=PricingGenerationService._get_fallback_brand_group(brand, group),
                is_fallback=True,
            )

        except Exception as e:
            logger.error(
                f"Unexpected error generating BrandGroup for {brand} + {group}: {e}",
                exc_info=True
            )
            logger.info(f"Using fallback values for {brand} + {group}")
            return GenerationResult(
                brand_group=PricingGenerationService._get_fallback_brand_group(brand, group),
                is_fallback=True,
            )

    @staticmethod
    def _build_brand_group_prompt(brand: str, group: str) -> str:
        """
        Build LLM prompt for BrandGroup generation.

        Args:
            brand: Brand name
            group: Pricing group

        Returns:
            Formatted prompt string
        """
        return f"""You are a secondhand fashion pricing expert specializing in marketplace pricing.

Your task: Generate pricing data for the brand "{brand}" in the "{group}" category for secondhand/vintage items.

Output format: JSON with the following fields:
{{
  "base_price": <float between 5 and 500>,
  "expected_origins": [<list of countries, max 5 strings>],
  "expected_decades": [<list of decades like "2010s", "1990s", max 3 strings>],
  "expected_trends": [<list of fashion trends, max 5 strings>],
  "condition_sensitivity": <float between 0.5 and 1.5>,
  "confidence": <float between 0.0 and 1.0>
}}

Field explanations:
- base_price: Average secondhand price in EUR for this brand+category (5-500€)
- expected_origins: Countries commonly associated with this brand's production
- expected_decades: Decades when this brand was popular in this category
- expected_trends: Fashion trends associated with this brand+category combination
- condition_sensitivity: How much condition affects price (0.5=forgiving, 1.0=standard, 1.5=critical)
- confidence: Your confidence in the pricing data (0.0=uncertain/unknown brand, 1.0=very confident)

Examples:
- Levi's jeans → {{"base_price": 25, "expected_origins": ["USA", "Mexico"], "expected_decades": ["1990s", "2000s"], "expected_trends": ["vintage", "workwear"], "condition_sensitivity": 1.0, "confidence": 0.95}}
- Nike sneakers → {{"base_price": 45, "expected_origins": ["Vietnam", "China"], "expected_decades": ["2010s", "2020s"], "expected_trends": ["streetwear", "athleisure"], "condition_sensitivity": 1.3, "confidence": 0.9}}
- Hermès bags → {{"base_price": 450, "expected_origins": ["France"], "expected_decades": ["2000s", "2010s"], "expected_trends": ["luxury", "investment"], "condition_sensitivity": 1.5, "confidence": 0.95}}

Consider:
- Brand positioning (luxury vs mass market)
- Category popularity in secondhand market
- Typical condition expectations for this combination

Generate realistic secondhand pricing data:"""

    @staticmethod
    def _validate_brand_group_response(
        response_data: dict, brand: str, group: str
    ) -> tuple[bool, dict]:
        """
        Validate LLM response for BrandGroup generation.

        Args:
            response_data: Parsed JSON from LLM
            brand: Brand name (for logging)
            group: Group name (for logging)

        Returns:
            Tuple of (is_valid, sanitized_data)
        """
        try:
            # Check all required fields present
            required_fields = [
                "base_price",
                "expected_origins",
                "expected_decades",
                "expected_trends",
                "condition_sensitivity",
                "confidence",
            ]
            for field in required_fields:
                if field not in response_data:
                    logger.warning(
                        f"Validation failed for {brand} + {group}: missing field '{field}'"
                    )
                    return False, {}

            # Validate base_price
            base_price = float(response_data["base_price"])
            if base_price < 5.0 or base_price > 500.0:
                logger.warning(
                    f"Validation failed for {brand} + {group}: "
                    f"base_price {base_price} out of range [5, 500]"
                )
                return False, {}

            # Validate condition_sensitivity
            sensitivity = float(response_data["condition_sensitivity"])
            if sensitivity < 0.5 or sensitivity > 1.5:
                logger.warning(
                    f"Validation failed for {brand} + {group}: "
                    f"condition_sensitivity {sensitivity} out of range [0.5, 1.5]"
                )
                return False, {}

            # Validate confidence
            confidence = float(response_data["confidence"])
            if confidence < 0.0 or confidence > 1.0:
                logger.warning(
                    f"Validation failed for {brand} + {group}: "
                    f"confidence {confidence} out of range [0.0, 1.0]"
                )
                return False, {}

            # Validate lists
            for field_name, max_items in [
                ("expected_origins", 5),
                ("expected_decades", 3),
                ("expected_trends", 5),
            ]:
                field_value = response_data[field_name]
                if not isinstance(field_value, list):
                    logger.warning(
                        f"Validation failed for {brand} + {group}: "
                        f"{field_name} is not a list"
                    )
                    return False, {}

                if len(field_value) > max_items:
                    logger.warning(
                        f"Validation failed for {brand} + {group}: "
                        f"{field_name} has {len(field_value)} items (max {max_items})"
                    )
                    return False, {}

                # Check all items are non-empty strings
                for item in field_value:
                    if not isinstance(item, str) or not item.strip():
                        logger.warning(
                            f"Validation failed for {brand} + {group}: "
                            f"{field_name} contains invalid item: {item}"
                        )
                        return False, {}

            # All validations passed, return sanitized data
            sanitized = {
                "base_price": base_price,
                "expected_origins": response_data["expected_origins"],
                "expected_decades": response_data["expected_decades"],
                "expected_trends": response_data["expected_trends"],
                "condition_sensitivity": sensitivity,
                "confidence": confidence,
            }

            return True, sanitized

        except (ValueError, TypeError, KeyError) as e:
            logger.warning(
                f"Validation failed for {brand} + {group}: exception {type(e).__name__}: {e}"
            )
            return False, {}

    @staticmethod
    def _get_fallback_brand_group(brand: str, group: str) -> BrandGroup:
        """
        Get fallback BrandGroup with conservative defaults.

        Args:
            brand: Brand name
            group: Group name

        Returns:
            BrandGroup with safe default values
        """
        logger.info(f"Using fallback values for BrandGroup: {brand} + {group}")

        return BrandGroup(
            brand=brand,
            group=group,
            base_price=Decimal("30.00"),  # Safe mid-range price
            expected_origins=[],  # No expectations = no origin adjustments
            expected_decades=[],  # No expectations = no decade adjustments
            expected_trends=[],  # No expectations = no trend adjustments
            condition_sensitivity=Decimal("1.0"),  # Standard sensitivity
        )

    # ===== MODEL GENERATION =====

    @staticmethod
    async def generate_model(
        brand: str, group: str, model: str, base_price: Decimal
    ) -> Model:
        """
        Generate Model pricing data using Gemini LLM.

        Args:
            brand: Brand name (e.g., "Levi's", "Nike")
            group: Pricing group (e.g., "jeans", "sneakers")
            model: Model name (e.g., "501", "Jordan 1")
            base_price: BrandGroup base_price for context (helps LLM accuracy)

        Returns:
            Model object with generated or fallback values

        Raises:
            AIGenerationError: On unrecoverable API errors (after fallback attempted)
        """
        logger.info(f"Generating Model for {brand} + {group} + {model}")

        try:
            # Initialize Gemini client with timeout
            client = genai.Client(
                api_key=settings.gemini_api_key,
                http_options=types.HttpOptions(timeout=settings.gemini_timeout_seconds * 1000),
            )

            # Build prompt with base_price context
            prompt = PricingGenerationService._build_model_prompt(
                brand, group, model, base_price
            )

            # Call Gemini API with structured output
            response = client.models.generate_content(
                model="gemini-3-flash-preview",  # Latest flash model
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7,  # Balanced creativity for pricing
                ),
            )

            # Parse JSON response
            response_data = json.loads(response.text)

            # Validate response
            is_valid, sanitized_data = PricingGenerationService._validate_model_response(
                response_data, brand, group, model
            )

            if not is_valid:
                logger.warning(
                    f"LLM response validation failed for model {model}, using fallback"
                )
                return PricingGenerationService._get_fallback_model(brand, group, model)

            # Create Model from validated data
            model_obj = Model(
                brand=brand,
                group=group,
                name=model,
                coefficient=Decimal(str(sanitized_data["coefficient"])),
                expected_features=sanitized_data["expected_features"],
            )

            logger.info(
                f"Generated Model for {brand} + {group} + {model}: "
                f"coefficient={model_obj.coefficient}, "
                f"features={len(model_obj.expected_features)}"
            )

            return model_obj

        except genai.errors.ClientError as e:
            logger.error(f"Gemini client error for model {model}: {e}")
            logger.info(f"Using fallback values for model {model}")
            return PricingGenerationService._get_fallback_model(brand, group, model)

        except genai.errors.ServerError as e:
            logger.error(f"Gemini server error for model {model}: {e}")
            logger.info(f"Using fallback values for model {model}")
            return PricingGenerationService._get_fallback_model(brand, group, model)

        except genai.errors.APIError as e:
            logger.error(f"Gemini API error for model {model}: {e}")
            logger.info(f"Using fallback values for model {model}")
            return PricingGenerationService._get_fallback_model(brand, group, model)

        except Exception as e:
            logger.error(
                f"Unexpected error generating Model for {model}: {e}",
                exc_info=True
            )
            logger.info(f"Using fallback values for model {model}")
            return PricingGenerationService._get_fallback_model(brand, group, model)

    @staticmethod
    def _build_model_prompt(
        brand: str, group: str, model: str, base_price: Decimal
    ) -> str:
        """
        Build LLM prompt for Model generation.

        Args:
            brand: Brand name
            group: Pricing group
            model: Model name
            base_price: BrandGroup base_price for context

        Returns:
            Formatted prompt string
        """
        return f"""You are a secondhand fashion pricing expert specializing in model-specific valuations.

Your task: Generate pricing coefficient and expected features for the model "{model}" within "{brand}" {group} (base price: {base_price}€).

Output format: JSON with the following fields:
{{
  "coefficient": <float between 0.5 and 3.0>,
  "expected_features": [<list of model-specific features, max 10 strings>]
}}

Field explanations:
- coefficient: Price multiplier relative to base group price
  * 1.0 = standard model (no premium or discount)
  * > 1.0 = premium model (more valuable than average)
  * < 1.0 = budget/entry model (less valuable than average)
- expected_features: Specific attributes that make THIS model valuable beyond the base group
  * Features should be model-specific, not category-wide
  * Examples: "selvedge denim", "original box", "limited edition", "vintage label"
  * Empty list if no special features expected

Examples:
- Levi's jeans + "501" (base: 25€) → {{"coefficient": 1.4, "expected_features": []}}
  (Classic model with 40% premium, no special features expected)

- Levi's jeans + "Big E" (base: 25€) → {{"coefficient": 2.5, "expected_features": ["selvedge", "chain_stitching", "vintage_label"]}}
  (Vintage premium model, specific features drive value)

- Nike sneakers + "Jordan 1" (base: 45€) → {{"coefficient": 2.8, "expected_features": ["original_box", "deadstock", "og_colorway"]}}
  (Iconic model with strong premium, condition and features critical)

- Zara basics + "Standard T-shirt" (base: 10€) → {{"coefficient": 0.8, "expected_features": []}}
  (Budget model with 20% discount, no special features)

Consider:
- Model's reputation and desirability in secondhand market
- How much more (or less) collectors/buyers pay for THIS model vs average
- Features that specifically make THIS model valuable (not just category features)
- Base price context: {base_price}€ is the group average

Generate realistic model pricing data:"""

    @staticmethod
    def _validate_model_response(
        response_data: dict, brand: str, group: str, model: str
    ) -> tuple[bool, dict]:
        """
        Validate LLM response for Model generation.

        Args:
            response_data: Parsed JSON from LLM
            brand: Brand name (for logging)
            group: Group name (for logging)
            model: Model name (for logging)

        Returns:
            Tuple of (is_valid, sanitized_data)
        """
        try:
            # Check required fields present
            required_fields = ["coefficient", "expected_features"]
            for field in required_fields:
                if field not in response_data:
                    logger.warning(
                        f"Validation failed for model {model}: missing field '{field}'"
                    )
                    return False, {}

            # Validate coefficient
            coefficient = float(response_data["coefficient"])
            if coefficient < 0.5 or coefficient > 3.0:
                logger.warning(
                    f"Validation failed for model {model}: "
                    f"coefficient {coefficient} out of range [0.5, 3.0]"
                )
                return False, {}

            # Validate expected_features
            features = response_data["expected_features"]
            if not isinstance(features, list):
                logger.warning(
                    f"Validation failed for model {model}: "
                    f"expected_features is not a list"
                )
                return False, {}

            if len(features) > 10:
                logger.warning(
                    f"Validation failed for model {model}: "
                    f"expected_features has {len(features)} items (max 10)"
                )
                return False, {}

            # Check all items are non-empty strings
            for item in features:
                if not isinstance(item, str) or not item.strip():
                    logger.warning(
                        f"Validation failed for model {model}: "
                        f"expected_features contains invalid item: {item}"
                    )
                    return False, {}

            # All validations passed, return sanitized data
            sanitized = {
                "coefficient": coefficient,
                "expected_features": features,
            }

            return True, sanitized

        except (ValueError, TypeError, KeyError) as e:
            logger.warning(
                f"Validation failed for model {model}: exception {type(e).__name__}: {e}"
            )
            return False, {}

    @staticmethod
    def _get_fallback_model(brand: str, group: str, model: str) -> Model:
        """
        Get fallback Model with conservative defaults.

        Args:
            brand: Brand name
            group: Group name
            model: Model name

        Returns:
            Model with safe default values
        """
        logger.info(f"Using fallback values for Model: {brand} + {group} + {model}")

        return Model(
            brand=brand,
            group=group,
            name=model,
            coefficient=Decimal("1.0"),  # Standard multiplier (no premium/discount)
            expected_features=[],  # No expectations = no feature adjustments
        )
