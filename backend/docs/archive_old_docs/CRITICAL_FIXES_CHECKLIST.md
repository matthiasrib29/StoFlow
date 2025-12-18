# Critical Business Logic Fixes - Developer Checklist

## Quick Navigation
| Priority | Issue | File | Line | Status |
|----------|-------|------|------|--------|
| P0 | Deleted products modifiable | `product_service.py` | 288-290 | TODO |
| P0 | Orphaned images on upload failure | `api/products.py` | 298-311 | TODO |
| P0 | Circular category references | `models/public/category.py` | 32-42 | TODO |
| P0 | Zero stock published products | `product_service.py` | 136-174 | TODO |
| P0 | Archive state regression | `api/products.py` | 124-156 | TODO |
| P1 | Incomplete FK validation | `product_service.py` | 305-318 | TODO |
| P1 | Image count race condition | `product_service.py` | 384-388 | TODO |
| P1 | SKU uniqueness & soft-delete | `models/tenant/product.py` | 164-166 | TODO |

---

## P0: Issue 1.1 - Prevent Modifying Deleted Products

### Test First
```python
# tests/test_products_critical.py
def test_cannot_update_soft_deleted_product(db_session, test_product):
    """CRITICAL: Deleted products must be immutable."""
    ProductService.delete_product(db_session, test_product.id)

    with pytest.raises(ValueError, match="Cannot update deleted"):
        ProductService.update_product(
            db_session,
            test_product.id,
            ProductUpdate(title="New Title")
        )
```

### Fix
**File:** `/home/maribeiro/Stoflow/Stoflow_BackEnd/services/product_service.py`

**Location:** Line 266-290 in `update_product()` method

```python
@staticmethod
def update_product(
    db: Session, product_id: int, product_data: ProductUpdate
) -> Optional[Product]:
    """
    Met à jour un produit.

    Business Rules:
    - Validation des FK si modifiés (brand, category, condition, etc.)
    - updated_at automatiquement mis à jour par SQLAlchemy
    - Ne peut pas modifier un produit supprimé
    - CRITICAL: Deleted products are immutable

    Args:
        db: Session SQLAlchemy
        product_id: ID du produit à modifier
        product_data: Nouvelles données (champs optionnels)

    Returns:
        Product mis à jour ou None si non trouvé

    Raises:
        ValueError: Si un attribut FK est invalide OU produit supprimé
    """
    product = ProductService.get_product_by_id(db, product_id)
    if not product:
        return None

    # CRITICAL FIX: Reject updates on deleted products
    if product.deleted_at is not None:
        raise ValueError(
            f"Cannot update deleted product {product_id}. "
            f"Product was deleted at {product.deleted_at}"
        )

    # ... rest of method unchanged ...
```

### Verification
```bash
# Run test
pytest tests/test_products_critical.py::test_cannot_update_soft_deleted_product -v

# Verify the check is in place
grep -n "Cannot update deleted" services/product_service.py
```

---

## P0: Issue 1.2 - Orphaned Images on Upload Failure

### Test First
```python
def test_image_upload_transaction_safety(db_session, test_product):
    """CRITICAL: File and DB must be atomic."""
    tenant_id = 1
    product_id = test_product.id

    # Mock FileService.save_product_image to succeed
    # Mock ProductService.add_image to fail
    with patch.object(ProductService, 'add_image', side_effect=DatabaseError("Connection lost")):
        with pytest.raises(DatabaseError):
            upload_product_image(
                product_id=product_id,
                file=fake_image,
                display_order=0,
                request=Mock(state=Mock(tenant_id=tenant_id)),
                db=db_session
            )

    # CRITICAL: File must be cleaned up
    # This test will fail until fix is implemented
    import os
    expected_path = f"uploads/{tenant_id}/products/{product_id}"
    assert not os.path.exists(expected_path) or len(os.listdir(expected_path)) == 0
```

### Fix
**File:** `/home/maribeiro/Stoflow/Stoflow_BackEnd/api/products.py`

**Location:** Lines 253-312 in `upload_product_image()` endpoint

```python
@router.post(
    "/{product_id}/images",
    response_model=ProductImageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    display_order: int = Query(0, ge=0),
    request: Request = None,
    db: Session = Depends(get_db),
) -> ProductImageResponse:
    """
    Upload une image pour un produit.

    CRITICAL: Implementation must ensure atomicity of file + DB operations.
    """
    tenant_id = request.state.tenant_id

    # STEP 1: Validate product exists FIRST
    product = ProductService.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )

    # STEP 2: Check image count limit BEFORE any file operations
    try:
        FileService.validate_image_count(db, product_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # STEP 3: Validate file format and size BEFORE DB commit
    try:
        # This will raise ValueError if format/size invalid
        # But only reads from memory, doesn't write to disk
        content = await file.read(512)
        await file.seek(0)
        image_type = imghdr.what(None, content)
        # ... full validation logic ...
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # STEP 4: Reserve slot in DB FIRST (creates transaction checkpoint)
    image_path = None
    product_image = None

    try:
        # Create DB record with temporary path
        product_image = ProductService.add_image(
            db, product_id,
            image_path="[pending-upload]",
            display_order=display_order
        )

        # STEP 5: NOW save file to disk (protected by DB record)
        image_path = await FileService.save_product_image(tenant_id, product_id, file)

        # STEP 6: Update DB record with real path
        product_image.image_path = image_path
        db.commit()

        return product_image

    except Exception as e:
        # CLEANUP on ANY exception

        # Delete DB record if it was created
        if product_image and product_image.id:
            try:
                db.rollback()  # Rollback any pending transaction
                ProductService.delete_image(db, product_image.id)
            except Exception:
                pass

        # Delete file if it was written
        if image_path:
            try:
                FileService.delete_product_image(image_path)
            except Exception:
                pass

        # Log error and re-raise
        import logging
        logging.error(f"Image upload failed for product {product_id}: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e) if isinstance(e, ValueError) else "Image upload failed"
        )
```

### Verification
```bash
pytest tests/test_products_critical.py::test_image_upload_transaction_safety -v
```

---

## P0: Issue 1.3 - Circular Category References

### Test First
```python
def test_category_cannot_be_own_parent(db_session):
    """CRITICAL: Circular references crash get_full_path()."""
    category = Category(name_en="Jeans", parent_category="Jeans")
    db_session.add(category)

    with pytest.raises(ValueError, match="own parent"):
        db_session.commit()

def test_category_circular_reference_detection(db_session):
    """CRITICAL: Multi-level cycles must be prevented."""
    # Create: A -> B -> C -> A (circular)
    cat_a = Category(name_en="A")
    cat_b = Category(name_en="B", parent_category="A")
    cat_c = Category(name_en="C", parent_category="B")

    db_session.add_all([cat_a, cat_b, cat_c])
    db_session.commit()

    # Now try to create cycle: A.parent = C
    cat_a.parent_category = "C"

    with pytest.raises(ValueError, match="circular"):
        db_session.commit()
```

### Fix
**File:** `/home/maribeiro/Stoflow/Stoflow_BackEnd/models/public/category.py`

**Location:** Lines 14-90 in Category model

```python
from sqlalchemy import event
from sqlalchemy.orm import validates

class Category(Base):
    """Category model with circular reference prevention."""

    __tablename__ = "categories"
    __table_args__ = {} if os.getenv("TESTING") else {"schema": "public"}

    name_en: Mapped[str] = mapped_column(
        String(100), primary_key=True, index=True, comment="Nom de la catégorie (EN)"
    )
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
    # ... other fields ...

    # CRITICAL FIX: Add validator to prevent circular references
    @validates('parent_category')
    def validate_parent_category(self, key, value):
        """
        Prevent self-references and circular hierarchies.

        CRITICAL: This prevents data corruption from circular references.
        """
        # Reject self-reference
        if value and value == self.name_en:
            raise ValueError(
                f"Category '{self.name_en}' cannot be its own parent"
            )

        # Check for circular hierarchy (max depth 10)
        if value:
            current = self
            visited = set()
            depth = 0
            max_depth = 10

            while current.parent and depth < max_depth:
                if current.parent.name_en == value:
                    raise ValueError(
                        f"Would create circular hierarchy: "
                        f"{self.name_en} -> {value} -> ... -> {self.name_en}"
                    )
                if current.parent.name_en in visited:
                    # Cycle detected in existing data
                    raise ValueError(f"Existing circular hierarchy detected")
                visited.add(current.parent.name_en)
                current = current.parent
                depth += 1

            if depth >= max_depth:
                raise ValueError("Category hierarchy too deep (max 10 levels)")

        return value

    def get_full_path(self) -> str:
        """
        Retourne le chemin complet de la catégorie.

        SAFE: Circular references prevented by validator.
        """
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name_en}"
        return self.name_en
```

### Verification
```bash
pytest tests/test_categories.py::test_category_cannot_be_own_parent -v
pytest tests/test_categories.py::test_category_circular_reference_detection -v
```

---

## P0: Issue 1.4 - Zero Stock Published Products

### Test First
```python
def test_cannot_publish_zero_stock_product(db_session, test_product):
    """CRITICAL: Publishing requires stock >= 1."""
    test_product.stock_quantity = 0
    db_session.commit()

    with pytest.raises(ValueError, match="stock_quantity is 0"):
        ProductService.update_product_status(
            db_session,
            test_product.id,
            ProductStatus.PUBLISHED
        )

def test_can_publish_with_stock(db_session, test_product):
    """CRITICAL: Publishing with stock should work."""
    test_product.stock_quantity = 1
    db_session.commit()

    result = ProductService.update_product_status(
        db_session,
        test_product.id,
        ProductStatus.PUBLISHED
    )

    assert result.status == ProductStatus.PUBLISHED
    assert result.published_at is not None
```

### Fix
**File:** `/home/maribeiro/Stoflow/Stoflow_BackEnd/services/product_service.py`

**Location:** Lines 478-542 in `update_product_status()` method

```python
@staticmethod
def update_product_status(
    db: Session, product_id: int, new_status: ProductStatus
) -> Optional[Product]:
    """
    Met à jour le status d'un produit.

    Business Rules (MVP - 2025-12-04):
    - Transitions MVP autorisées:
      - DRAFT → PUBLISHED
      - PUBLISHED → SOLD
      - PUBLISHED → ARCHIVED
      - SOLD → ARCHIVED
    - CRITICAL: Cannot publish without stock

    Args:
        db: Session SQLAlchemy
        product_id: ID du produit
        new_status: Nouveau status

    Returns:
        Product mis à jour ou None si non trouvé

    Raises:
        ValueError: Si status non autorisé ou transition invalide
    """
    if new_status not in ProductService.MVP_STATUSES:
        raise ValueError(
            f"Status {new_status} not allowed in MVP. "
            f"Allowed: {', '.join([s.value for s in ProductService.MVP_STATUSES])}"
        )

    product = ProductService.get_product_by_id(db, product_id)
    if not product:
        return None

    # Valider les transitions
    current_status = product.status
    valid_transitions = {
        ProductStatus.DRAFT: [ProductStatus.PUBLISHED],
        ProductStatus.PUBLISHED: [ProductStatus.SOLD, ProductStatus.ARCHIVED],
        ProductStatus.SOLD: [ProductStatus.ARCHIVED],
        ProductStatus.ARCHIVED: [],  # Aucune transition depuis ARCHIVED
    }

    if new_status not in valid_transitions.get(current_status, []):
        raise ValueError(
            f"Invalid transition: {current_status.value} → {new_status.value}"
        )

    # CRITICAL FIX: Prevent publishing without stock
    if new_status == ProductStatus.PUBLISHED and product.stock_quantity == 0:
        raise ValueError(
            f"Cannot publish product {product_id}: stock_quantity is 0. "
            f"Minimum stock required for publication: 1 unit"
        )

    # Mettre à jour le status
    product.status = new_status

    # Mettre à jour published_at si publication
    if new_status == ProductStatus.PUBLISHED and not product.published_at:
        product.published_at = func.now()

    # Mettre à jour sold_at si vendu
    if new_status == ProductStatus.SOLD and not product.sold_at:
        product.sold_at = func.now()

    db.commit()
    db.refresh(product)

    return product
```

### Verification
```bash
pytest tests/test_products_critical.py::test_cannot_publish_zero_stock_product -v
pytest tests/test_products_critical.py::test_can_publish_with_stock -v
```

---

## P0: Issue 1.5 - Archive State Regression Prevention

### Fix
**File:** `/home/maribeiro/Stoflow/Stoflow_BackEnd/services/product_service.py`

**Location:** Line 321-322 in `update_product()` method

Add guard clause at the start of the update logic:

```python
@staticmethod
def update_product(
    db: Session, product_id: int, product_data: ProductUpdate
) -> Optional[Product]:
    """..."""
    product = ProductService.get_product_by_id(db, product_id)
    if not product:
        return None

    if product.deleted_at is not None:
        raise ValueError(f"Cannot update deleted product {product_id}")

    # CRITICAL FIX: Prevent status changes via generic update
    update_dict = product_data.model_dump(exclude_unset=True)

    if 'status' in update_dict:
        raise ValueError(
            "Status cannot be updated via PUT endpoint. "
            "Use PATCH /products/{id}/status instead for status transitions"
        )

    # ... rest of validation ...
```

---

## P1: Issue 1.6 - Complete FK Validation

### Fix
**File:** `/home/maribeiro/Stoflow/Stoflow_BackEnd/services/product_service.py`

**Location:** Lines 315-318, add missing validators

```python
# In update_product method, after line 318, add:

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

## P1: Issue 2.3 - Image Count Race Condition

### Fix with Row Locking
**File:** `/home/maribeiro/Stoflow/Stoflow_BackEnd/services/product_service.py`

**Location:** Lines 384-388 in `add_image()` method

```python
@staticmethod
def add_image(
    db: Session, product_id: int, image_path: str, display_order: int = 0
) -> ProductImage:
    """
    Ajoute une image à un produit.

    Business Rules (2025-12-04):
    - Maximum 20 images par produit (limite Vinted)
    - CRITICAL: Use row locking to prevent race condition
    """
    # Vérifier que le produit existe
    product = ProductService.get_product_by_id(db, product_id)
    if not product:
        raise ValueError(f"Product with id {product_id} not found")

    # CRITICAL FIX: Lock row to prevent concurrent additions
    from sqlalchemy import text

    db.execute(
        text("SELECT 1 FROM products WHERE id = :product_id FOR UPDATE"),
        {"product_id": product_id}
    )

    # NOW check count (under lock - race condition prevented)
    image_count = db.query(ProductImage).filter(ProductImage.product_id == product_id).count()
    if image_count >= 20:
        raise ValueError(f"Product already has {image_count} images (max 20)")

    # Créer l'image
    product_image = ProductImage(
        product_id=product_id, image_path=image_path, display_order=display_order
    )

    db.add(product_image)
    db.commit()
    db.refresh(product_image)

    return product_image
```

---

## P1: Issue 2.9 - SKU Uniqueness Aware of Soft-Delete

### Fix
**File:** `/home/maribeiro/Stoflow/Stoflow_BackEnd/models/tenant/product.py`

**Step 1:** Update model (line 164-166):

```python
sku: Mapped[str | None] = mapped_column(
    String(100),
    nullable=True,
    index=True,
    comment="SKU du produit (unique among active products only)"
)
# Remove unique=True constraint - will use partial index instead
```

**Step 2:** Add migration for partial index:

```python
# migrations/versions/XXXX_add_partial_unique_sku_index.py

def upgrade():
    op.execute('''
    CREATE UNIQUE INDEX idx_product_sku_active
    ON products(sku)
    WHERE deleted_at IS NULL
    ''')
    op.execute('ALTER TABLE products DROP CONSTRAINT uq_product_sku')

def downgrade():
    op.execute('DROP INDEX idx_product_sku_active')
    op.execute('ALTER TABLE products ADD CONSTRAINT uq_product_sku UNIQUE(sku)')
```

---

## Testing Command

Run all critical tests:

```bash
# Run critical test suite
pytest tests/test_products_critical.py -v

# Run specific issues
pytest tests/test_products_critical.py::test_cannot_update_soft_deleted_product -v
pytest tests/test_products_critical.py::test_image_upload_transaction_safety -v
pytest tests/test_products_critical.py::test_category_cannot_be_own_parent -v
pytest tests/test_products_critical.py::test_cannot_publish_zero_stock_product -v

# Full coverage
pytest tests/test_products.py tests/test_products_critical.py --cov=services.product_service --cov=api.products
```

---

## Rollout Checklist

- [ ] Create CRITICAL_FIXES_CHECKLIST.md branch
- [ ] Implement P0 fixes (4 issues)
- [ ] Write tests for all P0 fixes
- [ ] Code review with senior developer
- [ ] Run full test suite
- [ ] Test in staging environment
- [ ] Deploy to production
- [ ] Monitor for issues (first 24h)
- [ ] Implement P1 fixes
- [ ] Document lessons learned

---

## References

Full analysis: `BUSINESS_LOGIC_ANALYSIS.md`

Lines referenced match line numbers in current codebase as of 2025-12-05.
