"""
Unit Tests for FileService

Tests file upload operations including image validation, optimization, and R2 storage.

Business Rules Tested:
- MAX_FILE_SIZE = 10MB (before optimization)
- ALLOWED_EXTENSIONS = {jpg, jpeg, png}
- MAX_IMAGES_PER_PRODUCT = 20
- Image optimization: resize max 2000px, JPEG quality 90%
- WebP support for URL imports (converted to JPEG)
- Format detection using magic bytes

Coverage:
- _detect_image_format: JPEG, PNG, WebP detection
- _optimize_image: resize, compress, RGBA->RGB conversion
- upload_image: validation and upload flow
- download_and_upload_from_url: external URL import

Created: 2026-01-08
Phase 1.1: Unit testing
"""

import pytest
from io import BytesIO
from unittest.mock import Mock, MagicMock, patch, AsyncMock

from services.file_service import FileService


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_r2_service():
    """Mock R2 service for storage operations."""
    with patch('services.file_service.r2_service') as mock:
        mock.is_available = True
        mock.upload_image = AsyncMock(
            return_value="https://cdn.stoflow.io/1/products/1/abc123.jpeg"
        )
        yield mock


@pytest.fixture
def mock_upload_file():
    """Mock FastAPI UploadFile."""
    file = MagicMock()
    file.filename = "test_image.jpg"
    file.read = AsyncMock()
    file.seek = AsyncMock()
    return file


@pytest.fixture
def mock_db():
    """Mock database session."""
    session = MagicMock()
    session.query = Mock()
    return session


@pytest.fixture
def jpeg_magic_bytes():
    """Valid JPEG magic bytes (header)."""
    # JPEG starts with FF D8 FF followed by marker
    return b'\xff\xd8\xff\xe0' + b'\x00' * 100


@pytest.fixture
def png_magic_bytes():
    """Valid PNG magic bytes (header)."""
    # PNG signature: 89 50 4E 47 0D 0A 1A 0A
    return b'\x89PNG\r\n\x1a\n' + b'\x00' * 100


@pytest.fixture
def webp_magic_bytes():
    """Valid WebP magic bytes (header)."""
    # WebP: RIFF....WEBP
    return b'RIFF' + b'\x00\x00\x00\x00' + b'WEBP' + b'\x00' * 100


@pytest.fixture
def mock_pil_image():
    """Mock PIL Image for optimization tests."""
    with patch('services.file_service.Image') as mock_image:
        mock_img = MagicMock()
        mock_img.mode = "RGB"
        mock_img.size = (1000, 800)
        mock_img.resize.return_value = mock_img
        mock_img.convert.return_value = mock_img
        mock_img.split.return_value = [MagicMock()] * 4

        mock_image.open.return_value = mock_img
        mock_image.new.return_value = mock_img
        mock_image.Resampling.LANCZOS = 1

        yield mock_image, mock_img


# =============================================================================
# IMAGE FORMAT DETECTION TESTS
# =============================================================================


class TestDetectImageFormat:
    """Tests for FileService._detect_image_format."""

    def test_detect_image_format_jpeg(self, jpeg_magic_bytes):
        """Should detect JPEG format from magic bytes."""
        result = FileService._detect_image_format(jpeg_magic_bytes)

        assert result == "jpeg"

    def test_detect_image_format_png(self, png_magic_bytes):
        """Should detect PNG format from magic bytes."""
        result = FileService._detect_image_format(png_magic_bytes)

        assert result == "png"

    def test_detect_image_format_webp(self, webp_magic_bytes):
        """Should detect WebP format from magic bytes."""
        result = FileService._detect_image_format(webp_magic_bytes)

        assert result == "webp"

    def test_detect_image_format_unknown(self):
        """Should return None for unknown/invalid format."""
        # Random bytes that don't match any known format
        unknown_bytes = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c'

        result = FileService._detect_image_format(unknown_bytes)

        assert result is None

    def test_detect_image_format_too_short(self):
        """Should return None if content too short (< 12 bytes)."""
        short_content = b'\xff\xd8\xff'  # Only 3 bytes

        result = FileService._detect_image_format(short_content)

        assert result is None

    def test_detect_image_format_empty(self):
        """Should return None for empty content."""
        result = FileService._detect_image_format(b'')

        assert result is None


# =============================================================================
# IMAGE OPTIMIZATION TESTS
# =============================================================================


class TestOptimizeImage:
    """Tests for FileService._optimize_image."""

    def test_optimize_image_resizes_large(self, mock_pil_image):
        """Should resize images larger than MAX_DIMENSION (2000px)."""
        mock_image_class, mock_img = mock_pil_image
        # Image larger than 2000px
        mock_img.size = (3000, 2400)

        # Mock the save operation
        def mock_save(output, format, quality, optimize):
            output.write(b'optimized_content')

        mock_img.save.side_effect = mock_save

        content = b'original_image_content_here' * 100
        result, output_format = FileService._optimize_image(content, "jpeg")

        # Should have called resize
        mock_img.resize.assert_called_once()
        # Check resize was called with correct ratio
        call_args = mock_img.resize.call_args
        new_size = call_args[0][0]
        # Max dimension should be 2000
        assert max(new_size) <= FileService.MAX_DIMENSION

    def test_optimize_image_compresses(self, mock_pil_image):
        """Should compress image to JPEG with quality setting."""
        mock_image_class, mock_img = mock_pil_image
        mock_img.size = (1000, 800)  # Already within limits

        def mock_save(output, format, quality, optimize):
            output.write(b'compressed')

        mock_img.save.side_effect = mock_save

        content = b'original_content' * 100
        result, output_format = FileService._optimize_image(content, "png")

        # Should save as JPEG with compression
        mock_img.save.assert_called_once()
        call_kwargs = mock_img.save.call_args[1]
        assert call_kwargs['format'] == "JPEG"
        assert call_kwargs['quality'] == FileService.JPEG_QUALITY
        assert call_kwargs['optimize'] is True
        assert output_format == "jpeg"

    def test_optimize_image_converts_rgba_to_rgb(self, mock_pil_image):
        """Should convert RGBA images to RGB (for PNG with transparency)."""
        mock_image_class, mock_img = mock_pil_image
        mock_img.mode = "RGBA"
        mock_img.size = (800, 600)

        # Create mock background with same size
        mock_background = MagicMock()
        mock_background.size = (800, 600)
        mock_background.mode = "RGB"
        mock_image_class.new.return_value = mock_background

        def mock_save(output, format, quality, optimize):
            output.write(b'rgb_content')

        mock_background.save.side_effect = mock_save

        content = b'rgba_image_content' * 100
        result, output_format = FileService._optimize_image(content, "png")

        # Should create white background
        mock_image_class.new.assert_called_once_with("RGB", mock_img.size, (255, 255, 255))
        # Should paste onto background
        mock_background.paste.assert_called_once()

    def test_optimize_image_converts_palette_mode(self, mock_pil_image):
        """Should convert palette mode (P) images via RGBA to RGB."""
        mock_image_class, mock_img = mock_pil_image
        mock_img.mode = "P"
        mock_img.size = (800, 600)

        # Mock convert to return a new mock with RGBA mode
        mock_rgba_img = MagicMock()
        mock_rgba_img.split.return_value = [MagicMock()] * 4
        mock_img.convert.return_value = mock_rgba_img

        # Create mock background with same size
        mock_background = MagicMock()
        mock_background.size = (800, 600)
        mock_background.mode = "RGB"
        mock_image_class.new.return_value = mock_background

        def mock_save(output, format, quality, optimize):
            output.write(b'converted')

        mock_background.save.side_effect = mock_save

        content = b'palette_image' * 100
        result, output_format = FileService._optimize_image(content, "png")

        # Should convert P to RGBA first
        mock_img.convert.assert_called_with("RGBA")

    def test_optimize_image_does_not_enlarge_small_images(self, mock_pil_image):
        """Should not enlarge images smaller than MAX_DIMENSION."""
        mock_image_class, mock_img = mock_pil_image
        mock_img.size = (500, 400)  # Small image
        mock_img.mode = "RGB"

        def mock_save(output, format, quality, optimize):
            output.write(b'small')

        mock_img.save.side_effect = mock_save

        content = b'small_image' * 100
        result, output_format = FileService._optimize_image(content, "jpeg")

        # Should NOT call resize
        mock_img.resize.assert_not_called()


# =============================================================================
# UPLOAD IMAGE TESTS
# =============================================================================


class TestUploadImage:
    """Tests for FileService.save_product_image (upload flow)."""

    @pytest.mark.asyncio
    async def test_upload_image_success(self, mock_r2_service, mock_upload_file, jpeg_magic_bytes):
        """Should successfully upload a valid image."""
        # Setup file mock
        mock_upload_file.filename = "product_photo.jpg"
        mock_upload_file.read = AsyncMock(side_effect=[
            jpeg_magic_bytes[:512],  # First read for format detection
            jpeg_magic_bytes,        # Full read for content
        ])

        with patch.object(FileService, '_optimize_image') as mock_optimize:
            mock_optimize.return_value = (b'optimized', 'jpeg')

            result = await FileService.save_product_image(
                user_id=1,
                product_id=123,
                file=mock_upload_file
            )

        assert result == "https://cdn.stoflow.io/1/products/1/abc123.jpeg"
        mock_r2_service.upload_image.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_image_file_too_large(self, mock_r2_service, mock_upload_file, jpeg_magic_bytes):
        """Should raise ValueError when file exceeds MAX_FILE_SIZE (10MB)."""
        mock_upload_file.filename = "large_image.jpg"

        # Create content larger than 10MB
        large_content = b'\xff' * (FileService.MAX_FILE_SIZE + 1)

        mock_upload_file.read = AsyncMock(side_effect=[
            jpeg_magic_bytes[:512],  # First read for format detection
            large_content,           # Full read - too large
        ])

        with pytest.raises(ValueError, match="File too large"):
            await FileService.save_product_image(
                user_id=1,
                product_id=123,
                file=mock_upload_file
            )

    @pytest.mark.asyncio
    async def test_upload_image_invalid_extension(self, mock_r2_service, mock_upload_file):
        """Should raise ValueError for disallowed file extension."""
        mock_upload_file.filename = "document.pdf"

        with pytest.raises(ValueError, match="Invalid file extension"):
            await FileService.save_product_image(
                user_id=1,
                product_id=123,
                file=mock_upload_file
            )

    @pytest.mark.asyncio
    async def test_upload_image_gif_not_allowed(self, mock_r2_service, mock_upload_file):
        """Should reject GIF files (not in ALLOWED_EXTENSIONS)."""
        mock_upload_file.filename = "animation.gif"

        with pytest.raises(ValueError, match="Invalid file extension"):
            await FileService.save_product_image(
                user_id=1,
                product_id=123,
                file=mock_upload_file
            )

    @pytest.mark.asyncio
    async def test_upload_image_r2_not_configured(self, mock_upload_file):
        """Should raise RuntimeError when R2 is not available."""
        with patch('services.file_service.r2_service') as mock_r2:
            mock_r2.is_available = False

            with pytest.raises(RuntimeError, match="R2 storage not configured"):
                await FileService.save_product_image(
                    user_id=1,
                    product_id=123,
                    file=mock_upload_file
                )

    @pytest.mark.asyncio
    async def test_upload_image_extension_format_mismatch(
        self, mock_r2_service, mock_upload_file, png_magic_bytes
    ):
        """Should reject when file extension doesn't match actual format."""
        # File claims to be JPEG but is actually PNG
        mock_upload_file.filename = "fake_jpeg.jpg"
        mock_upload_file.read = AsyncMock(side_effect=[
            png_magic_bytes[:512],  # PNG magic bytes
            png_magic_bytes,
        ])

        with pytest.raises(ValueError, match="does not match actual format"):
            await FileService.save_product_image(
                user_id=1,
                product_id=123,
                file=mock_upload_file
            )

    @pytest.mark.asyncio
    async def test_upload_image_empty_file(self, mock_r2_service, mock_upload_file, jpeg_magic_bytes):
        """Should reject empty files."""
        mock_upload_file.filename = "empty.jpg"
        mock_upload_file.read = AsyncMock(side_effect=[
            jpeg_magic_bytes[:512],  # First read OK
            b'',                     # Empty content
        ])

        with pytest.raises(ValueError, match="File is empty"):
            await FileService.save_product_image(
                user_id=1,
                product_id=123,
                file=mock_upload_file
            )

    @pytest.mark.asyncio
    async def test_upload_image_no_filename(self, mock_r2_service, mock_upload_file):
        """Should reject files without filename."""
        mock_upload_file.filename = None

        with pytest.raises(ValueError, match="Filename is missing"):
            await FileService.save_product_image(
                user_id=1,
                product_id=123,
                file=mock_upload_file
            )


# =============================================================================
# VALIDATE IMAGE COUNT TESTS
# =============================================================================


class TestValidateImageCount:
    """Tests for FileService.validate_image_count."""

    def test_upload_image_max_images_exceeded(self, mock_db):
        """Should raise ValueError when product has >= 20 images."""
        # Mock product with 20 images already
        mock_product = MagicMock()
        mock_product.images = [f"img_{i}.jpg" for i in range(20)]

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_product
        mock_db.query.return_value = mock_query

        with pytest.raises(ValueError, match="already has 20 images"):
            FileService.validate_image_count(mock_db, product_id=1)

    def test_validate_image_count_product_not_found(self, mock_db):
        """Should raise ValueError when product doesn't exist."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        with pytest.raises(ValueError, match="Product with id .* not found"):
            FileService.validate_image_count(mock_db, product_id=999)

    def test_validate_image_count_under_limit(self, mock_db):
        """Should pass when product has fewer than 20 images."""
        mock_product = MagicMock()
        mock_product.images = ["img_1.jpg", "img_2.jpg"]  # Only 2 images

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_product
        mock_db.query.return_value = mock_query

        # Should not raise
        FileService.validate_image_count(mock_db, product_id=1)

    def test_validate_image_count_empty_images(self, mock_db):
        """Should pass when product has no images."""
        mock_product = MagicMock()
        mock_product.images = []

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_product
        mock_db.query.return_value = mock_query

        # Should not raise
        FileService.validate_image_count(mock_db, product_id=1)

    def test_validate_image_count_none_images(self, mock_db):
        """Should pass when product.images is None."""
        mock_product = MagicMock()
        mock_product.images = None

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_product
        mock_db.query.return_value = mock_query

        # Should not raise (None treated as empty)
        FileService.validate_image_count(mock_db, product_id=1)


# =============================================================================
# DOWNLOAD AND UPLOAD FROM URL TESTS
# =============================================================================


class TestDownloadAndUploadFromUrl:
    """Tests for FileService.download_and_upload_from_url."""

    @pytest.mark.asyncio
    async def test_download_and_upload_from_url_success(self, mock_r2_service, jpeg_magic_bytes):
        """Should download image from URL and upload to R2."""
        mock_response = MagicMock()
        mock_response.content = jpeg_magic_bytes
        mock_response.raise_for_status = MagicMock()

        with patch('services.file_service.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            with patch.object(FileService, '_optimize_image') as mock_optimize:
                mock_optimize.return_value = (b'optimized', 'jpeg')

                result = await FileService.download_and_upload_from_url(
                    user_id=1,
                    product_id=123,
                    image_url="https://vinted.fr/images/product.jpg"
                )

        assert result == "https://cdn.stoflow.io/1/products/1/abc123.jpeg"
        mock_r2_service.upload_image.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_and_upload_from_url_converts_webp(
        self, mock_r2_service, webp_magic_bytes
    ):
        """Should convert WebP images to JPEG during import."""
        mock_response = MagicMock()
        mock_response.content = webp_magic_bytes
        mock_response.raise_for_status = MagicMock()

        with patch('services.file_service.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            with patch.object(FileService, '_optimize_image') as mock_optimize:
                # _optimize_image converts WebP to JPEG
                mock_optimize.return_value = (b'jpeg_content', 'jpeg')

                result = await FileService.download_and_upload_from_url(
                    user_id=1,
                    product_id=123,
                    image_url="https://vinted.fr/images/product.webp"
                )

        # Should call optimize with webp format
        mock_optimize.assert_called_once()
        call_args = mock_optimize.call_args
        assert call_args[0][1] == "webp"  # original format

        # Should upload as JPEG
        upload_call = mock_r2_service.upload_image.call_args
        assert upload_call[1]['content_type'] == "image/jpeg"

    @pytest.mark.asyncio
    async def test_download_and_upload_from_url_handles_network_error(self, mock_r2_service):
        """Should raise RuntimeError on network/HTTP errors."""
        import httpx

        with patch('services.file_service.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("Connection timeout")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            with pytest.raises(RuntimeError, match="Timeout"):
                await FileService.download_and_upload_from_url(
                    user_id=1,
                    product_id=123,
                    image_url="https://slow-server.com/image.jpg"
                )

    @pytest.mark.asyncio
    async def test_download_and_upload_from_url_handles_http_error(self, mock_r2_service):
        """Should raise RuntimeError on HTTP status errors (404, 500, etc.)."""
        import httpx

        with patch('services.file_service.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()

            # Create mock response and error
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.get.side_effect = httpx.HTTPStatusError(
                "Not Found",
                request=MagicMock(),
                response=mock_response
            )
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            with pytest.raises(RuntimeError, match="HTTP error 404"):
                await FileService.download_and_upload_from_url(
                    user_id=1,
                    product_id=123,
                    image_url="https://example.com/missing.jpg"
                )

    @pytest.mark.asyncio
    async def test_download_and_upload_from_url_r2_not_configured(self):
        """Should raise RuntimeError when R2 is not available."""
        with patch('services.file_service.r2_service') as mock_r2:
            mock_r2.is_available = False

            with pytest.raises(RuntimeError, match="R2 storage not configured"):
                await FileService.download_and_upload_from_url(
                    user_id=1,
                    product_id=123,
                    image_url="https://example.com/image.jpg"
                )

    @pytest.mark.asyncio
    async def test_download_and_upload_from_url_empty_content(self, mock_r2_service):
        """Should raise ValueError when downloaded content is empty."""
        mock_response = MagicMock()
        mock_response.content = b''  # Empty
        mock_response.raise_for_status = MagicMock()

        with patch('services.file_service.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            with pytest.raises(ValueError, match="Downloaded image is empty"):
                await FileService.download_and_upload_from_url(
                    user_id=1,
                    product_id=123,
                    image_url="https://example.com/empty.jpg"
                )

    @pytest.mark.asyncio
    async def test_download_and_upload_from_url_file_too_large(
        self, mock_r2_service, jpeg_magic_bytes
    ):
        """Should raise ValueError when downloaded file exceeds MAX_FILE_SIZE."""
        # Create content larger than 10MB
        large_content = jpeg_magic_bytes + (b'\x00' * (FileService.MAX_FILE_SIZE + 1))

        mock_response = MagicMock()
        mock_response.content = large_content
        mock_response.raise_for_status = MagicMock()

        with patch('services.file_service.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            with pytest.raises(ValueError, match="Downloaded image too large"):
                await FileService.download_and_upload_from_url(
                    user_id=1,
                    product_id=123,
                    image_url="https://example.com/huge.jpg"
                )

    @pytest.mark.asyncio
    async def test_download_and_upload_from_url_invalid_format(self, mock_r2_service):
        """Should raise ValueError for unsupported image formats."""
        # GIF magic bytes (not supported for URL import)
        gif_bytes = b'GIF89a' + b'\x00' * 100

        mock_response = MagicMock()
        mock_response.content = gif_bytes
        mock_response.raise_for_status = MagicMock()

        with patch('services.file_service.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            with pytest.raises(ValueError, match="Invalid image format from URL"):
                await FileService.download_and_upload_from_url(
                    user_id=1,
                    product_id=123,
                    image_url="https://example.com/animation.gif"
                )


# =============================================================================
# CONSTANTS AND CONFIGURATION TESTS
# =============================================================================


class TestFileServiceConstants:
    """Tests for FileService constants and configuration."""

    def test_max_file_size_is_10mb(self):
        """MAX_FILE_SIZE should be 10MB."""
        expected = 10 * 1024 * 1024  # 10MB in bytes
        assert FileService.MAX_FILE_SIZE == expected

    def test_allowed_extensions(self):
        """ALLOWED_EXTENSIONS should contain jpg, jpeg, png."""
        expected = {"jpg", "jpeg", "png"}
        assert FileService.ALLOWED_EXTENSIONS == expected

    def test_max_images_per_product(self):
        """MAX_IMAGES_PER_PRODUCT should be 20."""
        assert FileService.MAX_IMAGES_PER_PRODUCT == 20

    def test_max_dimension(self):
        """MAX_DIMENSION should be 2000px."""
        assert FileService.MAX_DIMENSION == 2000

    def test_jpeg_quality(self):
        """JPEG_QUALITY should be 90."""
        assert FileService.JPEG_QUALITY == 90

    def test_url_import_formats(self):
        """URL_IMPORT_FORMATS should include jpeg, png, webp."""
        expected = {"jpeg", "png", "webp"}
        assert FileService.URL_IMPORT_FORMATS == expected
