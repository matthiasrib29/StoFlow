"""
R2 Storage Service

Service for managing file uploads to Cloudflare R2 (S3-compatible).

Business Rules:
- Images stored in bucket: stoflow-images
- Path structure: {user_id}/products/{product_id}/{filename}
- Returns public URLs for serving images via CDN
- Fallback to local storage if R2 not configured
"""

import uuid
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from shared.config import settings
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class R2Service:
    """Service for Cloudflare R2 storage operations."""

    def __init__(self):
        """Initialize R2 client if configured."""
        self._client = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """
        Initialize boto3 S3 client for R2.

        R2 is S3-compatible, so we use boto3 with custom endpoint.
        """
        if not settings.r2_enabled:
            logger.warning(
                "[R2Service] R2 not configured - uploads will use local storage"
            )
            return

        try:
            self._client = boto3.client(
                "s3",
                endpoint_url=settings.r2_endpoint,
                aws_access_key_id=settings.r2_access_key_id,
                aws_secret_access_key=settings.r2_secret_access_key,
                config=Config(
                    signature_version="s3v4",
                    retries={"max_attempts": 3, "mode": "adaptive"},
                ),
                region_name="auto",  # R2 uses 'auto' region
            )
            logger.info(
                f"[R2Service] Initialized with bucket: {settings.r2_bucket_name}"
            )
        except Exception as e:
            logger.error(f"[R2Service] Failed to initialize client: {e}")
            self._client = None

    @property
    def is_available(self) -> bool:
        """Check if R2 storage is available."""
        return self._client is not None

    def _generate_object_key(
        self, user_id: int, product_id: int, extension: str
    ) -> str:
        """
        Generate unique object key for R2.

        Format: {user_id}/products/{product_id}/{uuid}.{ext}

        Args:
            user_id: User ID for path isolation
            product_id: Product ID
            extension: File extension (jpg, png)

        Returns:
            str: Object key for R2
        """
        unique_id = uuid.uuid4().hex
        return f"{user_id}/products/{product_id}/{unique_id}.{extension}"

    async def upload_image(
        self,
        user_id: int,
        product_id: int,
        content: bytes,
        extension: str,
        content_type: str = "image/jpeg",
    ) -> Optional[str]:
        """
        Upload image to R2 bucket.

        Args:
            user_id: User ID for path isolation
            product_id: Product ID
            content: Image bytes
            extension: File extension (jpg, jpeg, png)
            content_type: MIME type of the image

        Returns:
            str: Public URL of uploaded image, or None if failed

        Raises:
            Exception: If upload fails and R2 is the only storage option
        """
        if not self.is_available:
            logger.warning("[R2Service] R2 not available - cannot upload")
            return None

        object_key = self._generate_object_key(user_id, product_id, extension)

        try:
            self._client.put_object(
                Bucket=settings.r2_bucket_name,
                Key=object_key,
                Body=content,
                ContentType=content_type,
                # R2 doesn't require ACL for public access (configured at bucket level)
            )

            # Build public URL
            public_url = self._get_public_url(object_key)

            logger.info(
                f"[R2Service] Image uploaded: user_id={user_id}, "
                f"product_id={product_id}, key={object_key}, "
                f"size={len(content)/1024:.1f}KB"
            )

            return public_url

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(
                f"[R2Service] Upload failed: user_id={user_id}, "
                f"product_id={product_id}, error={error_code}: {e}"
            )
            raise
        except Exception as e:
            logger.error(
                f"[R2Service] Unexpected upload error: user_id={user_id}, "
                f"product_id={product_id}, error={e}"
            )
            raise

    def _get_public_url(self, object_key: str) -> str:
        """
        Get public URL for an object.

        Uses r2_public_url if configured (custom domain like cdn.stoflow.io),
        otherwise constructs URL from R2 endpoint.

        Args:
            object_key: Object key in the bucket

        Returns:
            str: Public URL for the object
        """
        if settings.r2_public_url:
            base_url = settings.r2_public_url.rstrip("/")
            return f"{base_url}/{object_key}"

        # Fallback: construct from endpoint (may not work without public access)
        # R2 public URL format: https://{bucket}.{account_id}.r2.dev/{key}
        # This requires public access enabled on the bucket
        if settings.r2_account_id:
            return f"https://{settings.r2_bucket_name}.{settings.r2_account_id}.r2.dev/{object_key}"

        logger.warning(
            "[R2Service] No public URL configured - returning object key only"
        )
        return object_key

    async def delete_image(self, image_url: str) -> bool:
        """
        Delete image from R2 bucket.

        Args:
            image_url: Public URL or object key of the image

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        if not self.is_available:
            logger.warning("[R2Service] R2 not available - cannot delete")
            return False

        # Extract object key from URL
        object_key = self._extract_object_key(image_url)
        if not object_key:
            logger.warning(
                f"[R2Service] Could not extract object key from: {image_url}"
            )
            return False

        try:
            self._client.delete_object(
                Bucket=settings.r2_bucket_name,
                Key=object_key,
            )
            logger.info(f"[R2Service] Image deleted: key={object_key}")
            return True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            # NoSuchKey means already deleted - consider success
            if error_code == "NoSuchKey":
                logger.info(
                    f"[R2Service] Image already deleted: key={object_key}"
                )
                return True
            logger.error(
                f"[R2Service] Delete failed: key={object_key}, error={error_code}: {e}"
            )
            return False
        except Exception as e:
            logger.error(
                f"[R2Service] Unexpected delete error: key={object_key}, error={e}"
            )
            return False

    def _extract_object_key(self, image_url: str) -> Optional[str]:
        """
        Extract object key from public URL or return as-is if already a key.

        Args:
            image_url: Public URL or object key

        Returns:
            str: Object key, or None if extraction failed
        """
        if not image_url:
            return None

        # If it's already an object key (no http)
        if not image_url.startswith("http"):
            return image_url

        # Extract from public URL
        # Expected formats:
        # - https://cdn.stoflow.io/{key}
        # - https://{bucket}.{account}.r2.dev/{key}
        try:
            # Remove protocol and domain
            parts = image_url.split("/", 3)
            if len(parts) >= 4:
                return parts[3]
            return None
        except Exception:
            return None

    async def check_connection(self) -> bool:
        """
        Test R2 connection by listing bucket.

        Returns:
            bool: True if connection successful
        """
        if not self.is_available:
            return False

        try:
            self._client.head_bucket(Bucket=settings.r2_bucket_name)
            logger.info("[R2Service] Connection check passed")
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(f"[R2Service] Connection check failed: {error_code}")
            return False
        except Exception as e:
            logger.error(f"[R2Service] Connection check error: {e}")
            return False


# Singleton instance for easy import
r2_service = R2Service()
