"""
Unit Tests for ProductImageService

Tests product image operations using product_images table.

Business Rules Tested:
- Maximum 20 images per product (Vinted limit)
- Cannot add images to SOLD products
- Auto-calculate display_order when not provided
- Auto-reorder remaining images after deletion
- Validate URLs during reorder operation
- Only one label per product allowed
- Photos vs labels distinction

Refactored: 2026-01-15 (Phase 3.2)
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch

from models.user.product import Product, ProductStatus
from models.user.product_image import ProductImage
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
    """Mock Product instance."""
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
        created_at=datetime.now(timezone.utc),
    )
    return product


@pytest.fixture
def mock_product_images():
    """Mock ProductImage instances."""
    return [
        ProductImage(
            id=1,
            product_id=1,
            url="http://cdn.example.com/img1.jpg",
            order=0,
            is_label=False,
            created_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        ),
        ProductImage(
            id=2,
            product_id=1,
            url="http://cdn.example.com/img2.jpg",
            order=1,
            is_label=False,
            created_at=datetime(2026, 1, 1, 10, 1, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 1, 10, 1, 0, tzinfo=timezone.utc),
        ),
        ProductImage(
            id=3,
            product_id=1,
            url="http://cdn.example.com/img3.jpg",
            order=2,
            is_label=False,
            created_at=datetime(2026, 1, 1, 10, 2, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 1, 10, 2, 0, tzinfo=timezone.utc),
        ),
    ]


@pytest.fixture
def mock_product_images_with_label():
    """Mock ProductImage instances with label."""
    return [
        ProductImage(
            id=1,
            product_id=1,
            url="http://cdn.example.com/photo1.jpg",
            order=0,
            is_label=False,
            created_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        ),
        ProductImage(
            id=2,
            product_id=1,
            url="http://cdn.example.com/photo2.jpg",
            order=1,
            is_label=False,
            created_at=datetime(2026, 1, 1, 10, 1, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 1, 10, 1, 0, tzinfo=timezone.utc),
        ),
        ProductImage(
            id=3,
            product_id=1,
            url="http://cdn.example.com/label.jpg",
            order=2,
            is_label=True,
            created_at=datetime(2026, 1, 1, 10, 2, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 1, 10, 2, 0, tzinfo=timezone.utc),
        ),
    ]


# =============================================================================
# ADD IMAGE TESTS
# =============================================================================


class TestAddImage:
    """Tests for ProductImageService.add_image."""

    @patch('services.product_image_service.ProductRepository')
    @patch('services.product_image_service.ProductImageRepository')
    def test_add_image_success(self, mock_img_repo, mock_prod_repo, mock_db, mock_product):
        """
        Should successfully add an image to a product.

        Business Rule:
        - Image is created in product_images table
        - Returns dict with image data
        """
        # Setup mocks
        mock_prod_repo.get_by_id.return_value = mock_product
        mock_img_repo.get_by_product.return_value = []  # No existing images

        new_image = ProductImage(
            id=1,
            product_id=1,
            url="http://cdn.example.com/new-image.jpg",
            order=0,
            is_label=False,
            created_at=datetime(2026, 1, 8, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 8, 12, 0, 0, tzinfo=timezone.utc),
        )
        mock_img_repo.create.return_value = new_image

        image_url = "http://cdn.example.com/new-image.jpg"

        # Execute
        result = ProductImageService.add_image(mock_db, product_id=1, image_url=image_url)

        # Verify
        assert result is not None
        assert result["url"] == image_url
        assert result["order"] == 0  # First image
        assert result["id"] == 1
        mock_prod_repo.get_by_id.assert_called_once_with(mock_db, 1)
        mock_img_repo.create.assert_called_once()
        mock_db.flush.assert_called_once()

    @patch('services.product_image_service.ProductRepository')
    @patch('services.product_image_service.ProductImageRepository')
    def test_add_image_auto_calculates_order(
        self, mock_img_repo, mock_prod_repo, mock_db, mock_product, mock_product_images
    ):
        """
        Should auto-calculate display_order when not provided.

        Business Rule:
        - If display_order is None, calculate as len(existing_images)
        - New image is appended at the end
        """
        # Setup mocks
        mock_prod_repo.get_by_id.return_value = mock_product
        mock_img_repo.get_by_product.return_value = mock_product_images  # 3 existing images

        new_image = ProductImage(
            id=4,
            product_id=1,
            url="http://cdn.example.com/img4.jpg",
            order=3,
            is_label=False,
            created_at=datetime(2026, 1, 8, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 8, 12, 0, 0, tzinfo=timezone.utc),
        )
        mock_img_repo.create.return_value = new_image

        # Execute (display_order=None by default)
        result = ProductImageService.add_image(mock_db, product_id=1, image_url="http://cdn.example.com/img4.jpg")

        # Verify
        assert result["order"] == 3  # Should be next in sequence (0, 1, 2, 3)

    @patch('services.product_image_service.ProductRepository')
    @patch('services.product_image_service.ProductImageRepository')
    def test_add_image_with_metadata(self, mock_img_repo, mock_prod_repo, mock_db, mock_product):
        """
        Should pass metadata kwargs to repository.

        Business Rule:
        - Metadata (mime_type, file_size, width, height, etc.) is preserved
        """
        # Setup mocks
        mock_prod_repo.get_by_id.return_value = mock_product
        mock_img_repo.get_by_product.return_value = []

        new_image = ProductImage(
            id=1,
            product_id=1,
            url="http://cdn.example.com/img.jpg",
            order=0,
            is_label=False,
            mime_type="image/jpeg",
            file_size=102400,
            width=1920,
            height=1080,
            alt_text="Product photo",
            tags=["front", "detail"],
            created_at=datetime(2026, 1, 8, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 8, 12, 0, 0, tzinfo=timezone.utc),
        )
        mock_img_repo.create.return_value = new_image

        # Execute
        result = ProductImageService.add_image(
            mock_db,
            product_id=1,
            image_url="http://cdn.example.com/img.jpg",
            mime_type="image/jpeg",
            file_size=102400,
            width=1920,
            height=1080,
            alt_text="Product photo",
            tags=["front", "detail"],
        )

        # Verify metadata in result
        assert result["mime_type"] == "image/jpeg"
        assert result["file_size"] == 102400
        assert result["width"] == 1920
        assert result["height"] == 1080
        assert result["alt_text"] == "Product photo"
        assert result["tags"] == ["front", "detail"]

    @patch('services.product_image_service.ProductRepository')
    def test_add_image_product_not_found(self, mock_prod_repo, mock_db):
        """
        Should raise ValueError when product does not exist.
        """
        mock_prod_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match="Product with id 999 not found"):
            ProductImageService.add_image(
                mock_db, product_id=999, image_url="http://cdn.example.com/img.jpg"
            )

    @patch('services.product_image_service.ProductRepository')
    @patch('services.product_image_service.ProductImageRepository')
    def test_add_image_max_limit_reached(self, mock_img_repo, mock_prod_repo, mock_db, mock_product):
        """
        Should raise ValueError when max image limit (20) is reached.
        """
        mock_prod_repo.get_by_id.return_value = mock_product
        # Return 20 images
        max_images = [
            ProductImage(id=i, product_id=1, url=f"http://cdn.example.com/img{i}.jpg", order=i, is_label=False)
            for i in range(MAX_IMAGES_PER_PRODUCT)
        ]
        mock_img_repo.get_by_product.return_value = max_images

        with pytest.raises(ValueError, match=f"Product already has 20 images \\(max {MAX_IMAGES_PER_PRODUCT}\\)"):
            ProductImageService.add_image(
                mock_db, product_id=1, image_url="http://cdn.example.com/img21.jpg"
            )

    @patch('services.product_image_service.ProductRepository')
    def test_add_image_sold_product_raises_error(self, mock_prod_repo, mock_db, mock_product_sold):
        """
        Should raise ValueError when trying to add image to SOLD product.
        """
        mock_prod_repo.get_by_id.return_value = mock_product_sold

        with pytest.raises(ValueError, match="Cannot add images to SOLD product"):
            ProductImageService.add_image(
                mock_db, product_id=1, image_url="http://cdn.example.com/img.jpg"
            )


# =============================================================================
# DELETE IMAGE TESTS
# =============================================================================


class TestDeleteImage:
    """Tests for ProductImageService.delete_image."""

    @patch('services.product_image_service.ProductRepository')
    @patch('services.product_image_service.ProductImageRepository')
    def test_delete_image_success(self, mock_img_repo, mock_prod_repo, mock_db, mock_product, mock_product_images):
        """
        Should successfully delete an image by URL.
        """
        mock_prod_repo.get_by_id.return_value = mock_product
        mock_img_repo.get_by_product.return_value = mock_product_images

        url_to_delete = "http://cdn.example.com/img2.jpg"

        # Execute
        result = ProductImageService.delete_image(mock_db, product_id=1, image_url=url_to_delete)

        # Verify
        assert result is True
        mock_img_repo.delete.assert_called_once_with(mock_db, 2)  # ID of img2
        mock_db.commit.assert_called_once()

    @patch('services.product_image_service.ProductRepository')
    @patch('services.product_image_service.ProductImageRepository')
    def test_delete_image_reorders_remaining(self, mock_img_repo, mock_prod_repo, mock_db, mock_product, mock_product_images):
        """
        Should auto-reorder remaining images after deletion.
        """
        mock_prod_repo.get_by_id.return_value = mock_product
        mock_img_repo.get_by_product.return_value = mock_product_images

        # Delete middle image (order=1, id=2)
        url_to_delete = "http://cdn.example.com/img2.jpg"

        # Execute
        ProductImageService.delete_image(mock_db, product_id=1, image_url=url_to_delete)

        # Verify reordering calls
        # img1 (id=1) stays at order=0
        # img3 (id=3) moves from order=2 to order=1
        mock_img_repo.update_order.assert_any_call(mock_db, 3, 1)

    @patch('services.product_image_service.ProductRepository')
    def test_delete_image_product_not_found(self, mock_prod_repo, mock_db):
        """
        Should return False when product does not exist.
        """
        mock_prod_repo.get_by_id.return_value = None

        result = ProductImageService.delete_image(
            mock_db, product_id=999, image_url="http://cdn.example.com/img.jpg"
        )

        assert result is False

    @patch('services.product_image_service.ProductRepository')
    @patch('services.product_image_service.ProductImageRepository')
    def test_delete_image_image_not_found(self, mock_img_repo, mock_prod_repo, mock_db, mock_product, mock_product_images):
        """
        Should return False when image URL does not exist in product.
        """
        mock_prod_repo.get_by_id.return_value = mock_product
        mock_img_repo.get_by_product.return_value = mock_product_images

        result = ProductImageService.delete_image(
            mock_db, product_id=1, image_url="http://cdn.example.com/nonexistent.jpg"
        )

        assert result is False
        mock_db.commit.assert_not_called()


# =============================================================================
# REORDER IMAGES TESTS
# =============================================================================


class TestReorderImages:
    """Tests for ProductImageService.reorder_images."""

    @patch('services.product_image_service.ProductRepository')
    @patch('services.product_image_service.ProductImageRepository')
    def test_reorder_images_success(self, mock_img_repo, mock_prod_repo, mock_db, mock_product, mock_product_images):
        """
        Should successfully reorder images based on provided URL order.
        """
        mock_prod_repo.get_by_id.return_value = mock_product
        mock_img_repo.get_by_product.side_effect = [
            mock_product_images,  # Initial call
            mock_product_images[::-1],  # After reorder (reversed)
        ]

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
        assert len(result) == 3
        mock_db.commit.assert_called_once()

    @patch('services.product_image_service.ProductRepository')
    @patch('services.product_image_service.ProductImageRepository')
    def test_reorder_images_validates_urls(self, mock_img_repo, mock_prod_repo, mock_db, mock_product, mock_product_images):
        """
        Should raise ValueError when URL doesn't belong to product.
        """
        mock_prod_repo.get_by_id.return_value = mock_product
        mock_img_repo.get_by_product.return_value = mock_product_images

        invalid_order = [
            "http://cdn.example.com/img1.jpg",
            "http://cdn.example.com/nonexistent.jpg",
            "http://cdn.example.com/img2.jpg",
        ]

        with pytest.raises(ValueError, match="Image URL not found in product 1"):
            ProductImageService.reorder_images(mock_db, product_id=1, ordered_urls=invalid_order)

    @patch('services.product_image_service.ProductRepository')
    def test_reorder_images_product_not_found(self, mock_prod_repo, mock_db):
        """
        Should raise ValueError when product does not exist.
        """
        mock_prod_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match="Product with id 999 not found"):
            ProductImageService.reorder_images(
                mock_db, product_id=999, ordered_urls=["http://cdn.example.com/img.jpg"]
            )


# =============================================================================
# GET IMAGES TESTS
# =============================================================================


class TestGetImages:
    """Tests for ProductImageService.get_images."""

    @patch('services.product_image_service.ProductRepository')
    @patch('services.product_image_service.ProductImageRepository')
    def test_get_images_success(self, mock_img_repo, mock_prod_repo, mock_db, mock_product, mock_product_images):
        """Should return all images for a product."""
        mock_prod_repo.get_by_id.return_value = mock_product
        mock_img_repo.get_by_product.return_value = mock_product_images

        result = ProductImageService.get_images(mock_db, product_id=1)

        assert len(result) == 3
        assert result[0]["url"] == "http://cdn.example.com/img1.jpg"
        assert result[0]["order"] == 0

    @patch('services.product_image_service.ProductRepository')
    def test_get_images_product_not_found(self, mock_prod_repo, mock_db):
        """Should return empty list when product not found."""
        mock_prod_repo.get_by_id.return_value = None

        result = ProductImageService.get_images(mock_db, product_id=999)

        assert result == []


# =============================================================================
# GET IMAGE COUNT TESTS
# =============================================================================


class TestGetImageCount:
    """Tests for ProductImageService.get_image_count."""

    @patch('services.product_image_service.ProductRepository')
    @patch('services.product_image_service.ProductImageRepository')
    def test_get_image_count_success(self, mock_img_repo, mock_prod_repo, mock_db, mock_product, mock_product_images):
        """Should return correct image count."""
        mock_prod_repo.get_by_id.return_value = mock_product
        mock_img_repo.get_by_product.return_value = mock_product_images

        result = ProductImageService.get_image_count(mock_db, product_id=1)

        assert result == 3

    @patch('services.product_image_service.ProductRepository')
    def test_get_image_count_product_not_found(self, mock_prod_repo, mock_db):
        """Should return 0 when product not found."""
        mock_prod_repo.get_by_id.return_value = None

        result = ProductImageService.get_image_count(mock_db, product_id=999)

        assert result == 0


# =============================================================================
# PHOTO/LABEL DISTINCTION TESTS
# =============================================================================


class TestGetProductPhotos:
    """Tests for ProductImageService.get_product_photos."""

    @patch('services.product_image_service.ProductRepository')
    @patch('services.product_image_service.ProductImageRepository')
    def test_get_product_photos_filters_labels(
        self, mock_img_repo, mock_prod_repo, mock_db, mock_product, mock_product_images_with_label
    ):
        """
        Should return only photos, excluding labels.
        """
        mock_prod_repo.get_by_id.return_value = mock_product
        # Repository should return only photos (is_label=False)
        photos_only = [img for img in mock_product_images_with_label if not img.is_label]
        mock_img_repo.get_photos_only.return_value = photos_only

        result = ProductImageService.get_product_photos(mock_db, product_id=1)

        assert len(result) == 2
        assert all(not img["is_label"] for img in result)
        assert result[0]["url"] == "http://cdn.example.com/photo1.jpg"
        assert result[1]["url"] == "http://cdn.example.com/photo2.jpg"


class TestGetLabelImage:
    """Tests for ProductImageService.get_label_image."""

    @patch('services.product_image_service.ProductRepository')
    @patch('services.product_image_service.ProductImageRepository')
    def test_get_label_image_returns_single(
        self, mock_img_repo, mock_prod_repo, mock_db, mock_product, mock_product_images_with_label
    ):
        """
        Should return label image if exists.
        """
        mock_prod_repo.get_by_id.return_value = mock_product
        label = next(img for img in mock_product_images_with_label if img.is_label)
        mock_img_repo.get_label.return_value = label

        result = ProductImageService.get_label_image(mock_db, product_id=1)

        assert result is not None
        assert result["is_label"] is True
        assert result["url"] == "http://cdn.example.com/label.jpg"

    @patch('services.product_image_service.ProductRepository')
    @patch('services.product_image_service.ProductImageRepository')
    def test_get_label_image_returns_none(self, mock_img_repo, mock_prod_repo, mock_db, mock_product):
        """
        Should return None if no label exists.
        """
        mock_prod_repo.get_by_id.return_value = mock_product
        mock_img_repo.get_label.return_value = None

        result = ProductImageService.get_label_image(mock_db, product_id=1)

        assert result is None


class TestSetLabelFlag:
    """Tests for ProductImageService.set_label_flag."""

    @patch('services.product_image_service.ProductRepository')
    @patch('services.product_image_service.ProductImageRepository')
    def test_set_label_flag_unsets_previous(self, mock_img_repo, mock_prod_repo, mock_db):
        """
        Should unset previous label when setting new one.

        Business Rule:
        - Only one label per product allowed
        - Setting new label unsets existing label first
        """
        # Setup: existing label with id=3
        existing_label = ProductImage(
            id=3, product_id=1, url="http://cdn.example.com/old-label.jpg",
            order=2, is_label=True,
            created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
        )

        # New image to be set as label
        new_label = ProductImage(
            id=1, product_id=1, url="http://cdn.example.com/photo1.jpg",
            order=0, is_label=False,
            created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
        )
        new_label_updated = ProductImage(
            id=1, product_id=1, url="http://cdn.example.com/photo1.jpg",
            order=0, is_label=True,
            created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
        )

        mock_img_repo.get_by_id.return_value = new_label
        mock_img_repo.get_label.return_value = existing_label
        mock_img_repo.set_label_flag.return_value = new_label_updated

        # Execute
        result = ProductImageService.set_label_flag(mock_db, product_id=1, image_id=1, is_label=True)

        # Verify
        # Should unset old label first
        mock_img_repo.set_label_flag.assert_any_call(mock_db, 3, False)
        # Then set new label
        mock_img_repo.set_label_flag.assert_any_call(mock_db, 1, True)
        assert result["is_label"] is True
        mock_db.commit.assert_called_once()

    @patch('services.product_image_service.ProductImageRepository')
    def test_set_label_flag_image_not_found(self, mock_img_repo, mock_db):
        """
        Should raise ValueError when image doesn't exist.
        """
        mock_img_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match="Image 999 not found in product 1"):
            ProductImageService.set_label_flag(mock_db, product_id=1, image_id=999, is_label=True)

    @patch('services.product_image_service.ProductImageRepository')
    def test_set_label_flag_wrong_product(self, mock_img_repo, mock_db):
        """
        Should raise ValueError when image belongs to different product.
        """
        wrong_product_image = ProductImage(
            id=1, product_id=2, url="http://cdn.example.com/img.jpg",
            order=0, is_label=False,
            created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
        )
        mock_img_repo.get_by_id.return_value = wrong_product_image

        with pytest.raises(ValueError, match="Image 1 not found in product 1"):
            ProductImageService.set_label_flag(mock_db, product_id=1, image_id=1, is_label=True)


# =============================================================================
# CONSTANTS TESTS
# =============================================================================


class TestConstants:
    """Tests for module constants."""

    def test_max_images_per_product_value(self):
        """Verify MAX_IMAGES_PER_PRODUCT is 20 (Vinted limit)."""
        assert MAX_IMAGES_PER_PRODUCT == 20
