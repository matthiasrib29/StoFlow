# Coding Conventions

## Naming Conventions

### Python Naming

| Element | Convention | Example |
|---------|------------|---------|
| Variables | `snake_case` | `user_id`, `product_data`, `image_url` |
| Functions | `snake_case` | `create_product()`, `get_user_by_id()` |
| Classes | `PascalCase` | `Product`, `ProductService`, `UserRole` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_IMAGES_PER_PRODUCT = 20` |
| Private | `_leading_underscore` | `_validate_image()`, `_build_query()` |
| Modules | `snake_case.py` | `product_service.py`, `auth_service.py` |

### SQLAlchemy 2.0 Patterns

**Model Declaration**:
```python
from sqlalchemy import String, Integer, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from enum import Enum

class ProductStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    SOLD = "sold"
    ARCHIVED = "archived"

class Product(Base):
    __tablename__ = "products"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Required strings
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text)

    # Optional with type union
    price: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2), nullable=True)

    # Enums
    status: Mapped[ProductStatus] = mapped_column(
        SQLEnum(ProductStatus, native_enum=False),
        default=ProductStatus.DRAFT
    )

    # JSONB for structured data
    images: Mapped[list[dict]] = mapped_column(JSONB, default=list)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Foreign keys
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("public.users.id"))

    # Relationships
    brand: Mapped["Brand"] = relationship(back_populates="products")
```

**Type Hints on All Columns**:
- Use `Mapped[T]` for all columns
- Use `T | None` for nullable columns (not `Optional[T]`)
- Use type unions: `str | None`, `int | None`, `Decimal | None`

**Soft Delete Pattern**:
```python
deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

# Always filter soft-deleted records
db.query(Product).filter(Product.deleted_at.is_(None))
```

---

## Pydantic v2 Schemas

### Create/Update/Response Pattern

**Request Schemas** (Create/Update):
```python
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal

class ProductCreate(BaseModel):
    """Schema for creating a product."""

    # Required with validation
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1, max_length=5000)
    category: str = Field(..., max_length=255)
    condition: int = Field(..., ge=0, le=10)

    # Optional with defaults
    price: Decimal | None = Field(None, gt=0, decimal_places=2)
    brand: str | None = Field(None, max_length=100)
    colors: list[str] | None = Field(None, max_length=5)
    materials: list[str] | None = Field(None, max_length=3)

    # Complex validators
    @field_validator('colors')
    @classmethod
    def validate_colors(cls, v):
        if v and len(v) > 5:
            raise ValueError('Maximum 5 colors allowed')
        return v


class ProductUpdate(BaseModel):
    """Schema for updating a product."""

    # All fields optional (partial update)
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = Field(None, min_length=1, max_length=5000)
    price: Decimal | None = Field(None, gt=0)
    colors: list[str] | None = Field(None, max_length=5)

    # Exclude unset fields in dict()
    model_config = {"extra": "forbid"}
```

**Response Schemas** (API Output):
```python
class ProductImageItem(BaseModel):
    """Image object in JSONB array."""
    url: str = Field(..., description="CDN URL")
    order: int = Field(..., ge=0, description="Display order")
    created_at: datetime = Field(..., description="Upload timestamp")


class ProductResponse(BaseModel):
    """Complete product response."""

    id: int
    title: str
    description: str
    price: Decimal | None
    category: str
    brand: str | None
    condition: int | None
    colors: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    images: list[ProductImageItem] = Field(default_factory=list)
    status: ProductStatus
    created_at: datetime
    updated_at: datetime

    # Enable SQLAlchemy → Pydantic conversion
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "title": "Vintage Levi's 501 Jeans",
                "description": "Classic straight-leg jeans...",
                "price": "49.99",
                "category": "Jeans",
                "brand": "Levi's",
                "condition": 8,
                "colors": ["blue"],
                "materials": ["cotton"],
                "images": [
                    {
                        "url": "https://cdn.example.com/img1.jpg",
                        "order": 0,
                        "created_at": "2026-01-01T10:00:00Z"
                    }
                ],
                "status": "draft",
                "created_at": "2026-01-01T10:00:00Z",
                "updated_at": "2026-01-01T10:00:00Z"
            }
        }
    }
```

### Validation Preferences

**Declarative (Preferred)**:
```python
price: Decimal = Field(..., gt=0, decimal_places=2)
name: str = Field(..., min_length=1, max_length=255)
age: int = Field(..., ge=0, le=150)
```

**Field Validator (Complex Logic)**:
```python
@field_validator('colors', mode='after')
@classmethod
def validate_colors_format(cls, v):
    if not all(isinstance(c, str) for c in v):
        raise ValueError('All colors must be strings')
    return v
```

---

## Service Layer Pattern

### Static Methods with Type Hints

```python
class ProductService:
    """Service for product business logic."""

    @staticmethod
    @timed_operation('product_creation', threshold_ms=1000)
    def create_product(
        db: Session,
        product_data: ProductCreate,
        user_id: int
    ) -> Product:
        """
        Create product with business rules.

        Business Rules (Updated 2025-12-09):
        - Auto-incremented ID as unique identifier
        - Price calculated if absent (PricingService)
        - Size adjusted if dim1/dim6 provided

        Args:
            db: SQLAlchemy Session
            product_data: Product data to create
            user_id: User ID (for user_X schema)

        Returns:
            Product: Created product

        Raises:
            ValueError: If FK attribute is invalid
        """
        logger.info(f"Creating product: user_id={user_id}, title={product_data.title[:50]}")

        # 1. Validate & adjust data
        size = ProductUtils.adjust_size(product_data.size_original, product_data.dim1)

        # 2. Call other services if needed
        price = PricingService.calculate_price(db, product_data.brand)

        # 3. Create model instance
        product = Product(
            title=product_data.title,
            description=product_data.description,
            price=price,
            status=ProductStatus.DRAFT,
            stock_quantity=1,
        )

        # 4. Persist
        db.add(product)
        db.commit()
        db.refresh(product)

        logger.info(f"Product created: product_id={product.id}")
        return product
```

**Key Patterns**:
- Static methods for easy testing
- Type hints on all parameters and return values
- Google-style docstrings with business rules
- Logging with context (user_id, product_id)
- Explicit transaction management (commit in service)

---

## Error Handling

### Custom Exception Hierarchy

**File**: `shared/exceptions.py`

```python
class StoflowError(Exception):
    """Base exception for all Stoflow errors."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# Database Errors
class DatabaseError(StoflowError):
    pass


class SchemaCreationError(DatabaseError):
    pass


# API Errors
class APIError(StoflowError):
    pass


class APIConnectionError(APIError):
    pass


class APIRateLimitError(APIError):
    pass


# Marketplace Errors
class MarketplaceError(StoflowError):
    def __init__(
        self,
        message: str,
        platform: str = None,
        operation: str = None,
        status_code: int = None,
        response_body: dict = None,
        details: dict = None
    ):
        super().__init__(message, details=details or {})
        self.platform = platform
        self.operation = operation
        self.status_code = status_code
        self.response_body = response_body

        self.details.update({
            "platform": platform,
            "operation": operation,
            "status_code": status_code,
        })


# Business Logic Errors
class ConcurrentModificationError(StoflowError):
    pass


class ValidationError(StoflowError):
    pass
```

### Conversion to HTTPException

**API Routes**:
```python
@router.post("/", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    user_db: tuple = Depends(get_user_db),
) -> ProductResponse:
    db, current_user = user_db

    try:
        db_product = ProductService.create_product(db, product, current_user.id)
        return db_product
    except ValueError as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ConcurrentModificationError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Concurrent modification detected"
        )
    except StoflowError as e:
        logger.error(f"Business logic error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred"
        )
```

---

## Docstring Standards (Google Style)

### Function Docstrings

```python
def create_product(db: Session, product_data: ProductCreate, user_id: int) -> Product:
    """
    Create a new product with all PostEditFlet features.

    Business Rules (Updated 2025-12-09):
    - Auto-incremented ID as unique identifier (PostgreSQL SERIAL)
    - Price calculated automatically if absent (PricingService)
    - Size adjusted automatically if dim1/dim6 provided (W{dim1}/L{dim6})
    - Auto-create size if missing (vintage unique piece)

    Args:
        db: SQLAlchemy Session
        product_data: Product data to create
        user_id: User ID (for user_X schema)

    Returns:
        Product: Created product with ID assigned

    Raises:
        ValueError: If a FK attribute is invalid (brand, category, condition, etc.)
        DatabaseError: If database operation fails
    """
```

### Class Docstrings

```python
class ProductService:
    """
    Service for product business logic.

    Handles CRUD operations, validation, and orchestration
    of product-related functionality across marketplaces.

    Business rules:
    - Cannot publish with stock_quantity = 0
    - deleted_at IS NOT NULL = soft deleted
    - Max 20 images per product (Vinted constraint)
    """
```

---

## Code Quality Standards

### Type Hints

**Required**:
- All function parameters
- All function return values
- Public class attributes
- Service layer functions

**Optional**:
- Simple internal functions
- Obvious return types (`def is_valid() -> bool`)

### Function Length

**Guidelines**:
- Prefer functions < 50 lines
- Max 100 lines before refactoring
- Break into smaller functions if logic is complex

### File Size

**Thresholds** (from CLAUDE.md):
- **500 lines** - Recommend refactoring
- **Current violations**:
  - `vinted_order_sync.py` - 920 lines
  - `ebay_fulfillment_client.py` - 836 lines
  - `marketplace_job_service.py` - 784 lines
  - `product_service.py` - 713 lines

---

## Import Organization

**Order**:
1. Standard library
2. Third-party packages
3. Local modules

**Example**:
```python
# Standard library
from datetime import datetime
from decimal import Decimal
import os

# Third-party
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

# Local
from models.user.product import Product
from services.product_service import ProductService
from schemas.product import ProductCreate, ProductResponse
from shared.database import get_user_db
from shared.exceptions import ValidationError
```

---

## Logging Standards

### Structured Logging

**File**: `shared/logging_setup.py`

**Levels**:
- `DEBUG` - Development (verbose)
- `INFO` - Production (operations)
- `WARNING` - Potential issues
- `ERROR` - Errors requiring attention
- `CRITICAL` - System failures

**Context**:
```python
logger.info(
    f"Creating product: user_id={user_id}, title={product_data.title[:50]}"
)

logger.error(
    f"Failed to create product: user_id={user_id}, error={str(e)}",
    exc_info=True
)
```

**Never**:
- `print()` statements (use logger)
- Logging sensitive data (passwords, tokens)
- Logging full stack traces in production (use `exc_info=True`)

---

## Database Conventions

### Table Naming

- **Plural**: `products`, `users`, `orders`
- **Snake case**: `product_images`, `marketplace_jobs`
- **Schema prefix**: `user_1.products`, `public.users`

### Column Naming

- **Snake case**: `created_at`, `user_id`, `brand_id`
- **Suffixes**: `_id` for foreign keys, `_at` for timestamps

### Indexes

```python
__table_args__ = (
    Index("idx_user_id_status", "user_id", "status"),
    Index("idx_created_at", "created_at"),
)
```

### Constraints

```python
CheckConstraint("price > 0", name="ck_price_positive"),
UniqueConstraint("external_id", "marketplace", name="uq_external_id"),
ForeignKeyConstraint(["brand_id"], ["public.brands.id"], ondelete="RESTRICT"),
```

---

## Testing Conventions

### Test Naming

**Pattern**: `test_<action>_<condition>_<result>`

```python
def test_create_product_with_valid_data():
    ...

def test_create_product_raises_error_on_duplicate_email():
    ...

def test_get_product_list_with_pagination():
    ...
```

### Fixture Naming

- `db_session` - Database session
- `client` - FastAPI TestClient
- `test_user` - Test user fixture
- `auth_headers` - Authorization headers
- `seed_attributes` - Seed product_attributes data

---

*Last analyzed: 2026-01-14*
