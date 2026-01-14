# Testing Practices

## Test Framework

**Framework**: pytest 8.3.4
**Coverage**: pytest-cov 6.0.0
**Test Database**: Docker Compose (port 5434)

---

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures (session scope)
├── unit/
│   ├── conftest.py               # Unit test fixtures (no DB)
│   ├── services/
│   │   ├── test_product_service.py
│   │   ├── test_auth_service.py
│   │   └── test_pricing_service.py
│   ├── schemas/
│   │   └── test_product_schemas.py
│   └── models/
│       └── test_product_models.py
└── integration/
    ├── api/
    │   ├── test_products.py       # API endpoint tests
    │   ├── test_auth.py
    │   └── test_batches.py
    └── database/
        ├── test_migrations.py
        └── test_validators.py
```

---

## Test Database Setup

### Docker Compose Configuration

**File**: `docker-compose.test.yml`

```yaml
services:
  postgres_test:
    image: postgres:15
    ports:
      - "5434:5432"
    environment:
      POSTGRES_USER: stoflow_test
      POSTGRES_PASSWORD: test_password_123
      POSTGRES_DB: stoflow_test
```

**Connection String**:
```
postgresql://stoflow_test:test_password_123@localhost:5434/stoflow_test
```

**Commands**:
```bash
docker-compose -f docker-compose.test.yml up -d   # Start test DB
pytest                                            # Run all tests
pytest --cov=. --cov-report=html                  # With coverage
```

---

## Fixtures Architecture

### Session-Scope Fixtures (Setup Once)

**File**: `tests/conftest.py`

```python
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Executed ONCE at the beginning of all tests:
    1. Apply Alembic migrations (structure = production)
    2. Create schemas user_1, user_2, user_3 by cloning template_tenant
    3. Cleanup at the end
    """
    # 1. Connect and verify DB
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
    except Exception as e:
        print(f"Cannot connect: {e}")
        sys.exit(1)

    # 2. Apply Alembic migrations
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", SQLALCHEMY_TEST_DATABASE_URL)
    command.upgrade(alembic_cfg, "head")

    # 3. Create user schemas by cloning template_tenant
    with engine.connect() as conn:
        for user_id in [1, 2, 3]:
            schema_name = f"user_{user_id}"
            conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
            conn.execute(text(f"CREATE SCHEMA {schema_name}"))

            # Clone tables dynamically
            result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'template_tenant'
            """))
            for (table_name,) in result:
                conn.execute(text(f"""
                    CREATE TABLE {schema_name}.{table_name}
                    (LIKE template_tenant.{table_name} INCLUDING ALL)
                """))

        conn.commit()

    yield  # Tests run here

    # Cleanup (schemas kept for next test run)
```

### Function-Scope Fixtures (Clean Per Test)

```python
@pytest.fixture(scope="function")
def db_session():
    """Provide clean DB session for each test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function", autouse=True)
def cleanup_data(request):
    """Clean data BEFORE and AFTER each test."""
    _run_cleanup()  # BEFORE

    request.addfinalizer(_run_cleanup)  # AFTER (even if test fails)

    yield
```

### Authentication Fixtures

```python
@pytest.fixture(scope="function")
def test_user(db_session: Session):
    """Create test user (admin@test.com)."""
    quota_free = SubscriptionQuota(
        tier=SubscriptionTier.FREE,
        max_products=30,
        max_platforms=2,
    )
    db_session.add(quota_free)
    db_session.commit()

    password_plain = "securepassword123"
    user = User(
        email="admin@test.com",
        hashed_password=AuthService.hash_password(password_plain),
        full_name="Test Admin",
        role=UserRole.ADMIN,
        subscription_tier=SubscriptionTier.FREE,
        is_active=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user, password_plain


@pytest.fixture(scope="function")
def auth_headers(client: TestClient, test_user):
    """Get Authorization Bearer headers after login."""
    user, password = test_user

    response = client.post(
        "/api/auth/login",
        json={"email": user.email, "password": password}
    )

    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
```

### Data Seeding Fixtures

```python
@pytest.fixture(scope="function")
def seed_attributes(db_session: Session):
    """Seed product_attributes with test data."""
    brands = [
        Brand(name="Levi's"),
        Brand(name="Nike"),
    ]
    for b in brands:
        db_session.merge(b)  # merge avoids duplicates

    categories = [
        Category(name_en="Jeans", name_fr="Jeans"),
        Category(name_en="T-Shirts", name_fr="T-Shirts"),
    ]
    for c in categories:
        db_session.merge(c)

    # ... other attributes

    db_session.commit()
    yield
```

---

## Unit Testing Patterns

### Mocking Dependencies

```python
import pytest
from unittest.mock import Mock, MagicMock, patch

@pytest.fixture
def mock_db():
    """Mock database session."""
    session = MagicMock()
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    session.execute = Mock()
    return session


class TestCreateProduct:
    """Tests for ProductService.create_product."""

    @patch('services.product_service.ProductRepository')
    @patch('services.product_service.PricingService')
    @patch('services.product_service.AttributeValidator')
    def test_create_product_success(
        self,
        mock_validator,
        mock_pricing,
        mock_repo,
        mock_db,
        mock_product_create
    ):
        """Should create a product with all attributes."""
        # Setup mocks
        mock_pricing.calculate_price.return_value = Decimal('49.99')
        mock_repo.create.return_value = Mock(id=1, title="Test")

        # Execute
        result = ProductService.create_product(mock_db, mock_product_create, user_id=1)

        # Assert
        assert result.id == 1
        mock_pricing.calculate_price.assert_called_once()
        mock_repo.create.assert_called_once()


    def test_create_product_raises_on_invalid_category(self, mock_db):
        """Should raise ValueError on invalid category."""
        invalid_product = ProductCreate(
            title="Test",
            description="Test",
            category="INVALID_CATEGORY"
        )

        with pytest.raises(ValueError, match="Category not found"):
            ProductService.create_product(mock_db, invalid_product, user_id=1)
```

---

## Integration Testing Patterns

### API Testing with TestClient

```python
def test_create_product_via_api(client: TestClient, auth_headers, seed_attributes):
    """Test product creation via API endpoint."""
    response = client.post(
        "/api/products/",
        headers=auth_headers,
        json={
            "title": "Test Product",
            "description": "Test description",
            "category": "Jeans",
            "brand": "Levi's",
            "condition": 8,
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] > 0
    assert data["title"] == "Test Product"
    assert data["status"] == "draft"


def test_get_product_list_with_pagination(
    client: TestClient,
    auth_headers,
    test_product
):
    """Test product list API with pagination."""
    response = client.get(
        "/api/products/?page=1&page_size=10",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert "total" in data
    assert "page" in data
    assert "total_pages" in data


def test_unauthorized_access_returns_401(client: TestClient):
    """Test API without auth headers returns 401."""
    response = client.get("/api/products/")

    assert response.status_code == 401
```

### Database Testing

```python
def test_soft_delete_product(db_session: Session, test_product):
    """Test soft delete (deleted_at column)."""
    product = test_product

    # Soft delete
    product.deleted_at = datetime.utcnow()
    db_session.commit()

    # Verify not in active query
    result = db_session.query(Product).filter(
        Product.id == product.id,
        Product.deleted_at.is_(None)
    ).first()

    assert result is None

    # Verify still in database
    result_all = db_session.query(Product).filter(
        Product.id == product.id
    ).first()

    assert result_all is not None
```

---

## Image Testing Fixtures

```python
@pytest.fixture
def test_product_with_images(db_session: Session, test_user):
    """Create product with JSONB image data."""
    from sqlalchemy import text

    user, _ = test_user
    db_session.execute(text(f"SET search_path TO user_{user.id}, public"))

    product = Product(
        title="Test Product",
        description="Test",
        price=25.99,
        images=[
            {
                "url": "https://cdn.example.com/img1.jpg",
                "order": 0,
                "created_at": "2026-01-01T10:00:00Z"
            },
            {
                "url": "https://cdn.example.com/img2.jpg",
                "order": 1,
                "created_at": "2026-01-01T10:01:00Z"
            }
        ]
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    return product


def test_add_image_to_product(db_session: Session, test_product_with_images):
    """Test adding image to JSONB array."""
    product = test_product_with_images

    # Add image
    new_image = {
        "url": "https://cdn.example.com/img3.jpg",
        "order": 2,
        "created_at": datetime.utcnow().isoformat()
    }
    product.images.append(new_image)
    db_session.commit()

    # Verify
    db_session.refresh(product)
    assert len(product.images) == 3
    assert product.images[2]["url"] == "https://cdn.example.com/img3.jpg"


def test_cannot_add_more_than_20_images(db_session: Session, test_product):
    """Test max 20 images constraint."""
    product = test_product

    # Add 20 images
    for i in range(20):
        product.images.append({
            "url": f"https://cdn.example.com/img{i}.jpg",
            "order": i,
            "created_at": datetime.utcnow().isoformat()
        })

    db_session.commit()

    # Try to add 21st
    with pytest.raises(ValueError, match="Maximum 20 images per product"):
        ProductImageService.add_image(db_session, product.id, "https://cdn.example.com/img21.jpg")
```

---

## Marketplace Job Testing

```python
@pytest.fixture
def mock_vinted_job(db_session: Session, test_user):
    """Create mock Vinted job for testing."""
    from models.user.marketplace_job import MarketplaceJob, JobStatus

    user, _ = test_user

    job = MarketplaceJob(
        marketplace="vinted",
        action_code="publish",
        product_id=1,
        user_id=user.id,
        status=JobStatus.PENDING,
        priority=2
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    return job


def test_process_vinted_job(db_session: Session, mock_vinted_job):
    """Test job processing flow."""
    job = mock_vinted_job

    # Process job (mocked)
    job.status = JobStatus.RUNNING
    db_session.commit()

    # Verify status change
    assert job.status == JobStatus.RUNNING

    # Complete job
    job.status = JobStatus.COMPLETED
    db_session.commit()

    assert job.status == JobStatus.COMPLETED
```

---

## Cleanup Function

```python
def _run_cleanup():
    """Clean test data idempotently."""
    cleanup_session = TestingSessionLocal()

    try:
        # 1. Clean user_X schemas
        for user_id in [1, 2, 3]:
            schema = f"user_{user_id}"
            tables_to_truncate = [
                "marketplace_jobs",
                "batch_jobs",
                "vinted_products",
                "products",
            ]
            for table in tables_to_truncate:
                try:
                    cleanup_session.execute(
                        text(f"TRUNCATE TABLE {schema}.{table} RESTART IDENTITY CASCADE")
                    )
                    cleanup_session.commit()
                except Exception:
                    cleanup_session.rollback()

        # 2. Clean public schema
        cleanup_session.execute(text("TRUNCATE TABLE public.ai_credits RESTART IDENTITY CASCADE"))
        cleanup_session.execute(text("TRUNCATE TABLE public.users RESTART IDENTITY CASCADE"))
        cleanup_session.commit()

        # 3. Clean product_attributes (optional)
        cleanup_session.execute(text("TRUNCATE TABLE product_attributes.brands CASCADE"))
        cleanup_session.execute(text("TRUNCATE TABLE product_attributes.categories CASCADE"))
        cleanup_session.commit()

    except Exception as e:
        cleanup_session.rollback()
        logger.error(f"Cleanup error: {e}")
    finally:
        cleanup_session.close()
```

---

## Test Naming Conventions

**Pattern**: `test_<action>_<condition>_<result>`

**Examples**:
```python
test_create_product_with_valid_data()
test_create_product_raises_error_on_invalid_category()
test_get_product_list_with_pagination()
test_update_product_requires_authentication()
test_delete_product_soft_deletes_record()
test_reorder_images_updates_order_field()
```

---

## Coverage Standards

| Component | Minimum Coverage | Current |
|-----------|------------------|---------|
| Services | 70% | - |
| Repositories | 60% | - |
| Models | 50% | - |
| API Routes | 70% | - |
| Overall | 65% | - |

**Run Coverage**:
```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

---

## Test Execution Commands

```bash
# Run all tests
pytest

# Run specific file
pytest tests/unit/services/test_product_service.py

# Run specific test
pytest tests/unit/services/test_product_service.py::test_create_product_success

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run with failed test re-run
pytest --lf  # last failed

# Run parallel (requires pytest-xdist)
pytest -n auto
```

---

## Key Testing Principles

1. **Isolation**: Each test is independent
2. **Idempotence**: Tests can run in any order
3. **Cleanup**: BEFORE and AFTER each test
4. **Real DB**: Integration tests use PostgreSQL Docker
5. **Mocking**: Unit tests mock external dependencies
6. **Fixtures**: Reusable via dependency injection
7. **Assertions**: Explicit, not implicit

---

*Last analyzed: 2026-01-14*
