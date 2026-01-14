# Technology Stack

## Core Technologies

### Backend Framework
- **Python 3.12.3** - Latest stable version with enhanced type hints
- **FastAPI 0.115.0** - Modern async web framework with auto-documentation
- **Uvicorn 0.32.0** - ASGI server for production deployment

### Database & ORM
- **PostgreSQL** - Primary RDBMS with multi-tenant schema isolation
- **SQLAlchemy 2.0.35** - ORM with modern `Mapped[T]` type hints
- **Alembic 1.14.0** - Database migrations with versioning
- **psycopg2-binary 2.9.9** - PostgreSQL driver

### Validation & Serialization
- **Pydantic 2.10.1** - Data validation with v2 performance improvements
- **Pydantic-settings 2.6.1** - Environment-based configuration
- **Email-validator 2.3.0** - RFC-compliant email validation

### Authentication & Security
- **python-jose 3.3.0** - JWT token generation/verification (RSA-256)
- **passlib[bcrypt] 1.7.4** - Password hashing (12 rounds)
- **python-dotenv 1.0.1** - Environment variable management

### HTTP & Communication
- **httpx 0.27.2** - Async HTTP client for external API calls
- **requests 2.32.3** - Sync HTTP client (fallback/OAuth2)
- **python-socketio 5.11.0** - WebSocket bidirectional communication (Socket.IO)

### AI & Vision
- **openai 1.54.3** - OpenAI GPT-4 Turbo integration (product descriptions)
- **google-genai >= 1.0.0** - Google Gemini Vision API (image analysis)

### Cloud Storage
- **boto3 1.35.0** - AWS S3 SDK (Cloudflare R2 compatible)

### Utilities
- **Pillow 11.0.0** - Image processing and optimization
- **python-dateutil 2.9.0** - Date/time manipulation
- **APScheduler 3.10.4** - Cron jobs for Etsy polling

### Payments
- **Stripe 11.3.0** - Subscription and AI credits management

### Testing
- **pytest 8.3.4** - Test framework with fixtures
- **pytest-cov 6.0.0** - Code coverage reporting
- **httpx (async)** - Async test client for FastAPI

## Architecture Patterns

### Multi-Tenant Strategy
**Schema-per-tenant** with PostgreSQL:
- `public` - Shared authentication and quotas
- `product_attributes` - Shared reference data (brands, colors, etc.)
- `user_{id}` - Tenant-isolated data (products, jobs, orders)
- `template_tenant` - Blueprint schema cloned for new users

### Database Access
- **Session Management**: `schema_translate_map` for automatic tenant scoping
- **Connection Pooling**: 10 connections with 20 max overflow
- **Pool Pre-Ping**: Automatic dead connection detection

## External Dependencies

### Marketplace APIs
| Service | Type | Protocol | Auth |
|---------|------|----------|------|
| **Vinted** | E-commerce | WebSocket → Browser Plugin | Cookies (v_sid, anon_id) |
| **eBay** | E-commerce | Direct HTTPS | OAuth 2.0 |
| **Etsy** | E-commerce | Direct HTTPS | OAuth 2.0 |

### AI & Vision
| Service | Purpose | Model | Cost |
|---------|---------|-------|------|
| **Google Gemini** | Image attribute extraction | gemini-3-flash-preview | $0.075/M input |
| **OpenAI GPT** | Product descriptions | gpt-4-turbo | Cached 30d |

### Cloud Services
- **Cloudflare R2** - S3-compatible object storage for product images
- **Stripe** - Payment processing for subscriptions
- **Brevo** (optional) - Transactional emails

## Development Tools

### Code Quality
- **black** - Code formatter (PEP 8)
- **isort** - Import sorting
- **flake8** - Linting
- **mypy** - Static type checking

### Database Management
- **Docker Compose** - PostgreSQL + Redis + pgAdmin (optional)
- **Alembic** - Schema versioning and migrations

### Environment
- **.env** - Environment variables (not committed)
- **requirements.txt** - Python dependencies (pinned versions)

## Key Versions & Compatibility

| Technology | Version | Notes |
|------------|---------|-------|
| Python | 3.12.3 | Type hints, match/case, async improvements |
| PostgreSQL | 15+ | JSONB, schemas, concurrent indexes |
| FastAPI | 0.115.0 | WebSocket support, dependency injection |
| SQLAlchemy | 2.0.35 | `Mapped[T]` syntax, async support |
| Pydantic | 2.10.1 | V2 rewrite, 5-50x faster validation |

## Configuration Management

**File**: `shared/config.py` (Pydantic Settings)

Key settings loaded from environment:
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY`, `JWT_ALGORITHM` - Authentication
- `OPENAI_API_KEY`, `GEMINI_API_KEY` - AI services
- `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID` - Cloud storage
- `EBAY_CLIENT_ID`, `ETSY_API_KEY` - Marketplace credentials
- `STRIPE_API_KEY` - Payment processing

## Deployment Architecture

```
FastAPI App (Uvicorn)
    ↓
PostgreSQL (multi-tenant schemas)
    ↓
Cloudflare R2 (image CDN)
    ↓
External APIs (Vinted, eBay, Etsy, AI)
```

**WebSocket Flow**:
```
Backend (Job) → Socket.IO → Frontend (Relay) → Plugin (Browser) → Vinted API
```

---

*Last analyzed: 2026-01-14*
