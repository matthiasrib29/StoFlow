# Phase 4 Plan 1: Model Coefficient & Condition Adjustment Summary

**TDD implementation of model coefficient and condition adjustment calculators with comprehensive test coverage**

## TDD Cycle

### RED Phase
- Created test file: `backend/tests/unit/services/pricing/test_adjustment_calculators.py`
- Tests written for `calculateModelCoefficient` (7 tests)
  - Standard coefficient extraction (1.5, 0.5, 3.0, 1.0)
  - Edge cases (None model, None coefficient)
  - Type validation (Decimal return)
- Tests written for `calculateConditionAdjustment` (24 tests)
  - Base calculation tests (scores 0-5 with sensitivity 1.0)
  - Sensitivity scaling tests (0.5, 1.0, 1.5)
  - Supplement bonus tests (original_box, tags, dust_bag, authenticity_card)
  - Multiple supplements and unknown supplement handling
  - Positive and negative capping at ±0.30
  - Edge case validation (score range, sensitivity range)
  - Decimal precision and rounding
- All tests initially failing (module not found)
- Total: **31 tests**

### GREEN Phase
- Created `backend/services/pricing/adjustment_calculators.py`
- Implemented `calculateModelCoefficient`:
  - Simple extraction from Model.coefficient field
  - Validation for None model and None coefficient
  - Returns Decimal in 0.5-3.0 range
- Implemented `calculateConditionAdjustment`:
  - Base formula: `(score - 3.0) / 10.0 * sensitivity`
  - Supplement values dictionary (4 known supplements)
  - Supplement sum calculation (ignores unknown supplements)
  - Capping at ±0.30 (MAX_ADJUSTMENT, MIN_ADJUSTMENT constants)
  - Decimal precision with quantize to 2 decimal places
  - Input validation for score [0-5] and sensitivity [0.5-1.5]
- All 31 tests passing

### REFACTOR Phase
- No refactoring needed - implementation clean and readable
- Code follows established patterns:
  - Decimal for precision
  - Clear variable names
  - Explicit validation with descriptive error messages
  - Constants defined at module level
  - Comprehensive docstrings (Google style)

## Commits

1. `test(04-01): add failing tests for model coefficient and condition adjustment calculators` - [02f2165]
2. `feat(04-01): implement calculateModelCoefficient` - [fbb5293]

Note: Both calculators were implemented in a single commit (fbb5293) as they share the same module file. The implementation is complete and all tests pass.

## Test Coverage

**31 tests total** - All passing

### TestCalculateModelCoefficient (7 tests)
- ✅ Extract coefficient (standard, minimum, maximum, neutral)
- ✅ Error handling (None model, None coefficient)
- ✅ Type validation (returns Decimal)

### TestCalculateConditionAdjustment (24 tests)
- ✅ Base calculations (6 tests: scores 0-5)
- ✅ Sensitivity scaling (3 tests: 0.5, 1.0, 1.5)
- ✅ Supplement bonuses (7 tests: individual + multiple + empty + unknown)
- ✅ Capping (2 tests: positive and negative caps)
- ✅ Edge case validation (4 tests: score and sensitivity bounds)
- ✅ Precision (2 tests: Decimal type and 2 decimal places)

## Files Created/Modified

### Created
- `backend/services/pricing/adjustment_calculators.py` - Calculator functions (98 lines)
- `backend/tests/unit/services/pricing/test_adjustment_calculators.py` - Test suite (343 lines)

### Implementation Details

**calculateModelCoefficient:**
- Function signature: `(model: Optional[Model]) -> Decimal`
- Validates model and coefficient are not None
- Returns model.coefficient directly
- Simple extraction pattern (5 lines of logic)

**calculateConditionAdjustment:**
- Function signature: `(condition_score: int, supplements: list[str], condition_sensitivity: Decimal) -> Decimal`
- Constants: SUPPLEMENT_VALUES dict, MAX/MIN_ADJUSTMENT
- Base calculation: `(score - 3.0) / 10.0 * sensitivity`
- Supplement sum: Iterates supplements, sums known values, ignores unknown
- Capping: min/max logic to enforce ±0.30 bounds
- Rounding: quantize to 2 decimal places
- Complex calculation pattern (~30 lines of logic)

## Formulas Implemented

### Model Coefficient
```
coefficient = model.coefficient
```

### Condition Adjustment
```
base = (score - 3.0) / 10.0 * sensitivity
supplement_sum = sum(SUPPLEMENT_VALUES.get(s, 0) for s in supplements)
total = base + supplement_sum
result = cap(total, -0.30, +0.30)
```

### Supplement Values
- original_box: +0.05
- tags: +0.03
- dust_bag: +0.03
- authenticity_card: +0.04

## Behavior Verification

### Model Coefficient
- ✅ Extracts coefficient correctly (0.5-3.0 range)
- ✅ Raises ValueError for None model
- ✅ Raises ValueError for None coefficient
- ✅ Returns Decimal type

### Condition Adjustment
- ✅ Score 3 (baseline) returns 0.00
- ✅ Score 5 (perfect) returns +0.20
- ✅ Score 0 (damaged) returns -0.30 (capped)
- ✅ Sensitivity scales adjustment correctly
- ✅ Supplements add bonus correctly
- ✅ Multiple supplements sum correctly
- ✅ Unknown supplements ignored
- ✅ Positive cap at +0.30 enforced
- ✅ Negative cap at -0.30 enforced
- ✅ Results rounded to 2 decimal places
- ✅ Validates score range [0-5]
- ✅ Validates sensitivity range [0.5-1.5]

## Next Step

Ready for **04-02-PLAN.md** (Origin & Decade Adjustments)

Phase 4 continues with:
- 04-02: Origin & Decade Adjustments (boost/penalty logic)
- 04-03: Trend & Rarity Adjustments (sum-based calculations)
