---
phase: 03-llm-generation
plan: 01
type: execute
domain: llm-integration
---

<objective>
Implement LLM-powered generation of BrandGroup pricing data using Google Gemini.

Purpose: Enable dynamic population of brand_groups table when data is missing, avoiding manual data entry for thousands of brand×group combinations. This is the foundation for the pricing system's ability to work with any brand.

Output: Working `PricingGenerationService` class with `generate_brand_group()` method that creates validated BrandGroup records via Gemini AI.
</objective>

<execution_context>
@./.claude/get-shit-done/workflows/execute-phase.md
@./.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/01-database-foundation/phase1-plan1-SUMMARY.md
@.planning/phases/02-group-determination/phase2-plan1-SUMMARY.md
@backend/models/public/brand_group.py
@backend/services/ai/vision_service.py
@backend/services/pricing/constants.py
@backend/services/pricing/group_determination.py

**Tech stack available:**
- Google Gemini API integration exists in `services/ai/vision_service.py`
- Gemini client: `from google import genai`
- Pydantic validation
- SQLAlchemy 2.0 async patterns
- BrandGroupRepository and ModelRepository exist

**Established patterns:**
- Services in `services/pricing/` module
- LLM prompts with structured output
- Response validation with fallback values
- Decimal precision for prices (DECIMAL(10, 2))
- JSON fields for lists (JSONB in PostgreSQL)

**Constraining decisions:**
- Phase 1: brand_groups table in public schema with CHECK constraints
- Phase 2: 69 groups defined in constants.py
- Must validate: base_price (5-500€), condition_sensitivity (0.5-1.5)
- Must handle LLM failures gracefully with fallbacks
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create PricingGenerationService with generate_brand_group method</name>
  <files>backend/services/pricing/pricing_generation_service.py, backend/services/pricing/__init__.py</files>
  <action>
Create `PricingGenerationService` class with async method `generate_brand_group(brand: str, group: str) -> BrandGroup`.

Implementation requirements:
1. Use Google Gemini API (model: gemini-2.5-flash for cost efficiency)
2. Configure Gemini client from shared config (API key from settings.gemini_api_key)
3. Build LLM prompt that specifies:
   - Context: "You are a secondhand fashion pricing expert"
   - Task: Generate pricing data for {brand} + {group} combination
   - Output format: JSON with fields base_price, expected_origins, expected_decades, expected_trends, condition_sensitivity
   - Constraints: base_price (5-500€), condition_sensitivity (0.5-1.5), origins/decades/trends as string lists
   - Examples: Levi's jeans → base_price=25, origins=["USA","Mexico"], sensitivity=1.0
4. Use structured output generation if available (Gemini supports JSON schema)
5. Parse LLM response into BrandGroup model
6. Return BrandGroup object (NOT saved to DB yet - repository handles that)

Error handling:
- Wrap in try/except for httpx errors, Gemini API errors
- Raise `AIGenerationError` on failures (import from shared.exceptions)
- Do NOT implement fallback logic here (Task 2 handles that)

What to avoid and WHY:
- Don't use GPT-4 (project uses Gemini, already integrated)
- Don't save to DB in this service (separation of concerns - service generates, repository saves)
- Don't hardcode prompts inline (makes them hard to maintain)
- Don't use gemini-2.5-pro (too expensive - Flash is sufficient for structured data)

Follow pattern from vision_service.py for:
- Gemini client initialization
- API call structure
- Response parsing

Export function in __init__.py: `from .pricing_generation_service import PricingGenerationService`
  </action>
  <verify>
1. File exists: backend/services/pricing/pricing_generation_service.py
2. Import works: `python3 -c "from backend.services.pricing import PricingGenerationService"`
3. Class has method: `python3 -c "from backend.services.pricing import PricingGenerationService; print(hasattr(PricingGenerationService, 'generate_brand_group'))"`
4. Type hints present (mypy check)
  </verify>
  <done>
- PricingGenerationService class created
- generate_brand_group() method implemented with Gemini integration
- LLM prompt specifies secondhand context and output format
- Method returns BrandGroup object
- Proper error handling with AIGenerationError
- Exported in __init__.py
  </done>
</task>

<task type="auto">
  <name>Task 2: Add response validation and fallback logic</name>
  <files>backend/services/pricing/pricing_generation_service.py</files>
  <action>
Add validation and fallback to `generate_brand_group()` method.

Validation logic (add private method `_validate_brand_group_response`):
1. Check base_price is float/int and within range 5-500
2. Check condition_sensitivity is float and within range 0.5-1.5
3. Check expected_origins is list of strings (max 5 items)
4. Check expected_decades is list of strings (max 3 items, format: "2010s", "1990s")
5. Check expected_trends is list of strings (max 5 items)
6. If validation fails, log warning with details
7. Return validation result (bool) and sanitized data

Fallback values (add private method `_get_fallback_brand_group`):
Use conservative defaults when LLM fails or validation fails:
- base_price: Decimal("30.00")  # Safe mid-range price
- expected_origins: []  # No expectations = no origin adjustments
- expected_decades: []  # No expectations = no decade adjustments
- expected_trends: []  # No expectations = no trend adjustments
- condition_sensitivity: Decimal("1.0")  # Standard sensitivity

Flow in generate_brand_group():
1. Try to call Gemini API
2. If success, validate response
3. If validation passes, return BrandGroup with LLM data
4. If validation fails, log warning, return BrandGroup with fallback values
5. If API fails, log error, return BrandGroup with fallback values

Logging (use shared.logging_setup.get_logger):
- INFO: "Generating BrandGroup for {brand} + {group}"
- WARNING: "LLM response validation failed for {brand} + {group}: {reason}"
- ERROR: "Gemini API error for {brand} + {group}: {error}"
- INFO: "Using fallback values for {brand} + {group}"

What to avoid and WHY:
- Don't raise exceptions on validation failure (graceful degradation - pricing still works with fallbacks)
- Don't retry LLM calls automatically (expensive - let caller decide to retry)
- Don't log sensitive data (API keys, full responses - GDPR compliance)
  </action>
  <verify>
1. Validation method exists: `grep "_validate_brand_group_response" backend/services/pricing/pricing_generation_service.py`
2. Fallback method exists: `grep "_get_fallback_brand_group" backend/services/pricing/pricing_generation_service.py`
3. Logging statements present: `grep "logger\." backend/services/pricing/pricing_generation_service.py | wc -l` (should be >=4)
4. Decimal type used for prices: `grep "Decimal" backend/services/pricing/pricing_generation_service.py`
  </verify>
  <done>
- Response validation implemented with range checks
- Fallback logic provides safe default values
- Method gracefully handles LLM failures
- Comprehensive logging for debugging
- No exceptions raised on recoverable errors
  </done>
</task>

<task type="auto">
  <name>Task 3: Create unit tests for PricingGenerationService</name>
  <files>backend/tests/unit/services/pricing/test_pricing_generation_service.py</files>
  <action>
Create comprehensive unit tests for the BrandGroup generation service.

Test structure (use pytest):

1. **TestGenerateBrandGroupSuccess** - Happy path
   - test_generate_brand_group_valid_response
     - Mock Gemini API to return valid JSON
     - Assert BrandGroup created with correct values
     - Assert base_price, sensitivity within ranges
     - Assert lists properly parsed

2. **TestGenerateBrandGroupValidation** - Validation edge cases
   - test_base_price_too_low (4€) → uses fallback
   - test_base_price_too_high (501€) → uses fallback
   - test_sensitivity_too_low (0.4) → uses fallback
   - test_sensitivity_too_high (1.6) → uses fallback
   - test_invalid_origins_format (not a list) → uses fallback
   - test_empty_response → uses fallback

3. **TestGenerateBrandGroupFallback** - Error handling
   - test_gemini_api_error → uses fallback, logs error
   - test_gemini_timeout → uses fallback, logs error
   - test_validation_failure → uses fallback, logs warning

4. **TestGenerateBrandGroupPrompt** - Prompt quality
   - test_prompt_includes_brand_and_group
   - test_prompt_includes_secondhand_context
   - test_prompt_specifies_output_format

Mocking strategy:
- Mock `genai.Client` or patch Gemini API calls
- Don't make real API calls (use pytest fixtures)
- Verify prompt content via mock calls

Assertions to include:
- Decimal types for prices
- JSONB-compatible lists (can be serialized)
- Fallback values match specification
- Logging called with appropriate levels

What to avoid and WHY:
- Don't test database operations (that's repository's job)
- Don't make real API calls (expensive, slow, flaky)
- Don't test Gemini library itself (trust Google's tests)

Coverage target: 100% of pricing_generation_service.py lines
  </action>
  <verify>
1. Test file exists: `ls backend/tests/unit/services/pricing/test_pricing_generation_service.py`
2. Tests run successfully: `cd backend && pytest tests/unit/services/pricing/test_pricing_generation_service.py -v`
3. Coverage check: `cd backend && pytest tests/unit/services/pricing/test_pricing_generation_service.py --cov=services/pricing/pricing_generation_service --cov-report=term-missing`
4. No real API calls: `grep -i "api_key\|genai\.Client" backend/tests/unit/services/pricing/test_pricing_generation_service.py | grep -v mock` (should be empty)
  </verify>
  <done>
- Test file created with 4 test classes
- 10+ tests covering success, validation, fallback, prompt cases
- Gemini API properly mocked
- All tests pass
- High coverage (aim for >95%)
- No external API dependencies
  </done>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] PricingGenerationService class exists and exports
- [ ] generate_brand_group() method implemented with Gemini integration
- [ ] Validation and fallback logic working
- [ ] Unit tests pass: `pytest tests/unit/services/pricing/test_pricing_generation_service.py`
- [ ] No TypeScript/Python syntax errors
- [ ] Can import service: `python3 -c "from services.pricing import PricingGenerationService"`
</verification>

<success_criteria>

- All 3 tasks completed
- All verification checks pass
- Service can generate BrandGroup objects via Gemini
- Validation prevents invalid data from being used
- Fallback ensures system works even if LLM fails
- Tests demonstrate reliability (mocked API calls)
  </success_criteria>

<output>
After completion, create `.planning/phases/03-llm-generation/phase3-plan1-SUMMARY.md`:

# Phase 3 Plan 1: BrandGroup Generation Service Summary

**LLM-powered BrandGroup data generation via Google Gemini implemented and tested**

## Accomplishments

- Created PricingGenerationService with generate_brand_group() method
- Integrated with Google Gemini API (gemini-2.5-flash model)
- Implemented response validation with range checks
- Added fallback logic for LLM failures
- Created comprehensive unit tests with mocked API calls

## Files Created/Modified

- `backend/services/pricing/pricing_generation_service.py` - Service implementation
- `backend/services/pricing/__init__.py` - Export added
- `backend/tests/unit/services/pricing/test_pricing_generation_service.py` - Unit tests

## Decisions Made

- Use gemini-2.5-flash model (cost-efficient for structured data)
- Graceful degradation: fallback values instead of exceptions
- Conservative defaults: base_price=30€, sensitivity=1.0, empty expectations
- Validation before use: prevent invalid LLM responses from breaking pricing

## Issues Encountered

[Document any issues or "None"]

## Next Phase Readiness

Ready for phase3-plan2: Model generation service. BrandGroup generation service is foundation for Model service (Model records reference brand+group combinations).
</output>
