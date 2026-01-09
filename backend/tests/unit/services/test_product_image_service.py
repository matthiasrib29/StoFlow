"""
Unit Tests for ProductImageService

Tests product image operations (JSONB) including add, delete, and reorder.

Business Rules Tested:
- Maximum 20 images per product (Vinted limit)
- Cannot add images to SOLD products
- Auto-calculate display_order when not provided
- Auto-reorder remaining images after deletion
- Validate URLs during reorder operation

Created: 2026-01-08
Phase 1.1: Unit testing
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch

from models.user.product import Product, ProductStatus
from services.product_image_service import ProductImageService, MAX_IMAGES_PER_PRODUCT


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_db():
    """Mock database session."""
    session = MagicMock()
    session.query = Mock()
    session.add = Mock()
    session.flush = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    session.execute = Mock()
    session.rollback = Mock()
    return session


@pytest.fixture
def mock_product():
    """Mock Product instance with no images."""
    product = Product(
        id=1,
        title="Test Product",
        description="Test description",
        price=49.99,
        category="T-shirt",
        brand="Nike",
        condition=8,
        stock_quantity=1,
        status=ProductStatus.DRAFT,
        images=[],
        created_at=datetime.now(timezone.utc),
    )
    return product


@pytest.fixture
def mock_product_with_images():
    """Mock Product instance with existing images."""
    product = Product(
        id=1,
        title="Test Product",
        description="Test description",
        price=49.99,
        category="T-shirt",
        brand="Nike",
        condition=8,
        stock_quantity=1,
        status=ProductStatus.DRAFT,
        images=[
            {"url": "http://cdn.example.com/img1.jpg", "order": 0, "created_at": "2026-01-01T10:00:00Z"},
            {"url": "http://cdn.example.com/img2.jpg", "order": 1, "created_at": "2026-01-01T10:01:00Z"},
            {"url": "http://cdn.example.com/img3.jpg", "order": 2, "created_at": "2026-01-01T10:02:00Z"},
        ],
        created_at=datetime.now(timezone.utc),
    )
    return product


@pytest.fixture
def mock_product_sold():
    """Mock SOLD Product instance."""
    product = Product(
        id=1,
        title="Sold Product",
        description="This product is sold",
        price=99.99,
        category="T-shirt",
        brand="Nike",
        condition=8,
        stock_quantity=0,
        status=ProductStatus.SOLD,
        images=[],
        created_at=datetime.now(timezone.utc),
    )
    return product


@pytest.fixture
def mock_product_max_images():
    """Mock Product with maximum images (20)."""
    images = [
        {"url": f"http://cdn.example.com/img{i}.jpg", "order": i, "created_at": "2026-01-01T10:00:00Z"}
        for i in range(MAX_IMAGES_PER_PRODUCT)
    ]
    product = Product(
        id=1,
        title="Product with max images",
        description="This product has 20 images",
        price=49.99,
        category="T-shirt",
        brand="Nike",
        condition=8,
        stock_quantity=1,
        status=ProductStatus.DRAFT,
        images=images,
        created_at=datetime.now(timezone.utc),
    )
    return product


# =============================================================================
# ADD IMAGE TESTS
# =============================================================================


class TestAddImage:
    """Tests for ProductImageService.add_image."""

    @patch('services.product_image_service.ProductRepository')
    @patch('services.product_image_service.utc_now')
    def test_add_image_success(self, mock_utc_now, mock_repo, mock_db, mock_product):
        """
        Should successfully add an image to a product.

        Business Rule:
        - Image is added with URL, order, and created_at timestamp
        - Product images list is updated
        """
        # Setup mocks
        mock_repo.get_by_id.return_value = mock_product
        mock_utc_now.return_value = datetime(2026, 1, 8, 12, 0, 0, tzinfo=timezone.utc)

        image_url = "http://cdn.example.com/new-image.jpg"

        # Execute
        result = ProductImageService.add_image(mock_db, product_id=1, image_url=image_url)

        # Verify
        assert result is not None
        assert result["url"] == image_url
        assert result["order"] == 0  # First image
        assert result["created_at"] == "2026-01-08T12:00:00Z"
        assert len(mock_product.images) == 1
        mock_repo.get_by_id.assert_called_once_with(mock_db, 1)

    @patch('services.product_image_service.ProductRepository')
    @patch('services.product_image_service.utc_now')
    def test_add_image_auto_calculates_order(
        self, mock_utc_now, mock_repo, mock_db, mock_product_with_images
    ):
        """
        Should auto-calculate display_order when not provided.

        Business Rule:
        - If display_order is None, calculate as len(existing_images)
        - New image is appended at the end of the list
        """
        # Setup mocks
        mock_repo.get_by_id.return_value = mock_product_with_images
        mock_utc_now.return_value = datetime(2026, 1, 8, 12, 0, 0, tzinfo=timezone.utc)

        image_url = "http://cdn.example.com/img4.jpg"

        # Execute (display_order=None by default)
        result = ProductImageService.add_image(mock_db, product_id=1, image_url=image_url)

        # Verify
        assert result["order"] == 3  # Should be next in sequence (0, 1, 2, 3)
        assert len(mock_product_with_images.images) == 4

    @patch('services.product_image_service.ProductRepository')
    @patch('services.product_image_service.utc_now')
    def test_add_image_with_explicit_order(
        self, mock_utc_now, mock_repo, mock_db, mock_product_with_images
    ):
        """
        Should use provided display_order when specified.

        Business Rule:
        - If display_order is explicitly provided, use that value
        """
        # Setup mocks
        mock_repo.get_by_id.return_value = mock_product_with_images
        mock_utc_now.return_value = datetime(2026, 1, 8, 12, 0, 0, tzinfo=timezone.utc)

        image_url = "http://cdn.example.com/img4.jpg"

        # Execute with explicit display_order
        result = ProductImageService.add_image(
            mock_db, product_id=1, image_url=image_url, display_order=5
        )

        # Verify
        assert result["order"] == 5  # Should use provided order

    @patch('services.product_image_service.ProductRepository')
    def test_add_image_product_not_found(self, mock_repo, mock_db):
        """
        Should raise ValueError when product does not exist.

        Business Rule:
        - Cannot add image to non-existent product
        """
        # Setup mocks
        mock_repo.get_by_id.return_value = None

        # Execute & Verify
        with pytest.raises(ValueError, match="Product with id 999 not found"):
            ProductImageService.add_image(
                mock_db, product_id=999, image_url="http://cdn.example.com/img.jpg"
            )

    @patch('services.product_image_service.ProductRepository')
    def test_add_image_max_limit_reached(self, mock_repo, mock_db, mock_product_max_images):
        """
        Should raise ValueError when max image limit (20) is reached.

        Business Rule:
        - Maximum 20 images per product (Vinted limit)
        - Cannot add more images when limit is reached
        """
        # Setup mocks
        mock_repo.get_by_id.return_value = mock_product_max_images

        # Execute & Verify
        with pytest.raises(ValueError, match=f"Product already has 20 images \\(max {MAX_IMAGES_PER_PRODUCT}\\)"):
            ProductImageService.add_image(
                mock_db, product_id=1, image_url="http://cdn.example.com/img21.jpg"
            )

    @patch('services.product_image_service.ProductRepository')
    def test_add_image_sold_product_raises_error(self, mock_repo, mock_db, mock_product_sold):
        """
        Should raise ValueError when trying to add image to SOLD product.

        Business Rule:
        - SOLD products are immutable (locked after sale)
        - Cannot add, delete, or modify images on SOLD products
        """
        # Setup mocks
        mock_repo.get_by_id.return_value = mock_product_sold

        # Execute & Verify
        with pytest.raises(ValueError, match="Cannot add images to SOLD product"):
            ProductImageService.add_image(
                mock_db, product_id=1, image_url="http://cdn.example.com/img.jpg"
            )

    @patch('services.product_image_service.ProductRepository')
    @patch('services.product_image_service.utc_now')
    def test_add_image_to_product_with_null_images(self, mock_utc_now, mock_repo, mock_db):
        """
        Should handle product with None images field.

        Business Rule:
        - images field may be None (not yet initialized)
        - Should treat None as empty list
        """
        # Setup mocks
        product = Product(
            id=1,
            title="Test Product",
            description="Test",
            price=49.99,
            category="T-shirt",
            brand="Nike",
            condition=8,
            stock_quantity=1,
            status=ProductStatus.DRAFT,
            images=None,  # Explicitly None
            created_at=datetime.now(timezone.utc),
        )
        mock_repo.get_by_id.return_value = product
        mock_utc_now.return_value = datetime(2026, 1, 8, 12, 0, 0, tzinfo=timezone.utc)

        # Execute
        result = ProductImageService.add_image(
            mock_db, product_id=1, image_url="http://cdn.example.com/img.jpg"
        )

        # Verify
        assert result["order"] == 0
        assert len(product.images) == 1


# =============================================================================
# DELETE IMAGE TESTS
# =============================================================================


class TestDeleteImage:
    """Tests for ProductImageService.delete_image."""

    @patch('services.product_image_service.ProductRepository')
    def test_delete_image_success(self, mock_repo, mock_db, mock_product_with_images):
        """
        Should successfully delete an image by URL.

        Business Rule:
        - Image is removed from the JSONB array
        - db.commit() is called to persist changes
        """
        # Setup mocks
        mock_repo.get_by_id.return_value = mock_product_with_images

        url_to_delete = "http://cdn.example.com/img2.jpg"
        initial_count = len(mock_product_with_images.images)

        # Execute
        result = ProductImageService.delete_image(mock_db, product_id=1, image_url=url_to_delete)

        # Verify
        assert result is True
        assert len(mock_product_with_images.images) == initial_count - 1
        mock_db.commit.assert_called_once()

        # Verify image is actually removed
        remaining_urls = [img["url"] for img in mock_product_with_images.images]
        assert url_to_delete not in remaining_urls

    @patch('services.product_image_service.ProductRepository')
    def test_delete_image_reorders_remaining(self, mock_repo, mock_db, mock_product_with_images):
        """
        Should auto-reorder remaining images after deletion.

        Business Rule:
        - After deleting an image, remaining images are reordered (0, 1, 2, ...)
        - Order is continuous with no gaps
        """
        # Setup mocks
        mock_repo.get_by_id.return_value = mock_product_with_images

        # Delete middle image (order=1)
        url_to_delete = "http://cdn.example.com/img2.jpg"

        # Execute
        ProductImageService.delete_image(mock_db, product_id=1, image_url=url_to_delete)

        # Verify reordering
        assert mock_product_with_images.images[0]["order"] == 0
        assert mock_product_with_images.images[1]["order"] == 1  # Was order=2, now order=1

    @patch('services.product_image_service.ProductRepository')
    def test_delete_image_product_not_found(self, mock_repo, mock_db):
        """
        Should return False when product does not exist.

        Business Rule:
        - Cannot delete image from non-existent product
        - Returns False instead of raising exception
        """
        # Setup mocks
        mock_repo.get_by_id.return_value = None

        # Execute
        result = ProductImageService.delete_image(
            mock_db, product_id=999, image_url="http://cdn.example.com/img.jpg"
        )

        # Verify
        assert result is False

    @patch('services.product_image_service.ProductRepository')
    def test_delete_image_image_not_found(self, mock_repo, mock_db, mock_product_with_images):
        """
        Should return False when image URL does not exist in product.

        Business Rule:
        - Cannot delete an image that doesn't exist
        - Returns False instead of raising exception
        """
        # Setup mocks
        mock_repo.get_by_id.return_value = mock_product_with_images

        # Execute
        result = ProductImageService.delete_image(
            mock_db, product_id=1, image_url="http://cdn.example.com/nonexistent.jpg"
        )

        # Verify
        assert result is False
        mock_db.commit.assert_not_called()

    @patch('services.product_image_service.ProductRepository')
    def test_delete_image_from_product_with_null_images(self, mock_repo, mock_db):
        """
        Should handle product with None images field.

        Business Rule:
        - images field may be None
        - Should return False (image not found)
        """
        # Setup mocks
        product = Product(
            id=1,
            title="Test Product",
            description="Test",
            price=49.99,
            category="T-shirt",
            brand="Nike",
            condition=8,
            stock_quantity=1,
            status=ProductStatus.DRAFT,
            images=None,
            created_at=datetime.now(timezone.utc),
        )
        mock_repo.get_by_id.return_value = product

        # Execute
        result = ProductImageService.delete_image(
            mock_db, product_id=1, image_url="http://cdn.example.com/img.jpg"
        )

        # Verify
        assert result is False

    @patch('services.product_image_service.ProductRepository')
    def test_delete_last_image(self, mock_repo, mock_db):
        """
        Should handle deleting the last image from a product.

        Business Rule:
        - Product can have zero images after deletion
        - Empty list is valid state
        """
        # Setup mocks
        product = Product(
            id=1,
            title="Test Product",
            description="Test",
            price=49.99,
            category="T-shirt",
            brand="Nike",
            condition=8,
            stock_quantity=1,
            status=ProductStatus.DRAFT,
            images=[{"url": "http://cdn.example.com/only-image.jpg", "order": 0, "created_at": "2026-01-01T10:00:00Z"}],
            created_at=datetime.now(timezone.utc),
        )
        mock_repo.get_by_id.return_value = product

        # Execute
        result = ProductImageService.delete_image(
            mock_db, product_id=1, image_url="http://cdn.example.com/only-image.jpg"
        )

        # Verify
        assert result is True
        assert product.images == []


# =============================================================================
# REORDER IMAGES TESTS
# =============================================================================


class TestReorderImages:
    """Tests for ProductImageService.reorder_images."""

    @patch('services.product_image_service.ProductRepository')
    def test_reorder_images_success(self, mock_repo, mock_db, mock_product_with_images):
        """
        Should successfully reorder images based on provided URL order.

        Business Rule:
        - Order in ordered_urls list determines new display_order
        - First URL gets order=0, second gets order=1, etc.
        """
        # Setup mocks
        mock_repo.get_by_id.return_value = mock_product_with_images

        # Reverse the order
        new_order = [
            "http://cdn.example.com/img3.jpg",
            "http://cdn.example.com/img1.jpg",
            "http://cdn.example.com/img2.jpg",
        ]

        # Execute
        result = ProductImageService.reorder_images(mock_db, product_id=1, ordered_urls=new_order)

        # Verify
        assert result is not None
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_product_with_images)

        # Verify new order
        assert mock_product_with_images.images[0]["url"] == "http://cdn.example.com/img3.jpg"
        assert mock_product_with_images.images[0]["order"] == 0
        assert mock_product_with_images.images[1]["url"] == "http://cdn.example.com/img1.jpg"
        assert mock_product_with_images.images[1]["order"] == 1
        assert mock_product_with_images.images[2]["url"] == "http://cdn.example.com/img2.jpg"
        assert mock_product_with_images.images[2]["order"] == 2

    @patch('services.product_image_service.ProductRepository')
    def test_reorder_images_validates_urls(self, mock_repo, mock_db, mock_product_with_images):
        """
        Should raise ValueError when URL doesn't belong to product.

        Business Rule:
        - All URLs in ordered_urls must exist in product's images
        - Prevents accidental inclusion of invalid URLs
        """
        # Setup mocks
        mock_repo.get_by_id.return_value = mock_product_with_images

        # Include a URL that doesn't exist
        invalid_order = [
            "http://cdn.example.com/img1.jpg",
            "http://cdn.example.com/nonexistent.jpg",  # Invalid URL
            "http://cdn.example.com/img2.jpg",
        ]

        # Execute & Verify
        with pytest.raises(ValueError, match="Image URL not found in product 1"):
            ProductImageService.reorder_images(mock_db, product_id=1, ordered_urls=invalid_order)

    @patch('services.product_image_service.ProductRepository')
    def test_reorder_images_product_not_found(self, mock_repo, mock_db):
        """
        Should raise ValueError when product does not exist.

        Business Rule:
        - Cannot reorder images for non-existent product
        """
        # Setup mocks
        mock_repo.get_by_id.return_value = None

        # Execute & Verify
        with pytest.raises(ValueError, match="Product with id 999 not found"):
            ProductImageService.reorder_images(
                mock_db, product_id=999, ordered_urls=["http://cdn.example.com/img.jpg"]
            )

    @patch('services.product_image_service.ProductRepository')
    def test_reorder_images_preserves_metadata(self, mock_repo, mock_db, mock_product_with_images):
        """
        Should preserve image metadata (created_at) during reorder.

        Business Rule:
        - Only the order field should change
        - URL and created_at should be preserved
        """
        # Setup mocks
        mock_repo.get_by_id.return_value = mock_product_with_images

        # Store original created_at values
        original_created_at = {
            img["url"]: img["created_at"] for img in mock_product_with_images.images
        }

        # Reorder
        new_order = [
            "http://cdn.example.com/img2.jpg",
            "http://cdn.example.com/img3.jpg",
            "http://cdn.example.com/img1.jpg",
        ]

        # Execute
        ProductImageService.reorder_images(mock_db, product_id=1, ordered_urls=new_order)

        # Verify metadata preserved
        for img in mock_product_with_images.images:
            assert img["created_at"] == original_created_at[img["url"]]

    @patch('services.product_image_service.ProductRepository')
    def test_reorder_images_empty_list(self, mock_repo, mock_db, mock_product):
        """
        Should handle reordering with empty URL list.

        Business Rule:
        - Empty ordered_urls is valid if product has no images
        """
        # Setup mocks
        mock_repo.get_by_id.return_value = mock_product

        # Execute
        result = ProductImageService.reorder_images(mock_db, product_id=1, ordered_urls=[])

        # Verify
        assert result is not None
        mock_db.commit.assert_called_once()

    @patch('services.product_image_service.ProductRepository')
    def test_reorder_images_partial_urls(self, mock_repo, mock_db, mock_product_with_images):
        """
        Should allow reordering subset of images.

        Business Rule:
        - ordered_urls can contain only some of the product's images
        - Only images in ordered_urls will be in the result
        Note: This test documents current behavior - partial reorder is allowed
        """
        # Setup mocks
        mock_repo.get_by_id.return_value = mock_product_with_images

        # Only include 2 of 3 images
        partial_order = [
            "http://cdn.example.com/img1.jpg",
            "http://cdn.example.com/img3.jpg",
        ]

        # Execute
        result = ProductImageService.reorder_images(mock_db, product_id=1, ordered_urls=partial_order)

        # Verify - only included images remain
        assert len(mock_product_with_images.images) == 2


# =============================================================================
# GET IMAGES TESTS
# =============================================================================


class TestGetImages:
    """Tests for ProductImageService.get_images."""

    @patch('services.product_image_service.ProductRepository')
    def test_get_images_success(self, mock_repo, mock_db, mock_product_with_images):
        """Should return all images for a product."""
        # Setup mocks
        mock_repo.get_by_id.return_value = mock_product_with_images

        # Execute
        result = ProductImageService.get_images(mock_db, product_id=1)

        # Verify
        assert len(result) == 3
        assert result[0]["url"] == "http://cdn.example.com/img1.jpg"

    @patch('services.product_image_service.ProductRepository')
    def test_get_images_product_not_found(self, mock_repo, mock_db):
        """Should return empty list when product not found."""
        # Setup mocks
        mock_repo.get_by_id.return_value = None

        # Execute
        result = ProductImageService.get_images(mock_db, product_id=999)

        # Verify
        assert result == []

    @patch('services.product_image_service.ProductRepository')
    def test_get_images_null_images(self, mock_repo, mock_db):
        """Should return empty list when images is None."""
        # Setup mocks
        product = Product(
            id=1,
            title="Test",
            description="Test",
            price=49.99,
            category="T-shirt",
            brand="Nike",
            condition=8,
            stock_quantity=1,
            status=ProductStatus.DRAFT,
            images=None,
            created_at=datetime.now(timezone.utc),
        )
        mock_repo.get_by_id.return_value = product

        # Execute
        result = ProductImageService.get_images(mock_db, product_id=1)

        # Verify
        assert result == []


# =============================================================================
# GET IMAGE COUNT TESTS
# =============================================================================


class TestGetImageCount:
    """Tests for ProductImageService.get_image_count."""

    @patch('services.product_image_service.ProductRepository')
    def test_get_image_count_success(self, mock_repo, mock_db, mock_product_with_images):
        """Should return correct image count."""
        # Setup mocks
        mock_repo.get_by_id.return_value = mock_product_with_images

        # Execute
        result = ProductImageService.get_image_count(mock_db, product_id=1)

        # Verify
        assert result == 3

    @patch('services.product_image_service.ProductRepository')
    def test_get_image_count_product_not_found(self, mock_repo, mock_db):
        """Should return 0 when product not found."""
        # Setup mocks
        mock_repo.get_by_id.return_value = None

        # Execute
        result = ProductImageService.get_image_count(mock_db, product_id=999)

        # Verify
        assert result == 0

    @patch('services.product_image_service.ProductRepository')
    def test_get_image_count_null_images(self, mock_repo, mock_db):
        """Should return 0 when images is None."""
        # Setup mocks
        product = Product(
            id=1,
            title="Test",
            description="Test",
            price=49.99,
            category="T-shirt",
            brand="Nike",
            condition=8,
            stock_quantity=1,
            status=ProductStatus.DRAFT,
            images=None,
            created_at=datetime.now(timezone.utc),
        )
        mock_repo.get_by_id.return_value = product

        # Execute
        result = ProductImageService.get_image_count(mock_db, product_id=1)

        # Verify
        assert result == 0

    @patch('services.product_image_service.ProductRepository')
    def test_get_image_count_max_images(self, mock_repo, mock_db, mock_product_max_images):
        """Should return MAX_IMAGES_PER_PRODUCT for product at limit."""
        # Setup mocks
        mock_repo.get_by_id.return_value = mock_product_max_images

        # Execute
        result = ProductImageService.get_image_count(mock_db, product_id=1)

        # Verify
        assert result == MAX_IMAGES_PER_PRODUCT


# =============================================================================
# EDGE CASES AND CONSTANTS
# =============================================================================


class TestConstants:
    """Tests for module constants."""

    def test_max_images_per_product_value(self):
        """Verify MAX_IMAGES_PER_PRODUCT is 20 (Vinted limit)."""
        assert MAX_IMAGES_PER_PRODUCT == 20
