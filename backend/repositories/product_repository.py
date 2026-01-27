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

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from models.user.product import Product, ProductStatus
from shared.datetime_utils import utc_now
from shared.logging import get_logger

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
        conditions = [Product.id == product_id]

        if not include_deleted:
            conditions.append(Product.deleted_at.is_(None))

        stmt = (
            select(Product)
            .options(
                selectinload(Product.product_images),
                selectinload(Product.vinted_product),
                selectinload(Product.ebay_product),
                # M2M relationships for attributes (prevent N+1 queries)
                selectinload(Product.product_colors),
                selectinload(Product.product_materials),
                selectinload(Product.product_condition_sups),
            )
            .where(and_(*conditions))
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ProductStatus] = None,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        search: Optional[str] = None,
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
            search: Recherche par ID, titre ou marque (optionnel)
            include_deleted: Si True, inclut les produits soft-deleted

        Returns:
            Tuple (liste de produits, total count)
        """
        conditions = []

        if not include_deleted:
            conditions.append(Product.deleted_at.is_(None))

        if status:
            conditions.append(Product.status == status)
        if category:
            conditions.append(Product.category == category)
        if brand:
            conditions.append(Product.brand == brand)

        if search:
            search_term = search.strip()
            search_conditions = [
                Product.title.ilike(f"%{search_term}%"),
                Product.brand.ilike(f"%{search_term}%"),
            ]
            if search_term.isdigit():
                search_conditions.append(Product.id == int(search_term))
            conditions.append(or_(*search_conditions))

        # Count total
        count_stmt = select(func.count(Product.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total = db.execute(count_stmt).scalar_one() or 0

        # Get products with images, marketplace links, and M2M relations (2026-01-19, 2026-01-20)
        stmt = (
            select(Product)
            .options(
                selectinload(Product.product_images),
                selectinload(Product.vinted_product),
                selectinload(Product.ebay_product),
                # M2M relationships for attributes (prevent N+1 queries)
                selectinload(Product.product_colors),
                selectinload(Product.product_materials),
                selectinload(Product.product_condition_sups),
            )
        )
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(Product.created_at.desc()).offset(skip).limit(limit)
        products = list(db.execute(stmt).scalars().all())

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
    def archive(db: Session, product: Product) -> Product:
        """
        Archive un Product (passe en status ARCHIVED).

        Args:
            db: Session SQLAlchemy
            product: Instance Product à archiver

        Returns:
            Product: Instance avec status ARCHIVED
        """
        product.status = ProductStatus.ARCHIVED
        db.flush()

        logger.info(f"[ProductRepository] Product archived: id={product.id}")

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
        stmt = (
            select(Product)
            .options(
                selectinload(Product.product_images),
                selectinload(Product.product_colors),
                selectinload(Product.product_materials),
            )
            .where(Product.status == status, Product.deleted_at.is_(None))
            .order_by(Product.created_at.desc())
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())

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
        stmt = select(func.count(Product.id))

        if not include_deleted:
            stmt = stmt.where(Product.deleted_at.is_(None))

        return db.execute(stmt).scalar_one() or 0

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
        stmt = (
            select(func.count(Product.id))
            .where(Product.status == status, Product.deleted_at.is_(None))
        )
        return db.execute(stmt).scalar_one() or 0

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
        stmt = (
            select(func.count(Product.id))
            .where(Product.id == product_id, Product.deleted_at.is_(None))
        )
        count = db.execute(stmt).scalar_one() or 0
        return count > 0

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

        stmt = (
            select(Product)
            .options(selectinload(Product.product_images))
            .where(Product.created_at >= cutoff, Product.deleted_at.is_(None))
            .order_by(Product.created_at.desc())
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())

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

        stmt = (
            select(Product)
            .options(selectinload(Product.product_images))
            .where(
                Product.deleted_at.is_(None),
                (Product.title.ilike(search_pattern))
                | (Product.description.ilike(search_pattern)),
            )
            .order_by(Product.created_at.desc())
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())


__all__ = ["ProductRepository"]
