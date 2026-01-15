"""
Integration Tests: eBay Conversion with Label Filtering

Tests that EbayProductConversionService correctly excludes label images (is_label=true)
when converting products to eBay inventory items.

Author: Claude
Date: 2026-01-15
Phase: 4.2 - eBay Marketplace Integration
"""
import pytest
from sqlalchemy.orm import Session

from models.user.product import Product
from services.product_image_service import ProductImageService
from services.ebay.ebay_product_conversion_service import EbayProductConversionService


@pytest.mark.asyncio
class TestEbayConversionWithLabels:
    """Test suite for eBay conversion label filtering."""

    @pytest.fixture
    def test_product_with_images(self, db_session: Session, test_user) -> Product:
        """
        Create a product with 3 photos + 1 label for testing.

        Structure:
        - Image 1: order=0, is_label=False (photo)
        - Image 2: order=1, is_label=False (photo)
        - Image 3: order=2, is_label=False (photo)
        - Image 4: order=3, is_label=True (label - should be excluded)
        """
        # Create product
        product = Product(
            title="Test Product for eBay Conversion",
            description="Test product with photos and label",
            price=49.99,
            stock_quantity=5,
            category="shoes"
        )
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)

        # Add 3 photos (regular images)
        ProductImageService.add_image(
            db=db_session,
            product_id=product.id,
            url="https://example.com/ebay-photo1.jpg",
            is_label=False,
            order=0,
            alt_text="Photo 1"
        )
        ProductImageService.add_image(
            db=db_session,
            product_id=product.id,
            url="https://example.com/ebay-photo2.jpg",
            is_label=False,
            order=1,
            alt_text="Photo 2"
        )
        ProductImageService.add_image(
            db=db_session,
            product_id=product.id,
            url="https://example.com/ebay-photo3.jpg",
            is_label=False,
            order=2,
            alt_text="Photo 3"
        )

        # Add 1 label (internal price tag - should be excluded)
        ProductImageService.add_image(
            db=db_session,
            product_id=product.id,
            url="https://example.com/ebay-label.jpg",
            is_label=True,
            order=3,
            alt_text="Internal price tag"
        )

        db_session.commit()
        db_session.refresh(product)

        return product

    def test_get_image_urls_excludes_labels(
        self,
        db_session: Session,
        test_user,
        test_product_with_images: Product
    ):
        """
        Test that _get_image_urls() excludes label images from eBay conversion.

        Given: Product with 3 photos + 1 label
        When: _get_image_urls() is called
        Then:
        - Only 3 image URLs are returned (label excluded)
        - Returned URLs match only the 3 photo URLs
        - Label URL is not in the returned list
        """
        product = test_product_with_images

        # Given: EbayProductConversionService
        service = EbayProductConversionService(db_session, user_id=test_user.id)

        # When: Get image URLs
        urls = service._get_image_urls(product)

        # Then: Only 3 photo URLs returned (label excluded)
        assert len(urls) == 3, \
            f"Expected 3 photo URLs, got {len(urls)}"

        # Verify URLs match only photos
        expected_urls = [
            "https://example.com/ebay-photo1.jpg",
            "https://example.com/ebay-photo2.jpg",
            "https://example.com/ebay-photo3.jpg"
        ]
        assert urls == expected_urls, \
            f"URLs do not match. Expected {expected_urls}, got {urls}"

        # Assert: Label URL is NOT in returned list
        label_url = "https://example.com/ebay-label.jpg"
        assert label_url not in urls, \
            f"Label URL {label_url} should not be in eBay image URLs"

    def test_convert_to_inventory_item_excludes_labels(
        self,
        db_session: Session,
        test_user,
        test_product_with_images: Product
    ):
        """
        Test that convert_to_inventory_item() excludes labels from imageUrls.

        Given: Product with 3 photos + 1 label
        When: convert_to_inventory_item() is called
        Then:
        - inventory_item['product']['imageUrls'] has only 3 URLs
        - Label URL is not in imageUrls array
        """
        product = test_product_with_images

        # Given: EbayProductConversionService
        service = EbayProductConversionService(db_session, user_id=test_user.id)

        # When: Convert to eBay inventory item
        inventory_item = service.convert_to_inventory_item(
            product=product,
            sku="TEST-EBAY-001",
            marketplace_id="EBAY_FR"
        )

        # Then: imageUrls has only 3 URLs (label excluded)
        image_urls = inventory_item.get("product", {}).get("imageUrls", [])
        assert len(image_urls) == 3, \
            f"Expected 3 image URLs in inventory item, got {len(image_urls)}"

        # Verify label URL not present
        label_url = "https://example.com/ebay-label.jpg"
        assert label_url not in image_urls, \
            f"Label URL {label_url} should not be in eBay inventory item imageUrls"

        # Verify photo URLs are present
        expected_urls = [
            "https://example.com/ebay-photo1.jpg",
            "https://example.com/ebay-photo2.jpg",
            "https://example.com/ebay-photo3.jpg"
        ]
        assert image_urls == expected_urls, \
            f"Image URLs in inventory item do not match expected. Got {image_urls}"

    def test_respects_ebay_12_image_limit_without_labels(
        self,
        db_session: Session,
        test_user
    ):
        """
        Test that eBay 12-image limit is respected after filtering labels.

        Given: Product with 13 photos + 1 label
        When: _get_image_urls() is called
        Then: Returns exactly 12 URLs (label excluded from count)
        """
        # Create product
        product = Product(
            title="Product with Many Images",
            description="Test 12-image limit",
            price=99.99,
            stock_quantity=1,
            category="clothing"
        )
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)

        # Add 13 photos
        for i in range(13):
            ProductImageService.add_image(
                db=db_session,
                product_id=product.id,
                url=f"https://example.com/photo{i+1}.jpg",
                is_label=False,
                order=i
            )

        # Add 1 label (should be excluded)
        ProductImageService.add_image(
            db=db_session,
            product_id=product.id,
            url="https://example.com/label-many.jpg",
            is_label=True,
            order=13
        )

        db_session.commit()
        db_session.refresh(product)

        # Given: EbayProductConversionService
        service = EbayProductConversionService(db_session, user_id=test_user.id)

        # When: Get image URLs
        urls = service._get_image_urls(product)

        # Then: Exactly 12 URLs returned (label excluded, limit applied)
        assert len(urls) == 12, \
            f"Expected 12 URLs (eBay limit), got {len(urls)}"

        # Verify label not in returned URLs
        label_url = "https://example.com/label-many.jpg"
        assert label_url not in urls, \
            "Label should not be in eBay URLs even with 12+ photos"

        # Verify first 12 photo URLs are returned
        expected_urls = [f"https://example.com/photo{i+1}.jpg" for i in range(12)]
        assert urls == expected_urls, \
            f"URLs do not match first 12 photos. Got {urls}"

    def test_get_image_urls_with_only_labels(
        self,
        db_session: Session,
        test_user
    ):
        """
        Test edge case: Product with ONLY label images (no photos).

        Given: Product with 1 label (no photos)
        When: _get_image_urls() is called
        Then: Returns empty list (no images to send to eBay)
        """
        # Create product
        product = Product(
            title="Product with Only Label",
            description="Edge case: only internal price tag, no photos",
            price=29.99,
            stock_quantity=1,
            category="accessories"
        )
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)

        # Add only 1 label (no photos)
        ProductImageService.add_image(
            db=db_session,
            product_id=product.id,
            url="https://example.com/only-label.jpg",
            is_label=True,
            order=0
        )

        db_session.commit()
        db_session.refresh(product)

        # Given: EbayProductConversionService
        service = EbayProductConversionService(db_session, user_id=test_user.id)

        # When: Get image URLs
        urls = service._get_image_urls(product)

        # Then: Empty list returned (no photos)
        assert len(urls) == 0, \
            f"Expected 0 URLs (no photos), got {len(urls)}"

    def test_get_image_urls_with_no_images(
        self,
        db_session: Session,
        test_user
    ):
        """
        Test edge case: Product with NO images at all.

        Given: Product with no images
        When: _get_image_urls() is called
        Then: Returns empty list
        """
        # Create product with no images
        product = Product(
            title="Product with No Images",
            description="Edge case: no images at all",
            price=19.99,
            stock_quantity=1,
            category="books"
        )
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)

        # Given: EbayProductConversionService
        service = EbayProductConversionService(db_session, user_id=test_user.id)

        # When: Get image URLs
        urls = service._get_image_urls(product)

        # Then: Empty list returned
        assert len(urls) == 0, \
            f"Expected 0 URLs (no images), got {len(urls)}"
