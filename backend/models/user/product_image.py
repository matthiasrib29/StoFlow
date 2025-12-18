"""
ProductImage Model - Schema Utilisateur

Ce modèle représente une image associée à un produit.
Remplace la colonne Text 'images' par une table dédiée avec ordre d'affichage.

Business Rules (2025-12-04):
- Maximum 20 images par produit (limite Vinted)
- Images ordonnées par display_order
- Cascade delete: suppression produit → suppression images
- Stockage local: uploads/{user_id}/products/{product_id}/filename
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class ProductImage(Base):
    """
    Modèle ProductImage - Représente une image de produit.

    Attributes:
        id: Identifiant unique de l'image
        product_id: FK vers Product (cascade delete)
        image_path: Chemin relatif de l'image (ex: uploads/1/products/5/abc123.jpg)
        display_order: Ordre d'affichage (0 = première image)
        created_at: Date d'upload
    """

    __tablename__ = "product_images"
    __table_args__ = (Index("idx_product_image_product_id_order", "product_id", "display_order"),)

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign Key vers Product
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID du produit (FK products.id, cascade delete)",
    )

    # Image data
    image_path: Mapped[str] = mapped_column(
        String(1000), nullable=False, comment="Chemin relatif de l'image"
    )

    display_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Ordre d'affichage (0 = première)"
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    product: Mapped["Product"] = relationship("Product", back_populates="product_images")

    def __repr__(self) -> str:
        return f"<ProductImage(id={self.id}, product_id={self.product_id}, order={self.display_order})>"
