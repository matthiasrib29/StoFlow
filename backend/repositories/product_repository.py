"""
Product Repository

Repository pour la gestion des produits (CRUD operations).
Responsabilité: Accès données pour products (schema user_{id}).

Architecture:
- Repository pattern pour isolation DB
- Opérations CRUD standards
- Soft delete via deleted_at
- Queries optimisées avec indexes

Created: 2026-01-06
Author: Claude
"""

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from models.user.product import Product, ProductStatus
from shared.datetime_utils import utc_now
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class ProductRepository:
    """
    Repository pour la gestion des Product.

    Fournit toutes les opérations CRUD et queries spécialisées.
    Toutes les méthodes sont statiques pour faciliter l'utilisation.
    """

    @staticmethod
    def create(db: Session, product: Product) -> Product:
        """
        Crée un nouveau Product.

        Args:
            db: Session SQLAlchemy
            product: Instance Product à créer

        Returns:
            Product: Instance créée avec ID assigné
        """
        db.add(product)
        db.flush()  # Get ID without committing (caller manages transaction)

        logger.debug(
            f"[ProductRepository] Product created: id={product.id}, "
            f"title={product.title[:50] if product.title else 'N/A'}"
        )

        return product

    @staticmethod
    def get_by_id(
        db: Session, product_id: int, include_deleted: bool = False
    ) -> Optional[Product]:
        """
        Récupère un Product par son ID.

        Args:
            db: Session SQLAlchemy
            product_id: ID du produit
            include_deleted: Si True, inclut les produits soft-deleted

        Returns:
            Product si trouvé, None sinon
        """
        query = db.query(Product).filter(Product.id == product_id)

        if not include_deleted:
            query = query.filter(Product.deleted_at.is_(None))

        return query.first()

    @staticmethod
    def list(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ProductStatus] = None,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        include_deleted: bool = False,
    ) -> Tuple[List[Product], int]:
        """
        Liste les produits avec filtres et pagination.

        Args:
            db: Session SQLAlchemy
            skip: Nombre de résultats à sauter (pagination)
            limit: Nombre max de résultats
            status: Filtre par status (optionnel)
            category: Filtre par catégorie (optionnel)
            brand: Filtre par marque (optionnel)
            include_deleted: Si True, inclut les produits soft-deleted

        Returns:
            Tuple (liste de produits, total count)
        """
        query = db.query(Product)

        if not include_deleted:
            query = query.filter(Product.deleted_at.is_(None))

        if status:
            query = query.filter(Product.status == status)
        if category:
            query = query.filter(Product.category == category)
        if brand:
            query = query.filter(Product.brand == brand)

        total = query.count()
        products = query.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()

        return products, total

    @staticmethod
    def update(db: Session, product: Product) -> Product:
        """
        Met à jour un Product existant.

        Args:
            db: Session SQLAlchemy
            product: Instance Product modifiée

        Returns:
            Product: Instance mise à jour
        """
        db.flush()  # Caller manages transaction

        logger.debug(f"[ProductRepository] Product updated: id={product.id}")

        return product

    @staticmethod
    def soft_delete(db: Session, product: Product) -> Product:
        """
        Soft delete un Product (marque deleted_at).

        Args:
            db: Session SQLAlchemy
            product: Instance Product à supprimer

        Returns:
            Product: Instance avec deleted_at défini
        """
        product.deleted_at = utc_now()
        db.flush()

        logger.info(f"[ProductRepository] Product soft deleted: id={product.id}")

        return product

    @staticmethod
    def hard_delete(db: Session, product: Product) -> bool:
        """
        Supprime physiquement un Product (utiliser avec précaution).

        Args:
            db: Session SQLAlchemy
            product: Instance Product à supprimer

        Returns:
            bool: True si supprimé
        """
        product_id = product.id
        db.delete(product)
        db.flush()

        logger.warning(f"[ProductRepository] Product hard deleted: id={product_id}")

        return True

    @staticmethod
    def get_by_status(
        db: Session, status: ProductStatus, limit: int = 100
    ) -> List[Product]:
        """
        Récupère les produits par status.

        Args:
            db: Session SQLAlchemy
            status: Status à filtrer
            limit: Nombre max de résultats

        Returns:
            Liste de Product
        """
        return (
            db.query(Product)
            .filter(Product.status == status, Product.deleted_at.is_(None))
            .order_by(Product.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_published(db: Session, limit: int = 100) -> List[Product]:
        """
        Récupère les produits publiés.

        Shortcut pour get_by_status(db, ProductStatus.PUBLISHED).

        Args:
            db: Session SQLAlchemy
            limit: Nombre max de résultats

        Returns:
            Liste de Product publiés
        """
        return ProductRepository.get_by_status(db, ProductStatus.PUBLISHED, limit)

    @staticmethod
    def get_drafts(db: Session, limit: int = 100) -> List[Product]:
        """
        Récupère les produits en brouillon.

        Args:
            db: Session SQLAlchemy
            limit: Nombre max de résultats

        Returns:
            Liste de Product en brouillon
        """
        return ProductRepository.get_by_status(db, ProductStatus.DRAFT, limit)

    @staticmethod
    def count(db: Session, include_deleted: bool = False) -> int:
        """
        Compte le nombre total de produits.

        Args:
            db: Session SQLAlchemy
            include_deleted: Si True, inclut les produits soft-deleted

        Returns:
            int: Nombre de produits
        """
        query = db.query(func.count(Product.id))

        if not include_deleted:
            query = query.filter(Product.deleted_at.is_(None))

        return query.scalar() or 0

    @staticmethod
    def count_by_status(db: Session, status: ProductStatus) -> int:
        """
        Compte les produits par status.

        Args:
            db: Session SQLAlchemy
            status: Status à compter

        Returns:
            int: Nombre de produits avec ce status
        """
        return (
            db.query(func.count(Product.id))
            .filter(Product.status == status, Product.deleted_at.is_(None))
            .scalar()
            or 0
        )

    @staticmethod
    def exists(db: Session, product_id: int) -> bool:
        """
        Vérifie si un produit existe.

        Args:
            db: Session SQLAlchemy
            product_id: ID du produit

        Returns:
            bool: True si existe (et non supprimé)
        """
        return (
            db.query(func.count(Product.id))
            .filter(Product.id == product_id, Product.deleted_at.is_(None))
            .scalar()
            or 0
        ) > 0

    @staticmethod
    def get_recent(db: Session, days: int = 7, limit: int = 50) -> List[Product]:
        """
        Récupère les produits créés récemment.

        Args:
            db: Session SQLAlchemy
            days: Nombre de jours à regarder en arrière
            limit: Nombre max de résultats

        Returns:
            Liste de Product récents
        """
        from datetime import timedelta

        cutoff = utc_now() - timedelta(days=days)

        return (
            db.query(Product)
            .filter(Product.created_at >= cutoff, Product.deleted_at.is_(None))
            .order_by(Product.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def search(
        db: Session, query_text: str, limit: int = 50
    ) -> List[Product]:
        """
        Recherche des produits par titre ou description.

        Args:
            db: Session SQLAlchemy
            query_text: Texte de recherche
            limit: Nombre max de résultats

        Returns:
            Liste de Product correspondants
        """
        search_pattern = f"%{query_text}%"

        return (
            db.query(Product)
            .filter(
                Product.deleted_at.is_(None),
                (Product.title.ilike(search_pattern))
                | (Product.description.ilike(search_pattern)),
            )
            .order_by(Product.created_at.desc())
            .limit(limit)
            .all()
        )


__all__ = ["ProductRepository"]
