"""
eBay Order Repository

Repository pour la gestion des commandes eBay (CRUD operations).
Responsabilité: Accès données pour ebay_orders et ebay_orders_products (schema user_{id}).

Architecture:
- Repository pattern pour isolation DB
- Opérations CRUD standards
- Queries optimisées avec indexes
- Pas de logique métier (pure data access)

Created: 2026-01-07
Author: Claude
"""

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from models.user.ebay_order import EbayOrder, EbayOrderProduct
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class EbayOrderRepository:
    """
    Repository pour la gestion des EbayOrder et EbayOrderProduct.

    Fournit toutes les opérations CRUD et queries spécialisées.
    Toutes les méthodes sont statiques pour faciliter l'utilisation.
    """

    # =========================================================================
    # CRUD Operations - EbayOrder
    # =========================================================================

    @staticmethod
    def create(db: Session, order: EbayOrder) -> EbayOrder:
        """
        Crée une nouvelle commande eBay.

        Args:
            db: Session SQLAlchemy
            order: Instance EbayOrder à créer

        Returns:
            EbayOrder: Instance créée avec ID assigné
        """
        db.add(order)
        db.flush()  # Get ID without committing (caller manages transaction)

        logger.debug(
            f"[EbayOrderRepository] Order created: id={order.id}, "
            f"order_id={order.order_id}"
        )

        return order

    @staticmethod
    def create_order_product(
        db: Session, product: EbayOrderProduct
    ) -> EbayOrderProduct:
        """
        Crée un produit de commande eBay (line item).

        Args:
            db: Session SQLAlchemy
            product: Instance EbayOrderProduct à créer

        Returns:
            EbayOrderProduct: Instance créée avec ID assigné
        """
        db.add(product)
        db.flush()

        logger.debug(
            f"[EbayOrderRepository] Order product created: id={product.id}, "
            f"order_id={product.order_id}, sku={product.sku}"
        )

        return product

    @staticmethod
    def get_by_id(db: Session, order_id: int) -> Optional[EbayOrder]:
        """
        Récupère une commande par son ID interne.

        Args:
            db: Session SQLAlchemy
            order_id: ID interne de la commande

        Returns:
            EbayOrder si trouvée, None sinon
        """
        return db.query(EbayOrder).filter(EbayOrder.id == order_id).first()

    @staticmethod
    def get_by_ebay_order_id(db: Session, ebay_order_id: str) -> Optional[EbayOrder]:
        """
        Récupère une commande par son order_id eBay (clé unique).

        Args:
            db: Session SQLAlchemy
            ebay_order_id: ID commande eBay (ex: "12-34567-89012")

        Returns:
            EbayOrder si trouvée, None sinon
        """
        return (
            db.query(EbayOrder).filter(EbayOrder.order_id == ebay_order_id).first()
        )

    @staticmethod
    def update(db: Session, order: EbayOrder) -> EbayOrder:
        """
        Met à jour une commande existante.

        Args:
            db: Session SQLAlchemy
            order: Instance EbayOrder à mettre à jour

        Returns:
            EbayOrder: Instance mise à jour
        """
        db.flush()

        logger.debug(
            f"[EbayOrderRepository] Order updated: id={order.id}, "
            f"order_id={order.order_id}"
        )

        return order

    @staticmethod
    def delete(db: Session, order: EbayOrder) -> bool:
        """
        Supprime une commande (hard delete, cascade sur products).

        Args:
            db: Session SQLAlchemy
            order: Instance EbayOrder à supprimer

        Returns:
            bool: True si suppression réussie
        """
        db.delete(order)
        db.flush()

        logger.debug(
            f"[EbayOrderRepository] Order deleted: id={order.id}, "
            f"order_id={order.order_id}"
        )

        return True

    # =========================================================================
    # Query Operations
    # =========================================================================

    @staticmethod
    def list_orders(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        marketplace_id: Optional[str] = None,
        fulfillment_status: Optional[str] = None,
        payment_status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Tuple[List[EbayOrder], int]:
        """
        Liste les commandes avec filtres et pagination.

        Args:
            db: Session SQLAlchemy
            skip: Nombre de résultats à sauter (pagination)
            limit: Nombre max de résultats
            marketplace_id: Filtre par marketplace (optionnel)
            fulfillment_status: Filtre par statut fulfillment (optionnel)
            payment_status: Filtre par statut paiement (optionnel)
            date_from: Filtre creation_date >= date_from (optionnel)
            date_to: Filtre creation_date <= date_to (optionnel)

        Returns:
            Tuple[List[EbayOrder], int]: (liste des commandes, total count)
        """
        query = db.query(EbayOrder)

        # Apply filters
        if marketplace_id:
            query = query.filter(EbayOrder.marketplace_id == marketplace_id)

        if fulfillment_status:
            query = query.filter(
                EbayOrder.order_fulfillment_status == fulfillment_status
            )

        if payment_status:
            query = query.filter(EbayOrder.order_payment_status == payment_status)

        if date_from:
            query = query.filter(EbayOrder.creation_date >= date_from)

        if date_to:
            query = query.filter(EbayOrder.creation_date <= date_to)

        # Count total
        total = query.count()

        # Apply pagination and ordering
        orders = (
            query.order_by(EbayOrder.creation_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        logger.debug(
            f"[EbayOrderRepository] list_orders: skip={skip}, limit={limit}, "
            f"total={total}, returned={len(orders)}"
        )

        return orders, total

    @staticmethod
    def list_by_status(
        db: Session, fulfillment_status: str, limit: int = 100
    ) -> List[EbayOrder]:
        """
        Liste les commandes par statut de fulfillment.

        Args:
            db: Session SQLAlchemy
            fulfillment_status: Statut fulfillment (NOT_STARTED, IN_PROGRESS, FULFILLED)
            limit: Nombre max de résultats

        Returns:
            List[EbayOrder]: Liste des commandes
        """
        orders = (
            db.query(EbayOrder)
            .filter(EbayOrder.order_fulfillment_status == fulfillment_status)
            .order_by(EbayOrder.creation_date.desc())
            .limit(limit)
            .all()
        )

        logger.debug(
            f"[EbayOrderRepository] list_by_status: status={fulfillment_status}, "
            f"returned={len(orders)}"
        )

        return orders

    @staticmethod
    def list_by_date_range(
        db: Session, start_date: datetime, end_date: datetime, limit: int = 200
    ) -> List[EbayOrder]:
        """
        Liste les commandes dans une plage de dates.

        Args:
            db: Session SQLAlchemy
            start_date: Date début (inclusive)
            end_date: Date fin (inclusive)
            limit: Nombre max de résultats

        Returns:
            List[EbayOrder]: Liste des commandes
        """
        orders = (
            db.query(EbayOrder)
            .filter(
                and_(
                    EbayOrder.creation_date >= start_date,
                    EbayOrder.creation_date <= end_date,
                )
            )
            .order_by(EbayOrder.creation_date.desc())
            .limit(limit)
            .all()
        )

        logger.debug(
            f"[EbayOrderRepository] list_by_date_range: "
            f"start={start_date.isoformat()}, end={end_date.isoformat()}, "
            f"returned={len(orders)}"
        )

        return orders

    # =========================================================================
    # Aggregation Operations
    # =========================================================================

    @staticmethod
    def count_by_status(db: Session, fulfillment_status: str) -> int:
        """
        Compte les commandes par statut de fulfillment.

        Args:
            db: Session SQLAlchemy
            fulfillment_status: Statut fulfillment (NOT_STARTED, IN_PROGRESS, FULFILLED)

        Returns:
            int: Nombre de commandes
        """
        count = (
            db.query(func.count(EbayOrder.id))
            .filter(EbayOrder.order_fulfillment_status == fulfillment_status)
            .scalar()
            or 0
        )

        logger.debug(
            f"[EbayOrderRepository] count_by_status: status={fulfillment_status}, "
            f"count={count}"
        )

        return count

    @staticmethod
    def exists(db: Session, ebay_order_id: str) -> bool:
        """
        Vérifie si une commande existe par son order_id eBay.

        Args:
            db: Session SQLAlchemy
            ebay_order_id: ID commande eBay (ex: "12-34567-89012")

        Returns:
            bool: True si existe, False sinon
        """
        count = (
            db.query(func.count(EbayOrder.id))
            .filter(EbayOrder.order_id == ebay_order_id)
            .scalar()
            or 0
        )

        return count > 0
