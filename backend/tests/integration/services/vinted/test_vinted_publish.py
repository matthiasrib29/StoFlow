"""
Integration Tests: Vinted Image Upload with Label Filtering

Tests that upload_product_images() correctly excludes label images (is_label=true)
when uploading to Vinted marketplace.

Author: Claude
Date: 2026-01-15
Phase: 4.1 - Vinted Marketplace Integration
"""
import pytest
from unittest.mock import patch, AsyncMock
from sqlalchemy.orm import Session

from models.user.product import Product
from services.product_image_service import ProductImageService
from services.vinted.vinted_product_helpers import upload_product_images


@pytest.mark.asyncio
class TestVintedImageUploadWithLabels:
    """Test suite for Vinted image upload label filtering."""

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
            title="Test Product for Vinted Upload",
            description="Test product with photos and label",
            price=29.99,
            stock_quantity=1,
            category="t-shirt"
        )
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)

        # Add 3 photos (regular images)
        ProductImageService.add_image(
            db=db_session,
            product_id=product.id,
            url="https://example.com/photo1.jpg",
            is_label=False,
            order=0,
            alt_text="Photo 1"
        )
        ProductImageService.add_image(
            db=db_session,
            product_id=product.id,
            url="https://example.com/photo2.jpg",
            is_label=False,
            order=1,
            alt_text="Photo 2"
        )
        ProductImageService.add_image(
            db=db_session,
            product_id=product.id,
            url="https://example.com/photo3.jpg",
            is_label=False,
            order=2,
            alt_text="Photo 3"
        )

        # Add 1 label (internal price tag - should be excluded)
        ProductImageService.add_image(
            db=db_session,
            product_id=product.id,
            url="https://example.com/label.jpg",
            is_label=True,
            order=3,
            alt_text="Internal price tag"
        )

        db_session.commit()
        db_session.refresh(product)

        return product

    async def test_upload_images_excludes_labels(
        self,
        db_session: Session,
        test_user,
        test_product_with_images: Product
    ):
        """
        Test that upload_product_images() excludes label images from Vinted upload.

        Given: Product with 3 photos + 1 label
        When: upload_product_images() is called
        Then:
        - Only 3 images are uploaded (label excluded)
        - Plugin HTTP call is made exactly 3 times (not 4)
        - Uploaded URLs match only the 3 photo URLs
        - Label URL is not in uploaded images
        """
        product = test_product_with_images

        # Mock plugin WebSocket call to return fake Vinted photo IDs
        with patch(
            'services.vinted.vinted_product_helpers.PluginWebSocketHelper.call_plugin',
            new_callable=AsyncMock
        ) as mock_call:
            # Return fake Vinted photo IDs (12345, 12346, 12347)
            mock_call.side_effect = [
                {'id': 12345},  # Photo 1
                {'id': 12346},  # Photo 2
                {'id': 12347},  # Photo 3
                # Label should never be uploaded (no 4th call)
            ]

            # Execute upload
            photo_ids = await upload_product_images(
                db=db_session,
                product=product,
                user_id=test_user.id
            )

            # Assert: Only 3 photos uploaded (label excluded)
            assert len(photo_ids) == 3, \
                f"Expected 3 photo IDs, got {len(photo_ids)}"

            # Assert: Plugin HTTP call made exactly 3 times
            assert mock_call.call_count == 3, \
                f"Expected 3 HTTP calls to plugin, got {mock_call.call_count}"

            # Assert: Correct photo IDs returned
            assert photo_ids == [12345, 12346, 12347], \
                f"Expected [12345, 12346, 12347], got {photo_ids}"

            # Assert: Uploaded URLs are only photo URLs (not label)
            uploaded_urls = [
                call.kwargs['payload']['image_url']
                for call in mock_call.call_args_list
            ]
            expected_urls = [
                "https://example.com/photo1.jpg",
                "https://example.com/photo2.jpg",
                "https://example.com/photo3.jpg"
            ]
            assert uploaded_urls == expected_urls, \
                f"Uploaded URLs do not match. Expected {expected_urls}, got {uploaded_urls}"

            # Assert: Label URL is NOT in uploaded images
            label_url = "https://example.com/label.jpg"
            assert label_url not in uploaded_urls, \
                f"Label URL {label_url} should not be uploaded to Vinted"

    async def test_upload_images_with_only_labels(
        self,
        db_session: Session,
        test_user
    ):
        """
        Test edge case: Product with ONLY label images (no photos).

        Given: Product with 1 label (no photos)
        When: upload_product_images() is called
        Then:
        - No images are uploaded (empty list)
        - Plugin HTTP call is never made
        - Warning is logged (no images found)
        """
        # Create product
        product = Product(
            title="Product with Only Label",
            description="Edge case: only internal price tag, no photos",
            price=19.99,
            stock_quantity=1,
            category="jeans"
        )
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)

        # Add only 1 label (no photos)
        ProductImageService.add_image(
            db=db_session,
            product_id=product.id,
            url="https://example.com/label_only.jpg",
            is_label=True,
            order=0,
            alt_text="Only a label"
        )
        db_session.commit()
        db_session.refresh(product)

        # Mock plugin call
        with patch(
            'services.vinted.vinted_product_helpers.PluginWebSocketHelper.call_plugin',
            new_callable=AsyncMock
        ) as mock_call:
            # Execute upload
            photo_ids = await upload_product_images(
                db=db_session,
                product=product,
                user_id=test_user.id
            )

            # Assert: No images uploaded
            assert len(photo_ids) == 0, \
                f"Expected 0 photo IDs (no photos), got {len(photo_ids)}"

            # Assert: Plugin HTTP call never made
            assert mock_call.call_count == 0, \
                f"Expected 0 HTTP calls (no photos), got {mock_call.call_count}"

    async def test_upload_images_with_no_images(
        self,
        db_session: Session,
        test_user
    ):
        """
        Test edge case: Product with NO images at all.

        Given: Product with no images
        When: upload_product_images() is called
        Then:
        - No images are uploaded (empty list)
        - Plugin HTTP call is never made
        - Warning is logged (no images found)
        """
        # Create product with no images
        product = Product(
            title="Product with No Images",
            description="Edge case: no images at all",
            price=9.99,
            stock_quantity=1,
            category="shoes"
        )
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)

        # Mock plugin call
        with patch(
            'services.vinted.vinted_product_helpers.PluginWebSocketHelper.call_plugin',
            new_callable=AsyncMock
        ) as mock_call:
            # Execute upload
            photo_ids = await upload_product_images(
                db=db_session,
                product=product,
                user_id=test_user.id
            )

            # Assert: No images uploaded
            assert len(photo_ids) == 0, \
                f"Expected 0 photo IDs (no images), got {len(photo_ids)}"

            # Assert: Plugin HTTP call never made
            assert mock_call.call_count == 0, \
                f"Expected 0 HTTP calls (no images), got {mock_call.call_count}"

    async def test_upload_images_maintains_order(
        self,
        db_session: Session,
        test_user,
        test_product_with_images: Product
    ):
        """
        Test that image order is preserved when labels are filtered.

        Given: Product with photos (order 0, 1, 2) and label (order 3)
        When: upload_product_images() is called
        Then:
        - Photos are uploaded in correct order (0, 1, 2)
        - Label at order 3 is skipped
        - Order integrity is maintained in returned photo IDs
        """
        product = test_product_with_images

        # Mock plugin call
        with patch(
            'services.vinted.vinted_product_helpers.PluginWebSocketHelper.call_plugin',
            new_callable=AsyncMock
        ) as mock_call:
            # Return fake Vinted photo IDs in order
            mock_call.side_effect = [
                {'id': 100},  # Photo at order 0
                {'id': 101},  # Photo at order 1
                {'id': 102},  # Photo at order 2
            ]

            # Execute upload
            photo_ids = await upload_product_images(
                db=db_session,
                product=product,
                user_id=test_user.id
            )

            # Assert: Photo IDs in correct order
            assert photo_ids == [100, 101, 102], \
                f"Photo order not preserved. Expected [100, 101, 102], got {photo_ids}"

            # Assert: URLs uploaded in correct order
            uploaded_urls = [
                call.kwargs['payload']['image_url']
                for call in mock_call.call_args_list
            ]
            expected_order = [
                "https://example.com/photo1.jpg",
                "https://example.com/photo2.jpg",
                "https://example.com/photo3.jpg"
            ]
            assert uploaded_urls == expected_order, \
                f"Upload order not preserved. Expected {expected_order}, got {uploaded_urls}"
