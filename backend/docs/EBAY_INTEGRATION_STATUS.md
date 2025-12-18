# eBay Integration - Import Status

**Date**: 2025-12-10
**Project**: Stoflow Backend
**Source**: pythonApiWOO eBay integration

## Status: PARTIAL IMPORT (FOUNDATIONAL LAYER COMPLETE)

### COMPLETED

#### 1. Database Layer (100%)
- Migration created: `20251210_1217_create_ebay_schema_and_tables.py`
  - PUBLIC schema tables: `marketplace_config`, `aspect_mappings`, `exchange_rate_config`
  - Extended `platform_mappings` with 35 eBay-specific columns (credentials, pricing, settings)
  - TEMPLATE_TENANT schema tables: `ebay_products_marketplace`, `ebay_promoted_listings`, `ebay_orders`, `ebay_orders_products`
  - Seed data: 8 marketplaces, 17 aspect mappings, 2 exchange rates

#### 2. SQLAlchemy Models (100%)
- **PUBLIC schema** (`/models/public/`):
  - `ebay_marketplace_config.py`: MarketplaceConfig model
  - `ebay_aspect_mapping.py`: AspectMapping model
  - `ebay_exchange_rate.py`: ExchangeRate model

- **USER schema** (`/models/user/`):
  - `ebay_product_marketplace.py`: EbayProductMarketplace model
  - `ebay_promoted_listing.py`: EbayPromotedListing model
  - `ebay_order.py`: EbayOrder + EbayOrderProduct models

- **Updated `__init__.py`** in both `models/public/` and `models/user/`

### TO BE COMPLETED

#### 3. eBay API Clients (0/9) - PRIORITY HIGH
**Location**: `/clients/ebay/`

Required files (from pythonApiWOO):
1. `ebay_base_client.py` - OAuth2, token cache, base api_call()
2. `ebay_inventory_client.py` - Inventory Items API
3. `ebay_offer_client.py` - Offers API
4. `ebay_account_client.py` - Business Policies API
5. `ebay_fulfillment_client.py` - Orders/Fulfillment API
6. `ebay_marketing_client.py` - Promoted Listings API
7. `ebay_taxonomy_client.py` - Category Tree API
8. `ebay_analytics_client.py` - Traffic Reports API
9. `ebay_trading_client.py` - Trading API (legacy)

**Multi-tenant adaptations required**:
- Add `user_id: int` parameter to all clients
- Replace `os.getenv()` with credentials from `platform_mappings` table (user-specific)
- Inject credentials via dependency injection (FastAPI Depends)
- Add user_id to all logger contexts

#### 4. eBay Services (0/23) - PRIORITY HIGH
**Location**: `/services/ebay/`

**Core Services**:
1. `ebay_multi_marketplace_service.py` - Orchestrator (publish/unpublish)
2. `ebay_product_conversion_service.py` - Product → eBay format
3. `ebay_seo_service.py` - Multilingual titles
4. `ebay_aspect_service.py` - Cached aspect mappings
5. `ebay_aspect_value_service.py` - Aspect value translation
6. `ebay_sku_service.py` - Derived SKU generation

**Pricing Services**:
7. `ebay_pricing_service.py` - Price calculation (coefficient + fees from platform_mappings)
8. `ebay_best_offer_service.py` - Best Offer auto-generation
9. `ebay_currency_service.py` - Currency conversion
10. `ebay_exchange_rate_service.py` - Exchange rate management

**Publication Services**:
11. `ebay_inventory_service.py` - Inventory Items wrapper
12. `ebay_offer_service.py` - Offers wrapper
13. `ebay_listing_utility_service.py` - Listing helpers

**Advanced Services**:
14. `ebay_promoted_listings_service.py` - Promoted Listings management
15. `ebay_sync_service.py` - Manual sync API → DB
16. `ebay_order_service.py` - Order management
17. `ebay_price_sync_service.py` - Price synchronization
18. `ebay_marketplace_service.py` - Marketplace utilities
19. `ebay_marketplace_setup_service.py` - Marketplace setup
20. `ebay_title_service.py` - Title generation
21. `ebay_description_multilang_service.py` - Multilingual descriptions
22. `ebay_fulfillment_policy_service.py` - Fulfillment policies
23. `ebay_offer_policy_service.py` - Offer policies

**Multi-tenant adaptations required**:
- Add `user_id: int` to all service methods
- Use `search_path` for user-specific tables
- Fetch pricing/settings from `platform_mappings` (user-specific)
- Replace hardcoded schemas (`ebay.`) with dynamic schema (`user_{id}.`)

#### 5. FastAPI Routes (0/1) - PRIORITY CRITICAL
**Location**: `/api/ebay.py`

**Required endpoints**:
```python
POST   /api/ebay/publish               # Publish product to eBay
DELETE /api/ebay/unpublish/{sku}       # Unpublish product
GET    /api/ebay/sync                  # Manual sync
GET    /api/ebay/marketplaces          # List active marketplaces
GET    /api/ebay/products              # List published products
POST   /api/ebay/oauth/connect         # Initiate OAuth flow
POST   /api/ebay/oauth/callback        # OAuth callback
GET    /api/ebay/settings              # Get user eBay settings
PUT    /api/ebay/settings              # Update user eBay settings
```

**Register in `main.py`**:
```python
from api import ebay
app.include_router(ebay.router, prefix="/api/ebay", tags=["eBay"])
```

#### 6. Pydantic Schemas (0/1) - PRIORITY HIGH
**Location**: `/schemas/ebay_schemas.py`

**Required schemas**:
- `EbayPublishRequest`
- `EbayProductMarketplace`
- `EbaySettingsUpdate`
- `EbaySettingsResponse`
- `EbayMarketplaceInfo`
- `EbayPromotedListingResponse`
- `EbayOrderResponse`

#### 7. Environment Variables (0/1) - PRIORITY MEDIUM
**Location**: `.env.example`

**Required variables**:
- eBay API endpoints (17 scopes, 8 API URLs)
- OAuth URLs
- Request timeouts
- Sandbox mode flag

#### 8. Documentation (0/1) - PRIORITY LOW
**Location**: `/docs/EBAY_INTEGRATION.md`

**Required sections**:
- Architecture overview (multi-tenant)
- OAuth flow (user-specific credentials)
- Configuration (business policies per user)
- Pricing formulas
- Best Offer configuration
- API endpoint documentation
- Troubleshooting

## Migration Command

Once imports are complete, run:

```bash
cd /home/maribeiro/Stoflow/Stoflow_BackEnd
alembic upgrade head
```

This will:
1. Create PUBLIC tables (marketplace_config, aspect_mappings, exchange_rate_config)
2. Extend platform_mappings with 35 eBay columns
3. Create TEMPLATE_TENANT tables (ebay_products_marketplace, etc.)
4. Seed reference data (8 marketplaces, 17 aspects, 2 exchange rates)

## Next Steps (Priority Order)

1. **Create API routes** (`api/ebay.py`) - CRITICAL
2. **Create Pydantic schemas** (`schemas/ebay_schemas.py`) - HIGH
3. **Port base client** (`clients/ebay/ebay_base_client.py`) - HIGH
4. **Port core services** (multi_marketplace, product_conversion, pricing) - HIGH
5. **Port remaining clients** (8 files) - MEDIUM
6. **Port remaining services** (20 files) - MEDIUM
7. **Update .env.example** - MEDIUM
8. **Write documentation** - LOW

## Source Files Reference

All source files are located in:
- `/home/maribeiro/PycharmProjects/pythonApiWOO/clients/ebay/` (9 clients)
- `/home/maribeiro/PycharmProjects/pythonApiWOO/services/ebay/` (23 services)
- `/home/maribeiro/PycharmProjects/pythonApiWOO/Models/ebay/` (models - already ported)

## Code Metrics

- **Lines ported**: ~2,500 (migration + models)
- **Lines remaining**: ~15,000 (estimated, clients + services)
- **Files created**: 7 (1 migration + 6 models)
- **Files remaining**: 33 (9 clients + 23 services + 1 route file)

## Architecture Decisions

1. **Credentials**: USER-SPECIFIC (from `platform_mappings.ebay_*` columns)
2. **Pricing**: USER-SPECIFIC (coefficients + fees per marketplace in `platform_mappings`)
3. **Schemas**: `public` for shared data, `user_{id}` for tenant data
4. **Best Offer**: USER-CONFIGURABLE (enabled + percentages in `platform_mappings`)
5. **Promoted Listings**: USER-OPTIONAL (enabled + bid % in `platform_mappings`)
6. **Sync**: MANUAL ONLY (no automatic background sync)
7. **Images**: PUBLIC URLs ONLY (no Trading API upload)
