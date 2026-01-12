# E2E Test Scenarios - Pricing Algorithm

**Purpose**: Manual validation with realistic brand and product data to verify end-to-end functionality.

**Prerequisites**:
- Backend running: `cd backend && uvicorn main:app --reload`
- Frontend running: `cd frontend && npm run dev`
- User authenticated in frontend
- At least one product created in dashboard

---

## Test Scenario 1: Luxury Fashion - Louis Vuitton Handbag

**Product Data**:
- Brand: Louis Vuitton
- Category: Bag
- Materials: [Leather]
- Model: Speedy 30
- Condition Score: 4 (Very Good)
- Supplements: [Original Box, Dust Bag, Authentication Card]
- Origin: France
- Decade: 2010s
- Trends: [Vintage Revival, Minimalism]
- Features: [Monogram Canvas, Golden Hardware]

**Expected Behavior**:
1. Click "Calculate Price" on product detail page
2. Loading spinner appears (1-5 seconds)
3. Backend determines group: "bag_leather"
4. Backend fetches/generates Louis Vuitton × bag_leather base price (expect ~€200-400)
5. Backend fetches/generates Speedy 30 model coefficient (expect ~1.2-1.5)
6. Backend calculates adjustments:
   - Condition: +0.14 (score 4 + 3 supplements)
   - Origin: +0.10 (France expected for luxury bags)
   - Decade: 0.00 (2010s typical for fashion)
   - Trend: +0.05 (Vintage Revival matches expected)
   - Feature: +0.10 (Monogram + Hardware expected features)
   - Total: ~+0.39
7. PricingDisplay shows 3 prices (proportions: 0.75 / 1.0 / 1.3)
8. Breakdown section toggles correctly
9. All 6 adjustments visible with correct signs and colors
10. Formula shown: Base × Model × (1 + Total)

**Validation Checklist**:
- [ ] Calculate button works
- [ ] Loading state appears
- [ ] Prices returned within 10 seconds
- [ ] 3 price cards displayed (Quick/Standard/Premium)
- [ ] Standard price marked "Recommended"
- [ ] Breakdown section expandable
- [ ] All 6 adjustments shown
- [ ] Colors correct (green for positive, red for negative)
- [ ] Formula visible and accurate
- [ ] No console errors

---

## Test Scenario 2: Streetwear - Nike Air Jordan 1

**Product Data**:
- Brand: Nike
- Category: Sneakers
- Materials: [Leather, Rubber]
- Model: Air Jordan 1 Retro High OG
- Condition Score: 5 (New/Mint)
- Supplements: [Original Box, Extra Laces]
- Origin: China
- Decade: 2020s
- Trends: [Streetwear, Sneaker Culture]
- Features: [OG Colorway, High Top]

**Expected Behavior**:
1. Group: "sneakers_leather"
2. Base price: €80-150 (mid-range sneakers)
3. Model coefficient: 1.8-2.2 (Air Jordan 1 is iconic)
4. Adjustments:
   - Condition: +0.16 (score 5 + 2 supplements)
   - Origin: 0.00 (China typical for sneakers)
   - Decade: -0.05 (2020s recent, less vintage value)
   - Trend: +0.10 (Streetwear + Sneaker Culture both expected)
   - Feature: +0.15 (OG Colorway highly valued)
   - Total: ~+0.36
5. Prices displayed correctly

**Validation**: Same checklist as Scenario 1

---

## Test Scenario 3: Vintage Furniture - Mid-Century Danish Chair

**Product Data**:
- Brand: Unknown/Generic
- Category: Furniture
- Materials: [Wood, Fabric]
- Model: (leave empty)
- Condition Score: 3 (Good)
- Supplements: []
- Origin: Denmark
- Decade: 1960s
- Trends: [Mid-Century Modern]
- Features: [Teak Wood, Original Upholstery]

**Expected Behavior**:
1. Group: "furniture_wood"
2. Base price: €50-100 (generic furniture)
3. Model coefficient: 1.0 (no model specified)
4. Adjustments:
   - Condition: +0.05 (score 3, no supplements)
   - Origin: +0.15 (Denmark premium for mid-century furniture)
   - Decade: +0.20 (1960s highly valued for mid-century)
   - Trend: +0.15 (Mid-Century Modern is expected trend)
   - Feature: +0.20 (Teak + Original Upholstery premium)
   - Total: ~+0.75
5. High premium due to vintage value

**Validation**: Same checklist as Scenario 1

---

## Test Scenario 4: Error Handling - Invalid Product

**Product Data**:
- Brand: (empty)
- Category: (empty)
- Materials: []

**Expected Behavior**:
1. "Calculate Price" button should be disabled (validation)
2. OR if clicked, backend returns 400
3. Error banner displays: "Invalid product data. Please check all fields."
4. No pricing displayed
5. User can correct and retry

**Validation**:
- [ ] Validation prevents calculation OR
- [ ] 400 error handled gracefully
- [ ] Error message user-friendly
- [ ] No crash or console errors

---

## Test Scenario 5: Timeout Simulation (if possible)

**Setup**: Temporarily modify backend to sleep 35+ seconds in calculate endpoint

**Expected Behavior**:
1. Loading spinner for 30+ seconds
2. Backend returns 504 (timeout)
3. Error banner: "Pricing calculation timed out. Please try again."
4. User can retry

**Validation**:
- [ ] Timeout handled without crash
- [ ] User-friendly error message
- [ ] Can retry successfully after timeout

---

## Summary Checklist

After all scenarios:
- [ ] 3+ successful price calculations with different brands/categories
- [ ] All price levels (Quick/Standard/Premium) reasonable
- [ ] Breakdown adjustments make logical sense
- [ ] Error handling works (validation, timeout if tested)
- [ ] No console errors in any scenario
- [ ] UI responsive on mobile and desktop
- [ ] Loading states clear and non-blocking
- [ ] Can calculate multiple times without page refresh
