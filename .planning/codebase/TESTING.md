# Testing Practices

## Testing Philosophy

**Coverage Focus**: Business logic > API endpoints > UI components

**Test Pyramid**:
```
        ▲
       / \
      /E2E\      (Few - expensive, slow)
     /─────\
    /Integr\     (Some - moderate cost/speed)
   /────────\
  /   Unit   \   (Many - cheap, fast)
 /────────────\
```

## Backend Testing (Pytest)

### Test Organization

```
backend/tests/
├── conftest.py                  # Global fixtures
├── unit/
│   ├── conftest.py             # Unit-specific fixtures
│   ├── services/
│   │   ├── test_product_service.py
│   │   ├── test_pricing_service.py
│   │   ├── test_auth_service.py
│   │   └── ...
│   ├── repositories/
│   ├── schemas/
│   └── models/
└── integration/
    ├── api/
    │   ├── test_products.py
    │   ├── test_auth.py
    │   ├── test_vinted_api.py
    │   └── ...
    ├── database/
    └── security/
        └── test_jwt_validation.py
```

### Test Database Setup

**Configuration**:
- **Database**: PostgreSQL (Docker container)
- **URL**: `postgresql://stoflow_test:test_password_123@localhost:5434/stoflow_test`
- **Port**: 5434 (separate from dev on 5433)
- **Schemas**: `user_1`, `user_2`, `user_3` for multi-tenant tests
- **Isolation**: Transaction rollback between tests

**Setup** in `conftest.py`:
```python
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Apply Alembic migrations and create test schemas."""
    # Run migrations
    alembic.command.upgrade(alembic_cfg, "head")
    
    # Create test user schemas
    engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
    with engine.connect() as conn:
        for user_id in [1, 2, 3]:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS user_{user_id}"))
            # Clone from template_tenant
    
    yield
    
    # Teardown (optional - keep for debugging)
```

### Pytest Fixtures

**Database Session**:
```python
@pytest.fixture
def db_session():
    """Provide a test database session with rollback."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()  # Rollback changes after test
        db.close()
```

**Mock User**:
```python
@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        id=1,
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.USER
    )
    db_session.add(user)
    db_session.commit()
    return user
```

**Authenticated Client**:
```python
@pytest.fixture
def auth_headers(test_user):
    """Generate JWT token for authenticated requests."""
    access_token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}
```

### Naming Conventions

**Test functions**:
```python
# Pattern: test_<action>_<condition>_<result>

def test_create_product_with_valid_data():
    """Test successful product creation."""
    pass

def test_create_product_raises_error_on_missing_title():
    """Test validation error for missing title."""
    pass

def test_calculate_price_with_rarity_coefficient():
    """Test pricing with Rare item (1.3x multiplier)."""
    pass
```

### Mocking Strategies

**Database Mocks**:
```python
from unittest.mock import MagicMock, Mock

@pytest.fixture
def mock_db():
    """Mock database session."""
    session = MagicMock()
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    return session
```

**External API Mocks**:
```python
@patch('services.vinted.vinted_adapter.httpx.AsyncClient.post')
def test_publish_to_vinted_success(mock_post):
    """Test successful Vinted publish."""
    mock_post.return_value.json.return_value = {"id": 12345}
    mock_post.return_value.status_code = 201
    
    result = vinted_adapter.publish_product(product_data)
    assert result["id"] == 12345
```

### Running Tests

**Commands**:
```bash
# Run all tests
pytest

# Run specific module
pytest tests/unit/services/test_pricing_service.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run in parallel
pytest -n auto

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

**Coverage Goals**:
- **Services**: 80%+ (business logic)
- **Repositories**: 70%+
- **API Routes**: 60%+ (integration tests)
- **Overall**: Target 70%+

## Frontend Testing (Vitest)

### Test Organization

```
frontend/tests/
├── unit/
│   ├── composables/
│   │   ├── useAuth.spec.ts
│   │   ├── useProducts.spec.ts
│   │   └── useAttributes.spec.ts
│   ├── components/
│   │   ├── ProductCard.spec.ts
│   │   └── DashboardSidebar.spec.ts
│   ├── stores/
│   │   └── auth.spec.ts
│   └── utils/
│       └── formatters.spec.ts
├── integration/
│   └── (future E2E tests)
└── security/
    └── jwt-validation.spec.ts
```

### Vitest Configuration

**Setup** in `vitest.config.ts`:
```typescript
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'happy-dom',  // DOM simulation
    setupFiles: './tests/setup.ts'
  }
})
```

### Component Testing

**Example**:
```typescript
import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ProductCard from '~/components/products/ProductCard.vue'

describe('ProductCard', () => {
  it('renders product title and price', () => {
    const wrapper = mount(ProductCard, {
      props: {
        product: {
          id: 1,
          title: 'Test Product',
          price: 29.99,
          status: 'draft'
        }
      }
    })
    
    expect(wrapper.text()).toContain('Test Product')
    expect(wrapper.text()).toContain('€29.99')
  })
  
  it('emits select event on click', async () => {
    const wrapper = mount(ProductCard, {
      props: { product: mockProduct }
    })
    
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('select')).toBeTruthy()
  })
})
```

### Composable Testing

**Example**:
```typescript
import { describe, it, expect, vi } from 'vitest'
import { useProducts } from '~/composables/useProducts'

// Mock $fetch
vi.mock('#app', () => ({
  useRuntimeConfig: () => ({ public: { apiBaseUrl: 'http://localhost:8000' } })
}))

describe('useProducts', () => {
  it('fetches products successfully', async () => {
    const { products, fetchProducts } = useProducts()
    
    // Mock API response
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [
        { id: 1, title: 'Product 1' },
        { id: 2, title: 'Product 2' }
      ]
    })
    
    await fetchProducts()
    expect(products.value).toHaveLength(2)
  })
})
```

### Running Frontend Tests

**Commands**:
```bash
# Run all tests
npm test

# Run in watch mode
npm test -- --watch

# Run with coverage
npm run test:coverage

# Run specific file
npm test -- useAuth.spec.ts
```

## Plugin Testing (Vitest)

### Test Focus
- **Service Worker logic** (background scripts)
- **Content script injection**
- **Message passing** between components
- **API client** communication

### Mock chrome APIs
```typescript
import { describe, it, expect, vi } from 'vitest'

// Mock Chrome APIs
global.chrome = {
  runtime: {
    sendMessage: vi.fn(),
    onMessage: {
      addListener: vi.fn()
    }
  },
  storage: {
    local: {
      get: vi.fn(),
      set: vi.fn()
    }
  }
} as any

describe('VintedActionHandler', () => {
  it('sends message to content script', async () => {
    const handler = new VintedActionHandler()
    await handler.publishProduct(productData)
    
    expect(chrome.runtime.sendMessage).toHaveBeenCalledWith({
      action: 'publish',
      payload: productData
    })
  })
})
```

## Test Data & Fixtures

### Backend Test Data

**Product Fixtures**:
```python
@pytest.fixture
def mock_product():
    return Product(
        id=1,
        user_id=1,
        title="Nike Air Max 90",
        price=Decimal("89.99"),
        brand_id=1,
        category_id=5,
        status=ProductStatus.DRAFT,
        created_at=datetime.utcnow()
    )
```

**Marketplace Job Fixtures**:
```python
@pytest.fixture
def mock_vinted_job():
    return MarketplaceJob(
        id=1,
        user_id=1,
        product_id=1,
        platform="vinted",
        action="publish",
        status="pending",
        priority=1
    )
```

### Frontend Test Data

**Mock API Responses**:
```typescript
export const mockProducts = [
  {
    id: 1,
    title: 'Product 1',
    price: 29.99,
    status: 'draft',
    created_at: '2026-01-01T00:00:00Z'
  },
  {
    id: 2,
    title: 'Product 2',
    price: 49.99,
    status: 'published',
    created_at: '2026-01-02T00:00:00Z'
  }
]
```

## Test Coverage Gaps

### Backend
- ✅ **Well covered**: Services, schemas, auth
- ⚠️ **Partial**: eBay webhook handlers (TODOs present)
- ⚠️ **Partial**: Etsy polling jobs
- ❌ **Missing**: Image synchronization services

### Frontend
- ✅ **Well covered**: Composables (useAuth, useApi)
- ⚠️ **Partial**: Large components (ProductCreate.vue)
- ❌ **Missing**: E2E tests with Playwright
- ❌ **Missing**: WebSocket communication tests

### Plugin
- ❌ **Minimal**: Very limited test coverage
- Priority: Content script injection, message passing

## CI/CD Integration

**GitHub Actions** (Future):
```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Start PostgreSQL
        run: docker-compose -f docker-compose.test.yml up -d
      - name: Run tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
  
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Node.js
        uses: actions/setup-node@v2
      - name: Run tests
        run: |
          cd frontend
          npm install
          npm run test:coverage
```

---
*Last updated: 2026-01-09 after codebase mapping*
