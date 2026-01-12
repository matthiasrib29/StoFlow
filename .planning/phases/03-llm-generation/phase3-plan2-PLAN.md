---
phase: 03-llm-generation
plan: 02
type: execute
domain: llm-integration
---

<objective>
Implement LLM-powered generation of Model pricing data using Google Gemini.

Purpose: Enable dynamic coefficient and feature generation for specific models within brand×group combinations. This completes the LLM generation system, allowing pricing to work for any brand's specific models without manual data entry.

Output: Working `generate_model()` method in PricingGenerationService that creates validated Model records via Gemini AI.
</objective>

<execution_context>
@./.claude/get-shit-done/workflows/execute-phase.md
@./.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/03-llm-generation/phase3-plan1-SUMMARY.md
@backend/models/public/model.py
@backend/services/pricing/pricing_generation_service.py
@backend/services/pricing/constants.py

**Tech stack available:**
- PricingGenerationService class exists with generate_brand_group()
- Gemini integration patterns established
- Validation and fallback patterns established

**Established patterns (from Plan 1)**:
- Gemini gemini-2.5-flash model for cost efficiency
- Structured JSON output with validation
- Fallback values on LLM failure
- Private validation methods (_validate_*)
- Private fallback methods (_get_fallback_*)
- Comprehensive logging (INFO, WARNING, ERROR)
- Unit tests with mocked API calls

**Constraining decisions:**
- Phase 1: models table with CHECK constraint on coefficient (0.5-3.0)
- Must validate: coefficient range, expected_features as string list
- Must handle LLM failures gracefully
- Model generation requires base_price from BrandGroup (context for LLM)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add generate_model method to PricingGenerationService</name>
  <files>backend/services/pricing/pricing_generation_service.py</files>
  <action>
Add async method `generate_model(brand: str, group: str, model: str, base_price: Decimal) -> Model` to existing PricingGenerationService class.

Implementation requirements:
1. Use same Gemini client as generate_brand_group() (gemini-2.5-flash)
2. Build LLM prompt that specifies:
   - Context: "You are a secondhand fashion pricing expert"
   - Task: Generate coefficient and expected features for {brand} + {group} + {model}
   - Context data: base_price from BrandGroup (helps LLM understand value context)
   - Output format: JSON with fields coefficient, expected_features
   - Constraints: coefficient (0.5-3.0), expected_features as string list
   - Examples:
     * Levi's jeans + 501 → coefficient=1.4, features=[]
     * Levi's jeans + Big E → coefficient=2.5, features=["selvedge", "chain_stitching"]
     * Nike sneakers + Jordan 1 → coefficient=2.8, features=["original_box", "deadstock"]
3. Explain to LLM that coefficient is multiplier (1.0 = standard, >1.0 = premium, <1.0 = budget)
4. Expected features are what makes this model valuable beyond the base group
5. Parse LLM response into Model object
6. Return Model object (NOT saved to DB - repository handles that)

Error handling:
- Same pattern as generate_brand_group()
- Raise AIGenerationError on unrecoverable failures
- Validation handled in Task 2

What to avoid and WHY:
- Don't call LLM without base_price context (less accurate results)
- Don't generate coefficient without understanding brand positioning
- Don't make features too generic (should be model-specific, not group-wide)

Follow established pattern from generate_brand_group() for consistency.
  </action>
  <verify>
1. Method exists: `grep "def generate_model" backend/services/pricing/pricing_generation_service.py`
2. Type hints present: `grep "-> Model" backend/services/pricing/pricing_generation_service.py`
3. Uses base_price parameter: `grep "base_price.*Decimal" backend/services/pricing/pricing_generation_service.py`
4. Import Model type: `grep "from models.public.model import Model" backend/services/pricing/pricing_generation_service.py`
  </verify>
  <done>
- generate_model() method added to PricingGenerationService
- Gemini integration for model-specific data
- LLM prompt includes base_price context
- Method returns Model object
- Error handling consistent with generate_brand_group()
  </done>
</task>

<task type="auto">
  <name>Task 2: Add validation and fallback for model generation</name>
  <files>backend/services/pricing/pricing_generation_service.py</files>
  <action>
Add validation and fallback to `generate_model()` method.

Validation logic (add private method `_validate_model_response`):
1. Check coefficient is float/int and within range 0.5-3.0
2. Check expected_features is list of strings (max 10 items)
3. Check features are not empty strings or whitespace-only
4. If validation fails, log warning with details
5. Return validation result (bool) and sanitized data

Fallback values (add private method `_get_fallback_model`):
Use conservative defaults when LLM fails:
- coefficient: Decimal("1.0")  # Standard multiplier (no premium/discount)
- expected_features: []  # No expectations = no feature adjustments

Flow in generate_model():
1. Try to call Gemini API with base_price context
2. If success, validate response
3. If validation passes, return Model with LLM data
4. If validation fails, log warning, return Model with fallback values
5. If API fails, log error, return Model with fallback values

Logging:
- INFO: "Generating Model for {brand} + {group} + {model}"
- WARNING: "LLM response validation failed for model {model}: {reason}"
- ERROR: "Gemini API error for model {model}: {error}"
- INFO: "Using fallback values for model {model}"

What to avoid and WHY:
- Don't fail hard on invalid coefficients (pricing still works with coefficient=1.0)
- Don't generate features if uncertain (empty list safer than wrong features)
- Don't retry automatically (let caller handle retries)
  </action>
  <verify>
1. Validation method exists: `grep "_validate_model_response" backend/services/pricing/pricing_generation_service.py`
2. Fallback method exists: `grep "_get_fallback_model" backend/services/pricing/pricing_generation_service.py`
3. Logging statements: `grep "logger\." backend/services/pricing/pricing_generation_service.py | grep -i model | wc -l` (should be >=3)
4. Fallback coefficient is 1.0: `grep "Decimal.*1\\.0" backend/services/pricing/pricing_generation_service.py`
  </verify>
  <done>
- Model response validation implemented
- Fallback logic provides safe defaults (coefficient=1.0, features=[])
- Method gracefully handles LLM failures
- Comprehensive logging for debugging
- Consistent error handling with BrandGroup generation
  </done>
</task>

<task type="auto">
  <name>Task 3: Create unit tests for Model generation</name>
  <files>backend/tests/unit/services/pricing/test_pricing_generation_service.py</files>
  <action>
Extend existing test file with tests for Model generation.

Add test classes:

1. **TestGenerateModelSuccess** - Happy path
   - test_generate_model_valid_response
     - Mock Gemini API to return valid JSON
     - Assert Model created with correct values
     - Assert coefficient within range 0.5-3.0
     - Assert expected_features properly parsed
   - test_generate_model_with_base_price_context
     - Verify base_price is used in prompt
     - Assert LLM receives pricing context

2. **TestGenerateModelValidation** - Validation edge cases
   - test_coefficient_too_low (0.4) → uses fallback
   - test_coefficient_too_high (3.1) → uses fallback
   - test_invalid_features_format (not a list) → uses fallback
   - test_empty_features_strings → filtered out
   - test_too_many_features (>10) → uses fallback

3. **TestGenerateModelFallback** - Error handling
   - test_gemini_api_error_model → uses fallback
   - test_validation_failure_model → uses fallback
   - test_fallback_coefficient_is_1_0
   - test_fallback_features_empty_list

4. **TestGenerateModelPrompt** - Prompt quality
   - test_prompt_includes_brand_group_model
   - test_prompt_includes_base_price
   - test_prompt_explains_coefficient_meaning

Mocking strategy:
- Reuse mocking patterns from BrandGroup tests
- Mock Gemini client consistently
- Verify prompt content contains base_price

Coverage target:
- 100% of new generate_model() code
- All validation and fallback branches
- All error paths

What to avoid and WHY:
- Don't duplicate test setup (use pytest fixtures for shared mocks)
- Don't test database saves (repository's responsibility)
- Don't test integration between BrandGroup and Model (that's integration test territory)
  </action>
  <verify>
1. Test file updated: `grep "TestGenerateModel" backend/tests/unit/services/pricing/test_pricing_generation_service.py | wc -l` (should be >=4)
2. Tests run successfully: `cd backend && pytest tests/unit/services/pricing/test_pricing_generation_service.py::TestGenerateModel -v`
3. Coverage maintained: `cd backend && pytest tests/unit/services/pricing/test_pricing_generation_service.py --cov=services/pricing/pricing_generation_service --cov-report=term-missing`
4. Both methods tested: `grep -E "test_generate_(brand_group|model)" backend/tests/unit/services/pricing/test_pricing_generation_service.py | wc -l` (should be >=15)
  </verify>
  <done>
- Test file extended with Model generation tests
- 4 new test classes covering success, validation, fallback, prompt
- 10+ new tests for Model generation
- All tests pass
- High coverage maintained (>95%)
- Consistent with BrandGroup test patterns
  </done>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] generate_model() method added to PricingGenerationService
- [ ] Validation and fallback for Model generation working
- [ ] Unit tests pass: `pytest tests/unit/services/pricing/test_pricing_generation_service.py -v`
- [ ] Both generate_brand_group() and generate_model() methods tested
- [ ] No Python syntax errors
- [ ] Import works: `python3 -c "from services.pricing import PricingGenerationService; print(hasattr(PricingGenerationService, 'generate_model'))"`
</verification>

<success_criteria>

- All 3 tasks completed
- All verification checks pass
- Service can generate both BrandGroup and Model objects via Gemini
- Validation prevents invalid coefficient/features
- Fallback ensures system works even if LLM fails
- Comprehensive test coverage for both generation methods
- Phase 3 complete: LLM Generation Service fully implemented
  </success_criteria>

<output>
After completion, create `.planning/phases/03-llm-generation/phase3-plan2-SUMMARY.md`:

# Phase 3 Plan 2: Model Generation Service Summary

**Model-specific pricing data generation via Gemini completed, Phase 3 fully implemented**

## Accomplishments

- Added generate_model() method to PricingGenerationService
- Integrated base_price context for more accurate LLM responses
- Implemented coefficient and feature validation
- Added fallback logic (coefficient=1.0, features=[])
- Extended unit tests to cover Model generation
- Phase 3 complete: Both BrandGroup and Model generation working

## Files Created/Modified

- `backend/services/pricing/pricing_generation_service.py` - Added generate_model() method
- `backend/tests/unit/services/pricing/test_pricing_generation_service.py` - Extended with Model tests

## Decisions Made

- Use base_price in Model generation prompt for context
- Fallback coefficient=1.0 (neutral multiplier, safe default)
- Empty features list on failure (no assumptions about model premiums)
- Max 10 features per model (prevent over-specification)

## Issues Encountered

[Document any issues or "None"]

## Next Phase Readiness

✅ Phase 3 complete. Ready for Phase 4: Adjustment Calculators.

LLM generation system is fully functional:
- BrandGroup generation: base prices + expectations
- Model generation: coefficients + expected features
- Validation: prevents invalid LLM responses
- Fallback: ensures system works even if LLM fails
- Tested: comprehensive unit tests with mocked API calls

Phase 4 can now implement adjustment calculators that use the generated BrandGroup/Model data.
</output>
