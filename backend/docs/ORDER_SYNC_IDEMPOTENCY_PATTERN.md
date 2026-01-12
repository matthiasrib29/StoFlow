# Order Synchronization Idempotency Pattern

**Security Phase 2.3 (2026-01-12)**

## Purpose

Provide a reference implementation for idempotent order creation/update to prevent duplicate orders when multiple workers sync simultaneously from marketplaces.

## Current Protection

All order models already have unique constraints:
- `EbayOrder.order_id` - UNIQUE constraint (models/user/ebay_order.py:63)
- `VintedOrder.transaction_id` - PRIMARY KEY (models/vinted/vinted_order.py:42)
- Future: `EtsyOrder.receipt_id` - should be UNIQUE

## Problem Scenario

Two workers sync orders simultaneously from marketplace API:
```
Worker A: Fetches order #12345 → Creates EbayOrder → DB INSERT
Worker B: Fetches order #12345 → Creates EbayOrder → DB INSERT (FAILS)
```

Without proper handling, Worker B crashes with IntegrityError.

## Solution: ON CONFLICT DO UPDATE Pattern

### Pattern 1: Try INSERT, catch IntegrityError, then UPDATE

```python
from sqlalchemy.exc import IntegrityError

def sync_order_idempotent(db: Session, order_data: dict) -> EbayOrder:
    """
    Create or update order (idempotent).

    Args:
        db: SQLAlchemy session
        order_data: Order data from marketplace API

    Returns:
        EbayOrder instance (created or updated)
    """
    order_id = order_data["order_id"]

    # Try INSERT first (optimistic)
    order = EbayOrder(
        order_id=order_id,
        marketplace_id=order_data["marketplace_id"],
        buyer_username=order_data["buyer_username"],
        # ... other fields ...
    )

    try:
        db.add(order)
        db.flush()  # Trigger unique constraint check
        logger.info(f"Created new order: {order_id}")
        return order

    except IntegrityError as e:
        # Another worker won the race
        db.rollback()

        if "order_id" in str(e) or "unique" in str(e).lower():
            # Get existing order and update
            order = db.query(EbayOrder).filter(
                EbayOrder.order_id == order_id
            ).first()

            if not order:
                # Rare case: order deleted between INSERT and SELECT
                raise

            # Update fields (only if needed)
            order.order_fulfillment_status = order_data["order_fulfillment_status"]
            order.order_payment_status = order_data["order_payment_status"]
            order.total_price = order_data["total_price"]
            # ... update other fields ...

            order.updated_at = datetime.now(timezone.utc)
            db.flush()
            logger.info(f"Updated existing order: {order_id}")
            return order
        else:
            # Other integrity error (FK violation, etc.)
            raise
```

### Pattern 2: SELECT FOR UPDATE then INSERT or UPDATE

```python
def sync_order_with_lock(db: Session, order_data: dict) -> EbayOrder:
    """
    Create or update order with pessimistic lock.

    Args:
        db: SQLAlchemy session
        order_data: Order data from marketplace API

    Returns:
        EbayOrder instance (created or updated)
    """
    order_id = order_data["order_id"]

    # Lock row if exists (prevents concurrent updates)
    order = (
        db.query(EbayOrder)
        .filter(EbayOrder.order_id == order_id)
        .with_for_update(nowait=True)
        .first()
    )

    if order:
        # Update existing
        order.order_fulfillment_status = order_data["order_fulfillment_status"]
        order.order_payment_status = order_data["order_payment_status"]
        order.total_price = order_data["total_price"]
        order.updated_at = datetime.now(timezone.utc)
        db.flush()
        logger.info(f"Updated order: {order_id}")
        return order
    else:
        # Create new
        order = EbayOrder(
            order_id=order_id,
            marketplace_id=order_data["marketplace_id"],
            # ... all fields ...
        )
        db.add(order)
        db.flush()
        logger.info(f"Created order: {order_id}")
        return order
```

### Pattern 3: PostgreSQL UPSERT (ON CONFLICT)

```python
from sqlalchemy import text

def sync_order_upsert(db: Session, order_data: dict) -> None:
    """
    Upsert order using PostgreSQL ON CONFLICT.

    Note: This bypasses SQLAlchemy ORM and uses raw SQL.
    """
    query = text("""
        INSERT INTO ebay_orders (
            order_id, marketplace_id, buyer_username, total_price,
            order_fulfillment_status, order_payment_status, created_at, updated_at
        ) VALUES (
            :order_id, :marketplace_id, :buyer_username, :total_price,
            :order_fulfillment_status, :order_payment_status, NOW(), NOW()
        )
        ON CONFLICT (order_id) DO UPDATE SET
            order_fulfillment_status = EXCLUDED.order_fulfillment_status,
            order_payment_status = EXCLUDED.order_payment_status,
            total_price = EXCLUDED.total_price,
            updated_at = NOW()
        RETURNING id
    """)

    result = db.execute(query, order_data)
    order_id = result.scalar()
    logger.info(f"Upserted order: {order_data['order_id']} (id={order_id})")
```

## Recommended Approach

**Pattern 1 (Try INSERT, catch IntegrityError)** is recommended because:
- ✅ Works with SQLAlchemy ORM (type-safe, relationships handled)
- ✅ Optimistic: Fast path for new orders (no lock)
- ✅ Handles race conditions gracefully
- ✅ Testable and maintainable

## Testing Idempotency

```python
def test_concurrent_order_sync_only_one_created():
    """Test that concurrent syncs create only one order."""
    order_data = {"order_id": "12-12345-12345", ...}

    def sync_worker():
        db = SessionLocal()
        try:
            return sync_order_idempotent(db, order_data)
        finally:
            db.close()

    # Run two workers concurrently
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(sync_worker) for _ in range(2)]
        results = [f.result() for f in futures]

    # Both should succeed (one creates, one updates)
    assert len(results) == 2
    assert results[0].order_id == results[1].order_id

    # Verify only one order in DB
    db = SessionLocal()
    orders = db.query(EbayOrder).filter(
        EbayOrder.order_id == order_data["order_id"]
    ).all()
    assert len(orders) == 1
    db.close()
```

## Implementation Checklist

When implementing order sync services:

- [ ] Unique constraint on marketplace order ID (already exists)
- [ ] Use Pattern 1 (Try INSERT, catch IntegrityError)
- [ ] Log created vs updated for monitoring
- [ ] Handle line items (EbayOrderProduct) idempotently
- [ ] Test with concurrent workers (ThreadPoolExecutor)
- [ ] Monitor sync_orders endpoint for IntegrityErrors

## Related Files

- `models/user/ebay_order.py` - EbayOrder model (unique on order_id)
- `models/vinted/vinted_order.py` - VintedOrder model (PK on transaction_id)
- `services/marketplace/handlers/base_publish_handler.py` - SELECT FOR UPDATE example

---

*Document created: 2026-01-12*
*Security Phase 2.3: Order deduplication protection*
