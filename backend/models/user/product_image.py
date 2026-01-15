"""
Product Image Model.

Represents product images with rich metadata in the product_images table.
Replaces JSONB products.images column with structured relational table.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Integer, String, Boolean, Text, ForeignKey, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.user.product import Product


class ProductImage(Base):
    """
    Product image with rich metadata.

    Attributes:
        id: Primary key
        product_id: Foreign key to products table
        url: Image URL (CDN)
        order: Display order (0-indexed)
        is_label: Whether this is an internal price label (not published to marketplaces)
        alt_text: Alt text for accessibility and SEO
        tags: Image tags for filtering (e.g., 'front', 'back', 'detail')
        mime_type: MIME type (e.g., 'image/jpeg')
        file_size: File size in bytes
        width: Image width in pixels
        height: Image height in pixels
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "product_images"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign key to products
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Core fields
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Metadata
    is_label: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    alt_text: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        server_default="now()",
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        server_default="now()",
        onupdate=datetime.utcnow,
    )

    # Relationship to Product
    product: Mapped["Product"] = relationship("Product", back_populates="product_images")

    def __repr__(self) -> str:
        return (
            f"<ProductImage(id={self.id}, product_id={self.product_id}, "
            f"order={self.order}, is_label={self.is_label})>"
        )
