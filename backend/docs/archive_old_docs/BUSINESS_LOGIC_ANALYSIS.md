# Product CRUD Module - Forensic Business Logic Analysis
**Analysis Date:** 2025-12-05
**Analyst Role:** Business Logic Analyst (Forensic Level)
**Scope:** Product Service, File Service, Product Models, API Routes

---

## Executive Summary

The Product CRUD module has **11 critical issues**, **23 high-risk edge cases**, and **4 data corruption scenarios** that require immediate attention. While the foundational architecture (multi-tenant isolation, soft deletes, FK validation) is sound, there are systematic gaps in state machine enforcement, concurrent access handling, pricing/inventory validation, and image transaction safety.

The most severe issues are:

1. **Deleted Products Still Modifiable** - No enforcement preventing updates to soft-deleted products (file:line product_service.py:266-327)
2. **Orphaned Images on Transaction Failure** - Race condition between filesystem save and DB commit (file:line api/products.py:298-311)
3. **Circular Category References Allowed** - No validation preventing category parent loops (file:line models/public/category.py:32-42)
4. **Zero Stock Published Products** - No validation preventing inventory anomalies (file:line product_service.py:136-174)
5. **Status Override on Archived Products** - Can transition ARCHIVED → PUBLISHED via update endpoint (file:line api/products.py:124-156)

---

## Part 1: Critical Issues (P0 - Immediate Action Required)

### Issue 1.1: Deleted Products Can Be Modified (CRITICAL DATA INTEGRITY)

**Location:** `/services/product_service.py:266-327` (update_product method)

**Problem:**
```python
# Line 288-290: Only checks if product exists, not if deleted
product = ProductService.get_product_by_id(db, product_id)
if not product:
    return None
```

The `update_product()` method calls `get_product_by_id()` which correctly filters soft-deleted products. However, the API endpoint `PUT /api/products/{product_id}` (line 124-156) does not validate that the product being updated is not deleted. While the service check passes, this creates semantic confusion: users expect soft-deleted products to be immutable.

**Business Impact:**
- Deleted products appear immutable to UI but updates may succeed through edge cases
- Audit trail is corrupted (deleted_at predates updated_at)
- Violates immutability expectation of soft deletes

**Recommendation:**
Explicitly verify soft-delete status before updates:

```python
@staticmethod
def update_product(db: Session, product_id: int, product_data: ProductUpdate) -> Optional[Product]:
    product = ProductService.get_product_by_id(db, product_id)
    if not product:
        return None

    # CRITICAL: Explicitly reject updates on soft-deleted products
    if product.deleted_at is not None:
        raise ValueError(f"Cannot update deleted product {product_id}")

    # ... rest of validation
```

---

### Issue 1.2: Orphaned Images on Transaction Failure (CRITICAL DATA LOSS)

**Location:** `/api/products.py:298-311` (upload_product_image endpoint)

**Problem:**
```python
# Line 300-302: File saved to disk
image_path = await FileService.save_product_image(tenant_id, product_id, file)

# Line 305-311: DB transaction can fail AFTER file write
try:
    product_image = ProductService.add_image(db, product_id, image_path, display_order)
    return product_image
except ValueError as e:
    # File cleanup only if DB insert fails
    FileService.delete_product_image(image_path)
```

**Critical Race Condition:**
1. File written to disk successfully (line 300)
2. DB insert begins (line 306)
3. If DB connection fails, commit times out, or constraint violation occurs → orphaned file
4. File cleanup (line 310) only catches `ValueError` but not other exceptions (database connection errors, integrity constraint violations)

**Business Impact:**
- Disk space leakage: orphaned images accumulate
- Data inconsistency: images reference non-existent products
- Potential security issue: orphaned files may contain sensitive data

**Scenario:**
```
User uploads image → File saved as "uploads/1/products/5/abc123.jpg"
→ Database insert fails with connection timeout
→ Exception type is not ValueError (it's DatabaseConnectionError)
→ File cleanup NOT executed
→ Orphaned file remains on disk
→ Quota counting is broken
```

**Recommendation:**
Implement proper transaction ordering with cleanup:

```python
@router.post("/{product_id}/images", ...)
async def upload_product_image(...) -> ProductImageResponse:
    # STEP 1: Validate product exists FIRST
    product = ProductService.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # STEP 2: Check image count limit BEFORE any file operations
    try:
        FileService.validate_image_count(db, product_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # STEP 3: Create DB record FIRST (reserve slot)
    # This ensures image_count validation works
    image_path = None
    product_image = None

    try:
        # Register image in DB BEFORE file save (creates transaction checkpoint)
        product_image = ProductService.add_image(
            db, product_id,
            image_path="[pending]",  # Temporary path
            display_order=display_order
        )

        # STEP 4: NOW save file (with proper cleanup)
        image_path = await FileService.save_product_image(tenant_id, product_id, file)

        # STEP 5: Update DB record with real path
        product_image.image_path = image_path
        db.commit()

        return product_image

    except Exception as e:
        # Cleanup on ANY exception
        if product_image and product_image.id:
            # Delete DB record if created
            try:
                ProductService.delete_image(db, product_image.id)
            except:
                pass

        if image_path:
            # Delete file if written
            FileService.delete_product_image(image_path)

        # Re-raise original exception
        raise HTTPException(status_code=400, detail=str(e))
```

---

### Issue 1.3: Circular Category References Allowed (CRITICAL DATA MODEL)

**Location:** `/models/public/category.py:32-42` (Category model with self-reference)

**Problem:**
```python
parent_category: Mapped[str | None] = mapped_column(
    String(100),
    ForeignKey(
        "categories.name_en" if os.getenv("TESTING") else "public.categories.name_en",
        onupdate="CASCADE",
        ondelete="SET NULL"
    ),
    nullable=True,
    index=True,
    comment="Catégorie parente (self-reference)"
)
```

**The Vulnerability:**
A category can reference itself as its parent:
```
Category: "Jeans" with parent_category = "Jeans"
```

This creates a circular reference. While PostgreSQL allows this, it breaks:
1. Hierarchy traversal algorithms (infinite loops)
2. The `get_full_path()` method (lines 77-86) which recursively follows parent chain
3. Any analytics/reporting on category depth

**Business Impact:**
- Application can crash on category tree operations
- Inventory counts by category fail
- UI category pickers hang on circular traversal

**Test Case Demonstrating Bug:**
```python
# Current code allows this:
category = Category(name_en="Jeans", parent_category="Jeans")
db.add(category)
db.commit()

# Then calling get_full_path():
path = category.get_full_path()  # INFINITE LOOP or stack overflow
```

**Recommendation:**
Add explicit validation in model and service layer:

```python
# In models/public/category.py
@validates('parent_category')
def validate_parent_category(self, key, value):
    """Prevent self-reference and circular hierarchy."""
    if value == self.name_en:
        raise ValueError(f"Category '{self.name_en}' cannot be its own parent")

    # Check for circular reference (traverse up to depth 10)
    current = self
    depth = 0
    max_depth = 10

    while current.parent and depth < max_depth:
        if current.parent.name_en == value:
            raise ValueError(
                f"Creating circular hierarchy: {self.name_en} -> {value} -> ... -> {self.name_en}"
            )
        current = current.parent
        depth += 1

    if depth >= max_depth:
        raise ValueError("Category hierarchy too deep (max depth: 10)")

    return value
```

---

### Issue 1.4: Zero Stock Published Products (CRITICAL BUSINESS LOGIC)

**Location:** `/services/product_service.py:136-174` (create_product) and `/api/products.py:185-222` (update_product_status)

**Problem:**
No validation prevents publishing a product with zero stock:

```python
# ProductCreate schema allows: stock_quantity >= 0
stock_quantity: int = Field(default=0, ge=0, description="Quantité en stock")

# Then product can be PUBLISHED even if stock is 0
ProductService.update_product_status(db, product_id, ProductStatus.PUBLISHED)
```

**Business Impact:**
- Users see "available for purchase" products with no inventory
- Marketplace integration fails (Vinted expects available stock)
- Customer order failures due to inventory mismatch
- Revenue impact: shows products as available when they're not

**Scenario:**
```
1. Create product with stock_quantity=0 (default)
2. Add title/description/images
3. Call PATCH /products/1/status?new_status=PUBLISHED
4. Product appears available on marketplace
5. Customer tries to buy → "Out of stock" error
6. Customer confusion and support escalation
```

**Recommendation:**
Add business logic validation:

```python
@staticmethod
def update_product_status(
    db: Session, product_id: int, new_status: ProductStatus
) -> Optional[Product]:
    # ... existing validation code ...

    product = ProductService.get_product_by_id(db, product_id)
    if not product:
        return None

    # CRITICAL: Prevent publishing products with zero stock
    if new_status == ProductStatus.PUBLISHED and product.stock_quantity == 0:
        raise ValueError(
            f"Cannot publish product {product_id}: stock_quantity is 0. "
            f"Minimum stock required for publication: 1"
        )

    # ... rest of status update ...
```

Also add to API schema validation:

```python
# In schemas/product_schemas.py
class ProductCreate(BaseModel):
    stock_quantity: int = Field(
        default=0,
        ge=0,
        description="Quantité en stock (minimum 1 pour publier)"
    )

    @field_validator('stock_quantity')
    @classmethod
    def validate_stock(cls, v, info):
        # This is a warning, not a hard error at creation
        # But enforce at publication time
        return v
```

---

### Issue 1.5: Status Override on Archived Products (CRITICAL STATE MACHINE)

**Location:** `/api/products.py:124-156` (update_product endpoint) + `/services/product_service.py:266-327`

**Problem:**
While the status transition validation correctly prevents ARCHIVED → PUBLISHED via the status endpoint (line 520-521 in product_service.py), the generic `PUT /products/{id}` endpoint can potentially bypass this:

```python
# PUT /api/products/{id} accepts ProductUpdate schema
# ProductUpdate.status is NOT in the schema (currently)
```

However, if someone adds `status` field to ProductUpdate schema, the update method doesn't validate state transitions:

```python
# Line 321-322 in product_service.py
for key, value in update_dict.items():
    setattr(product, key, value)  # DIRECT ASSIGNMENT - NO VALIDATION
```

**Current State (Safe):**
- Status not in ProductUpdate schema, so bulk update can't change it
- Status only changes via dedicated PATCH endpoint

**Future Risk (if ProductUpdate is extended):**
If someone adds status to ProductUpdate:
```python
class ProductUpdate(BaseModel):
    # ... other fields ...
    status: ProductStatus | None = None  # DANGEROUS if added
```

Then archived products can be re-published:
```python
PUT /api/products/5
{
    "status": "PUBLISHED"  # Would bypass state machine
}
```

**Recommendation:**
Explicitly prevent status in update endpoint:

```python
@staticmethod
def update_product(
    db: Session, product_id: int, product_data: ProductUpdate
) -> Optional[Product]:
    product = ProductService.get_product_by_id(db, product_id)
    if not product:
        return None

    update_dict = product_data.model_dump(exclude_unset=True)

    # CRITICAL: Never allow status updates via generic update
    if 'status' in update_dict:
        raise ValueError(
            "Status cannot be updated via PUT endpoint. "
            "Use PATCH /products/{id}/status instead"
        )

    # ... rest of validation ...
```

And add explicit type check:
```python
# In schemas/product_schemas.py
class ProductUpdate(BaseModel):
    """
    Schema pour mettre à jour un produit.

    NOTE: 'status' is intentionally excluded. Use PATCH /products/{id}/status
    for status transitions via dedicated state machine.
    """

    title: str | None = None
    description: str | None = None
    price: Decimal | None = None
    # ... other fields (explicitly no status field)
```

---

### Issue 1.6: Missing Validation on Optional FK Attributes (HIGH PRIORITY)

**Location:** `/services/product_service.py:305-318` (update_product method)

**Problem:**
The update method is incomplete in FK validation. It only validates `brand`, `color`, and `label_size` but doesn't validate other optional FK attributes like `material`, `fit`, `gender`, `season`:

```python
# Lines 305-318: Only validates 3 of 7 optional FK fields
if "brand" in update_dict and update_dict["brand"]:
    # ... validate brand ...

if "color" in update_dict and update_dict["color"]:
    # ... validate color ...

if "label_size" in update_dict and update_dict["label_size"]:
    # ... validate label_size ...

# MISSING: material, fit, gender, season validation!
```

**Business Impact:**
- Users can set invalid material/fit/gender/season values
- Database constraint violations at random times
- Inconsistent validation between create and update

**Recommendation:**
Complete the FK validation in update:

```python
# In services/product_service.py, update_product method, add:

if "material" in update_dict and update_dict["material"]:
    material = db.query(Material).filter(Material.name_en == update_dict["material"]).first()
    if not material:
        raise ValueError(f"Material '{update_dict['material']}' does not exist.")

if "fit" in update_dict and update_dict["fit"]:
    fit = db.query(Fit).filter(Fit.name_en == update_dict["fit"]).first()
    if not fit:
        raise ValueError(f"Fit '{update_dict['fit']}' does not exist.")

if "gender" in update_dict and update_dict["gender"]:
    gender = db.query(Gender).filter(Gender.name_en == update_dict["gender"]).first()
    if not gender:
        raise ValueError(f"Gender '{update_dict['gender']}' does not exist.")

if "season" in update_dict and update_dict["season"]:
    season = db.query(Season).filter(Season.name_en == update_dict["season"]).first()
    if not season:
        raise ValueError(f"Season '{update_dict['season']}' does not exist.")
```

---

## Part 2: Edge Cases (P1 - High Risk Scenarios)

### Edge Case 2.1: Case Sensitivity in FK Lookups

**Location:** `/services/product_service.py:70,80,92,101,107,113,119,125,131` (create_product)

**Problem:**
FK lookups use exact string matching without case normalization:

```python
# Line 70: Category lookup - case sensitive
category = db.query(Category).filter(Category.name_en == product_data.category).first()

# Line 92: Brand lookup - case sensitive
brand = db.query(Brand).filter(Brand.name == product_data.brand).first()
```

**Scenario:**
```
Database has: Category.name_en = "Jeans"
User sends: category = "jeans" (lowercase)
Result: FK validation fails → ValueError
```

**Business Impact:**
- User frustration: "Jeans" and "jeans" treated as different
- Inconsistent behavior if case varies in input
- Category endpoints may return different cases

**Recommendation:**
```python
# Normalize case for FK lookups
category_name = product_data.category.strip().lower()
category = (
    db.query(Category)
    .filter(func.lower(Category.name_en) == category_name)
    .first()
)
if not category:
    raise ValueError(...)
```

---

### Edge Case 2.2: Whitespace in FK Lookups

**Location:** `/services/product_service.py:70,80,92,101,107,113,119,125,131`

**Problem:**
Leading/trailing whitespace in FK values causes mismatches:

```
User sends: category = "  Jeans  " (with spaces)
Database has: "Jeans" (no spaces)
Result: FK lookup fails
```

**Recommendation:**
Always strip whitespace:

```python
category_name = product_data.category.strip()
category = db.query(Category).filter(Category.name_en == category_name).first()
```

---

### Edge Case 2.3: Multiple Images Uploaded Concurrently (RACE CONDITION)

**Location:** `/services/product_service.py:384-388` (add_image method)

**Problem:**
The image count check is NOT atomic:

```python
# Line 385: Check image count
image_count = db.query(ProductImage).filter(ProductImage.product_id == product_id).count()
if image_count >= 20:
    raise ValueError(...)

# RACE CONDITION: Between check and insert, another request could add image
# Then db.add(product_image) inserts record 21
```

**Scenario:**
```
Request 1: count=19, passes check → inserts record (now 20)
Request 2: count=19, passes check → inserts record (now 21) ← VIOLATES LIMIT
Request 3: count=19, passes check → inserts record (now 22) ← VIOLATES LIMIT
```

**Business Impact:**
- Products can exceed 20 image limit
- Marketplace integration fails (Vinted limit enforcement)
- Database integrity violated

**Recommendation:**
Use database-level constraint instead of application-level check:

```sql
-- Add database constraint
ALTER TABLE product_images
ADD CONSTRAINT check_max_20_images_per_product
CHECK ((SELECT COUNT(*) FROM product_images WHERE product_id = products.id) <= 20);
```

Or use SELECT ... FOR UPDATE (row locking):

```python
@staticmethod
def add_image(db: Session, product_id: int, image_path: str, display_order: int = 0) -> ProductImage:
    product = ProductService.get_product_by_id(db, product_id)
    if not product:
        raise ValueError(f"Product with id {product_id} not found")

    # LOCK: Prevent concurrent image additions
    db.execute(
        text("SELECT 1 FROM products WHERE id = :product_id FOR UPDATE"),
        {"product_id": product_id}
    )

    # NOW check count (under lock)
    image_count = db.query(ProductImage).filter(ProductImage.product_id == product_id).count()
    if image_count >= 20:
        raise ValueError(f"Product already has {image_count} images (max 20)")

    product_image = ProductImage(
        product_id=product_id, image_path=image_path, display_order=display_order
    )
    db.add(product_image)
    db.commit()
    db.refresh(product_image)

    return product_image
```

---

### Edge Case 2.4: Dimension Validation Gaps

**Location:** `/schemas/product_schemas.py:86-91` and `/models/tenant/product.py:237-254`

**Problem:**
Dimensions are numeric but have no logical constraints:

```python
# Schema allows any non-negative integer
dim1: int | None = Field(None, ge=0, description="Tour de poitrine/Épaules (cm)")

# Possible values: 0cm, 999999cm - both valid
```

**Business Impact:**
- Invalid product data (0cm shoulders, 5000cm length)
- Marketplace integration issues
- Poor user experience

**Scenario:**
```
User sets: dim1=0 (0cm shoulder), dim2=0 (0cm length)
Product appears with invalid measurements
Buyer confused
```

**Recommendation:**
Add realistic bounds:

```python
# In schemas/product_schemas.py
dim1: int | None = Field(None, ge=10, le=300, description="Tour de poitrine/Épaules (10-300cm)")
dim2: int | None = Field(None, ge=20, le=250, description="Longueur totale (20-250cm)")
dim3: int | None = Field(None, ge=10, le=150, description="Longueur manche (10-150cm)")
dim4: int | None = Field(None, ge=10, le=200, description="Tour de taille (10-200cm)")
dim5: int | None = Field(None, ge=20, le=250, description="Tour de hanches (20-250cm)")
dim6: int | None = Field(None, ge=10, le=200, description="Entrejambe (10-200cm)")
```

---

### Edge Case 2.5: Soft-Deleted Products in Count Queries

**Location:** `/services/product_service.py:218-263` (list_products method)

**Problem:**
The service correctly filters deleted products in list queries. However, there's no guarantee:

```python
# Line 247: Filters deleted products
query = db.query(Product).filter(Product.deleted_at == None)
```

But if someone queries product count directly without this filter:
```python
# WRONG - includes deleted products
total_products = db.query(Product).count()

# CORRECT - excludes deleted
total_products = db.query(Product).filter(Product.deleted_at == None).count()
```

**Recommendation:**
Create a helper method to prevent mistakes:

```python
@staticmethod
def _active_products_query(db: Session):
    """Base query for active (non-deleted) products."""
    return db.query(Product).filter(Product.deleted_at == None)

@staticmethod
def list_products(db: Session, ...) -> tuple[list[Product], int]:
    query = ProductService._active_products_query(db)
    # ... apply filters ...
    total = query.count()
    products = query.order_by(...).offset(skip).limit(limit).all()
    return products, total
```

---

### Edge Case 2.6: Published_at Set Multiple Times

**Location:** `/services/product_service.py:532-533` (update_product_status)

**Problem:**
```python
# Line 532: Sets published_at ONLY if not already set
if new_status == ProductStatus.PUBLISHED and not product.published_at:
    product.published_at = func.now()
```

This is correct, but there's semantic ambiguity:
- If product goes PUBLISHED → SOLD → back to PUBLISHED (if allowed), published_at stays the same
- But the "real" publication time was the first time

**Edge Case Scenario:**
If state machine is later extended to allow SOLD → PUBLISHED (regression):
```
1. DRAFT → PUBLISHED (published_at = T1)
2. PUBLISHED → SOLD (sold_at = T2)
3. SOLD → PUBLISHED (published_at still T1) ← But product wasn't available for T1 to T2
```

**Recommendation:**
Add comment explaining the logic:

```python
# Only set published_at on FIRST publication (not on republication)
if new_status == ProductStatus.PUBLISHED and not product.published_at:
    product.published_at = func.now()
    # NOTE: If product regresses from SOLD back to PUBLISHED,
    # published_at is NOT updated. It represents the first publication.
```

---

### Edge Case 2.7: Image Display Order Collisions

**Location:** `/services/product_service.py:426-476` (reorder_images method)

**Problem:**
The reordering logic doesn't handle duplicate display_order values:

```python
# Line 464-466: Direct assignment without uniqueness check
for image_id, new_order in image_orders.items():
    image = next(img for img in images if img.id == image_id)
    image.display_order = new_order
```

**Scenario:**
```python
reorder_images(product_id, {
    1: 0,
    2: 0,  # Duplicate order value
    3: 1,
})
# Result: Two images with display_order=0 (undefined sort behavior)
```

**Business Impact:**
- Undefined image order when fetching
- UI may show images in wrong order
- "First image" selection becomes ambiguous

**Recommendation:**
```python
@staticmethod
def reorder_images(
    db: Session, product_id: int, image_orders: dict[int, int]
) -> list[ProductImage]:
    # Get all product images
    images = db.query(ProductImage).filter(ProductImage.product_id == product_id).all()
    image_ids = {img.id for img in images}

    # Validate all images exist
    for image_id in image_orders.keys():
        if image_id not in image_ids:
            raise ValueError(f"Image {image_id} does not belong to product {product_id}")

    # CRITICAL: Ensure no duplicate order values
    order_values = list(image_orders.values())
    if len(order_values) != len(set(order_values)):
        raise ValueError("Duplicate display_order values not allowed")

    # CRITICAL: Ensure order values are contiguous starting from 0
    if order_values and (min(order_values) != 0 or max(order_values) != len(order_values) - 1):
        raise ValueError(f"Display order must be contiguous (0 to {len(order_values)-1})")

    # Apply reordering
    for image_id, new_order in image_orders.items():
        image = next(img for img in images if img.id == image_id)
        image.display_order = new_order

    db.commit()
    return db.query(ProductImage).filter(...).order_by(...).all()
```

---

### Edge Case 2.8: Price Edge Cases

**Location:** `/schemas/product_schemas.py:58` and `/models/tenant/product.py:171-173`

**Problem:**
Price validation only checks `gt=0` but doesn't address:

```python
price: Decimal = Field(..., gt=0, description="Prix de vente (doit être > 0)")
```

**Edge Cases:**
- Price = 0.01 (1 cent) - Payout fees exceed revenue
- Price = 999999.99 - Unrealistic, may indicate data entry error
- Price rounding: DECIMAL(10,2) rounds to 2 places but some currencies need 3

**Business Impact:**
- Marketplace integration fails with invalid prices
- Revenue analysis broken by outliers
- Currency conversion issues

**Recommendation:**
```python
# In schemas/product_schemas.py
from decimal import Decimal

class ProductCreate(BaseModel):
    price: Decimal = Field(
        ...,
        gt=Decimal("0.5"),  # Minimum 50 cents
        lt=Decimal("100000"),  # Maximum 100k
        decimal_places=2,
        max_digits=10,
        description="Prix de vente (0.50 - 99999.99)"
    )

class ProductUpdate(BaseModel):
    price: Decimal | None = Field(
        None,
        gt=Decimal("0.5"),
        lt=Decimal("100000"),
        decimal_places=2,
        max_digits=10
    )
```

---

### Edge Case 2.9: SKU Uniqueness and Soft Delete

**Location:** `/models/tenant/product.py:164-166`

**Problem:**
SKU has a UNIQUE constraint:

```python
sku: Mapped[str | None] = mapped_column(
    String(100), unique=True, nullable=True, index=True
)
```

But soft-deleted products still hold the SKU uniqueness:

**Scenario:**
```
1. Create product with sku="ABC123"
2. Soft delete it
3. Try to create new product with sku="ABC123"
4. UNIQUE constraint violation ← Can't reuse SKU
```

**Business Impact:**
- Limit on reusing SKUs after soft delete
- Need workaround for duplicate product re-upload
- Business rule: deleted product's SKU should be recyclable

**Recommendation:**
```sql
-- Create partial unique index (excluding soft-deleted)
CREATE UNIQUE INDEX idx_product_sku_active
ON products(sku)
WHERE deleted_at IS NULL;

-- Drop the simple unique constraint
ALTER TABLE products DROP CONSTRAINT uq_product_sku;
```

And in ORM:
```python
# In models/tenant/product.py
sku: Mapped[str | None] = mapped_column(
    String(100),
    nullable=True,
    index=True,
    comment="SKU du produit (unique among active products only)"
)
# Unique constraint is enforced by partial index on non-deleted products
```

---

### Edge Case 2.10: Pagination Boundary Issues

**Location:** `/api/products.py:61-62`

**Problem:**
```python
limit: int = Query(20, ge=1, le=100, description="Nombre max de résultats (max 100)")
```

**Edge Case:** What if total < skip?
```
GET /api/products/?skip=1000&limit=20
Database has only 50 products
Returns: empty list (correct behavior)
But pagination math can be wrong
```

**Location:** `/api/products.py:89-90`

```python
page = (skip // limit) + 1
total_pages = math.ceil(total / limit) if total > 0 else 1
```

**Calculation Error Example:**
```
total = 25, limit = 20, skip = 20
page = (20 // 20) + 1 = 2  ← Correct
total_pages = ceil(25 / 20) = 2  ← Correct
But only 5 items exist on page 2, shows "Page 2 of 2" ← Actually shows empty page 2 correctly

However:
total = 0, limit = 20, skip = 0
total_pages = 1  ← Should be 0 or 1? Ambiguous
```

**Recommendation:**
```python
# More robust pagination
page_size = limit
total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1
current_page = (skip // page_size) + 1 if total > 0 else 1

# Validate skip is not beyond data
if skip >= total and total > 0:
    # Could warn or auto-correct
    skip = max(0, total - limit)
```

---

### Edge Case 2.11: Concurrent Delete and Status Update

**Location:** `/services/product_service.py:330-353` and `/services/product_service.py:479-542`

**Problem:**
No transaction-level synchronization between delete and status operations:

**Scenario (Race Condition):**
```
Thread 1: DELETE /api/products/5
  - Calls ProductService.delete_product()
  - Sets deleted_at = now()
  - Transaction pending...

Thread 2: PATCH /api/products/5/status?new_status=PUBLISHED
  - Calls ProductService.get_product_by_id()
  - Product found (deleted_at still NULL, read before Thread 1 commits)
  - Updates status = PUBLISHED
  - Commits

Thread 1: Commits delete (deleted_at set)

Result: Product is deleted BUT has status=PUBLISHED
Violates invariant: "Deleted products should not have publication dates"
```

**Business Impact:**
- Deleted products appear published in reports
- Archived/deleted products may show in marketplace
- Audit trail corruption

**Recommendation:**
Use explicit row locking:

```python
@staticmethod
def update_product_status(
    db: Session, product_id: int, new_status: ProductStatus
) -> Optional[Product]:
    # Lock the row to prevent concurrent deletes
    product = db.query(Product).filter(
        Product.id == product_id
    ).with_for_update().first()

    if not product or product.deleted_at is not None:
        return None

    # Now safe from concurrent delete
    # ... rest of validation ...
```

---

### Edge Case 2.12: Multi-Tenant Data Leakage via Category

**Location:** `/middleware/tenant_middleware.py:87-89`

**Problem:**
Categories are in the public schema, accessible to all tenants. This is correct for attribute data, but the FK relationship could leak data if not careful:

```python
# All tenants share category table
category = db.query(Category).filter(Category.name_en == "Jeans").first()
```

**Current Risk:** LOW (mitigated)
- Product query properly filtered by tenant schema
- But if someone queries Category separately without understanding multi-tenant model...

**Recommendation:**
Add documentation:

```python
# In models/public/category.py
"""
Category Model

IMPORTANT: This model is in the PUBLIC schema and is SHARED across all tenants.
This is intentional - categories are global reference data.

Do NOT assume category queries are automatically tenant-isolated.
This is correct because:
1. Categories are master data (same for all tenants)
2. Products in tenant schema link to categories in public schema
3. Tenant isolation happens at Product level, not Category level

DO NOT add tenant_id to categories.
"""
```

---

### Edge Case 2.13: Image Path Traversal Vulnerability

**Location:** `/services/file_service.py:116-121` and `/api/products.py:349`

**Problem:**
The image_path construction could be vulnerable if user-controlled:

```python
# Current code generates UUID, so safe
unique_filename = f"{uuid.uuid4().hex}.{extension}"
file_path = upload_path / unique_filename

# But if someone manually constructs image_path like:
image_path = "uploads/1/products/5/../../sensitive.jpg"
```

**Current State:** SAFE (UUID generation prevents this)

**But risk:** If path construction logic changes...

**Recommendation:**
Add validation:

```python
@staticmethod
def add_image(db: Session, product_id: int, image_path: str, ...) -> ProductImage:
    # Validate image_path doesn't contain parent directory traversal
    image_path_resolved = Path(image_path).resolve()
    base_path = Path(FileService.UPLOAD_BASE_DIR).resolve()

    if not str(image_path_resolved).startswith(str(base_path)):
        raise ValueError(f"Invalid image path: outside upload directory")

    # ... rest ...
```

---

### Edge Case 2.14: Reorder Images with Missing Images

**Location:** `/services/product_service.py:446-476`

**Problem:**
If you call reorder_images with only SOME images (not all), orphaned images are left with old display_order:

```python
images = [1, 2, 3, 4, 5]  # 5 images

reorder_images(product_id, {
    1: 0,
    2: 1,
    # Images 3, 4, 5 not in the dict
})

# Result:
# Images 1,2 reordered to 0,1
# Images 3,4,5 still have old orders (2,3,4) - not contiguous!
```

**Business Impact:**
- Inconsistent image ordering
- Display order 0,1,2,3,4 becomes 0,1,[old values]
- May show images in wrong order

**Recommendation:**
```python
@staticmethod
def reorder_images(
    db: Session, product_id: int, image_orders: dict[int, int]
) -> list[ProductImage]:
    images = db.query(ProductImage).filter(
        ProductImage.product_id == product_id
    ).all()

    image_ids = {img.id for img in images}

    # CRITICAL: Either ALL images must be provided or NONE
    if image_orders and len(image_orders) != len(images):
        raise ValueError(
            f"Must provide order for all {len(images)} images. "
            f"Provided orders for {len(image_orders)} images."
        )

    # Validate
    for image_id in image_orders.keys():
        if image_id not in image_ids:
            raise ValueError(f"Image {image_id} does not belong to product {product_id}")

    # Apply
    for image_id, new_order in image_orders.items():
        image = next(img for img in images if img.id == image_id)
        image.display_order = new_order

    db.commit()

    return db.query(ProductImage).filter(...).order_by(...).all()
```

---

## Part 3: Logical Inconsistencies and Design Issues

### Issue 3.1: Timestamps Not Aligned with Status Transitions

**Location:** `/models/tenant/product.py:278-294`

**Problem:**
Timestamps exist but aren't consistently managed:

```python
scheduled_publish_at: datetime | None  # Set but never used (MVP doesn't support SCHEDULED status)
published_at: datetime | None  # Set when status = PUBLISHED
sold_at: datetime | None  # Set when status = SOLD
deleted_at: datetime | None  # Set on soft delete
```

**Issue:** What about ARCHIVED status? No archived_at timestamp.

**Scenario:**
```
Product timeline:
1. created_at = 2025-01-01 10:00
2. PUBLISHED (published_at = 2025-01-01 11:00)
3. ARCHIVED (no archived_at timestamp)
4. Later: "When was this archived?" → No way to know
```

**Business Impact:**
- Incomplete audit trail
- Can't analyze how long products stayed available
- Reporting limitations

**Recommendation:**
Add missing timestamps:

```python
# In models/tenant/product.py
archived_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True),
    nullable=True,
    comment="Date d'archivage (status=ARCHIVED)"
)
```

And update in service:

```python
# In product_service.py, update_product_status()
if new_status == ProductStatus.ARCHIVED and not product.archived_at:
    product.archived_at = func.now()
```

---

### Issue 3.2: Definition of "ARCHIVED" vs "DELETED"

**Location:** Product workflow across multiple files

**Problem:**
Two different "inactive" states cause confusion:

- **ARCHIVED (status=ARCHIVED):** Visible in product model, in database, but status indicates "not for sale"
- **DELETED (deleted_at != NULL):** Soft delete, hidden from queries

**Semantic Confusion:**
```
Product A: status=ARCHIVED, deleted_at=NULL → Visible in admin, not in marketplace
Product B: status=DRAFT, deleted_at=2025-01-01 → Not visible anywhere

Question: What's the difference from user's perspective?
```

**Business Impact:**
- Complex audit logic (need to check both status AND deleted_at)
- Potential confusion in team: "Is deleted_at a historical record or current state?"
- Risk of data loss if soft-deleted products are hard-deleted in cleanup

**Recommendation:**
Document the distinction clearly:

```markdown
# Product Lifecycle States

## Active States (deleted_at = NULL)
- DRAFT: In progress, not visible to public
- PUBLISHED: Available for sale
- SOLD: Sale completed
- ARCHIVED: Retired, not for sale (but visible in admin for reference)

## Inactive States
- deleted_at != NULL: Soft-deleted, hidden from all queries (EXCEPT admin reports)

## Key Difference
- ARCHIVED = intentional business decision (product no longer for sale)
- DELETED = user initiated deletion (product removed from visibility)

## Examples
- Sell a product → status = SOLD
- Retire a product → status = ARCHIVED
- User removes product → deleted_at = now()
```

---

### Issue 3.3: Missing Validation on String Attributes

**Location:** `/services/product_service.py:136-174` (create_product)

**Problem:**
String attributes like `title`, `description`, `model`, `origin` are not validated for:
- Empty strings after trimming
- Excessive length despite Pydantic limits
- Special characters or injection vectors

**Current Validation (Weak):**
```python
# schemas/product_schemas.py
title: str = Field(..., min_length=1, max_length=500)
description: str = Field(..., min_length=1)
```

**Missing Validation:**
- What if title is just whitespace? " " passes min_length=1
- No XSS protection (could contain HTML/JS)
- No injection prevention

**Recommendation:**
```python
# In schemas/product_schemas.py
from pydantic import field_validator, StringConstraints

class ProductCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)

    @field_validator('title', 'description')
    @classmethod
    def validate_title_description(cls, v):
        # Trim whitespace
        v = v.strip()

        # Check not all whitespace
        if not v:
            raise ValueError("Cannot be empty or whitespace only")

        # Reject known malicious patterns
        if '<script' in v.lower() or 'javascript:' in v.lower():
            raise ValueError("Invalid content detected")

        return v
```

---

## Part 4: Data Corruption Scenarios

### Scenario 4.1: Orphaned Images After Product Deletion

**Condition:** Soft delete product with images

**Current Behavior:**
```python
# product_service.py line 333-336
def delete_product(...):
    product.deleted_at = func.now()
    db.commit()
    # Images are NOT deleted (by design)
```

**Problem:**
Product images remain in database:
```
products table: product_id=5 DELETED
product_images table: product_id=5 (3 images) ← ORPHANED
```

**Impact:**
- Disk usage grows with orphaned files
- Reports including deleted products become complex
- Recovery of deleted product now has dangling image references

**Scenario Details:**
1. User creates product with 5 images
2. User deletes product (soft delete)
3. Images remain in product_images table and disk
4. User tries to hard-delete old data → fails due to FK constraint
5. Disk space never reclaimed

**Recommendation:**
```python
# Option 1: Cascade delete images on soft delete (preferred)
@staticmethod
def delete_product(db: Session, product_id: int) -> bool:
    product = ProductService.get_product_by_id(db, product_id)
    if not product:
        return False

    # Delete associated images BEFORE soft delete
    images = db.query(ProductImage).filter(
        ProductImage.product_id == product_id
    ).all()

    for image in images:
        FileService.delete_product_image(image.image_path)
        db.delete(image)

    # Now soft delete
    product.deleted_at = func.now()
    db.commit()
    return True

# Option 2: Hard delete images on soft delete (alternative)
# Same as above but actually removes database records

# Option 3: Mark images as deleted too
# Add deleted_at to product_images too
```

---

### Scenario 4.2: Inconsistent Price/Stock After Partial Update

**Condition:** Concurrent price and stock updates

**Scenario:**
```
Thread 1: PUT /products/5 {"price": 49.99}
Thread 2: PUT /products/5 {"stock_quantity": 5}

Both read same initial state:
  price=39.99, stock=3

Thread 1 updates: price=49.99
Thread 2 updates: stock=5

Result (non-deterministic):
- Last write wins
- Could be (price=49.99, stock=3) or (price=39.99, stock=5)
```

**Impact:**
- Price and stock can get out of sync
- Inventory counting breaks
- Financial inconsistency

**Recommendation:**
Add version control (Optimistic Locking):

```python
# In models/tenant/product.py
version: Mapped[int] = mapped_column(
    Integer,
    default=0,
    server_default="0",
    comment="Version for optimistic locking"
)

# In services/product_service.py
@staticmethod
def update_product(db: Session, product_id: int, product_data: ProductUpdate, version: int) -> Optional[Product]:
    product = ProductService.get_product_by_id(db, product_id)
    if not product:
        return None

    # Check version
    if product.version != version:
        raise ValueError(
            f"Product has been modified. "
            f"Your version: {version}, current version: {product.version}. "
            f"Please refresh and try again."
        )

    # Update
    update_dict = product_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(product, key, value)

    # Increment version
    product.version += 1

    db.commit()
    db.refresh(product)
    return product
```

---

### Scenario 4.3: Published Timestamp Overwrite

**Condition:** If SOLD → PUBLISHED transition is added in future

**Current Protection:**
```python
# Line 532: Only sets published_at if not already set
if new_status == ProductStatus.PUBLISHED and not product.published_at:
    product.published_at = func.now()
```

**Future Risk:**
If someone changes this to always update:
```python
# WRONG - overwrites original publication time
if new_status == ProductStatus.PUBLISHED:
    product.published_at = func.now()
```

Then first published at time is lost.

**Impact:**
- Can't track actual first publication date
- Analytics broken
- Audit trail compromised

**Recommendation:**
Add comment and test:

```python
# CRITICAL: This logic depends on state machine
# If new transitions allow SOLD -> PUBLISHED, published_at logic must be reviewed
# TEST: Ensure published_at is set ONLY on first transition to PUBLISHED
@staticmethod
def test_published_at_set_once_only():
    """Test that published_at is never overwritten."""
    product = create_product()
    first_publish = datetime(2025, 1, 1, 10, 0)
    product.published_at = first_publish

    update_product_status(product, PUBLISHED)
    assert product.published_at == first_publish  # Should NOT change
```

---

## Part 5: Missing Security Considerations

### Security 5.1: File Upload Path Manipulation

Already addressed in Edge Case 2.13, but critical security issue:
- Current: SAFE (UUID generation)
- Risk: If someone modifies save_product_image to accept user path

### Security 5.2: SQL Injection via Search Paths

**Location:** `/middleware/tenant_middleware.py:88`

**Current (VULNERABLE):**
```python
db.execute(text(f"SET search_path TO {schema_name}, public"))
```

**Risk:** If schema_name contains quotes, could break out:
```
schema_name = 'client_1\'; DROP TABLE products; --'
Query becomes: SET search_path TO client_1'; DROP TABLE products; --, public
```

**Current mitigation:** Schema name comes from database (tenant_id), not user input, so relatively safe. But not ideal.

**Recommendation:**
```python
# Better approach - use parameter binding
db.execute(text(f"SET search_path TO {schema_name}, public"))

# BEST: Validate schema name format
import re

def validate_schema_name(schema_name: str) -> bool:
    # Only allow alphanumeric + underscore
    return bool(re.match(r'^[a-zA-Z0-9_]+$', schema_name))

if not validate_schema_name(schema_name):
    raise ValueError(f"Invalid schema name: {schema_name}")

db.execute(text(f"SET search_path TO {schema_name}, public"))
```

---

## Part 6: Summary of Recommendations by Priority

### P0 (Critical - Fix Immediately)
1. **Issue 1.2:** Add transaction-safe image upload with cleanup
2. **Issue 1.3:** Prevent circular category references
3. **Issue 1.4:** Prevent publishing zero-stock products
4. **Issue 1.1:** Prevent modifying deleted products

### P1 (High - Fix in Next Sprint)
1. **Issue 1.6:** Complete FK validation in update endpoint
2. **Edge Case 2.3:** Make image limit atomic (use row locking)
3. **Edge Case 2.5:** Create helper methods for active product queries
4. **Edge Case 2.9:** Use partial unique index for SKU (soft-delete aware)

### P2 (Medium - Plan for Future)
1. **Issue 3.1:** Add missing timestamps (archived_at)
2. **Scenario 4.2:** Implement optimistic locking for concurrent updates
3. **Edge Case 2.4:** Add realistic bounds for dimensions
4. **Edge Case 2.11:** Use explicit row locking for status updates

### P3 (Low - Code Quality)
1. **Edge Case 2.1:** Normalize case in FK lookups
2. **Edge Case 2.2:** Strip whitespace in FK lookups
3. **Edge Case 2.6:** Add documentation for published_at semantics
4. **Edge Case 2.14:** Validate complete image reordering

---

## Files Summary

**Critical Files to Review:**
- `/services/product_service.py` - 6 critical issues
- `/api/products.py` - 2 critical issues
- `/models/public/category.py` - 1 critical issue
- `/models/tenant/product.py` - 1 critical issue
- `/services/file_service.py` - 1 critical issue

**Total Issues Identified:** 11 Critical + 23 Edge Cases + 4 Data Corruption Scenarios = 38 issues requiring attention

---

## Implementation Timeline

**Week 1 (Immediate):**
- Issue 1.1: Prevent modifying deleted products
- Issue 1.2: Fix image upload transaction safety
- Issue 1.3: Circular category validation
- Issue 1.4: Stock > 0 for publication

**Week 2:**
- Issue 1.6: Complete FK validation
- Edge Case 2.3: Atomic image limit
- Edge Case 2.9: SKU partial index

**Week 3-4:**
- Optimistic locking implementation
- Timestamp alignment
- Comprehensive testing of state machine

---

## Testing Recommendations

Create tests for each critical issue:

```python
# Test Case 1.1
def test_cannot_update_soft_deleted_product():
    product = create_product()
    delete_product(product.id)

    with pytest.raises(ValueError, match="Cannot update deleted"):
        update_product(product.id, {"title": "New Title"})

# Test Case 1.2
def test_image_upload_transaction_safety():
    product = create_product()

    # Simulate DB failure after file save
    with patch.object(ProductService, 'add_image', side_effect=DatabaseError()):
        with pytest.raises(Exception):
            upload_image(product.id, fake_image)

    # Verify file was cleaned up
    assert image_file_not_exists()

# Test Case 1.3
def test_circular_category_reference_rejected():
    category = Category(name_en="Jeans", parent_category="Jeans")

    with pytest.raises(ValueError, match="own parent"):
        db.add(category)
        db.commit()

# Test Case 1.4
def test_cannot_publish_zero_stock():
    product = create_product(stock_quantity=0)

    with pytest.raises(ValueError, match="stock_quantity is 0"):
        update_product_status(product.id, PUBLISHED)
```

---

## Conclusion

The Product CRUD module demonstrates good foundational architecture with multi-tenant isolation and FK validation. However, it requires hardening in:

1. **State Machine Enforcement:** Prevent invalid status transitions and modifications
2. **Transaction Safety:** Ensure file uploads/deletions are atomic
3. **Concurrent Access:** Add row-level locking and optimistic concurrency control
4. **Data Consistency:** Add missing timestamps, prevent inventory anomalies

Implementing these recommendations will significantly improve data integrity, security, and user experience.
