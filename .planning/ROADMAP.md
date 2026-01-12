# Roadmap: Pricing Algorithm Feature

**Project**: Add intelligent pricing system with LLM-generated data and "expected vs actual" logic

**Current milestone**: v1.0 - Complete pricing system (backend + frontend + tests)

---

## Phases

### Phase 1: Database Foundation ✅ COMPLETED (2026-01-09)
**Goal**: Create database schema for brand_groups and models tables

**Why this phase**: Need storage for LLM-generated data (Brand×Group base prices, Model coefficients) that will be cached and reused. Must be in place before any pricing logic can work.

**Deliverables**: ✅ All completed
- ✅ Migration to create `brand_groups` table (public schema) - revision 2f3a9708b420
- ✅ Migration to create `models` table (public schema) - revision 68a6d6ef6f65
- ✅ SQLAlchemy models for BrandGroup and Model
- ✅ Repositories for data access (BrandGroupRepository, ModelRepository)

**Dependencies**: None (foundation phase)

**Research needed**: No - database patterns well established in StoFlow

**Estimated complexity**: Low (standard CRUD with indexes)

**Execution Summary**: See `.planning/phases/01-database-foundation/phase1-plan1-SUMMARY.md`
- 6 files created (2 migrations, 2 models, 2 repositories)
- 8 commits (6 features + 2 fixes)
- All verification tests passed
- Migrations reversible and idempotent

---

### Phase 2: Group Determination Logic
**Goal**: Implement category + materials → group mapping for 69 groups

**Why this phase**: Core business logic that determines which "group" a product belongs to (e.g., "jacket_leather" vs "jacket_denim"). Required before any pricing calculations can start.

**Deliverables**:
- `determineGroup(category, materials)` function with material priority logic
- Constants for 69 groups and category mappings
- Unit tests for all group combinations
- Edge case handling (unknown category, multiple materials)

**Dependencies**: None (pure logic, no DB needed yet)

**Research needed**: No - specification is complete in documentation

**Estimated complexity**: Medium (69 groups, priority logic, extensive testing)

---

### Phase 3: LLM Generation Service
**Goal**: Generate Brand×Group and Model data via Google Gemini

**Why this phase**: Need to populate brand_groups and models tables dynamically when data is missing. This enables the pricing system to work for any brand without manual data entry.

**Deliverables**:
- `PricingGenerationService.generateBrandGroup(brand, group)` using Gemini
- `PricingGenerationService.generateModel(brand, group, model, basePrice)` using Gemini
- LLM prompts for secondhand pricing context
- Response validation (check ranges, reject outliers)
- Fallback logic for LLM failures
- Integration with existing `services/ai/gemini_service.py`

**Dependencies**: Phase 1 (needs tables to store generated data)

**Research needed**: No - Gemini integration exists, prompts are specified

**Estimated complexity**: Medium (LLM validation, fallback logic, async handling)

---

### Phase 4: Adjustment Calculators ✅ COMPLETED (2026-01-12)
**Goal**: Implement 6 adjustment calculation functions

**Why this phase**: Core pricing logic that calculates bonuses/malus based on product attributes. Each calculator is independent and testable. These feed into the main pricing algorithm.

**Deliverables**: ✅ All completed
- ✅ `calculateConditionAdjustment(score, supplements, sensitivity)` - Score + supplements with caps
- ✅ `calculateOriginAdjustment(actualOrigin, expectedOrigins)` - Tier-based comparison
- ✅ `calculateDecadeAdjustment(actualDecade, expectedDecades)` - Bonus if unexpected
- ✅ `calculateTrendAdjustment(actualTrends, expectedTrends)` - Best unexpected trend
- ✅ `calculateFeatureAdjustment(actualFeatures, expectedFeatures)` - Sum unexpected features
- ✅ `calculateModelCoefficient(modelData)` - Simple multiplier
- ✅ Unit tests for each calculator with edge cases (94 tests total)
- ✅ Constants for DECADE_COEFFICIENTS, TREND_COEFFICIENTS, FEATURE_COEFFICIENTS, ORIGIN_TIERS

**Dependencies**: Phase 2 (needs group determination for context)

**Research needed**: No - formulas are fully specified

**Estimated complexity**: Medium (6 functions, caps, edge cases, extensive tests)

**Execution Summary**: See `.planning/phases/04-adjustment-calculators/` (3 plans)
- 3 TDD plans executed (RED-GREEN-REFACTOR cycle)
- 94 unit tests (100% passing)
- All 6 calculators implemented in `backend/services/pricing/adjustment_calculators.py`
- Clean code with comprehensive docstrings and validation

---

### Phase 5: Main Pricing Algorithm & API
**Goal**: Orchestrate all calculations and expose pricing endpoint

**Why this phase**: Brings everything together - fetches/generates Brand×Group, fetches/generates Model, calculates all adjustments, returns 3 price levels. This is the complete pricing system.

**Deliverables**:
- `PricingService.calculatePrice(input: PriceInput) -> PriceOutput`
- Formula orchestration: `PRICE = BASE_PRICE × MODEL_COEFF × (1 + ADJUSTMENTS)`
- 3 price levels: quick (×0.75), standard (×1.0), premium (×1.30)
- Detailed breakdown in response (base_price, model_coeff, adjustments)
- API endpoint: `POST /api/pricing/calculate`
- Error handling (missing data, LLM timeout)
- Integration tests for full flow

**Dependencies**:
- Phase 1 (database tables)
- Phase 2 (group determination)
- Phase 3 (LLM generation)
- Phase 4 (adjustment calculators)

**Research needed**: No - integration of existing components

**Estimated complexity**: High (orchestration, error handling, full integration)

---

### Phase 6: Frontend UI
**Goal**: Display 3 pricing suggestions with breakdown on product page

**Why this phase**: User-facing interface to trigger pricing and view results. Make the algorithm transparent and useful.

**Deliverables**:
- `composables/usePricing.ts` - Composable for pricing logic
- `components/products/PricingDisplay.vue` - Display 3 prices with breakdown
- "Calculate Price" button in product detail page
- Loading states during LLM generation (2-5s)
- Error messages for failures
- Expandable details showing adjustments (condition +7%, features +15%, etc.)
- Visual: badges for quick/standard/premium, progress bars for adjustments

**Dependencies**: Phase 5 (needs working API endpoint)

**Research needed**: No - UI patterns established in StoFlow

**Estimated complexity**: Medium (Vue components, async handling, UX polish)

---

### Phase 7: Testing & Polish
**Goal**: Comprehensive tests, bug fixes, documentation

**Why this phase**: Ensure production quality, catch edge cases, document usage for future maintenance.

**Deliverables**:
- Unit tests for all pricing logic (>80% coverage)
- Integration tests for API endpoint
- Frontend component tests
- End-to-end test: create product → calculate price → verify output
- Manual testing with real brand data
- Bug fixes from testing
- Update PROJECT.md with implementation notes
- Code review readiness

**Dependencies**: All previous phases (testing the complete system)

**Research needed**: No - testing patterns established

**Estimated complexity**: Medium (comprehensive coverage, edge cases)

---

## Phase Dependencies

```
Phase 1 (Database Foundation)
  │
  ├─→ Phase 3 (LLM Generation Service)
  │     │
  │     └─→ Phase 5 (Main Algorithm & API)
  │           │
  │           └─→ Phase 6 (Frontend UI)
  │                 │
  │                 └─→ Phase 7 (Testing & Polish)
  │
  └─→ Phase 2 (Group Determination)
        │
        └─→ Phase 4 (Adjustment Calculators)
              │
              └─→ Phase 5 (Main Algorithm & API)
```

**Critical path**: 1 → 3 → 5 → 6 → 7 (LLM + API + UI)
**Parallel track**: 1 → 2 → 4 → 5 (Logic + calculators)

---

## Success Metrics

**Phase 1-4 (Backend Core)**:
- All tables created and indexed
- All calculators tested with >80% coverage
- LLM generation works with validation

**Phase 5 (Integration)**:
- API endpoint returns valid PriceOutput for any product
- Handles missing data gracefully (generates via LLM)
- Response time <10s (including LLM calls)

**Phase 6 (Frontend)**:
- User can trigger pricing with one click
- 3 prices displayed clearly
- Breakdown is transparent and understandable

**Phase 7 (Quality)**:
- All tests pass
- No critical bugs
- Code reviewed and approved

---

*Roadmap created: 2026-01-09*
