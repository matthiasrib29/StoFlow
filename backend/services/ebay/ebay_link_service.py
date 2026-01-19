"""
eBay Link Service

Service pour lier/délier les produits eBay aux produits Stoflow.

Business Rules:
- Un EbayProduct peut être lié à max 1 Product (relation 1:1)
- Un Product peut être lié à max 1 EbayProduct (relation 1:1)
- La liaison est passive (pas de sync automatique)
- Création depuis eBay: mappe les attributs texte directement (pas de mapping BDD comme Vinted)

Author: Claude
Date: 2026-01-19
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from models.user.ebay_product import EbayProduct
from models.user.product import Product
from shared.logging_setup import get_logger

logger = get_logger(__name__)


class EbayLinkService:
    """
    Service pour gérer la liaison entre EbayProduct et Product.
    """

    def __init__(self, db: Session):
        """
        Initialize service with database session.

        Args:
            db: SQLAlchemy session (user schema)
        """
        self.db = db

    def link_to_existing_product(
        self,
        ebay_product_id: int,
        product_id: int
    ) -> EbayProduct:
        """
        Lie un EbayProduct à un Product existant.

        Args:
            ebay_product_id: ID interne de l'EbayProduct
            product_id: ID du Product Stoflow à lier

        Returns:
            EbayProduct mis à jour

        Raises:
            ValueError: Si EbayProduct ou Product non trouvé
            ValueError: Si EbayProduct déjà lié à un autre Product
            ValueError: Si Product déjà lié à un autre EbayProduct
        """
        # Get EbayProduct
        ebay_product = self.db.query(EbayProduct).filter(
            EbayProduct.id == ebay_product_id
        ).first()

        if not ebay_product:
            raise ValueError(f"EbayProduct #{ebay_product_id} not found")

        # Check if already linked to a different product
        if ebay_product.product_id and ebay_product.product_id != product_id:
            raise ValueError(
                f"EbayProduct #{ebay_product_id} is already linked to Product #{ebay_product.product_id}"
            )

        # Get Product
        product = self.db.query(Product).filter(
            Product.id == product_id,
            Product.deleted_at.is_(None)
        ).first()

        if not product:
            raise ValueError(f"Product #{product_id} not found")

        # Check if Product is already linked to a different EbayProduct
        existing_ebay = self.db.query(EbayProduct).filter(
            EbayProduct.product_id == product_id,
            EbayProduct.id != ebay_product.id
        ).first()

        if existing_ebay:
            raise ValueError(
                f"Product #{product_id} is already linked to EbayProduct #{existing_ebay.id}"
            )

        # Link
        ebay_product.product_id = product_id
        self.db.flush()

        logger.info(f"Linked EbayProduct #{ebay_product_id} to Product #{product_id}")

        return ebay_product

    def unlink(self, ebay_product_id: int) -> EbayProduct:
        """
        Délie un EbayProduct de son Product.

        Args:
            ebay_product_id: ID interne de l'EbayProduct

        Returns:
            EbayProduct mis à jour

        Raises:
            ValueError: Si EbayProduct non trouvé
            ValueError: Si EbayProduct n'est pas lié
        """
        ebay_product = self.db.query(EbayProduct).filter(
            EbayProduct.id == ebay_product_id
        ).first()

        if not ebay_product:
            raise ValueError(f"EbayProduct #{ebay_product_id} not found")

        if not ebay_product.product_id:
            raise ValueError(f"EbayProduct #{ebay_product_id} is not linked to any Product")

        old_product_id = ebay_product.product_id
        ebay_product.product_id = None
        self.db.flush()

        logger.info(f"Unlinked EbayProduct #{ebay_product_id} from Product #{old_product_id}")

        return ebay_product

    def create_product_from_ebay(
        self,
        ebay_product_id: int,
        override_data: Optional[dict] = None
    ) -> tuple[Product, EbayProduct]:
        """
        Crée un Product Stoflow à partir des données EbayProduct et les lie.

        Args:
            ebay_product_id: ID interne de l'EbayProduct source
            override_data: Données à remplacer (optionnel)

        Returns:
            Tuple (Product créé, EbayProduct mis à jour)

        Raises:
            ValueError: Si EbayProduct non trouvé
            ValueError: Si EbayProduct déjà lié
        """
        # Get EbayProduct
        ebay_product = self.db.query(EbayProduct).filter(
            EbayProduct.id == ebay_product_id
        ).first()

        if not ebay_product:
            raise ValueError(f"EbayProduct #{ebay_product_id} not found")

        if ebay_product.product_id:
            raise ValueError(
                f"EbayProduct #{ebay_product_id} is already linked to Product #{ebay_product.product_id}"
            )

        # Map eBay data to Stoflow format
        product_data = self._map_ebay_to_stoflow(ebay_product)

        # Apply overrides
        if override_data:
            product_data.update(override_data)

        # Create Product
        product = Product(**product_data)
        self.db.add(product)
        self.db.flush()

        # Link
        ebay_product.product_id = product.id
        self.db.flush()

        logger.info(
            f"Created Product #{product.id} from EbayProduct #{ebay_product_id} and linked"
        )

        return product, ebay_product

    def _map_ebay_to_stoflow(self, ebay_product: EbayProduct) -> dict:
        """
        Mappe les données EbayProduct vers le format Product Stoflow.

        eBay stocke les attributs en texte (pas d'IDs comme Vinted),
        donc le mapping est plus simple - on copie directement les valeurs.

        Args:
            ebay_product: EbayProduct source

        Returns:
            dict: Données pour créer un Product
        """
        # Map condition from eBay format to Stoflow note (0-10)
        condition = self._map_condition(ebay_product.condition)

        # Build product data
        product_data = {
            "title": ebay_product.title or "Untitled",
            "description": ebay_product.description or "",
            "price": Decimal(str(ebay_product.price)) if ebay_product.price else Decimal("0"),

            # Direct text mapping (no FK constraint issues)
            "brand": ebay_product.brand,
            "size_original": ebay_product.size,

            # Condition mapped to note
            "condition": condition,

            # Category - will be set to default if not mapped
            "category": "other",

            # Stock (eBay quantity)
            "stock_quantity": ebay_product.quantity or 1,
        }

        # Remove None values to use defaults
        product_data = {k: v for k, v in product_data.items() if v is not None}

        return product_data

    def _map_condition(self, ebay_condition: Optional[str]) -> Optional[int]:
        """
        Mappe la condition eBay vers la note Stoflow (0-10).

        eBay uses string conditions:
        - NEW: Brand new, unused
        - LIKE_NEW: Almost new, minimal wear
        - NEW_OTHER: New but opened
        - USED_EXCELLENT: Excellent condition
        - USED_VERY_GOOD: Very good condition
        - USED_GOOD: Good condition
        - USED_ACCEPTABLE: Acceptable condition
        - FOR_PARTS_OR_NOT_WORKING: For parts only

        Args:
            ebay_condition: eBay condition string

        Returns:
            int: Stoflow condition note (0-10)
        """
        if not ebay_condition:
            return None

        mapping = {
            "NEW": 10,
            "LIKE_NEW": 9,
            "NEW_OTHER": 9,
            "USED_EXCELLENT": 8,
            "USED_VERY_GOOD": 7,
            "USED_GOOD": 6,
            "USED_ACCEPTABLE": 5,
            "FOR_PARTS_OR_NOT_WORKING": 2,
        }
        return mapping.get(ebay_condition.upper(), 7)

    def get_linkable_products(
        self,
        search: Optional[str] = None,
        limit: int = 20
    ) -> list[Product]:
        """
        Récupère les produits Stoflow pouvant être liés.

        Exclut les produits déjà liés à un EbayProduct.

        Args:
            search: Recherche textuelle (titre, marque)
            limit: Nombre max de résultats

        Returns:
            Liste de Products non liés
        """
        # Subquery: product_ids already linked to an EbayProduct
        linked_ids = self.db.query(EbayProduct.product_id).filter(
            EbayProduct.product_id.isnot(None)
        ).subquery()

        # Query products not linked
        query = self.db.query(Product).filter(
            Product.deleted_at.is_(None),
            Product.id.notin_(linked_ids)
        )

        # Search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Product.title.ilike(search_term)) |
                (Product.brand.ilike(search_term))
            )

        # Order by most recent
        query = query.order_by(Product.created_at.desc())

        return query.limit(limit).all()


__all__ = ["EbayLinkService"]
