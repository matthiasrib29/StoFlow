"""
Vinted Product Repository

Repository pour la gestion des produits Vinted (CRUD operations).
Responsabilité: Accès données pour vinted_products (schema user_{id}).

Architecture:
- Repository pattern pour isolation DB
- Opérations CRUD standards
- Queries optimisées avec indexes
- Filtres par status, date, etc.

Created: 2024-12-10
Author: Claude
"""

from datetime import date as date_type
from typing import List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from models.user.vinted_product import VintedProduct
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class VintedProductRepository:
    """
    Repository pour la gestion des VintedProduct.

    Fournit toutes les opérations CRUD et queries spécialisées.
    """

    @staticmethod
    def create(db: Session, vinted_product: VintedProduct) -> VintedProduct:
        """
        Crée un nouveau VintedProduct.

        Args:
            db: Session SQLAlchemy
            vinted_product: Instance VintedProduct à créer

        Returns:
            VintedProduct: Instance créée avec ID assigné

        Example:
            >>> vinted_prod = VintedProduct(product_id=123, status='pending')
            >>> created = VintedProductRepository.create(db, vinted_prod)
            >>> print(created.id)
            1
        """
        db.add(vinted_product)
        db.commit()
        db.refresh(vinted_product)

        logger.info(
            f"[VintedProductRepository] VintedProduct created: vinted_id={vinted_product.vinted_id}, "
            f"product_id={vinted_product.product_id}, status={vinted_product.status}"
        )

        return vinted_product

    @staticmethod
    def get_by_id(db: Session, vinted_product_id: int) -> Optional[VintedProduct]:
        """
        Récupère un VintedProduct par son ID.

        Args:
            db: Session SQLAlchemy
            vinted_product_id: ID du VintedProduct

        Returns:
            VintedProduct si trouvé, None sinon
        """
        stmt = select(VintedProduct).where(VintedProduct.vinted_id == vinted_product_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_product_id(db: Session, product_id: int) -> Optional[VintedProduct]:
        """
        Récupère un VintedProduct par l'ID du produit source.

        Args:
            db: Session SQLAlchemy
            product_id: ID du Product

        Returns:
            VintedProduct si trouvé, None sinon

        Example:
            >>> vinted_prod = VintedProductRepository.get_by_product_id(db, 123)
            >>> if vinted_prod:
            ...     print(vinted_prod.status)
            'published'
        """
        stmt = select(VintedProduct).where(VintedProduct.product_id == product_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_vinted_id(db: Session, vinted_id: int) -> Optional[VintedProduct]:
        """
        Récupère un VintedProduct par son ID Vinted.

        Args:
            db: Session SQLAlchemy
            vinted_id: ID du listing Vinted

        Returns:
            VintedProduct si trouvé, None sinon

        Example:
            >>> vinted_prod = VintedProductRepository.get_by_vinted_id(db, 987654321)
            >>> if vinted_prod:
            ...     print(vinted_prod.product_id)
            123
        """
        stmt = select(VintedProduct).where(VintedProduct.vinted_id == vinted_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_all_by_status(db: Session, status: str, limit: int = 100) -> List[VintedProduct]:
        """
        Récupère tous les VintedProduct par statut.

        Args:
            db: Session SQLAlchemy
            status: Statut à filtrer ('pending', 'published', 'error', 'deleted')
            limit: Nombre maximum de résultats (défaut: 100)

        Returns:
            Liste de VintedProduct

        Example:
            >>> pending = VintedProductRepository.get_all_by_status(db, 'pending')
            >>> print(len(pending))
            15
        """
        stmt = (
            select(VintedProduct)
            .where(VintedProduct.status == status)
            .order_by(VintedProduct.created_at.desc())
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_all_pending(db: Session, limit: int = 100) -> List[VintedProduct]:
        """
        Récupère tous les VintedProduct en attente de publication.

        Args:
            db: Session SQLAlchemy
            limit: Nombre maximum de résultats

        Returns:
            Liste de VintedProduct avec status='pending'
        """
        return VintedProductRepository.get_all_by_status(db, 'pending', limit)

    @staticmethod
    def get_all_published(db: Session, limit: int = 100) -> List[VintedProduct]:
        """
        Récupère tous les VintedProduct publiés.

        Args:
            db: Session SQLAlchemy
            limit: Nombre maximum de résultats

        Returns:
            Liste de VintedProduct avec status='published'
        """
        return VintedProductRepository.get_all_by_status(db, 'published', limit)

    @staticmethod
    def get_all_errors(db: Session, limit: int = 100) -> List[VintedProduct]:
        """
        Récupère tous les VintedProduct en erreur.

        Args:
            db: Session SQLAlchemy
            limit: Nombre maximum de résultats

        Returns:
            Liste de VintedProduct avec status='error'
        """
        return VintedProductRepository.get_all_by_status(db, 'error', limit)

    @staticmethod
    def get_published_by_date_range(
        db: Session,
        start_date: date_type,
        end_date: date_type
    ) -> List[VintedProduct]:
        """
        Récupère les VintedProduct publiés dans une période.

        Args:
            db: Session SQLAlchemy
            start_date: Date de début
            end_date: Date de fin

        Returns:
            Liste de VintedProduct publiés dans la période

        Example:
            >>> from datetime import date
            >>> products = VintedProductRepository.get_published_by_date_range(
            ...     db,
            ...     date(2024, 12, 1),
            ...     date(2024, 12, 10)
            ... )
            >>> print(len(products))
            42
        """
        stmt = (
            select(VintedProduct)
            .where(
                and_(
                    VintedProduct.status == 'published',
                    VintedProduct.date >= start_date,
                    VintedProduct.date <= end_date
                )
            )
            .order_by(VintedProduct.date.desc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def update(db: Session, vinted_product: VintedProduct) -> VintedProduct:
        """
        Met à jour un VintedProduct existant.

        Args:
            db: Session SQLAlchemy
            vinted_product: Instance VintedProduct avec modifications

        Returns:
            VintedProduct: Instance mise à jour

        Example:
            >>> vinted_prod = VintedProductRepository.get_by_id(db, 1)
            >>> vinted_prod.status = 'published'
            >>> vinted_prod.vinted_id = 987654321
            >>> updated = VintedProductRepository.update(db, vinted_prod)
            >>> print(updated.status)
            'published'
        """
        db.commit()
        db.refresh(vinted_product)

        logger.info(f"[VintedProductRepository] VintedProduct updated: vinted_id={vinted_product.vinted_id}")

        return vinted_product

    @staticmethod
    def update_status(db: Session, vinted_product_id: int, status: str) -> Optional[VintedProduct]:
        """
        Met à jour uniquement le statut d'un VintedProduct.

        Args:
            db: Session SQLAlchemy
            vinted_product_id: ID du VintedProduct
            status: Nouveau statut

        Returns:
            VintedProduct mis à jour si trouvé, None sinon

        Example:
            >>> updated = VintedProductRepository.update_status(db, 1, 'published')
            >>> print(updated.status)
            'published'
        """
        vinted_product = VintedProductRepository.get_by_id(db, vinted_product_id)
        if not vinted_product:
            return None

        vinted_product.status = status
        return VintedProductRepository.update(db, vinted_product)

    @staticmethod
    def update_vinted_id(
        db: Session,
        vinted_product_id: int,
        vinted_id: int
    ) -> Optional[VintedProduct]:
        """
        Met à jour l'ID Vinted d'un VintedProduct.

        Args:
            db: Session SQLAlchemy
            vinted_product_id: ID du VintedProduct
            vinted_id: ID Vinted assigné

        Returns:
            VintedProduct mis à jour si trouvé, None sinon
        """
        vinted_product = VintedProductRepository.get_by_id(db, vinted_product_id)
        if not vinted_product:
            return None

        vinted_product.vinted_id = vinted_id
        return VintedProductRepository.update(db, vinted_product)

    @staticmethod
    def update_analytics(
        db: Session,
        vinted_product_id: int,
        view_count: Optional[int] = None,
        favourite_count: Optional[int] = None,
        conversations: Optional[int] = None
    ) -> Optional[VintedProduct]:
        """
        Met à jour les statistiques analytics d'un VintedProduct.

        Args:
            db: Session SQLAlchemy
            vinted_product_id: ID du VintedProduct
            view_count: Nombre de vues (optionnel)
            favourite_count: Nombre de favoris (optionnel)
            conversations: Nombre de conversations (optionnel)

        Returns:
            VintedProduct mis à jour si trouvé, None sinon

        Example:
            >>> updated = VintedProductRepository.update_analytics(
            ...     db, 1, view_count=250, favourite_count=12, conversations=3
            ... )
            >>> print(updated.view_count)
            250
        """
        vinted_product = VintedProductRepository.get_by_id(db, vinted_product_id)
        if not vinted_product:
            return None

        if view_count is not None:
            vinted_product.view_count = view_count

        if favourite_count is not None:
            vinted_product.favourite_count = favourite_count

        if conversations is not None:
            vinted_product.conversations = conversations

        return VintedProductRepository.update(db, vinted_product)

    @staticmethod
    def delete(db: Session, vinted_product_id: int) -> bool:
        """
        Supprime un VintedProduct.

        Args:
            db: Session SQLAlchemy
            vinted_product_id: ID du VintedProduct à supprimer

        Returns:
            bool: True si supprimé, False si non trouvé

        Example:
            >>> success = VintedProductRepository.delete(db, 1)
            >>> print(success)
            True
        """
        vinted_product = VintedProductRepository.get_by_id(db, vinted_product_id)
        if not vinted_product:
            return False

        db.delete(vinted_product)
        db.commit()

        logger.info(
            f"[VintedProductRepository] VintedProduct deleted: id={vinted_product_id}, "
            f"vinted_id={vinted_product.vinted_id}"
        )

        return True

    @staticmethod
    def count_by_status(db: Session, status: str) -> int:
        """
        Compte le nombre de VintedProduct par statut.

        Args:
            db: Session SQLAlchemy
            status: Statut à compter

        Returns:
            int: Nombre de VintedProduct avec ce statut

        Example:
            >>> count = VintedProductRepository.count_by_status(db, 'published')
            >>> print(count)
            127
        """
        stmt = select(func.count(VintedProduct.vinted_id)).where(VintedProduct.status == status)
        return db.execute(stmt).scalar_one() or 0

    @staticmethod
    def get_analytics_summary(db: Session) -> dict:
        """
        Récupère un résumé des analytics pour tous les produits publiés.

        Args:
            db: Session SQLAlchemy

        Returns:
            dict: Résumé avec total_views, total_favourites, total_conversations, avg_views

        Example:
            >>> summary = VintedProductRepository.get_analytics_summary(db)
            >>> print(summary)
            {
                'total_views': 15420,
                'total_favourites': 782,
                'total_conversations': 134,
                'avg_views': 121.42,
                'published_count': 127
            }
        """
        stmt = (
            select(
                func.sum(VintedProduct.view_count).label('total_views'),
                func.sum(VintedProduct.favourite_count).label('total_favourites'),
                func.sum(VintedProduct.conversations).label('total_conversations'),
                func.avg(VintedProduct.view_count).label('avg_views'),
                func.count(VintedProduct.vinted_id).label('published_count')
            )
            .where(VintedProduct.status == 'published')
        )
        result = db.execute(stmt).first()

        return {
            'total_views': result.total_views or 0,
            'total_favourites': result.total_favourites or 0,
            'total_conversations': result.total_conversations or 0,
            'avg_views': float(result.avg_views or 0),
            'published_count': result.published_count or 0
        }
