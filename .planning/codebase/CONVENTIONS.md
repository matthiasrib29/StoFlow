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
