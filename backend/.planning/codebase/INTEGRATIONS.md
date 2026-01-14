# External Integrations

## Marketplace Integrations

### 1. Vinted Integration (WebSocket + Browser Plugin)

**Architecture**: Indirect via browser extension
```
Backend (Job) → WebSocket → Frontend → Plugin (Browser Extension) → Vinted API
```

**Authentication**: Cookie-based (v_sid, anon_id) - No official API
**Communication Protocol**: Socket.IO over WebSocket

**Key Components**:
- `services/websocket_service.py` - Socket.IO server
- `services/plugin_websocket_helper.py` - Async HTTP wrapper
- `services/vinted/` - Business logic (adapter, mapper, converters)
- `services/vinted/jobs/` - 7 job handlers (publish, update, delete, sync, orders, message, link)

**Services**:
- `VintedAdapter` - High-level orchestration
- `VintedImporter` - Import products from Vinted account
- `VintedPublisher` - Create/update listings
- `VintedMapper` - Attribute mapping (category, brand, condition, etc.)
- `VintedProductConverter` - Product → Vinted payload transformation
- `VintedImageDownloader` - Download images from Vinted CDN
- `VintedAttributeExtractor` - Extract attributes using AI vision

**Rate Limiting**: 40 requests per 2 hours, 20-50s random delay between requests
**Retry Logic**: 3 attempts with exponential backoff

**Endpoints Used** (via plugin):
- `POST /api/v2/items` - Create listing
- `PUT /api/v2/items/{id}` - Update listing
- `DELETE /api/v2/items/{id}` - Delete listing
- `GET /api/v2/items` - List products
- `POST /api/v2/photos` - Upload images
- `GET /api/v2/users/{id}/msg_threads` - Conversations
- `GET /api/v2/transactions/sold` - Sales

---

### 2. eBay Integration (Direct OAuth 2.0)

**Architecture**: Direct API access with OAuth 2.0
```
Backend → OAuth 2.0 Token (cached) → eBay API
```

**Authentication**: OAuth 2.0 (App Secret + Refresh Token)
**Base URL**: `https://api.ebay.com` (production) or `https://api.sandbox.ebay.com` (sandbox)

**Key Components**:
- `services/ebay/ebay_base_client.py` - OAuth 2.0 client with token caching
- `services/ebay/` - Service layer (inventory, offers, fulfillment, etc.)
- `services/ebay/jobs/` - 5 job handlers (publish, update, delete, sync, sync_orders)

**Services**:
- `EbayBaseClient` - HTTP client + OAuth2 + token cache (1h56min TTL)
- `EbayInventoryClient` - Inventory Item API (SKU, price, stock)
- `EbayOfferClient` - Offer API (listings, pricing)
- `EbayPublicationService` - Publishing orchestration
- `EbayFulfillmentClient` - Shipping and orders
- `EbayCancellationService` - Order cancellations
- `EbayInquiryService` - Buyer messages
- `EbayRefundService` - Refunds processing
- `EbayMarketingClient` - Promotions
- `EbayAnalyticsClient` - Performance reports

**OAuth 2.0 Scopes**:
- `sell.inventory` - Inventory management
- `sell.account` / `sell.account.readonly` - Account info
- `sell.fulfillment` / `sell.fulfillment.readonly` - Shipping
- `sell.analytics` / `sell.analytics.readonly` - Analytics
- `sell.compliance` - Compliance checks
- `sell.marketing` / `sell.marketing.readonly` - Marketing
- `commerce.catalog.readonly` - Product catalog

**Key APIs Used**:
- `POST /sell/inventory/v1/inventory_item` - Create inventory item
- `POST /sell/inventory/v1/offer` - Create offer
- `PUT /sell/inventory/v1/inventory_item/{sku}` - Update inventory
- `GET /sell/fulfillment/v1/order` - Fetch orders
- `POST /sell/fulfillment/v1/order/{orderId}/shipment` - Ship order
- `GET /sell/compliance/v1/listing_violation` - Compliance violations

**Token Management**: In-memory cache, 1h56min expiration (eBay tokens = 2h)

---

### 3. Etsy Integration (Direct OAuth 2.0)

**Architecture**: Direct API access with polling for orders
```
Backend → OAuth 2.0 Token → Etsy API (OpenAPI v3)
```

**Authentication**: OAuth 2.0 (API Key + Token)
**Base URL**: `https://openapi.etsy.com/v3`

**Key Components**:
- `services/etsy/etsy_base_client.py` - OAuth 2.0 client
- `services/etsy/` - Service layer (shop, listings, receipts)
- `services/etsy/etsy_polling_service.py` - Cron-based sync (APScheduler)
- `services/etsy/jobs/` - 5 job handlers (not fully integrated as of 2026-01-09)

**Services**:
- `EtsyBaseClient` - HTTP client + OAuth2
- `EtsyPublicationService` - Create/update listings
- `EtsyProductConversionService` - Product → Etsy listing format
- `EtsyMapper` - Attribute mapping
- `EtsyPollingService` - Poll for new orders (12h interval)
- `EtsyReceiptClient` - Orders/receipts management

**Polling Strategy**: APScheduler cron job runs every 12 hours to sync orders

**Key APIs Used**:
- `POST /v3/application/shops/{shop_id}/listings` - Create listing
- `PUT /v3/application/listings/{listing_id}` - Update listing
- `GET /v3/application/shops/{shop_id}/receipts` - Fetch orders
- `POST /v3/application/listings/{listing_id}/inventory` - Update stock
- `DELETE /v3/application/listings/{listing_id}` - Delete listing

**Note**: Etsy integration partially implemented (image upload marked TODO)

---

## AI & Vision Services

### Google Gemini Vision API

**Purpose**: Extract product attributes from images (brand, category, color, condition, etc.)

**Model**: `gemini-3-flash-preview` (configurable)
**Base URL**: `https://generativelanguage.googleapis.com`

**Authentication**: API Key

**Pricing (Jan 2026)**:
| Model | Input | Output |
|-------|-------|--------|
| gemini-2.5-flash | $0.075/M tokens | $0.30/M tokens |
| gemini-2.5-pro | $1.25/M tokens | $5.00/M tokens |
| gemini-2.0-flash | $0.10/M tokens | $0.40/M tokens |
| gemini-3-flash-preview | $0.075/M tokens | $0.30/M tokens |

**Flow**:
1. Download image from Cloudflare R2 CDN
2. Base64 encode image
3. Send to Gemini with structured prompt
4. Parse JSON response → extract attributes
5. Log usage in `ai_generation_logs` (tokens, cost)
6. Deduct credits from user account

**Services**:
- `VintedAttributeExtractor` - AI-based attribute extraction
- `AIGenerationLog` (model) - Track usage and costs

---

### OpenAI GPT-4 Turbo

**Purpose**: Generate rich product descriptions

**Model**: `gpt-4-turbo` (configurable)
**Base URL**: `https://api.openai.com/v1`

**Authentication**: API Key

**Caching**: 30-day TTL for similar prompts

**Services**:
- `api/text_generator.py` - Description generation endpoint
- AI credits deducted per generation

---

## Cloud Storage

### Cloudflare R2 (S3-Compatible)

**Purpose**: Product image CDN storage

**Provider**: Cloudflare R2
**Protocol**: S3-compatible (boto3)
**Access**: Public read, authenticated write

**Path Structure**: `{user_id}/products/{product_id}/{uuid}.{ext}`
**URL Format**: `https://r2-public-url/1/products/5/abc123.jpg`

**Services**:
- `services/r2_service.py` - S3 client configuration
- `services/file_service.py` - Upload/download/optimize images

**File Processing**:
1. Validate format (magic bytes: JPEG, PNG, WebP)
2. Check size (max 10MB before optimization)
3. Optimize (90% compression, max 2000px dimension)
4. Upload to R2 with unique UUID filename
5. Return public CDN URL

**Supported Formats**: JPG, JPEG, PNG, WebP
**Max Size**: 10MB (before optimization)

---

## Payment Processing

### Stripe

**Purpose**: Subscription management and AI credits

**Base URL**: `https://api.stripe.com/v1`
**Authentication**: API Key (secret key)

**Services**:
- `public.subscriptions` (model) - Subscription records
- `public.ai_credits` (model) - Credit balance tracking
- `public.ai_credit_packs` (model) - Pricing tiers
- Webhook handling for payment events

**Integration Points**:
- Subscription creation/update
- Credit purchase
- Payment failure handling
- Webhook verification

---

## Database

### PostgreSQL Multi-Tenant

**Connection**: Direct TCP/IP connection via psycopg2
**Pooling**: 10 connections, 20 max overflow
**Schemas**:
- `public` - Shared authentication, subscriptions
- `product_attributes` - Shared reference data (17 tables)
- `user_{id}` - Tenant-isolated data
- `template_tenant` - Blueprint for new users

**Isolation Mechanism**: `schema_translate_map` per session

---

## WebSocket Communication

### Socket.IO Server

**Purpose**: Real-time bidirectional communication with frontend/plugin

**Protocol**: Socket.IO over WebSocket (with polling fallback)
**Port**: Same as FastAPI (embedded)
**Library**: `python-socketio 5.11.0`

**Events**:
- `plugin:http:request` - Backend → Plugin command
- `plugin:http:response` - Plugin → Backend response
- `connect` / `disconnect` - Connection lifecycle
- Room-based routing: `user_{id}`

**Timeout**: 60s per request (configurable)
**Reconnection**: Automatic with exponential backoff (1-5s)

**Integration**: Wrapped with FastAPI via ASGIApp (lines 148-155 in `main.py`)

---

## Email (Optional)

### Brevo (formerly Sendinblue)

**Purpose**: Transactional emails (optional)

**Base URL**: `https://api.brevo.com/v3`
**Authentication**: API Key

**Use Cases** (when configured):
- Welcome emails
- Password reset
- Order notifications
- Account notifications

---

## Summary: Integration Patterns

| Integration | Type | Auth | Communication | Retry | Rate Limit |
|-------------|------|------|---------------|-------|------------|
| **Vinted** | Indirect | Cookies | WebSocket → Plugin | 3x exponential | 40/2h |
| **eBay** | Direct | OAuth 2.0 | HTTPS | Per API | Per endpoint |
| **Etsy** | Direct | OAuth 2.0 | HTTPS + Polling | Per API | Per endpoint |
| **Gemini** | Direct | API Key | HTTPS | 1x | Usage-based |
| **OpenAI** | Direct | API Key | HTTPS | Default | Usage-based |
| **R2** | Direct | AWS Keys | HTTPS (S3) | boto3 default | No limit |
| **Stripe** | Direct | API Key | HTTPS | Webhook | No limit |

---

*Last analyzed: 2026-01-14*
