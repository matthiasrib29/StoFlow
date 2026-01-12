"""
Integration tests for concurrent publication race condition fix.

Tests SELECT FOR UPDATE behavior to ensure only one worker
can publish a product at a time.

Author: Claude
Date: 2026-01-12
"""

import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session

from models.user.product import Product, ProductStatus
from shared.database import SessionLocal
from shared.exceptions import ConflictError


class TestConcurrentPublication:
    """Test concurrent publication with SELECT FOR UPDATE."""

    @pytest.fixture
    def product(self, db_session: Session) -> Product:
        """Create a test product."""
        product = Product(
            title="Test Product",
            description="Test Description",
            price=10.00,
            status=ProductStatus.DRAFT,
            stock_quantity=1,
        )
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)
        return product

    def test_concurrent_load_product_only_one_succeeds(self, product: Product):
        """
        When two workers try to load the same product with SELECT FOR UPDATE,
        only one should succeed and the other should get ConflictError.
        """
        product_id = product.id
        results = []

        def load_product_with_lock():
            """Simulate worker loading product with lock."""
            db = SessionLocal()
            try:
                # Simulate BasePublishHandler._load_product() logic
                from sqlalchemy.exc import OperationalError
                try:
                    product = (
                        db.query(Product)
                        .filter(Product.id == product_id)
                        .with_for_update(nowait=True)
                        .first()
                    )
                    # Hold lock for a moment to simulate processing
                    import time
                    time.sleep(0.2)
                    return {"success": True, "product_id": product.id}
                except OperationalError:
                    raise ConflictError("Product locked by another worker")
            finally:
                db.close()

        # Run two workers concurrently
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(load_product_with_lock) for _ in range(2)]

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(("success", result))
                except ConflictError as e:
                    results.append(("conflict", str(e)))

        # Verify results
        successes = [r for r in results if r[0] == "success"]
        conflicts = [r for r in results if r[0] == "conflict"]

        # Exactly one should succeed
        assert len(successes) == 1, f"Expected 1 success, got {len(successes)}"
        assert len(conflicts) == 1, f"Expected 1 conflict, got {len(conflicts)}"

        # Success should have the product
        assert successes[0][1]["product_id"] == product_id

        # Conflict should have error message
        assert "locked" in conflicts[0][1].lower()

    def test_second_worker_can_lock_after_first_commits(self, product: Product):
        """
        When first worker releases lock (commits), second worker should
        be able to acquire the lock successfully.
        """
        product_id = product.id

        # First worker locks and releases
        db1 = SessionLocal()
        try:
            product1 = (
                db1.query(Product)
                .filter(Product.id == product_id)
                .with_for_update(nowait=True)
                .first()
            )
            assert product1 is not None
            # Modify something
            product1.status = ProductStatus.PROCESSING
            db1.commit()
        finally:
            db1.close()

        # Second worker should now be able to lock
        db2 = SessionLocal()
        try:
            product2 = (
                db2.query(Product)
                .filter(Product.id == product_id)
                .with_for_update(nowait=True)
                .first()
            )
            assert product2 is not None
            assert product2.status == ProductStatus.PROCESSING
            db2.commit()
        finally:
            db2.close()

    def test_load_product_without_lock_allows_concurrent_reads(self, product: Product):
        """
        Loading product WITHOUT for_update should allow concurrent reads
        (this is the normal behavior for non-critical operations).
        """
        product_id = product.id
        results = []

        def read_product():
            """Read product without lock."""
            db = SessionLocal()
            try:
                product = (
                    db.query(Product)
                    .filter(Product.id == product_id)
                    .first()
                )
                import time
                time.sleep(0.1)
                return {"success": True, "title": product.title}
            finally:
                db.close()

        # Run multiple concurrent reads
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(read_product) for _ in range(5)]

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        # All reads should succeed
        assert len(results) == 5
        assert all(r["success"] for r in results)
        assert all(r["title"] == "Test Product" for r in results)
