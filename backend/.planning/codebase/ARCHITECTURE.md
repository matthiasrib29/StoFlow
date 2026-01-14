# Architecture Overview

## System Design Pattern

**Clean Architecture** with layered separation of concerns:

```
┌─────────────────────────────────────────┐
│  API Layer (FastAPI Routes)            │  ← HTTP/WebSocket
├─────────────────────────────────────────┤
│  Service Layer (Business Logic)        │  ← Domain rules
├─────────────────────────────────────────┤
│  Repository Layer (Data Access)        │  ← DB abstraction
├─────────────────────────────────────────┤
│  Model Layer (SQLAlchemy Entities)     │  ← Data models
└─────────────────────────────────────────┘
```

**Dependency Flow**: API → Services → Repositories → Models → Database

---

## Multi-Tenant Architecture

### Schema-per-Tenant Isolation

**Strategy**: PostgreSQL schema isolation (not database-per-tenant)

**Schema Types**:
| Schema | Purpose | Scope |
|--------|---------|-------|
| `public` | Authentication, subscriptions, quotas | Global (all users) |
| `product_attributes` | Brands, colors, conditions, materials, sizes | Shared reference data |
| `user_{id}` | Products, jobs, orders, conversations | Tenant-isolated |
| `template_tenant` | Blueprint cloned for new users | Template |

**Isolation Mechanism**:
- **File**: `shared/database.py`
- **Method**: `schema_translate_map` in execution_options (SQLAlchemy 2.0)
- **Deprecated**: `SET search_path` (removed 2026-01-13)

**Flow**:
1. API dependency `get_user_db()` authenticates user via JWT
2. Session configured: `execution_options(schema_translate_map={"tenant": f"user_{user_id}"})`
3. All ORM queries automatically scoped to `user_{id}` schema
4. Cross-schema access via explicit FK constraints (e.g., `user_X.products.brand_id → public.brands.id`)

**Advantages**:
- ✅ Strong isolation (schema-level permissions)
- ✅ Shared reference data (no duplication)
- ✅ Easy backup/restore per tenant
- ✅ Scales to ~1000 tenants

**Limitations**:
- Migrations must iterate over all `user_*` schemas (fan-out pattern)
- Metadata bloat if >1000 schemas
- Connection pool shared across tenants

---

## Image Management Architecture

### Current Implementation: JSONB in Product Model

**Model**: `models/user/product.py` (lines 386-394)

```python
images: Mapped[list[dict]] = mapped_column(
    JSONB,
    nullable=True,
    server_default="[]",
    comment="Product images as JSONB array [{url, order, created_at}]",
)
```

**Structure**:
```json
[
  {
    "url": "https://cdn.stoflow.io/1/products/5/abc123.jpg",
    "order": 0,
    "created_at": "2026-01-03T10:00:00Z"
  },
  ...max 20 images (Vinted constraint)
]
```

**Migration History**:
- **2026-01-03**: Migrated from `product_images` table to JSONB column
  - Phase 1: `20260103_1749_migrate_images_to_jsonb.py` - Data migration
  - Phase 2: `20260103_1759_drop_product_images_table.py` - Drop table
- **Rationale**: Simpler queries, no JOIN needed, JSONB indexing support

**Services**:
- `ProductImageService` - CRUD operations on JSONB array
  - `add_image()` - Append image (max 20 limit)
  - `delete_image()` - Remove + auto-reorder
  - `reorder_images()` - Change display order
- `FileService` - Upload/download/optimize images to Cloudflare R2

**Storage Flow**:
1. User uploads image via API (`POST /api/products/{id}/images`)
2. `FileService` validates format (magic bytes) + optimizes (Pillow)
3. Upload to Cloudflare R2: `{user_id}/products/{product_id}/{uuid}.ext`
4. `ProductImageService.add_image()` appends `{url, order, created_at}` to JSONB
5. Return public R2 CDN URL

**Limitations**:
- ❌ No image type classification (product photo vs. label/price tag)
- ❌ Cannot query "images of type X" without application logic
- ❌ No per-image metadata beyond URL, order, created_at
- ❌ Downgrade path recreates table structure but **does not restore data**

---

## Unified Job System (2026-01-09 Refactor)

### Marketplace Job Orchestration

**Problem Solved**: Previously separate job processors for Vinted, eBay, Etsy
**Solution**: Single `MarketplaceJobProcessor` with handler registry

**Architecture**:
```
MarketplaceJobProcessor (Unified)
  ├── Dispatch → VINTED_HANDLERS (7 handlers, WebSocket)
  ├── Dispatch → EBAY_HANDLERS (5 handlers, Direct HTTP)
  └── Dispatch → ETSY_HANDLERS (5 handlers, Direct HTTP)
```

**Data Model**: `models/user/marketplace_job.py`
```python
class MarketplaceJob(Base):
    __tablename__ = "marketplace_jobs"

    marketplace: str  # "vinted" | "ebay" | "etsy"
    action_type_id: int  # FK to public.marketplace_action_types
    product_id: int | None  # FK to product
    batch_job_id: int | None  # FK to BatchJob
    status: JobStatus  # pending → running → completed/failed/cancelled
    priority: int  # 0-10 (higher = more urgent)
```

**Status Flow**:
```
pending → running → completed
                 ↘ failed
                 ↘ cancelled
                 ↘ expired (timeout)
```

### Handler Pattern: Registry-Based Dispatch

**Registry Location**: `services/marketplace/marketplace_job_processor.py`

**Format**: `{action_code}_{marketplace}` → Handler class
- `publish_vinted` → `VintedPublishHandler`
- `update_ebay` → `EbayUpdateHandler`
- `delete_etsy` → `EtsyDeleteHandler`

**Base Handler**: `services/vinted/jobs/base_job_handler.py`

Two communication patterns:
1. **WebSocket** (Vinted) - `call_plugin()` → `PluginWebSocketHelper`
2. **HTTP** (eBay/Etsy) - `call_http()` → Direct OAuth 2.0 API

**Available Handlers**:
| Marketplace | Handlers |
|-------------|----------|
| Vinted | publish, update, delete, sync, orders, message, link (7 total) |
| eBay | publish, update, delete, sync, sync_orders (5 total) |
| Etsy | publish, update, delete, sync, sync_orders (5 total) |

**Processing Algorithm**:
1. Fetch highest priority pending job for marketplace
2. Lock job (status → running)
3. Dispatch to handler via registry lookup
4. Handler executes (WebSocket or HTTP)
5. Update job status (completed/failed)
6. Log result + retry if needed

---

## WebSocket Communication (2026-01-08)

### Real-Time Plugin Communication

**Architecture**:
```
Backend (MarketplaceJob)
    ↓ WebSocket Event
Frontend (useWebSocket composable)
    ↓ Socket.IO relay
Plugin (Browser Extension)
    ↓ XHR to Vinted API
Vinted API
```

**Components**:
- `services/websocket_service.py` - Socket.IO server (python-socketio)
- `services/plugin_websocket_helper.py` - Async HTTP wrapper
- `main.py` (lines 148-155) - ASGIApp wrapping

**Protocol**: Socket.IO Events
```python
# Backend → Plugin
sio.emit('plugin:http:request', {
    'request_id': uuid,
    'method': 'POST',
    'path': '/api/v2/items',
    'payload': {...}
})

# Plugin → Backend
sio.emit('plugin:http:response', {
    'request_id': uuid,
    'status': 200,
    'data': {...}
})
```

**Timeout**: 60 seconds (configurable per action)
**Reconnection**: Automatic with exponential backoff (1-5s)

**Room-Based Routing**: Each user has room `user_{id}` for message isolation

---

## Marketplace Conversion Pattern

### Product → Marketplace Format Transformation

**Pattern**: Each marketplace has a converter/mapper

| Marketplace | Converter | Output |
|-------------|-----------|--------|
| Vinted | `VintedProductConverter` | Vinted Item Payload (JSON) |
| eBay | `EbayProductConversionService` | Inventory Item + Offer (JSON) |
| Etsy | `EtsyProductConversionService` | Listing Payload (JSON) |

**Flow Example (Vinted)**:
```python
# 1. Map attributes (category, brand, condition, etc.)
mapped_attrs = VintedMappingService.map_all_attributes(db, product)

# 2. Calculate marketplace-specific price
prix_vinted = VintedPricingService.calculate_price(product)

# 3. Build payload
payload = VintedProductConverter.build_create_payload(
    product, photo_ids, mapped_attrs, prix_vinted, title, description
)

# 4. Send via WebSocket
result = await plugin_helper.call_plugin("POST", "/api/v2/items", payload)
```

**Converter Responsibilities**:
- Map internal attributes to marketplace-specific IDs
- Format images (extract URLs from JSONB)
- Calculate prices (platform-specific fees, rounding)
- Validate required fields
- Handle marketplace-specific rules (e.g., Vinted max 20 images)

---

## Authentication & Authorization

### JWT-Based Authentication

**File**: `services/auth_service.py`

**Token Types**:
| Token | TTL | Claims | Use |
|-------|-----|--------|-----|
| Access | 15 minutes | user_id, role, type, exp, iat | API authentication |
| Refresh | 7 days | user_id, type, exp, iat | Token renewal |

**Algorithm**: RS256 (asymmetric) - Public/private key pair
**Rotation**: Supports old + new secret (grace period for key rotation)

**Password Security**:
- **Hashing**: bcrypt with 12 rounds
- **Timing Attack Protection**: Random delay 100-300ms on failed login
- **Min Length**: 8 characters

**Roles**:
- `ADMIN` - Full access (all operations)
- `USER` - Own products/integrations only
- `SUPPORT` - Read-only + password reset

**Rate Limiting**: 5 login attempts before account lockout

---

## API Design Principles

### Specific Endpoints > Generic Endpoints

**✓ GOOD (Specific)**:
```
POST   /api/products/{id}/publish
POST   /api/products/{id}/duplicate
POST   /api/products/{id}/archive
POST   /api/products/{id}/images
PUT    /api/products/{id}/images/reorder
```

**✗ AVOID (Generic)**:
```
POST   /api/products/{id}/actions?action=publish
POST   /api/products/{id}/batch-actions
```

**Rationale**:
- ✅ Clear OpenAPI documentation
- ✅ Granular rate limiting per action
- ✅ Precise permission checks (RBAC)
- ✅ Better monitoring/logging per action
- ✅ Cache HTTP differentiation

**Exception**: Batch operations or webhooks where format is imposed externally (e.g., Stripe)

---

## Data Flow Diagrams

### Product Creation Flow
```
User → API → ProductService → AttributeValidator → ProductRepository → DB
                  ↓                                         ↓
            PricingService (calculate)              FileService (R2 upload)
```

### Vinted Publishing Flow
```
User → API → VintedPublisher → VintedProductConverter → PluginWebSocketHelper → Plugin → Vinted API
                  ↓                    ↓
            MarketplaceJobProcessor  VintedMappingService
```

### Image Upload Flow
```
User → API → FileService → R2 (S3 upload) → ProductImageService → Product.images (JSONB append)
              ↓
         Pillow (optimize)
```

---

## Key Design Decisions

| Decision | Rationale | Date |
|----------|-----------|------|
| Schema-per-tenant | Strong isolation, shared reference data | 2025-12 |
| JSONB for images | Simpler queries, no JOIN needed | 2026-01-03 |
| Unified job system | Reduce code duplication, extensible | 2026-01-09 |
| WebSocket for Vinted | Real-time, no polling overhead | 2026-01-08 |
| RSA-256 for JWT | Asymmetric keys for distributed systems | 2025-12 |
| Direct OAuth2 for eBay/Etsy | Official API support, stable | 2025-12 |

---

*Last analyzed: 2026-01-14*
