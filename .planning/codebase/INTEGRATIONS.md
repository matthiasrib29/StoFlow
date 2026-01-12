# External Integrations

## Overview

StoFlow integrates with 3 e-commerce marketplaces, AI services, payment processing, and cloud storage.

```
┌──────────────────────────────────────────────────────┐
│              StoFlow Backend (FastAPI)               │
├──────────────────────────────────────────────────────┤
│  WebSocket ←→ Plugin → Vinted API                    │
│  OAuth2 →  eBay Commerce API                         │
│  OAuth2 →  Etsy API v3                               │
│  HTTP → OpenAI GPT-4                                 │
│  HTTP → Google Gemini Vision                         │
│  HTTP → Stripe                                       │
│  S3 → Cloudflare R2                                  │
│  SMTP → Brevo (email)                                │
└──────────────────────────────────────────────────────┘
```

## Marketplace Integrations

### Vinted

**Integration Method**: Browser Extension (Plugin)

**Why**: Vinted has no public API, requires session-based authentication.

**Architecture**:
```
Backend → WebSocket (Socket.IO) → Frontend → chrome.runtime → Plugin → Vinted API
```

**Authentication**:
- Session cookies stored in browser extension
- Intercepted from user's Vinted.fr session
- Stored in `chrome.storage.local`

**API Operations**:
| Operation | Endpoint | Method |
|-----------|----------|--------|
| List products | `/api/v2/users/{user_id}/items` | GET |
| Create listing | `/api/v2/items` | POST |
| Update listing | `/api/v2/items/{item_id}` | PATCH |
| Delete listing | `/api/v2/items/{item_id}` | DELETE |
| Get conversations | `/api/v2/conversations` | GET |
| Send message | `/api/v2/messages` | POST |
| Get orders | `/api/v2/transactions` | GET |

**Rate Limiting**:
- **Limit**: 40 requests per 2 hours (Vinted anti-bot)
- **Enforcement**: Backend tracks via `plugin_task_rate_limiter.py`
- **Delay**: 20-50 seconds randomized between requests

**DataDome Detection**:
- Vinted uses DataDome anti-bot protection
- Plugin detects DataDome challenges
- Notifies backend via WebSocket event: `datadome_detected`
- Pauses operations until resolved

**Job Handlers** (7 handlers):
```python
services/vinted/jobs/
├── publish_job_handler.py     # Create new listing
├── update_job_handler.py      # Update existing listing
├── delete_job_handler.py      # Remove listing
├── sync_job_handler.py        # Sync inventory status
├── orders_job_handler.py      # Import orders/sales
├── message_job_handler.py     # Handle conversations
└── link_product_job_handler.py # Link product to listing
```

**Client Implementation**:
```python
# backend/services/vinted/vinted_adapter.py
class VintedAdapter:
    """Main Vinted API adapter."""
    
    def __init__(self, user_id: int, session_token: str):
        self.user_id = user_id
        self.session_token = session_token
    
    async def publish_product(self, product_data: dict) -> dict:
        """Send WebSocket command to plugin."""
        command = {
            "action": "publish",
            "payload": product_data
        }
        await websocket_service.emit_to_user(
            self.user_id,
            "execute_vinted_job",
            command
        )
        # Wait for response via WebSocket
        result = await self._wait_for_result(command_id)
        return result
```

### eBay

**Integration Method**: Direct OAuth 2.0

**API Version**: eBay Commerce APIs (REST)

**Authentication Flow**:
```
1. User clicks "Connect eBay"
2. Redirect to eBay authorize URL
3. User grants permissions (7 scopes)
4. eBay redirects with authorization_code
5. Backend exchanges for access_token + refresh_token
6. Tokens stored ENCRYPTED in database
7. Auto-refresh before expiry
```

**OAuth2 Configuration**:
```python
# Production
EBAY_OAUTH_AUTHORIZE_URL = "https://auth.ebay.fr/oauth2/authorize"
EBAY_OAUTH_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"

# Required Scopes
EBAY_SCOPES = [
    "https://api.ebay.com/oauth/api_scope",
    "https://api.ebay.com/oauth/api_scope/sell.marketing.readonly",
    "https://api.ebay.com/oauth/api_scope/sell.marketing",
    "https://api.ebay.com/oauth/api_scope/sell.inventory.readonly",
    "https://api.ebay.com/oauth/api_scope/sell.inventory",
    "https://api.ebay.com/oauth/api_scope/sell.account.readonly",
    "https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly"
]
```

**API Clients**:
| Client | Purpose | Base URL |
|--------|---------|----------|
| EbayInventoryClient | Manage inventory items | `/sell/inventory/v1` |
| EbayOfferClient | Create/update offers | `/sell/inventory/v1` |
| EbayFulfillmentClient | Order management | `/sell/fulfillment/v1` |
| EbayTaxonomyClient | Category mapping | `/commerce/taxonomy/v1` |
| EbayAnalyticsClient | Performance metrics | `/sell/analytics/v1` |
| EbayAccountClient | Policies, settings | `/sell/account/v1` |

**Example API Call**:
```python
# services/ebay/ebay_inventory.py
class EbayInventoryClient:
    async def create_inventory_item(self, sku: str, product_data: dict):
        """Create eBay inventory item."""
        url = f"{self.base_url}/inventory_item/{sku}"
        headers = await self._get_auth_headers()
        
        response = await self.http_client.put(
            url,
            json=product_data,
            headers=headers
        )
        return response.json()
```

**Webhooks** (Partial implementation):
```python
# api/ebay_webhook.py
@router.post("/ebay/webhook/order_created")
async def handle_order_created(event: dict):
    """Handle eBay order creation webhook."""
    # TODO: Process order creation
    pass  # Marked as TODO in code

@router.post("/ebay/webhook/payment_status")
async def handle_payment_status(event: dict):
    """Handle payment status updates."""
    # TODO: Update order payment status
    pass  # Marked as TODO in code
```

**Job Handlers** (5 handlers):
```python
services/ebay/jobs/
├── publish_job_handler.py      # Create listing
├── update_job_handler.py       # Update existing
├── delete_job_handler.py       # End listing
├── sync_job_handler.py         # Sync inventory
└── sync_orders_job_handler.py  # Import orders
```

### Etsy

**Integration Method**: Direct OAuth 2.0

**API Version**: Etsy API v3

**Status**: ⚠️ Temporarily disabled (pending `PlatformMapping` model)

**Authentication Flow**: Similar to eBay (OAuth2 authorization code flow)

**API Clients**:
| Client | Purpose | Base URL |
|--------|---------|----------|
| EtsyListingClient | Manage listings | `/v3/application/shops/{shop_id}/listings` |
| EtsyReceiptClient | Order sync | `/v3/application/shops/{shop_id}/receipts` |
| EtsyShopClient | Shop configuration | `/v3/application/shops/{shop_id}` |
| EtsyTaxonomyClient | Category mapping | `/v3/application/seller-taxonomy` |
| EtsyShippingClient | Shipping profiles | `/v3/application/shops/{shop_id}/shipping-profiles` |

**Polling Service** (APScheduler):
```python
# services/etsy_polling_cron.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', minutes=15)
async def poll_etsy_orders():
    """Poll Etsy for new orders every 15 minutes."""
    # TODO: Implement notification system
    # TODO: Sync orders to database
    pass
```

**Job Handlers** (5 handlers):
```python
services/etsy/jobs/
├── publish_job_handler.py      # Create listing
├── update_job_handler.py       # Update listing
├── delete_job_handler.py       # Remove listing
├── sync_job_handler.py         # Sync inventory
└── sync_orders_job_handler.py  # Import orders
```

## AI/ML Services

### OpenAI GPT-4

**Purpose**: Product description generation

**Model**: `gpt-4-turbo-preview`

**Implementation**:
```python
# services/ai/openai_service.py
class OpenAIService:
    async def generate_description(
        self,
        title: str,
        category: str,
        attributes: dict
    ) -> str:
        """Generate AI product description."""
        prompt = self._build_prompt(title, category, attributes)
        
        response = await openai.ChatCompletion.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a product description writer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
```

**Caching**: Generated descriptions cached for 30 days

**Credit System**:
- Users have AI credit balance
- 1 credit = 1 description generation
- Tracked in `ai_generation_log` table

### Google Gemini Vision

**Purpose**: Image analysis & attribute extraction

**Model**: `gemini-3-flash-preview`

**Use Case**: Extract product attributes from images (brand, category, color, condition)

**Implementation**:
```python
# services/ai/gemini_service.py
class GeminiService:
    async def analyze_product_images(
        self,
        image_urls: List[str],
        max_images: int = 10
    ) -> dict:
        """Analyze product images with Gemini Vision."""
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        images = [self._load_image(url) for url in image_urls[:max_images]]
        
        response = await model.generate_content([
            "Extract product attributes from these images: brand, category, color, condition",
            *images
        ])
        
        return self._parse_response(response.text)
```

## Payment Processing

### Stripe

**Purpose**: Subscription management & AI credit purchases

**API Version**: Stripe API v11.3.0

**Features**:
- Monthly subscriptions (Starter, Pro, Enterprise)
- One-time AI credit packs (500, 1000, 2000 credits)
- Webhook handling for payment events
- Grace period: 3 days for failed payments

**Webhook Events**:
```python
# api/stripe_routes.py
@router.post("/stripe/webhook")
async def handle_stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    event = stripe.Webhook.construct_event(
        payload=await request.body(),
        sig_header=request.headers.get('Stripe-Signature'),
        secret=settings.stripe_webhook_secret
    )
    
    if event['type'] == 'invoice.payment_succeeded':
        await handle_payment_succeeded(event['data']['object'])
    elif event['type'] == 'invoice.payment_failed':
        await handle_payment_failed(event['data']['object'])
    elif event['type'] == 'customer.subscription.deleted':
        await handle_subscription_cancelled(event['data']['object'])
```

**Subscription Tiers**:
| Tier | Price | Products | Marketplaces | AI Credits/mo |
|------|-------|----------|--------------|---------------|
| Starter | €9.99 | 100 | 1 | 50 |
| Pro | €29.99 | 500 | 3 | 200 |
| Enterprise | €99.99 | Unlimited | 3 | 1000 |

## Cloud Storage

### Cloudflare R2

**Purpose**: Product image storage & CDN

**Compatibility**: S3-compatible API (using boto3)

**Configuration**:
```python
# services/r2_service.py
import boto3

class R2Service:
    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name='auto'
        )
        self.bucket = 'stoflow-images'
    
    async def upload_image(self, file_content: bytes, file_name: str) -> str:
        """Upload image to R2 and return CDN URL."""
        self.client.put_object(
            Bucket=self.bucket,
            Key=file_name,
            Body=file_content,
            ContentType='image/jpeg'
        )
        
        # Return public CDN URL
        return f"{settings.r2_public_url}/{file_name}"
```

**CDN**: Cloudflare CDN for fast global distribution

## Email Service

### Brevo (formerly Sendinblue)

**Purpose**: Transactional emails (notifications, confirmations)

**Implementation**:
```python
# services/email_service.py
class EmailService:
    async def send_notification(
        self,
        to_email: str,
        subject: str,
        template: str,
        context: dict
    ):
        """Send email via Brevo API."""
        response = await httpx.post(
            'https://api.brevo.com/v3/smtp/email',
            headers={
                'api-key': settings.brevo_api_key,
                'Content-Type': 'application/json'
            },
            json={
                'sender': {'email': settings.brevo_sender_email},
                'to': [{'email': to_email}],
                'subject': subject,
                'htmlContent': self._render_template(template, context)
            }
        )
        return response.json()
```

## Database

### PostgreSQL 15

**Hosting**: Railway (production), Docker (development)

**Multi-Tenant Architecture**: Schema-per-tenant isolation

**Connection Pooling**:
```python
# shared/database.py
engine = create_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)
```

---
*Last updated: 2026-01-09 after codebase mapping*
