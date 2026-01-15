# Code Conventions

## Language & Communication

| Context | Language |
|---------|----------|
| Responses & explanations | French |
| Code & comments | English |
| Variable/function names | English |
| Git commits | English (Conventional Commits) |
| Documentation | English |

## Python Conventions (Backend)

### Naming
- **Variables & functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: `_leading_underscore`

### Type Hints
- **Required**: Public service functions
- **Optional**: Simple internal functions
- **Flexible**: Use when it helps understanding

```python
def create_product(db: Session, product_data: ProductCreate) -> Product:
    """Public service function - type hints required."""
    pass

def _internal_helper(value):
    """Simple internal - type hints optional."""
    pass
```

### Docstrings (Google Style)
```python
def calculate_price(brand: str, category: str) -> Decimal:
    """
    Calculate product price with coefficients.
    
    Business Rules:
    - Base price from database or default (€30)
    - Rarity coefficient (Rare: 1.3x, Vintage: 1.2x)
    - Quality coefficient (Premium: 1.2x, Good: 1.0x)
    
    Args:
        brand: Brand name
        category: Product category
    
    Returns:
        Calculated price rounded to 2 decimals
    
    Raises:
        ValueError: If brand/category invalid
    """
```

### Import Organization
```python
# 1. Standard library
from datetime import datetime
from decimal import Decimal

# 2. Third-party
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# 3. Local modules
from models.user.product import Product
from services.product_service import ProductService
from shared.exceptions import StoflowError
```

### Logging
```python
from shared.logging_setup import get_logger

logger = get_logger(__name__)

# Include context in logs
logger.info(
    f"Creating product: user_id={user_id}, "
    f"title={title[:50]}, category={category}"
)
logger.error(f"Failed to publish: {e}", exc_info=True)
```

### Error Handling
```python
# Use custom exception hierarchy
class StoflowError(Exception):
    """Base exception."""
    pass

class MarketplaceError(StoflowError):
    """Marketplace-specific errors."""
    def __init__(self, message, platform=None, operation=None):
        super().__init__(message)
        self.platform = platform
        self.operation = operation

# Never use bare except:
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise
except Exception as e:
    logger.exception("Unexpected error")
    raise
```

## TypeScript Conventions (Frontend)

### Naming
- **Components**: `PascalCase.vue` → `<ProductCard>`
- **Composables**: `camelCase.ts` with `use*` → `useProducts()`
- **Variables/functions**: `camelCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Types/Interfaces**: `PascalCase`

### Component Structure
```vue
<script setup lang="ts">
// 1. Imports
import { ref, computed, onMounted } from 'vue'
import type { Product } from '~/types/models'

// 2. Props & Emits (typed)
defineProps<{
  products: Product[]
  loading: boolean
}>()

defineEmits<{
  select: [product: Product]
  close: []
}>()

// 3. Reactive state
const selectedId = ref<number | null>(null)

// 4. Computed properties
const filteredProducts = computed(() => {
  // ...
})

// 5. Methods
const handleSelect = (id: number) => {
  selectedId.value = id
}

// 6. Lifecycle hooks
onMounted(() => {
  // ...
})
</script>

<template>
  <!-- Simple expressions, complex logic in computed -->
</template>

<style scoped>
/* Component-specific styles */
</style>
```

### Composable Pattern
```typescript
export function useProducts() {
  const products = ref<Product[]>([])
  const loading = ref(false)
  
  const fetchProducts = async () => {
    try {
      loading.value = true
      const data = await $fetch('/api/products')
      products.value = data
    } catch (error) {
      console.error('Failed to fetch products:', error)
    } finally {
      loading.value = false
    }
  }
  
  onUnmounted(() => {
    // Cleanup
  })
  
  return {
    products: readonly(products),
    loading: readonly(loading),
    fetchProducts
  }
}
```

### Type Definitions
```typescript
// Use interfaces for object shapes
interface Product {
  id: number
  title: string
  price: number
  status: ProductStatus
}

// Use type for unions/aliases
type ProductStatus = 'draft' | 'published' | 'sold' | 'archived'

// Generics for reusable types
interface ApiResponse<T> {
  data: T
  success: boolean
  message?: string
}
```

## Code Style & Formatting

### Python (Black + isort)
```bash
black .              # Format with 88 char line length
isort .              # Sort imports
```

Configuration in `pyproject.toml`:
```toml
[tool.black]
line-length = 88
target-version = ['py311']

[tool.isort]
profile = "black"
```

### TypeScript/JavaScript (Prettier + ESLint)
```bash
npm run lint         # ESLint
npm run lint:fix     # Auto-fix
```

Configuration in `.prettierrc`:
```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5"
}
```

## Git Commit Conventions

**Format**: Conventional Commits
```
<type>: <description>

[optional body]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Add/update tests
- `chore`: Maintenance (deps, config)

**Examples**:
```
feat: add pricing algorithm with rarity coefficients

fix: resolve multi-tenant schema isolation issue

docs: update API documentation for eBay integration

refactor: extract validation logic to service layer

test: add unit tests for pricing service
```

**Rules**:
- Messages in **English**
- Max 3 files per commit (when possible)
- Atomic commits (one logical change)
- Never commit secrets/credentials
- Co-authored by Claude: `Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>`

## Database Conventions

### Table Naming
- **Plural**: `users`, `products`, `marketplace_jobs`
- **Timestamps**: All tables have `created_at`, `updated_at`
- **Soft delete**: `deleted_at IS NOT NULL` for archiving
- **Indexes**: On FK, created_at, frequently queried columns

### Column Naming
- **snake_case**: `user_id`, `created_at`, `is_active`
- **Foreign keys**: `<table>_id` (e.g., `brand_id`, `category_id`)
- **Booleans**: `is_*`, `has_*`, `can_*`

### Constraints
- **NOT NULL**: For required fields
- **Foreign keys**: With `ondelete` specified (CASCADE, SET NULL, RESTRICT)
- **Check constraints**: For business rules
- **Unique constraints**: Where needed

## Image Handling Patterns

> **Context**: Migrated from JSONB to `product_images` table (2026-01-15)

### Overview

Product images are stored in the `product_images` table with rich metadata support. The `is_label` flag distinguishes internal price tag labels from marketplace-publishable photos.

**Service Layer**: `ProductImageService` (business logic) → `ProductImageRepository` (data access)

### Adding Images

Always use `ProductImageService.add_image()` - handles auto-ordering and validation:

```python
from services.product_image_service import ProductImageService

service = ProductImageService(db)

# Add a product photo
image_data = service.add_image(
    product_id=123,
    url="https://cdn.stoflow.com/products/abc123.jpg",
    is_label=False,
    alt_text="Red Nike sneakers front view",
    mime_type="image/jpeg",
    file_size=245678,
    width=1200,
    height=800
)

# Add a label (internal price tag)
label_data = service.add_image(
    product_id=123,
    url="https://cdn.stoflow.com/labels/xyz789.jpg",
    is_label=True,
    alt_text="Internal price label"
)
```

**Business Rules Enforced**:
- Max 20 images per product (raises `TooManyImagesError`)
- Auto-assigns `order` (increments from max existing order)
- Validates product exists

### Retrieving Images

Use the appropriate method based on your use case:

```python
# Get only photos (exclude labels) - for marketplace publishing
photos = service.get_product_photos(product_id=123)
# Returns: [{"id": 1, "url": "...", "order": 0, "is_label": False, ...}, ...]

# Get all images (photos + label)
all_images = service.get_images(product_id=123)
# Returns: [{"id": 1, "url": "...", "order": 0, ...}, {"id": 2, "url": "...", "order": 1, "is_label": True, ...}]

# Get only the label
label = service.get_label_image(product_id=123)
# Returns: {"id": 2, "url": "...", "is_label": True, ...} or None
```

**Sorting**: All methods return images sorted by `order` ASC.

### Label Flag Usage

**Purpose**: Distinguish internal price tags from marketplace-publishable images.

**Business Rules**:
- Only **one label per product** (enforced in `set_label_flag()`)
- Setting `is_label=True` on image A automatically unsets existing label B
- Labels are **excluded** from marketplace uploads (Vinted, eBay)

**Example - Toggle Label Flag**:

```python
# Mark image as label (unsets previous label if exists)
service.set_label_flag(product_id=123, image_id=456, is_label=True)

# Unmark image as label
service.set_label_flag(product_id=123, image_id=456, is_label=False)
```

**Marketplace Behavior**:
- **Vinted**: `upload_product_images()` uses `get_product_photos()` → labels excluded
- **eBay**: `_get_image_urls()` uses `get_product_photos()` → labels excluded
- **Frontend**: Display all images, highlight label with badge

**Migration Note**: During the 2026-01-15 migration, the last image (max order) was automatically marked as `is_label=True` for all products (pythonApiWOO pattern).

### Image Ordering

Images use 0-indexed ordering for display sequence:

```python
# Manual reordering
service.reorder_images(
    product_id=123,
    image_order=[
        {"id": 3, "order": 0},  # Move image 3 to first position
        {"id": 1, "order": 1},  # Move image 1 to second position
        {"id": 2, "order": 2}   # Move image 2 to third position
    ]
)
```

**Auto-Reordering**:
- **On add**: New image gets `max(order) + 1`
- **On delete**: Remaining images are renumbered (0, 1, 2, ...)
- **On manual reorder**: Provided order values are applied exactly

**Best Practices**:
- Always provide complete ordering when reordering (don't skip IDs)
- First image (order=0) is the primary product photo
- Label is typically last (max order)

### Metadata Best Practices

Provide rich metadata when adding images:

```python
image_data = service.add_image(
    product_id=123,
    url="https://cdn.stoflow.com/products/shoe.jpg",
    is_label=False,

    # Accessibility & SEO
    alt_text="Red Nike Air Max 90 sneakers - front view",

    # File metadata (from R2 upload response)
    mime_type="image/jpeg",  # or "image/png", "image/webp"
    file_size=245678,        # bytes
    width=1200,              # pixels
    height=800,              # pixels

    # Optional tagging (not widely used yet)
    tags=["front-view", "red", "sneakers"]
)
```

**Why Metadata Matters**:
- `alt_text`: SEO, accessibility, image search
- `mime_type`: Frontend rendering, browser caching
- `file_size`: Storage analytics, optimization candidates
- `width`/`height`: Responsive images, lazy loading
- `tags`: Future search/filtering features

**Minimal Required**:
- `url`: Always required
- `is_label`: Defaults to `False` if omitted
- All other fields optional

### Common Patterns

**Pattern 1: Upload + Add Image**
```python
# 1. Upload to R2 (FileService)
from services.file_service import FileService
file_service = FileService()
upload_result = file_service.upload(file_bytes, "products/shoe.jpg")

# 2. Add to product_images table
image_service = ProductImageService(db)
image_data = image_service.add_image(
    product_id=product.id,
    url=upload_result["url"],
    mime_type=upload_result["mime_type"],
    file_size=upload_result["size"],
    width=upload_result["width"],
    height=upload_result["height"]
)
```

**Pattern 2: Marketplace Publishing**
```python
# Get only photos (exclude label)
photos = image_service.get_product_photos(product.id)

# Vinted/eBay services internally use get_product_photos()
# No need to manually filter is_label=False
```

**Pattern 3: API Response**
```python
# FastAPI endpoint returns all images with metadata
from schemas.product_image_schema import ProductImageItem

images = image_service.get_images(product_id)
# ProductImageItem schema includes: id, url, order, is_label, alt_text, tags,
# mime_type, file_size, width, height, created_at, updated_at
```

### Database Queries (Advanced)

For direct repository access (rare - prefer service layer):

```python
from repositories.product_image_repository import ProductImageRepository

repo = ProductImageRepository(db)

# Get all images (SQLAlchemy models, not dicts)
images = repo.get_by_product_id(product_id=123)  # Returns List[ProductImage]

# Bulk reorder
repo.reorder_bulk(
    product_id=123,
    order_updates=[{"id": 1, "order": 0}, {"id": 2, "order": 1}]
)
```

**When to Use Repository Directly**:
- Custom queries not in service layer
- Performance-critical batch operations
- Advanced SQLAlchemy features (eager loading, etc.)

**Prefer Service Layer**: For standard operations (add, delete, reorder, get).

## API Conventions

### Endpoint Naming
- **Resource-based**: `/api/products`, `/api/products/{id}`
- **Actions**: `/api/products/{id}/publish`
- **Marketplace-specific**: `/api/vinted/jobs`, `/api/ebay/oauth/authorize`

### HTTP Methods
- `GET` - Retrieve resource(s)
- `POST` - Create resource
- `PUT` - Update entire resource
- `PATCH` - Partial update
- `DELETE` - Remove resource

### Response Format
```typescript
// Success
{
  "success": true,
  "data": { ... },
  "message": "Product created successfully"
}

// Error
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Title is required",
    "details": { ... }
  }
}
```

## Function/File Size Guidelines

### Recommended Limits
- **Functions**: Keep under 50 lines when possible
- **Files**: Target 300-500 lines, refactor at 500+
- **Components**: Target 300 lines, refactor at 500+

### Current Large Files (>500 lines)
- `product_service.py` (713) - Needs decomposition
- `marketplace_job_service.py` (784) - Consider splitting
- `validators.py` (628) - Could split by domain

**Philosophy**: Flexible - split when hard to understand, not artificially.

## Documentation Standards

### When to Document
- **Public APIs**: Always document
- **Business logic**: Explain "why", not "what"
- **Complex algorithms**: Provide context
- **NOT for**: Self-explanatory code

### Comment Style
```python
# ===== SECTION HEADER (CAPS) =====

# Inline comment explaining why (not what)
if price < MIN_PRICE:  # Ensure minimum viable price
    price = MIN_PRICE

# Avoid obvious comments
x = x + 1  # ❌ BAD: Increment x
```

---
*Last updated: 2026-01-09 after codebase mapping*
