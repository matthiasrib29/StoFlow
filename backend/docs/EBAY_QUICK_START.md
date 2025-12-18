# eBay Integration - Quick Start Guide

**Date**: 2025-12-10
**Status**: Foundation Layer Complete ✅

---

## What's Been Done

### 1. Database Layer ✅ COMPLETE

**Migration Created**: `migrations/versions/20251210_1217_create_ebay_schema_and_tables.py`

**What it does**:
- Creates 3 PUBLIC tables (shared across all users)
- Extends `platform_mappings` with 35 eBay columns
- Creates 4 TEMPLATE_TENANT tables (cloned to each user schema)
- Seeds reference data (8 marketplaces, 17 aspects, 2 exchange rates)

### 2. SQLAlchemy Models ✅ COMPLETE

**PUBLIC schema models** (`models/public/`):
- `ebay_marketplace_config.py` - MarketplaceConfig
- `ebay_aspect_mapping.py` - AspectMapping
- `ebay_exchange_rate.py` - ExchangeRate

**USER schema models** (`models/user/`):
- `ebay_product_marketplace.py` - EbayProductMarketplace
- `ebay_promoted_listing.py` - EbayPromotedListing
- `ebay_order.py` - EbayOrder + EbayOrderProduct

### 3. API Routes ✅ COMPLETE (Structure)

**File**: `api/ebay.py`

**Functional endpoints** (4/9):
- `GET /api/ebay/marketplaces` - List active marketplaces
- `GET /api/ebay/settings` - Get user eBay settings
- `PUT /api/ebay/settings` - Update user eBay settings
- `GET /api/ebay/products` - List published products

**TODO endpoints** (5/9 - need services):
- `POST /api/ebay/publish` - Publish product
- `DELETE /api/ebay/unpublish/{sku}` - Unpublish product
- `GET /api/ebay/sync` - Manual sync
- `POST /api/ebay/oauth/connect` - Initiate OAuth
- `POST /api/ebay/oauth/callback` - OAuth callback

### 4. Pydantic Schemas ✅ COMPLETE

**File**: `schemas/ebay_schemas.py`
- 14 schemas for requests/responses
- Full validation + type hints

### 5. Environment Config ✅ COMPLETE

**File**: `.env.example`
- 27 eBay environment variables added
- OAuth scopes, API endpoints, URLs

### 6. Documentation ✅ COMPLETE

**Files**:
- `docs/EBAY_INTEGRATION_STATUS.md` - Detailed status
- `docs/EBAY_IMPORT_REPORT.md` - Full import report
- `docs/EBAY_QUICK_START.md` - This file

---

## Quick Start

### Step 1: Apply the Migration

```bash
cd /home/maribeiro/Stoflow/Stoflow_BackEnd

# Apply migration
alembic upgrade head
```

**Expected output**:
```
INFO  [alembic.runtime.migration] Running upgrade ... -> 20251210_1217, create ebay schema and tables
```

**What this creates**:
- ✅ `public.marketplace_config` (8 marketplaces)
- ✅ `public.aspect_mappings` (17 aspects)
- ✅ `public.exchange_rate_config` (2 rates)
- ✅ 35 new columns in `public.platform_mappings`
- ✅ 4 tables in `template_tenant` schema

### Step 2: Verify Database

```sql
-- Check marketplaces
SELECT * FROM public.marketplace_config;
-- Expected: 8 rows (EBAY_FR, EBAY_GB, EBAY_DE, etc.)

-- Check aspects
SELECT * FROM public.aspect_mappings;
-- Expected: 17 rows (brand, color, size, etc.)

-- Check platform_mappings has eBay columns
\d public.platform_mappings
-- Expected: See ebay_client_id, ebay_price_coefficient_fr, etc.

-- Check template_tenant tables
SELECT * FROM template_tenant.ebay_products_marketplace;
-- Expected: Empty table (structure only)
```

### Step 3: Start the Server

```bash
# Start FastAPI
python main.py
```

**Expected output**:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     ✅ All required secrets configured
INFO:     Upload directory initialized
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 4: Test the API

**1. Get marketplaces** (no auth required):
```bash
curl http://localhost:8000/api/ebay/marketplaces
```

**Expected response**:
```json
[
  {
    "marketplace_id": "EBAY_FR",
    "country_code": "FR",
    "site_id": 71,
    "currency": "EUR",
    "is_active": true
  },
  ...
]
```

**2. Get user settings** (requires auth):
```bash
# First login to get token
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"yourpassword"}'

# Then get eBay settings
curl http://localhost:8000/api/ebay/settings \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Expected response**:
```json
{
  "has_credentials": false,
  "payment_policy_id": null,
  "price_coefficient_fr": 1.00,
  "price_coefficient_gb": 1.10,
  "best_offer_enabled": true,
  "best_offer_auto_accept_pct": 85.00,
  ...
}
```

**3. Update settings**:
```bash
curl -X PUT http://localhost:8000/api/ebay/settings \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "price_coefficient_fr": 1.05,
    "price_fee_gb": 7.00,
    "best_offer_enabled": false
  }'
```

### Step 5: Explore the API Docs

Open in browser: http://localhost:8000/docs

**You'll see**:
- ✅ eBay section with 9 endpoints
- ✅ Interactive testing interface
- ✅ Schema documentation

---

## What's Missing (To Be Completed)

### Priority 1: eBay Clients (9 files)

**Location**: `/home/maribeiro/PycharmProjects/pythonApiWOO/clients/ebay/`

**Files to port**:
1. `ebay_base_client.py` - OAuth2 + token management
2. `ebay_inventory_client.py` - Inventory Items API
3. `ebay_offer_client.py` - Offers API
4. `ebay_account_client.py` - Business Policies API
5. `ebay_fulfillment_client.py` - Orders API
6. `ebay_marketing_client.py` - Promoted Listings API
7. `ebay_taxonomy_client.py` - Category Tree API
8. `ebay_analytics_client.py` - Analytics API
9. `ebay_trading_client.py` - Trading API (legacy)

**Destination**: `/home/maribeiro/Stoflow/Stoflow_BackEnd/clients/ebay/`

**Adaptations required**:
- Add `user_id: int` parameter
- Replace `os.getenv()` with DB lookups from `platform_mappings`
- Use dependency injection for credentials

### Priority 2: eBay Services (23 files)

**Location**: `/home/maribeiro/PycharmProjects/pythonApiWOO/services/ebay/`

**Critical services** (start with these):
1. `ebay_multi_marketplace_service.py` - Publication orchestrator
2. `ebay_product_conversion_service.py` - Product → eBay format
3. `ebay_pricing_service.py` - Price calculation
4. `ebay_sku_service.py` - SKU derivation
5. `ebay_inventory_service.py` - Inventory wrapper
6. `ebay_offer_service.py` - Offers wrapper

**Destination**: `/home/maribeiro/Stoflow/Stoflow_BackEnd/services/ebay/`

**Adaptations required**:
- Add `user_id: int` to all methods
- Use `set_user_schema(db, user_id)` for tenant isolation
- Fetch pricing from `platform_mappings` (user-specific)

### Priority 3: Wire Up Routes

**File**: `api/ebay.py`

**Update TODO endpoints**:
1. `POST /api/ebay/publish`
   - Call `EbayMultiMarketplaceService.publish_to_marketplaces()`

2. `DELETE /api/ebay/unpublish/{sku}`
   - Call `EbayMultiMarketplaceService.unpublish_from_marketplaces()`

3. `GET /api/ebay/sync`
   - Call `EbaySyncService.sync_all_marketplaces()`

4. OAuth endpoints
   - Implement OAuth flow with eBay

---

## Architecture Decisions

### Multi-Tenant Strategy

**Problem**: How to handle user-specific eBay credentials?

**Solution**: Store in `public.platform_mappings` table (35 new columns)

**Example**:
```python
# Each user has their own:
mapping.ebay_client_id = "USER_CLIENT_ID"
mapping.ebay_client_secret = "USER_CLIENT_SECRET"
mapping.ebay_refresh_token = "USER_REFRESH_TOKEN"
mapping.ebay_payment_policy_id = 123456
mapping.ebay_price_coefficient_fr = 1.05  # User-specific pricing
```

### Pricing Strategy

**Formula**:
```python
final_price = (base_price_eur * coefficient) + fee
```

**Example**:
```python
# Product: 100 EUR
# EBAY_GB: coefficient=1.10, fee=5.00
# Result: (100 * 1.10) + 5 = 115.00 GBP (before currency conversion)
```

### Schema Isolation

**PUBLIC schema**:
- `marketplace_config` - Shared (8 marketplaces)
- `aspect_mappings` - Shared (17 aspects)
- `exchange_rate_config` - Shared (2 rates)
- `platform_mappings` - User settings (35 eBay columns)

**USER_{id} schema**:
- `ebay_products_marketplace` - User's published products
- `ebay_promoted_listings` - User's campaigns
- `ebay_orders` - User's orders

---

## File Structure

```
Stoflow_BackEnd/
├── api/
│   └── ebay.py                           ✅ API routes (9 endpoints)
├── migrations/versions/
│   └── 20251210_1217_*.py                ✅ eBay migration
├── models/
│   ├── public/
│   │   ├── ebay_marketplace_config.py    ✅ MarketplaceConfig
│   │   ├── ebay_aspect_mapping.py        ✅ AspectMapping
│   │   └── ebay_exchange_rate.py         ✅ ExchangeRate
│   └── user/
│       ├── ebay_product_marketplace.py   ✅ EbayProductMarketplace
│       ├── ebay_promoted_listing.py      ✅ EbayPromotedListing
│       └── ebay_order.py                 ✅ EbayOrder + EbayOrderProduct
├── schemas/
│   └── ebay_schemas.py                   ✅ 14 Pydantic schemas
├── clients/ebay/                         ❌ TO BE CREATED (9 files)
├── services/ebay/                        ❌ TO BE COMPLETED (23 files)
├── docs/
│   ├── EBAY_INTEGRATION_STATUS.md        ✅ Detailed status
│   ├── EBAY_IMPORT_REPORT.md             ✅ Full report
│   └── EBAY_QUICK_START.md               ✅ This file
└── .env.example                          ✅ Updated with eBay vars
```

---

## Code Metrics

| Category | Files Created | Lines of Code |
|----------|---------------|---------------|
| Migration | 1 | ~350 |
| Models | 6 | ~710 |
| API Routes | 1 | ~390 |
| Schemas | 1 | ~260 |
| Documentation | 3 | ~900 |
| **TOTAL** | **12** | **~2,610** |

---

## Next Steps

### Immediate (Today)

1. ✅ Apply migration: `alembic upgrade head`
2. ✅ Start server: `python main.py`
3. ✅ Test endpoints: `curl http://localhost:8000/api/ebay/marketplaces`
4. ✅ Explore docs: http://localhost:8000/docs

### Short-term (This Week)

1. Port `ebay_base_client.py` (OAuth foundation)
2. Implement OAuth flow (connect + callback endpoints)
3. Port core services (multi_marketplace, pricing, sku)
4. Test basic publication flow

### Medium-term (This Month)

1. Port all remaining clients (9 files)
2. Port all remaining services (23 files)
3. Wire up all TODO endpoints
4. Add comprehensive tests
5. Production deployment

---

## Support

**For technical questions**: See full reports in `docs/EBAY_IMPORT_REPORT.md`

**For architecture questions**: See `docs/EBAY_INTEGRATION_STATUS.md`

**For source reference**: `/home/maribeiro/PycharmProjects/pythonApiWOO/`

---

**Created**: 2025-12-10 12:50
**Author**: Claude Sonnet 4.5
**Version**: 1.0
