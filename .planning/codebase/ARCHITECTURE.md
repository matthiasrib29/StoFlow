# System Architecture

## Overview

StoFlow is a **multi-channel e-commerce management platform** built as a monorepo with three primary modules:

```
┌──────────────────────────────────────────────────────────────┐
│                    StoFlow Platform                          │
├──────────────────────────────────────────────────────────────┤
│  Frontend (Nuxt.js)  │  Backend (FastAPI)  │  Plugin (Vue)  │
│   Web Dashboard      │   REST API + WS     │   Browser Ext  │
└──────────────────────────────────────────────────────────────┘
         │                      │                      │
         └──────────┬───────────┴──────────┬──────────┘
                    │                      │
         ┌──────────▼──────────┐  ┌────────▼────────┐
         │  PostgreSQL (Multi- │  │  Marketplaces   │
         │   Tenant Schemas)   │  │  Vinted/eBay    │
         └─────────────────────┘  └─────────────────┘
```

## Core Architecture Patterns

### Clean Architecture (Backend)

The backend follows **Clean Architecture** principles with clear separation of concerns:

```
┌─────────────────────────────────────────────────────┐
│  API Routes (FastAPI)                               │
│  - Input validation via Pydantic                    │
│  - Dependency injection for DB/auth                 │
│  - HTTP exception handling                          │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│  Services (Business Logic)                          │
│  - ProductService, PricingService, AuthService      │
│  - MarketplaceJobProcessor (unified)                │
│  - Coordinate repositories + external APIs          │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│  Repositories (Data Access)                         │
│  - ProductRepository, UserRepository                │
│  - Abstract database queries                        │
│  - Multi-tenant schema handling                     │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│  Models (SQLAlchemy)                                │
│  - Product, User, MarketplaceJob                    │
│  - Database schema definitions                      │
└─────────────────────────────────────────────────────┘
```

**Benefits**:
- Business logic independent of framework
- Easy to test (mock repositories)
- Database changes don't affect services
- Clear dependency flow (top → down)

### Composition API (Frontend)

Frontend uses **Vue 3 Composition API** for reusable, type-safe logic:

```
┌─────────────────────────────────────────────────────┐
│  Vue Components (<script setup lang="ts">)          │
│  - ProductList.vue, DashboardSidebar.vue            │
│  - Use composables for logic                        │
│  - Reactive state with ref/computed                 │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│  Composables (Reusable Logic)                       │
│  - useProducts(), useAuth(), useWebSocket()         │
│  - Return reactive state + methods                  │
│  - Type-safe with TypeScript                        │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│  Stores (Pinia - Global State)                      │
│  - authStore, productsStore, vintedStore            │
│  - Shared state across components                   │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│  API Client (useApi composable)                     │
│  - JWT token management                             │
│  - Request/response interceptors                    │
│  - Error handling                                   │
└─────────────────────────────────────────────────────┘
```

## Multi-Tenant Architecture

### Schema-Per-Tenant Design

StoFlow uses **PostgreSQL schemas** for tenant isolation:

```
PostgreSQL Database
├── public                    # Shared data
│   ├── users                 # User authentication
│   ├── subscription_quotas   # Usage limits
│   ├── ai_credits            # Credit ledger
│   └── marketplace_action_types
│
├── product_attributes        # Shared catalogs
│   ├── brands                # Nike, Adidas, etc.
│   ├── categories            # Shoes, Clothing, etc.
│   ├── colors                # Red, Blue, etc.
│   ├── conditions            # New, Used, etc.
│   └── [35+ attribute tables]
│
├── user_1                    # Tenant 1 data
│   ├── products              # User's products
│   ├── vinted_products       # Marketplace listings
│   ├── marketplace_jobs      # Job queue
│   └── [10+ tables]
│
├── user_2                    # Tenant 2 data
└── template_tenant           # Blueprint for new users
```

### Isolation Mechanism

**Per-Request Schema Switching**:
```python
# In backend/api/dependencies.py
@contextmanager
def get_user_db(current_user: User):
    """Set search_path to user schema for isolation."""
    db = SessionLocal()
    try:
        # Critical: SET LOCAL (transaction-scoped)
        db.execute(text(f"SET LOCAL search_path TO user_{current_user.id}, public"))
        yield db, current_user
    finally:
        db.close()
```

**Security**: Each request sees only its own schema + shared public data.

**Scalability**: Works well up to ~1000 tenants. Beyond that, consider Citus or tenant_id column approach.

## Authentication & Authorization

### JWT Authentication (RS256)

**Token Flow**:
```
1. User logs in → Backend validates credentials
2. Backend generates:
   - Access Token (15 min, RS256)
   - Refresh Token (7 days, stored in DB)
3. Frontend stores in localStorage
4. Every API request includes: Authorization: Bearer <access_token>
5. Backend validates JWT signature + expiry
6. If expired, use refresh token to get new access token
```

**Security Features**:
- **RS256 algorithm** - Asymmetric keys prevent token forgery
- **Short-lived access tokens** - Limit attack window
- **Refresh token rotation** - Planned (currently TODO)
- **Token blacklist** - For logout/revoke
- **Encryption key rotation** - Previous key stored for migration

### OAuth2 (Marketplace Integrations)

**eBay & Etsy OAuth Flow**:
```
1. User clicks "Connect eBay"
2. Frontend redirects to eBay OAuth authorize URL
3. User grants permissions
4. eBay redirects back with authorization_code
5. Backend exchanges code for access_token + refresh_token
6. Tokens stored ENCRYPTED in database (Fernet)
7. Auto-refresh before expiry
```

**Token Storage**: `ebay_credentials.access_token` encrypted at rest using `shared/encryption.py`

## Data Flow Patterns

### Product Publishing Flow

**Unified Marketplace Job System** (2026-01-09):
```
User → Frontend → Backend API → MarketplaceJobProcessor
                                        ↓
                    ┌───────────────────┴───────────────────┐
                    │                                       │
         ┌──────────▼─────────┐              ┌─────────────▼──────────┐
         │  Vinted Handler    │              │  eBay Handler          │
         │  (via WebSocket)   │              │  (Direct HTTP API)     │
         └──────────┬─────────┘              └─────────────┬──────────┘
                    │                                      │
         ┌──────────▼─────────┐              ┌─────────────▼──────────┐
         │  Plugin (Browser)  │              │  eBay Commerce API     │
         │  → Vinted API      │              │  (OAuth2 authenticated)│
         └────────────────────┘              └────────────────────────┘
```

**Job Lifecycle**:
1. User clicks "Publish to Vinted"
2. Backend creates `MarketplaceJob` (status: pending)
3. `MarketplaceJobProcessor.process_next_job()` picks it up
4. Dispatches to `VintedPublishJobHandler`
5. Handler sends WebSocket command to plugin
6. Plugin executes Vinted API call
7. Result sent back via WebSocket
8. Job status updated (completed/failed)
9. Frontend shows notification

### Real-Time Communication (WebSocket)

**Socket.IO Architecture**:
```
Backend (Socket.IO Server)
    ├─ Namespace: /
    ├─ Events emitted:
    │   - execute_job (command to plugin)
    │   - job_status_update (to frontend)
    │   - vinted_connection_status
    │
    └─ Events received:
        - job_result (from plugin via frontend)
        - vinted_session_update
        - datadome_detected
```

**Connection Management**:
- CORS origins: localhost:3000-3003, app.stoflow.com
- Timeout: 60 seconds
- Auto-reconnect in frontend (useWebSocket composable)

## External Integrations

### Vinted Integration (Browser Extension)

**Why Browser Extension**: Vinted has no public API, requires session-based authentication.

**Architecture**:
```
StoFlow Backend (MarketplaceJobProcessor)
       │ WebSocket (Socket.IO)
       ▼
StoFlow Frontend (Nuxt.js useVintedBridge)
       │ chrome.runtime.sendMessage
       ▼
Browser Extension (Content Script)
       │ Inject into vinted.fr
       ▼
Vinted API (intercept fetch/XHR)
```

**Security**:
- Extension only accepts messages from stoflow.io
- Session tokens stored in chrome.storage (encrypted by browser)
- No remote code execution (Manifest V3)

### eBay Integration (Direct OAuth2)

**API Clients**:
- `EbayInventoryClient` - Manage inventory items
- `EbayOfferClient` - Create/update listings
- `EbayFulfillmentClient` - Order management
- `EbayTaxonomyClient` - Category mapping
- `EbayAnalyticsClient` - Performance metrics

**Rate Limiting**: Handled by eBay (5000 calls/day for production app)

### Etsy Integration (Direct OAuth2)

**Status**: Implemented but temporarily disabled pending `PlatformMapping` model.

**API Clients**:
- `EtsyListingClient` - Manage listings
- `EtsyReceiptClient` - Order synchronization
- `EtsyShopClient` - Shop configuration
- `EtsyPollingService` - Periodic order polling (APScheduler)

## Job Processing System

### Unified MarketplaceJobProcessor

**Design** (Refactored 2026-01-09):
```python
class MarketplaceJobProcessor:
    """Process jobs for all marketplaces."""

    VINTED_HANDLERS = {
        'publish': VintedPublishJobHandler,
        'update': VintedUpdateJobHandler,
        'delete': VintedDeleteJobHandler,
        'sync': VintedSyncJobHandler,
        'orders': VintedOrdersJobHandler,
        'message': VintedMessageJobHandler,
        'link': VintedLinkProductJobHandler,
    }

    EBAY_HANDLERS = {
        'publish': EbayPublishJobHandler,
        'update': EbayUpdateJobHandler,
        'delete': EbayDeleteJobHandler,
        'sync': EbaySyncJobHandler,
        'sync_orders': EbaySyncOrdersJobHandler,
    }

    def process_next_job(self) -> dict:
        """Pick highest priority job and process."""
        job = self.get_next_pending_job()
        handler_class = self.get_handler(job.platform, job.action)
        handler = handler_class(self.db, self.user_id)
        result = handler.execute(job)
        return result
```

**Priority System**: Jobs processed in order of creation (FIFO), with status filtering (pending first).

## State Management

### Backend State

**Session Management**:
- SQLAlchemy sessions via `SessionLocal()` factory
- Per-request session with `get_db()` dependency
- Multi-tenant via `SET LOCAL search_path`

**Caching**:
- AI-generated descriptions cached for 30 days
- No distributed cache (Redis) yet - room for optimization

### Frontend State (Pinia)

**Stores**:
- `authStore` - User authentication, JWT tokens
- `productsStore` - Product listing cache
- `vintedStore` - Vinted connection status
- `ebayStore` - eBay connection status
- `publicationsStore` - Publication history

**Persistence**: localStorage for auth tokens only.

## Security Architecture

### Request Security Flow

```
1. Client Request
   ↓
2. CORS Middleware (check origin)
   ↓
3. Rate Limiting Middleware (check IP)
   ↓
4. JWT Validation (verify signature + expiry)
   ↓
5. RBAC Check (verify user role/permissions)
   ↓
6. Multi-Tenant Isolation (SET LOCAL search_path)
   ↓
7. Business Logic Execution
   ↓
8. Security Headers Middleware (add CSP, HSTS, etc.)
   ↓
9. Response
```

### Input Validation

**Backend**:
- Pydantic schemas validate all inputs
- SQLAlchemy parameterized queries (no SQL injection)
- Custom validators in `shared/validators.py`

**Frontend**:
- DOMPurify sanitizes HTML (XSS prevention)
- TypeScript type checking
- Form validation via PrimeVue validators

## Deployment Architecture

### Development

**4 Parallel Environments** (git worktrees):
```
~/StoFlow/           → develop branch (ports 8000/3000)
~/StoFlow-env2/      → feature branch (ports 8001/3001)
~/StoFlow-env3/      → feature branch (ports 8002/3002)
~/StoFlow-env4/      → feature branch (ports 8003/3003)
```

**Benefits**:
- Work on multiple features simultaneously
- No branch switching overhead
- Shared .venv via symlinks

### Production

| Component | Platform | Auto-Deploy |
|-----------|----------|-------------|
| Frontend | Vercel | ✅ (from `prod` branch) |
| Backend | Railway | ✅ (from `prod` branch) |
| Database | Railway PostgreSQL | Managed service |
| Storage | Cloudflare R2 | CDN integrated |
| Extension | Chrome Web Store | Manual upload |

**Git Flow**: `feature/* → develop → prod`

## Performance Patterns

### Database Optimization

- **Connection pooling** via SQLAlchemy (pool_size=5, max_overflow=10)
- **Schema-per-tenant** reduces query complexity
- **Indexes** on frequently queried columns (created_at, foreign keys)
- **Soft deletes** via `deleted_at IS NOT NULL`

### Frontend Optimization

- **Code splitting** via Nuxt auto-imports
- **Lazy loading** for routes and components
- **Image optimization** via Cloudflare R2 CDN
- **SSR/SSG** for SEO (Nuxt capability)

## Error Handling Architecture

### Custom Exception Hierarchy

```
StoflowError (Base)
├── DatabaseError
│   └── SchemaCreationError
├── APIError
│   ├── APIConnectionError
│   └── APITimeoutError
└── MarketplaceError
    ├── VintedError
    ├── EbayError
    └── EtsyError
```

**Propagation**:
1. Service raises custom exception
2. Route catches and converts to HTTPException
3. Frontend receives structured error response
4. Display user-friendly message

## Scalability Considerations

**Current Capacity**: ~1000 tenants with schema-per-tenant approach.

**Bottlenecks**:
- Migration fan-out (must update all user_X schemas)
- PostgreSQL connection limit (~100 concurrent)
- WebSocket connection pool (not currently limited)

**Future Scaling Paths**:
- **Citus** for distributed PostgreSQL (shard by user_id)
- **Read replicas** for analytics queries
- **Redis** for caching + session storage
- **Message queue** (Celery/RabbitMQ) for job processing

---
*Last updated: 2026-01-09 after codebase mapping*
