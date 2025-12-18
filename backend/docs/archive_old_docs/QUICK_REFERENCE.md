# Product CRUD - Critical Issues Quick Reference

## Issues at a Glance

### P0 CRITICAL (Fix immediately)

| Issue | File | Lines | Impact | Fix Time |
|-------|------|-------|--------|----------|
| Deleted products modifiable | product_service.py | 288-290 | Data integrity | 30min |
| Orphaned images on failure | api/products.py | 298-311 | Data loss | 2h |
| Circular categories | category.py | 32-42 | Crash | 1h |
| Zero stock published | product_service.py | 136-174 | Business logic | 45min |
| Archive state override | api/products.py | 124-156 | State violation | 20min |

### P1 HIGH (Next sprint)

| Issue | File | Lines | Impact | Fix Time |
|-------|------|-------|--------|----------|
| Incomplete FK validation | product_service.py | 305-318 | Constraint violation | 1h |
| Image count race condition | product_service.py | 384-388 | Limit bypass | 1.5h |
| SKU soft-delete aware | product.py | 164-166 | Reusability issue | 1h |

---

## Code Locations Reference

```
/home/maribeiro/Stoflow/Stoflow_BackEnd/
├── services/
│   ├── product_service.py
│   │   ├── Line 266-327: update_product() ← Issue P0.1, P0.5
│   │   ├── Line 136-174: create_product() ← Issue P0.4
│   │   ├── Line 305-318: update() FK validation ← Issue P1
│   │   ├── Line 384-388: add_image() ← Issue P1 race
│   │   └── Line 478-542: update_product_status() ← Issue P0.4
│   └── file_service.py
│       └── Line 48-130: save_product_image() ← Issue P0.2
│
├── api/
│   └── products.py
│       ├── Line 124-156: PUT endpoint ← Issue P0.5
│       ├── Line 185-222: PATCH status ← Issue P0.4
│       └── Line 253-312: POST image upload ← Issue P0.2
│
├── models/
│   ├── public/
│   │   └── category.py
│   │       └── Line 32-42: Parent FK ← Issue P0.3
│   └── tenant/
│       └── product.py
│           └── Line 164-166: SKU uniqueness ← Issue P1
│
└── schemas/
    └── product_schemas.py
        ├── Line 58: Price validation ← Edge case
        └── Line 94: Stock validation ← Issue P0.4
```

---

## One-Minute Summary Per Issue

### P0.1: Deleted Products Modifiable
```python
# Current: Updates allowed on soft-deleted products
product.deleted_at = now()  # Product deleted
update_product(product_id)  # Still works!

# Fix: Add check in update_product()
if product.deleted_at is not None:
    raise ValueError("Cannot update deleted product")
```

### P0.2: Orphaned Images
```python
# Current: File saved, then DB fails
file_path = save_file()  # Success
db.add(image)            # Fails
# Result: File exists but no DB record

# Fix: DB first, then file, with cleanup
db.add(image)                    # Reserve slot
file_path = save_file()         # Protected
db.commit()
# If fails: cleanup both DB + file
```

### P0.3: Circular Categories
```python
# Current: Allowed
Category(name="Jeans", parent="Jeans")  # Valid!
cat.get_full_path()  # INFINITE LOOP

# Fix: Validator
if value == self.name_en:
    raise ValueError("Cannot be own parent")
```

### P0.4: Zero Stock Published
```python
# Current: Allowed
product.stock_quantity = 0
status = PUBLISHED  # Valid!

# Fix: Check before publish
if status == PUBLISHED and product.stock == 0:
    raise ValueError("Need stock >= 1")
```

### P0.5: Archive Override
```python
# Current: Status in update dict bypasses state machine
PUT /api/products/5 {"status": "PUBLISHED"}  # Bypasses transition rules

# Fix: Guard in update()
if 'status' in update_dict:
    raise ValueError("Use PATCH /products/{id}/status")
```

### P1: Incomplete FK Validation
```python
# Current: Only validates brand, color, size
# Missing: material, fit, gender, season

# Fix: Add validators for all 7 optional FK fields
if "material" in update_dict:
    material = db.query(Material).filter(...).first()
    if not material:
        raise ValueError(...)
# ... repeat for fit, gender, season
```

### P1: Image Count Race
```python
# Current: Check then insert (vulnerable to race)
count = db.query(...).count()  # count=19
if count >= 20: raise Error
# RACE: Another request adds image (now 20)
db.add(image)  # Inserts record 21!

# Fix: Use row locking
db.execute("SELECT ... FOR UPDATE")
count = db.query(...).count()  # NOW safe
if count >= 20: raise Error
db.add(image)
```

### P1: SKU Reusability
```python
# Current: UNIQUE constraint on SKU
sku="ABC" product_1 (deleted)
sku="ABC" product_2 (new) ← UNIQUE violation!

# Fix: Partial unique index
CREATE UNIQUE INDEX idx_sku_active 
ON products(sku) WHERE deleted_at IS NULL
-- Only enforces uniqueness on active products
```

---

## Testing Quick Commands

```bash
# Run all critical tests
pytest tests/test_products_critical.py -v

# Test specific issue
pytest tests/test_products_critical.py::test_cannot_update_soft_deleted_product -v

# Full coverage check
pytest --cov=services.product_service tests/

# Check specific file changed
git diff services/product_service.py
```

---

## Rollout Checklist (Minimal)

- [ ] Create feature branch: `fix/product-business-logic-critical`
- [ ] Implement P0.1 (30 min) + test
- [ ] Implement P0.2 (2 h) + test
- [ ] Implement P0.3 (1 h) + test
- [ ] Implement P0.4 (45 min) + test
- [ ] Implement P0.5 (20 min) + test
- [ ] All tests pass: `pytest tests/test_products_critical.py`
- [ ] Code review (at least 2 approvals)
- [ ] Merge to develop
- [ ] Deploy to staging
- [ ] Smoke test (24 hours monitoring)
- [ ] Deploy to production

---

## Key Files for Implementation

1. **Start here:** `CRITICAL_FIXES_CHECKLIST.md` - Has exact code to copy
2. **Understanding:** `BUSINESS_LOGIC_ANALYSIS.md` - Full context
3. **Testing:** Create `tests/test_products_critical.py` - Test each fix
4. **Reference:** This document - Quick lookup

---

## Common Questions

**Q: Can we fix P1 first (quicker)?**  
A: No. P0 are data corruption risks. Fix in order.

**Q: How long total?**  
A: P0 fixes = 4.25 hours implementation + 2 hours testing = 6.25 hours (1 day)

**Q: Do we need database migration?**  
A: Only for P1 (SKU partial index). Add before deploying.

**Q: What if production breaks?**  
A: Rollback to previous version. No data loss with these fixes (they prevent loss).

---

## Files to Update

| File | Changes | Reason |
|------|---------|--------|
| product_service.py | 5 methods | Fix P0.1, P0.4, P1 validation, P1 race |
| api/products.py | 2 endpoints | Fix P0.2, P0.5 |
| category.py | 1 validator | Fix P0.3 |
| product.py | 1 column | Fix P1 SKU uniqueness |
| test_products_critical.py | NEW file | Test all fixes |
| migration file | 1 migration | P1 SKU index |

**Total files changed: 6**  
**Total lines changed: ~150 lines** (across all files)

---

Last updated: 2025-12-05
