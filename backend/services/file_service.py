"""
File Service

Service pour la gestion des uploads de fichiers (images produits).

Business Rules (2025-12-23):
- Stockage: Cloudflare R2 (S3-compatible) - REQUIS
- Formats autorisés: jpg, jpeg, png
- Taille max: 10MB par image (avant optimisation)
- Maximum 20 images par produit (limite Vinted)
- Optimisation: redimensionnement max 2000px, compression 90%
"""

import imghdr
from io import BytesIO
from typing import Tuple

from fastapi import UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from models.user.product import Product
from services.r2_service import r2_service
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class FileService:
    """Service pour gérer les uploads de fichiers vers R2."""

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB (before optimization)
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
    MAX_IMAGES_PER_PRODUCT = 20

    # Image optimization settings
    MAX_DIMENSION = 2000  # Max width or height in pixels
    JPEG_QUALITY = 90  # Compression quality (1-100)

    @staticmethod
    def _optimize_image(content: bytes, original_format: str) -> Tuple[bytes, str]:
        """
        Optimize image: resize if too large, compress.

        Args:
            content: Original image bytes
            original_format: 'jpeg' or 'png'

        Returns:
            Tuple of (optimized_bytes, output_format)
        """
        img = Image.open(BytesIO(content))
        original_size = len(content)

        # Convert RGBA to RGB for JPEG (PNG with transparency)
        if img.mode in ("RGBA", "P"):
            # Create white background for transparent images
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
            img = background

        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Resize if larger than MAX_DIMENSION
        width, height = img.size
        if width > FileService.MAX_DIMENSION or height > FileService.MAX_DIMENSION:
            ratio = min(
                FileService.MAX_DIMENSION / width,
                FileService.MAX_DIMENSION / height
            )
            new_size = (int(width * ratio), int(height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            logger.info(
                f"[FileService] Image resized: {width}x{height} -> {new_size[0]}x{new_size[1]}"
            )

        # Save as JPEG with compression
        output = BytesIO()
        img.save(output, format="JPEG", quality=FileService.JPEG_QUALITY, optimize=True)
        optimized_content = output.getvalue()

        optimized_size = len(optimized_content)
        savings = ((original_size - optimized_size) / original_size) * 100
        logger.info(
            f"[FileService] Image optimized: {original_size/1024:.1f}KB -> "
            f"{optimized_size/1024:.1f}KB ({savings:.1f}% saved)"
        )

        return optimized_content, "jpeg"

    @staticmethod
    async def _validate_and_optimize(file: UploadFile) -> Tuple[bytes, str, str]:
        """
        Validate and optimize image file.

        Args:
            file: Uploaded file

        Returns:
            Tuple of (optimized_bytes, extension, content_type)

        Raises:
            ValueError: If validation fails
        """
        if not file.filename:
            raise ValueError("Filename is missing")

        extension = file.filename.split(".")[-1].lower()
        if extension not in FileService.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Invalid file extension: {extension}. "
                f"Allowed: {', '.join(FileService.ALLOWED_EXTENSIONS)}"
            )

        # Validate real format (anti-spoofing)
        content = await file.read(512)
        await file.seek(0)

        image_type = imghdr.what(None, content)
        if image_type not in ["jpeg", "png"]:
            raise ValueError(
                f"Invalid image format: {image_type}. File may be corrupted or not a valid image."
            )

        # Check extension matches real format
        if (extension in ["jpg", "jpeg"] and image_type != "jpeg") or (
            extension == "png" and image_type != "png"
        ):
            raise ValueError(
                f"File extension '{extension}' does not match actual format '{image_type}'"
            )

        # Validate size (before optimization)
        content_full = await file.read()
        file_size = len(content_full)

        if file_size > FileService.MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            max_mb = FileService.MAX_FILE_SIZE / (1024 * 1024)
            raise ValueError(f"File too large: {size_mb:.2f}MB (max {max_mb}MB)")

        if file_size == 0:
            raise ValueError("File is empty")

        # Optimize image (resize + compress)
        optimized_content, output_format = FileService._optimize_image(
            content_full, image_type
        )

        return optimized_content, output_format, "image/jpeg"

    @staticmethod
    async def save_product_image(
        user_id: int, product_id: int, file: UploadFile
    ) -> str:
        """
        Save product image to Cloudflare R2.

        Args:
            user_id: User ID for path isolation
            product_id: Product ID
            file: Uploaded file (FastAPI UploadFile)

        Returns:
            str: R2 public URL

        Raises:
            ValueError: If validation fails
            RuntimeError: If R2 is not configured
        """
        if not r2_service.is_available:
            raise RuntimeError(
                "R2 storage not configured. Set R2_ACCESS_KEY_ID, "
                "R2_SECRET_ACCESS_KEY, and R2_ENDPOINT in environment."
            )

        logger.info(
            f"[FileService] Uploading image: user_id={user_id}, "
            f"product_id={product_id}, filename={file.filename}"
        )

        # Validate and optimize image
        content, extension, content_type = await FileService._validate_and_optimize(file)
        file_size = len(content)

        # Upload to R2
        image_url = await r2_service.upload_image(
            user_id=user_id,
            product_id=product_id,
            content=content,
            extension=extension,
            content_type=content_type,
        )

        logger.info(
            f"[FileService] Image uploaded: user_id={user_id}, "
            f"product_id={product_id}, url={image_url}, size={file_size/1024:.1f}KB"
        )

        return image_url

    @staticmethod
    async def delete_product_image(image_url: str) -> bool:
        """
        Delete image from R2.

        Args:
            image_url: R2 public URL of the image

        Returns:
            bool: True if deleted, False if didn't exist
        """
        if not r2_service.is_available:
            logger.warning("[FileService] R2 not available - cannot delete image")
            return False

        result = await r2_service.delete_image(image_url)
        if result:
            logger.info(f"[FileService] Image deleted: {image_url}")
        return result

    @staticmethod
    def validate_image_count(db: Session, product_id: int) -> None:
        """
        Vérifie que le produit n'a pas atteint la limite de 20 images.

        Args:
            db: Session SQLAlchemy
            product_id: ID du produit

        Raises:
            ValueError: Si limite atteinte (>= 20 images)
        """
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product with id {product_id} not found")

        image_count = len(product.images or [])

        if image_count >= FileService.MAX_IMAGES_PER_PRODUCT:
            raise ValueError(
                f"Product already has {image_count} images "
                f"(max {FileService.MAX_IMAGES_PER_PRODUCT})"
            )
