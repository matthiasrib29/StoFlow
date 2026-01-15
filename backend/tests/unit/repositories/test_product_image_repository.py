"""
Unit tests for ProductImageRepository.

Tests CRUD operations on product_images table.
Uses PostgreSQL test database with multi-tenant schemas.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from models.user.product import Product, ProductStatus
from models.user.product_image import ProductImage
from repositories.product_image_repository import ProductImageRepository

# Get engine from conftest
from tests.conftest import TestingSessionLocal


@pytest.fixture(scope="function")
def db_session():
    """
    Session DB with schema_translate_map configured for user_1 schema.

    Overrides the global db_session fixture from conftest to add
    schema_translate_map support for multi-tenant models.
    """
    # Get engine from TestingSessionLocal
    engine = TestingSessionLocal.kw.get('bind')
    if engine is None:
        temp_session = TestingSessionLocal()
        engine = temp_session.bind
        temp_session.close()

    # Create connection with schema_translate_map
    # This maps 'tenant' → 'user_1' for all models with schema='tenant'
    connection = engine.connect().execution_options(
        schema_translate_map={"tenant": "user_1"}
    )

    # Create session bound to this connection
    session = Session(bind=connection)

    try:
        # Also set search_path for queries (fallback for non-tenant tables)
        session.execute(text("SET search_path TO user_1, public"))
        session.commit()

        yield session
    finally:
        session.close()
        connection.close()


@pytest.fixture
def test_product(db_session: Session) -> Product:
    """
    Create a test product in user_1 schema.

    Returns:
        Product instance with id
    """
    product = Product(
        title="Test Product",
        description="Test description for repository tests",
        price=25.99,
        stock_quantity=5,
        category="T-shirt",
        brand="Nike",
        condition="EXCELLENT",
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def test_images(db_session: Session, test_product: Product) -> list[ProductImage]:
    """
    Create test images for a product.

    Creates 3 images:
    - 2 photos (is_label=False, order=0,1)
    - 1 label (is_label=True, order=2)

    Returns:
        List of ProductImage instances
    """
    images = [
        ProductImage(
            product_id=test_product.id,
            url="https://cdn.stoflow.io/1/img1.jpg",
            order=0,
            is_label=False,
            mime_type="image/jpeg",
            file_size=245678,
            width=1200,
            height=1600,
        ),
        ProductImage(
            product_id=test_product.id,
            url="https://cdn.stoflow.io/1/img2.jpg",
            order=1,
            is_label=False,
            alt_text="Back view",
            tags=["back", "product"],
        ),
        ProductImage(
            product_id=test_product.id,
            url="https://cdn.stoflow.io/1/label.jpg",
            order=2,
            is_label=True,
            alt_text="Price tag",
            tags=["label"],
        ),
    ]
    db_session.add_all(images)
    db_session.commit()
    for img in images:
        db_session.refresh(img)
    return images


# ===== GET OPERATIONS =====


def test_get_by_id_exists(db_session: Session, test_images: list[ProductImage]):
    """Test get_by_id returns ProductImage when it exists."""
    image = test_images[0]
    result = ProductImageRepository.get_by_id(db_session, image.id)

    assert result is not None
    assert result.id == image.id
    assert result.url == image.url
    assert result.product_id == image.product_id


def test_get_by_id_not_found(db_session: Session):
    """Test get_by_id returns None when image doesn't exist."""
    result = ProductImageRepository.get_by_id(db_session, 99999)
    assert result is None


def test_get_by_product_returns_ordered(
    db_session: Session, test_product: Product, test_images: list[ProductImage]
):
    """Test get_by_product returns all images ordered by order ASC."""
    results = ProductImageRepository.get_by_product(db_session, test_product.id)

    assert len(results) == 3
    assert results[0].order == 0
    assert results[1].order == 1
    assert results[2].order == 2
    assert results[0].url == test_images[0].url
    assert results[1].url == test_images[1].url
    assert results[2].url == test_images[2].url


def test_get_by_product_empty(db_session: Session, test_product: Product):
    """Test get_by_product returns empty list when product has no images."""
    # Delete all images first
    db_session.query(ProductImage).filter_by(product_id=test_product.id).delete()
    db_session.commit()

    results = ProductImageRepository.get_by_product(db_session, test_product.id)
    assert results == []


def test_get_photos_only_filters_labels(
    db_session: Session, test_product: Product, test_images: list[ProductImage]
):
    """Test get_photos_only returns only photos (excludes labels)."""
    results = ProductImageRepository.get_photos_only(db_session, test_product.id)

    assert len(results) == 2
    assert all(not img.is_label for img in results)
    assert results[0].url == test_images[0].url
    assert results[1].url == test_images[1].url


def test_get_label_returns_single(
    db_session: Session, test_product: Product, test_images: list[ProductImage]
):
    """Test get_label returns the label image."""
    result = ProductImageRepository.get_label(db_session, test_product.id)

    assert result is not None
    assert result.is_label is True
    assert result.url == test_images[2].url


def test_get_label_not_found(db_session: Session, test_product: Product):
    """Test get_label returns None when no label exists."""
    # Create product with only photos
    image = ProductImage(
        product_id=test_product.id,
        url="https://cdn.stoflow.io/1/photo.jpg",
        order=0,
        is_label=False,
    )
    db_session.add(image)
    db_session.commit()

    result = ProductImageRepository.get_label(db_session, test_product.id)
    assert result is None


# ===== CREATE OPERATION =====


def test_create_image(db_session: Session, test_product: Product):
    """Test create() inserts a new image."""
    image = ProductImageRepository.create(
        db_session,
        product_id=test_product.id,
        url="https://cdn.stoflow.io/1/new.jpg",
        order=0,
        is_label=False,
        mime_type="image/jpeg",
        file_size=123456,
        width=800,
        height=1200,
        alt_text="Test image",
        tags=["front", "product"],
    )
    db_session.commit()
    db_session.refresh(image)

    assert image.id is not None
    assert image.product_id == test_product.id
    assert image.url == "https://cdn.stoflow.io/1/new.jpg"
    assert image.order == 0
    assert image.is_label is False
    assert image.mime_type == "image/jpeg"
    assert image.file_size == 123456
    assert image.width == 800
    assert image.height == 1200
    assert image.alt_text == "Test image"
    assert image.tags == ["front", "product"]


def test_create_image_minimal_fields(db_session: Session, test_product: Product):
    """Test create() works with minimal required fields."""
    image = ProductImageRepository.create(
        db_session,
        product_id=test_product.id,
        url="https://cdn.stoflow.io/1/minimal.jpg",
        order=0,
    )
    db_session.commit()
    db_session.refresh(image)

    assert image.id is not None
    assert image.product_id == test_product.id
    assert image.url == "https://cdn.stoflow.io/1/minimal.jpg"
    assert image.order == 0
    assert image.is_label is False  # Default value
    assert image.alt_text is None
    assert image.tags is None


# ===== DELETE OPERATION =====


def test_delete_image(db_session: Session, test_images: list[ProductImage]):
    """Test delete() removes an image."""
    image_id = test_images[0].id

    result = ProductImageRepository.delete(db_session, image_id)
    db_session.commit()

    assert result is True

    # Verify image no longer exists
    deleted_image = ProductImageRepository.get_by_id(db_session, image_id)
    assert deleted_image is None


def test_delete_nonexistent(db_session: Session):
    """Test delete() returns False when image doesn't exist."""
    result = ProductImageRepository.delete(db_session, 99999)
    assert result is False


# ===== UPDATE OPERATIONS =====


def test_update_order(db_session: Session, test_images: list[ProductImage]):
    """Test update_order() changes display order."""
    image = test_images[0]
    original_order = image.order

    updated = ProductImageRepository.update_order(db_session, image.id, 5)
    db_session.commit()

    assert updated is not None
    assert updated.id == image.id
    assert updated.order == 5
    assert updated.order != original_order


def test_update_order_nonexistent(db_session: Session):
    """Test update_order() returns None when image doesn't exist."""
    result = ProductImageRepository.update_order(db_session, 99999, 10)
    assert result is None


def test_set_label_flag_to_true(db_session: Session, test_images: list[ProductImage]):
    """Test set_label_flag() sets is_label to True."""
    photo = test_images[0]  # Originally a photo
    assert photo.is_label is False

    updated = ProductImageRepository.set_label_flag(db_session, photo.id, True)
    db_session.commit()

    assert updated is not None
    assert updated.id == photo.id
    assert updated.is_label is True


def test_set_label_flag_to_false(db_session: Session, test_images: list[ProductImage]):
    """Test set_label_flag() sets is_label to False."""
    label = test_images[2]  # Originally a label
    assert label.is_label is True

    updated = ProductImageRepository.set_label_flag(db_session, label.id, False)
    db_session.commit()

    assert updated is not None
    assert updated.id == label.id
    assert updated.is_label is False


def test_set_label_flag_nonexistent(db_session: Session):
    """Test set_label_flag() returns None when image doesn't exist."""
    result = ProductImageRepository.set_label_flag(db_session, 99999, True)
    assert result is None
