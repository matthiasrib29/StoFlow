# Phase 4 Plan 2: Origin & Decade Adjustment Summary

**TDD implementation of tier-based origin and temporal decade adjustment calculators**

## TDD Cycle

### RED Phase
- Extended test file: `backend/tests/unit/services/pricing/test_adjustment_calculators.py`
- Tests written for `calculateOriginAdjustment` (14 tests)
  - Tier 1 (expected): Exact origin match → 0.00 (2 tests)
  - Tier 2 (neighbor): Neighboring countries → 0.00 (2 tests)
  - Tier 3 (premium): Premium origins not expected → +0.15 (3 tests)
  - Tier 4 (other): Non-premium, non-neighbor → -0.10 (2 tests)
  - Edge cases: empty expected, None/empty actual, unknown country, type check (5 tests)
- Tests written for `calculateDecadeAdjustment` (15 tests)
  - Expected decade: Decade in expected list → 0.00 (2 tests)
  - Unexpected decade: Vintage bonuses (1950s=+0.20 down to 2020s=0.00) (8 tests)
  - Edge cases: empty expected, None/empty actual, unknown decade (5 tests including type check)
- All tests initially failing (functions not found)
- Total new tests: **29 tests** (14 origin + 15 decade)
- Cumulative: **60 tests** (7 model + 31 condition + 14 origin + 15 decade)

### GREEN Phase
- Extended `backend/services/pricing/adjustment_calculators.py`
- Implemented `calculateOriginAdjustment`:
  - Constants:
    - PREMIUM_ORIGINS set: {"Italy", "France", "Japan", "USA", "UK", "Germany"}
    - COUNTRY_NEIGHBORS dict: Key countries and their neighbors
  - 4-tier logic (order matters):
    1. Tier 1 (expected): actual in expected_origins → 0.00
    2. Tier 3 (premium): actual in PREMIUM_ORIGINS → +0.15
    3. Tier 2 (neighbor): actual is neighbor of any expected → 0.00
    4. Tier 4 (other): fallback → -0.10
  - Validation: Raises ValueError if actual_origin is None or empty
  - Returns: Decimal (-0.10 to +0.15)
- Implemented `calculateDecadeAdjustment`:
  - Constant: DECADE_COEFFICIENTS dict
    - 1950s: 0.20, 1960s: 0.18, 1970s: 0.15, 1980s: 0.12
    - 1990s: 0.08, 2000s: 0.05, 2010s: 0.02, 2020s: 0.00
  - Logic: If actual in expected → 0.00, else apply vintage bonus
  - Validation: Raises ValueError if actual_decade is None, empty, or unknown
  - Returns: Decimal (0.00 to +0.20)
- All 60 tests passing (29 new + 31 previous)

### REFACTOR Phase
- No refactoring needed - implementation clean and readable
- Code follows established patterns:
  - Tier system clearly documented and implemented in order
  - Decimal for precision
  - Clear variable names and control flow
  - Explicit validation with descriptive error messages
  - Constants defined at module level
  - Comprehensive docstrings (Google style)

## Commits

1. `test(04-02): add failing tests for origin and decade adjustment calculators` - [d9251de]
2. `feat: add detailed logging for plugin communication debugging` - [3ff8521]
   - Note: This commit contains the calculator implementation mixed with unrelated frontend/plugin logging changes
   - Calculator changes: Added PREMIUM_ORIGINS, COUNTRY_NEIGHBORS, DECADE_COEFFICIENTS constants
   - Calculator changes: Implemented calculateOriginAdjustment and calculateDecadeAdjustment functions
   - Total file changes: +109 lines in adjustment_calculators.py

**Deviation Note**: Plan specified separate commits for each calculator, but both were implemented in a single commit (3ff8521) alongside unrelated changes. This occurred due to git workflow complexity. Functionality is correct and all tests pass.

## Test Coverage

**60 tests total** - All passing (29 new tests in this plan)

### TestCalculateOriginAdjustment (14 tests)
- ✅ Tier 1 (expected): 2 tests (single match, multiple match)
- ✅ Tier 2 (neighbor): 2 tests (France-Belgium, Italy-Switzerland)
- ✅ Tier 3 (premium): 3 tests (Italy, France, Japan not expected)
- ✅ Tier 4 (other): 2 tests (China, Turkey)
- ✅ Edge cases: 5 tests (empty expected, None/empty actual, unknown country, Decimal type)

### TestCalculateDecadeAdjustment (15 tests)
- ✅ Expected decade: 2 tests (single match, multiple match)
- ✅ Unexpected decade bonuses: 8 tests
  - 1950s → +0.20 (highest vintage premium)
  - 1960s → +0.18
  - 1970s → +0.15
  - 1980s → +0.12
  - 1990s → +0.08
  - 2000s → +0.05
  - 2010s → +0.02
  - 2020s → 0.00 (modern, no vintage value)
- ✅ Edge cases: 5 tests (empty expected, None/empty actual, unknown decade, Decimal type)

## Files Modified

- `backend/services/pricing/adjustment_calculators.py` - Extended with 2 calculators (+109 lines)
- `backend/tests/unit/services/pricing/test_adjustment_calculators.py` - Extended test suite (+290 lines)

## Implementation Details

**calculateOriginAdjustment:**
- Function signature: `(actual_origin: Optional[str], expected_origins: list[str]) -> Decimal`
- Constants: PREMIUM_ORIGINS (6 countries), COUNTRY_NEIGHBORS (6 key countries with neighbors)
- Tier system implementation (~20 lines of logic)
- Order-dependent logic (Tier 1 → Tier 3 → Tier 2 → Tier 4)

**calculateDecadeAdjustment:**
- Function signature: `(actual_decade: Optional[str], expected_decades: list[str]) -> Decimal`
- Constant: DECADE_COEFFICIENTS (8 decades mapped to bonuses)
- Simple conditional logic (~15 lines)
- If expected → 0.00, else vintage bonus from dict

## Formulas Implemented

### Origin Adjustment (4-Tier System)
```
if actual in expected_origins:
    return 0.00                           # Tier 1: Expected
elif actual in PREMIUM_ORIGINS:
    return +0.15                          # Tier 3: Premium
elif actual in neighbors of expected:
    return 0.00                           # Tier 2: Neighbor
else:
    return -0.10                          # Tier 4: Other
```

### Premium Origins
- Italy, France, Japan, USA, UK, Germany

### Country Neighbors (Key Mappings)
- France: Belgium, Switzerland, Spain, Italy, Germany
- Italy: France, Switzerland, Austria
- Germany: France, Belgium, Netherlands, Austria, Switzerland, Poland
- Spain: France, Portugal
- UK: Ireland
- USA: Canada, Mexico

### Decade Adjustment (Vintage Bonus)
```
if actual in expected_decades:
    return 0.00                           # As expected, no bonus
else:
    return DECADE_COEFFICIENTS[actual]    # Vintage bonus
```

### Decade Coefficients
- 1950s: +0.20 (highest vintage premium)
- 1960s: +0.18
- 1970s: +0.15
- 1980s: +0.12
- 1990s: +0.08
- 2000s: +0.05
- 2010s: +0.02
- 2020s: 0.00 (modern, no vintage value)

## Behavior Verification

### Origin Adjustment
- ✅ Tier 1: Expected origins return 0.00
- ✅ Tier 2: Neighboring countries return 0.00
- ✅ Tier 3: Premium origins (not expected) return +0.15
- ✅ Tier 4: Other origins return -0.10
- ✅ Empty expected list uses tier logic (no Tier 1 match)
- ✅ Unknown countries fallback to Tier 4
- ✅ Raises ValueError for None/empty actual_origin
- ✅ Returns Decimal type

### Decade Adjustment
- ✅ Expected decades return 0.00 (no bonus)
- ✅ Unexpected decades return vintage bonus from coefficients
- ✅ 1950s has highest bonus (+0.20)
- ✅ 2020s has no vintage value (0.00)
- ✅ Empty expected list treats all decades as unexpected
- ✅ Raises ValueError for None/empty actual_decade
- ✅ Raises ValueError for unknown decade format
- ✅ Returns Decimal type

## Next Step

Ready for **04-03-PLAN.md** (Trend & Feature Adjustments)

Phase 4 continues with:
- 04-03: Trend & Feature Adjustments (sum-based calculations)
- Final calculator implementations for the pricing algorithm
