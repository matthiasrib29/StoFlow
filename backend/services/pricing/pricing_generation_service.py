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
from decimal import Decimal
from typing import Optional

from google import genai
from google.genai import types

from models.public.brand_group import BrandGroup
from shared.config import settings
from shared.exceptions import AIGenerationError
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class PricingGenerationService:
    """Service for generating pricing data via Gemini LLM."""

    # Gemini pricing (USD per million tokens) - Jan 2026
    MODEL_PRICING = {
        "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
    }

    @staticmethod
    async def generate_brand_group(brand: str, group: str) -> BrandGroup:
        """
        Generate BrandGroup pricing data using Gemini LLM.

        Args:
            brand: Brand name (e.g., "Levi's", "Nike")
            group: Pricing group (e.g., "jeans", "sneakers")

        Returns:
            BrandGroup object with generated or fallback values

        Raises:
            AIGenerationError: On unrecoverable API errors (after fallback attempted)
        """
        logger.info(f"Generating BrandGroup for {brand} + {group}")

        try:
            # Initialize Gemini client
            client = genai.Client(api_key=settings.gemini_api_key)

            # Build prompt
            prompt = PricingGenerationService._build_brand_group_prompt(brand, group)

            # Call Gemini API with structured output
            response = client.models.generate_content(
                model="gemini-2.5-flash",  # Cost-efficient for structured data
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7,  # Balanced creativity for pricing
                ),
            )

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
                return PricingGenerationService._get_fallback_brand_group(brand, group)

            # Create BrandGroup from validated data
            brand_group = BrandGroup(
                brand=brand,
                group=group,
                base_price=Decimal(str(sanitized_data["base_price"])),
                expected_origins=sanitized_data["expected_origins"],
                expected_decades=sanitized_data["expected_decades"],
                expected_trends=sanitized_data["expected_trends"],
                condition_sensitivity=Decimal(str(sanitized_data["condition_sensitivity"])),
            )

            logger.info(
                f"Generated BrandGroup for {brand} + {group}: "
                f"base_price={brand_group.base_price}, "
                f"sensitivity={brand_group.condition_sensitivity}"
            )

            return brand_group

        except genai.errors.ClientError as e:
            logger.error(f"Gemini client error for {brand} + {group}: {e}")
            logger.info(f"Using fallback values for {brand} + {group}")
            return PricingGenerationService._get_fallback_brand_group(brand, group)

        except genai.errors.ServerError as e:
            logger.error(f"Gemini server error for {brand} + {group}: {e}")
            logger.info(f"Using fallback values for {brand} + {group}")
            return PricingGenerationService._get_fallback_brand_group(brand, group)

        except genai.errors.APIError as e:
            logger.error(f"Gemini API error for {brand} + {group}: {e}")
            logger.info(f"Using fallback values for {brand} + {group}")
            return PricingGenerationService._get_fallback_brand_group(brand, group)

        except Exception as e:
            logger.error(
                f"Unexpected error generating BrandGroup for {brand} + {group}: {e}",
                exc_info=True
            )
            logger.info(f"Using fallback values for {brand} + {group}")
            return PricingGenerationService._get_fallback_brand_group(brand, group)

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
  "condition_sensitivity": <float between 0.5 and 1.5>
}}

Field explanations:
- base_price: Average secondhand price in EUR for this brand+category (5-500€)
- expected_origins: Countries commonly associated with this brand's production
- expected_decades: Decades when this brand was popular in this category
- expected_trends: Fashion trends associated with this brand+category combination
- condition_sensitivity: How much condition affects price (0.5=forgiving, 1.0=standard, 1.5=critical)

Examples:
- Levi's jeans → {{"base_price": 25, "expected_origins": ["USA", "Mexico"], "expected_decades": ["1990s", "2000s"], "expected_trends": ["vintage", "workwear"], "condition_sensitivity": 1.0}}
- Nike sneakers → {{"base_price": 45, "expected_origins": ["Vietnam", "China"], "expected_decades": ["2010s", "2020s"], "expected_trends": ["streetwear", "athleisure"], "condition_sensitivity": 1.3}}
- Hermès bags → {{"base_price": 450, "expected_origins": ["France"], "expected_decades": ["2000s", "2010s"], "expected_trends": ["luxury", "investment"], "condition_sensitivity": 1.5}}

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
