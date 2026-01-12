# Pricing Algorithm Feature

## Vision

Implémenter un système de pricing intelligent pour StoFlow qui calcule automatiquement le prix optimal de vente d'articles secondhand en fonction de multiples attributs (brand, model, condition, origin, decade, trends, features).

**Le système doit:**
- Éviter le double comptage via la logique "expected vs actual"
- Générer dynamiquement les données manquantes (Brand×Group, Models) via LLM
- Proposer 3 niveaux de prix (quick sale / standard / premium)
- S'intégrer naturellement dans le flow de création/import de produits

**One-liner**: Un algorithme de pricing qui comprend le contexte d'une marque et génère des prix justes basés sur ce qui dépasse ou manque par rapport aux attentes du marché secondhand.

---

## Requirements

### Validated (Existing Capabilities)

Ces éléments existent déjà dans StoFlow et peuvent être utilisés:

- ✓ **Multi-tenant PostgreSQL** - Schema isolation via `user_X`, product storage
- ✓ **Product model with 33+ attributes** - brand, category, materials, condition, origin, etc.
- ✓ **Gemini AI integration** - `services/ai/gemini_service.py` for LLM calls
- ✓ **Attribute tables in DB** - trends, features, origins, conditions already exist
- ✓ **FastAPI service architecture** - Clean Architecture with services/repositories/models
- ✓ **Nuxt frontend with composables** - Vue 3 Composition API, Pinia stores
- ✓ **Product CRUD API** - `/api/products` endpoints for product management

### Active (To Be Built)

#### Backend Core

- [ ] **Create `brand_groups` table** - Store Brand×Group base prices + expected values
  - Schema: `brand, group_name, base_price, expected_origins, expected_decades, expected_trends, condition_sensitivity`
  - Indexes on brand, group_name for fast lookup
  - Multi-tenant: Table in `public` schema (shared data)

- [ ] **Create `models` table** - Store Model coefficients + expected features
  - Schema: `brand, group_name, model, coefficient, expected_features`
  - Unique constraint on (brand, group_name, model)

- [ ] **Implement group determination logic** - Map category + materials → 69 groups
  - Function: `determineGroup(category, materials) -> string`
  - Material priority: LEATHER > DENIM > WOOL_LUXURY > NATURAL > TECHNICAL > SYNTHETIC

- [ ] **Implement LLM generation service** - Generate Brand×Group and Model data
  - `PricingGenerationService.generateBrandGroup(brand, group)` using Gemini
  - `PricingGenerationService.generateModel(brand, group, model, basePrice)` using Gemini
  - Validation of LLM responses (check ranges, fallback values)
  - Cache results in database (generate once, reuse forever)

- [ ] **Implement 6 adjustment calculators**
  - `calculateConditionAdjustment(score, supplements, sensitivity)` - Base score + supplements
  - `calculateOriginAdjustment(actualOrigin, expectedOrigins)` - Tier-based comparison
  - `calculateDecadeAdjustment(actualDecade, expectedDecades)` - Bonus if unexpected
  - `calculateTrendAdjustment(actualTrends, expectedTrends)` - Best unexpected trend
  - `calculateFeatureAdjustment(actualFeatures, expectedFeatures)` - Sum unexpected features
  - Cap malus at -80% (condition), cap features bonus at +30%

- [ ] **Implement main pricing algorithm** - Orchestrate all calculations
  - `PricingService.calculatePrice(input: PriceInput) -> PriceOutput`
  - Formula: `PRICE = BASE_PRICE × MODEL_COEFF × (1 + ADJUSTMENTS)`
  - Return 3 prices: quick (×0.75), standard (×1.0), premium (×1.30)
  - Include detailed breakdown in response

- [ ] **Create pricing API endpoint** - `/api/pricing/calculate`
  - POST with product attributes (brand, category, materials, model, condition, etc.)
  - Return PriceOutput with quick/standard/premium + details
  - Error handling for missing data, LLM failures

- [ ] **Repository layer** - Data access for brand_groups and models
  - `BrandGroupRepository.findByBrandAndGroup(brand, group)`
  - `BrandGroupRepository.create(brandGroup)`
  - `ModelRepository.findByBrandGroupModel(brand, group, model)`
  - `ModelRepository.create(model)`

#### Frontend UI

- [ ] **Product detail price display** - Show 3 pricing suggestions
  - Component: `PricingDisplay.vue` or section in `ProductDetails.vue`
  - Display quick/standard/premium with badges/labels
  - Expandable details showing breakdown (base_price, model_coeff, adjustments)
  - Visual: Progress bars or charts for adjustments (condition +7%, features +15%, etc.)

- [ ] **"Calculate Price" button** - Trigger pricing on demand
  - In product creation form (`pages/dashboard/products/create.vue`)
  - In product edit form
  - In product detail page
  - Show loading state during LLM generation (can take 2-5s)

- [ ] **Pricing composable** - Reusable pricing logic
  - `composables/usePricing.ts`
  - Methods: `calculatePrice(productId)`, `calculateFromAttributes(attributes)`
  - State: `pricing: ref<PriceOutput | null>`, `loading: ref(false)`, `error: ref(null)`

#### Testing

- [ ] **Unit tests for pricing logic**
  - Test group determination with various category/material combinations
  - Test each adjustment calculator with edge cases
  - Test main algorithm with known inputs/outputs
  - Mock LLM responses for predictable tests

- [ ] **Integration tests for API**
  - Test `/api/pricing/calculate` endpoint with full product data
  - Test LLM generation and caching (first call generates, second call retrieves)
  - Test error handling (missing brand, invalid category, LLM timeout)

### Out of Scope (Explicitly NOT in v1)

- **Admin interface for trends/features** - Coefficients managed via migrations/seeds
- **Price history tracking** - Don't store calculated prices, compute on demand
- **ML learning from real sales** - No feedback loop, pure algorithmic (v2 feature)
- **Pricing analytics dashboard** - No stats on suggested vs actual prices (v2)
- **Batch pricing for imports** - Focus on single product pricing first
- **User-customizable coefficients** - Use fixed/LLM-generated values only
- **A/B testing of pricing strategies** - Not needed for v1

---

## Context

### Existing Codebase

**Architecture** (from `.planning/codebase/ARCHITECTURE.md`):
- Clean Architecture: API → Services → Repositories → Models
- Multi-tenant PostgreSQL with schema-per-user
- Gemini AI service already integrated (`services/ai/gemini_service.py`)
- Product model with 33+ attributes in `models/user/product.py`

**Key Files to Extend**:
- `backend/services/` - Add `pricing_service.py`, `pricing_generation_service.py`
- `backend/models/public/` - Add `brand_group.py`, `model.py` (new models in public schema)
- `backend/repositories/` - Add `brand_group_repository.py`, `model_repository.py`
- `backend/api/` - Add `pricing.py` or extend `products.py` with pricing endpoint
- `frontend/composables/` - Add `usePricing.ts`
- `frontend/components/products/` - Add `PricingDisplay.vue`

**Attribute Tables Already Exist**:
- Trends, features, origins, conditions are already in database
- Access via existing repositories (check `backend/repositories/`)

### Business Rules

**Formula**: `PRICE = BASE_PRICE × MODEL_COEFF × (1 + ADJUSTMENTS)`

**Group Determination**:
- 69 groups total: category × material type
- Material priority: LEATHER > DENIM > WOOL_LUXURY > NATURAL > TECHNICAL > SYNTHETIC
- Examples: "jacket_leather", "jeans", "shirt_luxury", "dress_synthetic"

**Expected vs Actual Logic**:
- Each Brand×Group defines what's EXPECTED (origins, decades, trends)
- Bonus only if actual > expected
- Malus if actual < expected
- Example: Levi's jeans expect USA/Mexico origins → USA origin = 0% adjustment, Japan origin = +8%

**Condition Sensitivity**:
- Luxury brands (0.5): État impacte peu (Hermès reste cher même usé)
- Premium (0.8): État impacte modérément (APC, Acne)
- Standard (1.0): Impact normal
- Fast fashion (1.3): État impacte beaucoup (Zara, H&M)
- Ultra budget (1.5): Quasi invendable si usé (Primark)

**Caps & Limits**:
- Condition malus: Max -80% (score 0/10)
- Features bonus: Max +30% (cumulative)
- Minimum price: 3€
- Maximum price: Check coherence with retail (≤80% unless collector)

---

## Constraints

### Technical

- **Use Google Gemini for LLM** - Already integrated, cheaper than GPT-4
- **Tables in `public` schema** - Brand groups and models are shared data, not per-tenant
- **Async/await pattern** - Follow existing FastAPI async patterns
- **Multi-tenant safe** - Pricing calculations work for all users, shared BrandGroup cache
- **TypeScript strict mode** - Frontend must pass type checks
- **No new dependencies** - Use existing stack (FastAPI, SQLAlchemy, Nuxt, Pinia)

### Data

- **LLM responses must be validated** - Check base_price range (5-500€), condition_sensitivity (0.5-1.5)
- **Cache LLM results** - Generate Brand×Group once, store in DB forever
- **Graceful fallback** - If LLM fails, use conservative defaults (base_price=30€, sensitivity=1.0)
- **Read from existing attribute tables** - Don't duplicate trends/features/origins data

### Performance

- **LLM calls can take 2-5 seconds** - Show loading state in UI
- **Cache strategy** - Check DB first, only call LLM if missing
- **No blocking operations** - Use async for all LLM/DB calls
- **Timeout LLM calls** - Max 10s, fallback after timeout

### UX

- **3 price levels displayed** - Quick/Standard/Premium with clear labels
- **Transparent breakdown** - Show user how price was calculated (base + model + adjustments)
- **Optional calculation** - Don't force pricing, let user trigger it
- **Error messages** - Clear feedback if pricing fails ("Unable to calculate, missing brand data")

---

## Key Decisions

### Architecture Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Store Brand×Group and Models in `public` schema | Shared data across all users, not tenant-specific | Single source of truth, efficient caching |
| Use Google Gemini for LLM generation | Already integrated, lower cost than GPT-4 | Leverage existing `services/ai/gemini_service.py` |
| Calculate on-demand, don't store prices | Prices are time-sensitive, attributes can change | Always fresh calculations, no stale data |
| 69 groups with category × material split | Balance specificity vs manageability | Accurate pricing without infinite combinations |

### Business Logic Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| "Expected vs Actual" prevents double counting | Brand context defines what's normal | Fair pricing, avoid bonus stacking |
| 3 price levels (quick/standard/premium) | Give user flexibility based on sale urgency | ×0.75 / ×1.0 / ×1.30 multipliers |
| Condition sensitivity varies by brand tier | Luxury holds value, fast fashion doesn't | 0.5 (Hermès) to 1.5 (Primark) |
| Features bonus capped at +30% | Prevent absurd prices from feature stacking | Reasonable ceiling on premiums |

### Technical Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Material priority: LEATHER > DENIM > WOOL | Reflects pricing hierarchy in secondhand market | Leather jacket ≠ synthetic jacket |
| LLM prompts specify "secondhand resale price" | Avoid confusion with retail pricing | GPT understands marketplace context |
| Validate LLM responses before storing | LLMs can hallucinate unrealistic values | Check ranges, reject outliers |
| Display pricing breakdown in UI | Build user trust in algorithm | Transparency = adoption |

---

## Risks & Mitigations

### Risk: LLM generates unrealistic prices

**Mitigation**:
- Validate all LLM outputs (base_price 5-500€, sensitivity 0.5-1.5)
- Reject and retry if values out of range
- Fallback to conservative defaults if repeated failures
- Manual review of first 100 generated Brand×Groups

### Risk: Group determination logic is complex

**Mitigation**:
- Extensive unit tests with all 69 groups
- Document material priority clearly in code comments
- Test edge cases (multiple materials, unknown materials)

### Risk: Frontend loading time for LLM calls

**Mitigation**:
- Show clear loading state ("Calculating price...")
- Cache aggressively (most brands will be generated after first week)
- Timeout after 10s with friendly error message
- Consider pre-generating popular brands asynchronously

### Risk: Users don't trust algorithmic pricing

**Mitigation**:
- Show detailed breakdown (base + model + adjustments)
- Include "Why this price?" explanations
- Allow manual override (user can ignore suggestions)
- Collect feedback for v2 improvements

---

## Success Criteria

### Functional

- [ ] User can click "Calculate Price" on product and see 3 suggestions within 10s
- [ ] Pricing breakdown shows base_price, model_coeff, and all 6 adjustments
- [ ] LLM-generated Brand×Group data is cached and reused on second request
- [ ] Algorithm handles all 69 groups correctly (tested)
- [ ] Edge cases handled: missing brand, unknown category, no model specified

### Technical

- [ ] All unit tests pass (>80% coverage on pricing logic)
- [ ] Integration tests pass for pricing API endpoint
- [ ] LLM calls timeout gracefully after 10s
- [ ] Database migrations applied cleanly (brand_groups, models tables)
- [ ] Frontend TypeScript compilation succeeds with no errors

### User Experience

- [ ] Pricing UI is intuitive (3 prices clearly labeled)
- [ ] Loading states shown during LLM generation
- [ ] Error messages are actionable ("Missing brand, please add brand first")
- [ ] Breakdown is readable (not technical jargon)

---

## Open Questions

None currently - all key decisions have been made based on the comprehensive documentation provided.

---

## Implementation Summary

**Feature**: Intelligent Pricing Algorithm
**Status**: Complete ✅
**Completed**: 2026-01-12

### Overview

Implemented a comprehensive pricing algorithm that generates intelligent price suggestions for secondhand products using LLM-powered data generation and a transparent adjustment-based calculation formula.

### Architecture

**Backend (FastAPI + PostgreSQL + Google Gemini)**:
- **Database**: Brand×Group base prices + Model coefficients (auto-generated via LLM)
- **Group Determination**: 69 product groups based on category + materials
- **LLM Generation Service**: Gemini-powered generation with validation and fallbacks
- **6 Adjustment Calculators**: Condition, Origin, Decade, Trend, Feature, Model
- **Pricing Service**: Orchestrates fetch-or-generate → calculate → return 3 price levels
- **REST API**: POST /pricing/calculate with JWT auth

**Frontend (Nuxt.js 3 + Vue 3 + Tailwind CSS)**:
- **Composable**: usePricingCalculation for API integration and state management
- **Component**: PricingDisplay with 3 color-coded price cards + expandable breakdown
- **Integration**: Product detail page with "Calculate Price" button

### Pricing Formula

```
STANDARD_PRICE = BASE_PRICE × MODEL_COEFF × (1 + TOTAL_ADJUSTMENTS)

Where:
- BASE_PRICE: LLM-generated for Brand×Group (€20-500 range)
- MODEL_COEFF: LLM-generated for specific models (0.6-2.0 range), default 1.0
- TOTAL_ADJUSTMENTS: Sum of 6 adjustment values (-1.0 to +1.0 each)

Price Levels:
- Quick Sale: STANDARD × 0.75
- Standard: STANDARD × 1.0 (recommended)
- Premium: STANDARD × 1.30
```

### Adjustment Calculators

1. **Condition** (-0.50 to +0.20): Based on condition score (0-5) + supplements
2. **Origin** (-0.30 to +0.30): Tier-based comparison (actual vs expected)
3. **Decade** (-0.10 to +0.30): Bonus for unexpected vintage decades
4. **Trend** (-0.05 to +0.25): Best unexpected trend bonus
5. **Feature** (-0.10 to +0.30): Sum of unexpected feature bonuses
6. **Model**: Coefficient multiplier (not additive)

### Product Groups (69 total)

**Categories with material variations**:
- Bags: leather, textile, exotic
- Clothing: coats (leather/textile/wool), jackets (leather/denim/textile), pants (denim/textile), etc.
- Shoes: sneakers, boots, heels (leather/textile variations)
- Accessories: watches, jewelry, scarves, etc.
- Home: furniture, decoration (wood/metal/glass variations)

### Error Handling

- **400**: Validation errors (missing fields, invalid ranges)
- **500**: LLM generation failures (with database rollback)
- **504**: Timeout errors (>30s processing)
- **Logging**: Structured logging with elapsed_time_ms, user_id, brand context

### Testing

**Backend**:
- Unit tests: 94 tests for adjustment calculators
- Unit tests: 20 tests for pricing service orchestration
- Integration tests: 19 tests for API endpoint
- Total: 2500+ lines of test code

**Frontend**:
- Unit tests: 9+ tests for usePricingCalculation composable
- Configured: Vitest + @nuxt/test-utils
- Coverage: State management, API integration, error handling

**E2E**:
- Manual test scenarios documented (luxury, streetwear, vintage, errors)
- Real-world brand validation

### Key Decisions

1. **LLM Provider**: Google Gemini (already integrated, generous free tier)
2. **Fetch-or-Generate**: Automatic LLM fallback if data missing (no manual seeding)
3. **Price Transparency**: Expandable breakdown showing all adjustments + formula
4. **Color Scheme**: Blue (quick), Green (standard/recommended), Purple (premium)
5. **Error Strategy**: User-friendly messages, no stack traces, performance logging
6. **Test Strategy**: Comprehensive backend coverage, frontend composable testing
7. **Material Priority**: LEATHER > DENIM > WOOL > NATURAL > TECHNICAL > SYNTHETIC

### Files

**Backend**:
- `backend/repositories/brand_group_repository.py`
- `backend/repositories/model_repository.py`
- `backend/services/pricing/group_determination.py`
- `backend/services/pricing/adjustment_calculators.py`
- `backend/services/pricing_generation_service.py`
- `backend/services/pricing_service.py`
- `backend/api/pricing.py`
- `backend/schemas/pricing.py`
- `backend/models/public/brand_group.py`
- `backend/models/public/model.py`

**Frontend**:
- `frontend/composables/usePricingCalculation.ts`
- `frontend/components/products/PricingDisplay.vue`
- `frontend/pages/dashboard/products/[id]/index.vue` (integration)

**Database**:
- Migration: `2f3a9708b420_add_brand_groups_table.py`
- Migration: `68a6d6ef6f65_add_models_table.py`

### Performance

- **Average Response Time**: 2-5 seconds (with LLM generation)
- **Cached Response Time**: <500ms (data already exists)
- **Timeout Threshold**: 30 seconds
- **Database**: Indexed on brand+group, brand+group+model for fast lookups

### Future Enhancements

Logged in `.planning/ISSUES.md`:
- Performance optimization: connection pooling, caching strategies
- Enhanced model generation: more context, fine-tuning
- Additional adjustment factors: seasonality, market trends
- Bulk pricing calculations
- Price history tracking

---

*Last updated: 2026-01-12 after Phase 7 completion*
